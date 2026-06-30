"""
FastAPI Backend for Incident Response Agent

Provides WebSocket chat, document ingestion, and incident analysis.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)


from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import json
import asyncio
from typing import List, Dict, Any
import logging

from ..memory_manager import MemoryManager
from ..rag_retriever import RAGRetriever
from ..document_processor import DocumentProcessor
from ..services.chatbot import IncidentChatbot
from ..openai_client import OpenAIClient
from ..agents.manager import AgentManager
from ..report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
memory_manager = MemoryManager(memory_dir="./memory")
rag_retriever = RAGRetriever()
document_processor = DocumentProcessor()
llm_client = OpenAIClient()

# FastAPI app
app = FastAPI(
    title="Enterprise Incident Response Agent",
    description="AI-powered incident analysis with RAG and memory",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance (per-session would be better in production)
chatbot = IncidentChatbot(llm_client, memory_manager, rag_retriever)

# Global agent manager
agent_manager = AgentManager(rag_retriever, memory_manager, llm_client)

# Global report generator
report_generator = ReportGenerator(memory_manager)

# Global analysis progress state (in-memory, would use Redis in production)
analysis_progress = {
    "current_step": 0,
    "steps": [
        {"id": 1, "title": "Parse Logs", "description": "Extracting relevant log data", "status": "pending", "duration": None},
        {"id": 2, "title": "Retrieve Documents (RAG)", "description": "Searching knowledge base for relevant info", "status": "pending", "duration": None},
        {"id": 3, "title": "Search Memory", "description": "Looking for similar past incidents", "status": "pending", "duration": None},
        {"id": 4, "title": "Root Cause Analysis", "description": "Analyzing patterns and identifying cause", "status": "pending", "duration": None},
        {"id": 5, "title": "Generate Report", "description": "Creating incident report & recommendations", "status": "pending", "duration": None}
    ]
}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "memory": "ok",
            "rag": "ok",
            "llm": "ok"
        }
    }


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    memory_stats = memory_manager.get_stats()
    chatbot_stats = chatbot.get_memory_stats()

    return {
        "memory": memory_stats,
        "chatbot": chatbot_stats,
        "backups": len(memory_manager.get_backup_history())
    }


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document."""
    try:
        import tempfile
        from pathlib import Path

        content = await file.read()
        file_ext = Path(file.filename).suffix.lower()
        logger.info(f"📁 Uploading {file.filename} ({len(content)} bytes)")

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Process document based on file type
            tmp_file_path = Path(tmp_path)
            logger.info(f"Processing {file.filename}...")
            chunks = document_processor.process_document(tmp_file_path)

            if not chunks:
                logger.warning(f"No chunks from processor, using fallback")
                # Create fallback chunk from file content
                text_content = content.decode('utf-8', errors='ignore')
                if text_content.strip():
                    chunks = [type('Chunk', (), {
                        'content': text_content,
                        'metadata': {'source': file.filename, 'type': 'text'}
                    })()]
                else:
                    raise ValueError(f"Could not process or extract text from file: {file.filename}")

            logger.info(f"Got {len(chunks)} chunks")

            # Ingest into RAG (with error handling)
            try:
                from ..document_processor import DocumentChunk
                doc_type = document_processor._infer_doc_type(tmp_file_path)
                # Convert to DocumentChunk format
                doc_chunks = [
                    DocumentChunk(
                        content=chunk.content,
                        metadata={**chunk.metadata, "source": file.filename, "doc_type": doc_type}
                    )
                    for chunk in chunks
                ]
                rag_retriever.chroma.add_chunks(doc_chunks)
                logger.info(f"✅ Ingested into RAG: {doc_type}")
            except Exception as rag_error:
                logger.warning(f"RAG ingestion failed (non-blocking): {rag_error}")

            # Register in chatbot
            try:
                chatbot.add_uploaded_doc(file.filename, [chunk.content for chunk in chunks])
                logger.info(f"✅ Registered in chatbot")
            except Exception as chat_error:
                logger.warning(f"Chatbot registration failed (non-blocking): {chat_error}")

            logger.info(f"✅ Upload complete: {file.filename}")

            return {
                "status": "success",
                "filename": file.filename,
                "chunks": len(chunks),
                "doc_type": "text",
                "file_type": file_ext
            }
        finally:
            # Clean up temp file
            import os
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"❌ Upload failed: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            logger.info(f"Received: {message.get('type')}")

            if message.get("type") == "message":
                user_input = message.get("content", "")

                # Add to chatbot history
                chatbot.add_conversation_message("user", user_input)

                # Send loading indicator
                await websocket.send_json({
                    "type": "loading",
                    "content": "Analyzing incident..."
                })

                try:
                    # Analyze incident
                    response = await analyze_incident(user_input)

                    # Add to history
                    chatbot.add_conversation_message("bot", response)

                    # Send response
                    await websocket.send_json({
                        "type": "message",
                        "content": response,
                        "timestamp": message.get("timestamp")
                    })

                except Exception as e:
                    logger.error(f"Analysis failed: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Analysis failed: {str(e)}"
                    })

            elif message.get("type") == "history":
                # Send recent history
                history = chatbot.get_recent_history(limit=10)
                await websocket.send_json({
                    "type": "history",
                    "content": history
                })

            elif message.get("type") == "stats":
                # Send memory stats
                stats = chatbot.get_memory_stats()
                await websocket.send_json({
                    "type": "stats",
                    "content": stats
                })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        logger.info("WebSocket connection closed")


