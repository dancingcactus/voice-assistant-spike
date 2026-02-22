/**
 * Observability Dashboard - Home Page
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type UserSummary } from '../services/api';
import { StoryBeatTool } from './StoryBeatTool';
import { ToolsView } from './tools/ToolsView';
import UserTestingTool from './UserTestingTool';
import { ToolCallsTool } from './ToolCallsTool';
import { CharacterTool } from './CharacterTool';
import { SystemLogTool } from './SystemLogTool';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { LoadingSpinner } from './LoadingSpinner';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import './Dashboard.css';
import './LoadingSpinner.css';

export function Dashboard() {
  const [currentView, setCurrentView] = useState<'home' | 'story' | 'tools' | 'users' | 'toolcalls' | 'characters'>('home');
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [showShortcuts, setShowShortcuts] = useState(false);
  const userSelectRef = useRef<HTMLSelectElement>(null);

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.health(),
  });

  const { data: users, isLoading: usersLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.listUsers(),
  });

  // Keyboard shortcuts
  useKeyboardShortcuts([
    { key: '1', handler: () => setCurrentView('home'), description: 'Go to Logs' },
    { key: '2', handler: () => setCurrentView('story'), description: 'Go to Story Beats' },
    { key: '3', handler: () => setCurrentView('tools'), description: 'Go to Tools' },
    { key: '4', handler: () => setCurrentView('users'), description: 'Go to User Testing' },
    { key: '5', handler: () => setCurrentView('toolcalls'), description: 'Go to Tool Calls' },
    { key: '6', handler: () => setCurrentView('characters'), description: 'Go to Characters' },
    { key: 'u', ctrl: true, handler: () => userSelectRef.current?.focus(), description: 'Focus user selector' },
    { key: '?', shift: true, handler: () => setShowShortcuts(true), description: 'Show shortcuts' },
  ]);

  // Initialize selectedUserId to first available user (preferably user_justin) when users load
  useEffect(() => {
    if (!selectedUserId && users && users.length > 0) {
      const userJustin = users.find((u: UserSummary) => u.user_id === 'user_justin');
      setSelectedUserId(userJustin?.user_id || users[0].user_id);
    }
  }, [users, selectedUserId]);

  if (healthLoading || usersLoading) {
    return (
      <div className="dashboard">
        <LoadingSpinner text="Loading dashboard..." size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <h2>Connection Error</h2>
          <p>Unable to connect to API. Make sure the backend is running.</p>
          <p className="error-details">{String(error)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Hey Chat! Observability Dashboard</h1>
        <nav className="main-nav">
          <button
            className={currentView === 'home' ? 'active' : ''}
            onClick={() => setCurrentView('home')}
          >
            Logs
          </button>
          <button
            className={currentView === 'story' ? 'active' : ''}
            onClick={() => setCurrentView('story')}
          >
            Story Beats
          </button>
          <button
            className={currentView === 'tools' ? 'active' : ''}
            onClick={() => setCurrentView('tools')}
          >
            Tools
          </button>
          <button
            className={currentView === 'users' ? 'active' : ''}
            onClick={() => setCurrentView('users')}
          >
            User Testing
          </button>
          <button
            className={currentView === 'toolcalls' ? 'active' : ''}
            onClick={() => setCurrentView('toolcalls')}
          >
            Tool Calls
          </button>
          <button
            className={currentView === 'characters' ? 'active' : ''}
            onClick={() => setCurrentView('characters')}
          >
            Characters
          </button>
        </nav>
        <div className="header-controls">
          <div className="user-selector">
            <label htmlFor="user-select">User:</label>
            <select
              ref={userSelectRef}
              id="user-select"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="user-select"
            >
              {users?.map((user: UserSummary) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.user_id}
                  {user.user_id === 'user_justin' ? ' (Production)' : ''}
                </option>
              ))}
            </select>
          </div>
          <button
            className="help-button"
            onClick={() => setShowShortcuts(true)}
            title="Keyboard shortcuts (Shift+?)"
          >
            ?
          </button>
          <div className="health-indicator">
            <span className={`status-dot ${health?.status === 'ok' ? 'healthy' : 'error'}`}></span>
            <span>{health?.status === 'ok' ? 'Connected' : 'Error'}</span>
          </div>
        </div>
      </header>

      {currentView === 'story' ? (
        <StoryBeatTool userId={selectedUserId} />
      ) : currentView === 'tools' ? (
        <ToolsView userId={selectedUserId} />
      ) : currentView === 'users' ? (
        <UserTestingTool />
      ) : currentView === 'toolcalls' ? (
        <ToolCallsTool userId={selectedUserId} />
      ) : currentView === 'characters' ? (
        <CharacterTool userId={selectedUserId} />
      ) : (
        <SystemLogTool />
      )}

      <footer className="dashboard-footer">
        <p>Version {health?.version} • Last updated: {new Date(health?.timestamp || '').toLocaleTimeString()}</p>
        <p className="shortcuts-hint">Press <kbd className="key-hint">?</kbd> for keyboard shortcuts</p>
      </footer>

      <KeyboardShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
    </div>
  );
}
