"""
Debug API endpoints for Phase 4.5 / Phase 5.1 development and testing.

These endpoints are for development/testing only and should not be exposed in production.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.intent_detector import IntentDetector
from core.character_planner import CharacterPlanner
from core.coordination_tracker import CoordinationTracker
from core.memory_manager import MemoryManager
from core.turn_classifier import TurnClassifier
from core.conversation_router import ConversationRouter
from core.conversation_state import ConversationStateManager
from integrations.llm_integration import LLMIntegration
from models.intent import IntentResult
from models.character_plan import CharacterPlan
from models.coordination import CoordinationEvent, CoordinationMetrics
from models.message import ConversationContext
from config.character_assignments import get_available_characters

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])

# Global instances (initialized on first request)
_intent_detector: Optional[IntentDetector] = None
_character_planner: Optional[CharacterPlanner] = None
_coordination_tracker: Optional[CoordinationTracker] = None
_memory_manager: Optional[MemoryManager] = None
_turn_classifier: Optional[TurnClassifier] = None
_conversation_router: Optional[ConversationRouter] = None
_state_manager: ConversationStateManager = ConversationStateManager()


def get_intent_detector() -> IntentDetector:
    """Get or create the global IntentDetector instance."""
    global _intent_detector
    if _intent_detector is None:
        try:
            llm = LLMIntegration()
            _intent_detector = IntentDetector(llm=llm)
            logger.info("IntentDetector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize IntentDetector: {e}")
            # Create detector without LLM as fallback
            _intent_detector = IntentDetector(llm=None)
            logger.warning("IntentDetector initialized without LLM support")
    return _intent_detector


def get_character_planner() -> CharacterPlanner:
    """Get or create the global CharacterPlanner instance."""
    global _character_planner
    if _character_planner is None:
        try:
            # Create story chapter provider that looks up user's actual chapter
            memory_manager = get_memory_manager()
            
            def get_user_chapter(user_id: str) -> int:
                """Get the current chapter for a user from their story progress."""
                try:
                    user_state = memory_manager.load_user_state(user_id)
                    return user_state.story_progress.current_chapter
                except Exception as e:
                    logger.warning(f"Failed to get chapter for user {user_id}: {e}")
                    return 1  # Default to Chapter 1
            
            _character_planner = CharacterPlanner(story_chapter_provider=get_user_chapter)
            logger.info("CharacterPlanner initialized successfully with story chapter provider")
        except Exception as e:
            logger.error(f"Failed to initialize CharacterPlanner: {e}")
            raise
    return _character_planner


def get_memory_manager() -> MemoryManager:
    """Get or create the global MemoryManager instance."""
    global _memory_manager
    if _memory_manager is None:
        try:
            _memory_manager = MemoryManager()
            logger.info("MemoryManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryManager: {e}")
            raise
    return _memory_manager


def get_coordination_tracker() -> CoordinationTracker:
    """Get or create the global CoordinationTracker instance."""
    global _coordination_tracker
    if _coordination_tracker is None:
        try:
            memory_manager = get_memory_manager()
            _coordination_tracker = CoordinationTracker(memory_manager=memory_manager)
            logger.info("CoordinationTracker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CoordinationTracker: {e}")
            raise
    return _coordination_tracker


def get_turn_classifier() -> TurnClassifier:
    """Get or create the global TurnClassifier instance."""
    global _turn_classifier
    if _turn_classifier is None:
        try:
            llm = LLMIntegration()
            _turn_classifier = TurnClassifier(llm=llm)
            logger.info("TurnClassifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TurnClassifier: {e}")
            raise
    return _turn_classifier


def get_conversation_router() -> ConversationRouter:
    """Get or create the global ConversationRouter instance."""
    global _conversation_router
    if _conversation_router is None:
        try:
            llm = LLMIntegration()
            _conversation_router = ConversationRouter(llm=llm)
            logger.info("ConversationRouter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationRouter: {e}")
            raise
    return _conversation_router


# Request/Response models
class DetectIntentRequest(BaseModel):
    """Request to detect intent of a query."""
    query: str = Field(..., description="User query to classify", min_length=1)
    user_id: str = Field(default="debug_user", description="User ID for context")


class DetectIntentResponse(BaseModel):
    """Response containing intent detection results."""
    query: str = Field(..., description="Original query")
    intent_result: dict = Field(..., description="Intent detection result")
    classification_method: str = Field(..., description="Method used for classification")
    processing_time_ms: int = Field(..., description="Time taken to classify (milliseconds)")
    detector_stats: dict = Field(..., description="Intent detector statistics")


@router.post("/detect-intent", response_model=DetectIntentResponse)
async def detect_intent(request: DetectIntentRequest) -> DetectIntentResponse:
    """
    Detect the intent of a query without executing it.
    
    This endpoint is for testing and debugging intent detection.
    It classifies the query but does not trigger any character responses.
    
    Args:
        request: DetectIntentRequest with query and user_id
        
    Returns:
        DetectIntentResponse with intent classification results
        
    Raises:
        HTTPException: If intent detection fails
    """
    try:
        detector = get_intent_detector()
        
        # Measure processing time
        start_time = time.time()
        
        # Detect intent (no context for debug endpoint)
        intent_result = detector.detect(query=request.query, context=None)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Intent detected for query '{request.query}': "
            f"{intent_result.intent} (confidence: {intent_result.confidence:.2f}, "
            f"method: {intent_result.classification_method}, "
            f"time: {processing_time_ms}ms)"
        )
        
        # Get detector statistics
        detector_stats = detector.get_statistics()
        
        return DetectIntentResponse(
            query=request.query,
            intent_result=intent_result.to_dict(),
            classification_method=intent_result.classification_method,
            processing_time_ms=processing_time_ms,
            detector_stats=detector_stats
        )
        
    except Exception as e:
        logger.error(f"Intent detection failed for query '{request.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Intent detection failed: {str(e)}"
        )


@router.get("/intent-stats")
async def get_intent_stats():
    """
    Get statistics about the intent detection system.
    
    Returns:
        Dictionary with intent detector statistics
    """
    try:
        detector = get_intent_detector()
        stats = detector.get_statistics()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get intent stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


# ============================================================================
# Character Planning Endpoints (Milestone 2)
# ============================================================================

class CreatePlanRequest(BaseModel):
    """Request to create a character plan for a query."""
    query: str = Field(..., description="User query to plan for", min_length=1)
    user_id: str = Field(default="debug_user", description="User ID for chapter context")


class CreatePlanResponse(BaseModel):
    """Response containing character plan results."""
    query: str = Field(..., description="Original query")
    intent_result: dict = Field(..., description="Detected intent")
    character_plan: dict = Field(..., description="Generated character plan")
    estimated_execution_time_ms: int = Field(..., description="Total estimated execution time")
    processing_time_ms: float = Field(..., description="Time to create plan (milliseconds)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


@router.post("/create-plan", response_model=CreatePlanResponse)
async def create_plan(request: CreatePlanRequest) -> CreatePlanResponse:
    """
    Create a character execution plan for a query.
    
    This endpoint tests the full intent detection → character planning pipeline
    without executing the plan. It's useful for debugging character assignments
    and task decomposition.
    
    Args:
        request: CreatePlanRequest with query and user_id
        
    Returns:
        CreatePlanResponse with intent detection and character plan
        
    Raises:
        HTTPException: If planning fails
    """
    try:
        # Get system components
        detector = get_intent_detector()
        planner = get_character_planner()
        
        # Measure total processing time
        start_time = time.time()
        
        # Step 1: Detect intent
        intent_detection_start = time.time()
        intent_result = detector.detect(query=request.query, context=None)
        intent_detection_time = (time.time() - intent_detection_start) * 1000
        
        # Step 2: Create character plan
        planning_start = time.time()
        character_plan = planner.create_plan(
            intent_result=intent_result,
            context=None,
            user_id=request.user_id
        )
        planning_time = (time.time() - planning_start) * 1000
        
        total_processing_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Plan created for query '{request.query}': "
            f"intent={intent_result.intent}, "
            f"tasks={len(character_plan.tasks)}, "
            f"mode={character_plan.execution_mode.value}, "
            f"time={total_processing_time:.1f}ms"
        )
        
        # Build response
        return CreatePlanResponse(
            query=request.query,
            intent_result=intent_result.to_dict(),
            character_plan=character_plan.to_dict(),
            estimated_execution_time_ms=character_plan.estimated_total_duration_ms,
            processing_time_ms=total_processing_time,
            metadata={
                "intent_detection_time_ms": intent_detection_time,
                "planning_time_ms": planning_time,
                "chapter_id": character_plan.metadata.get("chapter_id", 1),
                "available_characters": character_plan.metadata.get("available_characters", []),
                "classification_method": intent_result.classification_method
            }
        )
        
    except Exception as e:
        logger.error(f"Character planning failed for query '{request.query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Character planning failed: {str(e)}"
        )


# ==================== Coordination Tracking Endpoints ====================

class CoordinationMetricsResponse(BaseModel):
    """Response containing coordination metrics for a user."""
    user_id: str
    metrics: dict = Field(..., description="Coordination metrics")


class CoordinationEventsResponse(BaseModel):
    """Response containing recent coordination events."""
    user_id: str
    events: List[dict] = Field(..., description="List of coordination events")
    total_count: int = Field(..., description="Total number of events returned")


class CoordinationMilestonesResponse(BaseModel):
    """Response containing coordination milestone status."""
    user_id: str
    milestones: dict = Field(..., description="Milestone completion status")


@router.get("/coordination/metrics/{user_id}", response_model=CoordinationMetricsResponse)
async def get_coordination_metrics(user_id: str) -> CoordinationMetricsResponse:
    """
    Get aggregated coordination metrics for a user.
    
    Returns statistics on handoffs, multi-task completions, character
    interactions, and template usage patterns.
    
    Args:
        user_id: User identifier
        
    Returns:
        CoordinationMetricsResponse with calculated metrics
    """
    try:
        tracker = get_coordination_tracker()
        metrics = tracker.get_metrics(user_id)
        
        logger.info(f"Retrieved coordination metrics for user {user_id}")
        
        return CoordinationMetricsResponse(
            user_id=user_id,
            metrics=metrics.model_dump()
        )
        
    except Exception as e:
        logger.error(f"Failed to get coordination metrics for {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve coordination metrics: {str(e)}"
        )


@router.get("/coordination/events/{user_id}", response_model=CoordinationEventsResponse)
async def get_coordination_events(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Maximum events to return"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type")
) -> CoordinationEventsResponse:
    """
    Get recent coordination events for a user.
    
    Returns a list of recent coordination events, optionally filtered by type.
    Events are returned in reverse chronological order (most recent first).
    
    Args:
        user_id: User identifier
        limit: Maximum number of events to return (1-100)
        event_type: Optional filter (handoff, multi_task, sign_up)
        
    Returns:
        CoordinationEventsResponse with event list
    """
    try:
        tracker = get_coordination_tracker()
        events = tracker.get_recent_events(
            user_id=user_id,
            limit=limit,
            event_type=event_type
        )
        
        logger.info(
            f"Retrieved {len(events)} coordination events for user {user_id} "
            f"(limit={limit}, type={event_type})"
        )
        
        return CoordinationEventsResponse(
            user_id=user_id,
            events=[e.model_dump() for e in events],
            total_count=len(events)
        )
        
    except Exception as e:
        logger.error(f"Failed to get coordination events for {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve coordination events: {str(e)}"
        )


@router.get("/coordination/milestones/{user_id}", response_model=CoordinationMilestonesResponse)
async def get_coordination_milestones(user_id: str) -> CoordinationMilestonesResponse:
    """
    Get coordination milestone status for a user.
    
    Returns the completion status of various coordination milestones,
    such as first handoff, five handoffs completed, etc.
    
    Args:
        user_id: User identifier
        
    Returns:
        CoordinationMilestonesResponse with milestone status
    """
    try:
        tracker = get_coordination_tracker()
        milestones = tracker.get_milestones(user_id)
        
        logger.info(f"Retrieved coordination milestones for user {user_id}")
        
        return CoordinationMilestonesResponse(
            user_id=user_id,
            milestones=milestones
        )
        
    except Exception as e:
        logger.error(f"Failed to get coordination milestones for {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve coordination milestones: {str(e)}"
        )


# ============================================================================
# Phase 5.1 Routing Debug Endpoints (Milestone 2)
# ============================================================================


class HistoryMessage(BaseModel):
    """A single history message for router/classifier testing."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class TestRouterRequest(BaseModel):
    """
    Request body for the test-router endpoint.

    Simulates a user message arriving with a given conversation history so
    that the TurnClassifier and ConversationRouter can be exercised without
    needing a live conversation session.
    """
    user_id: str = Field(default="debug_user", description="User ID (for chapter lookup)")
    message: str = Field(..., description="Latest user message to route", min_length=1)
    history: List[HistoryMessage] = Field(
        default_factory=list,
        description="Recent conversation history (last few turns)",
    )
    chapter_id: int = Field(
        default=2,
        ge=1,
        description="Story chapter to use for available characters and handoff pairs",
    )


