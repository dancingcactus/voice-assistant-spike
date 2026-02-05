"""
Observability API for Phase 1.5

Provides REST endpoints for debugging and testing the voice assistant system.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import os
from pathlib import Path

from .data_access import DataAccessLayer
from .story_access import StoryAccessLayer
from .memory_access import MemoryAccessor
from .user_testing_access import UserTestingAccessor
from .tool_call_access import ToolCallDataAccess
from .character_access import CharacterAccessLayer

# Import StoryEngine for auto-advance functionality
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.story_engine import StoryEngine
from .tool_call_models import (
    ToolCallLog,
    ToolCallFilter,
    ToolCallStatus,
    ToolCallStatistics,
    ReplayRequest,
    ReplayResult,
)


# Configuration
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "dev_token_12345")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# Find project root and use its data directory for consistency across DALs
project_root = Path(__file__).parent.parent.parent.parent
data_dir = project_root / "data"

# Initialize FastAPI app
app = FastAPI(
    title="Hey Chat! Observability API",
    description="Debugging and testing tools for the voice assistant system",
    version="1.0.0"
)

# Note: CORS is handled by the main app when this is mounted as a sub-application
# Do not add CORS middleware here to avoid conflicts

# Initialize data access layers
dal = DataAccessLayer(data_dir=str(data_dir))
story_dal = StoryAccessLayer(project_root=str(project_root))
memory_dal = MemoryAccessor(data_dir=str(data_dir))
user_testing_dal = UserTestingAccessor(data_dir=str(data_dir))
tool_call_dal = ToolCallDataAccess(data_dir=str(data_dir))
character_dal = CharacterAccessLayer(project_root=project_root)

# Initialize Story Engine for auto-advance and conditional progression
story_engine = StoryEngine(story_dir=str(project_root / "story"), memory_manager=None)


# Authentication
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify API token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")
    if token != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class UserSummary(BaseModel):
    user_id: str
    current_chapter: int
    interaction_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserDetailResponse(BaseModel):
    user_id: str
    preferences: dict
    conversation_history: dict
    device_preferences: dict
    story_progress: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChapterSummary(BaseModel):
    id: int
    title: str
    description: str
    is_current: bool
    is_completed: bool
    is_locked: bool


class BeatDeliveryInfo(BaseModel):
    timestamp: Optional[str] = None
    variant: Optional[str] = None
    stage: Optional[int] = None


class BeatSummary(BaseModel):
    id: str
    type: str
    required: bool
    priority: str
    status: str
    delivery_info: Optional[BeatDeliveryInfo] = None


class ChapterProgressSummary(BaseModel):
    current_chapter: int
    beats_total: int
    beats_delivered: int
    beats_ready: int
    interaction_count: int
    chapter_start_time: Optional[str] = None


class TriggerBeatRequest(BaseModel):
    variant: str = "standard"
    stage: Optional[int] = 1


class AutoAdvanceNotificationResponse(BaseModel):
    beat_id: str
    name: str
    chapter_id: int
    ready_since: str
    content: str
    notified: bool


class MemoryResponse(BaseModel):
    memory_id: str
    category: str
    content: str
    source: str
    importance: int
    verified: bool
    created_at: str
    last_accessed: Optional[str] = None
    access_count: int
    metadata: dict


class CreateMemoryRequest(BaseModel):
    category: str
    content: str
    source: str
    importance: int = 5
    verified: bool = False
    metadata: Optional[dict] = None


class UpdateMemoryRequest(BaseModel):
    category: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[int] = None
    verified: Optional[bool] = None
    metadata: Optional[dict] = None


class ContextPreviewResponse(BaseModel):
    total_memories: int
    context_memories: int
    estimated_tokens: int
    by_category: dict
    memories: List[dict]


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/users", response_model=List[UserSummary])
async def list_users(authorization: Optional[str] = Header(None)):
    """List all users with summary information."""
    verify_token(authorization)

    user_ids = dal.list_users()
    users = []

    for user_id in user_ids:
        user_data = dal.get_user(user_id)
        if user_data:
            users.append(UserSummary(
                user_id=user_id,
                current_chapter=user_data.get("story_progress", {}).get("current_chapter", 1),
                interaction_count=user_data.get("story_progress", {}).get("interaction_count", 0),
                created_at=user_data.get("created_at"),
                updated_at=user_data.get("updated_at")
            ))

    return users


@app.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, authorization: Optional[str] = Header(None)):
    """Get detailed user information."""
    verify_token(authorization)

    user_data = dal.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return UserDetailResponse(**user_data)


# Story Beat Endpoints

@app.get("/story/chapters", response_model=List[ChapterSummary])
async def list_chapters(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """List all chapters with user progress status."""
    verify_token(authorization)

    chapters = story_dal.get_all_chapters()
    progress = story_dal.get_user_story_progress(user_id)

    if not progress:
        # No progress yet, all locked except chapter 1
        return [
            ChapterSummary(
                id=ch["id"],
                title=ch["title"],
                description=ch["description"],
                is_current=ch["id"] == 1,
                is_completed=False,
                is_locked=ch["id"] != 1
            )
            for ch in chapters
        ]

    current_chapter = progress.get("current_chapter", 1)

    return [
        ChapterSummary(
            id=ch["id"],
            title=ch["title"],
            description=ch["description"],
            is_current=ch["id"] == current_chapter,
            is_completed=ch["id"] < current_chapter,
            is_locked=ch["id"] > current_chapter
        )
        for ch in chapters
    ]


@app.get("/story/chapters/{chapter_id}/beats", response_model=List[BeatSummary])
async def list_chapter_beats(
    chapter_id: int,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """List all beats for a chapter with user progress."""
    verify_token(authorization)

    enriched_beats = story_dal.get_enriched_chapter_beats(chapter_id, user_id)

    return [
        BeatSummary(
            id=beat["id"],
            type=beat["type"],
            required=beat["required"],
            priority=beat["priority"],
            status=beat["status"],
            delivery_info=BeatDeliveryInfo(**beat["delivery_info"]) if beat["delivery_info"] else None
        )
        for beat in enriched_beats
    ]


@app.get("/story/chapters/{chapter_id}/beats/{beat_id}")
async def get_beat_detail(
    chapter_id: int,
    beat_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get detailed information about a specific beat."""
    verify_token(authorization)

    beat = story_dal.get_beat(chapter_id, beat_id)
    if not beat:
        raise HTTPException(status_code=404, detail=f"Beat {beat_id} not found in chapter {chapter_id}")

    user_status = story_dal.get_user_beat_status(user_id, beat_id)

    return {
        **beat,
        "user_status": user_status
    }


