/**
 * System Log Tool
 * Displays a running log of system activity captured from the backend.
 * Phase 7: Collapsible turn groups, level toggle pills, structured fields,
 * file logging control panel.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, type LogEntry, type LogGroup, type FileLoggingStatus } from '../services/api';
import './SystemLogTool.css';

const ALL_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] as const;
type Level = typeof ALL_LEVELS[number];

const REFETCH_INTERVAL_MS = 3000;

const LEVEL_CLASS: Record<string, string> = {
  DEBUG: 'log-debug',
  INFO: 'log-info',
  WARNING: 'log-warning',
  ERROR: 'log-error',
  CRITICAL: 'log-critical',
};

// ===========================================================================
// Helpers
// ===========================================================================

function formatTime(isoTimestamp: string): string {
  try {
    return new Date(isoTimestamp).toLocaleTimeString([], {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    });
  } catch {
    return isoTimestamp;
  }
}

function relativeMs(entryTimestamp: string, groupStart: string): string {
  const delta = new Date(entryTimestamp).getTime() - new Date(groupStart).getTime();
  if (delta < 0) return '+0ms';
  return delta < 1000 ? `+${delta}ms` : `+${(delta / 1000).toFixed(1)}s`;
}

function groupSeverityClass(g: LogGroup): string {
  const c = g.level_counts;
  if ((c['ERROR'] ?? 0) + (c['CRITICAL'] ?? 0) > 0) return 'log-group--error';
  if ((c['WARNING'] ?? 0) > 0) return 'log-group--warning';
  return '';
}

function levelCountBadges(counts: Record<string, number>): string {
  return ALL_LEVELS
    .filter((l) => (counts[l] ?? 0) > 0)
    .map((l) => `${counts[l]} ${l}`)
    .join(' · ');
}

// ===========================================================================
// FileLoggingPanel
// ===========================================================================

function FileLoggingPanel() {
  const [filename, setFilename] = useState('aperture-assist.log');
  const [filenameError, setFilenameError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: status } = useQuery<FileLoggingStatus>({
    queryKey: ['fileLoggingStatus'],
    queryFn: () => apiClient.getFileLoggingStatus(),
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const mutation = useMutation({
    mutationFn: ({ enabled, fname }: { enabled: boolean; fname: string }) =>
      apiClient.setFileLogging(enabled, fname),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fileLoggingStatus'] });
    },
  });

  function validateFilename(name: string): string | null {
    if (/[/\\]/.test(name) || name.includes('..')) {
      return 'Filename must be a plain name (no paths or ..)';
    }
    return null;
  }

  function handleToggle() {
    const enabled = !(status?.enabled ?? false);
    if (enabled) {
      const err = validateFilename(filename);
      if (err) { setFilenameError(err); return; }
      setFilenameError(null);
    }
    mutation.mutate({ enabled, fname: filename });
  }

  const isEnabled = status?.enabled ?? false;

  return (
    <div className="file-logging-panel">
      <span className="file-logging-label">File log:</span>
      <button
        className={`file-logging-toggle${isEnabled ? ' file-logging-toggle--on' : ''}`}
        onClick={handleToggle}
        title={isEnabled ? 'Disable file logging' : 'Enable file logging'}
      >
        {isEnabled ? 'ON' : 'OFF'}
      </button>
      <input
        className="file-logging-filename"
        type="text"
        value={isEnabled && status?.path ? status.path.split('/').pop() ?? filename : filename}
        onChange={(e) => { setFilename(e.target.value); setFilenameError(null); }}
        disabled={isEnabled}
        placeholder="aperture-assist.log"
        aria-label="Log filename"
      />
      {isEnabled && status?.path && (
        <span className="file-logging-path" title={status.path}>
          {status.path}
          {status.size_bytes != null && ` (${(status.size_bytes / 1024).toFixed(1)} KB)`}
        </span>
      )}
      {filenameError && <span className="file-logging-error">{filenameError}</span>}
      {mutation.isError && (
        <span className="file-logging-error">
          {(mutation.error as Error)?.message ?? 'Error'}
        </span>
      )}
    </div>
  );
}

// ===========================================================================
// LevelTogglePills
// ===========================================================================

function LevelTogglePills({
  activeLevels,
  onToggle,
}: {
  activeLevels: Set<Level>;
  onToggle: (l: Level) => void;
}) {
  return (
    <div className="level-pills">
      {ALL_LEVELS.map((l) => (
        <button
          key={l}
          className={`level-pill level-pill--${l.toLowerCase()}${activeLevels.has(l) ? ' level-pill--active' : ''}`}
          onClick={() => onToggle(l)}
          title={activeLevels.has(l) ? `Hide ${l}` : `Show ${l}`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

// ===========================================================================
// LogEntryRow
// ===========================================================================

function LogEntryRow({ entry, groupStart }: { entry: LogEntry; groupStart: string }) {
  const hasFields = Object.keys(entry.fields ?? {}).length > 0;
  return (
    <div className={`log-line ${LEVEL_CLASS[entry.level] ?? ''}`}>
      <span className="log-entry__relative-time">{relativeMs(entry.timestamp, groupStart)}</span>
      <span className={`log-level-badge ${LEVEL_CLASS[entry.level] ?? ''}`}>{entry.level}</span>
      <span className="log-logger">{entry.logger}</span>
      <span className="log-message">{entry.message}</span>
      {hasFields && (
        <details className="log-entry__fields">
          <summary>Fields</summary>
          <pre>{JSON.stringify(entry.fields, null, 2)}</pre>
        </details>
      )}
    </div>
  );
}

// ===========================================================================
// TurnGroupRow
// ===========================================================================

interface TurnGroupState {
  group: LogGroup;
  expanded: boolean;
  loading: boolean;
  entries: LogEntry[] | null;
}

function TurnGroupRow({
  state,
  activeLevels,
  onExpand,
}: {
  state: TurnGroupState;
  activeLevels: Set<Level>;
  onExpand: (turnId: string | null) => void;
}) {
  const { group, expanded, loading, entries } = state;
  const severityClass = groupSeverityClass(group);
  const badges = levelCountBadges(group.level_counts);
  const turnLabel = group.turn_id
    ? (group.headline ?? group.turn_id.slice(0, 8))
    : 'System';
  const visibleEntries = entries?.filter((e) => activeLevels.has(e.level as Level)) ?? [];

  return (
    <div className={`log-group ${severityClass}`}>
      <div
        className="log-group__header"
        onClick={() => onExpand(group.turn_id)}
        role="button"
        aria-expanded={expanded}
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onExpand(group.turn_id)}
      >
        <span className="log-group__chevron">{expanded ? '▼' : '▶'}</span>
        <span className="log-group__headline">{turnLabel}</span>
        <span className="log-group__timestamp">{formatTime(group.start_timestamp)}</span>
        {badges && <span className="log-group__level-counts">{badges}</span>}
        <span className="log-group__entry-count">{group.entry_count}</span>
      </div>
      {expanded && (
        <div className="log-group__entries">
          {loading && (
            <>
              <div className="log-skeleton" />
              <div className="log-skeleton" />
              <div className="log-skeleton" />
            </>
          )}
          {!loading && visibleEntries.length === 0 && (
            <div className="log-status">No entries match the current level filter.</div>
          )}
          {!loading && visibleEntries.map((entry, idx) => (
            <LogEntryRow
              key={`${entry.timestamp}-${entry.logger}-${idx}`}
              entry={entry}
              groupStart={group.start_timestamp}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ===========================================================================
// SystemLogTool
// ===========================================================================

export function SystemLogTool() {
  const [activeLevels, setActiveLevels] = useState<Set<Level>>(new Set(ALL_LEVELS));
  const [groupStates, setGroupStates] = useState<TurnGroupState[]>([]);
  const prevGroupTurnIds = useRef<Set<string | null>>(new Set());

  // Poll group summaries every 3 s
  const { data: groupsData } = useQuery({
    queryKey: ['logGroups'],
    queryFn: () => apiClient.getLogGroups(),
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  // When new group data arrives, merge into groupStates
  useEffect(() => {
    if (!groupsData?.groups) return;
    const incoming = groupsData.groups;

    setGroupStates((prev) => {
      const stateMap = new Map(prev.map((s) => [s.group.turn_id, s]));
      let hasNew = false;

      const next: TurnGroupState[] = incoming.map((g) => {
        const existing = stateMap.get(g.turn_id);
        if (existing) {
          // Update group metadata (level counts may have grown), preserve expanded/entries
          return { ...existing, group: g };
        }
        hasNew = true;
        return { group: g, expanded: false, loading: false, entries: null };
      });

      // Auto-expand the most recent non-system group when it first appears
      if (hasNew) {
        const firstNew = next.find(
          (s) => s.group.turn_id !== null && !prevGroupTurnIds.current.has(s.group.turn_id)
        );
        if (firstNew) {
          const idx = next.indexOf(firstNew);
          if (idx !== -1) {
            next[idx] = { ...next[idx], expanded: true, loading: true };
          }
        }
      }

      return next;
    });

    // Update seen turn IDs
    incoming.forEach((g) => prevGroupTurnIds.current.add(g.turn_id));
  }, [groupsData]);

  // Fetch entries for groups that became expanded but have no entries yet
  useEffect(() => {
    groupStates.forEach((s) => {
      if (s.expanded && s.loading && s.entries === null) {
        const turnId = s.group.turn_id;
        (turnId
          ? apiClient.getLogsForTurn(turnId)
          : apiClient.getLogs(200, undefined, undefined, undefined, 'asc')
        ).then((resp) => {
          setGroupStates((prev) =>
            prev.map((gs) =>
              gs.group.turn_id === turnId
                ? { ...gs, entries: resp.logs, loading: false }
                : gs
            )
          );
        }).catch(() => {
          setGroupStates((prev) =>
            prev.map((gs) =>
              gs.group.turn_id === turnId
                ? { ...gs, entries: [], loading: false }
                : gs
            )
          );
        });
      }
    });
  }, [groupStates]);

  const handleExpand = useCallback((turnId: string | null) => {
    setGroupStates((prev) =>
      prev.map((s) => {
        if (s.group.turn_id !== turnId) return s;
        if (s.entries !== null) return { ...s, expanded: !s.expanded };
        return { ...s, expanded: true, loading: true };
      })
    );
  }, []);

  function toggleLevel(level: Level) {
    setActiveLevels((prev) => {
      const next = new Set(prev);
      if (next.has(level)) { next.delete(level); } else { next.add(level); }
      return next;
    });
  }

  const totalCount = useMemo(
    () => groupStates.reduce((acc, s) => acc + s.group.entry_count, 0),
    [groupStates]
  );

  return (
    <div className="system-log-tool">
      <div className="log-toolbar">
        <div className="log-toolbar-left">
          <LevelTogglePills activeLevels={activeLevels} onToggle={toggleLevel} />
          <span className="log-count">{totalCount} entries</span>
        </div>
        <div className="log-toolbar-right">
          <FileLoggingPanel />
        </div>
      </div>

      <div className="log-output">
        {groupStates.length === 0 && (
          <div className="log-status">No log entries yet. Activity will appear here automatically.</div>
        )}
        {groupStates.map((s) => (
          <TurnGroupRow
            key={s.group.turn_id ?? '__system__'}
            state={s}
            activeLevels={activeLevels}
            onExpand={handleExpand}
          />
        ))}
      </div>
    </div>
  );
}

