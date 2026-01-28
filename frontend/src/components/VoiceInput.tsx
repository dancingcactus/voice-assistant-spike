/**
 * VoiceInput Component - Speech-to-text using Web Speech API
 * Phase 6: TTS Integration
 */

import { useState, useEffect, useRef } from 'react';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

// Check if Web Speech API is available
const isSpeechRecognitionSupported = () => {
  return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
};

export function VoiceInput({ onTranscript, onError, disabled = false }: VoiceInputProps) {
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (!isSpeechRecognitionSupported()) {
      console.warn('Web Speech API not supported in this browser');
      return;
    }

    // Initialize Speech Recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      console.log('Speech recognition started');
      setIsListening(true);
      setInterimTranscript('');
    };

    recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim) {
        setInterimTranscript(interim);
      }

      if (final) {
        console.log('Final transcript:', final);
        onTranscript(final);
        setInterimTranscript('');
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      setInterimTranscript('');

      const errorMessage = getErrorMessage(event.error);
      onError?.(errorMessage);
    };

    recognition.onend = () => {
      console.log('Speech recognition ended');
      setIsListening(false);
      setInterimTranscript('');
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onTranscript, onError]);

  const getErrorMessage = (error: string): string => {
    switch (error) {
      case 'no-speech':
        return 'No speech detected. Please try again.';
      case 'audio-capture':
        return 'No microphone found. Please check your audio settings.';
      case 'not-allowed':
        return 'Microphone access denied. Please grant permission in browser settings.';
      case 'network':
        return 'Network error. Please check your connection.';
      default:
        return `Speech recognition error: ${error}`;
    }
  };

  const startListening = () => {
    if (!recognitionRef.current || isListening || disabled) return;

    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      onError?.('Failed to start speech recognition');
    }
  };

  const stopListening = () => {
    if (!recognitionRef.current || !isListening) return;

    recognitionRef.current.stop();
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSpeechRecognitionSupported()) {
    return (
      <button
        className="voice-input-button unsupported"
        disabled
        title="Speech recognition not supported in this browser"
      >
        🎤
      </button>
    );
  }

  return (
    <div className="voice-input-container">
      <button
        className={`voice-input-button ${isListening ? 'listening' : ''}`}
        onClick={toggleListening}
        disabled={disabled}
        title={isListening ? 'Stop listening' : 'Start voice input'}
      >
        {isListening ? '🔴' : '🎤'}
      </button>
      {interimTranscript && (
        <div className="interim-transcript">
          {interimTranscript}
        </div>
      )}
    </div>
  );
}
