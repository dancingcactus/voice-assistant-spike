"""
Tests for Phase 8 Milestone 2: Scenario Runner Backend.

Covers:
- start_run() returns a run_id and persists the initial pending file
- start_run() raises RuntimeError when another run is already active
- _execute_scenario() with a mocked ConversationManager builds correct TurnResult
- _capture_effects() maps request_handoff → character_handoff effect
- _capture_effects() maps advance_story_beat → story_beat effect
- _capture_effects() maps set_timer → timer_set effect
- _capture_effects() maps save_memory → memory_saved effect
- _capture_effects() maps unknown tool call → generic tool_call effect
- expected_effects_missed: expected effect that fires → not in missed list
- expected_effects_missed: expected effect that does not fire → in missed list
- 50-run cap: creating 51 runs deletes the oldest
- cancel: setting cancel flag stops run between scenarios; completed results preserved
- list_runs() returns runs newest-first
- GET /api/test-runs/scenarios returns correct count and fields
- POST /api/test-runs returns 409 when a run is already active
- GET /api/test-runs/{run_id} returns 404 for unknown run_id
- POST /api/test-runs/{run_id}/cancel returns 409 for already-complete run
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import core.scenario_runner as runner_module
from core.scenario_runner import (
    _compute_missed_effects,
    _enforce_run_cap,
    _load_run,
    _persist_run,
    _tool_call_to_effect,
    list_runs,
    start_run,
)
from models.test_run_models import (
    CapturedEffect,
    ScenarioResult,
    TestRunRequest,
    TestRunResult,
    TurnResult,
    WatchForEffect,
)
from observability.tool_call_models import ToolCallLog, ToolCallStatus


# ===========================================================================
# Helpers
# ===========================================================================


def _make_tool_call(
    tool_name: str,
    request: dict | None = None,
    response: dict | None = None,
    character: str = "delilah",
    turn_id: str = "tid-001",
) -> ToolCallLog:
    from datetime import datetime

    return ToolCallLog(
        call_id="call-001",
        turn_id=turn_id,
        timestamp=datetime.now(),
        duration_ms=10,
        tool_name=tool_name,
        user_id="test_user",
        character=character,
        request=request or {},
        response=response or {},
        status=ToolCallStatus.SUCCESS,
    )


def _fake_run(tmp_path: Path, run_id: str, started_at: str | None = None) -> TestRunResult:
    """Create and persist a minimal run in *tmp_path*."""
    run = TestRunResult(
        run_id=run_id,
        run_label="stub",
        started_at=started_at or datetime.now(timezone.utc).isoformat(),
        status="complete",
        user_id="u",
    )
    (tmp_path / f"{run_id}.json").write_text(run.model_dump_json(), encoding="utf-8")
    return run


# ===========================================================================
# _tool_call_to_effect
# ===========================================================================


class TestToolCallToEffect:
    def test_request_handoff_maps_to_character_handoff(self):
        tc = _make_tool_call("request_handoff", response={"to": "hank"})
        effect = _tool_call_to_effect(tc)
        assert effect.type == "character_handoff"
        assert "hank" in effect.label

    def test_advance_story_beat_maps_to_story_beat(self):
        tc = _make_tool_call("advance_story_beat", request={"beat_id": "hank_arrival"})
        effect = _tool_call_to_effect(tc)
        assert effect.type == "story_beat"
        assert "hank_arrival" in effect.label

    def test_set_timer_maps_to_timer_set(self):
        tc = _make_tool_call("set_timer", request={"duration": "5 minutes"})
        effect = _tool_call_to_effect(tc)
        assert effect.type == "timer_set"
        assert "5 minutes" in effect.label

    def test_save_memory_maps_to_memory_saved(self):
        tc = _make_tool_call("save_memory", response={"saved": "allergic to nuts"})
        effect = _tool_call_to_effect(tc)
        assert effect.type == "memory_saved"
        assert "memory_saved" == effect.type

    def test_unknown_tool_maps_to_generic_tool_call(self):
        tc = _make_tool_call("some_other_tool")
        effect = _tool_call_to_effect(tc)
        assert effect.type == "tool_call"
        assert "some_other_tool" in effect.label

    def test_raw_field_is_set(self):
        tc = _make_tool_call("set_timer", request={"duration": "3 minutes"})
        effect = _tool_call_to_effect(tc)
        assert effect.raw is not None
        assert effect.raw["tool_name"] == "set_timer"


# ===========================================================================
# _compute_missed_effects
# ===========================================================================


class TestComputeMissedEffects:
    def _turn(self, effects: list[CapturedEffect]) -> TurnResult:
        return TurnResult(
            turn_index=0,
            user_message="test",
            character="delilah",
            response="ok",
            turn_id="t",
            effects=effects,
        )

    def test_fired_effect_not_in_missed(self):
        want = WatchForEffect(type="story_beat", label="beat fired")
        fired = CapturedEffect(type="story_beat", label="beat fired")
        missed = _compute_missed_effects([want], [self._turn([fired])])
        assert missed == []

    def test_unfired_effect_is_in_missed(self):
        want = WatchForEffect(type="story_beat", label="beat fired")
        missed = _compute_missed_effects([want], [self._turn([])])
        assert len(missed) == 1
        assert missed[0].label == "beat fired"

    def test_partial_miss(self):
        wants = [
            WatchForEffect(type="story_beat", label="beat fired"),
            WatchForEffect(type="character_handoff", label="handoff"),
        ]
        fired = CapturedEffect(type="story_beat", label="beat fired")
        missed = _compute_missed_effects(wants, [self._turn([fired])])
        assert len(missed) == 1
        assert missed[0].type == "character_handoff"

    def test_empty_expected_returns_empty(self):
        assert _compute_missed_effects([], []) == []


# ===========================================================================
# Run persistence and 50-run cap
# ===========================================================================


class TestRunPersistence:
    def test_persist_then_load(self, tmp_path):
        with patch.object(runner_module, "RUNS_DIR", tmp_path):
            run = TestRunResult(
                run_id="run_abc",
                run_label="test",
                started_at="2026-02-24T10:00:00Z",
                status="complete",
                user_id="u",
            )
            _persist_run(run)
            loaded = _load_run("run_abc")
            assert loaded.run_id == "run_abc"
            assert loaded.status == "complete"

    def test_load_raises_file_not_found(self, tmp_path):
        with patch.object(runner_module, "RUNS_DIR", tmp_path):
            with pytest.raises(FileNotFoundError):
                _load_run("nonexistent_run")

    def test_enforce_cap_deletes_oldest(self, tmp_path):
        # Create 51 stub files with slightly different mtimes
        for i in range(51):
            p = tmp_path / f"run_{i:04d}.json"
            p.write_text("{}")
            # Nudge mtime so sorting is deterministic
            mtime = time.time() - (51 - i)
            import os
            os.utime(p, (mtime, mtime))

        with patch.object(runner_module, "RUNS_DIR", tmp_path):
            _enforce_run_cap(max_runs=50)

        remaining = list(tmp_path.glob("*.json"))
        assert len(remaining) == 50
        # The oldest file (run_0000.json) should be gone
        assert not (tmp_path / "run_0000.json").exists()
        # The newest (run_0050.json) should be present
        assert (tmp_path / "run_0050.json").exists()

    def test_list_runs_returns_newest_first(self, tmp_path):
        import os

        with patch.object(runner_module, "RUNS_DIR", tmp_path):
            for i, rid in enumerate(["run_a", "run_b", "run_c"]):
                run = TestRunResult(
                    run_id=rid,
                    run_label=rid,
                    started_at="2026-02-24T10:00:00Z",
                    status="complete",
                    user_id="u",
                )
                p = tmp_path / f"{rid}.json"
                p.write_text(run.model_dump_json())
                mtime = time.time() - (10 - i)  # run_a oldest, run_c newest
                os.utime(p, (mtime, mtime))

            runs = list_runs()

        ids = [r.run_id for r in runs]
        assert ids == ["run_c", "run_b", "run_a"]


# ===========================================================================
# start_run and concurrency guard
# ===========================================================================


class TestStartRun:
    def _make_request(self, run_all: bool = True) -> TestRunRequest:
        return TestRunRequest(
            scenario_ids=[],
            run_all=run_all,
            user_id="test_user",
            run_label="smoke",
        )

    def test_start_run_persists_pending_file(self, tmp_path):
        mock_cm = AsyncMock()
        mock_cm.handle_user_message = AsyncMock(return_value={
            "text": "hi",
            "character": "delilah",
            "metadata": {"turn_id": "tid-x"},
        })

        with (
            patch.object(runner_module, "RUNS_DIR", tmp_path),
            patch.object(runner_module, "_conversation_manager", mock_cm),
            patch.object(runner_module, "_active_run_id", None),
            patch("core.scenario_runner.asyncio.create_task"),
            patch("core.scenario_runner.load_all") as mock_load,
        ):
            from models.test_run_models import Scenario
            mock_load.return_value = [
                Scenario(
                    id="s1",
                    name="S1",
                    description="d",
                    characters_expected=["delilah"],
                    user_turns=["hello"],
                    tags=["test"],
                )
            ]
            run_id = start_run(self._make_request())

        assert run_id.startswith("run_")
        path = tmp_path / f"{run_id}.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["status"] == "pending"
        assert len(data["scenario_results"]) == 1
        assert data["scenario_results"][0]["status"] == "skipped"

        # Reset global
        runner_module._active_run_id = None

    def test_start_run_raises_when_active(self, tmp_path):
        with (
            patch.object(runner_module, "RUNS_DIR", tmp_path),
            patch.object(runner_module, "_active_run_id", "run_existing"),
        ):
            with pytest.raises(RuntimeError, match="already active"):
                start_run(self._make_request())

    def test_start_run_raises_on_unknown_scenario_id(self, tmp_path):
        with (
            patch.object(runner_module, "RUNS_DIR", tmp_path),
            patch.object(runner_module, "_active_run_id", None),
            patch.object(runner_module, "_conversation_manager", AsyncMock()),
        ):
            req = TestRunRequest(
                scenario_ids=["nonexistent_id"],
                run_all=False,
                user_id="u",
                run_label="x",
            )
            with pytest.raises(ValueError, match="nonexistent_id"):
                start_run(req)


# ===========================================================================
# _execute_scenario (mocked ConversationManager)
# ===========================================================================


class TestExecuteScenario:
    @pytest.mark.asyncio
    async def test_builds_turn_results(self, tmp_path):
        from core.scenario_runner import _execute_scenario
        from models.test_run_models import Scenario

        scenario = Scenario(
            id="s1",
            name="Test scenario",
            description="desc",
            characters_expected=["delilah"],
            user_turns=["hello", "goodbye"],
            tags=["test"],
        )

        mock_cm = AsyncMock()
        mock_cm.handle_user_message = AsyncMock(return_value={
            "text": "Hi sugar!",
            "character": "delilah",
            "metadata": {"turn_id": "turn-abc"},
        })

        with (
            patch.object(runner_module, "_conversation_manager", mock_cm),
            patch("core.scenario_runner._capture_effects", return_value=[]),
            patch(
                "core.scenario_runner._get_log_handler" if hasattr(runner_module, "_get_log_handler")
                else "observability.log_handler.get_handler",
                return_value=MagicMock(get_logs=MagicMock(return_value=[])),
            ),
        ):
            # Patch the imported get_handler inside the runner
            with patch("observability.log_handler.get_handler") as mock_handler:
                mock_handler.return_value.get_logs.return_value = []
                result = await _execute_scenario(scenario, "test_user")

        assert result.status == "complete"
        assert len(result.turns) == 2
        assert result.turns[0].user_message == "hello"
        assert result.turns[0].turn_id == "turn-abc"
        assert result.turns[0].character == "delilah"
        assert result.turns[1].user_message == "goodbye"

    @pytest.mark.asyncio
    async def test_failed_scenario_on_exception(self):
        from core.scenario_runner import _execute_scenario
        from models.test_run_models import Scenario

        scenario = Scenario(
            id="s_fail",
            name="Failing",
            description="d",
            characters_expected=["delilah"],
            user_turns=["hello"],
            tags=["test"],
        )

        mock_cm = AsyncMock()
        mock_cm.handle_user_message = AsyncMock(side_effect=RuntimeError("LLM error"))

        with patch.object(runner_module, "_conversation_manager", mock_cm):
            result = await _execute_scenario(scenario, "u")

        assert result.status == "failed"
        assert "LLM error" in result.error


# ===========================================================================
# Cancel behaviour
# ===========================================================================


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_stops_between_scenarios(self, tmp_path):
        """Completed scenario result is preserved; remaining are skipped."""
        from core.scenario_runner import _run_scenarios
        from models.test_run_models import Scenario

        scenarios = [
            Scenario(id=f"s{i}", name=f"S{i}", description="d",
                     characters_expected=["delilah"], user_turns=["hi"],
                     tags=["test"])
            for i in range(3)
        ]

        run = TestRunResult(
            run_id="run_cancel_test",
            run_label="cancel",
            started_at=datetime.now(timezone.utc).isoformat(),
            status="pending",
            user_id="u",
            scenario_results=[
                ScenarioResult(scenario_id=s.id, scenario_name=s.name, status="skipped")
                for s in scenarios
            ],
        )

        with patch.object(runner_module, "RUNS_DIR", tmp_path):
            _persist_run(run)

        async def _fake_exec(scenario, user_id):
            # Cancel after first scenario executes
            if scenario.id == "s0":
                runner_module._cancel_flags["run_cancel_test"] = True
            return ScenarioResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                status="complete",
            )

        with (
            patch.object(runner_module, "RUNS_DIR", tmp_path),
            patch("core.scenario_runner._execute_scenario", side_effect=_fake_exec),
        ):
            await _run_scenarios("run_cancel_test", scenarios, "u")

        loaded = (tmp_path / "run_cancel_test.json").read_text()
        data = json.loads(loaded)
        assert data["status"] == "cancelled"
        statuses = [r["status"] for r in data["scenario_results"]]
        # s0 completes, s1 and s2 remain skipped
        assert statuses[0] == "complete"
        assert statuses[1] == "skipped"
        assert statuses[2] == "skipped"


# ===========================================================================
# REST endpoints via TestClient
# ===========================================================================


@pytest.fixture
def test_client(tmp_path):
    """Create a FastAPI TestClient with the test_runs router and a patched RUNS_DIR."""
    from fastapi import FastAPI
    from api.test_runs_api import router, set_runner_dependencies

    app = FastAPI()
    app.include_router(router)
    set_runner_dependencies(conversation_manager=AsyncMock())

    with patch.object(runner_module, "RUNS_DIR", tmp_path):
        yield TestClient(app), tmp_path


class TestApiEndpoints:
    def test_get_scenarios_returns_eleven(self, test_client):
        client, _ = test_client
        response = client.get("/api/test-runs/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) == 11

    def test_get_scenarios_includes_required_fields(self, test_client):
        client, _ = test_client
        response = client.get("/api/test-runs/scenarios")
        first = response.json()["scenarios"][0]
        for field in ("id", "name", "description", "required_chapter",
                      "characters_expected", "tags", "turn_count"):
            assert field in first, f"Missing field: {field}"

    def test_get_run_404_for_unknown_id(self, test_client):
        client, _ = test_client
        response = client.get("/api/test-runs/run_does_not_exist")
        assert response.status_code == 404

    def test_post_run_409_when_already_active(self, test_client):
        client, tmp_path = test_client
        with patch.object(runner_module, "_active_run_id", "run_existing"):
            response = client.post(
                "/api/test-runs",
                json={
                    "scenario_ids": [],
                    "run_all": True,
                    "user_id": "u",
                    "run_label": "test",
                },
            )
        assert response.status_code == 409
        assert "already active" in response.json()["detail"]

    def test_cancel_409_for_complete_run(self, test_client):
        client, tmp_path = test_client
        run = TestRunResult(
            run_id="run_done",
            run_label="done",
            started_at="2026-02-24T10:00:00Z",
            status="complete",
            user_id="u",
        )
        (tmp_path / "run_done.json").write_text(run.model_dump_json())

        with patch.object(runner_module, "_active_run_id", None):
            response = client.post("/api/test-runs/run_done/cancel")
        assert response.status_code == 409

    def test_cancel_404_for_unknown_run(self, test_client):
        client, _ = test_client
        with patch.object(runner_module, "_active_run_id", None):
            response = client.post("/api/test-runs/run_ghost/cancel")
        assert response.status_code == 404

    def test_list_runs_returns_empty_initially(self, test_client):
        client, _ = test_client
        response = client.get("/api/test-runs")
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []
        assert data["total"] == 0

    def test_list_runs_returns_persisted_run(self, test_client):
        client, tmp_path = test_client
        run = TestRunResult(
            run_id="run_visible",
            run_label="visible",
            started_at="2026-02-24T10:00:00Z",
            status="complete",
            user_id="u",
        )
        (tmp_path / "run_visible.json").write_text(run.model_dump_json())
        response = client.get("/api/test-runs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["runs"][0]["run_id"] == "run_visible"

    def test_get_run_returns_full_result(self, test_client):
        client, tmp_path = test_client
        run = TestRunResult(
            run_id="run_full",
            run_label="full",
            started_at="2026-02-24T10:00:00Z",
            status="complete",
            user_id="u",
        )
        (tmp_path / "run_full.json").write_text(run.model_dump_json())
        response = client.get("/api/test-runs/run_full")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run_full"
        assert data["status"] == "complete"


# ===========================================================================
# ToolCallLog turn_id field
# ===========================================================================


class TestToolCallLogTurnId:
    def test_turn_id_field_exists(self):
        from observability.tool_call_models import ToolCallLog
        assert "turn_id" in ToolCallLog.model_fields

    def test_turn_id_defaults_to_none(self):
        tc = _make_tool_call("some_tool")
        # Turn_id can be set or None
        tc_no_tid = ToolCallLog(
            call_id="x",
            timestamp=datetime.now(),
            duration_ms=1,
            tool_name="t",
            user_id="u",
            request={},
            response={},
            status=ToolCallStatus.SUCCESS,
        )
        assert tc_no_tid.turn_id is None

    def test_turn_id_can_be_set(self):
        tc = _make_tool_call("some_tool", turn_id="abc-123")
        assert tc.turn_id == "abc-123"


# ===========================================================================
# ToolCallDataAccess.get_tool_calls_for_turn
# ===========================================================================


class TestGetToolCallsForTurn:
    def test_returns_matching_turn_ids(self, tmp_path):
        from observability.tool_call_access import ToolCallDataAccess

        access = ToolCallDataAccess(data_dir=str(tmp_path))
        tc1 = _make_tool_call("set_timer", turn_id="tid-A")
        tc2 = _make_tool_call("save_memory", turn_id="tid-B")
        access.append_tool_call(tc1)
        access.append_tool_call(tc2)

        results = access.get_tool_calls_for_turn("tid-A", user_id="test_user")
        assert len(results) == 1
        assert results[0].tool_name == "set_timer"

    def test_returns_empty_for_unknown_turn_id(self, tmp_path):
        from observability.tool_call_access import ToolCallDataAccess

        access = ToolCallDataAccess(data_dir=str(tmp_path))
        results = access.get_tool_calls_for_turn("nonexistent", user_id="test_user")
        assert results == []
