# Local Docker Setup Guide

Run the entire application using Docker Compose - the easiest way to get everything running locally.

## What is Docker?

Docker is a containerization platform that packages your application with all dependencies into a single unit. You don't need to install Python, Node.js, or manage dependencies - Docker handles everything.

**Benefits:**
- ✅ No need to install Python, Node.js separately
- ✅ Works exactly the same on all machines
- ✅ No dependency conflicts
- ✅ One command to start everything
- ✅ Easy to stop and clean up

---

## Prerequisites

### What You Need

1. **Docker Desktop** (includes Docker & Docker Compose)
   - macOS: https://www.docker.com/products/docker-desktop
   - Windows: https://www.docker.com/products/docker-desktop
   - Linux: https://docs.docker.com/engine/install/

2. **API Key** (Anthropic or OpenAI)
   - Get from: https://console.anthropic.com/ or https://platform.openai.com/api-keys

That's it! No Python, Node.js, or other installations needed.

### Verify Docker Installation

```bash
docker --version
# Output: Docker version 20.10.x or higher

docker-compose --version
# Output: Docker Compose version 2.x or higher
```

---

## Step 1: Setup Environment File

Navigate to project directory:
```bash
cd /home/coder/myProject/enterprise-incident-response-agent
```

Create `.env` file from template:
```bash
cp .env.example .env
```

Edit `.env` with your API key:
```bash
nano .env
# or: vim .env
# or: open in your text editor
```

Add **ONE** of these options:

**Option A: Anthropic (Recommended)**
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
DEFAULT_PROVIDER=anthropic
USE_RAG=true
USE_MEMORY=true
```

**Option B: OpenAI**
```
OPENAI_API_KEY=sk-your-actual-key-here
DEFAULT_PROVIDER=openai
USE_RAG=true
USE_MEMORY=true
```

Save and exit.

---

## Step 2: Build Docker Images (First Time Only)

```bash
cd /home/coder/myProject/enterprise-incident-response-agent

docker-compose build

# This will:
# - Download base images (Python 3.10, Node 18, Nginx)
# - Install Python dependencies
# - Install Node dependencies
# - Build React app
# - Create two Docker images: api and web
#
# Takes 2-5 minutes the first time
```

You'll see output like:
```
Step 1/10 : FROM python:3.10-slim
Step 2/10 : WORKDIR /app
...
Successfully built abc123def456
```

---

## Step 3: Start All Services with Docker Compose

```bash
docker-compose up -d

# The -d flag runs in detached mode (background)
# Services will start automatically
```

You'll see:
```
Creating incident-response-agent_api_1 ... done
Creating incident-response-agent_web_1 ... done
```

### What Just Happened:

1. **API Container** (Backend)
   - FastAPI server running on `localhost:8000`
   - WebSocket endpoint at `localhost:8000/ws/chat`
   - Python dependencies installed
   - Memory and RAG systems ready

2. **Web Container** (Frontend)
   - React app running on `localhost:3000`
   - Nginx reverse proxy
   - Automatically routes API calls to backend

---

## Step 4: Verify Services Are Running

### Check Container Status

```bash
docker-compose ps

# Output should show:
# NAME                              STATUS              PORTS
# incident-response-agent_api_1     Up 2 minutes        0.0.0.0:8000->8000/tcp
# incident-response-agent_web_1     Up 2 minutes        0.0.0.0:3000->3000/tcp
```

### Check Backend Health

```bash
curl http://localhost:8000/api/health

# Should return:
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "memory": "ok",
    "rag": "ok",
    "llm": "ok"
  }
}
```

### Check Frontend

Open browser: **http://localhost:3000**

You should see:
- Header: "Enterprise Incident Response Agent"
- Green dot: "Connected"
- Sidebar with stats
- Chat interface
- Upload zone

---

## Step 5: Test the Application

### Test 1: Send a Message

1. Click the chat textarea
2. Type: `"Database connection failed - how to fix?"`
3. Press Enter
4. Wait 3-5 seconds for response

Expected: Bot responds with incident analysis

### Test 2: Upload Document

```bash
# Create test document
echo "Connection Pool Management

When pool is exhausted:
1. Check active connections
2. Identify long queries
3. Increase pool size" > /tmp/test_doc.txt
```

In browser:
1. Drag `/tmp/test_doc.txt` to upload zone (or click to select)
2. Should appear in "Uploaded Documents"

### Test 3: Check Stats

Watch sidebar (updates every 5 seconds):
- Messages increase
- Memory usage shown
- Backup count visible

---

## Common Docker Compose Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f web

# Last 50 lines
docker-compose logs --tail=50

# Exit: Ctrl+C
```

