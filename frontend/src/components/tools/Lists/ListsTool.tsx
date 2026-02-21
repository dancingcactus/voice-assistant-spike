/**
 * Lists Tool - View and manage user lists
 */

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import './ListsTool.css';
import { LoadingSpinner } from '../../LoadingSpinner';

interface ListItem {
  item_id: string;
  name: string;
  description?: string;
  quantity?: string;
  completed: boolean;
  created_at: string;
  completed_at?: string;
}

interface ListSummary {
  list_id: string;
  list_name: string;
  total_items: number;
  active_items: number;
  completed_items: number;
  created_at: string;
  updated_at: string;
}

interface ListsSummaryResponse {
  user_id: string;
  total_lists: number;
  lists: ListSummary[];
}

interface ListsToolProps {
  userId: string;
  apiClient: any; // Will be typed properly when we update api.ts
}

export function ListsTool({ userId, apiClient }: ListsToolProps) {
  const [expandedLists, setExpandedLists] = useState<Set<string>>(new Set());
  const [showCompleted, setShowCompleted] = useState(false);

  const { data: listsData, isLoading, error } = useQuery<ListsSummaryResponse>({
    queryKey: ['lists', userId],
    queryFn: () => apiClient.getLists(userId),
    enabled: !!userId,
  });

  const toggleListExpanded = (listId: string) => {
    const newExpanded = new Set(expandedLists);
    if (newExpanded.has(listId)) {
      newExpanded.delete(listId);
    } else {
      newExpanded.add(listId);
    }
    setExpandedLists(newExpanded);
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading lists..." />;
  }

  if (error) {
    return <div className="error">Error loading lists: {String(error)}</div>;
  }

  if (!listsData || listsData.total_lists === 0) {
    return (
      <div className="lists-tool">
        <div className="empty-state">
          <h3>No lists yet</h3>
          <p>This user hasn't created any lists yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="lists-tool">
      <div className="lists-header">
        <h3>Lists for {userId}</h3>
        <div className="lists-controls">
          <label>
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={(e) => setShowCompleted(e.target.checked)}
            />
            Show completed items
          </label>
        </div>
      </div>

      <div className="lists-summary">
        <div className="summary-stat">
          <span className="stat-value">{listsData.total_lists}</span>
          <span className="stat-label">Lists</span>
        </div>
        <div className="summary-stat">
          <span className="stat-value">
            {listsData.lists.reduce((sum, list) => sum + list.active_items, 0)}
          </span>
          <span className="stat-label">Active Items</span>
        </div>
        <div className="summary-stat">
          <span className="stat-value">
            {listsData.lists.reduce((sum, list) => sum + list.completed_items, 0)}
          </span>
          <span className="stat-label">Completed</span>
        </div>
      </div>

      <div className="lists-container">
        {listsData.lists.map((list) => (
          <div key={list.list_id} className="list-card">
            <div className="list-header" onClick={() => toggleListExpanded(list.list_id)}>
              <span className="expand-icon">
                {expandedLists.has(list.list_id) ? '▼' : '▶'}
              </span>
              <h4>{list.list_name}</h4>
              <div className="list-stats">
                <span className="stat-badge active">{list.active_items} active</span>
                {list.completed_items > 0 && (
                  <span className="stat-badge completed">{list.completed_items} done</span>
                )}
              </div>
            </div>

            {expandedLists.has(list.list_id) && (
              <div className="list-details">
                <p className="list-meta">
                  Last updated: {new Date(list.updated_at).toLocaleString()}
                </p>
                <div className="list-items-placeholder">
                  <p><em>Item details will load here when API is connected</em></p>
                  <p className="note">Total items: {list.total_items}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
