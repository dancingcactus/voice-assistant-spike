"""
Pydantic data models for Phase 8: Experience Testing Suite.

Shared between the scenario loader, runner, and API layer.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


# ── Scenario models (loaded from YAML) ────────────────────────────────────


class SetupStep(BaseModel):
    type: Literal["set_chapter", "trigger_beat"]
    chapter: Optional[int] = None
    beat_id: Optional[str] = None
    variant: Optional[str] = "standard"


class WatchForEffect(BaseModel):
    type: Literal["tool_call", "character_handoff", "story_beat", "memory_saved", "timer_set"]
    tool: Optional[str] = None   # for tool_call
    to: Optional[str] = None     # for character_handoff
    label: str


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    required_chapter: int = 1
    characters_expected: List[str]
    setup_steps: List[SetupStep] = []
    user_turns: List[str]
    watch_for_effects: List[WatchForEffect] = []
    tags: List[str] = []


# ── Run request ────────────────────────────────────────────────────────────


class TestRunRequest(BaseModel):
    scenario_ids: List[str] = []
    run_all: bool = False
    user_id: str
    run_label: str


# ── Run result models (persisted as JSON) ─────────────────────────────────


class CapturedEffect(BaseModel):
    type: str
    label: str
    raw: Optional[dict] = None


class TurnResult(BaseModel):
    turn_index: int
    user_message: str
    character: Optional[str] = None
    response: str
    turn_id: str
    effects: List[CapturedEffect] = []
    logs: List[dict] = []


class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    status: Literal["complete", "failed", "skipped"]
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    turns: List[TurnResult] = []
    expected_effects_missed: List[WatchForEffect] = []


class TestRunResult(BaseModel):
    run_id: str
    run_label: str
    started_at: str
    completed_at: Optional[str] = None
    status: Literal["pending", "running", "complete", "failed", "cancelled"]
    user_id: str
    scenario_results: List[ScenarioResult] = []


# ── List endpoint summary ──────────────────────────────────────────────────


class TestRunSummary(BaseModel):
    run_id: str
    run_label: str
    started_at: str
    status: str
    scenario_count: int
    completed_count: int
    user_id: str