class TestRouterResponse(BaseModel):
    """Response from the test-router endpoint."""
    routing_decision: Dict[str, Any] = Field(..., description="RoutingDecision as dict")
    turn_classification: Optional[Dict[str, Any]] = Field(
        default=None,
        description="TurnClassification (only present when coordination_state is non-IDLE)",
    )
    available_characters: List[str] = Field(..., description="Characters active for this chapter")
    processing_time_ms: float = Field(..., description="Total time taken (milliseconds)")


@router.post("/test-router", response_model=TestRouterResponse)
async def test_router(request: TestRouterRequest) -> TestRouterResponse:
    """
    Exercise the ConversationRouter (and optionally TurnClassifier) without a live session.

    Useful for debugging routing decisions and verifying that character assignments
    and pending-followup logic behave correctly for a given conversation.

    The TurnClassifier is called only when ``coordination_state`` is non-IDLE.
    For this debug endpoint the coordination state is always IDLE (no pending context),
    so only the ConversationRouter runs.
    """
    try:
        conv_router = get_conversation_router()

        available_chars = get_available_characters(request.chapter_id)
        history = [{"role": m.role, "content": m.content} for m in request.history]

        start_time = time.time()

        decision = conv_router.route(
            user_message=request.message,
            recent_history=history,
            available_characters=available_chars,
            chapter_id=request.chapter_id,
        )

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            "test-router: message=%r → primary=%s, followup=%s (%.1f ms)",
            request.message,
            decision.primary_character,
            decision.pending_followup.character if decision.pending_followup else None,
            elapsed_ms,
        )

        return TestRouterResponse(
            routing_decision=decision.to_dict(),
            turn_classification=None,
            available_characters=available_chars,
            processing_time_ms=elapsed_ms,
        )

    except Exception as exc:
        logger.error("test-router failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Router test failed: {exc}")


