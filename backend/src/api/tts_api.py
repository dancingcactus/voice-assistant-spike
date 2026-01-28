"""
TTS API - REST endpoint for on-demand text-to-speech generation.

Provides manual TTS generation for chat interactions where automatic
TTS is not desired (e.g., to save API costs during testing).
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from integrations.tts_integration import TTSProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    """Request model for manual TTS generation."""
    text: str
    character_id: str = "delilah"
    voice_mode: Optional[str] = None


class TTSResponse(BaseModel):
    """Response model for TTS generation."""
    audio_url: str


# TTS provider will be injected during app startup
_tts_provider: Optional[TTSProvider] = None


def set_tts_provider(provider: TTSProvider):
    """Set the TTS provider instance (called from main.py)."""
    global _tts_provider
    _tts_provider = provider
    logger.info("TTS provider registered in TTS API router")


@router.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate speech audio from text on-demand.

    This endpoint allows manual TTS generation for chat interactions
    where automatic TTS is not desired.

    Args:
        request: TTS generation request containing text and voice parameters

    Returns:
        TTSResponse with audio_url path

    Raises:
        HTTPException: If TTS provider is not configured or generation fails
    """
    if not _tts_provider:
        logger.error("TTS generation requested but no provider configured")
        raise HTTPException(
            status_code=503,
            detail="TTS provider not configured. Please set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID."
        )

    try:
        logger.info(
            f"Manual TTS generation requested: {len(request.text)} chars, "
            f"character={request.character_id}, mode={request.voice_mode or 'default'}"
        )

        audio_path = _tts_provider.generate_speech(
            text=request.text,
            character_id=request.character_id,
            voice_mode=request.voice_mode
        )

        if not audio_path:
            logger.error("TTS generation returned no audio path")
            raise HTTPException(
                status_code=500,
                detail="TTS generation failed - no audio file generated"
            )

        audio_url = f"/{audio_path}"
        logger.info(f"Manual TTS generated successfully: {audio_url}")

        return TTSResponse(audio_url=audio_url)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.get("/health")
async def tts_health():
    """
    Check TTS service health.

    Returns:
        Status information about TTS provider availability
    """
    return {
        "status": "available" if _tts_provider else "unavailable",
        "provider": type(_tts_provider).__name__ if _tts_provider else None
    }
