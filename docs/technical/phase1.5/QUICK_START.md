# Phase 1.5 Observability Dashboard - Quick Start

## Overview

The Observability Dashboard provides tools to debug, test, and inspect the Hey Chat! voice assistant system.

## Prerequisites

- Python 3.11+ with venv
- Node.js 18+
- Backend dependencies installed
- Frontend dependencies installed

## Starting the System

### 1. Start the Backend API

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.observability.api:app --reload --port 8000
```

You should see:
```
🚀 Observability API starting...
📁 Data directory: /Users/justin/projects/voice-assistant-spike/backend/data
👥 Users found: 6
✅ Ready!
```

### 2. Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

You should see:
```
VITE ready in XXX ms
➜ Local: http://localhost:5175/
```

### 3. Access the Dashboard

Open your browser to: **http://localhost:5175/observability**

## What You'll See

### Dashboard Home
- Connection status indicator
- Your user profile (user_justin)
- Current chapter and progress
- List of all users in the system
- Milestone completion roadmap

### User Profile Information
- User ID
- Current chapter
- Total interactions
- Story beat progress (5/8 beats delivered)

## Quick Tests

### Test 1: Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-28T...",
  "version": "1.0.0"
}
```

### Test 2: List All Users
```bash
curl -H "Authorization: Bearer dev_token_12345" \
     http://localhost:8000/api/v1/users
```

Should return array of users including `user_justin`.

### Test 3: Get Your Profile
```bash
curl -H "Authorization: Bearer dev_token_12345" \
     http://localhost:8000/api/v1/users/user_justin
```

Should return your full user profile with story progress and preferences.

## Troubleshooting

### Backend won't start
- Check Python virtual environment is activated
- Ensure port 8000 is not in use: `lsof -i :8000`
- Verify DATA_DIR path in [backend/.env](../../../backend/.env:18)

### Frontend shows connection error
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify API_AUTH_TOKEN matches in both [backend/.env](../../../backend/.env:21) and [frontend/.env](../../../frontend/.env:2)

### No users showing up
- Check that user JSON files exist in `backend/data/users/`
- Ensure files are valid JSON
- Check backend logs for file read errors

### CORS errors in browser
- Verify frontend port is in CORS_ORIGINS in [backend/.env](../../../backend/.env:22)
- Backend should auto-reload when .env changes
- Try hard refresh (Cmd+Shift+R)

## Configuration

### Backend Environment ([backend/.env](../../../backend/.env:1))
```env
API_AUTH_TOKEN=dev_token_12345
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175
DATA_DIR=../data
```

### Frontend Environment ([frontend/.env](../../../frontend/.env:1))
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_AUTH_TOKEN=dev_token_12345
```

## Accessing Original Phase 1 Interface

The original voice assistant interface is still available at:
**http://localhost:5175/** (root path)

Use the "🔧 Observability Dashboard" link in the top-right to switch between them.

## Next Steps

Once Milestone 1 is working:
1. Verify you can see your user data
2. Check that all users are listed
3. Confirm no console errors
4. Ready to proceed to Milestone 2: Story Beat Tool

## API Documentation

Full API documentation available at:
**http://localhost:8000/docs** (Swagger UI)

## Support

For issues or questions, check:
- [Implementation Plan](IMPLEMENTATION_PLAN.md:1)
- [Milestone 1 Completion Notes](MILESTONE_1_COMPLETE.md:1)
- Backend logs in terminal
- Browser console for frontend errors
