"""
Debug API endpoints for Phase 4.5 development and testing.

These endpoints are for development/testing only and should not be exposed in production.
"""

import time
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intent_detector import IntentDetector
from integrations.llm_integration import LLMIntegration
from models.intent import IntentResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])

# Global intent detector instance (initialized on first request)
_intent_detector: Optional[IntentDetector] = None


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
