/**
 * WebSocket service for real-time communication with backend
 * Phase 1: Basic message sending and receiving
 */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  audioUrl?: string;
  character?: string;
  inputMode?: 'voice' | 'chat';  // Track how the message was input
  metadata?: {
    tokens_used?: number;
    response_time?: number;
    voice_mode?: string;
    [key: string]: any;
  };
}

export interface WebSocketMessage {
  type: 'user_message' | 'assistant_response' | 'error' | 'status';
  data: any;
  timestamp: string;
}

export type MessageHandler = (message: Message) => void;
export type StatusHandler = (status: 'connected' | 'disconnected' | 'error', message?: string) => void;
export type ErrorHandler = (error: string) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  private messageHandlers: MessageHandler[] = [];
  private statusHandlers: StatusHandler[] = [];
  private errorHandlers: ErrorHandler[] = [];

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyStatus('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const wsMessage: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(wsMessage);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.notifyStatus('error', 'WebSocket connection error');
      };

      this.ws.onclose = () => {
        console.log('❌ WebSocket disconnected');
        this.notifyStatus('disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.notifyStatus('error', 'Failed to create connection');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(text: string, inputMode: 'voice' | 'chat' = 'chat'): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.notifyError('WebSocket is not connected');
      return;
    }

    const message: WebSocketMessage = {
      type: 'user_message',
      data: {
        text,
        input_mode: inputMode
      },
      timestamp: new Date().toISOString()
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Request TTS generation for a given text
   * @param text Text to convert to speech
   * @param characterId Character ID for voice selection
   * @param voiceMode Optional voice mode
   * @returns Promise with audio URL
   */
  async requestTTS(text: string, characterId: string = 'delilah', voiceMode?: string): Promise<string> {
    const response = await fetch('http://localhost:8000/api/tts/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        character_id: characterId,
        voice_mode: voiceMode
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'TTS generation failed');
    }

    const data = await response.json();
    return data.audio_url;
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter(h => h !== handler);
    };
  }

  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.push(handler);
    return () => {
      this.errorHandlers = this.errorHandlers.filter(h => h !== handler);
    };
  }

  private handleMessage(wsMessage: WebSocketMessage): void {
    switch (wsMessage.type) {
      case 'assistant_response':
        const message: Message = {
          role: 'assistant',
          content: wsMessage.data.text,
          timestamp: wsMessage.timestamp,
          audioUrl: wsMessage.data.audio_url,
          character: wsMessage.data.character,
          metadata: wsMessage.data.metadata
        };
        this.notifyMessage(message);
        // Clear thinking status when response arrives
        this.notifyStatus('connected');
        break;

      case 'status':
        console.log('Status:', wsMessage.data);
        if (wsMessage.data.status === 'connected') {
          this.notifyStatus('connected', wsMessage.data.message);
        } else if (wsMessage.data.status === 'thinking') {
          this.notifyStatus('connected', 'thinking');
        }
        break;

      case 'error':
        this.notifyError(wsMessage.data.error);
        break;

      default:
        console.log('Unknown message type:', wsMessage.type);
    }
  }

  private notifyMessage(message: Message): void {
    this.messageHandlers.forEach(handler => handler(message));
  }

  private notifyStatus(status: 'connected' | 'disconnected' | 'error', message?: string): void {
    this.statusHandlers.forEach(handler => handler(status, message));
  }

  private notifyError(error: string): void {
    this.errorHandlers.forEach(handler => handler(error));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      this.notifyStatus('error', 'Failed to reconnect after multiple attempts');
    }
  }
}
