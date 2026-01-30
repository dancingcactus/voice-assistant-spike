# Services Setup Guide

## Overview

This project has **two separate backend servers** that run simultaneously:

1. **Chat Backend** (main voice assistant) - Port 8000
2. **Observability API** (dashboard) - Port 8001
3. **Frontend** (React app) - Port 5173

## Why Two Backend Servers?

- **Chat Backend**: Handles WebSocket connections for real-time chat, voice processing, and LLM interactions
- **Observability API**: Provides REST endpoints for debugging tools, story beat inspection, memory management, and tool call logs

They serve different purposes and cannot share the same port.

## Starting All Services

### Terminal 1: Chat Backend (Port 8000)

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000
```

### Terminal 2: Observability API (Port 8001)

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.observability.api:app --reload --port 8001
```

### Terminal 3: Frontend (Port 5173)

```bash
cd frontend
npm run dev
```

## Accessing the Applications

- **Chat Interface**: <http://localhost:5173/>
- **Observability Dashboard**: <http://localhost:5173/observability>
- **Chat Backend Health**: <http://localhost:8000/health>
- **Observability API Health**: <http://localhost:8001/health>
- **OpenAPI Docs (Chat)**: <http://localhost:8000/docs>
- **OpenAPI Docs (Observability)**: <http://localhost:8001/docs>

## Frontend Configuration

The frontend knows which port to use based on the `.env` file:

**`/frontend/.env`**:

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_API_AUTH_TOKEN=dev_token_12345
```

- The observability dashboard uses `VITE_API_BASE_URL` (port 8001)
- The chat interface hardcodes WebSocket to `ws://localhost:8000/ws`

## Port Summary

| Service | Port | Purpose |
|---------|------|---------|
| Chat Backend | 8000 | WebSocket `/ws`, LLM processing, voice |
| Observability API | 8001 | REST API for debugging tools |
| Frontend | 5173 | React dev server (Vite) |

## Troubleshooting

### Chat interface not connecting

**Problem**: WebSocket connection fails
**Solution**: Ensure chat backend is running on port 8000

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"development"}
```

### Observability dashboard not loading

**Problem**: 404 errors in browser console
**Solution**: Ensure observability API is running on port 8001

```bash
curl http://localhost:8001/health
# Should return: {"status":"ok","timestamp":"...","version":"1.0.0"}
```

### Port already in use

**Problem**: `Address already in use` error
**Solution**: Kill existing processes

```bash
# Find process on port 8000
lsof -ti:8000 | xargs kill -9

# Find process on port 8001
lsof -ti:8001 | xargs kill -9

# Find process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Frontend uses wrong API port

**Problem**: Observability dashboard tries to connect to port 8000
**Solution**: Update `/frontend/.env` and restart frontend

```bash
# Edit .env to use port 8001
# Then restart:
cd frontend
npm run dev
```

## Quick Start (All Services)

Run this to start everything:

```bash
# Terminal 1: Chat Backend
cd /Users/justin/projects/voice-assistant-spike/backend && \
source venv/bin/activate && \
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: Observability API
cd /Users/justin/projects/voice-assistant-spike/backend && \
source venv/bin/activate && \
python -m uvicorn src.observability.api:app --reload --port 8001

# Terminal 3: Frontend
cd /Users/justin/projects/voice-assistant-spike/frontend && \
npm run dev
```

Then open:

- Chat: <http://localhost:5173/>
- Dashboard: <http://localhost:5173/observability>

## Current Status

✅ **Chat Backend** running on port 8000
✅ **Observability API** running on port 8001
✅ **Frontend** running on port 5173

All services are operational and properly configured!
