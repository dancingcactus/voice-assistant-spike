/**
 * Observability Dashboard - Home Page
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type UserSummary } from '../services/api';
import { StoryBeatTool } from './StoryBeatTool';
import { MemoryTool } from './MemoryTool';
import UserTestingTool from './UserTestingTool';
import { ToolCallsTool } from './ToolCallsTool';
import './Dashboard.css';

export function Dashboard() {
  const [currentView, setCurrentView] = useState<'home' | 'story' | 'memory' | 'users' | 'toolcalls'>('home');
  const [selectedUserId, setSelectedUserId] = useState<string>('default_user');

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.health(),
  });

  const { data: users, isLoading: usersLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.listUsers(),
  });

  if (healthLoading || usersLoading) {
    return (
      <div className="dashboard">
        <div className="loading">Loading...</div>
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

  const userJustin = users?.find((u: UserSummary) => u.user_id === 'user_justin');

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
        </nav>
        <div className="health-indicator">
          <span className={`status-dot ${health?.status === 'ok' ? 'healthy' : 'error'}`}></span>
          <span>{health?.status === 'ok' ? 'Connected' : 'Error'}</span>
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
      ) : (
        <div className="dashboard-content">
          <section className="info-card">
          <h2>Welcome!</h2>
          <p>
            This is the Observability Dashboard for Phase 1.5 of the Hey Chat! voice assistant system.
            Use the tools here to debug, test, and inspect the system state.
          </p>
        </section>

        {userJustin && (
          <section className="info-card highlight">
            <h3>Your Profile</h3>
            <div className="profile-info">
              <div className="profile-field">
                <label>User ID:</label>
                <span>{userJustin.user_id}</span>
              </div>
              <div className="profile-field">
                <label>Current Chapter:</label>
                <span>Chapter {userJustin.current_chapter}</span>
              </div>
              <div className="profile-field">
                <label>Interactions:</label>
                <span>{userJustin.interaction_count}</span>
              </div>
              <div className="profile-field">
                <label>Progress:</label>
                <span>5/8 beats delivered (62%)</span>
              </div>
            </div>
          </section>
        )}

        <section className="info-card">
          <h3>All Users ({users?.length || 0})</h3>
          <div className="users-list">
            {users?.map((user: UserSummary) => (
              <div key={user.user_id} className="user-card">
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

        <section className="info-card">
          <h3>Next Steps</h3>
          <ul className="next-steps">
            <li>✅ Milestone 1: Foundation & Data Access (Complete!)</li>
            <li>✅ Milestone 2: Story Beat Tool (Complete!)</li>
            <li>✅ Milestone 3: Memory Tool (Complete!)</li>
            <li>✅ Milestone 4: User Testing Tool (Complete!)</li>
            <li>⏸️ Milestone 5: Tool Calls Inspection (Coming soon)</li>
            <li>⏸️ Milestone 6: Character Tool (Coming soon)</li>
            <li>⏸️ Milestone 7: Polish & Integration (Coming soon)</li>
          </ul>
        </section>
        </div>
      )}

      <footer className="dashboard-footer">
        <p>Version {health?.version} • Last updated: {new Date(health?.timestamp || '').toLocaleTimeString()}</p>
      </footer>
    </div>
  );
}
