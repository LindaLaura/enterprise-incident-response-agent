# Week 3-4 Implementation Plan: Chatbox with Document Ingestion

## Overview

Build a production-ready web interface with an intelligent chatbox that:
- Analyzes incident logs conversationally
- Ingests documents dynamically
- Provides real-time recommendations
- Maintains conversation history
- Integrates with RAG and Memory systems

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Vue.js Web Application                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Chatbox Component                      │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  Message History                           │ │ │
│  │  │  [Bot] Hi, upload docs or analyze logs     │ │ │
│  │  │  [User] Analyzing these logs...            │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  File Upload Zone (Drag & Drop)           │ │ │
│  │  │  📎 Drop files or click to upload         │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  Chat Input                               │ │ │
│  │  │  [Textarea: Ask anything...]              │ │ │
│  │  │  [Upload] [Send]                          │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Sidebar Navigation                     │ │
│  │  • Dashboard                                     │ │
│  │  • Documents (Manage uploaded docs)              │ │
│  │  • History (Past incidents)                      │ │
│  │  • Analytics                                     │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                    WebSocket
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────────┐  ┌──────────┐  ┌──────────────┐
    │ FastAPI    │  │ChromaDB  │  │Memory Manager│
    │Server      │  │RAG       │  │Long-term     │
    │            │  │System    │  │              │
    │• Chat      │  │• Search  │  │• Incidents   │
    │• Upload    │  │• Embed   │  │• Context     │
    │• Analyze   │  │• Filter  │  │              │
    └────────────┘  └──────────┘  └──────────────┘
         │               │               │
    ┌────────────┐  ┌──────────┐  ┌──────────────┐
    │  LLM API   │  │ Docs/    │  │JSON Files    │
    │ Anthropic  │  │ Chunks   │  │              │
    │ OpenAI     │  │          │  │              │
    └────────────┘  └──────────┘  └──────────────┘
```

---

## Phase 1: Backend Setup (Week 3, Days 1-2)

### 1.1 Create API Server Structure

```
src/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat WebSocket endpoint
│   │   ├── documents.py       # Document upload/management
│   │   └── incidents.py       # Incident queries
│   ├── models.py              # Pydantic models
│   └── dependencies.py        # Shared dependencies
├── services/
│   ├── __init__.py
│   ├── chatbot.py             # Chatbot logic
│   └── document_service.py    # Document processing
└── ... (existing files)
```

### 1.2 Create FastAPI Main App

**File: `src/api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Global instances
llm_client = None
memory_manager = None
rag_retriever = None
chatbot = None

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Incident Response API...")
    global llm_client, memory_manager, rag_retriever, chatbot
    
    from src.anthropic_client import AnthropicClient
    from src.memory_manager import MemoryManager
    from src.rag_retriever import RAGRetriever
    from src.services.chatbot import IncidentChatbot
    
    llm_client = AnthropicClient()
    memory_manager = MemoryManager()
    rag_retriever = RAGRetriever()
    chatbot = IncidentChatbot(llm_client, memory_manager, rag_retriever)
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="Incident Response API",
    description="AI-powered incident analysis with document ingestion",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://incidents.your-domain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from src.api.routes import chat, documents, incidents