class CoordinationStateResponse(BaseModel):
    """Response for the coordination-state endpoint."""
    user_id: str
    coordination_state: Dict[str, Any] = Field(
        ..., description="Current CoordinationState as dict (IDLE when no active session)"
    )
    note: str = Field(
        default="",
        description="Advisory message (e.g. no active session found)",
    )


@router.get("/coordination-state/{user_id}", response_model=CoordinationStateResponse)
async def get_coordination_state(user_id: str) -> CoordinationStateResponse:
    """
    Return the current coordination state for *user_id*.

    Reads the in-memory ``ConversationContext.metadata`` for the user's active
    session via the shared ``ConversationManager`` reference when available,
    and otherwise returns an IDLE placeholder.

    This endpoint is primarily useful for debugging multi-turn handoff scenarios
    via ``GET /api/debug/coordination-state/{user_id}`` to inspect whether the
    system is currently in PROPOSING or AWAITING_ACTION mode.
    """
    try:
        # Attempt to load from ConversationManager if accessible
        # (the manager lives in the websocket router; import lazily to avoid circular imports)
        try:
            from api.websocket import conversation_manager

            ctx = conversation_manager.conversations.get(user_id)
            if ctx is None:
                # Try with user_id as session_id (common in debug usage)
                ctx = ConversationContext(session_id=user_id, user_id=user_id)
                note = f"No active session for '{user_id}'; returning IDLE placeholder"
            else:
                note = ""
        except Exception:
            ctx = ConversationContext(session_id=user_id, user_id=user_id)
            note = "ConversationManager unavailable; returning IDLE placeholder"

        state = _state_manager.get_state(ctx)

        logger.info("coordination-state: user=%s mode=%s", user_id, state.mode.value)

        return CoordinationStateResponse(
            user_id=user_id,
            coordination_state=state.to_dict(),
            note=note,
        )

    except Exception as exc:
        logger.error("coordination-state lookup failed for %s: %s", user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve coordination state: {exc}"
        )
