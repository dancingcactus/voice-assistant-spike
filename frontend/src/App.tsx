import { useState, useEffect, useRef } from 'react';
import './App.css';
import { WebSocketService } from './services/websocket';
import type { Message } from './services/websocket';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [statusMessage, setStatusMessage] = useState('');
  const wsRef = useRef<WebSocketService | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize WebSocket service
    const ws = new WebSocketService();
    wsRef.current = ws;

    // Set up event handlers
    ws.onMessage((message) => {
      setMessages((prev) => [...prev, message]);
    });

    ws.onStatus((status, message) => {
      setConnectionStatus(status);
      setStatusMessage(message || '');
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
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to backend
    wsRef.current.sendMessage(inputText);

    // Clear input
    setInputText('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
              <p className="phase-indicator">Phase 1: Echo Mode</p>
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
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type a message..."
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
