"""
Testing/Automation API for programmatic control and validation.

This API is only enabled when ENABLE_TEST_API=true in environment.
It provides endpoints for automated testing and scenario validation.
"""

import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.conversation_manager import ConversationManager
from core.memory_manager import MemoryManager
from models.user_state import UserState


# Check if test API should be enabled
def is_test_api_enabled() -> bool:
    """Check if test API is enabled via environment variable."""
    return os.getenv("ENABLE_TEST_API", "false").lower() == "true"


def require_test_api_enabled():
    """Dependency to ensure test API is enabled."""
    if not is_test_api_enabled():
        raise HTTPException(
            status_code=403,
            detail="Test API is not enabled. Set ENABLE_TEST_API=true in environment."
        )


# Create router with dependency
router = APIRouter(
    prefix="/api/test",
    tags=["testing"],
    dependencies=[Depends(require_test_api_enabled)]
)


# Request/Response models
class ConversationRequest(BaseModel):
    """Request model for sending a test conversation message."""
    user_id: str
    message: str
    include_state: bool = False


class ConversationResponse(BaseModel):
    """Response model for conversation API."""
    response_text: str
    audio_url: Optional[str] = None
    tool_calls: list = []
    state: Optional[Dict[str, Any]] = None


class StateUpdateRequest(BaseModel):
    """Request model for updating user state."""
    state_updates: Dict[str, Any]


class ScenarioRequest(BaseModel):
    """Request model for loading a test scenario."""
    scenario_name: str
    user_id: str


# Global instances (will be set by main.py)
conversation_manager: Optional[ConversationManager] = None
memory_manager: Optional[MemoryManager] = None


def set_managers(conv_mgr: ConversationManager, mem_mgr: MemoryManager):
    """Set the manager instances for the test API."""
    global conversation_manager, memory_manager
    conversation_manager = conv_mgr
    memory_manager = mem_mgr


@router.post("/conversation", response_model=ConversationResponse)
async def send_test_message(request: ConversationRequest):
    """
    Send a message programmatically and receive the response.

    This endpoint simulates a user conversation without needing WebSocket.
    Useful for automated testing and scenario validation.
    """
    if not conversation_manager:
        raise HTTPException(status_code=500, detail="Conversation manager not initialized")

    # Handle the message
    # Use user_id as session_id for testing (each test user has own session)
    response = await conversation_manager.handle_user_message(
        session_id=f"test-session-{request.user_id}",
        user_message=request.message,
        user_id=request.user_id,
        input_mode="chat"  # Always use chat mode for test API
    )

    # Build response
    result = ConversationResponse(
        response_text=response.get("text", ""),
        audio_url=response.get("audio_url"),
        tool_calls=response.get("tool_calls", [])
    )

    # Include state if requested
    if request.include_state:
        state = memory_manager.load_user_state(request.user_id)
        result.state = state.model_dump() if state else None

    return result


@router.get("/state/{user_id}")
async def get_user_state(user_id: str):
    """
    Get the complete state for a user.

    Returns story progress, conversation history, device states, and preferences.
    """
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    state = memory_manager.load_user_state(user_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return state.model_dump()


@router.post("/state/{user_id}")
async def update_user_state(user_id: str, request: StateUpdateRequest):
    """
    Update specific fields in user state.

    Useful for setting up test scenarios (e.g., setting chapter, unlocking beats).
    """
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    # Get current state
    state = memory_manager.load_user_state(user_id)
    if not state:
        # Create new state if it doesn't exist
        state = UserState(user_id=user_id)

    # Update fields
    for field, value in request.state_updates.items():
        if hasattr(state, field):
            setattr(state, field, value)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {field}"
            )

    # Update cache and save state
    memory_manager._user_cache[user_id] = state
    memory_manager.save_user_state(user_id, force=True)

    return {"status": "success", "updated_fields": list(request.state_updates.keys())}


@router.post("/reset/{user_id}")
async def reset_user_state(user_id: str):
    """
    Reset user state to a clean slate.

    Useful for starting test scenarios from scratch.
    """
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    # Create fresh state
    fresh_state = UserState(user_id=user_id)
    memory_manager._user_cache[user_id] = fresh_state

    memory_manager.save_user_state(user_id, force=True)

    return {
        "status": "success",
        "message": f"User {user_id} state reset to defaults"
    }


@router.post("/scenario")
async def load_scenario(request: ScenarioRequest):
    """
    Load a predefined test scenario.

    Test scenarios are JSON files that define:
    - Initial user state
    - Expected conversation flow
    - Validation criteria
    """
    import json
    from pathlib import Path

    # Look for scenario file
    # Paths relative to project root (backend/src needs ../..)
    project_root = Path(__file__).parent.parent.parent.parent
    scenario_paths = [
        project_root / "tests/scenarios/story" / f"{request.scenario_name}.json",
        project_root / "tests/scenarios/character" / f"{request.scenario_name}.json",
        project_root / "tests/scenarios/tools" / f"{request.scenario_name}.json",
        project_root / "tests/scenarios/edge-cases" / f"{request.scenario_name}.json",
    ]

    scenario_file = None
    for path in scenario_paths:
        if path.exists():
            scenario_file = path
            break

    if not scenario_file:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{request.scenario_name}' not found"
        )

    # Load scenario
    with open(scenario_file, 'r') as f:
        scenario = json.load(f)

    # Apply initial state if provided
    if "initial_state" in scenario:
        state = UserState(user_id=request.user_id)
        for field, value in scenario["initial_state"].items():
            if hasattr(state, field):
                setattr(state, field, value)
        memory_manager._user_cache[request.user_id] = state

        memory_manager.save_user_state(request.user_id, force=True)

    return {
        "status": "success",
        "scenario": request.scenario_name,
        "description": scenario.get("description", ""),
        "steps": len(scenario.get("conversation_flow", []))
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for the test API."""
    return {
        "status": "healthy",
        "test_api_enabled": True,
        "conversation_manager": conversation_manager is not None,
        "memory_manager": memory_manager is not None
    }