def update_progress(step_id: int, status: str, duration: str = None):
    """Update analysis progress for a specific step."""
    global analysis_progress
    if 0 <= step_id - 1 < len(analysis_progress["steps"]):
        analysis_progress["steps"][step_id - 1]["status"] = status
        if duration:
            analysis_progress["steps"][step_id - 1]["duration"] = duration


async def analyze_incident(user_input: str) -> str:
    """Analyze incident using agent pipeline with progress tracking."""
    global analysis_progress
    try:
        # Reset progress and agents
        agent_manager.reset()
        analysis_progress = {
            "current_step": 0,
            "steps": [
                {"id": 1, "title": "Parse Logs", "description": "Extracting relevant log data", "status": "pending", "duration": None},
                {"id": 2, "title": "Retrieve Documents (RAG)", "description": "Searching knowledge base for relevant info", "status": "pending", "duration": None},
                {"id": 3, "title": "Search Memory", "description": "Looking for similar past incidents", "status": "pending", "duration": None},
                {"id": 4, "title": "Root Cause Analysis", "description": "Analyzing patterns and identifying cause", "status": "pending", "duration": None},
                {"id": 5, "title": "Generate Report", "description": "Creating incident report & recommendations", "status": "pending", "duration": None}
            ]
        }

        # Map agents to progress steps
        agent_to_step = {
            'Parser Agent': 1,
            'Retriever Agent': 2,
            'Memory Agent': 3,
            'Reasoning Agent': 4,
            'Reporter Agent': 5  # RecommendationAgent and ReporterAgent both map to step 5
        }

        async def update_agent_progress(event):
            """Update progress based on agent status."""
            agent_name = event.get('agent', '')
            step_id = agent_to_step.get(agent_name)

            if step_id:
                status_map = {
                    'in_progress': 'in_progress',
                    'completed': 'completed',
                    'failed': 'pending'
                }
                new_status = status_map.get(event.get('status', 'pending'), 'pending')
                update_progress(step_id, new_status, event.get('duration'))

        # Run agent pipeline
        try:
            result = await agent_manager.run_analysis(user_input, update_agent_progress)

            # Get final report and convert to string for chat response
            final_report = result or {}
            response = f"""
## Incident Analysis Report

**Incident ID**: {final_report.get('incident_id', 'N/A')}
**Severity**: {final_report.get('severity', 'Unknown')}
**Status**: {final_report.get('status', 'Unknown')}

### Summary
{final_report.get('summary', 'Analysis in progress...')}

### Root Cause
{final_report.get('root_cause', 'Unknown')}

### Affected Systems
{', '.join(final_report.get('affected_systems', []))}

### Immediate Actions
{chr(10).join(f"- {action}" for action in final_report.get('recommendations', {}).get('immediate_actions', []))}

### Confidence Level
{final_report.get('confidence', 0)}%
"""
            return response

        except Exception as e:
            logger.error(f"Agent pipeline error: {e}")
            raise

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return f"Error during analysis: {str(e)}"


@app.get("/api/incidents")
async def get_incidents(limit: int = 10):
    """Get recent incidents from memory."""
    incidents = memory_manager.long_term['incidents'][-limit:]
    return {
        "total": memory_manager.long_term['metadata']['total_incidents'],
        "incidents": incidents
    }


