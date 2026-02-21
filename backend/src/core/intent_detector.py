"""
Intent Detection System for Phase 4.5.

This module provides intelligent query classification to determine user intent
and route queries to appropriate characters. Supports both rule-based (fast)
and LLM-based (accurate) classification methods.
"""

import json
import re
import time
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

from models.intent import IntentResult, SubTask, IntentCategory, ClassificationMethod
from models.message import ConversationContext
from integrations.llm_integration import LLMIntegration

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects user intent from queries using rule-based and LLM-based classification.
    
    Classification Strategy:
    1. Rule-based fast path for clear, simple queries
    2. LLM-assisted classification for complex or ambiguous queries
    3. Multi-task detection and decomposition
    """
    
    def __init__(self, patterns_path: Optional[str] = None, llm: Optional[LLMIntegration] = None):
        """
        Initialize the Intent Detector.
        
        Args:
            patterns_path: Path to intent_patterns.json config file
            llm: LLM integration instance for complex classification
        """
        if patterns_path is None:
            # Default: backend/src/config/intent_patterns.json
            config_dir = Path(__file__).parent.parent / "config"
            patterns_path = config_dir / "intent_patterns.json"
        
        self.patterns_path = Path(patterns_path)
        self.patterns: Dict[str, Any] = {}
        self.llm = llm
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load intent patterns from configuration file."""
        if not self.patterns_path.exists():
            logger.error(f"Intent patterns file not found: {self.patterns_path}")
            self.patterns = {}
            return
        
        try:
            with open(self.patterns_path, "r") as f:
                self.patterns = json.load(f)
            logger.info(f"Loaded intent patterns from {self.patterns_path}")
        except Exception as e:
            logger.error(f"Failed to load intent patterns: {e}")
            self.patterns = {}
    
    def detect(
        self, 
        query: str, 
        context: Optional[ConversationContext] = None
    ) -> IntentResult:
        """
        Detect the intent of a user query.
        
        Args:
            query: User's query string
            context: Optional conversation context for better classification
            
        Returns:
            IntentResult with detected intent, confidence, and metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to intent detector")
            return IntentResult(
                intent="general",
                confidence=0.0,
                classification_method="fallback"
            )
        
        query = query.strip()
        
        # Step 1: Check for multi-task indicators FIRST (before single-intent classification)
        # This ensures multi-task queries are properly detected even if they contain strong single-intent keywords
        if self._has_multi_task_indicators(query):
            # Use LLM to parse multi-task query
            try:
                sub_tasks = self._parse_multi_task_llm(query)
                if sub_tasks and len(sub_tasks) > 1:
                    logger.info(f"Multi-task query detected with {len(sub_tasks)} sub-tasks")
                    return IntentResult(
                        intent="multi_task",
                        confidence=0.85,
                        classification_method="llm_assisted",
                        sub_tasks=sub_tasks
                    )
            except Exception as e:
                logger.error(f"Multi-task parsing failed: {e}")
                # Fall through to single-intent classification
        
        # Step 2: Try rule-based classification (fast path for single-intent queries)
        intent, confidence = self._apply_rules(query)
        
        # If rule-based classification is confident, use it
        if confidence >= 0.7:
            logger.info(f"Rule-based classification: {intent} (confidence: {confidence:.2f})")
            return IntentResult(
                intent=intent,
                confidence=confidence,
                classification_method="rule_based"
            )
        
        # Step 3: Use LLM for complex/ambiguous queries
        if self.llm:
            try:
                llm_intent, llm_confidence = self._classify_with_llm(query, context)
                logger.info(f"LLM classification: {llm_intent} (confidence: {llm_confidence:.2f})")
                return IntentResult(
                    intent=llm_intent,
                    confidence=llm_confidence,
                    classification_method="llm_assisted"
                )
            except Exception as e:
                logger.error(f"LLM classification failed: {e}")
        
        # Step 4: Fallback - use rule-based result even if low confidence
        logger.warning(f"Using low-confidence rule-based result as fallback: {intent}")
        return IntentResult(
            intent=intent if confidence > 0.0 else "general",
            confidence=max(confidence, 0.3),  # Minimum fallback confidence
            classification_method="fallback"
        )
    
    def _apply_rules(self, query: str) -> Tuple[IntentCategory, float]:
        """
        Apply rule-based classification using patterns and keywords.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (intent, confidence score)
        """
        query_lower = query.lower()
        
        # Score each category
        category_scores: Dict[str, float] = {
            "cooking": 0.0,
            "household": 0.0,
            "smart_home": 0.0,
            "general": 0.0
        }
        
        # Check patterns for each category
        for category in ["cooking", "household", "smart_home", "general"]:
            if category not in self.patterns:
                continue
            
            category_config = self.patterns[category]
            max_score = 0.0
            
            # Check regex patterns (higher weight)
            patterns = category_config.get("patterns", [])
            for pattern in patterns:
                try:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        max_score = max(max_score, 0.9)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            
            # Check keywords (lower weight)
            keywords = category_config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    max_score = max(max_score, 0.6)
            
            category_scores[category] = max_score
        
        # Find highest scoring category
        best_category = max(category_scores.items(), key=lambda x: x[1])
        intent, confidence = best_category
        
        # If no strong match, default to general
        if confidence < 0.3:
            return "general", confidence
        
        return intent, confidence
    
    def _has_multi_task_indicators(self, query: str) -> bool:
        """
        Check if query contains indicators of multiple tasks.
        
        Args:
            query: User's query string
            
        Returns:
            True if multi-task indicators found
        """
        if "multi_task_indicators" not in self.patterns:
            return False
        
        indicators = self.patterns["multi_task_indicators"]
        patterns = indicators.get("patterns", [])
        
        query_lower = query.lower()
        for pattern in patterns:
            try:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return True
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return False
    
    def _classify_with_llm(
        self, 
        query: str, 
        context: Optional[ConversationContext]
    ) -> Tuple[IntentCategory, float]:
        """
        Use LLM to classify query intent.
        
        Args:
            query: User's query string
            context: Optional conversation context
            
        Returns:
            Tuple of (intent, confidence score)
        """
        system_prompt = """You are an intent classifier for a voice assistant system.
