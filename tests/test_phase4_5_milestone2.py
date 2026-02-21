"""
End-to-End Tests for Phase 4.5 Milestone 2: Character Planning System

Tests the character planning API endpoint and character assignment logic.
"""

import pytest
import httpx
from typing import Dict, Any, List


# Test configuration
BASE_URL = "http://localhost:8000"


class TestClient:
    """Test client for interacting with the debug API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def create_plan(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """
        Call the create-plan endpoint.
        
        Args:
            query: Query to create a plan for
            user_id: User ID for context
            
        Returns:
            Response JSON with character plan
        """
        response = self.client.post(
            "/api/debug/create-plan",
            json={"query": query, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client"""
        self.client.close()


@pytest.fixture
def client():
    """Create a test client and clean up after test."""
    test_client = TestClient()
    yield test_client
    test_client.close()


# ============================================================================
# Test Character Plan Creation
# ============================================================================

class TestCharacterPlanning:
    """Test basic character planning functionality."""

    def test_cooking_intent_delilah(self, client: TestClient):
        """Test that cooking intents are assigned to Delilah."""
        result = client.create_plan("Set a timer for 30 minutes")
        
        # Check response structure
        assert "query" in result
        assert "intent_result" in result
        assert "character_plan" in result
        
        # Check intent detection
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "cooking"
        assert intent_result["confidence"] > 0.5
        
        # Check character plan
        plan = result["character_plan"]
        assert "tasks" in plan
        assert len(plan["tasks"]) == 1
        assert plan["execution_mode"] == "single"
        
        # Check character assignment
        task = plan["tasks"][0]
        assert task["character"] == "delilah"
        assert task["intent"] == "cooking"
        assert not task["requires_handoff"]

    def test_household_intent_chapter1(self, client: TestClient):
        """Test that household intents go to Delilah in Chapter 1."""
        result = client.create_plan("Add milk to shopping list")
        
        # Check intent detection
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "household"
        
        # In Chapter 1 (default), Delilah handles everything
        plan = result["character_plan"]
        assert len(plan["tasks"]) == 1
        task = plan["tasks"][0]
        assert task["character"] == "delilah"
        assert task["intent"] == "household"

    def test_smart_home_intent(self, client: TestClient):
        """Test smart home intent handling."""
        result = client.create_plan("Turn on the kitchen lights")
        
        # Check intent detection
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "smart_home"
        
        # Check character assignment
        plan = result["character_plan"]
        assert len(plan["tasks"]) == 1
        task = plan["tasks"][0]
        # In Chapter 1, Delilah handles smart_home
        assert task["character"] == "delilah"
        assert task["intent"] == "smart_home"

    def test_general_intent(self, client: TestClient):
        """Test general intent handling."""
        result = client.create_plan("What's the weather like?")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "general"
        
        plan = result["character_plan"]
        assert len(plan["tasks"]) == 1
        assert plan["execution_mode"] == "single"


# ============================================================================
# Test Multi-Task Planning
# ============================================================================

class TestMultiTaskPlanning:
    """Test multi-task query decomposition and character coordination."""

    def test_multi_task_detection(self, client: TestClient):
        """Test that multi-task queries are properly detected."""
        result = client.create_plan("Set a timer for 20 minutes and add eggs to the list")
        
        # Check intent detection
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "multi_task"
        assert "sub_tasks" in intent_result
        assert len(intent_result["sub_tasks"]) >= 2
        
        # Check character plan
        plan = result["character_plan"]
        assert len(plan["tasks"]) >= 2

    def test_multi_task_sequential_execution(self, client: TestClient):
        """Test that multi-task plans use sequential execution mode."""
        result = client.create_plan("Set a timer and add milk to the list")
        
        plan = result["character_plan"]
        # Should have multiple tasks
        assert len(plan["tasks"]) >= 2
        
        # Execution mode should be sequential or single (if same character)
        assert plan["execution_mode"] in ["single", "sequential"]

    def test_multi_task_confidence(self, client: TestClient):
        """Test that multi-task plans have appropriate confidence scores."""
        result = client.create_plan("Set timer for 10 minutes and turn off the lights")
        
        plan = result["character_plan"]
        # Total confidence should be averaged from sub-tasks
        assert 0.0 <= plan["total_confidence"] <= 1.0
        
        # Each task should have confidence
        for task in plan["tasks"]:
            assert 0.0 <= task["confidence"] <= 1.0

    def test_multi_task_time_estimation(self, client: TestClient):
        """Test that multi-task plans include time estimates."""
        result = client.create_plan("Set a timer and add eggs to shopping list")
        
        plan = result["character_plan"]
        assert "estimated_total_duration_ms" in plan
        assert plan["estimated_total_duration_ms"] > 0
        
        # Each task should have duration estimate
        for task in plan["tasks"]:
            assert "estimated_duration_ms" in task
            assert task["estimated_duration_ms"] > 0


