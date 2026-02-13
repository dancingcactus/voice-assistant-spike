"""
Character Planning System for Phase 4.5 Milestone 2.

This module maps detected intents to character assignments and creates
execution plans for handling user queries. It orchestrates character
coordination, task decomposition, and handoff logic.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.intent import IntentResult, SubTask
from models.character_plan import (
    CharacterTask,
    CharacterPlan,
    ExecutionMode,
    PlanLog,
    CharacterName
)
from models.message import ConversationContext
from config.character_assignments import (
    get_character_for_intent,
    get_available_characters,
    get_character_assignments,
    DEFAULT_CHARACTER
)

logger = logging.getLogger(__name__)


class CharacterPlanner:
    """
    Creates character execution plans based on detected intents.
    
    Responsibilities:
    - Map intents to character assignments
    - Decompose multi-task queries
    - Determine handoff requirements
    - Calculate confidence scores and execution times
    - Handle fallback scenarios
    """
    
    def __init__(self, story_chapter_provider=None):
        """
        Initialize the Character Planner.
        
        Args:
            story_chapter_provider: Optional callable that returns (user_id) -> chapter_id
                                  If None, defaults to Chapter 1
        """
        self.story_chapter_provider = story_chapter_provider
        self.plan_count = 0
        logger.info("CharacterPlanner initialized")
    
    def _get_user_chapter(self, user_id: str) -> int:
        """
        Get the current story chapter for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Current chapter ID (defaults to 1 if provider not available)
        """
        if self.story_chapter_provider:
            try:
                return self.story_chapter_provider(user_id)
            except Exception as e:
                logger.warning(f"Failed to get chapter for user {user_id}: {e}")
        
        # Default to Chapter 1
        return 1
    
    def create_plan(
        self,
        intent_result: IntentResult,
        context: Optional[ConversationContext] = None,
        user_id: str = "default_user"
    ) -> CharacterPlan:
        """
        Create a character execution plan for an intent.
        
        Args:
            intent_result: The detected intent with confidence and metadata
            context: Optional conversation context
            user_id: User identifier for chapter-based character availability
            
        Returns:
            CharacterPlan with tasks, execution mode, and metadata
        """
        start_time = time.time()
        
        # Get user's current chapter
        chapter_id = self._get_user_chapter(user_id)
        available_characters = get_available_characters(chapter_id)
        
        logger.info(
            f"Creating plan for intent '{intent_result.intent}' "
            f"(confidence: {intent_result.confidence:.2f}, chapter: {chapter_id})"
        )
        
        # Handle multi-task queries
        if intent_result.intent == "multi_task" and intent_result.sub_tasks:
            plan = self._create_multi_task_plan(
                intent_result,
                chapter_id,
                available_characters
            )
        else:
            # Single intent query
            plan = self._create_single_task_plan(
                intent_result,
                chapter_id,
                available_characters
            )
        
        # Add planning metadata
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        plan.metadata["processing_time_ms"] = processing_time
        plan.metadata["chapter_id"] = chapter_id
        plan.metadata["available_characters"] = available_characters
        plan.metadata["plan_number"] = self.plan_count
        
        self.plan_count += 1
        
        logger.info(
            f"✅ Plan created: {len(plan.tasks)} task(s), "
            f"mode={plan.execution_mode.value}, "
            f"confidence={plan.total_confidence:.2f}, "
            f"time={processing_time:.1f}ms"
        )
        
        return plan
    
    def _create_single_task_plan(
        self,
        intent_result: IntentResult,
        chapter_id: int,
        available_characters: List[str]
    ) -> CharacterPlan:
        """
        Create a plan for a single-intent query.
        
        Args:
            intent_result: The detected intent
            chapter_id: Current story chapter
            available_characters: List of available character names
            
        Returns:
            CharacterPlan with a single task
        """
        # Determine which character should handle this intent
        character_name = get_character_for_intent(
            intent_result.intent,
            chapter_id,
            intent_result.confidence
        )
        
        # Ensure character is available
        if character_name not in available_characters:
            logger.warning(
                f"Assigned character '{character_name}' not available in chapter {chapter_id}, "
                f"falling back to '{DEFAULT_CHARACTER}'"
            )
            character_name = DEFAULT_CHARACTER
        
        # Cast to CharacterName type for type safety
        character: CharacterName = character_name  # type: ignore
        
        # Create single task
        task = CharacterTask(
            character=character,
            task_description=f"Handle {intent_result.intent} query",
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            requires_handoff=False,
            handoff_from=None,
            estimated_duration_ms=self._estimate_duration(intent_result.intent),
            metadata={
                "classification_method": intent_result.classification_method
            }
        )
        
        # Create plan
        plan = CharacterPlan(
            tasks=[task],
            execution_mode=ExecutionMode.SINGLE,
            total_confidence=intent_result.confidence,
            estimated_total_duration_ms=task.estimated_duration_ms,
            metadata={
                "intent": intent_result.intent,
                "classification_method": intent_result.classification_method
            }
        )
        
        return plan
    
    def _create_multi_task_plan(
        self,
        intent_result: IntentResult,
        chapter_id: int,
        available_characters: List[str]
    ) -> CharacterPlan:
        """
        Create a plan for a multi-task query.
        
        Decomposes the query into sub-tasks and assigns characters.
        Determines handoff requirements between characters.
        
        Args:
            intent_result: The intent result with sub_tasks
            chapter_id: Current story chapter
            available_characters: List of available character names
            
        Returns:
            CharacterPlan with multiple sequential tasks
        """
        if not intent_result.sub_tasks:
            logger.error("Multi-task intent has no sub_tasks, falling back to single task")
            return self._create_single_task_plan(intent_result, chapter_id, available_characters)
        
        tasks: List[CharacterTask] = []
        prev_character: Optional[CharacterName] = None
        total_confidence = 0.0
        total_duration = 0
        
        for i, sub_task in enumerate(intent_result.sub_tasks):
            # Determine character for this sub-task
            character_name = get_character_for_intent(
                sub_task.intent,
                chapter_id,
                sub_task.confidence
            )
            
            # Ensure character is available
            if character_name not in available_characters:
                logger.warning(
                    f"Sub-task character '{character_name}' not available, "
                    f"falling back to '{DEFAULT_CHARACTER}'"
                )
                character_name = DEFAULT_CHARACTER
            
            # Cast to CharacterName type for type safety
            character: CharacterName = character_name  # type: ignore
            
            # Determine if handoff is needed
            requires_handoff = (i > 0 and prev_character is not None and 
                              character != prev_character)
            
            # Create task
            task = CharacterTask(
                character=character,
                task_description=sub_task.text,
                intent=sub_task.intent,
                confidence=sub_task.confidence,
                requires_handoff=requires_handoff,
                handoff_from=prev_character if requires_handoff else None,
                estimated_duration_ms=self._estimate_duration(sub_task.intent),
                metadata={
                    "sub_task_index": i,
                    "sub_task_text": sub_task.text
                }
            )
            
            tasks.append(task)
            total_confidence += sub_task.confidence
            total_duration += task.estimated_duration_ms
            prev_character = character
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(tasks) if tasks else 0.0
        
        # Add extra time for handoffs
        handoff_count = sum(1 for task in tasks if task.requires_handoff)
        handoff_overhead = handoff_count * 500  # 500ms per handoff
        total_duration += handoff_overhead
        
        # Determine execution mode
        unique_characters = set(task.character for task in tasks)
        if len(unique_characters) == 1:
            execution_mode = ExecutionMode.SINGLE
        else:
            execution_mode = ExecutionMode.SEQUENTIAL
        
        # Create plan
        plan = CharacterPlan(
            tasks=tasks,
            execution_mode=execution_mode,
            total_confidence=avg_confidence,
            estimated_total_duration_ms=total_duration,
            metadata={
                "intent": "multi_task",
                "sub_task_count": len(tasks),
                "unique_characters": list(unique_characters),
                "handoff_count": handoff_count,
                "classification_method": intent_result.classification_method
            }
        )
        
        return plan
    
    def _estimate_duration(self, intent: str) -> int:
        """
        Estimate execution time for an intent in milliseconds.
        
        Args:
            intent: Intent category
            
        Returns:
            Estimated duration in milliseconds
        """
        # Base durations by intent type
        durations = {
            "cooking": 2000,      # Recipes can be complex
            "household": 1500,    # Lists, calendar, tasks
            "smart_home": 1000,   # Device control is quick
            "general": 1500,      # Varies widely
            "multi_task": 2000    # Usually more complex
        }
        
        return durations.get(intent, 1500)
    
    def create_plan_log(
        self,
        query: str,
        user_id: str,
        intent_result: IntentResult,
        character_plan: CharacterPlan,
        processing_time_ms: float
    ) -> PlanLog:
        """
        Create a log entry for a planning operation.
        
        Args:
            query: Original user query
            user_id: User identifier
            intent_result: Detected intent
            character_plan: Generated plan
            processing_time_ms: Time taken to create plan
            
        Returns:
            PlanLog for observability
        """
        chapter_id = self._get_user_chapter(user_id)
        
        return PlanLog(
            timestamp=datetime.now(),
            user_id=user_id,
            query=query,
            intent_category=intent_result.intent,
            character_plan=character_plan,
            processing_time_ms=processing_time_ms,
            current_chapter=f"chapter_{chapter_id}",
            metadata={
                "intent_confidence": intent_result.confidence,
                "classification_method": intent_result.classification_method
            }
        )
