/**
 * Tool Calls Inspection Tool
 * View, filter, and analyze tool call logs
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  apiClient,
  type ToolCallLog,
  type ToolCallStatistics,
  type ToolCallFilterOptions,
  type ToolCallStatus,
} from '../services/api';
import './ToolCallsTool.css';

interface ToolCallsToolProps {
  userId: string;
}

export function ToolCallsTool({ userId }: ToolCallsToolProps) {
  const [selectedView, setSelectedView] = useState<'timeline' | 'stats'>('timeline');
  const [selectedCall, setSelectedCall] = useState<ToolCallLog | null>(null);
  const [filters, setFilters] = useState<ToolCallFilterOptions>({
    limit: 100,
    offset: 0,
  });

  // Fetch tool calls
  const { data: toolCalls, isLoading: callsLoading, refetch: refetchCalls } = useQuery({
    queryKey: ['toolCalls', userId, filters],
    queryFn: () => apiClient.listToolCalls(userId, filters),
  });

  // Fetch statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['toolCallStats', userId],
    queryFn: () => apiClient.getToolCallStatistics(userId),
  });

  // Fetch available filters
  const { data: availableTools } = useQuery({
    queryKey: ['availableTools', userId],
    queryFn: () => apiClient.getAvailableTools(userId),
  });

  const { data: availableCharacters } = useQuery({
    queryKey: ['availableCharacters', userId],
    queryFn: () => apiClient.getAvailableCharacters(userId),
  });

  const handleFilterChange = (key: keyof ToolCallFilterOptions, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value,
    }));
  };

  const handleClearFilters = () => {
    setFilters({ limit: 100, offset: 0 });
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getStatusIcon = (status: ToolCallStatus): string => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'timeout': return '⏱️';
      default: return '❓';
    }
  };

  const getStatusClass = (status: ToolCallStatus): string => {
    switch (status) {
      case 'success': return 'status-success';
      case 'error': return 'status-error';
      case 'timeout': return 'status-timeout';
      default: return 'status-unknown';
    }
  };

  const getDurationClass = (ms: number): string => {
    if (ms > 2000) return 'duration-slow';
    if (ms > 1000) return 'duration-medium';
    return 'duration-fast';
  };

  if (callsLoading || statsLoading) {
    return (
      <div className="tool-calls-tool">
        <div className="loading">Loading tool calls...</div>
      </div>
    );
  }

  return (
    <div className="tool-calls-tool">
      <header className="tool-header">
        <h2>🔧 Tool Calls Inspection</h2>
        <p>View and analyze all tool call executions</p>
      </header>

      <nav className="tool-nav">
        <button
          className={selectedView === 'timeline' ? 'active' : ''}
          onClick={() => setSelectedView('timeline')}
        >
          📋 Timeline
        </button>
        <button
          className={selectedView === 'stats' ? 'active' : ''}
          onClick={() => setSelectedView('stats')}
        >
          📊 Statistics
        </button>
      </nav>

      {selectedView === 'timeline' ? (
        <div className="timeline-view">
          {/* Filters */}
          <div className="filters-panel">
            <h3>Filters</h3>
            <div className="filter-grid">
              <div className="filter-group">
                <label htmlFor="tool-filter">Tool:</label>
                <select
                  id="tool-filter"
                  value={filters.tool_name || ''}
                  onChange={(e) => handleFilterChange('tool_name', e.target.value)}
                >
                  <option value="">All Tools</option>
                  {availableTools?.tools.map(tool => (
                    <option key={tool} value={tool}>{tool}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="character-filter">Character:</label>
                <select
                  id="character-filter"
                  value={filters.character || ''}
                  onChange={(e) => handleFilterChange('character', e.target.value)}
                >
                  <option value="">All Characters</option>
                  {availableCharacters?.characters.map(char => (
                    <option key={char} value={char}>{char}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="status-filter">Status:</label>
                <select
                  id="status-filter"
                  value={filters.status || ''}
                  onChange={(e) => handleFilterChange('status', e.target.value as ToolCallStatus)}
                >
                  <option value="">All Status</option>
                  <option value="success">✅ Success</option>
                  <option value="error">❌ Error</option>
                  <option value="timeout">⏱️ Timeout</option>
                </select>
              </div>

              <div className="filter-actions">
                <button onClick={handleClearFilters} className="btn-secondary">
                  Clear Filters
                </button>
                <button onClick={() => refetchCalls()} className="btn-primary">
                  Refresh
                </button>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="timeline-container">
            <div className="timeline-header">
              <h3>Recent Calls ({toolCalls?.length || 0})</h3>
            </div>

            {!toolCalls || toolCalls.length === 0 ? (
              <div className="empty-state">
                <p>No tool calls found</p>
                <p className="hint">Try adjusting your filters or make some interactions with the system</p>
              </div>
            ) : (
              <div className="timeline-list">
                {toolCalls.map(call => (
                  <div
                    key={call.call_id}
                    className={`timeline-item ${getStatusClass(call.status)}`}
                    onClick={() => setSelectedCall(call)}
                  >
                    <div className="timeline-item-header">
                      <span className="status-icon">{getStatusIcon(call.status)}</span>
                      <span className="tool-name">{call.tool_name}</span>
                      {call.character && (
                        <span className="character-badge">{call.character}</span>
                      )}
                      <span className={`duration ${getDurationClass(call.duration_ms)}`}>
                        {formatDuration(call.duration_ms)}
                      </span>
                    </div>
                    <div className="timeline-item-details">
                      <span className="timestamp">{formatTimestamp(call.timestamp)}</span>
                      {call.error_message && (
                        <span className="error-preview">{call.error_message}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="stats-view">
          {stats && (
            <>
              {/* Overall Stats */}
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Total Calls</div>
                  <div className="stat-value">{stats.total_calls}</div>
                </div>
                <div className="stat-card success">
                  <div className="stat-label">Successes</div>
                  <div className="stat-value">{stats.total_successes}</div>
                </div>
                <div className="stat-card error">
                  <div className="stat-label">Errors</div>
                  <div className="stat-value">{stats.total_errors}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Success Rate</div>
                  <div className="stat-value">{stats.overall_success_rate.toFixed(1)}%</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Avg Duration</div>
                  <div className="stat-value">{formatDuration(stats.avg_duration_ms)}</div>
                </div>
              </div>

              {/* By Tool */}
              <div className="stats-section">
                <h3>By Tool</h3>
                <div className="stats-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Tool</th>
                        <th>Calls</th>
                        <th>Success</th>
                        <th>Error</th>
                        <th>Success Rate</th>
                        <th>Avg Duration</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.by_tool.map(tool => (
                        <tr key={tool.tool_name}>
                          <td className="tool-name-cell">{tool.tool_name}</td>
                          <td>{tool.total_calls}</td>
                          <td className="success">{tool.success_count}</td>
                          <td className="error">{tool.error_count}</td>
                          <td>
                            <span className={tool.success_rate >= 95 ? 'success' : tool.success_rate >= 80 ? 'warning' : 'error'}>
                              {tool.success_rate.toFixed(1)}%
                            </span>
                          </td>
                          <td>{formatDuration(tool.avg_duration_ms)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* By Character */}
              {stats.by_character.length > 0 && (
                <div className="stats-section">
                  <h3>By Character</h3>
                  <div className="stats-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Character</th>
                          <th>Calls</th>
                          <th>Success Rate</th>
                          <th>Most Used Tool</th>
                          <th>Avg Duration</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.by_character.map(char => (
                          <tr key={char.character}>
                            <td className="character-cell">{char.character}</td>
                            <td>{char.total_calls}</td>
                            <td>
                              <span className={char.success_rate >= 95 ? 'success' : char.success_rate >= 80 ? 'warning' : 'error'}>
                                {char.success_rate.toFixed(1)}%
                              </span>
                            </td>
                            <td>{char.most_used_tool || 'N/A'}</td>
                            <td>{formatDuration(char.avg_duration_ms)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Slowest Calls */}
              {stats.slowest_calls.length > 0 && (
                <div className="stats-section">
                  <h3>⏱️ Slowest Calls</h3>
                  <div className="calls-list">
                    {stats.slowest_calls.map(call => (
                      <div
                        key={call.call_id}
                        className="call-item slow"
                        onClick={() => setSelectedCall(call)}
                      >
                        <span className="tool-name">{call.tool_name}</span>
                        {call.character && <span className="character-badge">{call.character}</span>}
                        <span className="duration slow">{formatDuration(call.duration_ms)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Errors */}
              {stats.recent_errors.length > 0 && (
                <div className="stats-section">
                  <h3>❌ Recent Errors</h3>
                  <div className="calls-list">
                    {stats.recent_errors.map(call => (
                      <div
                        key={call.call_id}
                        className="call-item error"
                        onClick={() => setSelectedCall(call)}
                      >
                        <span className="tool-name">{call.tool_name}</span>
                        {call.character && <span className="character-badge">{call.character}</span>}
                        <span className="error-message">{call.error_message}</span>
                        <span className="timestamp-small">{formatTimestamp(call.timestamp)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {selectedCall && (
        <div className="modal-overlay" onClick={() => setSelectedCall(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <header className="modal-header">
              <h2>Tool Call Detail</h2>
              <button onClick={() => setSelectedCall(null)} className="close-btn">✕</button>
            </header>

            <div className="modal-body">
              <div className="detail-section">
                <h3>Overview</h3>
                <div className="detail-grid">
                  <div><strong>Call ID:</strong> {selectedCall.call_id}</div>
                  <div><strong>Tool:</strong> {selectedCall.tool_name}</div>
                  <div><strong>Status:</strong> <span className={getStatusClass(selectedCall.status)}>{selectedCall.status}</span></div>
                  <div><strong>Duration:</strong> <span className={getDurationClass(selectedCall.duration_ms)}>{formatDuration(selectedCall.duration_ms)}</span></div>
                  <div><strong>Timestamp:</strong> {formatTimestamp(selectedCall.timestamp)}</div>
                  {selectedCall.character && <div><strong>Character:</strong> {selectedCall.character}</div>}
                </div>
              </div>

              {selectedCall.reasoning && (
                <div className="detail-section">
                  <h3>Reasoning</h3>
                  <div className="detail-content">{selectedCall.reasoning}</div>
                </div>
              )}

              <div className="detail-section">
                <h3>Request</h3>
                <pre className="code-block">{JSON.stringify(selectedCall.request, null, 2)}</pre>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedCall.request, null, 2))}
                  className="btn-secondary btn-small"
                >
                  Copy Request
                </button>
              </div>

              <div className="detail-section">
                <h3>Response</h3>
                <pre className="code-block">{JSON.stringify(selectedCall.response, null, 2)}</pre>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedCall.response, null, 2))}
                  className="btn-secondary btn-small"
                >
                  Copy Response
                </button>
              </div>

              {selectedCall.error_message && (
                <div className="detail-section error">
                  <h3>Error</h3>
                  <div className="error-content">{selectedCall.error_message}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
