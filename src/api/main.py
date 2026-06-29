"""
FastAPI Backend for Incident Response Agent

Provides WebSocket chat, document ingestion, and incident analysis.
"""

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging

from ..memory_manager import MemoryManager
from ..rag_retriever import RAGRetriever
from ..document_processor import DocumentProcessor
from ..services.chatbot import IncidentChatbot
from ..openai_client import OpenAIClient

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
        content = await file.read()
        text = content.decode('utf-8')

        # Process document
        chunks = document_processor.chunk_text(text, chunk_size=500, overlap=50)

        # Ingest into RAG
        doc_type = document_processor.infer_doc_type(file.filename)
        rag_retriever.ingest_documents(
            [{"text": chunk.text, "metadata": {"source": file.filename, "type": doc_type}}
             for chunk in chunks]
        )

        # Register in chatbot
        chatbot.add_uploaded_doc(file.filename, [chunk.text for chunk in chunks])

        return {
            "status": "success",
            "filename": file.filename,
            "chunks": len(chunks),
            "doc_type": doc_type
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
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


async def analyze_incident(user_input: str) -> str:
    """Analyze incident using the LLM."""
    try:
        # Get memory context
        memory_context = memory_manager.get_memory_context(keywords=user_input.split()[:5])

        # Get RAG context
        rag_context = rag_retriever.retrieve_and_format(user_input, n_results=2)

        # Build prompt
        prompt = f"""You are an expert incident response analyst.

User Input: {user_input}

{memory_context}

{rag_context}

Provide a concise incident analysis with:
1. Summary
2. Root cause hypothesis
3. Recommended immediate actions
4. Affected services

Keep response under 500 words."""

        # Call LLM
        response = llm_client.analyze(prompt)
        return response

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
