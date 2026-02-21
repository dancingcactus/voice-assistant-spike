import { useState, useEffect, useRef } from 'react';
import './App.css';
import { WebSocketService } from './services/websocket';
import type { Message } from './services/websocket';
import { AudioPlayer } from './components/AudioPlayer';
import { VoiceInput } from './components/VoiceInput';
import { apiClient } from './services/api';
import type { UserSummary, AutoAdvanceNotification } from './services/api';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [statusMessage, setStatusMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string>('user_justin');
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [autoAdvanceBeats, setAutoAdvanceBeats] = useState<AutoAdvanceNotification[]>([]);
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
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

  useEffect(() => {
    // Load available users
    const loadUsers = async () => {
      try {
        const userList = await apiClient.listUsers();
        setUsers(userList);
        // Auto-select user_justin if available, otherwise first user
        if (userList.length > 0 && !selectedUserId) {
          const userJustin = userList.find(u => u.user_id === 'user_justin');
          setSelectedUserId(userJustin?.user_id || userList[0].user_id);
        }
      } catch (error) {
        console.error('Failed to load users:', error);
      }
    };
    loadUsers();
  }, []);

  useEffect(() => {
    // Poll for auto-advance beats every 5 seconds
    const pollAutoAdvance = async () => {
      if (!selectedUserId) return;

      try {
        const beats = await apiClient.getAutoAdvanceReady(selectedUserId);
        setAutoAdvanceBeats(beats);
      } catch (error) {
        console.error('Failed to poll auto-advance beats:', error);
      }
    };

    // Poll immediately on mount or user change
    pollAutoAdvance();

    // Then poll every 5 seconds
    const interval = setInterval(pollAutoAdvance, 5000);

    return () => clearInterval(interval);
  }, [selectedUserId]);

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

    // Send to backend with input mode and userId
    wsRef.current.sendMessage(inputText, 'chat', selectedUserId);

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

    // Send to backend with voice mode and userId
    wsRef.current.sendMessage(text, 'voice', selectedUserId);
  };

  const handleVoiceError = (error: string) => {
    console.error('Voice input error:', error);
    setStatusMessage(error);
  };

  const handleDeliverBeat = async (beatId: string) => {
    try {
      await apiClient.deliverAutoAdvanceBeat(selectedUserId, beatId);
      // Remove the delivered beat from the list
      setAutoAdvanceBeats(beats => beats.filter(b => b.beat_id !== beatId));
    } catch (error) {
      console.error('Failed to deliver beat:', error);
      setStatusMessage('Failed to deliver story beat');
    }
  };

  const copyConversation = async () => {
    const text = messages
      .map((message) => {
        const role = message.role === 'user' ? 'User' : (message.character || 'Delilah');
        return `${role}: ${message.content}`;
      })
      .join('\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus('copied');
    } catch {
      setCopyStatus('error');
    } finally {
      setTimeout(() => setCopyStatus('idle'), 2000);
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
        <div className="header-controls">
          <div className="user-selector">
            <label htmlFor="user-select">User:</label>
            <select
              id="user-select"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="user-select"
            >
              {users.map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.user_id}
                  {user.user_id === 'user_justin' ? ' (Production)' : ''}
                </option>
              ))}
            </select>
          </div>
          <button
            className={`btn-copy-conversation${copyStatus !== 'idle' ? ` btn-copy-${copyStatus}` : ''}`}
            onClick={copyConversation}
            disabled={messages.length === 0}
            title="Copy conversation to clipboard"
          >
            {copyStatus === 'copied' ? '✓ Copied!' : copyStatus === 'error' ? '✗ Failed' : 'Copy Conversation'}
          </button>
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
        </div>
      </header>

      <main className="chat-container">
        {/* Auto-advance notification banner */}
        {autoAdvanceBeats.length > 0 && (
          <div className="auto-advance-banner">
            <div className="banner-header">
              <span className="banner-icon">📖</span>
              <h3>Story Update Available</h3>
            </div>
            <div className="banner-content">
              <h4>{autoAdvanceBeats[0].name}</h4>
              <p className="content-preview">
                {autoAdvanceBeats[0].content.substring(0, 150)}
                {autoAdvanceBeats[0].content.length > 150 ? '...' : ''}
              </p>
            </div>
            <div className="banner-actions">
              <button
                className="btn-continue-story"
                onClick={() => {
                  if (confirm(`Continue story with "${autoAdvanceBeats[0].name}"?`)) {
                    handleDeliverBeat(autoAdvanceBeats[0].beat_id);
                  }
                }}
              >
                Continue Story
              </button>
              {autoAdvanceBeats.length > 1 && (
                <span className="more-beats">+{autoAdvanceBeats.length - 1} more</span>
              )}
            </div>
          </div>
        )}

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