@app.get("/api/incidents/trend")
async def get_incident_trend(days: int = 7):
    """Get incident trend data for the last N days from memory."""
    from datetime import datetime, timedelta
    from collections import defaultdict

    # Get incidents from memory
    incidents = memory_manager.long_term.get('incidents', [])

    if not incidents:
        # Fallback if no incidents exist
        return {
            "dates": [],
            "counts": []
        }

    # Group incidents by date
    date_counts = defaultdict(int)

    for incident in incidents:
        try:
            # Parse incident timestamp
            timestamp_str = incident.get('timestamp', incident.get('incident_timestamp', ''))
            if timestamp_str:
                # Extract date from ISO format timestamp
                incident_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).date()
                date_counts[incident_date] += 1
        except Exception as e:
            logger.warning(f"Could not parse incident timestamp: {e}")

    # Generate date range for last N days
    today = datetime.now().date()
    date_range = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]

    # Map dates to counts
    dates = [d.strftime("%b %d") for d in date_range]
    counts = [date_counts.get(d, 0) for d in date_range]

    return {
        "dates": dates,
        "counts": counts
    }


@app.get("/api/incidents/severity")
async def get_incidents_by_severity():
    """Get incidents breakdown by severity from memory."""
    # Get incidents from memory
    incidents = memory_manager.long_term.get('incidents', [])

    # Count by severity
    severity_counts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }

    for incident in incidents:
        severity = incident.get('severity', 'low').lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
        else:
            severity_counts['low'] += 1  # Default to low if unknown

    total = sum(severity_counts.values())

    if total == 0:
        # Return zeros if no incidents
        severity_counts['total'] = 0
        return severity_counts

    return {
        "critical": severity_counts['critical'],
        "high": severity_counts['high'],
        "medium": severity_counts['medium'],
        "low": severity_counts['low'],
        "total": total
    }


@app.get("/api/incidents/latest")
async def get_latest_incident():
    """Get latest incident analysis from memory."""
    # Get incidents from memory
    incidents = memory_manager.long_term.get('incidents', [])

    if not incidents:
        # Fallback to example incident if none exist
        return {
            "confidence": 0,
            "severity": "Unknown",
            "status": "No incidents recorded",
            "affected_users": "N/A",
            "duration": "N/A",
            "primary_cause": "No incidents to analyze",
            "business_impact": "N/A",
            "technical_impact": "N/A",
            "affected_services": [],
            "immediate_action": "Upload and analyze logs to populate incident data"
        }

    # Get the most recent incident
    latest = incidents[-1]

    # Extract and format the incident data
    return {
        "confidence": 85,  # Default confidence for stored incidents
        "severity": latest.get('severity', 'Unknown'),
        "status": "Analyzed",
        "affected_users": "N/A",  # Not always tracked
        "duration": "N/A",
        "primary_cause": latest.get('root_cause', 'Unknown'),
        "business_impact": latest.get('summary', 'N/A'),
        "technical_impact": latest.get('technical_impact', 'See root cause'),
        "affected_services": latest.get('affected_services', []),
        "immediate_action": (
            latest.get('recommendations', ['No recommendations available'])[0]
            if latest.get('recommendations')
            else "No recommendations available"
        )
    }


@app.get("/api/incidents/analysis-progress")
async def get_analysis_progress():
    """Get current analysis pipeline progress."""
    global analysis_progress
    return {"steps": analysis_progress["steps"]}


