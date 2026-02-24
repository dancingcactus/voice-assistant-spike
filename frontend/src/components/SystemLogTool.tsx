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

function formatEntryForCopy(entry: LogEntry): string {
  const ts = formatTime(entry.timestamp);
  let line = `[${ts}] ${entry.level} ${entry.logger} - ${entry.message}`;
  if (entry.fields && Object.keys(entry.fields).length > 0) {
    line += `  ${JSON.stringify(entry.fields)}`;
  }
  return line;
}

function formatGroupForCopy(group: LogGroup, entries: LogEntry[]): string {
  const label = group.turn_id ? `Turn ${group.turn_id.slice(0, 8)}` : 'System';
  const header = `=== ${label} (${formatTime(group.start_timestamp)}) — ${entries.length} entries ===`;
  return [header, ...entries.map(formatEntryForCopy)].join('\n');
}

// ===========================================================================
// CopyButton
// ===========================================================================

function CopyButton({ getText, title = 'Copy to clipboard', className = '' }: {
  getText: () => string;
  title?: string;
  className?: string;
}) {
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle');

  function handleClick(e: React.MouseEvent) {
    e.stopPropagation();
    const text = getText();
    navigator.clipboard.writeText(text).then(() => {
      setState('copied');
      setTimeout(() => setState('idle'), 2000);
    }).catch(() => {
      setState('failed');
      setTimeout(() => setState('idle'), 2000);
    });
  }

  const icon = state === 'copied' ? '✓' : state === 'failed' ? '✗' : '⎘';
  const label = state === 'copied' ? 'Copied!' : state === 'failed' ? 'Copy failed' : title;

  return (
    <button
      className={`log-copy-btn${state === 'copied' ? ' log-copy-btn--copied' : state === 'failed' ? ' log-copy-btn--failed' : ''}${className ? ` ${className}` : ''}`}
      onClick={handleClick}
      title={label}
      aria-label={label}
    >
      {icon}
    </button>
  );
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
      <CopyButton
        getText={() => formatEntryForCopy(entry)}
        title="Copy log line"
        className="log-copy-btn--entry"
      />
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

// ===========================================================================
// ConversationGroupSection
// ===========================================================================

function ConversationGroupSection({
  conversationId,
  turns,
  expanded,
  onToggle,
  activeLevels,
  onExpandTurn,
}: {
  conversationId: string;
  turns: TurnGroupState[];
  expanded: boolean;
  onToggle: (id: string) => void;
  activeLevels: Set<Level>;
  onExpandTurn: (turnId: string | null) => void;
}) {
  const shortId = conversationId.slice(0, 8);
  const startTime = turns[0]?.group.start_timestamp ?? '';
  const totalEntries = turns.reduce((acc, s) => acc + s.group.entry_count, 0);

  const levelCounts: Record<string, number> = {};
  for (const s of turns) {
    for (const [k, v] of Object.entries(s.group.level_counts)) {
      levelCounts[k] = (levelCounts[k] ?? 0) + v;
    }
  }

  const badges = levelCountBadges(levelCounts);
  const hasError = turns.some((s) => groupSeverityClass(s.group) === 'log-group--error');
  const hasWarning = turns.some((s) => groupSeverityClass(s.group) === 'log-group--warning');
  const severityClass = hasError ? 'log-group--error' : hasWarning ? 'log-group--warning' : '';

  return (
    <div className={`log-conversation ${severityClass}`}>
      <div
        className="log-conversation__header"
        onClick={() => onToggle(conversationId)}
        role="button"
        aria-expanded={expanded}
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onToggle(conversationId)}
      >
        <span className="log-group__chevron">{expanded ? '▼' : '▶'}</span>
        <span className="log-conversation__id">Chat {shortId}…</span>
        <span className="log-group__timestamp">{formatTime(startTime)}</span>
        {badges && <span className="log-group__level-counts">{badges}</span>}
        <span className="log-group__entry-count">{totalEntries}</span>
      </div>
      {expanded && (
        <div className="log-conversation__turns">
          {turns.map((s) => (
            <TurnGroupRow
              key={s.group.turn_id ?? '__system__'}
              state={s}
              activeLevels={activeLevels}
              onExpand={onExpandTurn}
            />
          ))}
        </div>
      )}
    </div>
  );
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
        {entries !== null && !loading && (
          <CopyButton
            getText={() => formatGroupForCopy(group, entries)}
            title="Copy all entries in this group"
            className="log-copy-btn--group"
          />
        )}
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
  const [expandedConversations, setExpandedConversations] = useState<Set<string>>(new Set());
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
          // Auto-expand the conversation containing this new turn
          const newConvId = firstNew.group.conversation_id;
          if (newConvId) {
            setExpandedConversations((prev) => {
              if (prev.has(newConvId)) return prev;
              return new Set([...prev, newConvId]);
            });
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

  const handleConversationToggle = useCallback((conversationId: string) => {
    setExpandedConversations((prev) => {
      const next = new Set(prev);
      if (next.has(conversationId)) {
        next.delete(conversationId);
      } else {
        next.add(conversationId);
      }
      return next;
    });
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

  // Group turn states by conversation_id for display
  const { systemStates, conversationGroups } = useMemo(() => {
    const systemStates = groupStates.filter((s) => !s.group.turn_id);
    const convMap = new Map<string, TurnGroupState[]>();
    for (const s of groupStates) {
      if (s.group.turn_id) {
        const cid = s.group.conversation_id || '__unknown__';
        if (!convMap.has(cid)) convMap.set(cid, []);
        convMap.get(cid)!.push(s);
      }
    }
    // Sort conversations newest-first by the start time of their most recent turn
    const sorted = [...convMap.entries()].sort((a, b) => {
      const aStart = a[1][0]?.group.start_timestamp ?? '';
      const bStart = b[1][0]?.group.start_timestamp ?? '';
      return bStart.localeCompare(aStart);
    });
    return { systemStates, conversationGroups: sorted };
  }, [groupStates]);

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
        {systemStates.map((s) => (
          <TurnGroupRow
            key={s.group.turn_id ?? '__system__'}
            state={s}
            activeLevels={activeLevels}
            onExpand={handleExpand}
          />
        ))}
        {conversationGroups.map(([cid, turns]) => (
          <ConversationGroupSection
            key={cid}
            conversationId={cid}
            turns={turns}
            expanded={expandedConversations.has(cid)}
            onToggle={handleConversationToggle}
            activeLevels={activeLevels}
            onExpandTurn={handleExpand}
          />
        ))}
      </div>
    </div>
  );
}

