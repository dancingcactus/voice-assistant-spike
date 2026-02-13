"""
Debug API endpoints for Phase 4.5 development and testing.

These endpoints are for development/testing only and should not be exposed in production.
"""

import time
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.intent_detector import IntentDetector
from core.character_planner import CharacterPlanner
from core.coordination_tracker import CoordinationTracker
from core.memory_manager import MemoryManager
from integrations.llm_integration import LLMIntegration
from models.intent import IntentResult
from models.character_plan import CharacterPlan
from models.coordination import CoordinationEvent, CoordinationMetrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])

# Global instances (initialized on first request)
_intent_detector: Optional[IntentDetector] = None
_character_planner: Optional[CharacterPlanner] = None
_coordination_tracker: Optional[CoordinationTracker] = None
_memory_manager: Optional[MemoryManager] = None


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
            # For now, CharacterPlanner defaults to Chapter 1 without story engine
            # In production, this would be connected to the actual StoryEngine
            _character_planner = CharacterPlanner(story_chapter_provider=None)
            logger.info("CharacterPlanner initialized successfully")
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
