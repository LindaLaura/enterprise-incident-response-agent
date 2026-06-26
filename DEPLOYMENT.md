# Web Interface & Deployment Guide

## Overview

Production-ready React web interface with FastAPI backend, WebSocket real-time chat, drag-drop document ingestion, and Docker containerization.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├────────────────────────┬──────────────────────────────────┤
│                        │                                  │
│   Web (React)          │      API (FastAPI)              │
│   Port: 3000           │      Port: 8000                 │
│   ├─ Nginx proxy       │      ├─ WebSocket (/ws/chat)   │
│   ├─ Static files      │      ├─ REST API (/api/*)       │
│   └─ React SPA         │      ├─ Document upload         │
│                        │      ├─ Memory manager          │
│                        │      ├─ RAG retriever           │
│                        │      └─ LLM client              │
│                        │                                  │
│                        ├─ Volumes:                       │
│                        │   - memory/                     │
│                        │   - chroma_db/                  │
│                        │   - docs/                       │
└────────────────────────┴──────────────────────────────────┘
```

## Prerequisites

- Docker & Docker Compose
- OpenAI API key OR Anthropic API key
- ~4GB RAM, 2 CPU cores

## Local Development Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run Backend (Dev)

```bash
python -m uvicorn src.api.main:app --reload
# API available at http://localhost:8000
```

### 5. Run Frontend (Dev)

```bash
cd frontend
npm start
# App available at http://localhost:3000
```

## Docker Deployment

### 1. Build Containers

```bash
docker-compose build
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services

```bash
docker-compose up -d
```

Services will be available at:
- **Web UI:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f web
```

### 5. Stop Services

```bash
docker-compose down
```

## Production Deployment

### AWS EC2

1. **Launch Instance**
   ```bash
   # t3.medium (2 vCPU, 4GB RAM)
   ami-0c55b159cbfafe1f0  # Ubuntu 22.04 LTS
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker ec2-user
   ```

3. **Clone Repository**
   ```bash
   git clone <your-repo> /opt/incident-response
   cd /opt/incident-response
   ```

4. **Configure Environment**
   ```bash
   # Set API keys in .env
   nano .env
   ```

5. **Deploy**
   ```bash
   docker-compose up -d
   ```

6. **Setup Monitoring**
   ```bash
   # Check health
   curl http://localhost:8000/api/health
   ```

### Kubernetes

```yaml
# Example: k8s deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: incident-response-api
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: api
        image: incident-response:api
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
```

## API Endpoints

### REST API

- `GET /api/health` - Health check
- `GET /api/stats` - System statistics
- `GET /api/incidents` - List recent incidents
- `GET /api/backups` - List backups
- `POST /api/backups/restore/{index}` - Restore backup
- `POST /api/documents/upload` - Upload document
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat

### WebSocket

- `WS /ws/chat` - Real-time chat connection

Messages:
```json
{
  "type": "message",
  "content": "Describe incident...",
  "timestamp": "2026-06-26T..."
}
```

## Frontend Features

### Chat Interface
- Real-time WebSocket communication
- Message history with timestamps
- Auto-scroll to latest messages
- Loading indicators
- Error handling

### Document Upload
- Drag-and-drop interface
- Multiple file support
- Supported formats: .txt, .pdf, .md, .docx, .log
- Upload progress tracking
- File chunk management

### Sidebar
- System statistics
- Recent incidents
- Memory usage tracking
- Clear chat button
- Connection status

### Header
- Connection status indicator
- Live statistics display
- System health monitoring

## Development

### Project Structure

```
.
├── frontend/                 # React web app
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
│
├── src/
│   ├── api/                  # FastAPI backend
│   │   └── main.py
│   ├── services/             # Business logic
│   │   └── chatbot.py
│   ├── memory_manager.py     # Memory persistence
│   ├── rag_retriever.py      # RAG system
│   └── ...
│
├── docker-compose.yml        # Multi-container setup
├── Dockerfile.api            # Backend image
├── Dockerfile.web            # Frontend image
└── nginx.conf               # Web server config
```

### Adding Features

**1. Backend Endpoint:**
```python
# src/api/main.py
@app.get("/api/custom")
async def custom_endpoint():
    return {"data": "value"}
```

**2. Frontend Component:**
```jsx
// frontend/src/components/Custom.js
function Custom() {
  return <div>Component</div>;
}
export default Custom;
```

## Troubleshooting

### WebSocket Connection Failed
- Check backend is running: `curl http://localhost:8000/api/health`
- Check proxy configuration in nginx.conf
- Check browser console for errors

### Document Upload Fails
- Verify file format is supported
- Check file size (<100MB recommended)
- Check disk space in container

### API Returns 500 Error
- Check server logs: `docker-compose logs api`
- Verify environment variables are set
- Check API keys are valid

### Memory Issues
- Check container resource limits
- Monitor with: `docker stats`
- Review memory_manager logs

## Performance Optimization

### Frontend
- Code splitting for faster loads
- Image compression
- Caching strategy in nginx.conf

### Backend
- Connection pooling for LLM clients
- Async WebSocket handling
- Memory cleanup (auto-truncation)
- Backup rotation (7-day retention)

### Database
- ChromaDB indexing
- Memory file compression (future)

## Security

### Authentication
- Add JWT tokens for production
- Implement role-based access control
- Rate limiting on upload endpoint

### Data Protection
- Enable HTTPS/TLS
- Encrypt API keys in environment
- Backup encryption
- Data retention policies

### Network
- Run behind reverse proxy (nginx)
- Restrict WebSocket connections
- Validate file uploads

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/health

# Web server health
curl http://localhost:3000/

# System stats
curl http://localhost:8000/api/stats
```

### Metrics to Track

- API response time
- WebSocket connection count
- Document upload success rate
- Memory usage growth
- Backup creation frequency
- Chat message rate

### Logs

```bash
# Docker logs
docker-compose logs --tail=100 -f

# Specific service
docker-compose logs -f api
```

## Backup & Recovery

### Automatic Backups
- Created before each memory save
- 7-day retention (configurable)
- Stored in `memory/backups/`

### Manual Restore
```bash
# Via API
curl -X POST http://localhost:8000/api/backups/restore/0

# Or through web UI
# Settings → Backups → Restore
```

## Scaling

### Horizontal Scaling (Kubernetes)
- Load balance API servers
- Shared memory backend (Redis/PostgreSQL)
- Session affinity for WebSocket

### Vertical Scaling
- Increase container resource limits
- Optimize LLM model selection
- Increase backup retention
- Archive old incidents

## Maintenance

### Daily
- Monitor health checks
- Check error logs
- Verify backups created

### Weekly
- Clean old backups (automated)
- Review memory usage
- Check storage space

### Monthly
- Archive old incidents
- Update dependencies
- Security patches

## Support & Debugging

Enable debug logging:
```python
# src/api/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Common issues:
- **Port already in use:** Change in docker-compose.yml
- **Out of memory:** Reduce max_conversation_history
- **Slow uploads:** Check network, file size
- **WebSocket timeouts:** Increase proxy timeout

---

**Ready to deploy!** 🚀
