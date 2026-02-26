"""
Scenario Runner for Phase 8: Experience Testing Suite.

Async background engine that:
- Executes test scenarios sequentially against the live conversation system
- Captures tool-call effects and log entries per turn
- Persists incremental results to backend/data/test_runs/
- Enforces a 50-run cap (oldest deleted when exceeded)
- Honours a per-run cancellation flag (checked between scenarios)
- Exposes a concurrency guard (only one run active at a time)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from core.logging_context import generate_id, set_correlation_ids
from core.scenario_loader import load_all, load_by_ids
from models.test_run_models import (
    CapturedEffect,
    ScenarioResult,
    Scenario,
    TestRunRequest,
    TestRunResult,
    TurnResult,
    WatchForEffect,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RUNS_DIR = Path(__file__).parent.parent.parent / "data" / "test_runs"

# ---------------------------------------------------------------------------
# Module-level singleton state
# ---------------------------------------------------------------------------

_active_run_id: Optional[str] = None
_cancel_flags: dict[str, bool] = {}   # run_id → cancel requested
_conversation_manager = None          # injected at startup via set_conversation_manager()

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def set_conversation_manager(cm) -> None:
    """Inject the live ConversationManager instance used by the WebSocket handler."""
    global _conversation_manager
    _conversation_manager = cm


def get_active_run_id() -> Optional[str]:
    """Return the run_id of the currently executing run, or None."""
    return _active_run_id


def request_cancel(run_id: str) -> None:
    """Set the cancellation flag for *run_id*. Checked between scenarios."""
    _cancel_flags[run_id] = True


# ---------------------------------------------------------------------------
# Effect capture map
# ---------------------------------------------------------------------------

def _tool_call_to_effect(tc) -> CapturedEffect:
    """Convert a ToolCallLog record to a CapturedEffect."""
    name = tc.tool_name
    args = tc.request or {}
    result = tc.response or {}

    if name == "request_handoff":
        to = result.get("to") or result.get("target") or "?"
        label = f"Handoff: {tc.character} → {to}"
        return CapturedEffect(type="character_handoff", label=label, raw=tc.model_dump())

    if name == "advance_story_beat":
        beat = args.get("beat_id") or result.get("beat_id") or "?"
        return CapturedEffect(type="story_beat", label=f"Story beat advanced: {beat}", raw=tc.model_dump())

    if name == "save_memory":
        snippet = str(result)[:60]
        return CapturedEffect(type="memory_saved", label=f"Memory saved: {snippet}", raw=tc.model_dump())

    if name == "set_timer":
        duration = args.get("duration") or result.get("duration") or "?"
        return CapturedEffect(type="timer_set", label=f"Timer set: {duration}", raw=tc.model_dump())

    # Generic fallback
    result_preview = str(result)[:80] if result else ""
    label = f"{name}: {result_preview}" if result_preview else name
    return CapturedEffect(type="tool_call", label=label, raw=tc.model_dump())


def _capture_effects(turn_id: str, user_id: str) -> List[CapturedEffect]:
    """Query the tool-call log for *turn_id* and convert entries to CapturedEffects."""
    from observability.tool_call_access import ToolCallDataAccess
    import os

    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    access = ToolCallDataAccess(data_dir=str(data_dir))
    tool_calls = access.get_tool_calls_for_turn(turn_id=turn_id, user_id=user_id)
    return [_tool_call_to_effect(tc) for tc in tool_calls]


# ---------------------------------------------------------------------------
# Run persistence
# ---------------------------------------------------------------------------


def _persist_run(run: TestRunResult) -> None:
    """Write the run result to disk and enforce the 50-run cap."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run.run_id}.json").write_text(
        run.model_dump_json(indent=2), encoding="utf-8"
    )
    _enforce_run_cap()


def _enforce_run_cap(max_runs: int = 50) -> None:
    """Delete the oldest run files if count exceeds *max_runs*."""
    files = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    while len(files) > max_runs:
        files[0].unlink()
        files = files[1:]


def _load_run(run_id: str) -> TestRunResult:
    """Load a persisted run result by ID. Raises FileNotFoundError if absent."""
    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Run {run_id!r} not found")
    return TestRunResult.model_validate_json(path.read_text(encoding="utf-8"))


