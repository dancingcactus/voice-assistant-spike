# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Chat Interface Won't Connect + Character Tool Shows "No Characters Found"

**Symptoms:**

- Chat interface shows disconnected status
- WebSocket connection errors (403 Forbidden)
- Character Tool displays "No characters found" message
- Browser console shows failed API requests

**Root Cause:**
The system has two components that need to work together:

1. **Main Server** (`src/main.py`) - Runs on port 8000, provides WebSocket for chat + mounts observability API
2. **Observability API** (`src/observability/api.py`) - Should be mounted at `/api/v1` inside main server, NOT run standalone

**The Problem:**
Running the observability API standalone with:

```bash
python -m uvicorn src.observability.api:app --reload --port 8000
```

This conflicts with the main server and doesn't provide the WebSocket endpoint needed for chat.

**Solution:**

1. **Kill any standalone observability API processes:**

```bash
lsof -ti:8000 | xargs kill -9
```

1. **Start only the main server:**

```bash
cd backend
source venv/bin/activate
python src/main.py
```

This will:

- ✅ Start main server on port 8000
- ✅ Mount observability API at `/api/v1`
- ✅ Provide WebSocket endpoint at `ws://localhost:8000/ws`
- ✅ Serve both chat interface and observability dashboard

1. **Ensure frontend is configured correctly:**

Check `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_AUTH_TOKEN=dev_token_12345
```

**NOT** ~~`http://localhost:8001`~~ or ~~`http://localhost:8000`~~ (missing `/api/v1`)

1. **Verify it's working:**

```bash
# Test main server
curl http://localhost:8000/health

# Test observability API (characters endpoint)
curl -H "Authorization: Bearer dev_token_12345" \
  http://localhost:8000/api/v1/characters

# Check WebSocket in browser console
# Should see: "✅ WebSocket connected"
```

---

## Server Architecture

### Port Mapping

- **8000** - Main server (with observability API mounted at `/api/v1`)
- **5173** - Frontend (Vite dev server)

### API Routes

- `GET /health` - Main server health check
- `GET /` - Main server root
- `WebSocket /ws` - Chat interface WebSocket
- `GET /api/v1/health` - Observability API health
- `GET /api/v1/characters` - Characters endpoint
- `GET /api/v1/users` - Users endpoint
- `GET /api/v1/story/chapters` - Story beats endpoint
- etc.

### Correct Startup Sequence

1. **Backend:**

```bash
cd backend
source venv/bin/activate
python src/main.py
```

Expected output:

```
✅ Loaded OpenAI key from backend/.env
✅ Environment variables validated
✅ Test API enabled
✅ Observability API mounted at /api/v1
🎉 Aperture Assist Server Starting
🌐 Server: http://localhost:8000
```

1. **Frontend:**

```bash
cd frontend
npm run dev
```

Expected output:

```
VITE v5.x.x ready in xxx ms
➜ Local: http://localhost:5173/
```

---

## Debugging Checklist

When things aren't working:

### 1. Check Running Processes

```bash
# Check what's running on port 8000
lsof -i:8000

# Should show only ONE process: python src/main.py
```

### 2. Check Frontend Configuration

```bash
cat frontend/.env

# Should show:
# VITE_API_BASE_URL=http://localhost:8000/api/v1
# VITE_API_AUTH_TOKEN=dev_token_12345
```

### 3. Test API Endpoints

```bash
# Main server
curl http://localhost:8000/health

# Observability API
curl -H "Authorization: Bearer dev_token_12345" \
  http://localhost:8000/api/v1/health

# Characters (specific test for Character Tool)
curl -H "Authorization: Bearer dev_token_12345" \
  http://localhost:8000/api/v1/characters | python -m json.tool
```

### 4. Check Browser Console

Open DevTools (F12) → Console tab:

- ✅ Should see: "✅ WebSocket connected"
- ❌ Should NOT see: 403 Forbidden errors
- ❌ Should NOT see: Failed to fetch errors

### 5. Check Server Logs

Look for these messages in the terminal running `python src/main.py`:

```
✅ WebSocket connected: [uuid]
INFO: connection open
INFO: 127.0.0.1:xxx - "GET /api/v1/characters HTTP/1.1" 200 OK
```

---

## Known Issues

### "No characters found" despite API returning data

**Cause:** Frontend caching or stale connection

**Solution:**

1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Clear browser cache
3. Restart frontend dev server

### WebSocket keeps disconnecting and reconnecting

**Cause:** Multiple server instances competing for port 8000

**Solution:**

```bash
# Kill everything on port 8000
lsof -ti:8000 | xargs kill -9

# Start only main server
cd backend && source venv/bin/activate && python src/main.py
```

### Character API returns 404

**Cause:** Frontend pointing to wrong URL

**Solution:**
Check `frontend/.env` has `/api/v1` in the base URL:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1  # ← Must include /api/v1
```

---

## Prevention

To avoid these issues in the future:

1. **Always use `python src/main.py`** to start the backend
   - ❌ Don't use: `python -m uvicorn src.observability.api:app`
   - ✅ Do use: `python src/main.py`

2. **Check frontend .env before starting**
   - Verify `VITE_API_BASE_URL` includes `/api/v1`

3. **Clean shutdown**
   - Use Ctrl+C to stop servers gracefully
   - Avoid killing processes mid-operation

4. **Port conflicts**
   - Before starting, check no other process is using port 8000:

   ```bash
   lsof -i:8000
   ```

---

## Quick Fix Script

Save this as `restart_servers.sh`:

```bash
#!/bin/bash
echo "🔄 Restarting Aperture Assist servers..."

# Kill any existing processes
echo "Stopping existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting backend..."
cd backend
source venv/bin/activate
python src/main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🌐 Backend API: http://localhost:8000"
echo "🌐 Observability API: http://localhost:8000/api/v1"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
wait
```

Usage:

```bash
chmod +x restart_servers.sh
./restart_servers.sh
```

---

## Support

If you encounter issues not covered here, check:

1. Server logs (terminal running `python src/main.py`)
2. Browser console (F12 → Console tab)
3. Network tab (F12 → Network tab) for failed requests

For Character Tool specific issues, run the test script:

```bash
./tests/scripts/test_milestone7_character_tool.sh
```

All 10 tests should pass if the system is configured correctly.
