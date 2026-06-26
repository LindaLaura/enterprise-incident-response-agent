# Testing Guide - Web Interface in Browser

## 🚀 Quick Start (Recommended: Docker)

### Option 1: Docker Compose (Easiest - One Command)

```bash
# Start everything
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Open in browser
open http://localhost:3000
# or: firefox http://localhost:3000
# or: google-chrome http://localhost:3000
```

Check if services are running:
```bash
# Check API health
curl http://localhost:8000/api/health
# Expected: {"status": "healthy", ...}

# Check Web server
curl http://localhost:3000/
```

View logs:
```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f api

# Frontend only
docker-compose logs -f web

# Exit: Ctrl+C
```

Stop services:
```bash
docker-compose down
```

---

## 💻 Option 2: Local Development (Best for Development)

### Step 1: Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Step 2: Start Backend (Terminal 1)

```bash
# From project root
python -m uvicorn src.api.main:app --reload

# Output should show:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### Step 3: Start Frontend (Terminal 2)

```bash
# From project root
cd frontend
npm start

# Output should show:
# On Your Network: http://192.168.x.x:3000
# Local: http://localhost:3000
```

### Step 4: Open Browser

```
http://localhost:3000
```

---

## 🧪 Testing Checklist

### 1. Page Load Test
- [ ] Page loads without errors
- [ ] Header shows "Enterprise Incident Response Agent"
- [ ] Connection status shows (green or red dot)
- [ ] Sidebar visible with stats
- [ ] Chat box visible with input area

### 2. Connection Test
- [ ] Wait a few seconds
- [ ] Header connection indicator turns green
- [ ] Sidebar stats populate
- [ ] No errors in browser console

**If red/disconnected:**
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check logs
docker-compose logs api
# or: see Terminal 1 output if local dev
```

### 3. Chat Test - Simple Message
1. Click on the textarea in the chat box
2. Type: `Test message - is the system working?`
3. Press Enter (or Shift+Enter for new line)
4. Expected:
   - Your message appears on right (blue bubble)
   - Loading indicator appears ("Analyzing incident...")
   - Bot response appears on left (gray bubble) after 2-5 seconds
   - Timestamp on each message

**If it fails:**
- Check browser console (F12 → Console tab)
- Check backend logs for errors
- Verify API is responding: `curl http://localhost:8000/api/health`

### 4. Chat Test - Real Incident
Try pasting real logs:
```
2026-06-26 10:15:23 ERROR [DatabaseService] Connection pool exhausted: 500 connections in use
2026-06-26 10:15:24 CRITICAL [DatabaseService] Failed to acquire connection within 30s timeout
2026-06-26 10:15:25 ERROR [OrderService] Cannot insert order - database unavailable
2026-06-26 10:15:26 ERROR [OrderService] Failed attempt 1/3 to insert order ID: ORD-12345
```

Expected response: Incident analysis with root cause, recommendations, affected services

### 5. Document Upload Test
1. **Prepare test file:**
   ```bash
   cat > /tmp/test_doc.txt << 'EOF'
   Database Connection Pool Management
   =====================================
   
   When the connection pool is exhausted:
   1. Check current active connections
   2. Identify long-running queries
   3. Increase pool size if needed
   4. Implement connection timeouts
   
   Best practice: Use try-with-resources pattern
   EOF
   ```

2. **Upload via drag-and-drop:**
   - Open Files app
   - Drag `/tmp/test_doc.txt` onto the upload zone
   - Should show upload progress
   - File should appear in "Uploaded Documents" list

3. **Or upload via click:**
   - Click on upload zone
   - Select `/tmp/test_doc.txt`
   - Should upload successfully

4. **Verify upload:**
   - File appears in list with green checkmark
   - Shows filename, chunk count, type
   - Sidebar shows updated document count

### 6. System Stats Test
- [ ] Sidebar updates every 5 seconds
- [ ] Incident count increases when you analyze
- [ ] Memory usage shown in KB
- [ ] Message count increases
- [ ] Document count shows uploaded files
- [ ] Backup count visible

### 7. Clear Chat Test
1. After sending messages, sidebar shows message count
2. Click "🗑️ Clear Chat" button
3. Expected:
   - Chat history disappears
   - Message count in sidebar resets to 0
   - Input field ready for new messages

### 8. Recent Incidents Test
1. Send multiple incident analyses
2. Click "📋 Recent Incidents" in sidebar
3. Should show:
   - Total incident count
   - Root cause types
   - User preferences

### 9. Error Handling Test
- [ ] **Wrong message:** Disconnect backend
  - Type a message
  - Should see error: "Not connected to server" or similar
  
- [ ] **Upload non-supported file:**
  - Try uploading .exe or .zip file
  - Should show error message
  
- [ ] **Invalid incident text:**
  - Type something that breaks the LLM
  - Should show graceful error

### 10. WebSocket Reconnection Test
1. Start app with Docker
2. Send a message (works)
3. Stop backend: `docker-compose stop api`
4. Try sending another message: Shows "Not connected"
5. Restart backend: `docker-compose start api`
6. Wait 3 seconds
7. Status should turn green
8. Should be able to send messages again

---

## 🔍 Browser DevTools Testing

### Open DevTools
```
Windows/Linux: F12 or Ctrl+Shift+I
Mac: Cmd+Option+I
```

