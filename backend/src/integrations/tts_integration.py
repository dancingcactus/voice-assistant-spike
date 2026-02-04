"""
TTS Integration - Text-to-Speech provider abstraction and implementations.

Supports:
- ElevenLabs API for high-quality character voices
- Extensible for future providers (Piper, OpenAI TTS, etc.)
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import uuid

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def generate_speech(
        self,
        text: str,
        character_id: str,
        voice_mode: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            character_id: Character identifier for voice selection
            voice_mode: Optional voice mode (e.g., "passionate", "protective")

        Returns:
            Path to generated audio file, or None if generation failed
        """
        pass

    @abstractmethod
    def get_voice_id(self, character_id: str) -> Optional[str]:
        """
        Get the provider-specific voice ID for a character.

        Args:
            character_id: Character identifier

        Returns:
            Provider-specific voice ID, or None if not found
        """
        pass


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS implementation."""

    def __init__(self, audio_dir: str = "audio"):
        """
        Initialize ElevenLabs TTS provider.

        Args:
            audio_dir: Directory to store generated audio files (relative to backend dir)
        """
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY not found in environment")
            raise ValueError("ELEVENLABS_API_KEY is required")

        # Make path absolute from backend directory
        if not Path(audio_dir).is_absolute():
            # Get backend directory (parent of src)
            backend_dir = Path(__file__).parent.parent.parent
            self.audio_dir = backend_dir / audio_dir
        else:
            self.audio_dir = Path(audio_dir)

        self.audio_dir.mkdir(exist_ok=True)

        # Voice mapping: character_id -> ElevenLabs voice ID
        self.voice_mapping = {
            "delilah": os.getenv("ELEVENLABS_VOICE_ID", ""),
            # Future characters will be added here
            # "hank": os.getenv("ELEVENLABS_HANK_VOICE_ID", ""),
            # "cave": os.getenv("ELEVENLABS_CAVE_VOICE_ID", ""),
        }

        # Voice settings per character
        # Phase 3 validated settings (9.72/10 average quality)
        # See: docs/technical/phase3/ for complete testing methodology
        self.voice_settings = {
            "delilah": {
                "default": {
                    "stability": 0.50,  # Match warm_baseline
                    "similarity_boost": 0.75,
                    "style": 0.50,  # Match warm_baseline
                    "use_speaker_boost": True
                },
                "passionate": {
                    "stability": 0.35,  # Phase 3: 9.0/10 (2 iterations)
                    "similarity_boost": 0.75,
                    "style": 0.65,  # High energy, tumbling thought pattern
                    "use_speaker_boost": True
                },
                "protective": {
                    "stability": 0.55,  # Phase 3: 9.8/10 (2 iterations)
                    "similarity_boost": 0.75,
                    "style": 0.45,  # Controlled intensity, firm but caring
                    "use_speaker_boost": True
                },
                "mama_bear": {
                    "stability": 0.65,  # Phase 3: 10.0/10 (1 iteration)
                    "similarity_boost": 0.75,
                    "style": 0.40,  # Soft, nurturing, deliberate
                    "use_speaker_boost": True
                },
                "startled": {
                    "stability": 0.30,  # Phase 3: 10.0/10 (1 iteration)
                    "similarity_boost": 0.75,
                    "style": 0.50,  # High pitch, rapid questions, quick recovery
                    "use_speaker_boost": True
                },
                "deadpan": {
                    "stability": 0.65,  # Phase 3: 9.6/10 (1 iteration)
                    "similarity_boost": 0.75,
                    "style": 0.35,  # Flat, minimal expression, efficient
                    "use_speaker_boost": True
                },
                "warm_baseline": {
                    "stability": 0.50,  # Phase 3: 9.9/10 (1 iteration - best debut!)
                    "similarity_boost": 0.75,
                    "style": 0.50,  # Natural, conversational, versatile default
                    "use_speaker_boost": True
                }
            }
        }

        self.base_url = "https://api.elevenlabs.io/v1"

        logger.info(
            f"ElevenLabs TTS initialized "
            f"(voices: {list(self.voice_mapping.keys())}, "
            f"audio_dir: {self.audio_dir})"
        )

    def get_voice_id(self, character_id: str) -> Optional[str]:
        """Get ElevenLabs voice ID for a character."""
        voice_id = self.voice_mapping.get(character_id)
        if not voice_id:
            logger.warning(f"No voice mapping found for character: {character_id}")
        return voice_id

    def get_voice_settings(
        self,
        character_id: str,
        voice_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get voice settings for a character and mode.

        Args:
            character_id: Character identifier
            voice_mode: Optional voice mode

        Returns:
            Voice settings dict
        """
        character_settings = self.voice_settings.get(character_id, {})
        mode = voice_mode or "default"

        # Fall back to default if specific mode not found
        settings = character_settings.get(mode, character_settings.get("default", {}))

        return settings

    def generate_speech(
        self,
        text: str,
        character_id: str,
        voice_mode: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate speech using ElevenLabs API.

        Args:
            text: Text to convert to speech
            character_id: Character identifier
            voice_mode: Optional voice mode for settings

        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            voice_id = self.get_voice_id(character_id)
            if not voice_id:
                logger.error(f"No voice ID configured for character: {character_id}")
                return None

            # Get voice settings for this mode
            voice_settings = self.get_voice_settings(character_id, voice_mode)

            # Prepare API request
            url = f"{self.base_url}/text-to-speech/{voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            payload = {
                "text": text,
                "model_id": "eleven_flash_v2_5",  # Fast, supports library voices on free tier
                "voice_settings": voice_settings
            }

            logger.info(
                f"Generating speech for {character_id} "
                f"(mode: {voice_mode or 'default'}, length: {len(text)} chars)"
            )

            # Make API request
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    f"ElevenLabs API error: {response.status_code} - {response.text}"
                )
                return None

            # Generate unique filename
            filename = f"{character_id}_{uuid.uuid4()}.mp3"
            file_path = self.audio_dir / filename

            # Save audio file
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Generated audio file: {filename}")

            # Return relative path for serving
            return str(file_path.relative_to(self.audio_dir.parent))

        except requests.Timeout:
            logger.error("ElevenLabs API request timed out")
            return None
        except requests.RequestException as e:
            logger.error(f"ElevenLabs API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}", exc_info=True)
            return None

    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """
        Clean up audio files older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
        """
        import time

        try:
            now = time.time()
            deleted_count = 0

            for audio_file in self.audio_dir.glob("*.mp3"):
                file_age = now - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audio files")

        except Exception as e:
            logger.error(f"Error cleaning up audio files: {str(e)}")


class MockTTS(TTSProvider):
    """Mock TTS provider for testing without API calls."""

    def __init__(self):
        """Initialize mock TTS provider."""
        logger.info("Mock TTS provider initialized (no actual audio generation)")

    def get_voice_id(self, character_id: str) -> Optional[str]:
        """Return mock voice ID."""
        return f"mock_{character_id}"

    def generate_speech(
        self,
        text: str,
        character_id: str,
        voice_mode: Optional[str] = None
    ) -> Optional[str]:
        """
        Mock speech generation - returns None to simulate no audio.

        Args:
            text: Text to convert
            character_id: Character ID
            voice_mode: Voice mode

        Returns:
            None (no audio file)
        """
        logger.info(
            f"Mock TTS: Would generate speech for {character_id} "
            f"(mode: {voice_mode or 'default'}, length: {len(text)} chars)"
        )
        return None


def create_tts_provider(provider: str = "elevenlabs") -> TTSProvider:
    """
    Factory function to create TTS provider.

    Args:
        provider: Provider name ("elevenlabs" or "mock")

    Returns:
        TTSProvider instance
    """
    if provider == "mock":
        return MockTTS()
    elif provider == "elevenlabs":
        return ElevenLabsTTS()
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")
