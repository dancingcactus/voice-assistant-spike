/**
 * AudioPlayer Component - Handles TTS audio playback
 * Phase 6: TTS Integration
 *
 * Supports two modes:
 * 1. Auto-play mode: For voice input responses (audioUrl provided)
 * 2. Manual mode: For chat input responses (generate on-demand)
 */

import { useEffect, useRef, useState } from 'react';
import type { WebSocketService } from '../services/websocket';

interface AudioPlayerProps {
  // Auto-play mode (for voice input)
  audioUrl?: string;
  autoPlay?: boolean;
  onPlaybackEnd?: () => void;

  // Manual mode (for chat input)
  text?: string;
  character?: string;
  voiceMode?: string;
  wsService?: WebSocketService | null;
}

export function AudioPlayer({
  audioUrl,
  autoPlay = true,
  onPlaybackEnd,
  text,
  character,
  voiceMode,
  wsService
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Auto-play mode (when audioUrl is provided)
  useEffect(() => {
    if (!audioUrl || !audioRef.current) return;

    const audio = audioRef.current;

    // Load the new audio
    audio.src = `http://localhost:8000${audioUrl}`;
    audio.load();

    // Auto-play if enabled
    if (autoPlay) {
      const playPromise = audio.play();

      if (playPromise !== undefined) {
        playPromise.catch((error) => {
          // Auto-play was prevented (browser policy)
          console.warn('Auto-play prevented:', error);
          // User will need to manually play
        });
      }
    }
  }, [audioUrl, autoPlay]);

  // Manual mode - handle generated audio playback
  useEffect(() => {
    if (!generatedAudioUrl || !audioRef.current) return;

    const audio = audioRef.current;
    audio.src = `http://localhost:8000${generatedAudioUrl}`;
    audio.load();

    // Always auto-play after manual generation
    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.catch((error) => {
        console.warn('Playback prevented:', error);
      });
    }
  }, [generatedAudioUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => {
      onPlaybackEnd?.();
    };

    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('ended', handleEnded);
    };
  }, [onPlaybackEnd]);

  const handleGenerateTTS = async () => {
    if (!text || !wsService) return;

    setIsGenerating(true);
    setError(null);

    try {
      const audioUrl = await wsService.requestTTS(text, character || 'delilah', voiceMode);
      setGeneratedAudioUrl(audioUrl);
    } catch (err) {
      console.error('Failed to generate TTS:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate speech');
    } finally {
      setIsGenerating(false);
    }
  };

  // Auto-play mode (voice input)
  if (audioUrl) {
    return (
      <audio
        ref={audioRef}
        controls
        className="audio-player"
        preload="auto"
      >
        Your browser does not support the audio element.
      </audio>
    );
  }

  // Manual mode (chat input)
  if (text && !autoPlay) {
    return (
      <div className="audio-player-manual">
        {!generatedAudioUrl ? (
          <button
            onClick={handleGenerateTTS}
            disabled={isGenerating}
            className="speak-button"
            title="Generate and play speech"
          >
            {isGenerating ? '🔊 Generating...' : '🔊 Speak'}
          </button>
        ) : (
          <audio
            ref={audioRef}
            controls
            className="audio-player"
            preload="auto"
          >
            Your browser does not support the audio element.
          </audio>
        )}
        {error && <div className="audio-error">{error}</div>}
      </div>
    );
  }

  return null;
}