Your job is to classify user queries into one of these categories:
- cooking: recipes, timers, cooking instructions, ingredients, meal planning
- household: shopping lists, calendars, appointments, reminders, schedules
- smart_home: lights, thermostat, locks, garage, greenhouse, devices
- general: weather, time, greetings, general questions

Respond with ONLY a JSON object in this format:
{"intent": "category_name", "confidence": 0.85}

Confidence should be between 0.0 and 1.0 based on how clear the intent is."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this query: {query}"}
        ]
        
        response = self.llm.generate_response(
            messages=messages,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=50
        )
        
        # Parse JSON response
        content = response.get("content", "")
        try:
            result = json.loads(content)
            intent = result.get("intent", "general")
            confidence = float(result.get("confidence", 0.5))
            
            # Validate intent category
            valid_intents = ["cooking", "household", "smart_home", "general"]
            if intent not in valid_intents:
                logger.warning(f"Invalid intent from LLM: {intent}, defaulting to 'general'")
                intent = "general"
                confidence = 0.5
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            return intent, confidence
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"LLM response content: {content}")
            return "general", 0.5
    
    def _parse_multi_task_llm(self, query: str) -> List[SubTask]:
        """
        Use LLM to parse a multi-task query into sub-tasks.
        
        Args:
            query: User's query string containing multiple tasks
            
        Returns:
            List of SubTask objects
        """
        if not self.llm:
            return []
        
        system_prompt = """You are a task parser for a voice assistant.
Your job is to break down multi-task queries into separate sub-tasks.

For each sub-task, determine:
- text: the task description
- intent: category (cooking, household, smart_home, or general)
  - cooking: recipes, meal planning, dinner ideas, food suggestions, timers, ingredients
  - household: shopping lists, to-do lists, calendar, reminders, appointments
  - smart_home: lights, thermostat, locks, devices, greenhouse
  - general: everything else
- confidence: how confident you are (0.0 to 1.0)
- is_dependent: Set to true ONLY when the user has NOT yet approved or confirmed the second task
  and genuinely needs to see the first task's output before deciding whether to proceed.
  Set to false in ALL of these cases:
    * The user explicitly requests both tasks in one message ("X then Y", "X and also Y")
    * The second task references output from the first but can proceed using conversation context
      (e.g., "plan a dinner then make a shopping list" — Hank can read the dinner plan from context)
    * The user gives a clear end-to-end workflow ("plan dinner for this weekend then make a list
      for the supplies" — both tasks are pre-approved)
  Only set to true when the user is still deciding (e.g., "what should I make for dinner?
  ...if I like it, add the ingredients" — the user hasn't yet committed to the second task).

IMPORTANT: When a user says "do X then do Y" or "do X and make me Y", BOTH tasks are
pre-approved. Mark them BOTH as is_dependent: false so they execute in the same turn.

Respond with ONLY a JSON array of tasks:
[
  {"text": "set a timer for 30 minutes", "intent": "cooking", "confidence": 0.9, "is_dependent": false},
  {"text": "add milk to shopping list", "intent": "household", "confidence": 0.95, "is_dependent": false},
  {"text": "plan a fancy dinner for this weekend", "intent": "cooking", "confidence": 0.9, "is_dependent": false},
  {"text": "make a shopping list for the dinner supplies", "intent": "household", "confidence": 0.9, "is_dependent": false}
]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this query into sub-tasks: {query}"}
        ]
        
        response = self.llm.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=300
        )
        
        # Parse JSON response
        content = response.get("content", "")
        try:
            tasks_data = json.loads(content)
            
            if not isinstance(tasks_data, list):
                logger.error("LLM did not return a list of tasks")
                return []
            
            sub_tasks = []
            valid_intents = ["cooking", "household", "smart_home", "general"]
            
            for task_data in tasks_data:
                text = task_data.get("text", "").strip()
                intent = task_data.get("intent", "general")
                confidence = float(task_data.get("confidence", 0.5))
                is_dependent = bool(task_data.get("is_dependent", False))
                
                # Validate
                if not text:
                    continue
                if intent not in valid_intents:
                    intent = "general"
                confidence = max(0.0, min(1.0, confidence))
                
                sub_tasks.append(SubTask(
                    text=text,
                    intent=intent,
                    confidence=confidence,
                    is_dependent=is_dependent
                ))
            
            return sub_tasks
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse multi-task LLM response: {e}")
            logger.debug(f"LLM response content: {content}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about intent detection performance.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "patterns_loaded": len(self.patterns),
            "llm_available": self.llm is not None
        }
        
        if self.llm:
            stats["llm_model"] = self.llm.model
            stats["llm_total_requests"] = self.llm.total_requests
            stats["llm_total_tokens"] = self.llm.total_tokens_used
        
        return stats
