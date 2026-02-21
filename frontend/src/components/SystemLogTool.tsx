/**
 * System Log Tool
 * Displays a running log of system activity captured from the backend.
 */

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, type LogEntry } from '../services/api';
import './SystemLogTool.css';

const LEVEL_OPTIONS = ['', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
const REFETCH_INTERVAL_MS = 3000;

const LEVEL_CLASS: Record<string, string> = {
  DEBUG: 'log-debug',
  INFO: 'log-info',
  WARNING: 'log-warning',
  ERROR: 'log-error',
  CRITICAL: 'log-critical',
};

export function SystemLogTool() {
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', levelFilter],
    queryFn: () => apiClient.getLogs(200, levelFilter || undefined),
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const logs: LogEntry[] = data?.logs ?? [];

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs.length, autoScroll]);

  function formatTime(isoTimestamp: string): string {
    try {
      return new Date(isoTimestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return isoTimestamp;
    }
  }

  return (
    <div className="system-log-tool">
      <div className="log-toolbar">
        <div className="log-toolbar-left">
          <label htmlFor="log-level-filter">Level:</label>
          <select
            id="log-level-filter"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="log-level-select"
          >
            {LEVEL_OPTIONS.map((l) => (
              <option key={l} value={l}>
                {l || 'All'}
              </option>
            ))}
          </select>
          <span className="log-count">{logs.length} entries</span>
        </div>
        <div className="log-toolbar-right">
          <label className="auto-scroll-label">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
        </div>
      </div>

      <div className="log-output">
        {isLoading && <div className="log-status">Loading logs…</div>}
        {error && <div className="log-status log-error-msg">Failed to load logs.</div>}
        {!isLoading && logs.length === 0 && (
          <div className="log-status">No log entries yet. Activity will appear here automatically.</div>
        )}
        {logs.map((entry, idx) => (
          <div key={idx} className={`log-line ${LEVEL_CLASS[entry.level] ?? ''}`}>
            <span className="log-time">{formatTime(entry.timestamp)}</span>
            <span className={`log-level-badge ${LEVEL_CLASS[entry.level] ?? ''}`}>{entry.level}</span>
            <span className="log-logger">{entry.logger}</span>
            <span className="log-message">{entry.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