app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(incidents.router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 1.3 Create Pydantic Models

**File: `src/api/models.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user" or "bot"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class DocumentMetadata(BaseModel):
    """Document metadata"""
    filename: str
    doc_type: str
    chunks_created: int
    upload_time: datetime
    size_bytes: int

class AnalysisRequest(BaseModel):
    """Incident analysis request"""
    logs: str
    use_rag: bool = True
    use_memory: bool = True

class AnalysisResponse(BaseModel):
    """Analysis response"""
    incident_id: str
    severity: str
    summary: str
    root_cause: Dict[str, Any]
    events_by_severity: Dict[str, List[Dict[str, str]]]
    recommendations: Dict[str, List[str]]
    metadata: Dict[str, Any]

class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    status: str  # "success" or "error"
    message: str
    filename: Optional[str] = None
    chunks_created: Optional[int] = None
    summary: Optional[str] = None

class IncidentSummary(BaseModel):
    """Incident summary for list view"""
    incident_id: str
    timestamp: str
    severity: str
    summary: str
    affected_services: List[str]
    events_count: int
```

---

## Phase 2: Chat & Document Services (Week 3, Days 3-5)

### 2.1 Chatbot Service

**File: `src/services/chatbot.py`**

```python
import re
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IncidentChatbot:
    """Conversational chatbot for incident analysis"""
    
    def __init__(self, llm_client, memory_manager, rag_retriever):
        self.llm = llm_client
        self.memory = memory_manager
        self.rag = rag_retriever
        self.current_incident: Optional[Dict] = None
        self.uploaded_docs: Dict[str, List[str]] = {}  # Track recent docs
        self.conversation_history: List[Dict] = []
        
    async def process_message(self, user_message: str) -> str:
        """Process user message and return bot response"""
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        user_lower = user_message.lower()
        
        # Detect user intent
        if self._is_analyze_intent(user_lower):
            return await self._handle_analyze(user_message)
        
        elif self._is_root_cause_intent(user_lower):
            return self._handle_root_cause_query()
        
        elif self._is_recommendations_intent(user_lower):
            return self._handle_recommendations_query()
        
        elif self._is_similar_intent(user_lower):
            return self._handle_similar_incidents()
        
        elif self._is_doc_search_intent(user_lower):
            query = self._extract_search_query(user_message)
            return self._handle_doc_search(query)
        
        elif self._is_doc_reference(user_lower):
            return self._handle_doc_reference(user_message)
        
        else:
            return self._handle_general_chat(user_message)
    
    async def _handle_analyze(self, user_message: str) -> str:
        """Handle incident analysis request"""
        
        # Extract logs from message
        logs = self._extract_logs(user_message)
        
        if not logs:
            return ("❓ I couldn't find logs to analyze. Please paste your incident logs:\n\n"
                   "```\n[2026-06-26 14:23:45] ERROR...\n```")
        
        try:
            # Show loading message
            logger.info(f"Analyzing incident logs (length: {len(logs)})")
            
            # Run analysis
            from src.incident_chain import IncidentAnalysisChain
            chain = IncidentAnalysisChain(self.llm, use_rag=True, use_memory=True)
            result = chain.analyze(logs)
            
            self.current_incident = result
            
            # Check if recently uploaded docs are relevant
            relevant_docs = self._check_doc_relevance(result)
            
            # Format response
            response = self._format_incident_response(result, relevant_docs)
            
            self.conversation_history.append({
                "role": "bot",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return f"❌ Error during analysis: {str(e)}\n\nPlease check your logs format."
    
    def _handle_root_cause_query(self) -> str:
        """Handle root cause question"""
        
        if not self.current_incident:
            return "❓ No incident analyzed yet. Please paste logs first."
        
        root_cause = self.current_incident.get('root_cause', {})
        primary = root_cause.get('primary_cause', 'Unknown')
        confidence = root_cause.get('confidence_level', 'Unknown')
        evidence = root_cause.get('supporting_evidence', [])
        
        response = f"""💡 **Root Cause Analysis**

**Primary Cause:** {primary}

**Confidence:** {confidence}

**Supporting Evidence:**
"""
        
        for i, ev in enumerate(evidence[:5], 1):
            response += f"{i}. {ev}\n"
        
        if len(evidence) > 5:
            response += f"\n... and {len(evidence) - 5} more pieces of evidence"
        
        return response
    
    def _handle_recommendations_query(self) -> str:
        """Handle recommendations question"""
        
        if not self.current_incident:
            return "❓ No incident analyzed yet. Please paste logs first."
        
        recs = self.current_incident.get('recommendations', {})
        
        response = "✅ **Recommended Actions**\n\n"
        
        # Immediate actions
        immediate = recs.get('immediate_actions', [])
        if immediate:
            response += "**🔴 Immediate (Now):**\n"
            for action in immediate[:3]:
                response += f"• {action}\n"
        
        # Short-term fixes
        short_term = recs.get('short_term_fixes', [])
        if short_term:
            response += "\n**🟡 Short-term (This week):**\n"
            for fix in short_term[:3]:
                response += f"• {fix}\n"
        
        # Long-term improvements
        long_term = recs.get('long_term_improvements', [])
        if long_term:
            response += "\n**🟢 Long-term (This month):**\n"
            for imp in long_term[:3]:
                response += f"• {imp}\n"
        
        return response
    
    def _handle_similar_incidents(self) -> str:
        """Handle similar incidents query"""
        
        if not self.current_incident:
            return "❓ No incident analyzed yet."
        
        # Extract keywords
        keywords = self._extract_keywords(
            self.current_incident.get('incident_summary', '')
        )
        
        # Get similar incidents from memory
        similar = self.memory.get_similar_incidents(keywords, limit=3)
        
        if not similar:
            return "📊 No similar past incidents found in memory."
        
        response = "📊 **Similar Past Incidents**\n\n"
        
        for inc in similar:
            response += f"**{inc['incident_id']}** ({inc['severity']})\n"
            response += f"Services: {', '.join(inc.get('affected_services', [])[:2])}\n"
            response += f"Root Cause: {inc.get('root_cause', 'N/A')[:100]}...\n\n"
        
        return response
    
    def _handle_doc_search(self, query: str) -> str:
        """Handle documentation search"""
        
        if not query:
            return "❓ What would you like to search for in the documentation?"
        
        try:
            context = self.rag.retrieve_and_format(query, n_results=3)
            
            if not context or "No documents found" in context:
                return f"📚 No documentation found for: '{query}'\n\nTry uploading relevant documents."
            
            response = f"📚 **Documentation Search Results for: '{query}'**\n\n{context}"
            return response
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"❌ Error searching documentation: {str(e)}"
    
    def _handle_doc_reference(self, user_message: str) -> str:
        """Handle reference to recently uploaded document"""
        
        for doc_name, chunks in self.uploaded_docs.items():
            if doc_name.lower() in user_message.lower():
                response = f"📄 **Referencing: {doc_name}**\n\n"
                response += "Key content:\n"
                for chunk in chunks[:2]:
                    response += f"• {chunk[:200]}...\n"
                return response
        
        return None
    
    def _handle_general_chat(self, user_message: str) -> str:
        """Handle general chat"""
        
        # If there's a current incident, provide context-aware response
        if self.current_incident:
            context = f"""Current Incident: {self.current_incident['incident_id']}
Severity: {self.current_incident['severity']}
Summary: {self.current_incident['incident_summary']}"""
        else:
            context = "No incident currently analyzed"
        
        # For now, return helpful guidance
        return ("💬 I'm here to help with incident analysis!\n\n"
               "You can:\n"
               "• Paste logs to analyze\n"
               "• Upload documentation\n"
               "• Ask about root causes\n"
               "• Search our documentation\n"
               "• Compare with similar incidents\n\n"
               f"Current state: {context}")
    
    def _format_incident_response(self, incident: Dict, relevant_docs: List = None) -> str:
        """Format incident analysis for chat"""
        
        response = f"""📋 **Incident Analysis Complete**

🆔 ID: {incident['incident_id']}
🔴 Severity: {incident['severity']}
📍 Status: {incident.get('status', 'INVESTIGATING')}

🏢 **Affected Services:**
{', '.join(incident.get('affected_services', [])[:5])}

📝 **Summary:**
{incident.get('incident_summary', 'N/A')}

💡 **Root Cause (Confidence: {}):**
{}

✅ **Quick Actions:**
""".format(
            incident.get('root_cause', {}).get('confidence_level', 'Unknown'),
            incident.get('root_cause', {}).get('primary_cause', 'Unknown')
        )
        
        # Add immediate actions
        immediate = incident.get('recommendations', {}).get('immediate_actions', [])
        for action in immediate[:3]:
            response += f"• {action}\n"
        
        response += "\n❓ Ask me:"
        response += "\n• What's the root cause?"
        response += "\n• What should we do?"
        response += "\n• Show me similar incidents"
        
        if relevant_docs:
            response += "\n• Relevant docs: " + ", ".join(relevant_docs)
        
        return response
    
    # Helper methods
    def _is_analyze_intent(self, text: str) -> bool:
        keywords = ['analyze', 'error', 'logs', 'incident', 'problem', 'failed', 'failure']
        return any(kw in text for kw in keywords) and len(text) > 50
    
    def _is_root_cause_intent(self, text: str) -> bool:
        return any(kw in text for kw in ['root cause', 'why', 'what caused', 'cause'])
    
    def _is_recommendations_intent(self, text: str) -> bool:
        return any(kw in text for kw in ['recommend', 'what should', 'action', 'fix', 'do'])
    
    def _is_similar_intent(self, text: str) -> bool:
        return any(kw in text for kw in ['similar', 'past', 'history', 'before', 'happened'])
    
    def _is_doc_search_intent(self, text: str) -> bool:
        return any(kw in text for kw in ['search', 'docs', 'documentation', 'guide', 'find'])
    
    def _is_doc_reference(self, text: str) -> bool:
        return any(doc.lower() in text.lower() for doc in self.uploaded_docs.keys())
    
    def _extract_logs(self, text: str) -> str:
        """Extract logs from message"""
        # Look for log format: [timestamp] level [component] message
        pattern = r'\[\d{4}-\d{2}-\d{2}.*?\]'
        if re.search(pattern, text):
            # Extract from first [ to end
            start = text.find('[')
            return text[start:]
        return ""
    
    def _extract_search_query(self, text: str) -> str:
        """Extract search query from message"""
        patterns = [
            r'search (?:for |)(.+?)(?:\.|$)',
            r'find (?:info |)(?:about |)(.+?)(?:\.|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        keywords = []
        common_terms = ['database', 'connection', 'kubernetes', 'deployment',
                       'api', 'timeout', 'memory', 'network', 'service', 'error']
        text_lower = text.lower()
        for term in common_terms:
            if term in text_lower:
                keywords.append(term)
        return keywords[:5]
    
    def _check_doc_relevance(self, incident: Dict) -> List[str]:
        """Check if uploaded docs are relevant to incident"""
        relevant = []
        summary = incident.get('incident_summary', '').lower()
        
        for doc_name in self.uploaded_docs.keys():
            if any(word in summary for word in doc_name.lower().split('_')):
                relevant.append(doc_name)
        
        return relevant
    
    def add_uploaded_doc(self, doc_name: str, chunks: List[str]):
        """Register uploaded document"""
        self.uploaded_docs[doc_name] = chunks
```

### 2.2 Document Service

**File: `src/services/document_service.py`**

```python
import os
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for managing document uploads and ingestion"""
    
    def __init__(self, doc_processor, chroma_manager):
        self.doc_processor = doc_processor
        self.chroma_manager = chroma_manager
        self.upload_dir = Path("./uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def upload_and_ingest(self, file_path: str) -> Tuple[bool, str, int]:
        """Upload and ingest a document
        
        Returns: (success, message, chunks_created)
        """
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Get filename
            filename = os.path.basename(file_path)
            
            # Process document
            chunks = self.doc_processor.load_and_chunk_document(file_path)
            
            if not chunks:
                return False, f"No content extracted from {filename}", 0
            
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Add to ChromaDB
            self.chroma_manager.add_chunks(chunks)
            
            logger.info(f"Successfully ingested {filename} ({len(chunks)} chunks)")
            
            return True, f"✅ Successfully ingested {filename}", len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False, f"❌ Error: {str(e)}", 0
    
    async def reload_all_documents(self) -> Tuple[bool, str, int]:
        """Reload all documents from docs/ directory"""
        
        try:
            docs_dir = Path("./docs")
            
            if not docs_dir.exists():
                return False, "docs/ directory not found", 0
            
            # Reset ChromaDB
            self.chroma_manager.reset_collection()
            
            total_chunks = 0
            
            # Process all documents
            for file_path in docs_dir.glob("*"):
                if file_path.suffix in ['.txt', '.md', '.pdf']:
                    success, _, chunks = await self.upload_and_ingest(str(file_path))
                    if success:
                        total_chunks += chunks
            
            return True, f"✅ Reloaded all documents", total_chunks
            
        except Exception as e:
            logger.error(f"Error reloading documents: {e}")
            return False, f"❌ Error: {str(e)}", 0
    
    def get_collection_stats(self) -> dict:
        """Get ChromaDB collection statistics"""
        return self.chroma_manager.get_stats()
```

---

## Phase 3: API Routes (Week 3, Days 4-5)

### 3.1 Chat Route

**File: `src/api/routes/chat.py`**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.api.main import chatbot
import logging

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    logger.info("✅ Chat connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"User message: {data[:100]}...")
            
            # Process message
            response = await chatbot.process_message(data)
            
            # Send response back
            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        logger.info("❌ Chat connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(f"❌ Error: {str(e)}")
```

### 3.2 Documents Route

**File: `src/api/routes/documents.py`**

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.main import chatbot
from src.services.document_service import DocumentService
from src.document_processor import DocumentProcessor
from src.chroma_db_manager import ChromaDBManager
import logging
import tempfile
import os

router = APIRouter(prefix="/api/v1", tags=["documents"])
logger = logging.getLogger(__name__)

doc_processor = DocumentProcessor()
chroma_manager = ChromaDBManager()
doc_service = DocumentService(doc_processor, chroma_manager)

@router.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a new document"""
    
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Validate file
        if file.size > 50_000_000:  # 50MB max
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        allowed_types = ['.txt', '.pdf', '.md', '.docx']
        if not any(file.filename.endswith(t) for t in allowed_types):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Process document
        success, message, chunks = await doc_service.upload_and_ingest(tmp_path)
        
        # Cleanup temp file
        os.unlink(tmp_path)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Register with chatbot
        # Extract first few chunks as preview
        from src.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        doc_chunks = processor.load_and_chunk_document(file.filename)
        chunk_texts = [c.content[:100] for c in doc_chunks[:3]]
        chatbot.add_uploaded_doc(file.filename, chunk_texts)
        
        return {
            "status": "success",
            "message": message,
            "filename": file.filename,
            "chunks_created": chunks,
            "suggestion": f"📎 {file.filename} is now available. Ask me anything about it!"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List all ingested documents"""
    try:
        stats = doc_service.get_collection_stats()
        return {
            "status": "success",
            "documents": stats
        }
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/reload")
async def reload_documents():
    """Reload all documents from docs/ folder"""
    try:
        success, message, chunks = await doc_service.reload_all_documents()
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "status": "success",
            "message": message,
            "total_chunks": chunks
        }
        
    except Exception as e:
        logger.error(f"Reload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.3 Incidents Route

**File: `src/api/routes/incidents.py`**

```python
from fastapi import APIRouter, HTTPException
from src.api.main import memory_manager
from src.api.models import IncidentSummary
from typing import List
import logging

router = APIRouter(prefix="/api/v1", tags=["incidents"])
logger = logging.getLogger(__name__)

@router.get("/incidents", response_model=dict)
async def list_incidents(limit: int = 20, skip: int = 0):
    """List all incidents"""
    try:
        incidents = memory_manager.long_term['incidents']
        
        summaries = []
        for inc in incidents[skip:skip+limit]:
            events = inc.get('events_by_severity', {})
            event_count = sum(len(events.get(s, [])) for s in ['CRITICAL', 'ERROR', 'WARN', 'INFO'])
            
            summaries.append({
                "incident_id": inc['incident_id'],
                "timestamp": inc.get('incident_timestamp', 'N/A'),
                "severity": inc['severity'],
                "summary": inc.get('root_cause', 'N/A')[:100],
                "affected_services": inc.get('affected_services', [])[:3],
                "events_count": event_count
            })
        
        return {
            "status": "success",
            "total": len(incidents),
            "incidents": summaries
        }
        
    except Exception as e:
        logger.error(f"List incidents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get specific incident details"""
    try:
        for inc in memory_manager.long_term['incidents']:
            if inc['incident_id'] == incident_id:
                return {
                    "status": "success",
                    "incident": inc
                }
        
        raise HTTPException(status_code=404, detail="Incident not found")
        
    except Exception as e:
        logger.error(f"Get incident error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """Get overall statistics"""
    try:
        incidents = memory_manager.long_term['incidents']
        
        return {
            "status": "success",
            "total_incidents": len(incidents),
            "critical_count": sum(1 for i in incidents if i['severity'] == 'CRITICAL'),
            "services_affected": len(set(s for i in incidents for s in i.get('affected_services', []))),
            "memory_stats": memory_manager.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Phase 4: Frontend (Week 4, Days 1-3)

### 4.1 Project Setup

```bash
cd web
npm create vite@latest . -- --template vue
npm install
npm install axios markdown-it dompurify
```

### 4.2 Main Chatbox Component

**File: `web/src/components/ChatBox.vue`**

```vue
<template>
  <div class="chatbox-container">
    <!-- Messages Area -->
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx" 
        :class="['message', msg.role]"
      >
        <div class="message-content" v-html="formatMessage(msg.content)"></div>
        <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
      </div>
    </div>
    
    <!-- Upload Zone -->
    <div 
      @drop="handleDrop" 
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      :class="['upload-zone', { dragging: isDragging }]"
    >
      <input 
        type="file" 
        @change="handleFileSelect" 
        accept=".txt,.pdf,.md,.docx"
        multiple
        ref="fileInput"
        class="file-input"
      />
      
      <div v-if="!files.length" class="upload-prompt">
        <p class="upload-icon">📎</p>
        <p class="upload-text">Drop documents here or click to upload</p>
        <p class="upload-hint">Supports: .txt, .pdf, .md, .docx (Max 50MB each)</p>
      </div>
      
      <div v-else class="file-list">
        <div v-for="file in files" :key="file.name" class="file-item">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">({{ formatFileSize(file.size) }})</span>
          <button @click="removeFile(file.name)" class="remove-btn">×</button>
        </div>
      </div>
    </div>
    
    <!-- Input Area -->
    <div class="input-area">
      <textarea 
        v-model="input" 
        @keydown.enter.ctrl="sendMessage"
        @keydown.enter.meta="sendMessage"
        placeholder="Paste incident logs, ask questions, or describe your issue..."
        class="chat-input"
      ></textarea>
      
      <div class="button-group">
        <button 
          @click="uploadFiles" 
          :disabled="!files.length || uploading"
          class="btn btn-upload"
          title="Upload documents"
        >
          {{ uploading ? '📤 Uploading...' : `📎 Upload (${files.length})` }}
        </button>
        <button 
          @click="sendMessage" 
          :disabled="!input.trim() || sending"
          class="btn btn-send"
          title="Send message (Ctrl+Enter)"
        >
          {{ sending ? '⏳ Sending...' : '▶ Send' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { marked } from 'markdown-it'
import DOMPurify from 'dompurify'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const messages = ref([
  { 
    role: 'bot', 
    content: 'Hi! 👋 I\'m your incident analysis assistant.\n\n**You can:**\n• Paste incident logs to analyze\n• Upload documentation\n• Ask questions about incidents\n• Search our knowledge base',
    timestamp: new Date()
  }
])
const input = ref('')
const files = ref([])
const sending = ref(false)
const uploading = ref(false)
const isDragging = ref(false)
const ws = ref(null)
const messagesContainer = ref(null)
const fileInput = ref(null)

const connect = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/chat`
  
  ws.value = new WebSocket(wsUrl)
  
  ws.value.onopen = () => {
    console.log('✅ Chat connected')
  }
  
  ws.value.onmessage = (event) => {
    messages.value.push({ 
      role: 'bot', 
      content: event.data,
      timestamp: new Date()
    })
    sending.value = false
    scrollToBottom()
  }
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    messages.value.push({
      role: 'bot',
      content: '❌ Connection error. Please refresh the page.',
      timestamp: new Date()
    })
  }
  
  ws.value.onclose = () => {
    console.log('❌ Chat disconnected')
  }
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const droppedFiles = Array.from(e.dataTransfer.files)
  files.value = [...files.value, ...droppedFiles]
}

const handleFileSelect = (e) => {
  files.value = [...files.value, ...Array.from(e.target.files)]
}

const removeFile = (name) => {
  files.value = files.value.filter(f => f.name !== name)
}

const uploadFiles = async () => {
  if (!files.value.length) return
  
  uploading.value = true
  
  for (const file of files.value) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      messages.value.push({
        role: 'user',
        content: `📎 Uploading: ${file.name}`,
        timestamp: new Date()
      })
      
      const response = await axios.post(`${API_URL}/api/v1/upload-doc`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      messages.value.push({
        role: 'bot',
        content: response.data.message || '✅ Document uploaded successfully',
        timestamp: new Date()
      })
      
    } catch (error) {
      messages.value.push({
        role: 'bot',
        content: `❌ Error uploading ${file.name}: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date()
      })
    }
  }
  
  files.value = []
  uploading.value = false
  scrollToBottom()
}

const sendMessage = () => {
  if (!input.value.trim() || !ws.value) return
  
  const userMessage = input.value
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })
  
  ws.value.send(userMessage)
  input.value = ''
  sending.value = true
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatMessage = (text) => {
  // Simple markdown support
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
  
  return DOMPurify.sanitize(html)
}

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  connect()
  scrollToBottom()
})
</script>

<style scoped>
.chatbox-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: white;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8f9fa;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 80%;
  animation: slideIn 0.3s ease-in-out;
}

.message.user {
  align-self: flex-end;
}

.message.bot {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.4;
}

.message.user .message-content {
  background: #007bff;
  color: white;
}

.message.bot .message-content {
  background: white;
  color: #333;
  border: 1px solid #ddd;
}

.message-time {
  font-size: 12px;
  color: #666;
  padding: 0 16px;
}

.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 20px;
  margin: 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.upload-zone.dragging {
  border-color: #007bff;
  background: #e7f3ff;
}

.upload-zone .file-input {
  display: none;
}

.upload-prompt {
  cursor: pointer;
}

.upload-icon {
  font-size: 32px;
  margin: 0;
}

.upload-text {
  margin: 8px 0 4px 0;
  font-weight: 500;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #666;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f3f5;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
}

.file-icon {
  font-size: 16px;
}

.file-name {
  flex: 1;
  text-align: left;
}

.file-size {
  font-size: 12px;
  color: #666;
}

.remove-btn {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.input-area {
  padding: 15px;
  border-top: 1px solid #ddd;
  background: white;
}

.chat-input {
  width: 100%;
  min-height: 60px;
  max-height: 120px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 10px;
}

.chat-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-upload {
  background: #6c757d;
  color: white;
}

.btn-upload:hover:not(:disabled) {
  background: #5a6268;
}

.btn-send {
  background: #007bff;
  color: white;
}

.btn-send:hover:not(:disabled) {
  background: #0056b3;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .message {
    max-width: 95%;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
```

### 4.3 App Layout

**File: `web/src/App.vue`**

```vue
<template>
  <div class="app">
    <header class="header">
      <div class="header-content">
        <h1>🚨 Incident Response Assistant</h1>
        <p>AI-powered analysis with document ingestion</p>
      </div>
      <nav class="nav">
        <button @click="currentPage = 'chat'" :class="{ active: currentPage === 'chat' }">
          💬 Chat
        </button>
        <button @click="currentPage = 'history'" :class="{ active: currentPage === 'history' }">
          📋 History
        </button>
        <button @click="currentPage = 'docs'" :class="{ active: currentPage === 'docs' }">
          📚 Docs
        </button>
        <button @click="currentPage = 'stats'" :class="{ active: currentPage === 'stats' }">
          📊 Stats
        </button>
      </nav>
    </header>

    <main class="main-content">
      <ChatBox v-if="currentPage === 'chat'" />
      <HistoryView v-else-if="currentPage === 'history'" />
      <DocsView v-else-if="currentPage === 'docs'" />
      <StatsView v-else-if="currentPage === 'stats'" />
    </main>

    <footer class="footer">
      <p>Incident Response Assistant v2.0 | Powered by Claude</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatBox from './components/ChatBox.vue'
import HistoryView from './views/HistoryView.vue'
import DocsView from './views/DocsView.vue'
import StatsView from './views/StatsView.vue'

const currentPage = ref('chat')
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  background: #f5f7fa;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: white;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  margin-bottom: 15px;
}

.header-content h1 {
  font-size: 24px;
  margin-bottom: 4px;
}

.header-content p {
  font-size: 14px;
  opacity: 0.9;
}

.nav {
  display: flex;
  gap: 10px;
}

.nav button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.nav button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.nav button.active {
  background: white;
  color: #667eea;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.footer {
  background: #f8f9fa;
  color: #666;
  padding: 12px;
  text-align: center;
  font-size: 12px;
  border-top: 1px solid #ddd;
}
</style>
```

---

## Phase 5: Deployment & Testing (Week 4, Days 4-5)

### 5.1 Docker Setup

**Dockerfile (Backend)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY docs/ ./docs/

ENV USE_RAG=true
ENV USE_MEMORY=true
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile (Frontend)**
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY web/package*.json ./
RUN npm ci

COPY web/ .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    volumes:
      - ./memory:/app/memory
      - ./chroma_db:/app/chroma_db
      - ./docs:/app/docs
      - ./uploads:/app/uploads
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      USE_RAG: "true"
      USE_MEMORY: "true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "80:80"
    environment:
      VITE_API_URL: http://api:8000
    depends_on:
      - api
```

### 5.2 Environment Configuration

**File: `.env.example`**

```
# Backend
ANTHROPIC_API_KEY=your_key_here
USE_RAG=true
USE_MEMORY=true
LOG_LEVEL=INFO

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Implementation Checklist

### Week 3
- [ ] Day 1-2: Backend API structure & FastAPI setup
  - [ ] `src/api/main.py` - Main app
  - [ ] `src/api/models.py` - Pydantic models
  - [ ] Project layout

- [ ] Day 3-4: Chat & Document Services
  - [ ] `src/services/chatbot.py` - Chatbot logic
  - [ ] `src/services/document_service.py` - Document ingestion
  - [ ] Intent detection

- [ ] Day 4-5: API Routes
  - [ ] `src/api/routes/chat.py` - WebSocket chat
  - [ ] `src/api/routes/documents.py` - File upload
  - [ ] `src/api/routes/incidents.py` - Query incidents

### Week 4
- [ ] Day 1-2: Frontend Setup
  - [ ] Vue.js project setup
  - [ ] `ChatBox.vue` component
  - [ ] File upload handling

- [ ] Day 2-3: Navigation & Views
  - [ ] `App.vue` layout
  - [ ] History view
  - [ ] Docs view
  - [ ] Stats view

- [ ] Day 4-5: Deployment
  - [ ] Docker setup
  - [ ] docker-compose
  - [ ] Local testing
  - [ ] Documentation

---

## Key Features Checklist

### Chat Features
- [ ] WebSocket real-time chat
- [ ] Intent detection (analyze, search, recommendations)
- [ ] Context-aware responses
- [ ] Conversation history
- [ ] Message formatting (markdown)

### Document Ingestion
- [ ] Drag & drop file upload
- [ ] Support for .txt, .pdf, .md, .docx
- [ ] Automatic chunking & embedding
- [ ] ChromaDB integration
- [ ] Document preview/search

### Integration
- [ ] RAG context in responses
- [ ] Memory system integration
- [ ] Service-level event tracking
- [ ] Dual timestamp system
- [ ] Source attribution

### User Experience
- [ ] Responsive design
- [ ] Loading states
- [ ] Error messages
- [ ] Success notifications
- [ ] Smooth animations

---

## Testing Plan

### Unit Tests
```bash
pytest tests/test_chatbot.py
pytest tests/test_document_service.py
```

### Integration Tests
```bash
pytest tests/api/test_routes.py
```

### Manual Testing
1. Upload document → Verify chunks created
2. Ask question → Verify RAG retrieval
3. Check history → Verify memory persistence
4. Multiple users → Verify WebSocket isolation

### Performance Testing
- [ ] Document upload <5s for 10MB
- [ ] Chat response <2s average
- [ ] RAG retrieval <500ms
- [ ] Concurrent users: 10+ simultaneous

---

## Success Metrics

✅ **Week 3 Complete:**
- FastAPI backend running
- WebSocket chat working
- Document upload functional
- All routes tested

✅ **Week 4 Complete:**
- Frontend chatbox working
- All views functional
- Docker deployment working
- Ready for production

---

## Next Steps (Week 5+)

- [ ] Add authentication/user management
- [ ] Implement conversation persistence
- [ ] Add export (PDF reports)
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Team collaboration features
- [ ] Slack/Teams integration

---

This comprehensive plan provides everything needed to deploy a production-ready incident response system with intelligent chatbox and dynamic document ingestion! 🚀
