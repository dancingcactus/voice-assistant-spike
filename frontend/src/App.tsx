import { useState, useEffect, useRef } from 'react';
import { Send, Copy, CheckCircle, XCircle } from 'lucide-react';
import { WebSocketService } from './services/websocket';
import type { Message } from './services/websocket';
import { AudioPlayer } from './components/AudioPlayer';
import { VoiceInput } from './components/VoiceInput';
import { apiClient } from './services/api';
import type { UserSummary, AutoAdvanceNotification } from './services/api';
import { ThemeToggle } from './components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

import { cn } from '@/lib/utils';

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
  const [characterDisplayNames, setCharacterDisplayNames] = useState<Record<string, string>>({});
  const wsRef = useRef<WebSocketService | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocketService();
    wsRef.current = ws;

    ws.onMessage((message) => {
      setMessages((prev) => {
        const lastUserMessage = [...prev].reverse().find(m => m.role === 'user');
        const inputMode = lastUserMessage?.inputMode || 'chat';
        return [...prev, { ...message, inputMode }];
      });
    });

    ws.onStatus((status, message) => {
      setConnectionStatus(status);
      setStatusMessage(message || '');
      if (message === 'thinking') setIsThinking(true);
      else if (status === 'connected') setIsThinking(false);
    });

    ws.onError((error) => {
      console.error('WebSocket error:', error);
      setStatusMessage(error);
    });

    ws.connect();
    return () => { ws.disconnect(); };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const userList = await apiClient.listUsers();
        setUsers(userList);
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
    const loadCharacters = async () => {
      try {
        const { characters } = await apiClient.listCharacters();
        const names: Record<string, string> = {};
        for (const char of characters) {
          names[char.id] = char.display_name || char.name;
        }
        setCharacterDisplayNames(names);
      } catch (error) {
        console.error('Failed to load characters:', error);
      }
    };
    loadCharacters();
  }, []);

  useEffect(() => {
    const pollAutoAdvance = async () => {
      if (!selectedUserId) return;
      try {
        const beats = await apiClient.getAutoAdvanceReady(selectedUserId);
        setAutoAdvanceBeats(beats);
      } catch (error) {
        console.error('Failed to poll auto-advance beats:', error);
      }
    };
    pollAutoAdvance();
    const interval = setInterval(pollAutoAdvance, 5000);
    return () => clearInterval(interval);
  }, [selectedUserId]);

  const handleSend = () => {
    if (!inputText.trim() || !wsRef.current) return;
    const userMessage: Message = {
      role: 'user', content: inputText,
      timestamp: new Date().toISOString(), inputMode: 'chat'
    };
    setMessages((prev) => [...prev, userMessage]);
    wsRef.current.sendMessage(inputText, 'chat', selectedUserId);
    setInputText('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleVoiceTranscript = (text: string) => {
    if (!wsRef.current) return;
    const userMessage: Message = {
      role: 'user', content: text,
      timestamp: new Date().toISOString(), inputMode: 'voice'
    };
    setMessages((prev) => [...prev, userMessage]);
    wsRef.current.sendMessage(text, 'voice', selectedUserId);
  };

  const handleVoiceError = (error: string) => {
    console.error('Voice input error:', error);
    setStatusMessage(error);
  };

  const handleDeliverBeat = async (beatId: string) => {
    try {
      await apiClient.deliverAutoAdvanceBeat(selectedUserId, beatId);
      setAutoAdvanceBeats(beats => beats.filter(b => b.beat_id !== beatId));
    } catch (error) {
      console.error('Failed to deliver beat:', error);
      setStatusMessage('Failed to deliver story beat');
    }
  };

  const getMessageRole = (message: Message): string => {
    if (message.role === 'user') return 'You';
    if (message.character) return characterDisplayNames[message.character] || message.character;
    return 'Assistant';
  };

  const copyConversation = async () => {
    const text = messages
      .map((message) => `${getMessageRole(message)}: ${message.content}`)
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

  const statusColors: Record<string, string> = {
    connected: 'bg-green-500',
    disconnected: 'bg-red-500',
    error: 'bg-yellow-500',
  };

  const statusLabels: Record<string, string> = {
    connected: 'Connected',
    disconnected: 'Disconnected',
    error: 'Error',
  };

  return (
    <div className="flex h-screen flex-col bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      {/* ── Header ── */}
      <header className="flex h-14 items-center justify-between border-b border-[hsl(var(--border))] px-6 shrink-0">
        <h1 className="text-lg font-semibold text-[hsl(var(--primary))]">Aperture Assist</h1>
        <div className="flex items-center gap-3">
          {/* User selector */}
          <div className="flex items-center gap-2">
            <label htmlFor="user-select" className="text-xs text-[hsl(var(--muted-foreground))]">User:</label>
            <Select
              id="user-select"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="h-8 text-xs w-44"
            >
              {users.map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.user_id}{user.user_id === 'user_justin' ? ' (Production)' : ''}
                </option>
              ))}
            </Select>
          </div>

          {/* Copy conversation */}
          <Button
            variant="outline"
            size="sm"
            onClick={copyConversation}
            disabled={messages.length === 0}
            className={cn(
              'text-xs h-8 gap-1.5',
              copyStatus === 'copied' && 'border-green-500 text-green-500',
              copyStatus === 'error'  && 'border-red-500 text-red-500'
            )}
          >
            {copyStatus === 'copied' ? <CheckCircle className="h-3.5 w-3.5" /> :
             copyStatus === 'error'  ? <XCircle className="h-3.5 w-3.5" /> :
                                       <Copy className="h-3.5 w-3.5" />}
            {copyStatus === 'copied' ? 'Copied!' : copyStatus === 'error' ? 'Failed' : 'Copy'}
          </Button>

          {/* Connection status */}
          <div className="flex items-center gap-1.5 text-xs text-[hsl(var(--muted-foreground))]">
            <span className={cn('h-2 w-2 rounded-full', statusColors[connectionStatus])} />
            {statusLabels[connectionStatus]}
            {statusMessage && `: ${statusMessage}`}
          </div>

          <ThemeToggle />
        </div>
      </header>

      {/* ── Chat Area (centered) ── */}
      <main className="flex flex-1 flex-col overflow-hidden items-center">
        <div className="flex flex-1 flex-col w-full max-w-3xl overflow-hidden">
          {/* Auto-advance notification banner */}
          {autoAdvanceBeats.length > 0 && (
            <div className="mx-4 mt-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 p-4 shadow-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">📖</span>
                <h3 className="font-semibold text-white text-sm">Story Update Available</h3>
              </div>
              <h4 className="text-white/90 text-sm font-medium mb-1">{autoAdvanceBeats[0].name}</h4>
              <p className="text-white/80 text-xs mb-3 line-clamp-2">
                {autoAdvanceBeats[0].content.substring(0, 150)}
                {autoAdvanceBeats[0].content.length > 150 ? '...' : ''}
              </p>
              <div className="flex items-center gap-3">
                <Button
                  size="sm"
                  className="bg-white text-violet-600 hover:bg-white/90 h-8 text-xs font-semibold"
                  onClick={() => {
                    if (confirm(`Continue story with "${autoAdvanceBeats[0].name}"?`)) {
                      handleDeliverBeat(autoAdvanceBeats[0].beat_id);
                    }
                  }}
                >
                  Continue Story
                </Button>
                {autoAdvanceBeats.length > 1 && (
                  <span className="text-white/70 text-xs">+{autoAdvanceBeats.length - 1} more</span>
                )}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-16">
                <div className="rounded-full bg-[hsl(var(--muted))] p-4 mb-4">
                  <span className="text-3xl">💬</span>
                </div>
                <p className="text-[hsl(var(--muted-foreground))] font-medium">
                  Chat with {characterDisplayNames['delilah'] || 'Delilah'}
                </p>
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 italic">
                  Phase 6: TTS Integration — Voice Input &amp; Audio Output
                </p>
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  'flex flex-col max-w-[80%] animate-in fade-in slide-in-from-bottom-2 duration-300',
                  message.role === 'user' ? 'self-end items-end ml-auto' : 'self-start items-start'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn(
                    'text-xs font-semibold',
                    message.role === 'user' ? 'text-[hsl(var(--muted-foreground))]' : 'text-[hsl(var(--primary))]'
                  )}>
                    {getMessageRole(message)}
                  </span>
                  <span className="text-xs text-[hsl(var(--muted-foreground))] opacity-60">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className={cn(
                  'rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap',
                  message.role === 'user'
                    ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded-br-sm'
                    : 'bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] rounded-bl-sm border border-[hsl(var(--border))]'
                )}>
                  {message.content}
                </div>
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
                  <div className="mt-1 text-xs text-[hsl(var(--muted-foreground))] opacity-50 font-mono">
                    Tokens: {message.metadata.tokens_used} •{' '}
                    Time: {message.metadata.response_time?.toFixed(2)}s
                    {message.metadata.voice_mode && ` • Voice: ${message.metadata.voice_mode}`}
                  </div>
                )}
              </div>
            ))}
            {isThinking && (
              <div className="flex flex-col items-start max-w-[80%]">
                <span className="text-xs font-semibold text-[hsl(var(--primary))] mb-1">
                  {characterDisplayNames['delilah'] || 'Delilah'}
                </span>
                <div className="rounded-2xl rounded-bl-sm bg-[hsl(var(--muted))] border border-[hsl(var(--border))] px-4 py-3 flex gap-1.5 items-center">
                  {[0, 0.2, 0.4].map((delay, i) => (
                    <span
                      key={i}
                      className="h-2 w-2 rounded-full bg-[hsl(var(--primary))] animate-bounce"
                      style={{ animationDelay: `${delay}s` }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-[hsl(var(--border))] bg-[hsl(var(--background))] px-4 py-3">
            <div className="flex items-end gap-2">
              <VoiceInput
                onTranscript={handleVoiceTranscript}
                onError={handleVoiceError}
                disabled={connectionStatus !== 'connected'}
              />
              <Textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type a message or use voice input…"
                disabled={connectionStatus !== 'connected'}
                rows={2}
                className="flex-1 resize-none text-sm"
              />
              <Button
                onClick={handleSend}
                disabled={connectionStatus !== 'connected' || !inputText.trim()}
                size="icon"
                className="h-10 w-10 shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-1 text-xs text-center text-[hsl(var(--muted-foreground))]">
              Press <kbd className="rounded bg-[hsl(var(--muted))] border border-[hsl(var(--border))] px-1 font-mono">Enter</kbd> to send,{' '}
              <kbd className="rounded bg-[hsl(var(--muted))] border border-[hsl(var(--border))] px-1 font-mono">Shift+Enter</kbd> for new line
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