def list_runs() -> List[TestRunResult]:
    """Return all persisted runs sorted newest-first."""
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            runs.append(TestRunResult.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Skipping corrupt run file %s: %s", path.name, exc)
    return runs


# ---------------------------------------------------------------------------
# Setup step execution
# ---------------------------------------------------------------------------


def _apply_setup_steps(steps, user_id: str) -> None:
    """Execute setup_steps synchronously before a scenario starts."""
    from observability.data_access import DataAccessLayer
    from core.story_engine import StoryEngine
    from datetime import datetime

    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    story_dir = project_root / "story"

    dal = DataAccessLayer(data_dir=str(data_dir))
    engine = StoryEngine(story_dir=str(story_dir), memory_manager=None)

    for step in steps:
        if step.type == "set_chapter":
            chapter = step.chapter
            user_data = dal.get_user(user_id)
            if not user_data:
                logger.warning("setup_steps: user %s not found for set_chapter", user_id)
                continue
            if "story_progress" not in user_data:
                user_data["story_progress"] = {}
            user_data["story_progress"]["current_chapter"] = chapter
            user_data["story_progress"]["chapter_start_time"] = datetime.now().isoformat()
            user_data["updated_at"] = datetime.now().isoformat()
            dal.save_user(user_id, user_data)
            logger.info("setup_steps: set chapter=%d for user %s", chapter, user_id)

        elif step.type == "trigger_beat":
            beat_id = step.beat_id
            variant = step.variant or "standard"
            user_data = dal.get_user(user_id)
            if not user_data:
                logger.warning("setup_steps: user %s not found for trigger_beat", user_id)
                continue

            # Hydrate story engine state from saved user data
            story_progress = user_data.get("story_progress", {})
            current_chapter = story_progress.get("current_chapter", 1)
            state = engine.get_or_create_user_state(user_id)
            state.current_chapter = current_chapter

            from models.story import ChapterProgress
            if current_chapter not in state.chapter_progress:
                state.chapter_progress[current_chapter] = ChapterProgress(
                    chapter_id=current_chapter,
                    started_at=datetime.utcnow(),
                    interaction_count=story_progress.get("interaction_count", 0),
                )

            # Mark beat as delivered
            engine.mark_beat_stage_delivered(user_id, beat_id, stage=1)
            engine.check_chapter_progression(user_id)

            # Sync back to user data file
            updated_state = engine.get_or_create_user_state(user_id)
            chapter_prog = updated_state.chapter_progress.get(updated_state.current_chapter)
            if chapter_prog:
                beats_delivered = user_data["story_progress"].get("beats_delivered", {})
                for bid, beat_prog in chapter_prog.beat_progress.items():
                    if not beat_prog.delivered and not beat_prog.delivered_stages:
                        continue
                    beats_delivered[bid] = {
                        "delivered": beat_prog.delivered,
                        "timestamp": (beat_prog.last_delivered or datetime.utcnow()).isoformat(),
                        "variant": variant,
                        "stage": beat_prog.current_stage,
                        "delivered_stages": list(beat_prog.delivered_stages),
                    }
                user_data["story_progress"]["beats_delivered"] = beats_delivered

            user_data["updated_at"] = datetime.now().isoformat()
            dal.save_user(user_id, user_data)
            logger.info("setup_steps: triggered beat %s for user %s", beat_id, user_id)


# ---------------------------------------------------------------------------
# Scenario execution
# ---------------------------------------------------------------------------


async def _execute_scenario(scenario: Scenario, user_id: str) -> ScenarioResult:
    """Execute a single scenario and return a complete ScenarioResult."""
    from observability.log_handler import get_handler as _get_log_handler

    start_time = datetime.now(timezone.utc)
    turns: List[TurnResult] = []

    try:
        # Apply setup steps before conversation begins
        if scenario.setup_steps:
            _apply_setup_steps(scenario.setup_steps, user_id)

        # One conversation_id shared across all turns in this scenario
        conversation_id = generate_id()
        set_correlation_ids(conversation_id, "")

        for turn_index, user_message in enumerate(scenario.user_turns):
            response = await _conversation_manager.handle_user_message(
                session_id=conversation_id,
                user_message=user_message,
                user_id=user_id,
                input_mode="chat",
            )
            turn_id: str = response.get("metadata", {}).get("turn_id", "")
            character: Optional[str] = response.get("character") or response.get(
                "metadata", {}
            ).get("character")
            text: str = response.get("text", "")

            effects = _capture_effects(turn_id, user_id)
            log_entries = _get_log_handler().get_logs(turn_id=turn_id) if turn_id else []

            turns.append(
                TurnResult(
                    turn_index=turn_index,
                    user_message=user_message,
                    character=character,
                    response=text,
                    turn_id=turn_id,
                    effects=effects,
                    logs=log_entries,
                )
            )

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Compute expected effects that did not fire
        missed = _compute_missed_effects(scenario.watch_for_effects, turns)

        return ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            status="complete",
            duration_seconds=round(elapsed, 2),
            turns=turns,
            expected_effects_missed=missed,
        )

    except Exception as exc:
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.error("Scenario %s failed: %s", scenario.id, exc, exc_info=True)
        return ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            status="failed",
            duration_seconds=round(elapsed, 2),
            error=str(exc),
            turns=turns,
        )


