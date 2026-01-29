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
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",  # Vite dev server (alternate port)
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://localhost:5181",
        "http://localhost:5182",
        "http://localhost:5183",  # Vite dev server (additional ports)
        "http://localhost:3000"   # Express dev server
    ],
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
from api.websocket import router as websocket_router, memory_manager, conversation_manager
from api.tts_api import router as tts_router, set_tts_provider

app.include_router(websocket_router)
app.include_router(tts_router)

# Test API (Phase 8) - only enabled if ENABLE_TEST_API=true
if os.getenv("ENABLE_TEST_API", "false").lower() == "true":
    from api.test_api import router as test_router, set_managers
    set_managers(conversation_manager, memory_manager)
    app.include_router(test_router)
    print("✅ Test API enabled")

# Startup event to initialize memory manager periodic flush
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    await memory_manager.start_periodic_flush()
    print("✅ Memory Manager periodic flush started")

    # Register TTS provider with TTS API if available
    if conversation_manager.tts_provider:
        set_tts_provider(conversation_manager.tts_provider)
        print("✅ TTS provider registered with TTS API")

# Shutdown event to clean up
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    memory_manager.stop_periodic_flush()
    await memory_manager.flush_dirty_users()
    print("✅ Memory Manager flushed and stopped")

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "name": "Aperture Assist API",
        "version": "0.1.0",
        "status": "online",
        "phase": "1.5 - Observability Dashboard"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

# Observability API (Phase 1.5) - mounted after main routes to avoid conflicts
from observability.api import app as observability_app
app.mount("/api/v1", observability_app)
print("✅ Observability API mounted at /api/v1")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    print("\n🎉 Aperture Assist Server Starting")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"🤖 Phase 1.5: Observability Dashboard")
    print(f"   - Story Beat Tool")
    print(f"   - Memory Tool")
    print(f"   - User Testing Tool")
    print(f"   - Full Phase 1 features + debugging")
    print("=" * 50)
    print("💡 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
