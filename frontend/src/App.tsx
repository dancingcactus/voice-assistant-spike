import { useState, useEffect, useRef } from 'react';
import './App.css';
import { WebSocketService } from './services/websocket';
import type { Message } from './services/websocket';
import { AudioPlayer } from './components/AudioPlayer';
import { VoiceInput } from './components/VoiceInput';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [statusMessage, setStatusMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const wsRef = useRef<WebSocketService | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize WebSocket service
    const ws = new WebSocketService();
    wsRef.current = ws;

    // Set up event handlers
    ws.onMessage((message) => {
      setMessages((prev) => {
        // Find the most recent user message to determine input mode
        const lastUserMessage = [...prev].reverse().find(m => m.role === 'user');
        const inputMode = lastUserMessage?.inputMode || 'chat';

        // Add input mode to assistant message for rendering logic
        return [...prev, { ...message, inputMode }];
      });
    });

    ws.onStatus((status, message) => {
      setConnectionStatus(status);
      setStatusMessage(message || '');

      // Handle thinking status
      if (message === 'thinking') {
        setIsThinking(true);
      } else if (status === 'connected') {
        setIsThinking(false);
      }
    });

    ws.onError((error) => {
      console.error('WebSocket error:', error);
      setStatusMessage(error);
    });

    // Connect
    ws.connect();

    // Cleanup on unmount
    return () => {
      ws.disconnect();
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputText.trim() || !wsRef.current) return;

    // Add user message to display
    const userMessage: Message = {
      role: 'user',
      content: inputText,
      timestamp: new Date().toISOString(),
      inputMode: 'chat'
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to backend with input mode
    wsRef.current.sendMessage(inputText, 'chat');

    // Clear input
    setInputText('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceTranscript = (text: string) => {
    // For voice input, send immediately as voice mode
    if (!wsRef.current) return;

    // Add user message to display
    const userMessage: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      inputMode: 'voice'
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to backend with voice mode
    wsRef.current.sendMessage(text, 'voice');
  };

  const handleVoiceError = (error: string) => {
    console.error('Voice input error:', error);
    setStatusMessage(error);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return '#22c55e';
      case 'disconnected':
        return '#ef4444';
      case 'error':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Aperture Assist</h1>
        <div className="status-bar">
          <div
            className="status-indicator"
            style={{ backgroundColor: getStatusColor() }}
          />
          <span className="status-text">
            {getStatusText()}
            {statusMessage && `: ${statusMessage}`}
          </span>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p>Send a message to start chatting with Delilah!</p>
              <p className="phase-indicator">Phase 6: TTS Integration - Voice Input & Audio Output</p>
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role}`}
            >
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? 'You' : message.character || 'Delilah'}
                </span>
                <span className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="message-content">{message.content}</div>
              {message.role === 'assistant' && message.inputMode === 'voice' && message.audioUrl && (
                <AudioPlayer audioUrl={message.audioUrl} autoPlay={true} />
              )}
              {message.role === 'assistant' && message.inputMode === 'chat' && (
                <AudioPlayer
                  text={message.content}
                  character={message.character || 'delilah'}
                  voiceMode={message.metadata?.voice_mode}
                  wsService={wsRef.current}
                  autoPlay={false}
                />
              )}
              {message.metadata?.tokens_used && (
                <div className="message-metadata">
                  Tokens: {message.metadata.tokens_used} |
                  Time: {message.metadata.response_time?.toFixed(2)}s
                  {message.metadata.voice_mode && ` | Voice: ${message.metadata.voice_mode}`}
                </div>
              )}
            </div>
          ))}
          {isThinking && (
            <div className="message assistant thinking">
              <div className="message-header">
                <span className="message-role">Delilah</span>
              </div>
              <div className="message-content thinking-indicator">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            onError={handleVoiceError}
            disabled={connectionStatus !== 'connected'}
          />
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type a message or use voice input..."
            disabled={connectionStatus !== 'connected'}
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={connectionStatus !== 'connected' || !inputText.trim()}
          >
            Send
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;
