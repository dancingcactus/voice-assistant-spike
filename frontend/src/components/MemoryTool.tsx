import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { Memory, CreateMemoryRequest, UpdateMemoryRequest, ContextPreview } from '../services/api';
import './MemoryTool.css';

interface MemoryToolProps {
  userId: string;
}

export const MemoryTool: React.FC<MemoryToolProps> = ({ userId }) => {
  const queryClient = useQueryClient();

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [importanceFilter, setImportanceFilter] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'recent' | 'importance' | 'access_count'>('recent');

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showContextModal, setShowContextModal] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  // Form state
  const [formData, setFormData] = useState<CreateMemoryRequest>({
    category: 'preference',
    content: '',
    source: 'manual_entry',
    importance: 5,
    verified: false,
    metadata: {}
  });

  // Load memories with React Query
  const { data: memories = [], isLoading: loading, error } = useQuery({
    queryKey: ['memories', userId],
    queryFn: () => apiClient.listMemories(userId),
  });

  const { data: contextPreview } = useQuery({
    queryKey: ['contextPreview', userId],
    queryFn: () => apiClient.getContextPreview(userId, 3),
  });

  // Mutations
  const createMemoryMutation = useMutation({
    mutationFn: (memory: CreateMemoryRequest) => apiClient.createMemory(userId, memory),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories', userId] });
      queryClient.invalidateQueries({ queryKey: ['contextPreview', userId] });
    },
  });

  const updateMemoryMutation = useMutation({
    mutationFn: ({ memoryId, updates }: { memoryId: string; updates: UpdateMemoryRequest }) =>
      apiClient.updateMemory(memoryId, userId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories', userId] });
      queryClient.invalidateQueries({ queryKey: ['contextPreview', userId] });
    },
  });

  const deleteMemoryMutation = useMutation({
    mutationFn: (memoryId: string) => apiClient.deleteMemory(memoryId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories', userId] });
      queryClient.invalidateQueries({ queryKey: ['contextPreview', userId] });
    },
  });

  // Filtered and sorted memories
  const filteredMemories = useMemo(() => {
    let filtered = memories;

    // Category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(m => m.category === categoryFilter);
    }

    // Importance filter
    if (importanceFilter > 0) {
      filtered = filtered.filter(m => m.importance >= importanceFilter);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        m.content.toLowerCase().includes(query) ||
        m.category.toLowerCase().includes(query) ||
        m.source.toLowerCase().includes(query)
      );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'importance':
          return b.importance - a.importance;
        case 'access_count':
          return b.access_count - a.access_count;
        case 'recent':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    return filtered;
  }, [memories, categoryFilter, importanceFilter, searchQuery, sortBy]);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(memories.map(m => m.category));
    return Array.from(cats).sort();
  }, [memories]);

  // Handlers
  const handleCreateMemory = async () => {
    if (!formData.content) {
      alert('Content is required');
      return;
    }

    try {
      await createMemoryMutation.mutateAsync(formData);
      setShowCreateModal(false);
      resetForm();
    } catch (err) {
      alert('Failed to create memory');
      console.error(err);
    }
  };

  const handleUpdateMemory = async () => {
    if (!selectedMemory || !formData.content) {
      return;
    }

    try {
      const updates: UpdateMemoryRequest = {
        category: formData.category,
        content: formData.content,
        importance: formData.importance,
        verified: formData.verified,
        metadata: formData.metadata
      };

      await updateMemoryMutation.mutateAsync({
        memoryId: selectedMemory.memory_id,
        updates
      });
      setShowEditModal(false);
      setSelectedMemory(null);
      resetForm();
    } catch (err) {
      alert('Failed to update memory');
      console.error(err);
    }
  };

  const handleDeleteMemory = async () => {
    if (!selectedMemory) return;

    try {
      await deleteMemoryMutation.mutateAsync(selectedMemory.memory_id);
      setShowDeleteConfirm(false);
      setSelectedMemory(null);
    } catch (err) {
      alert('Failed to delete memory');
      console.error(err);
    }
  };

  const openEditModal = (memory: Memory) => {
    setSelectedMemory(memory);
    setFormData({
      category: memory.category,
      content: memory.content,
      source: memory.source,
      importance: memory.importance,
      verified: memory.verified,
      metadata: memory.metadata
    });
    setShowEditModal(true);
  };

  const openDeleteConfirm = (memory: Memory) => {
    setSelectedMemory(memory);
    setShowDeleteConfirm(true);
  };

  const resetForm = () => {
    setFormData({
      category: 'preference',
      content: '',
      source: 'manual_entry',
      importance: 5,
      verified: false,
      metadata: {}
    });
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      'dietary_restriction': '🚫',
      'preference': '❤️',
      'fact': '📌',
      'relationship': '👥',
      'event': '📅'
    };
    return icons[category] || '💭';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="memory-tool">
      <div className="memory-tool-header">
        <h2>Memory Management</h2>
        <div className="header-actions">
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            + New Memory
          </button>
          <button className="btn-secondary" onClick={() => setShowContextModal(true)}>
            View Context Preview
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="memory-filters">
        <div className="filter-group">
          <label>Search:</label>
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <label>Category:</label>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="all">All ({memories.length})</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat} ({memories.filter(m => m.category === cat).length})
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Min Importance:</label>
          <input
            type="range"
            min="0"
            max="10"
            value={importanceFilter}
            onChange={(e) => setImportanceFilter(Number(e.target.value))}
          />
          <span className="importance-value">{importanceFilter > 0 ? `${importanceFilter}+` : 'All'}</span>
        </div>

        <div className="filter-group">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="recent">Most Recent</option>
            <option value="importance">Importance</option>
            <option value="access_count">Access Count</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="memory-stats">
        <div className="stat-card">
          <div className="stat-value">{memories.length}</div>
          <div className="stat-label">Total Memories</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{filteredMemories.length}</div>
          <div className="stat-label">Filtered</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{contextPreview?.context_memories || 0}</div>
          <div className="stat-label">In Context</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{contextPreview?.estimated_tokens || 0}</div>
          <div className="stat-label">Est. Tokens</div>
        </div>
      </div>

      {/* Memory List */}
      {loading ? (
        <div className="loading">Loading memories...</div>
      ) : error ? (
        <div className="error">{String(error)}</div>
      ) : (
        <div className="memory-list">
          {filteredMemories.map(memory => (
            <div key={memory.memory_id} className="memory-card">
              <div className="memory-header">
                <div className="memory-category">
                  <span className="category-icon">{getCategoryIcon(memory.category)}</span>
                  <span className="category-name">{memory.category}</span>
                </div>
                <div className="memory-importance">
                  <span className={`importance-badge importance-${Math.ceil(memory.importance / 3)}`}>
                    {memory.importance}/10
                  </span>
                  {memory.verified && <span className="verified-badge">✓</span>}
                </div>
              </div>

              <div className="memory-content">{memory.content}</div>

              <div className="memory-meta">
                <span className="meta-item">Source: {memory.source}</span>
                <span className="meta-item">Created: {formatDate(memory.created_at)}</span>
                <span className="meta-item">Accessed: {memory.access_count}x</span>
              </div>

              <div className="memory-actions">
                <button className="btn-small btn-edit" onClick={() => openEditModal(memory)}>
                  Edit
                </button>
                <button className="btn-small btn-delete" onClick={() => openDeleteConfirm(memory)}>
                  Delete
                </button>
              </div>
            </div>
          ))}

          {filteredMemories.length === 0 && (
            <div className="no-memories">
              No memories match your filters. Try adjusting your search criteria.
            </div>
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <div className="modal-overlay" onClick={() => { setShowCreateModal(false); setShowEditModal(false); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{showEditModal ? 'Edit Memory' : 'Create New Memory'}</h3>

            <div className="form-group">
              <label>Category *</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                <option value="preference">Preference</option>
                <option value="fact">Fact</option>
                <option value="dietary_restriction">Dietary Restriction</option>
                <option value="relationship">Relationship</option>
                <option value="event">Event</option>
              </select>
            </div>

            <div className="form-group">
              <label>Content *</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                placeholder="Enter memory content..."
                rows={3}
                required
              />
            </div>

            <div className="form-group">
              <label>Source</label>
              <input
                type="text"
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                placeholder="e.g., conversation_2026-01-27, manual_entry"
              />
            </div>

            <div className="form-group">
              <label>Importance (1-10): {formData.importance}</label>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.importance}
                onChange={(e) => setFormData({ ...formData, importance: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.verified}
                  onChange={(e) => setFormData({ ...formData, verified: e.target.checked })}
                />
                Verified
              </label>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => {
                setShowCreateModal(false);
                setShowEditModal(false);
                resetForm();
              }}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={showEditModal ? handleUpdateMemory : handleCreateMemory}
              >
                {showEditModal ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedMemory && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
          <div className="modal modal-small" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Memory?</h3>
            <p>Are you sure you want to delete this memory?</p>
            <div className="memory-preview">
              <strong>{selectedMemory.category}:</strong> {selectedMemory.content}
            </div>
            <p className="warning">This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowDeleteConfirm(false)}>
                Cancel
              </button>
              <button className="btn-danger" onClick={handleDeleteMemory}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Context Preview Modal */}
      {showContextModal && contextPreview && (
        <div className="modal-overlay" onClick={() => setShowContextModal(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <h3>Context Preview</h3>

            <div className="context-stats">
              <div className="stat">
                <strong>{contextPreview.context_memories}</strong> / {contextPreview.total_memories} memories
              </div>
              <div className="stat">
                <strong>{contextPreview.estimated_tokens}</strong> estimated tokens
              </div>
            </div>

            <h4>By Category:</h4>
            <div className="category-breakdown">
              {Object.entries(contextPreview.by_category).map(([cat, count]) => (
                <div key={cat} className="category-stat">
                  {getCategoryIcon(cat)} {cat}: <strong>{count}</strong>
                </div>
              ))}
            </div>

            <h4>Memories in Context (importance ≥ 3):</h4>
            <div className="context-memories">
              {contextPreview.memories.map(mem => (
                <div key={mem.memory_id} className="context-memory">
                  <div className="context-memory-header">
                    <span className="category-badge">{mem.category}</span>
                    <span className="importance-badge">Importance: {mem.importance}</span>
                    <span className="tokens-badge">{mem.tokens} tokens</span>
                  </div>
                  <div className="context-memory-content">{mem.content}</div>
                </div>
              ))}
            </div>

            <div className="modal-actions">
              <button className="btn-primary" onClick={() => setShowContextModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
