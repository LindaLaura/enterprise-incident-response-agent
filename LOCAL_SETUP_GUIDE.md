# Local Development Setup Guide

Complete step-by-step instructions to run the Enterprise Incident Response Agent on your local machine.

## Prerequisites

### What You Need Installed

1. **Python 3.10+**
   ```bash
   python --version
   # Should output: Python 3.10.x or higher
   ```
   Install from: https://www.python.org/downloads/

2. **Node.js 18+**
   ```bash
   node --version
   npm --version
   # Should output: v18.x or higher
   ```
   Install from: https://nodejs.org/

3. **Git** (optional, but recommended)
   ```bash
   git --version
   ```

4. **API Keys** (choose one)
   - OpenAI API key from https://platform.openai.com/api-keys
   - OR Anthropic API key from https://console.anthropic.com/

5. **Text Editor or IDE**
   - VS Code (recommended): https://code.visualstudio.com/
   - PyCharm Community
   - Or any text editor

---

## Step 1: Navigate to Project Directory

```bash
cd /home/coder/myProject/enterprise-incident-response-agent
```

Verify you're in the right place:
```bash
ls -la
# Should show: README.md, src/, frontend/, requirements.txt, etc.
```

---

## Step 2: Setup Backend (Python)

### 2.1: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

After activation, your prompt should show `(venv)` prefix.

### 2.2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (web server)
- Pydantic (data validation)
- Anthropic & OpenAI clients
- ChromaDB (vector database)
- And other dependencies

Verify installation:
```bash
pip list | grep -E "fastapi|uvicorn|anthropic|openai"
# Should show installed packages
```

### 2.3: Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
# or: vim .env
# or: open in your text editor
```

Edit to add **ONE** of these:

**Option A: Using Anthropic (Recommended)**
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEFAULT_PROVIDER=anthropic
```

**Option B: Using OpenAI**
```
OPENAI_API_KEY=sk-your-key-here
DEFAULT_PROVIDER=openai
```

Also set:
```
USE_RAG=true
USE_MEMORY=true
```

Save and exit.

### 2.4: Start Backend Server

```bash
python -m uvicorn src.api.main:app --reload

# Output should show:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started server process [12345]
# INFO:     Application startup complete
```

✅ Backend is now running on `http://localhost:8000`

**Keep this terminal open!** Open a new terminal for the next steps.

---

## Step 3: Setup Frontend (Node.js/React)

### In a NEW Terminal:

### 3.1: Navigate to Frontend Directory

```bash
cd /home/coder/myProject/enterprise-incident-response-agent/frontend
```

Verify you're in the right place:
```bash
ls -la
# Should show: src/, public/, package.json
```

### 3.2: Install Node Dependencies

```bash
npm install

# Output should show:
# added XXX packages in X.XXs
```

This installs React and other dependencies listed in package.json.

Verify installation:
```bash
npm list react react-dom
# Should show versions installed
```

### 3.3: Start Frontend Development Server

```bash
npm start

# Output should show:
# Compiled successfully!
# 
# On Your Network: http://192.168.x.x:3000
# Local: http://localhost:3000
#
# webpack compiled...
```

✅ Frontend is now running on `http://localhost:3000`

Browser may auto-open. If not, manually visit: **http://localhost:3000**

---

## Step 4: Verify Everything is Running

### Terminal 1 (Backend) - Check:
```bash
# Should show running and no errors
# INFO:     Application startup complete
```

### Terminal 2 (Frontend) - Check:
```bash
# Should show compiled successfully
# webpack compiled...
```

### Browser - Check:
1. Go to **http://localhost:3000**
2. Should see:
   - Header: "Enterprise Incident Response Agent"
   - Green dot indicator: "Connected"
   - Sidebar with stats
   - Chat interface
   - Upload zone

### Verify Backend Health:

```bash
# In a new terminal (Terminal 3), test API:
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

---

## Step 5: Test the Application

### Test 1: Send a Chat Message

1. In browser (http://localhost:3000)
2. Click the textarea at bottom
3. Type: `"What should I do about database connection failures?"`
4. Press Enter
5. Wait 3-5 seconds
6. Bot responds with analysis

✅ If you see a response: Everything is working!

### Test 2: Upload a Document

1. Create a test file:
   ```bash
   cat > /tmp/test_doc.txt << 'EOF'
   Database Connection Pool Management
   ====================================
   
   When pool is exhausted:
   1. Check active connections
   2. Identify long-running queries
   3. Increase pool size
   4. Implement connection timeouts
   EOF
   ```

2. In browser, drag-drop onto upload zone (or click to select)
3. File should appear in "Uploaded Documents"

✅ If file uploads: RAG system is working!

### Test 3: Check Live Stats

1. Send a few messages
2. Watch sidebar (updates every 5 seconds):
   - Memory: should increase
   - Messages: should increase
   - Incidents: should increase
   - Backups: should show count

---

## Step 6: Monitor Activity

### Backend Terminal (Terminal 1):
Shows request logs:
```
INFO:     127.0.0.1:54321 - "WebSocket /ws/chat" [accepted]
INFO:     127.0.0.1:54322 - "POST /api/documents/upload" 200 OK
```

### Frontend Terminal (Terminal 2):
Shows build/compilation info:
```
Compiled successfully!
webpack compiled...
```

### Browser Console (F12 → Console):
Should be mostly empty, no red errors.

---

## Useful Commands Reference

### Backend (Terminal 1):

```bash
# Activate environment (if not already)
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Start backend (with auto-reload)
python -m uvicorn src.api.main:app --reload

# Start backend (without reload)
python -m uvicorn src.api.main:app

# Stop backend
Ctrl+C

