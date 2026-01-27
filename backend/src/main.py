"""
Aperture Assist - Main application entry point
Phase 1: Foundation Setup
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = Path(__file__).parent.parent
dotenv_path = backend_dir / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

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
# Use try/except to handle both module and direct execution
try:
    from .api.websocket import router as websocket_router
except ImportError:
    from api.websocket import router as websocket_router

app.include_router(websocket_router)

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
        "phase": "1 - Foundation Setup"
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
    print(f"🤖 Phase 1: Foundation Setup")
    print("=" * 50)
    print("💡 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
