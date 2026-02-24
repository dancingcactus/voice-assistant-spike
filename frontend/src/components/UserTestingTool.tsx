import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { UserWithType, CreateTestUserRequest } from '../services/api';
import './UserTestingTool.css';

export default function UserTestingTool() {
  const [users, setUsers] = useState<UserWithType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);

  // Create user form state
  const [startingChapter, setStartingChapter] = useState(1);
  const [tags, setTags] = useState('');
  const [initialMemories, setInitialMemories] = useState<Array<{content: string; category: string; importance: number}>>([]);
  const [newMemoryContent, setNewMemoryContent] = useState('');
  const [newMemoryCategory, setNewMemoryCategory] = useState('preference');
  const [newMemoryImportance, setNewMemoryImportance] = useState(5);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listUsersWithType();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      const request: CreateTestUserRequest = {
        starting_chapter: startingChapter,
        tags: tags.split(',').map(t => t.trim()).filter(t => t),
        initial_memories: initialMemories.length > 0 ? initialMemories.map(m => ({
          content: m.content,
          category: m.category,
          importance: m.importance,
          verified: true
        })) : undefined
      };

      await apiClient.createTestUser(request);
      setShowCreateModal(false);

      // Reset form
      setStartingChapter(1);
      setTags('');
      setInitialMemories([]);

      // Reload users
      loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await apiClient.deleteTestUser(userId);
      setShowDeleteModal(null);
      loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  const handleExportUser = async (userId: string) => {
    try {
      const data = await apiClient.exportUserData(userId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${userId}_export_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export user');
    }
  };

  const addMemory = () => {
    if (newMemoryContent.trim()) {
      setInitialMemories([...initialMemories, {
        content: newMemoryContent.trim(),
        category: newMemoryCategory,
        importance: newMemoryImportance
      }]);
      setNewMemoryContent('');
      setNewMemoryCategory('preference');
      setNewMemoryImportance(5);
    }
  };

  const removeMemory = (index: number) => {
    setInitialMemories(initialMemories.filter((_, i) => i !== index));
  };

  if (loading) {
    return <div className="user-testing-tool"><div className="loading">Loading users...</div></div>;
  }

  const userToDelete = users.find(u => u.user_id === showDeleteModal);

  return (
    <div className="user-testing-tool">
      <h1>User Testing Tool</h1>
      <p className="subtitle">Create, manage, and switch between test users for isolated testing scenarios</p>

      {error && <div className="error">{error}</div>}

      <div className="header-actions">
        <div>
          <strong>{users.length}</strong> user{users.length !== 1 ? 's' : ''} total
          {' '}| <strong>{users.filter(u => u.type === 'production').length}</strong> production
          {' '}| <strong>{users.filter(u => u.type === 'test').length}</strong> test
        </div>
        <button className="create-user-btn" onClick={() => setShowCreateModal(true)}>
          + Create Test User
        </button>
      </div>

      <div className="users-grid">
        {users.map(user => (
          <div key={user.user_id} className={`user-card ${user.type}`}>
            <div className="user-card-badges">
              <div className={`user-type-badge ${user.type}`}>{user.type}</div>
              {user.metadata?.source === 'bulk_testing' && (
                <span className="badge badge-bulk-test">BULK TEST</span>
              )}
            </div>

            <h3>{user.user_id}</h3>

            <div className="user-stats">
              <div className="stat">
                <div className="stat-label">Chapter</div>
                <div className="stat-value">{user.current_chapter}</div>
              </div>
              <div className="stat">
                <div className="stat-label">Interactions</div>
                <div className="stat-value">{user.interaction_count}</div>
              </div>
            </div>

            {user.tags && user.tags.length > 0 && (
              <div className="user-tags">
                {user.tags.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
              </div>
            )}

            <div className="user-actions">
              <button
                className="action-btn secondary"
                onClick={() => handleExportUser(user.user_id)}
              >
                Export
              </button>
              <button
                className="action-btn danger"
                onClick={() => setShowDeleteModal(user.user_id)}
                disabled={user.type === 'production'}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create Test User</h2>

            <div className="form-group">
              <label>Starting Chapter</label>
              <select value={startingChapter} onChange={e => setStartingChapter(parseInt(e.target.value))}>
                <option value="1">Chapter 1 - Awakening</option>
                <option value="2">Chapter 2 - Expansion (Hank arrives)</option>
                <option value="3">Chapter 3 - Rex enters</option>
              </select>
            </div>

            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                value={tags}
                onChange={e => setTags(e.target.value)}
                placeholder="testing, chapter1, debug"
              />
            </div>

            <div className="form-group">
              <label>Initial Memories</label>

              <div style={{display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '10px', marginBottom: '10px'}}>
                <input
                  type="text"
                  value={newMemoryContent}
                  onChange={e => setNewMemoryContent(e.target.value)}
                  placeholder="Memory content..."
                />
                <select value={newMemoryCategory} onChange={e => setNewMemoryCategory(e.target.value)}>
                  <option value="preference">Preference</option>
                  <option value="dietary_restriction">Dietary</option>
                  <option value="fact">Fact</option>
                  <option value="relationship">Relationship</option>
                </select>
                <select value={newMemoryImportance} onChange={e => setNewMemoryImportance(parseInt(e.target.value))}>
                  {[1,2,3,4,5,6,7,8,9,10].map(i => (
                    <option key={i} value={i}>Importance: {i}</option>
                  ))}
                </select>
              </div>

              <button className="add-memory-btn" onClick={addMemory}>Add Memory</button>

              {initialMemories.length > 0 && (
                <div className="memories-list">
                  {initialMemories.map((mem, i) => (
                    <div key={i} className="memory-item">
                      <div className="content">
                        <strong>{mem.category}</strong> ({mem.importance}/10): {mem.content}
                      </div>
                      <button className="remove-btn" onClick={() => removeMemory(i)}>Remove</button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="primary-btn" onClick={handleCreateUser}>Create User</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && userToDelete && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Delete User</h2>

            {userToDelete.type === 'production' ? (
              <div className="confirmation-text">
                <strong>Cannot delete production user!</strong>
                <p>Production users are protected from deletion for safety.</p>
              </div>
            ) : (
              <>
                <div className="confirmation-text">
                  <strong>This action cannot be undone!</strong>
                  <p>You are about to delete user: <strong>{userToDelete.user_id}</strong></p>
                  <ul>
                    <li>Chapter: {userToDelete.current_chapter}</li>
                    <li>Interactions: {userToDelete.interaction_count}</li>
                    <li>All memories will be deleted</li>
                    <li>All conversation history will be deleted</li>
                  </ul>
                </div>

                <div className="modal-actions">
                  <button className="cancel-btn" onClick={() => setShowDeleteModal(null)}>Cancel</button>
                  <button className="action-btn danger" onClick={() => handleDeleteUser(userToDelete.user_id)}>
                    Delete User
                  </button>
                </div>
              </>
            )}

            {userToDelete.type === 'production' && (
              <div className="modal-actions">
                <button className="cancel-btn" onClick={() => setShowDeleteModal(null)}>Close</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