# Run tests
python -m pytest tests/ -v
```

### Frontend (Terminal 2 - in frontend/ directory):

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Stop frontend
Ctrl+C
```

### Testing APIs (Terminal 3):

```bash
# Check health
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

## Troubleshooting

### Problem: Python not found

```bash
# Check Python version
python3 --version

# Use python3 instead
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Problem: "pip: command not found"

```bash
# Activate virtual environment first
source venv/bin/activate
# Then try pip again
pip install -r requirements.txt
```

### Problem: Module not found (e.g., "ModuleNotFoundError: No module named 'fastapi'")

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

### Problem: Port already in use (3000 or 8000)

```bash
# Check what's using the port (macOS/Linux)
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports:
# Backend on 8001:
python -m uvicorn src.api.main:app --reload --port 8001

# Frontend on 3001 (in frontend/):
REACT_APP_API_URL=http://localhost:8001 npm start
```

### Problem: Red dot (disconnected) in browser

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check backend logs (Terminal 1)
# Should show: "Application startup complete"

# If not running, start backend:
python -m uvicorn src.api.main:app --reload
```

### Problem: Message doesn't send

```bash
# Open browser DevTools: F12
# Check Console tab for errors

# Check backend logs for errors
# If API key is missing, you'll see error in backend logs

# Verify API key is set in .env
cat .env | grep -E "OPENAI|ANTHROPIC"
```

### Problem: Upload fails

```bash
# Check file format
# Supported: .txt, .pdf, .md, .docx, .log

# Check file size
ls -lh /path/to/file
# Should be < 100MB

# Check backend logs for error details
```

### Problem: Frontend won't start (npm start)

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Start again
npm start
```

### Problem: API returns 500 error

```bash
# Check backend logs (Terminal 1)
# Look for error message

# Verify API keys in .env
cat .env | grep -E "OPENAI|ANTHROPIC|DEFAULT_PROVIDER"

# Test API directly
curl http://localhost:8000/api/health

# If needed, restart backend
# Ctrl+C in Terminal 1
# Then: python -m uvicorn src.api.main:app --reload
```

---

## File Structure for Local Development

```
project/
├── venv/                          # Virtual environment (created)
│   └── [Python packages]
│
├── frontend/
│   ├── node_modules/              # Dependencies (created)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── [other files]
│
├── src/
│   ├── api/
│   │   └── main.py               # Backend server
│   ├── services/
│   │   └── chatbot.py
│   ├── memory_manager.py
│   ├── rag_retriever.py
│   └── [other services]
│
├── .env                          # Your API keys (create this)
├── .env.example                  # Template
├── requirements.txt
└── [other files]
```

---

## Development Tips

### 1. Hot Reloading

**Backend:**
- `--reload` flag enables auto-reload on code changes
- Just save your Python file, backend restarts

**Frontend:**
- React auto-reloads on file save
- Very fast development cycle

### 2. Open Multiple Terminals

Use tabs or split terminal to run:
- Terminal 1: Backend (python)
- Terminal 2: Frontend (npm)
- Terminal 3: Testing/curl commands

### 3. Browser DevTools (F12)

- **Console:** Check for JavaScript errors
- **Network:** See API calls and WebSocket
- **Application:** Check local storage and cookies

### 4. VS Code Setup (Optional)

Install extensions for better development:
- Python
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter

### 5. Debug Backend

Add prints in Python code:
```python
print(f"Debug: {variable_name}")
```

Shows in Terminal 1.

### 6. Debug Frontend

Add logs in JavaScript:
```javascript
console.log("Debug:", variableName);
```

Shows in browser console (F12).

---

## Performance Monitoring

### Backend Performance

```bash
# Time API responses
time curl http://localhost:8000/api/health

# Monitor memory usage (on macOS)
top -l1 -pid <backend-pid>
```

### Frontend Performance

Browser DevTools → Performance tab:
1. Click Record
2. Send a message
3. Click Stop
4. Analyze timeline

---

## Stopping Everything

### To stop backend:
```bash
# In Terminal 1
Ctrl+C
```

### To stop frontend:
```bash
# In Terminal 2
Ctrl+C
```

### To deactivate Python environment:
```bash
# In Terminal 1
deactivate
```

---

## Next Steps After Local Setup

### 1. Test Everything Works
- Follow "Step 5: Test the Application" above

### 2. Make Code Changes
- Edit files in `src/` (backend) or `frontend/src/` (frontend)
- Changes auto-reload

### 3. Run Tests
```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### 4. Deploy to Production
- See DEPLOYMENT.md for Docker & cloud deployment

### 5. Add Features
- Backend: Edit `src/api/main.py`
- Frontend: Edit `frontend/src/components/`

---

## Common Development Workflow

```bash
# Terminal 1: Start backend
source venv/bin/activate
python -m uvicorn src.api.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm start

# Terminal 3: Make code changes and test
# Edit files, see changes automatically reload

# Terminal 3: Test APIs as needed
curl http://localhost:8000/api/health
curl http://localhost:8000/api/stats

# Browser: Test UI at http://localhost:3000
open http://localhost:3000

# When done, stop both servers (Ctrl+C in each terminal)
```

---

## System Requirements

**Minimum:**
- 4GB RAM
- 2 CPU cores
- 2GB disk space
- macOS, Linux, or Windows (with WSL2)

**Recommended:**
- 8GB RAM
- 4 CPU cores
- 5GB disk space
- SSD

---

## Questions?

If you run into issues:

1. Check console output for error messages
2. Verify all prerequisites are installed
3. Check `.env` file has API key
4. See TESTING_GUIDE.md for more tests
5. See DEPLOYMENT.md for Docker alternative

---

**Ready to start? Go to Step 1!** 🚀