### Stop Services

```bash
# Stop but keep containers
docker-compose stop

# Stop and remove containers (but keep volumes/data)
docker-compose down

# Stop, remove everything including volumes
docker-compose down -v
```

### Restart Services

```bash
# Restart specific service
docker-compose restart api
docker-compose restart web

# Restart all services
docker-compose restart
```

### Rebuild Images

```bash
# Rebuild without cache (clean build)
docker-compose build --no-cache

# Then restart
docker-compose up -d
```

---

## Accessing Services

### Frontend (React App)
```
http://localhost:3000
```

### Backend API
```
http://localhost:8000
```

### Swagger API Documentation
```
http://localhost:8000/docs
```

### API Endpoints (via curl)

```bash
# Health check
curl http://localhost:8000/api/health

# Get stats
curl http://localhost:8000/api/stats

# Get incidents
curl http://localhost:8000/api/incidents

# Get chat history
curl http://localhost:8000/api/chat/history

# List backups
curl http://localhost:8000/api/backups
```

---

## File Persistence (Docker Volumes)

Your data is stored in Docker volumes (managed by Docker):

```bash
# View volumes
docker volume ls

# See volume details
docker inspect incident-response-agent_memory
```

Data persists even if you stop/restart containers:
- `memory/` - Incident history, backups
- `chroma_db/` - Vector embeddings
- `docs/` - Uploaded documents

To delete all data:
```bash
docker-compose down -v
```

---

## Editing Code in Docker

Docker runs a **read-only copy** of your code. Changes on your machine won't automatically appear.

### Option 1: Restart Container to Pick Up Changes (Recommended)

```bash
# Stop all services
docker-compose down

# Make your code changes
# Edit files as needed

# Restart everything
docker-compose build
docker-compose up -d
```

### Option 2: Run Locally Instead

If you want hot-reload (changes apply instantly), use the manual local setup instead:
- See: `LOCAL_SETUP_GUIDE.md`

### Option 3: Mount Code as Volume (Advanced)

Edit `docker-compose.yml` to mount local code:

```yaml
services:
  api:
    volumes:
      - ./src:/app/src          # Mount backend code
      - ./memory:/app/memory    # Keep data volume

  web:
    volumes:
      - ./frontend/src:/app/src # Mount frontend code
```

Then:
```bash
docker-compose up -d
```

Now changes on your machine appear in Docker immediately (still need to restart services for full effect).

---

## Troubleshooting

### Problem: Containers won't start

```bash
# Check logs
docker-compose logs

# Look for error messages
# Common: API key missing or invalid
```

**Solution:**
```bash
# Verify .env file
cat .env | grep -E "OPENAI|ANTHROPIC|DEFAULT_PROVIDER"

# Restart
docker-compose down
docker-compose up -d
```

### Problem: Red dot (disconnected)

```bash
# Check API health
curl http://localhost:8000/api/health

# Check container status
docker-compose ps

# View API logs
docker-compose logs api
```

**Solution:**
```bash
# Restart containers
docker-compose restart
```

### Problem: Port already in use

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports in docker-compose.yml
# Change: ports: "3000:3000" to "3001:3000"
```

### Problem: "Cannot connect to Docker daemon"

Make sure Docker Desktop is running.

```bash
# Check Docker status
docker ps

# If error: Start Docker Desktop
# macOS: open /Applications/Docker.app
# Windows: Open Docker Desktop from Start Menu
```

### Problem: Out of disk space

Docker images and volumes take space. Clean up:

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# See what's taking space
docker system df
```

### Problem: Changes in code not reflecting

Remember: Docker runs a frozen copy of code.

**Solution:**
```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Problem: Database/Memory corrupted

Reset everything:

```bash
# Delete everything including data
docker-compose down -v

# Rebuild fresh
docker-compose build
docker-compose up -d
```

---

## Docker Compose File Structure

```yaml
version: '3.8'

services:
  api:
    build:                      # Build from Dockerfile.api
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"            # Port mapping: host:container
    environment:                # Pass environment variables
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:                    # Mount directories
      - ./memory:/app/memory
      - ./chroma_db:/app/chroma_db
    healthcheck:                # Check if service is healthy
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "3000:3000"
    depends_on:                 # Wait for api to start first
      - api
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/"]

networks:
  incident-response:           # Network for inter-container communication
    driver: bridge

volumes:
  memory:
  chroma_db:
```

---

## Docker Commands Quick Reference

```bash
# Build images
docker-compose build

# Start services (detached)
docker-compose up -d

# Start services (foreground, see logs)
docker-compose up

