/**
 * BulkTestingTool — Phase 8 Milestone 3: Suite Controls
 *
 * Manages three view states:
 *  - "suite"   → Scenario picker + run controls (implemented here)
 *  - "running" → Live progress view (Milestone 4)
 *  - "detail"  → Transcript view   (Milestone 4 / 5)
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical } from 'lucide-react';
import { apiClient } from '../services/api';
import type { ScenarioSummary } from '../services/api';
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

// ── RunHistoryPlaceholder ──────────────────────────────────────────────────

function RunHistoryPlaceholder() {
  return (
    <div className="btt-right-panel">
      <h3 className="btt-section-title">Run History</h3>
      <div className="btt-placeholder">
        <FlaskConical className="btt-placeholder-icon" size={32} />
        <p>Run history will appear here once you complete a run.</p>
        <p className="btt-placeholder-sub">Full history, transcript view, and comparison coming in the next milestone.</p>
      </div>
    </div>
  );
}

// ── RunningPlaceholder ─────────────────────────────────────────────────────

function RunningPlaceholder({ runId }: { runId: string }) {
  return (
    <div className="btt-placeholder btt-running-placeholder">
      <div className="btt-spinner" />
      <p>Run <code>{runId}</code> is in progress…</p>
      <p className="btt-placeholder-sub">Live progress view coming in the next milestone.</p>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export function BulkTestingTool() {
  const [view, setView] = useState<ViewState>('suite');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [tagFilter, setTagFilter] = useState<string | null>(null);

  const { data: scenariosData, isLoading, error } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => apiClient.getScenarios(),
    staleTime: Infinity,
  });

  const scenarios: ScenarioSummary[] = scenariosData?.scenarios ?? [];

  const toggleScenario = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // select-all toggling is driven by ScenarioList; we expose a no-op
  // because the child handles the actual toggle calls via onToggle
  const handleSelectAll = () => {};

  const handleRunStarted = (runId: string, _totalCount: number) => {
    setActiveRunId(runId);
    setView('running');
  };

  if (isLoading) {
    return (
      <div className="btt-root">
        <div className="btt-loading">Loading scenarios…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="btt-root">
        <div className="btt-error">Failed to load scenarios: {String(error)}</div>
      </div>
    );
  }

  return (
    <div className="btt-root">
      <div className="btt-header">
        <h2 className="btt-title">Bulk Testing</h2>
        <p className="btt-subtitle">
          Run scripted scenarios against the live system and review conversation transcripts.
        </p>
      </div>

      {view === 'suite' && (
        <div className="btt-suite-layout">
          {/* Left panel */}
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

          {/* Right panel */}
          <RunHistoryPlaceholder />
        </div>
      )}

      {view === 'running' && activeRunId && (
        <RunningPlaceholder runId={activeRunId} />
      )}

      {view === 'detail' && (
        <div className="btt-placeholder">
          <p>Transcript view coming in the next milestone.</p>
          <button className="btt-btn btt-btn-secondary" onClick={() => setView('suite')}>
            ← Back to Suite
          </button>
        </div>
      )}
    </div>
  );
}
