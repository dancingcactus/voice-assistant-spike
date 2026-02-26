/**
 * BulkTestingTool — Phase 8 Milestones 3, 4 & 5
 *
 * Manages three view states:
 *  - "suite"   → Scenario picker + run controls + run history sidebar
 *  - "running" → Live progress view with polling, cancel, auto-transition
 *  - "detail"  → Transcript view (single or side-by-side comparison)
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical } from 'lucide-react';
import { apiClient } from '../services/api';
import type { ScenarioSummary, ScenarioResult, TurnResult, LogEntry, TestRunResult } from '../services/api';
import './BulkTestingTool.css';

// ── Types ──────────────────────────────────────────────────────────────────

type ViewState = 'suite' | 'running' | 'detail';

// ── Helper: default run label ──────────────────────────────────────────────

function defaultRunLabel(): string {
  return `Run — ${new Date().toLocaleString()}`;
}

// ── CreateTestUserForm ─────────────────────────────────────────────────────

interface CreateTestUserFormProps {
  onCreated: (userId: string) => void;
  onCancel: () => void;
}

function CreateTestUserForm({ onCreated, onCancel }: CreateTestUserFormProps) {
  const [name, setName] = useState('Bulk Test User');
  const [cleanSlate, setCleanSlate] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const result = await apiClient.createBulkTestUser({
        name,
        clean_slate: cleanSlate,
        copy_from_user_id: null,
      });
      onCreated(result.user_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
      setCreating(false);
    }
  };

  return (
    <div className="btt-create-user-form">
      <div className="btt-form-row">
        <label className="btt-form-label">Name</label>
        <input
          className="btt-input"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Bulk Test User"
        />
      </div>
      <div className="btt-form-row btt-form-row-inline">
        <label className="btt-form-label">
          <input
            type="checkbox"
            checked={cleanSlate}
            onChange={e => setCleanSlate(e.target.checked)}
          />
          {' '}Clean slate
        </label>
      </div>
      {error && <div className="btt-error">{error}</div>}
      <div className="btt-form-actions">
        <button className="btt-btn btt-btn-secondary" onClick={onCancel} disabled={creating}>
          Cancel
        </button>
        <button className="btt-btn btt-btn-primary" onClick={handleCreate} disabled={creating}>
          {creating ? 'Creating…' : 'Create'}
        </button>
      </div>
    </div>
  );
}

// ── ScenarioList ───────────────────────────────────────────────────────────

interface ScenarioListProps {
  scenarios: ScenarioSummary[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onSelectAll: () => void;
  tagFilter: string | null;
  onTagFilter: (tag: string | null) => void;
}

function ScenarioList({ scenarios, selectedIds, onToggle, onSelectAll, tagFilter, onTagFilter }: ScenarioListProps) {
  // Collect all unique tags
  const allTags = Array.from(new Set(scenarios.flatMap(s => s.tags))).sort();

  const filtered = tagFilter
    ? scenarios.filter(s => s.tags.includes(tagFilter))
    : scenarios;

  const allSelected = filtered.length > 0 && filtered.every(s => selectedIds.has(s.id));

  const handleSelectAllToggle = () => {
    if (allSelected) {
      filtered.forEach(s => selectedIds.has(s.id) && onToggle(s.id));
    } else {
      filtered.forEach(s => !selectedIds.has(s.id) && onToggle(s.id));
    }
    onSelectAll();
  };

  return (
    <div className="btt-scenario-list">
      {/* Tag filter chips */}
      <div className="btt-tag-filters">
        <button
          className={`btt-tag-chip ${tagFilter === null ? 'btt-tag-chip-active' : ''}`}
          onClick={() => onTagFilter(null)}
        >
          All
        </button>
        {allTags.map(tag => (
          <button
            key={tag}
            className={`btt-tag-chip ${tagFilter === tag ? 'btt-tag-chip-active' : ''}`}
            onClick={() => onTagFilter(tag === tagFilter ? null : tag)}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Select all toggle */}
      <div className="btt-select-all-row">
        <label className="btt-select-all-label">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={handleSelectAllToggle}
          />
          {allSelected ? 'Deselect All' : 'Select All'}
          {' '}({filtered.length})
        </label>
      </div>

      {/* Scenario rows */}
      {filtered.map(scenario => (
        <div
          key={scenario.id}
          className={`btt-scenario-row ${selectedIds.has(scenario.id) ? 'btt-scenario-row-selected' : ''}`}
          onClick={() => onToggle(scenario.id)}
        >
          <input
            type="checkbox"
            checked={selectedIds.has(scenario.id)}
            onChange={() => onToggle(scenario.id)}
            onClick={e => e.stopPropagation()}
            className="btt-scenario-checkbox"
          />
          <div className="btt-scenario-info">
            <div className="btt-scenario-name">
              <span className="btt-chapter-badge">Ch{scenario.required_chapter}</span>
              {scenario.name}
            </div>
            <div className="btt-scenario-meta">
              {scenario.characters_expected.map(c => (
                <span key={c} className={`btt-character-badge btt-char-${c}`}>{c}</span>
              ))}
              {scenario.tags.slice(0, 3).map(tag => (
                <span key={tag} className="btt-tag">{tag}</span>
              ))}
              <span className="btt-turn-count">{scenario.turn_count} turns</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── RunControls ────────────────────────────────────────────────────────────

interface RunControlsProps {
  selectedIds: Set<string>;
  totalScenarioCount: number;
  onRunStarted: (runId: string, totalCount: number) => void;
}

function RunControls({ selectedIds, totalScenarioCount, onRunStarted }: RunControlsProps) {
  const [userId, setUserId] = useState('');
  const [runLabel, setRunLabel] = useState(defaultRunLabel);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: users, refetch: refetchUsers } = useQuery({
    queryKey: ['users-with-type'],
    queryFn: () => apiClient.listUsersWithType(),
  });

  const handleUserCreated = (newUserId: string) => {
    setShowCreateUser(false);
    refetchUsers();
    setUserId(newUserId);
  };

  const startRun = async (runAll: boolean) => {
    if (!userId) {
      setError('Please select a user before running.');
      return;
    }
    setStarting(true);
    setError(null);
    try {
      const result = await apiClient.startTestRun({
        scenario_ids: runAll ? [] : Array.from(selectedIds),
        run_all: runAll,
        user_id: userId,
        run_label: runLabel,
      });
      const count = runAll ? totalScenarioCount : selectedIds.size;
      onRunStarted(result.run_id, count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
      setStarting(false);
    }
  };

  return (
    <div className="btt-run-controls">
      <h3 className="btt-section-title">Run Controls</h3>

      {/* User selector */}
      <div className="btt-form-row">
        <label className="btt-form-label">User</label>
        <select
          className="btt-select"
          value={userId}
          onChange={e => {
            if (e.target.value === '__new__') {
              setShowCreateUser(true);
            } else {
              setUserId(e.target.value);
            }
          }}
        >
          <option value="">— select a user —</option>
          {users?.map(u => {
            const isBulk = u.metadata?.source === 'bulk_testing' ||
                           u.tags?.includes('bulk_testing');
            return (
              <option key={u.user_id} value={u.user_id}>
                {u.user_id}
                {isBulk ? ' [BULK TEST]' : u.type === 'production' ? ' (Prod)' : ''}
              </option>
            );
          })}
          <option value="__new__">+ New test user…</option>
        </select>
      </div>

      {/* Inline create user form */}
      {showCreateUser && (
        <CreateTestUserForm
          onCreated={handleUserCreated}
          onCancel={() => setShowCreateUser(false)}
        />
      )}

      {/* Run label */}
      <div className="btt-form-row">
        <label className="btt-form-label">Label</label>
        <input
          className="btt-input"
          value={runLabel}
          onChange={e => setRunLabel(e.target.value)}
          placeholder="Run label…"
        />
      </div>

      {error && <div className="btt-error">{error}</div>}

      <div className="btt-run-buttons">
        <button
          className="btt-btn btt-btn-primary"
          onClick={() => startRun(false)}
          disabled={starting || selectedIds.size === 0}
          title={selectedIds.size === 0 ? 'Select at least one scenario' : undefined}
        >
          {starting ? 'Starting…' : `Run Selected (${selectedIds.size})`}
        </button>
        <button
          className="btt-btn btt-btn-secondary"
          onClick={() => startRun(true)}
          disabled={starting}
        >
          {starting ? 'Starting…' : 'Run All'}
        </button>
      </div>
    </div>
  );
}

// ── Character colours ──────────────────────────────────────────────────────

const CHARACTER_COLORS: Record<string, string> = {
  delilah:  '#f59e0b',
  hank:     '#3b82f6',
  rex:      '#f97316',
  dimitria: '#8b5cf6',
};

// ── Helpers ────────────────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }); }
  catch { return iso; }
}

// ── LogDisclosureRow ───────────────────────────────────────────────────────

const LEVEL_CLASS: Record<string, string> = {
  DEBUG: 'log-debug', INFO: 'log-info', WARNING: 'log-warning',
  ERROR: 'log-error', CRITICAL: 'log-critical',
};

interface LogDisclosureProps {
  logs: LogEntry[];
  turnId: string;
  openMap: Map<string, boolean>;
  onToggle: (id: string) => void;
}

function LogDisclosureRow({ logs, turnId, openMap, onToggle }: LogDisclosureProps) {
  if (logs.length === 0) return null;
  const open = openMap.get(turnId) ?? false;
  return (
    <div className="btt-log-disclosure">
      <button className="btt-log-disclosure-toggle" onClick={() => onToggle(turnId)}>
        {open ? '▼' : '▶'} Logs ({logs.length} {logs.length === 1 ? 'entry' : 'entries'})
      </button>
      {open && (
        <div className="btt-log-entries">
          {logs.map((entry, i) => (
            <div key={i} className={`btt-log-entry ${LEVEL_CLASS[entry.level] ?? ''}`}>
              <span className="btt-log-time">{formatTimestamp(entry.timestamp)}</span>
              <span className={`btt-log-level-badge ${LEVEL_CLASS[entry.level] ?? ''}`}>{entry.level}</span>
              <span className="btt-log-message">{entry.message}</span>
              {entry.fields && Object.keys(entry.fields).length > 0 && (
                <span className="btt-log-fields">{JSON.stringify(entry.fields)}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── TurnBlock ──────────────────────────────────────────────────────────────

interface TurnBlockProps {
  turn: TurnResult;
  openMap: Map<string, boolean>;
  onLogToggle: (id: string) => void;
}

function TurnBlock({ turn, openMap, onLogToggle }: TurnBlockProps) {
  const charColor = turn.character ? (CHARACTER_COLORS[turn.character.toLowerCase()] ?? '#888') : '#888';
  const charName = turn.character
    ? turn.character.charAt(0).toUpperCase() + turn.character.slice(1)
    : 'Assistant';

  return (
    <div className="btt-turn-block">
      {/* User message */}
      <div className="btt-user-turn">
        <span className="btt-turn-speaker btt-turn-speaker-user">You</span>
        <span className="btt-turn-text">{turn.user_message}</span>
      </div>

      {/* Character response */}
      <div className="btt-char-turn">
        <span className="btt-turn-speaker" style={{ color: charColor }}>{charName}</span>
        <span className="btt-turn-text">{turn.response}</span>
      </div>

      {/* Effects */}
      {turn.effects.map((effect, i) => (
        <div key={i} className="btt-effect-row">
          <span className="btt-effect-indicator">►</span>
          <span className="btt-effect-label">{effect.label}</span>
        </div>
      ))}

      {/* Log disclosure */}
      <LogDisclosureRow
        logs={turn.logs}
        turnId={turn.turn_id || `turn-${turn.turn_index}`}
        openMap={openMap}
        onToggle={onLogToggle}
      />
    </div>
  );
}

// ── ScenarioBlock ──────────────────────────────────────────────────────────

interface ScenarioBlockProps {
  result: ScenarioResult;
  openMap: Map<string, boolean>;
  onLogToggle: (id: string) => void;
}

function ScenarioBlock({ result, openMap, onLogToggle }: ScenarioBlockProps) {
  const durationStr = result.duration_seconds != null
    ? `${result.duration_seconds.toFixed(1)}s`
    : null;

  const statusClass = result.status === 'complete' ? 'btt-scenario-status-complete'
    : result.status === 'failed' ? 'btt-scenario-status-failed'
    : 'btt-scenario-status-skipped';

  return (
    <div className="btt-scenario-block">
      {/* Header */}
      <div className={`btt-scenario-block-header ${statusClass}`}>
        <span className="btt-scenario-block-name">{result.scenario_name}</span>
        <span className="btt-scenario-block-meta">
          {durationStr && <span>{durationStr}</span>}
          <span className={`btt-status-badge ${statusClass}`}>
            {result.status === 'complete' ? '✓' : result.status === 'failed' ? '✗' : '–'}
            {' '}{result.status}
          </span>
        </span>
      </div>

      {/* Failed scenario error box */}
      {result.status === 'failed' && result.error && (
        <div className="btt-scenario-error-box">{result.error}</div>
      )}

      {/* Turns */}
      {result.turns.map(turn => (
        <TurnBlock
          key={turn.turn_index}
          turn={turn}
          openMap={openMap}
          onLogToggle={onLogToggle}
        />
      ))}

      {/* Missed effects */}
      {result.expected_effects_missed.length > 0 && (
        <div className="btt-missed-effects">
          {result.expected_effects_missed.map((e, i) => (
            <div key={i} className="btt-missed-effect-row">
              <span className="btt-missed-indicator">✗</span>
              <span className="btt-missed-label">Expected but not seen: {e.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── TranscriptView ─────────────────────────────────────────────────────────

interface TranscriptViewProps {
  results: ScenarioResult[];
  wasCancelled: boolean;
}

function TranscriptView({ results, wasCancelled }: TranscriptViewProps) {
  const [openMap, setOpenMap] = useState<Map<string, boolean>>(new Map());

  const handleLogToggle = (id: string) => {
    setOpenMap(prev => {
      const next = new Map(prev);
      next.set(id, !(next.get(id) ?? false));
      return next;
    });
  };

  const rendered = results.filter(r => r.status !== 'skipped' || r.turns.length > 0);

  return (
    <div className="btt-transcript">
      {wasCancelled && (
        <div className="btt-cancelled-banner">
          Run cancelled — results below are from completed scenarios only.
        </div>
      )}
      {rendered.length === 0 && (
        <div className="btt-placeholder">
          <p>No completed scenarios to show yet.</p>
        </div>
      )}
      {rendered.map(result => (
        <ScenarioBlock
          key={result.scenario_id}
          result={result}
          openMap={openMap}
          onLogToggle={handleLogToggle}
        />
      ))}
    </div>
  );
}

// ── RunProgressView ────────────────────────────────────────────────────────

interface RunProgressViewProps {
  runId: string;
  totalExpected: number;
  onCompleted: (runId: string) => void;
}

function RunProgressView({ runId, totalExpected, onCompleted }: RunProgressViewProps) {
  const [cancelState, setCancelState] = useState<'idle' | 'cancelling'>('idle');

  const { data: runResult } = useQuery({
    queryKey: ['test-run', runId],
    queryFn: () => apiClient.getTestRun(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'running' || status === 'pending' ? 2000 : false;
    },
    enabled: !!runId,
  });

  // Auto-transition to detail on completion / cancellation
  useEffect(() => {
    if (!runResult) return;
    const terminal = ['complete', 'failed', 'cancelled'];
    if (terminal.includes(runResult.status)) {
      onCompleted(runId);
    }
  }, [runResult?.status, runId, onCompleted]);

  const handleCancel = async () => {
    setCancelState('cancelling');
    try {
      await apiClient.cancelTestRun(runId);
    } catch {
      // Best-effort; the status poll will pick up the cancel
    }
  };

  const results = runResult?.scenario_results ?? [];
  const completedCount = results.filter(r => r.status === 'complete' || r.status === 'failed').length;
  const total = totalExpected > 0 ? totalExpected : results.length || 1;
  const pct = Math.min(100, Math.round((completedCount / total) * 100));

  return (
    <div className="btt-progress-view">
      <div className="btt-progress-header">
        <span className="btt-progress-label">
          {runResult?.run_label ?? runId}
        </span>
        <span className="btt-progress-fraction">{completedCount} / {total}</span>
      </div>

      {/* Progress bar */}
      <div className="btt-progress-bar-track">
        <div className="btt-progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>

      {/* Scenario status list */}
      <div className="btt-progress-scenario-list">
        {results.map((r, idx) => {
          const isFirst = r.status === 'skipped' && (idx === 0 || results[idx - 1]?.status !== 'skipped');
          const statusClass = r.status === 'complete' ? 'btt-ps-complete'
            : r.status === 'failed' ? 'btt-ps-failed'
            : isFirst ? 'btt-ps-running'
            : 'btt-ps-queued';
          return (
            <div key={r.scenario_id} className={`btt-progress-scenario ${statusClass}`}>
              <span className="btt-ps-icon">
                {r.status === 'complete' ? '✓'
                  : r.status === 'failed' ? '✗'
                  : isFirst ? <span className="btt-mini-spinner" /> : '–'}
              </span>
              <span className="btt-ps-name">{r.scenario_name}</span>
            </div>
          );
        })}
      </div>

      {/* Cancel button */}
      {cancelState !== 'cancelling' ? (
        <button className="btt-btn btt-btn-secondary btt-cancel-btn" onClick={handleCancel}>
          Stop after this scenario
        </button>
      ) : (
        <button className="btt-btn btt-btn-secondary btt-cancel-btn" disabled>
          Stopping…
        </button>
      )}
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatRunDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false,
    });
  } catch { return iso; }
}

// ── RunHistoryList ─────────────────────────────────────────────────────────

interface RunHistoryListProps {
  onSelectRun: (runId: string) => void;
  currentRunId?: string | null;
  refetchKey?: number;
}

function RunHistoryList({ onSelectRun, currentRunId, refetchKey }: RunHistoryListProps) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['test-runs', refetchKey],
    queryFn: () => apiClient.listTestRuns(),
    staleTime: 5_000,
  });

  // Refetch whenever refetchKey changes (e.g. a run just completed)
  useEffect(() => { refetch(); }, [refetchKey, refetch]);

  const runs = data?.runs ?? [];

  if (isLoading) {
    return (
      <div className="btt-right-panel">
        <h3 className="btt-section-title">Run History</h3>
        <div className="btt-placeholder"><div className="btt-spinner" /></div>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="btt-right-panel">
        <h3 className="btt-section-title">Run History</h3>
        <div className="btt-placeholder">
          <FlaskConical className="btt-placeholder-icon" size={32} />
          <p>Run history will appear here once you complete a run.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="btt-right-panel">
      <h3 className="btt-section-title">
        Run History
        <span className="btt-scenario-count">{runs.length} runs</span>
      </h3>
      <div className="btt-run-history-list">
        {runs.map(run => (
          <button
            key={run.run_id}
            className={`btt-run-card ${currentRunId === run.run_id ? 'btt-run-card-active' : ''}`}
            onClick={() => onSelectRun(run.run_id)}
          >
            <div className="btt-run-card-label">{run.run_label}</div>
            <div className="btt-run-card-meta">
              <span className="btt-run-card-date">{formatRunDate(run.started_at)}</span>
              <span className="btt-run-card-user">{run.user_id}</span>
              <span className="btt-run-card-count">{run.completed_count}/{run.scenario_count} scenarios</span>
              <span className={`btt-status-badge btt-scenario-status-${run.status}`}>{run.status}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── RunPickerModal ─────────────────────────────────────────────────────────

interface RunPickerModalProps {
  excludeRunId: string;
  onSelect: (runId: string) => void;
  onClose: () => void;
}

function RunPickerModal({ excludeRunId, onSelect, onClose }: RunPickerModalProps) {
  const { data } = useQuery({
    queryKey: ['test-runs-picker'],
    queryFn: () => apiClient.listTestRuns(),
    staleTime: 5_000,
  });

  const runs = (data?.runs ?? []).filter(r => r.run_id !== excludeRunId);

  return (
    <div className="btt-modal-backdrop" onClick={onClose}>
      <div className="btt-modal" onClick={e => e.stopPropagation()}>
        <div className="btt-modal-header">
          <span className="btt-modal-title">Compare with…</span>
          <button className="btt-modal-close" onClick={onClose}>✕</button>
        </div>
        {runs.length === 0 ? (
          <div className="btt-placeholder" style={{ padding: '24px 16px' }}>
            <p>No other runs available to compare.</p>
          </div>
        ) : (
          <div className="btt-run-history-list btt-run-picker-list">
            {runs.map(run => (
              <button
                key={run.run_id}
                className="btt-run-card"
                onClick={() => { onSelect(run.run_id); onClose(); }}
              >
                <div className="btt-run-card-label">{run.run_label}</div>
                <div className="btt-run-card-meta">
                  <span className="btt-run-card-date">{formatRunDate(run.started_at)}</span>
                  <span className={`btt-status-badge btt-scenario-status-${run.status}`}>{run.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── ComparisonView ─────────────────────────────────────────────────────────

interface ComparisonViewProps {
  primaryRun: TestRunResult;
  comparisonRun: TestRunResult;
}

function ComparisonView({ primaryRun, comparisonRun }: ComparisonViewProps) {
  const leftRef  = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);
  const lockScroll = useRef(false);

  function handleLeftScroll() {
    if (lockScroll.current || !rightRef.current || !leftRef.current) return;
    lockScroll.current = true;
    rightRef.current.scrollTop = leftRef.current.scrollTop;
    requestAnimationFrame(() => { lockScroll.current = false; });
  }

  function handleRightScroll() {
    if (lockScroll.current || !leftRef.current || !rightRef.current) return;
    lockScroll.current = true;
    leftRef.current.scrollTop = rightRef.current.scrollTop;
    requestAnimationFrame(() => { lockScroll.current = false; });
  }

  // Build ordered scenario list across both runs (union, in primary order first)
  const primaryIds = primaryRun.scenario_results.map(r => r.scenario_id);
  const extraIds   = comparisonRun.scenario_results
    .filter(r => !primaryIds.includes(r.scenario_id))
    .map(r => r.scenario_id);
  const allIds = [...primaryIds, ...extraIds];

  const primaryMap  = Object.fromEntries(primaryRun.scenario_results.map(r => [r.scenario_id, r]));
  const compareMap  = Object.fromEntries(comparisonRun.scenario_results.map(r => [r.scenario_id, r]));

  return (
    <div className="btt-comparison-layout">
      {/* Column headers */}
      <div className="btt-comparison-header">
        <div className="btt-comparison-col-header">
          <span className="btt-comparison-run-label">{primaryRun.run_label}</span>
          <span className={`btt-status-badge btt-scenario-status-${primaryRun.status}`}>{primaryRun.status}</span>
        </div>
        <div className="btt-comparison-col-header">
          <span className="btt-comparison-run-label">{comparisonRun.run_label}</span>
          <span className={`btt-status-badge btt-scenario-status-${comparisonRun.status}`}>{comparisonRun.status}</span>
        </div>
      </div>

      {/* Side-by-side scroll panels */}
      <div className="btt-comparison-panels">
        <div
          ref={leftRef}
          className="btt-comparison-panel"
          onScroll={handleLeftScroll}
        >
          <ComparisonColumn runResults={allIds.map(id => primaryMap[id] ?? null)} scenarioIds={allIds} />
        </div>
        <div
          ref={rightRef}
          className="btt-comparison-panel"
          onScroll={handleRightScroll}
        >
          <ComparisonColumn runResults={allIds.map(id => compareMap[id] ?? null)} scenarioIds={allIds} />
        </div>
      </div>
    </div>
  );
}

interface ComparisonColumnProps {
  runResults: (ScenarioResult | null)[];
  scenarioIds: string[];
}

function ComparisonColumn({ runResults, scenarioIds }: ComparisonColumnProps) {
  const [openMap, setOpenMap] = useState<Map<string, boolean>>(new Map());

  const handleLogToggle = (id: string) => {
    setOpenMap(prev => {
      const next = new Map(prev);
      next.set(id, !(next.get(id) ?? false));
      return next;
    });
  };

  return (
    <div className="btt-comparison-column">
      {runResults.map((result, idx) =>
        result ? (
          <ScenarioBlock
            key={result.scenario_id}
            result={result}
            openMap={openMap}
            onLogToggle={handleLogToggle}
          />
        ) : (
          <div key={scenarioIds[idx]} className="btt-missing-scenario">
            <span>Scenario "{scenarioIds[idx]}" not present in this run</span>
          </div>
        )
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export function BulkTestingTool() {
  const [view, setView] = useState<ViewState>('suite');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [comparisonRunId, setComparisonRunId] = useState<string | null>(null);
  const [showRunPicker, setShowRunPicker] = useState(false);
  const [totalExpected, setTotalExpected] = useState(0);
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  // Incremented after a run completes to trigger history list refetch
  const [historyRefetchKey, setHistoryRefetchKey] = useState(0);

  // Primary run data for detail/comparison view
  const { data: detailRun } = useQuery({
    queryKey: ['test-run', selectedRunId],
    queryFn: () => apiClient.getTestRun(selectedRunId!),
    enabled: !!selectedRunId && view === 'detail',
    staleTime: 30_000,
  });

  // Comparison run data
  const { data: comparisonRun } = useQuery({
    queryKey: ['test-run', comparisonRunId],
    queryFn: () => apiClient.getTestRun(comparisonRunId!),
    enabled: !!comparisonRunId,
    staleTime: 30_000,
  });

  // Known users — used to show "(user deleted)" note in detail header
  const { data: knownUsers, isSuccess: usersLoaded } = useQuery({
    queryKey: ['users-with-type'],
    queryFn: () => apiClient.listUsersWithType(),
    staleTime: 30_000,
  });

  const { data: scenariosData, isLoading, error } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => apiClient.getScenarios(),
    staleTime: Infinity,
  });

  const scenarios: ScenarioSummary[] = scenariosData?.scenarios ?? [];

  const toggleScenario = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else { next.add(id); }
      return next;
    });
  };

  const handleSelectAll = () => {};

  const handleRunStarted = (runId: string, count: number) => {
    setActiveRunId(runId);
    setTotalExpected(count);
    setView('running');
  };

  const handleRunCompleted = (runId: string) => {
    setSelectedRunId(runId);
    setComparisonRunId(null);
    setActiveRunId(null);
    setHistoryRefetchKey(k => k + 1);
    setView('detail');
  };

  const openDetail = (runId: string) => {
    setSelectedRunId(runId);
    setComparisonRunId(null);
    setView('detail');
  };

  // Helper: render user_id in detail header with "(user deleted)" when the
  // users query has completed and the user is no longer present.
  function DetailUserId({ userId }: { userId: string }) {
    const isDeleted = usersLoaded && !knownUsers?.some(u => u.user_id === userId);
    return (
      <span className="btt-detail-user-id" title="User who ran this test">
        {userId}
        {isDeleted && <span className="btt-user-deleted"> (user deleted)</span>}
      </span>
    );
  }

  if (isLoading) {
    return <div className="btt-root"><div className="btt-loading">Loading scenarios…</div></div>;
  }

  if (error) {
    return <div className="btt-root"><div className="btt-error">Failed to load scenarios: {String(error)}</div></div>;
  }

  return (
    <div className="btt-root">
      <div className="btt-header">
        <h2 className="btt-title">Bulk Testing</h2>
        <p className="btt-subtitle">
          Run scripted scenarios against the live system and review conversation transcripts.
          {import.meta.env.DEV && (
            <button
              className="btt-dev-preview-btn"
              title="Dev mode: preview transcript view with latest completed run"
              onClick={async () => {
                try {
                  const res = await apiClient.listTestRuns();
                  const run = res.runs.find(r => r.status === 'complete') ?? res.runs[0];
                  if (run) { openDetail(run.run_id); }
                } catch { /* ignore */ }
              }}
            >
              [dev: preview transcript]
            </button>
          )}
        </p>
      </div>

      {view === 'suite' && (
        <div className="btt-suite-layout">
          <div className="btt-left-panel">
            <h3 className="btt-section-title">
              Scenarios
              <span className="btt-scenario-count">{scenarios.length} available</span>
            </h3>
            <ScenarioList
              scenarios={scenarios}
              selectedIds={selectedIds}
              onToggle={toggleScenario}
              onSelectAll={handleSelectAll}
              tagFilter={tagFilter}
              onTagFilter={setTagFilter}
            />
            <RunControls
              selectedIds={selectedIds}
              totalScenarioCount={scenarios.length}
              onRunStarted={handleRunStarted}
            />
          </div>
          <RunHistoryList
            onSelectRun={openDetail}
            currentRunId={selectedRunId}
            refetchKey={historyRefetchKey}
          />
        </div>
      )}

      {view === 'running' && activeRunId && (
        <RunProgressView
          runId={activeRunId}
          totalExpected={totalExpected}
          onCompleted={handleRunCompleted}
        />
      )}

      {view === 'detail' && (
        <div className="btt-detail-view">
          <div className="btt-detail-header">
            <button className="btt-btn btt-btn-secondary" onClick={() => setView('suite')}>
              ← Back to Suite
            </button>
            <span className="btt-detail-run-label">{detailRun?.run_label ?? selectedRunId}</span>
            {detailRun && (
              <span className={`btt-status-badge btt-scenario-status-${detailRun.status}`}>
                {detailRun.status}
              </span>
            )}
            {detailRun?.user_id && <DetailUserId userId={detailRun.user_id} />}
            <button
              className="btt-btn btt-btn-secondary btt-compare-btn"
              onClick={() => setShowRunPicker(true)}
              disabled={!detailRun}
            >
              {comparisonRunId ? `Comparing: ${comparisonRun?.run_label ?? comparisonRunId}` : 'Compare with…'}
            </button>
            {comparisonRunId && (
              <button
                className="btt-btn btt-btn-secondary"
                onClick={() => setComparisonRunId(null)}
                title="Close comparison"
              >
                ✕ Close comparison
              </button>
            )}
          </div>

          {/* Transcript or comparison */}
          {comparisonRunId && detailRun && comparisonRun ? (
            <ComparisonView primaryRun={detailRun} comparisonRun={comparisonRun} />
          ) : comparisonRunId && (!detailRun || !comparisonRun) ? (
            <div className="btt-placeholder"><div className="btt-spinner" /><p>Loading comparison…</p></div>
          ) : detailRun ? (
            <TranscriptView
              results={detailRun.scenario_results}
              wasCancelled={detailRun.status === 'cancelled'}
            />
          ) : (
            <div className="btt-placeholder"><div className="btt-spinner" /><p>Loading transcript…</p></div>
          )}
        </div>
      )}

      {/* Run picker modal */}
      {showRunPicker && selectedRunId && (
        <RunPickerModal
          excludeRunId={selectedRunId}
          onSelect={id => { setComparisonRunId(id); }}
          onClose={() => setShowRunPicker(false)}
        />
      )}
    </div>
  );
}