# ============================================================================
# Test Handoff Logic
# ============================================================================

class TestHandoffLogic:
    """Test handoff detection between characters."""

    def test_no_handoff_single_character(self, client: TestClient):
        """Test that single-character plans have no handoffs."""
        result = client.create_plan("Set a timer for 5 minutes")
        
        plan = result["character_plan"]
        for task in plan["tasks"]:
            assert not task["requires_handoff"]
            assert task["handoff_from"] is None

    def test_handoff_metadata_in_multi_task(self, client: TestClient):
        """Test that handoff metadata is properly set in multi-task plans."""
        result = client.create_plan("Set timer and add milk to list")
        
        plan = result["character_plan"]
        if len(plan["tasks"]) > 1:
            # Check that handoff flags are boolean
            for task in plan["tasks"]:
                assert isinstance(task["requires_handoff"], bool)


# ============================================================================
# Test Plan Metadata
# ============================================================================

class TestPlanMetadata:
    """Test that plans include proper metadata."""

    def test_plan_includes_processing_time(self, client: TestClient):
        """Test that plans include processing time metrics."""
        result = client.create_plan("What's for dinner?")
        
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], (int, float))
        assert result["processing_time_ms"] > 0

    def test_plan_includes_chapter_info(self, client: TestClient):
        """Test that plans include chapter information."""
        result = client.create_plan("Set a timer")
        
        assert "metadata" in result
        metadata = result["metadata"]
        assert "chapter_id" in metadata
        assert isinstance(metadata["chapter_id"], int)

    def test_plan_includes_available_characters(self, client: TestClient):
        """Test that plans indicate available characters."""
        result = client.create_plan("Help me cook dinner")
        
        metadata = result["metadata"]
        assert "available_characters" in metadata
        assert isinstance(metadata["available_characters"], list)
        assert len(metadata["available_characters"]) > 0

    def test_plan_includes_classification_method(self, client: TestClient):
        """Test that plans include intent classification method."""
        result = client.create_plan("Turn on the lights")
        
        intent_result = result["intent_result"]
        assert "classification_method" in intent_result
        assert intent_result["classification_method"] in ["rule_based", "llm_assisted", "fallback"]


# ============================================================================
# Test Character Assignment Rules
# ============================================================================

class TestCharacterAssignments:
    """Test character assignment logic for different intents."""

    def test_cooking_always_delilah(self, client: TestClient):
        """Test that cooking tasks always go to Delilah."""
        queries = [
            "Set a timer for 30 minutes",
            "How do I cook rice?",
            "What's a recipe for cookies?",
            "Convert cups to tablespoons"
        ]
        
        for query in queries:
            result = client.create_plan(query)
            plan = result["character_plan"]
            
            # Find cooking tasks
            for task in plan["tasks"]:
                if task["intent"] == "cooking":
                    assert task["character"] == "delilah", f"Failed for query: {query}"

    def test_default_fallback_character(self, client: TestClient):
        """Test that low-confidence queries fall back to default character."""
        result = client.create_plan("Hmm, not sure what I want")
        
        plan = result["character_plan"]
        # Should have at least one task
        assert len(plan["tasks"]) > 0
        
        # Should fall back to Delilah (default character)
        task = plan["tasks"][0]
        assert task["character"] == "delilah"


# ============================================================================
# Test Execution Time Estimates
# ============================================================================

class TestExecutionTimeEstimates:
    """Test execution time estimation logic."""

    def test_single_task_duration(self, client: TestClient):
        """Test that single tasks have reasonable duration estimates."""
        result = client.create_plan("Set a timer")
        
        plan = result["character_plan"]
        assert plan["estimated_total_duration_ms"] > 0
        # Should be less than 5 seconds for a simple task
        assert plan["estimated_total_duration_ms"] < 5000

    def test_multi_task_duration_sum(self, client: TestClient):
        """Test that multi-task duration is greater than single tasks."""
        result = client.create_plan("Set timer and add eggs to list")
        
        plan = result["character_plan"]
        if len(plan["tasks"]) > 1:
            # Total should be sum of tasks plus handoff overhead
            task_sum = sum(task["estimated_duration_ms"] for task in plan["tasks"])
            assert plan["estimated_total_duration_ms"] >= task_sum


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in character planning."""

    def test_empty_query_handling(self, client: TestClient):
        """Test that empty queries are rejected."""
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.create_plan("")
        
        assert exc_info.value.response.status_code == 422  # Validation error

    def test_invalid_query_gets_fallback_plan(self, client: TestClient):
        """Test that invalid/unclear queries still get a plan."""
        result = client.create_plan("asdfghjkl")
        
        # Should still get a valid plan (fallback to general intent)
        assert "character_plan" in result
        plan = result["character_plan"]
        assert len(plan["tasks"]) > 0


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])
