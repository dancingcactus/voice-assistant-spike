"""
Coordination tracking system for Phase 4.5 Milestone 4.

This module tracks multi-character coordination events, calculates metrics,
and manages progression toward coordination milestones. Events are stored
in user state and exposed via API endpoints for observability.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from models.coordination import (
    CoordinationEvent,
    CoordinationMetrics,
    CoordinationMilestones,
    CoordinationHistory
)

logger = logging.getLogger(__name__)


class CoordinationTracker:
    """
    Tracks and analyzes multi-character coordination events.
    
    Responsibilities:
    - Log coordination events (handoffs, multi-task, sign-ups)
    - Calculate aggregated metrics
    - Detect milestone achievements
    - Persist coordination history to user state
    - Provide data for observability dashboard
    """
    
    def __init__(self, memory_manager=None):
        """
        Initialize the Coordination Tracker.
        
        Args:
            memory_manager: MemoryManager instance for accessing user state
        """
        self.memory_manager = memory_manager
        
    def log_event(self, event: CoordinationEvent) -> None:
        """
        Log a coordination event and update metrics/milestones.
        
        Args:
            event: CoordinationEvent to log
        """
        if not self.memory_manager:
            logger.warning("No memory manager available, event not persisted")
            return
            
        try:
            # Load user state
            user_state = self.memory_manager.load_user_state(event.user_id)
            
            # Get or create coordination history
            if not hasattr(user_state, 'coordination_history') or user_state.coordination_history is None:
                from models.coordination import CoordinationHistory
                user_state.coordination_history = CoordinationHistory()
            
            history = user_state.coordination_history
            
            # Add event
            history.events.append(event)
            
            # Update metrics
            history.metrics = self._calculate_metrics(history.events)
            
            # Update milestones
            history.milestones = self._check_milestones(history)
            
            # Save user state
            self.memory_manager.save_user_state(event.user_id, force=False)
            
            logger.info(f"Logged {event.event_type} event for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error logging coordination event: {e}", exc_info=True)
    
    def log_handoff(
        self,
        user_id: str,
        from_character: str,
        to_character: str,
        intent: str,
        template_used: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a handoff event between characters.
        
        Args:
            user_id: User identifier
            from_character: Character initiating handoff
            to_character: Character receiving handoff
            intent: Intent type that triggered handoff
            template_used: Template identifier used for handoff
            success: Whether handoff completed successfully
            metadata: Additional context
        """
        event = CoordinationEvent(
            event_type="handoff",
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            from_character=from_character,
            to_character=to_character,
            intent=intent,
            template_used=template_used,
            success=success,
            metadata=metadata or {}
        )
        self.log_event(event)
    
    def log_multi_task(
        self,
        user_id: str,
        query: str,
        characters_involved: List[str],
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a multi-task completion event.
        
        Args:
            user_id: User identifier
            query: Original user query
            characters_involved: List of characters who participated
            success: Whether multi-task completed successfully
            metadata: Additional context
        """
        event = CoordinationEvent(
            event_type="multi_task",
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            success=success,
            metadata={
                **(metadata or {}),
                "query": query,
                "characters_involved": characters_involved
            }
        )
        self.log_event(event)
    
    def log_sign_up(
        self,
        user_id: str,
        characters: List[str],
        intents: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a sign-up pattern (characters claiming work).
        
        Args:
            user_id: User identifier
            characters: Characters who signed up
            intents: Intents claimed by each character
            metadata: Additional context
        """
        event = CoordinationEvent(
            event_type="sign_up",
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            success=True,
            metadata={
                **(metadata or {}),
                "characters": characters,
                "intents": intents
            }
        )
        self.log_event(event)
    
    def get_metrics(self, user_id: str) -> CoordinationMetrics:
        """
        Get aggregated coordination metrics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            CoordinationMetrics with calculated statistics
        """
        if not self.memory_manager:
            return CoordinationMetrics()
            
        try:
            user_state = self.memory_manager.load_user_state(user_id)
            
            if not hasattr(user_state, 'coordination_history') or user_state.coordination_history is None:
                from models.coordination import CoordinationHistory
                user_state.coordination_history = CoordinationHistory()
            
            return user_state.coordination_history.metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return CoordinationMetrics()
    
    def get_recent_events(
        self,
        user_id: str,
        limit: int = 10,
        event_type: Optional[str] = None
    ) -> List[CoordinationEvent]:
        """
        Get recent coordination events for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            event_type: Optional filter by event type
            
        Returns:
            List of recent CoordinationEvents
        """
        if not self.memory_manager:
            return []
            
        try:
            user_state = self.memory_manager.load_user_state(user_id)
            
            if not hasattr(user_state, 'coordination_history') or user_state.coordination_history is None:
                from models.coordination import CoordinationHistory
                user_state.coordination_history = CoordinationHistory()
            
            events = user_state.coordination_history.events
            
            # Filter by type if specified
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            # Return most recent events
            return list(reversed(events[-limit:]))
            
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []
    
    def get_milestones(self, user_id: str) -> Dict[str, bool]:
        """
        Get coordination milestone status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of milestone names to completion status
        """
        if not self.memory_manager:
            return {}
            
        try:
            user_state = self.memory_manager.load_user_state(user_id)
            
            if not hasattr(user_state, 'coordination_history') or user_state.coordination_history is None:
                from models.coordination import CoordinationHistory
                user_state.coordination_history = CoordinationHistory()
            
            return user_state.coordination_history.milestones.model_dump()
            
        except Exception as e:
            logger.error(f"Error getting milestones: {e}")
            return {}
    
    def _calculate_metrics(self, events: List[CoordinationEvent]) -> CoordinationMetrics:
        """
        Calculate coordination metrics from event history.
        
        Args:
            events: List of coordination events
            
        Returns:
            Calculated CoordinationMetrics
        """
        metrics = CoordinationMetrics()
        
        if not events:
            return metrics
        
        handoff_events = [e for e in events if e.event_type == "handoff"]
        multi_task_events = [e for e in events if e.event_type == "multi_task"]
        sign_up_events = [e for e in events if e.event_type == "sign_up"]
        
        # Count handoffs
        metrics.total_handoffs = len(handoff_events)
        
        # Calculate success rate
        if handoff_events:
            successful = len([e for e in handoff_events if e.success])
            metrics.handoff_success_rate = successful / len(handoff_events)
        
        # Count directional handoffs
        for event in handoff_events:
            if event.from_character == "delilah" and event.to_character == "hank":
                metrics.delilah_to_hank_count += 1
            elif event.from_character == "hank" and event.to_character == "delilah":
                metrics.hank_to_delilah_count += 1
        
        # Count multi-task completions
        metrics.multi_task_completions = len(multi_task_events)
        
        # Count sign-up patterns
        metrics.sign_up_pattern_count = len(sign_up_events)
        
        # Track template usage
        template_usage = {}
        for event in handoff_events:
            if event.template_used:
                template_usage[event.template_used] = template_usage.get(event.template_used, 0) + 1
        metrics.template_usage = template_usage
        
        # Calculate average latency (if available in metadata)
        latencies = []
        for event in handoff_events:
            if "latency_ms" in event.metadata:
                latencies.append(event.metadata["latency_ms"])
        if latencies:
            metrics.average_handoff_latency_ms = sum(latencies) / len(latencies)
        
        return metrics
    
    def _check_milestones(self, history: CoordinationHistory) -> CoordinationMilestones:
        """
        Check and update coordination milestones.
        
        Args:
            history: Current coordination history
            
        Returns:
            Updated CoordinationMilestones
        """
        milestones = history.milestones
        metrics = history.metrics
        events = history.events
        
        # First handoff
        if not milestones.first_handoff and metrics.total_handoffs >= 1:
            milestones.first_handoff = True
            logger.info("Milestone achieved: first_handoff")
        
        # First multi-task
        if not milestones.first_multi_task and metrics.multi_task_completions >= 1:
            milestones.first_multi_task = True
            logger.info("Milestone achieved: first_multi_task")
        
        # First sign-up
        if not milestones.first_sign_up and metrics.sign_up_pattern_count >= 1:
            milestones.first_sign_up = True
            logger.info("Milestone achieved: first_sign_up")
        
        # Five handoffs
        if not milestones.five_handoffs and metrics.total_handoffs >= 5:
            milestones.five_handoffs = True
            logger.info("Milestone achieved: five_handoffs")
        
        # All templates used (assuming 24 different templates as per Milestone 3)
        # This checks if all the main templates have been used at least once
        if not milestones.all_templates_used:
            unique_templates = len(metrics.template_usage)
            # We'll be lenient and consider it achieved if most templates used (>= 20)
            if unique_templates >= 20:
                milestones.all_templates_used = True
                logger.info("Milestone achieved: all_templates_used")
        
        return milestones
