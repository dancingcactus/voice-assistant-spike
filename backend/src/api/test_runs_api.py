"""
REST API router for Phase 8: Experience Testing Suite.

Mounted at prefix /api/test-runs. Provides endpoints for starting, polling,
cancelling, and reviewing test runs, plus a test-user creation convenience
endpoint for the Bulk Testing UI.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from core import scenario_loader, scenario_runner
from models.test_run_models import TestRunRequest, TestRunSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

_conversation_manager = None


def set_runner_dependencies(conversation_manager) -> None:
    """Inject the live ConversationManager into the runner module."""
    global _conversation_manager
    _conversation_manager = conversation_manager
    scenario_runner.set_conversation_manager(conversation_manager)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/scenarios")
async def list_scenarios():
    """Return all available test scenarios from the library."""
    scenarios = scenario_loader.load_all()
    return {
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "required_chapter": s.required_chapter,
                "characters_expected": s.characters_expected,
                "tags": s.tags,
                "turn_count": len(s.user_turns),
            }
            for s in scenarios
        ]
    }


@router.post("", status_code=202)
async def start_test_run(request: TestRunRequest):
    """
    Start a new test run.

    Returns a run_id immediately; execution happens in the background.
    Returns 409 if another run is already active.
    Returns 422 if any scenario IDs are unknown.
    """
    try:
        run_id = scenario_runner.start_run(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"run_id": run_id, "status": "pending"}


@router.get("")
async def list_test_runs():
    """Return all persisted runs sorted newest-first."""
    runs = scenario_runner.list_runs()
    summaries = [
        TestRunSummary(
            run_id=r.run_id,
            run_label=r.run_label,
            started_at=r.started_at,
            status=r.status,
            scenario_count=len(r.scenario_results),
            completed_count=sum(1 for s in r.scenario_results if s.status == "complete"),
            user_id=r.user_id,
        )
        for r in runs
    ]
    return {"runs": [s.model_dump() for s in summaries], "total": len(summaries)}


@router.get("/{run_id}")
async def get_test_run(run_id: str):
    """Return the full result for a specific run (status + all turns)."""
    try:
        return scenario_runner._load_run(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")


@router.post("/{run_id}/cancel", status_code=202)
async def cancel_test_run(run_id: str):
    """
    Request cancellation of an active run.

    Returns 409 if the run is already complete, failed, or cancelled.
    Returns 404 if the run is not found.
    """
    active = scenario_runner.get_active_run_id()
    if active != run_id:
        # Check if the run exists but is in a terminal state
        try:
            run = scenario_runner._load_run(run_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
        if run.status in ("complete", "failed", "cancelled"):
            raise HTTPException(
                status_code=409,
                detail=f"Run {run_id!r} is already {run.status}",
            )

    scenario_runner.request_cancel(run_id)
    return {"message": "Cancellation requested"}


@router.post("/users", status_code=201)
async def create_bulk_test_user(body: dict):
    """
    Create a new test user for use in bulk test runs.

    Sets source='bulk_testing' on the created user record so it can be
    distinguished from ordinary test users in the User Testing Tool.
    """
    from observability.user_testing_access import UserTestingAccessor

    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    accessor = UserTestingAccessor(data_dir=str(data_dir))

    name: str = body.get("name", "Bulk Test User")
    clean_slate: bool = body.get("clean_slate", True)
    copy_from_user_id: Optional[str] = body.get("copy_from_user_id")

    starting_chapter = 1
    initial_memories = None

    if copy_from_user_id and not clean_slate:
        # Copy memories and story state from another user
        try:
            exported = accessor.export_user_data(copy_from_user_id)
            initial_memories = exported.get("memories")
            from_data = exported.get("user_data", {})
            starting_chapter = from_data.get("story_progress", {}).get("current_chapter", 1)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Source user {copy_from_user_id!r} not found",
            )

    user_data = accessor.create_test_user(
        starting_chapter=starting_chapter,
        initial_memories=initial_memories if not clean_slate else None,
        tags=["bulk_testing"],
    )

    # Patch in source field so the UI can show a BULK TEST badge
    user_data.setdefault("metadata", {})["source"] = "bulk_testing"
    user_data["metadata"]["name"] = name

    from observability.data_access import DataAccessLayer
    dal = DataAccessLayer(data_dir=str(data_dir))
    dal.save_user(user_data["user_id"], user_data)

    return {
        "user_id": user_data["user_id"],
        "name": name,
        "source": "bulk_testing",
    }