@app.get("/story/users/{user_id}/progress", response_model=ChapterProgressSummary)
async def get_user_story_progress(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get user's current chapter progress summary."""
    verify_token(authorization)

    progress_summary = story_dal.get_user_chapter_progress_summary(user_id)
    return ChapterProgressSummary(**progress_summary)


@app.get("/story/chapters/{chapter_id}/diagram")
async def get_chapter_diagram(
    chapter_id: int,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get Mermaid diagram for chapter beat flow.

    If user_id is provided, beats will be color-coded by delivery status:
    - Green: Delivered
    - Yellow/Amber: Ready (can be triggered)
    - Blue: Not started
    - Gray: Locked (prerequisites not met)

    If user_id is not provided, beats are colored by required/optional status.
    """
    verify_token(authorization)

    diagram = story_dal.generate_chapter_flow_diagram(chapter_id, user_id)
    return {
        "chapter_id": chapter_id,
        "diagram": diagram,
        "format": "mermaid",
        "user_specific": user_id is not None
    }


@app.post("/story/users/{user_id}/beats/{beat_id}/trigger")
async def trigger_beat(
    user_id: str,
    beat_id: str,
    request: TriggerBeatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Manually trigger a beat delivery (for testing).
    This updates the user's story progress to mark the beat as delivered.
    """
    verify_token(authorization)

    # Get user data
    user_data = dal.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Update story progress
    story_progress = user_data.get("story_progress", {})
    beats_delivered = story_progress.get("beats_delivered", {})

    # Mark beat as delivered
    beats_delivered[beat_id] = {
        "delivered": True,
        "timestamp": datetime.now().isoformat(),
        "variant": request.variant,
        "stage": request.stage
    }

    story_progress["beats_delivered"] = beats_delivered
    user_data["story_progress"] = story_progress
    user_data["updated_at"] = datetime.now().isoformat()

    # Save updated user data
    dal.save_user(user_id, user_data)

    return {
        "status": "success",
        "message": f"Beat {beat_id} triggered successfully",
        "beat_id": beat_id,
        "variant": request.variant,
        "stage": request.stage
    }


# -----------------------------
# Milestone 3: Untrigger API
# -----------------------------

class UntriggerRequest(BaseModel):
    stage: Optional[int] = None


class UntriggerResult(BaseModel):
    beat_id: str
    stage: Optional[int] = None
    untriggered: List[str]
    dependencies_affected: List[str]
    explanation: str
    dry_run: bool
    timestamp: str


def _find_dependent_beats(chapter_id: int, target_beat_id: str) -> List[str]:
    """Find beats in the same chapter that depend on target_beat_id (directly)."""
    dependents: List[str] = []
    beats = story_dal.get_chapter_beats(chapter_id)
    prereq_key = f"{target_beat_id}_delivered"

    for beat in beats:
        conditions = beat.get("conditions", {}) or {}
        if conditions.get(prereq_key) is True:
            dependents.append(beat.get("id"))
    return dependents


def _find_transitive_dependents(chapter_id: int, beat_id: str, delivered_map: dict) -> List[str]:
    """Breadth-first search of dependents that are currently delivered."""
    to_visit = [beat_id]
    affected: List[str] = []
    seen = set()

    while to_visit:
        current = to_visit.pop(0)
        if current in seen:
            continue
        seen.add(current)

        direct = _find_dependent_beats(chapter_id, current)
        for dep in direct:
            # Only include if currently delivered
            if delivered_map.get(dep, {}).get("delivered"):
                if dep not in affected:
                    affected.append(dep)
                to_visit.append(dep)

    # Remove the root beat if it got added inadvertently
    return [b for b in affected if b != beat_id]


@app.post("/story/users/{user_id}/beats/{beat_id}/untrigger", response_model=UntriggerResult)
async def untrigger_beat(
    user_id: str,
    beat_id: str,
    request: UntriggerRequest,
    dry_run: bool = True,
    authorization: Optional[str] = Header(None)
):
    """
    Roll back a delivered beat (and any dependents). If dry_run=true, returns
    a preview of what would be changed without mutating user state.

    Notes:
    - Dependency detection is currently based on same-chapter prerequisites
      declared via conditions like "<beat_id>_delivered": true.
    - Progression beats: if a stage is provided, higher stages are implicitly
      considered affected.
    """
    verify_token(authorization)

    user_data = dal.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    story_progress = user_data.get("story_progress", {})
    current_chapter = story_progress.get("current_chapter", 1)
    beats_delivered = story_progress.get("beats_delivered", {})

    # Build dependency list (transitive, currently delivered only)
    dependents = _find_transitive_dependents(current_chapter, beat_id, beats_delivered)

    # If a stage is specified, add a note to explanation but we reset the whole beat for now
    explanation_parts = [
        f"Untriggering '{beat_id}' will roll back it and {len(dependents)} dependent beat(s)."
    ]
    if request.stage is not None:
        explanation_parts.append(
            f"Requested stage {request.stage}; stage-specific rollback will reset the beat's entry."
        )

    to_remove = [beat_id] + dependents

    result = UntriggerResult(
        beat_id=beat_id,
        stage=request.stage,
        untriggered=to_remove,
        dependencies_affected=dependents,
        explanation=" ".join(explanation_parts),
        dry_run=dry_run,
        timestamp=datetime.utcnow().isoformat()
    )

    if dry_run:
        return result

    # Apply mutation: remove beats from beats_delivered
    mutated = False
    for b in to_remove:
        if b in beats_delivered:
            del beats_delivered[b]
            mutated = True

    if mutated:
        # Persist changes
        story_progress["beats_delivered"] = beats_delivered
        user_data["story_progress"] = story_progress
        user_data["updated_at"] = datetime.utcnow().isoformat()
        dal.save_user(user_id, user_data)

    return result


@app.get("/story/auto-advance-ready/{user_id}", response_model=List[AutoAdvanceNotificationResponse])
async def get_auto_advance_ready(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get all auto-advance beats that are ready for delivery.
    """
    verify_token(authorization)

    # Sync user state from DAL to story engine (since story engine has no memory_manager)
    user_data = dal.get_user(user_id)
    if user_data:
        # Get or create user state in story engine
        state = story_engine.get_or_create_user_state(user_id)
        # Update chapter from user data
        current_chapter = user_data.get("story_progress", {}).get("current_chapter", 1)
        state.current_chapter = current_chapter

        # Initialize chapter progress if needed
        if current_chapter not in state.chapter_progress:
            from models.story import ChapterProgress, BeatProgress
            state.chapter_progress[current_chapter] = ChapterProgress(
                chapter_id=current_chapter,
                started_at=user_data.get("story_progress", {}).get("chapter_start_time"),
                interaction_count=user_data.get("story_progress", {}).get("interaction_count", 0)
            )

        # Load beat progress from user data
        beats_delivered = user_data.get("story_progress", {}).get("beats_delivered", {})
        if beats_delivered:
            from models.story import BeatProgress
            for beat_id, beat_data in beats_delivered.items():
                if beat_data.get("delivered"):
                    # Add beat progress to the chapter
                    beat_progress = BeatProgress(
                        beat_id=beat_id,
                        delivered=True,
                        current_stage=beat_data.get("current_stage", 1),
                        delivered_stages=set(beat_data.get("delivered_stages", [])),
                        first_delivered_at=beat_data.get("first_delivered_at")
                    )
                    state.chapter_progress[current_chapter].beat_progress[beat_id] = beat_progress

    # Get ready beats from story engine
    ready_beats = story_engine.get_auto_advance_ready(user_id)

    # Convert to response format
    return [
        AutoAdvanceNotificationResponse(
            beat_id=beat.beat_id,
            name=beat.name,
            chapter_id=beat.chapter_id,
            ready_since=beat.ready_since.isoformat(),
            content=beat.content,
            notified=beat.notified
        )
        for beat in ready_beats
    ]


@app.post("/story/auto-advance/{user_id}/{beat_id}")
async def deliver_auto_advance_beat(
    user_id: str,
    beat_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Deliver an auto-advance beat to the user.
    """
    verify_token(authorization)

    # Deliver the beat
    content = story_engine.deliver_auto_advance_beat(user_id, beat_id)

    if not content:
        raise HTTPException(
            status_code=404,
            detail=f"Auto-advance beat {beat_id} not found in queue for user {user_id}"
        )

    # Sync the updated state back to DAL (since story_engine has no memory_manager)
    user_data = dal.get_user(user_id)
    if user_data:
        # Update beats_delivered in user data
        if "story_progress" not in user_data:
            user_data["story_progress"] = {}
        if "beats_delivered" not in user_data["story_progress"]:
            user_data["story_progress"]["beats_delivered"] = {}

        # Mark beat as delivered
        user_data["story_progress"]["beats_delivered"][beat_id] = {
            "delivered": True,
            "current_stage": 1,
            "delivered_stages": [1],
            "first_delivered_at": datetime.utcnow().isoformat()
        }

        # Save back to DAL
        dal.save_user(user_id, user_data)

    return {
        "status": "success",
        "message": f"Auto-advance beat {beat_id} delivered successfully",
        "beat_id": beat_id,
        "content": content
    }


# Memory Endpoints

@app.get("/memory/users/{user_id}", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str,
    category: Optional[str] = None,
    min_importance: Optional[int] = None,
    authorization: Optional[str] = Header(None)
):
    """Get all memories for a user with optional filtering."""
    verify_token(authorization)

    memories = memory_dal.get_all_memories(user_id)

    # Apply filters
    if category:
        memories = [m for m in memories if m.category == category]
    if min_importance is not None:
        memories = [m for m in memories if m.importance >= min_importance]

    # Convert to response format
    return [
        MemoryResponse(
            memory_id=m.memory_id,
            category=m.category,
            content=m.content,
            source=m.source,
            importance=m.importance,
            verified=m.verified,
            created_at=m.created_at.isoformat() if m.created_at else None,
            last_accessed=m.last_accessed.isoformat() if m.last_accessed else None,
            access_count=m.access_count,
            metadata=m.metadata
        )
        for m in memories
    ]


@app.get("/memory/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get a specific memory by ID."""
    verify_token(authorization)

    memory = memory_dal.get_memory(user_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

    return MemoryResponse(
        memory_id=memory.memory_id,
        category=memory.category,
        content=memory.content,
        source=memory.source,
        importance=memory.importance,
        verified=memory.verified,
        created_at=memory.created_at.isoformat() if memory.created_at else None,
        last_accessed=memory.last_accessed.isoformat() if memory.last_accessed else None,
        access_count=memory.access_count,
        metadata=memory.metadata
    )


@app.post("/memory/users/{user_id}", response_model=MemoryResponse)
async def create_memory(
    user_id: str,
    request: CreateMemoryRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a new memory for a user."""
    verify_token(authorization)

    try:
        memory = memory_dal.create_memory(
            user_id=user_id,
            category=request.category,
            content=request.content,
            source=request.source,
            importance=request.importance,
            verified=request.verified,
            metadata=request.metadata or {}
        )

        return MemoryResponse(
            memory_id=memory.memory_id,
            category=memory.category,
            content=memory.content,
            source=memory.source,
            importance=memory.importance,
            verified=memory.verified,
            created_at=memory.created_at.isoformat() if memory.created_at else None,
            last_accessed=memory.last_accessed.isoformat() if memory.last_accessed else None,
            access_count=memory.access_count,
            metadata=memory.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/memory/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    user_id: str,
    request: UpdateMemoryRequest,
    authorization: Optional[str] = Header(None)
):
    """Update an existing memory."""
    verify_token(authorization)

    memory = memory_dal.update_memory(
        user_id=user_id,
        memory_id=memory_id,
        category=request.category,
        content=request.content,
        importance=request.importance,
        verified=request.verified,
        metadata=request.metadata
    )

    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

    return MemoryResponse(
        memory_id=memory.memory_id,
        category=memory.category,
        content=memory.content,
        source=memory.source,
        importance=memory.importance,
        verified=memory.verified,
        created_at=memory.created_at.isoformat() if memory.created_at else None,
        last_accessed=memory.last_accessed.isoformat() if memory.last_accessed else None,
        access_count=memory.access_count,
        metadata=memory.metadata
    )


@app.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a memory."""
    verify_token(authorization)

    success = memory_dal.delete_memory(user_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

    return {
        "status": "success",
        "message": f"Memory {memory_id} deleted successfully"
    }


@app.get("/memory/users/{user_id}/context", response_model=ContextPreviewResponse)
async def get_context_preview(
    user_id: str,
    min_importance: int = 3,
    authorization: Optional[str] = Header(None)
):
    """Get a preview of what memories would be loaded into context."""
    verify_token(authorization)

    preview = memory_dal.get_context_preview(user_id, min_importance)
    return ContextPreviewResponse(**preview)


# User Testing Endpoints

class CreateTestUserRequest(BaseModel):
    starting_chapter: int = 1
    initial_memories: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None


class UserStateSummaryResponse(BaseModel):
    user_id: str
    type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str]
    profile: dict
    story_progress: dict
    memory_count: int
    device_count: int


class SetActiveUserRequest(BaseModel):
    user_id: str


@app.get("/users/test/list")
async def list_all_users_with_type(authorization: Optional[str] = Header(None)):
    """List all users with type information (production, test)."""
    verify_token(authorization)
    return user_testing_dal.list_all_users_with_type()


@app.post("/users/test")
async def create_test_user(
    request: CreateTestUserRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a new test user with optional initial state."""
    verify_token(authorization)

    try:
        user_data = user_testing_dal.create_test_user(
            starting_chapter=request.starting_chapter,
            initial_memories=request.initial_memories,
            tags=request.tags,
            user_id=request.user_id
        )

        return {
            "status": "success",
            "message": f"Test user {user_data['user_id']} created successfully",
            "user": user_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/state", response_model=UserStateSummaryResponse)
async def get_user_state_summary(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get comprehensive user state summary."""
    verify_token(authorization)

    try:
        summary = user_testing_dal.get_user_state_summary(user_id)
        return UserStateSummaryResponse(**summary)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/users/{user_id}")
async def delete_test_user(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a test user and all associated data."""
    verify_token(authorization)

    try:
        result = user_testing_dal.delete_test_user(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/{user_id}/export")
async def export_user_data(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Export complete user data for backup or analysis."""
    verify_token(authorization)

    try:
        export_data = user_testing_dal.export_user_data(user_id)
        return export_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Tool Call Endpoints

class ToolCallFilterRequest(BaseModel):
    """Query parameters for filtering tool calls"""
    tool_name: Optional[str] = None
    character: Optional[str] = None
    status: Optional[ToolCallStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@app.get("/tool-calls", response_model=List[ToolCallLog])
async def list_tool_calls(
    user_id: str,
    tool_name: Optional[str] = None,
    character: Optional[str] = None,
    status: Optional[ToolCallStatus] = None,
    limit: int = 100,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """List tool calls with optional filtering."""
    verify_token(authorization)

    filters = ToolCallFilter(
        user_id=user_id,
        tool_name=tool_name,
        character=character,
        status=status,
        limit=limit,
        offset=offset
    )

    tool_calls = tool_call_dal.get_tool_calls(user_id, filters)
    return tool_calls


@app.get("/tool-calls/stats", response_model=ToolCallStatistics)
async def get_tool_call_statistics(
    user_id: str,
    hours: Optional[int] = None,
    authorization: Optional[str] = Header(None)
):
    """Get aggregate statistics for tool calls."""
    verify_token(authorization)

    from datetime import timedelta
    time_range = timedelta(hours=hours) if hours else None
    stats = tool_call_dal.get_statistics(user_id, time_range)
    return stats


@app.get("/tool-calls/metadata/tools")
async def get_available_tools(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get list of all tool names that have been called."""
    verify_token(authorization)

    tool_names = tool_call_dal.get_all_tool_names(user_id)
    return {"tools": tool_names}


@app.get("/tool-calls/metadata/characters")
async def get_available_characters(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get list of all characters that have made tool calls."""
    verify_token(authorization)

    characters = tool_call_dal.get_all_characters(user_id)
    return {"characters": characters}


@app.get("/tool-calls/{call_id}", response_model=ToolCallLog)
async def get_tool_call_detail(
    call_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get detailed information about a specific tool call."""
    verify_token(authorization)

    tool_call = tool_call_dal.get_tool_call_by_id(user_id, call_id)
    if not tool_call:
        raise HTTPException(status_code=404, detail=f"Tool call {call_id} not found")

    return tool_call


# Character Endpoints

class CharacterSummary(BaseModel):
    id: str
    name: str
    nickname: Optional[str] = None
    role: str
    description: Optional[str] = None
    num_voice_modes: int
    num_capabilities: int
    has_story_arc: bool
    has_tool_instructions: bool


class VoiceModeResponse(BaseModel):
    id: str
    name: str
    triggers: List[str]
    characteristics: List[str]
    example_phrases: List[str]
    response_style: str


class VoiceModeSelectionResponse(BaseModel):
    mode: VoiceModeResponse
    confidence: float
    reasoning: Optional[str] = None


class SystemPromptRequest(BaseModel):
    voice_mode_id: Optional[str] = None
    user_id: Optional[str] = None  # For memory context


class SystemPromptResponse(BaseModel):
    character_id: str
    character_name: str
    prompt: str
    token_estimate: int


class PromptBreakdownResponse(BaseModel):
    character_id: str
    character_name: str
    sections: Dict[str, Dict[str, Any]]
    total_token_estimate: int


@app.get("/characters")
async def list_characters(authorization: Optional[str] = Header(None)):
    """List all available characters with summary info."""
    verify_token(authorization)

    characters = character_dal.list_characters()
    return {"characters": [CharacterSummary(**char) for char in characters]}


@app.get("/characters/{character_id}")
async def get_character(
    character_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get full character definition."""
    verify_token(authorization)

    character = character_dal.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    return character.dict()


@app.get("/characters/{character_id}/voice-modes")
async def get_character_voice_modes(
    character_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get all voice modes for a character."""
    verify_token(authorization)

    voice_modes = character_dal.get_voice_modes(character_id)
    if voice_modes is None:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    return {"voice_modes": [VoiceModeResponse(**mode.dict()) for mode in voice_modes]}


@app.post("/characters/{character_id}/test-voice-mode")
async def test_voice_mode_selection(
    character_id: str,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    authorization: Optional[str] = Header(None)
):
    """Test voice mode selection for given user input."""
    verify_token(authorization)

    selection = character_dal.test_voice_mode_selection(character_id, user_input, context)
    if selection is None:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    return VoiceModeSelectionResponse(
        mode=VoiceModeResponse(**selection.mode.dict()),
        confidence=selection.confidence,
        reasoning=selection.reasoning
    )


@app.post("/characters/{character_id}/system-prompt")
async def get_system_prompt(
    character_id: str,
    request: SystemPromptRequest,
    authorization: Optional[str] = Header(None)
):
    """Build system prompt for a character with optional user context."""
    verify_token(authorization)

    # Get memory context if user_id provided
    memory_context = None
    if request.user_id:
        try:
            memories = memory_dal.load_memories(request.user_id)
            # Group memories by category
            memory_context = {}
            for memory in memories:
                category = memory.category
                if category not in memory_context:
                    memory_context[category] = []
                memory_context[category].append(memory)
        except Exception as e:
            # User not found or no memories - continue without context
            pass

    prompt = character_dal.build_system_prompt(
        character_id,
        voice_mode_id=request.voice_mode_id,
        memory_context=memory_context
    )

    if prompt is None:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    character = character_dal.get_character(character_id)
    token_estimate = character_dal.count_prompt_tokens(prompt)

    return SystemPromptResponse(
        character_id=character_id,
        character_name=character.name,
        prompt=prompt,
        token_estimate=token_estimate
    )


@app.get("/characters/{character_id}/prompt-breakdown")
async def get_prompt_breakdown(
    character_id: str,
    voice_mode_id: Optional[str] = None,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Get detailed breakdown of system prompt sections with token counts."""
    verify_token(authorization)

    # Get memory context if user_id provided
    memory_context = None
    if user_id:
        try:
            memories = memory_dal.load_memories(user_id)
            # Group memories by category
            memory_context = {}
            for memory in memories:
                category = memory.category
                if category not in memory_context:
                    memory_context[category] = []
                memory_context[category].append(memory)
        except Exception as e:
            pass

    breakdown = character_dal.get_prompt_breakdown(
        character_id,
        voice_mode_id=voice_mode_id,
        memory_context=memory_context
    )

    if breakdown is None:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    return PromptBreakdownResponse(**breakdown)


@app.get("/characters/{character_id}/statistics")
async def get_character_statistics(
    character_id: str,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Get usage statistics for a character."""
    verify_token(authorization)

    stats = character_dal.get_character_statistics(character_id, user_id)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

    return stats


@app.get("/characters/{character_id}/tool-instructions")
async def get_character_tool_instructions(
    character_id: str,
    tool_name: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Get tool usage instructions for a character."""
    verify_token(authorization)

    instructions = character_dal.get_tool_instructions(character_id, tool_name)
    if instructions is None:
        raise HTTPException(
            status_code=404,
            detail=f"Character {character_id} not found or has no tool instructions"
        )

    return {"tool_instructions": instructions}


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Observability API starting...")
    print(f"📁 Data directory: {data_dir}")
    print(f"👥 Users found: {len(dal.list_users())}")
    print(f"👤 Characters found: {len(character_dal.list_characters())}")
    print("✅ Ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Observability API shutting down...")
