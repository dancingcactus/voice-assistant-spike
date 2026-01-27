"""
Aperture Assist - Main application entry point
Phase 2: LLM Integration
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Add the backend/src directory to the Python path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Load environment variables from backend/.env
# Clear any existing OpenAI key from shell environment first to ensure backend/.env takes precedence
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

backend_dir = Path(__file__).parent.parent
dotenv_path = backend_dir / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

# Verify we loaded the backend .env
loaded_key = os.getenv('OPENAI_API_KEY', '')
if loaded_key:
    print(f"✅ Loaded OpenAI key from backend/.env: ...{loaded_key[-6:]}")
else:
    print("⚠️  No OpenAI key found!")

# Validate required environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or "your_" in value or "_here" in value:
            missing.append(var)
    
    if missing:
        print("❌ Missing or invalid environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Please copy backend/.env.example to backend/.env and configure your API keys\n")
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    print("✅ Environment variables validated")

# Validate on import
validate_environment()

# Create FastAPI app
app = FastAPI(
    title="Aperture Assist API",
    description="Voice assistant backend with character-driven conversations",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and Express dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create audio directory for temporary TTS files
audio_dir = Path(__file__).parent.parent / "audio"
audio_dir.mkdir(exist_ok=True)

# Serve audio files
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Import and register routers
from api.websocket import router as websocket_router, memory_manager

app.include_router(websocket_router)

# Startup event to initialize memory manager periodic flush
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    await memory_manager.start_periodic_flush()
    print("✅ Memory Manager periodic flush started")

# Shutdown event to clean up
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    memory_manager.stop_periodic_flush()
    await memory_manager.flush_dirty_users()
    print("✅ Memory Manager flushed and stopped")

# Test API will be added in Phase 8
# from .api.test_api import router as test_router
# if os.getenv("ENABLE_TEST_API", "false").lower() == "true":
#     app.include_router(test_router, prefix="/api/test", tags=["testing"])

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "name": "Aperture Assist API",
        "version": "0.1.0",
        "status": "online",
        "phase": "6 - TTS Integration (Voice Input & Audio Output)"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    print("\n🎉 Aperture Assist Server Starting")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"🤖 Phase 7: Memory & State")
    print(f"   - Persistent user state & preferences")
    print(f"   - 30-minute conversation history window")
    print(f"   - Story progress persistence")
    print(f"   - Device state persistence")
    print(f"   - Delilah with 6 voice modes + TTS")
    print(f"   - Timer & device management")
    print("=" * 50)
    print("💡 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