# View logs
docker-compose logs -f

# View status
docker-compose ps

# Stop services
docker-compose stop

# Stop and remove
docker-compose down

# Restart services
docker-compose restart

# Execute command in container
docker-compose exec api bash

# View specific logs
docker-compose logs api | tail -100

# Remove everything including volumes
docker-compose down -v
```

---

## Development Workflow with Docker

```bash
# 1. Initial setup
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Test in browser
open http://localhost:3000

# 4. View logs while testing
docker-compose logs -f

# 5. Edit code locally
nano src/api/main.py
# or edit frontend files

# 6. Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# 7. Verify changes work
curl http://localhost:8000/api/health

# 8. When done
docker-compose down
```

---

## Container Resource Management

### Limit Container Resources

Edit `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'            # 1 CPU core max
          memory: 1G           # 1GB RAM max
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Monitor Resource Usage

```bash
# Real-time stats
docker stats

# One-time report
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Debugging in Docker

### Access Container Shell

```bash
# Backend container
docker-compose exec api bash

# Inside container:
# $ ls -la          # List files
# $ pip list        # Check Python packages
# $ python -c "import fastapi" # Test imports
# $ exit            # Exit container
```

### Check Container Details

```bash
# Inspect container
docker-compose config

# View container environment
docker-compose exec api env

# Check mounted volumes
docker volume inspect incident-response-agent_memory
```

---

## Performance Tips

1. **First Run:** Build takes 2-5 minutes - be patient
2. **Subsequent Runs:** Start in ~10 seconds
3. **Memory:** Allocate at least 2GB to Docker
4. **CPU:** Use at least 2 cores

### Improve Build Speed

```bash
# Use BuildKit (faster builds)
DOCKER_BUILDKIT=1 docker-compose build
```

---

## Switching Between Docker and Local

### To Use Docker:
```bash
docker-compose up -d
# Visit: http://localhost:3000
```

### To Use Local Setup:
```bash
# Stop Docker
docker-compose down

# Run locally
source venv/bin/activate
python -m uvicorn src.api.main:app --reload

# In another terminal
cd frontend && npm start
# Visit: http://localhost:3000
```

Both run on the same ports and ports so you can easily switch.

---

## Production vs Local Docker

**Local Docker (this guide):**
- Uses `docker-compose.yml`
- Automatic rebuild from source
- Volumes for data persistence
- Easy to stop/restart
- Good for development and testing

**Production Docker:**
- Pre-built images pushed to registry
- Read-only containers
- External database
- Load balancing
- Advanced deployment (see `DEPLOYMENT.md`)

---

## Cleanup

### Remove Everything (Keep data)

```bash
docker-compose stop
docker-compose down
```

### Complete Reset (Delete all data)

```bash
docker-compose down -v
```

### Remove Images

```bash
docker image rm incident-response-agent:api
docker image rm incident-response-agent:web
```

---

## FAQ

**Q: Do I need to install Python or Node.js?**
A: No! Docker handles everything.

**Q: Can I modify code?**
A: Yes, but need to rebuild: `docker-compose build` then `docker-compose up -d`

**Q: Does data persist?**
A: Yes, in Docker volumes. Lost only if you run `docker-compose down -v`

**Q: How do I add new Python packages?**
A: Edit `requirements.txt`, then rebuild: `docker-compose build`

**Q: How do I add new Node packages?**
A: Edit `frontend/package.json`, then rebuild: `docker-compose build`

**Q: Can I run frontend separately?**
A: No, frontend depends on backend. Use `docker-compose up -d` for both.

**Q: Is Docker slower than local?**
A: Negligible difference for development. Docker adds ~5-10% overhead.

---

## Next Steps

1. **Verify Setup:**
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/health
   ```

2. **Test Application:**
   - Open http://localhost:3000
   - Send message
   - Upload document

3. **Check Logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Edit Code (if needed):**
   - Edit files locally
   - Run: `docker-compose build && docker-compose up -d`

5. **Stop When Done:**
   ```bash
   docker-compose down
   ```

---

## Getting Help

### Check Logs
```bash
docker-compose logs -f
```

### Check Status
```bash
docker-compose ps
```

### See All Commands
```bash
docker-compose --help
```

### Read Documentation
- Docker Compose: https://docs.docker.com/compose/
- Docker Desktop: https://www.docker.com/products/docker-desktop
- This guide: `LOCAL_DOCKER_SETUP.md`

---

**Ready to start with Docker?** Just run:

```bash
cd /home/coder/myProject/enterprise-incident-response-agent
docker-compose up -d
open http://localhost:3000
```

That's it! 🚀
