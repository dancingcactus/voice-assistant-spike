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


# Configuration
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "dev_token_12345")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# Find data directory
data_dir = Path(__file__).parent.parent.parent / "data"
project_root = Path(__file__).parent.parent.parent.parent

# Initialize FastAPI app
app = FastAPI(
    title="Hey Chat! Observability API",
    description="Debugging and testing tools for the voice assistant system",
    version="1.0.0"
)

# Configure CORS - must be before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize data access layers
dal = DataAccessLayer(data_dir=str(data_dir))
story_dal = StoryAccessLayer(project_root=str(project_root))
memory_dal = MemoryAccessor(data_dir=str(data_dir))
user_testing_dal = UserTestingAccessor(data_dir=str(data_dir))


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

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/api/v1/users", response_model=List[UserSummary])
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


@app.get("/api/v1/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, authorization: Optional[str] = Header(None)):
    """Get detailed user information."""
    verify_token(authorization)

    user_data = dal.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return UserDetailResponse(**user_data)


# Story Beat Endpoints

@app.get("/api/v1/story/chapters", response_model=List[ChapterSummary])
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


@app.get("/api/v1/story/chapters/{chapter_id}/beats", response_model=List[BeatSummary])
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


@app.get("/api/v1/story/chapters/{chapter_id}/beats/{beat_id}")
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


@app.get("/api/v1/story/users/{user_id}/progress", response_model=ChapterProgressSummary)
async def get_user_story_progress(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get user's current chapter progress summary."""
    verify_token(authorization)

    progress_summary = story_dal.get_user_chapter_progress_summary(user_id)
    return ChapterProgressSummary(**progress_summary)


@app.get("/api/v1/story/chapters/{chapter_id}/diagram")
async def get_chapter_diagram(
    chapter_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get Mermaid diagram for chapter beat flow."""
    verify_token(authorization)

    diagram = story_dal.generate_chapter_flow_diagram(chapter_id)
    return {
        "chapter_id": chapter_id,
        "diagram": diagram,
        "format": "mermaid"
    }


@app.post("/api/v1/story/users/{user_id}/beats/{beat_id}/trigger")
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


# Memory Endpoints

@app.get("/api/v1/memory/users/{user_id}", response_model=List[MemoryResponse])
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


@app.get("/api/v1/memory/{memory_id}", response_model=MemoryResponse)
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


@app.post("/api/v1/memory/users/{user_id}", response_model=MemoryResponse)
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


@app.put("/api/v1/memory/{memory_id}", response_model=MemoryResponse)
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


@app.delete("/api/v1/memory/{memory_id}")
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


@app.get("/api/v1/memory/users/{user_id}/context", response_model=ContextPreviewResponse)
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


@app.get("/api/v1/users/test/list")
async def list_all_users_with_type(authorization: Optional[str] = Header(None)):
    """List all users with type information (production, test)."""
    verify_token(authorization)
    return user_testing_dal.list_all_users_with_type()


@app.post("/api/v1/users/test")
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


@app.get("/api/v1/users/{user_id}/state", response_model=UserStateSummaryResponse)
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


@app.delete("/api/v1/users/{user_id}")
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


@app.post("/api/v1/users/{user_id}/export")
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


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Observability API starting...")
    print(f"📁 Data directory: {data_dir}")
    print(f"👥 Users found: {len(dal.list_users())}")
    print("✅ Ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Observability API shutting down...")
