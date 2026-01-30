/**
 * Observability Dashboard - Home Page
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type UserSummary } from '../services/api';
import { StoryBeatTool } from './StoryBeatTool';
import { MemoryTool } from './MemoryTool';
import UserTestingTool from './UserTestingTool';
import { ToolCallsTool } from './ToolCallsTool';
import { CharacterTool } from './CharacterTool';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { LoadingSpinner } from './LoadingSpinner';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import './Dashboard.css';
import './LoadingSpinner.css';

export function Dashboard() {
  const [currentView, setCurrentView] = useState<'home' | 'story' | 'memory' | 'users' | 'toolcalls' | 'characters'>('home');
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
    { key: '1', handler: () => setCurrentView('home'), description: 'Go to Home' },
    { key: '2', handler: () => setCurrentView('story'), description: 'Go to Story Beats' },
    { key: '3', handler: () => setCurrentView('memory'), description: 'Go to Memory' },
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

  const selectedUser = users?.find((u: UserSummary) => u.user_id === selectedUserId);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🎭 Hey Chat! Observability Dashboard</h1>
        <nav className="main-nav">
          <button
            className={currentView === 'home' ? 'active' : ''}
            onClick={() => setCurrentView('home')}
          >
            Home
          </button>
          <button
            className={currentView === 'story' ? 'active' : ''}
            onClick={() => setCurrentView('story')}
          >
            Story Beats
          </button>
          <button
            className={currentView === 'memory' ? 'active' : ''}
            onClick={() => setCurrentView('memory')}
          >
            Memories
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
      ) : currentView === 'memory' ? (
        <MemoryTool userId={selectedUserId} />
      ) : currentView === 'users' ? (
        <UserTestingTool />
      ) : currentView === 'toolcalls' ? (
        <ToolCallsTool userId={selectedUserId} />
      ) : currentView === 'characters' ? (
        <CharacterTool userId={selectedUserId} />
      ) : (
        <div className="dashboard-content">
          {/* Welcome Section */}
          <section className="info-card welcome-card">
            <h2>🎭 Welcome to Observability Dashboard</h2>
            <p>
              Comprehensive tooling for debugging, testing, and inspecting the Hey Chat! voice assistant system.
              All Phase 1.5 milestones are complete.
            </p>
          </section>

          {/* Quick Actions */}
          <section className="info-card">
            <h3>Quick Actions</h3>
            <div className="quick-actions">
              <button className="action-card" onClick={() => setCurrentView('story')}>
                <span className="action-icon">📖</span>
                <span className="action-title">Story Beats</span>
                <span className="action-desc">View and trigger story beats</span>
              </button>
              <button className="action-card" onClick={() => setCurrentView('memory')}>
                <span className="action-icon">🧠</span>
                <span className="action-title">Memories</span>
                <span className="action-desc">Manage user memories</span>
              </button>
              <button className="action-card" onClick={() => setCurrentView('users')}>
                <span className="action-icon">👥</span>
                <span className="action-title">Test Users</span>
                <span className="action-desc">Create and manage test users</span>
              </button>
              <button className="action-card" onClick={() => setCurrentView('toolcalls')}>
                <span className="action-icon">🔧</span>
                <span className="action-title">Tool Calls</span>
                <span className="action-desc">Inspect API calls and performance</span>
              </button>
              <button className="action-card" onClick={() => setCurrentView('characters')}>
                <span className="action-icon">🎭</span>
                <span className="action-title">Characters</span>
                <span className="action-desc">View character configurations</span>
              </button>
            </div>
          </section>

          {/* Current User Profile */}
          {selectedUser && (
            <section className="info-card highlight">
              <h3>Current User: {selectedUser.user_id}</h3>
              <div className="profile-info">
                <div className="profile-field">
                  <label>User ID:</label>
                  <span>{selectedUser.user_id}</span>
                </div>
                <div className="profile-field">
                  <label>Current Chapter:</label>
                  <span>Chapter {selectedUser.current_chapter}</span>
                </div>
                <div className="profile-field">
                  <label>Interactions:</label>
                  <span>{selectedUser.interaction_count}</span>
                </div>
                <div className="profile-field">
                  <label>Type:</label>
                  <span>{selectedUser.user_id === 'user_justin' ? <span className="badge production">PRODUCTION</span> : 'Test User'}</span>
                </div>
              </div>
            </section>
          )}

          {/* System Overview */}
          <section className="info-card">
            <h3>System Overview</h3>
            <div className="system-stats">
              <div className="stat-card">
                <div className="stat-value">{users?.length || 0}</div>
                <div className="stat-label">Total Users</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">6</div>
                <div className="stat-label">Available Tools</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">1</div>
                <div className="stat-label">Active Character</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">7/7</div>
                <div className="stat-label">Milestones Complete</div>
              </div>
            </div>
          </section>

          {/* All Users */}
          <section className="info-card">
            <h3>All Users ({users?.length || 0})</h3>
            <div className="users-list">
              {users?.map((user: UserSummary) => (
                <div
                  key={user.user_id}
                  className={`user-card ${user.user_id === selectedUserId ? 'selected' : ''}`}
                  onClick={() => setSelectedUserId(user.user_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="user-header">
                    <strong>{user.user_id}</strong>
                    {user.user_id === 'user_justin' && (
                      <span className="badge production">PRODUCTION</span>
                    )}
                  </div>
                  <div className="user-stats">
                    <span>Chapter {user.current_chapter}</span>
                    <span>•</span>
                    <span>{user.interaction_count} interactions</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Phase 1.5 Milestones */}
          <section className="info-card">
            <h3>Phase 1.5 Milestones</h3>
            <ul className="next-steps">
              <li>✅ Milestone 1: Foundation & Data Access</li>
              <li>✅ Milestone 2: Story Beat Tool</li>
              <li>✅ Milestone 3: Memory Tool</li>
              <li>✅ Milestone 4: User Testing Tool</li>
              <li>✅ Milestone 5: Tool Calls Inspection</li>
              <li>✅ Milestone 6: Memory Extraction & Character Tool</li>
              <li>✅ Milestone 7: Polish & Integration</li>
            </ul>
          </section>
        </div>
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