### Console Tab (F12 → Console)
Look for:
- No red errors
- WebSocket connection messages
- Any warnings about CORS

Test commands in console:
```javascript
// Check if app is loaded
console.log('App loaded')

// Check window object
console.log(window.location)
```

### Network Tab (F12 → Network)
Click a message, watch for:
- WebSocket connection to `ws://localhost:8000/ws/chat`
- Shows as "pending" then changes to "established"
- Messages flow as text frames

### Storage Tab (F12 → Storage/Application)
- Check LocalStorage (if using)
- Check Cookies
- Check WebSocket state

### Performance Tab (F12 → Performance)
1. Open DevTools
2. Click Performance tab
3. Click red Record button
4. Send a chat message
5. Click Stop
6. Review timeline for delays

---

## 📊 API Testing (via curl/Postman)

### Test Health Endpoint
```bash
curl http://localhost:8000/api/health

# Expected response:
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

### Get System Stats
```bash
curl http://localhost:8000/api/stats

# Expected response:
{
  "memory": {
    "total_incidents": 2,
    "root_cause_types": 1,
    ...
  },
  "chatbot": {
    "conversation_history_size": 4,
    "uploaded_docs_count": 1,
    ...
  },
  "backups": 2
}
```

### List Recent Incidents
```bash
curl http://localhost:8000/api/incidents?limit=5
```

### Get Chat History
```bash
curl http://localhost:8000/api/chat/history?limit=10
```

### List Backups
```bash
curl http://localhost:8000/api/backups
```

### Upload Document via curl
```bash
curl -X POST \
  -F "file=@/tmp/test_doc.txt" \
  http://localhost:8000/api/documents/upload

# Expected response:
{
  "status": "success",
  "filename": "test_doc.txt",
  "chunks": 2,
  "doc_type": "troubleshooting"
}
```

### Clear Chat
```bash
curl -X POST http://localhost:8000/api/chat/clear
```

---

## 🐛 Troubleshooting

### Issue: Can't connect to localhost:3000

**Solution:**
```bash
# Check if web service is running
docker-compose ps
# Should show "web" container running

# Check if port is in use
lsof -i :3000

# If port in use, stop other services
docker-compose down

# Restart
docker-compose up -d
```

### Issue: Backend connection fails (red dot)

**Check backend:**
```bash
# Is backend running?
docker-compose ps api
# Should show "Up"

# Is it healthy?
curl http://localhost:8000/api/health

# Check logs
docker-compose logs api | tail -20
```

### Issue: WebSocket connection fails

**Browser console shows WebSocket errors:**
```
1. Check nginx config is correct
2. Verify API container is running: docker-compose ps
3. Check proxy settings in nginx.conf
4. Restart containers: docker-compose restart
```

### Issue: Document upload fails

**Check file:**
```bash
# File exists?
ls -la /path/to/file.txt

# Is it text readable?
file /path/to/file.txt

# Supported formats: .txt, .pdf, .md, .docx, .log
```

### Issue: Slow responses (>10s)

**Could be:**
- LLM API latency (normal: 2-5s)
- Backend processing time
- Network lag
- Check API key is valid

### Issue: Memory usage keeps growing

**Expected behavior:**
- Conversation auto-truncates to 100 messages
- Docs auto-truncate to 50 files
- If growing unbounded, check logs for errors

---

## 📈 Performance Testing

### Test message latency
```
1. Open DevTools Network tab
2. Note timestamp when sending message
3. Observe WebSocket frame timestamp
4. Calculate round-trip time

Expected: <100ms network, 2-5s total (LLM processing)
```

### Test with many messages
```
1. Send 50+ messages
2. Monitor memory in DevTools
3. Watch for slowdown

Expected: No significant slowdown, chat remains responsive
```

### Test file upload performance
```
1. Create large file: dd if=/dev/urandom of=large.txt bs=1M count=5
2. Upload file
3. Measure time to completion

Expected: <5 seconds for 5MB file
```

---

## ✅ Sign-Off Checklist

After testing, verify all work:

- [ ] Page loads at http://localhost:3000
- [ ] Connection indicator shows green
- [ ] Can send messages and receive responses
- [ ] Can upload documents
- [ ] Stats update in real-time
- [ ] Clear chat works
- [ ] No console errors
- [ ] Backend API responds (curl test)
- [ ] Docker logs show no errors
- [ ] System is stable (no crashes)

---

## 🎯 Next Steps After Testing

### If everything works:
1. Deploy to cloud (AWS, GCP, Azure)
2. Configure production environment
3. Set up monitoring and logging
4. Add authentication (JWT)
5. Set up HTTPS/TLS

### If you find issues:
1. Check logs: `docker-compose logs -f`
2. Review error messages in browser console (F12)
3. Test API endpoints with curl
4. Verify environment variables in .env
5. Ensure API keys are set (OPENAI_API_KEY or ANTHROPIC_API_KEY)

---

## 📚 Documentation

- Full API docs: http://localhost:8000/docs (Swagger UI)
- Deployment: DEPLOYMENT.md
- Architecture: WEB_INTERFACE_COMPLETE.md
- Memory system: PHASE1_MEMORY_ENHANCEMENTS.md

**Ready to test? Start with:** `docker-compose up -d` then open http://localhost:3000 🚀