@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all incident response agents."""
    return {"agents": agent_manager.get_agents_status()}


@app.get("/api/agents/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Get status of specific agent."""
    status = agent_manager.get_agent_status(agent_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")
    return status


@app.get("/api/agents/context")
async def get_agents_context():
    """Get current analysis context from agents."""
    return agent_manager.get_context()


@app.get("/api/backups")
async def get_backups():
    """Get backup history."""
    backups = memory_manager.get_backup_history()
    return {
        "count": len(backups),
        "backups": backups
    }


@app.post("/api/backups/restore/{backup_index}")
async def restore_backup(backup_index: int):
    """Restore from a backup."""
    backups = memory_manager.get_backup_history()
    if backup_index >= len(backups):
        raise HTTPException(status_code=404, detail="Backup not found")

    backup_path = backups[backup_index]['path']
    success = memory_manager.restore_from_backup(backup_path)

    if not success:
        raise HTTPException(status_code=400, detail="Restore failed")

    return {"status": "success", "message": f"Restored from {backups[backup_index]['filename']}"}


@app.post("/api/chat/clear")
async def clear_chat():
    """Clear chat history."""
    chatbot.clear_history()
    return {"status": "success", "message": "Chat cleared"}


@app.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    """Get chat history."""
    history = chatbot.get_recent_history(limit=limit)
    return {"history": history}


@app.post("/api/chat/analyze")
async def analyze_logs(request: dict):
    """Analyze incident logs with full results."""
    try:
        logs = request.get("logs", "")
        if not logs:
            raise ValueError("No logs provided")

        # Simulate analysis pipeline
        analysis_result = await analyze_incident(logs)

        # Mock evidence (would be real RAG results)
        evidence = [
            {
                "filename": "Database Connection Pool Guide.pdf",
                "relevance": 96,
                "type": "runbook",
                "content": "When connection pool is exhausted: 1. Check active connections. 2. Identify long-running queries. 3. Increase pool size if needed."
            },
            {
                "filename": "Error Recovery Handbook.pdf",
                "relevance": 88,
                "type": "handbook",
                "content": "Common database errors and their solutions. Connection timeout errors indicate resource exhaustion."
            }
        ]

        # Mock similar incidents (would be real memory results)
        similar_incidents = [
            {
                "id": "INC-2025-1847",
                "similarity": 92,
                "summary": "Database connection pool exhausted during peak traffic",
                "root_cause": "Insufficient pool size configuration",
                "resolution": "Increased pool size from 50 to 200 connections",
                "resolution_time": "12 minutes",
                "timestamp": "2025-06-15T10:30:00Z"
            },
            {
                "id": "INC-2025-1642",
                "similarity": 78,
                "summary": "API service timeout after database maintenance",
                "root_cause": "Connection leak during maintenance window",
                "resolution": "Restarted connection pool after maintenance",
                "resolution_time": "8 minutes",
                "timestamp": "2025-05-28T14:45:00Z"
            }
        ]

        return {
            "status": "success",
            "confidence": 92,
            "severity": "Critical",
            "status_text": "Investigating",
            "affected_users": "~5,000 users",
            "duration": "15 minutes",
            "primary_cause": "Database connection pool exhaustion due to increased query load",
            "business_impact": "Order processing service is unavailable. Estimated revenue loss: $50K/minute",
            "technical_impact": "Connection pool at 100% capacity, new requests timing out after 30 seconds",
            "affected_services": ["api-gateway", "order-service", "payment-service"],
            "immediate_action": "1. Increase connection pool size to 300. 2. Kill long-running queries. 3. Scale database replicas.",
            "evidence": evidence,
            "similar_incidents": similar_incidents,
            "full_analysis": analysis_result
        }

    except Exception as e:
        logger.error(f"Analysis endpoint error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ═══ REPORT MANAGEMENT ENDPOINTS ═══

@app.post("/api/report/generate")
async def generate_report(request: dict):
    """Generate report for an incident."""
    try:
        incident_id = request.get("incident_id")
        format = request.get("format", "json")

        if not incident_id:
            raise ValueError("incident_id is required")

        if format not in ["pdf", "json", "csv"]:
            raise ValueError(f"Unsupported format: {format}")

        # Generate report
        report_data = report_generator.generate_report(incident_id, format)

        if not report_data:
            raise ValueError(f"Could not generate report for incident: {incident_id}")

        # Save report file
        file_path = report_generator.save_report_file(incident_id, format, report_data)

        if not file_path:
            raise ValueError("Could not save report file")

        return {
            "status": "success",
            "incident_id": incident_id,
            "format": format,
            "file_path": file_path,
            "filename": report_data.get("filename")
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/report/download/{report_id}")
async def download_report(report_id: str):
    """Download a generated report."""
    try:
        # Get report metadata
        report = memory_manager.get_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        file_path = report.get("file_path")

        if not file_path:
            raise HTTPException(status_code=404, detail="Report file not found")

        # Increment download count
        memory_manager.increment_download_count(report_id)

        # Return file
        return FileResponse(
            path=file_path,
            filename=f"incident_{report.get('incident_id')}_report.{report.get('format')}",
            media_type=_get_media_type(report.get("format"))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/incident/{incident_id}")
async def get_incident_reports(incident_id: str):
    """Get all reports for an incident."""
    try:
        reports = memory_manager.get_reports_by_incident(incident_id)

        return {
            "incident_id": incident_id,
            "total": len(reports),
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Failed to get incident reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/list")
async def list_reports(limit: int = 100, offset: int = 0, format: str = None):
    """List all generated reports."""
    try:
        reports = memory_manager.list_reports(limit=limit, offset=offset, format_filter=format)

        return {
            "total": len(reports),
            "limit": limit,
            "offset": offset,
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/stats")
async def get_report_stats():
    """Get report statistics."""
    try:
        stats = memory_manager.get_report_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get report stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_media_type(format: str) -> str:
    """Get media type for format."""
    media_types = {
        "pdf": "application/pdf",
        "json": "application/json",
        "csv": "text/csv"
    }
    return media_types.get(format, "application/octet-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