def _compute_missed_effects(
    expected: List[WatchForEffect],
    turns: List[TurnResult],
) -> List[WatchForEffect]:
    """Return the subset of *expected* effects that did not appear in any turn."""
    fired_types_labels = {(e.type, e.label) for t in turns for e in t.effects}
    fired_types = {e.type for t in turns for e in t.effects}

    missed: List[WatchForEffect] = []
    for want in expected:
        # Match by (type, label) if possible; fall back to just type
        if (want.type, want.label) not in fired_types_labels and want.type not in fired_types:
            missed.append(want)
    return missed


# ---------------------------------------------------------------------------
# Background run coroutine
# ---------------------------------------------------------------------------


async def _run_scenarios(
    run_id: str,
    scenarios: List[Scenario],
    user_id: str,
) -> None:
    """Background coroutine that executes all scenarios and persists results."""
    global _active_run_id

    run = _load_run(run_id)
    run.status = "running"
    _persist_run(run)

    try:
        for idx, scenario in enumerate(scenarios):
            if _cancel_flags.get(run_id):
                # Remaining scenarios stay as "skipped" (pre-populated)
                logger.info("Run %s cancelled before scenario %s", run_id, scenario.id)
                break

            logger.info("Run %s: starting scenario %s (%d/%d)", run_id, scenario.id, idx + 1, len(scenarios))
            result = await _execute_scenario(scenario, user_id)
            run.scenario_results[idx] = result
            _persist_run(run)
            logger.info("Run %s: scenario %s → %s", run_id, scenario.id, result.status)
        else:
            run.status = "complete"

    except Exception as exc:
        run.status = "failed"
        logger.error("Run %s failed unexpectedly: %s", run_id, exc, exc_info=True)

    finally:
        if _cancel_flags.get(run_id) and run.status == "running":
            run.status = "cancelled"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        _persist_run(run)
        _cancel_flags.pop(run_id, None)
        _active_run_id = None
        logger.info("Run %s finished with status=%s", run_id, run.status)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_run(request: TestRunRequest) -> str:
    """
    Start a new test run asynchronously.

    Returns:
        The generated run_id.

    Raises:
        RuntimeError: If another run is already active.
        ValueError: If scenario IDs are invalid (forwarded from load_by_ids).
    """
    global _active_run_id

    if _active_run_id is not None:
        raise RuntimeError(f"A run is already active: {_active_run_id}")

    if _conversation_manager is None:
        raise RuntimeError("ConversationManager not injected — call set_conversation_manager() first")

    # Select scenarios
    scenarios = load_all() if request.run_all else load_by_ids(request.scenario_ids)

    # Generate run ID
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # Build initial result with all scenarios pre-populated as "skipped"
    initial_results = [
        ScenarioResult(
            scenario_id=s.id,
            scenario_name=s.name,
            status="skipped",
        )
        for s in scenarios
    ]

    run = TestRunResult(
        run_id=run_id,
        run_label=request.run_label,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="pending",
        user_id=request.user_id,
        scenario_results=initial_results,
    )
    _persist_run(run)
    _active_run_id = run_id

    # Schedule background execution
    asyncio.create_task(_run_scenarios(run_id, scenarios, request.user_id))

    return run_id
