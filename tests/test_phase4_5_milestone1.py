"""
End-to-End Tests for Phase 4.5 Milestone 1: Intent Detection System

Tests the intent detection API endpoint and classification accuracy.
"""

import pytest
import httpx
from typing import Dict, Any


# Test configuration
BASE_URL = "http://localhost:8000"


class TestClient:
    """Test client for interacting with the debug API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def detect_intent(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """
        Call the intent detection endpoint.
        
        Args:
            query: Query to classify
            user_id: User ID for context
            
        Returns:
            Response JSON with intent detection results
        """
        response = self.client.post(
            "/api/debug/detect-intent",
            json={"query": query, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    def get_intent_stats(self) -> Dict[str, Any]:
        """Get intent detection statistics."""
        response = self.client.get("/api/debug/intent-stats")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client"""
        self.client.close()


@pytest.fixture
def test_client():
    """Fixture providing a test client"""
    client = TestClient()
    yield client
    client.close()


class TestIntentDetection:
    """Test suite for intent detection system"""

    def test_cooking_intent_timer(self, test_client):
        """Test 1: Single cooking intent - timer"""
        result = test_client.detect_intent("Set a timer for 30 minutes")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "cooking", f"Expected 'cooking', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.7, "Confidence should be high for clear cooking query"
        assert result["processing_time_ms"] < 1000, "Should respond quickly"
    
    def test_cooking_intent_recipe(self, test_client):
        """Test: Cooking intent - recipe query"""
        result = test_client.detect_intent("How do I make chocolate chip cookies?")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "cooking", f"Expected 'cooking', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.5, "Should have reasonable confidence"
    
    def test_household_intent_shopping_list(self, test_client):
        """Test 2: Single household intent - shopping list"""
        result = test_client.detect_intent("Add milk to shopping list")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "household", f"Expected 'household', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.7, "Confidence should be high for clear household query"
        assert result["processing_time_ms"] < 1000, "Should respond quickly"
    
    def test_household_intent_calendar(self, test_client):
        """Test: Household intent - calendar query"""
        result = test_client.detect_intent("What's on my calendar today?")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "household", f"Expected 'household', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.5, "Should have reasonable confidence"
    
    def test_smart_home_intent_lights(self, test_client):
        """Test: Smart home intent - lights"""
        result = test_client.detect_intent("Turn on the kitchen lights")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "smart_home", f"Expected 'smart_home', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.7, "Confidence should be high for clear smart home query"
    
    def test_smart_home_intent_thermostat(self, test_client):
        """Test: Smart home intent - thermostat"""
        result = test_client.detect_intent("Set the thermostat to 72 degrees")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "smart_home", f"Expected 'smart_home', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.5, "Should have reasonable confidence"
    
    def test_multi_task_intent(self, test_client):
        """Test 3: Multi-task intent"""
        result = test_client.detect_intent("Set a timer for 20 minutes and add eggs to the list")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "multi_task", f"Expected 'multi_task', got '{intent_result['intent']}'"
        
        # Check for sub-tasks
        assert "sub_tasks" in intent_result, "Multi-task should have sub_tasks"
        sub_tasks = intent_result["sub_tasks"]
        assert len(sub_tasks) >= 2, f"Expected at least 2 sub-tasks, got {len(sub_tasks)}"
        
        # Verify sub-task intents
        intents = [task["intent"] for task in sub_tasks]
        assert "cooking" in intents, "Should detect cooking sub-task"
        assert "household" in intents, "Should detect household sub-task"
    
    def test_general_intent_weather(self, test_client):
        """Test 4: General intent - ambiguous query"""
        result = test_client.detect_intent("What's the weather like today?")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "general", f"Expected 'general', got '{intent_result['intent']}'"
        # General queries may have lower confidence
        assert 0.0 <= intent_result["confidence"] <= 1.0, "Confidence should be in valid range"
    
    def test_general_intent_greeting(self, test_client):
        """Test: General intent - greeting"""
        result = test_client.detect_intent("Hello, how are you?")
        
        intent_result = result["intent_result"]
        assert intent_result["intent"] == "general", f"Expected 'general', got '{intent_result['intent']}'"
        assert intent_result["confidence"] >= 0.3, "Should have some confidence"
    
    def test_empty_query(self, test_client):
        """Test 5: Edge case - empty query"""
        # Note: The API should reject completely empty queries due to min_length=1 validation
        # But let's test with just whitespace
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            test_client.detect_intent("")
        
        # Should get a 422 validation error
        assert exc_info.value.response.status_code == 422
    
    def test_whitespace_only_query(self, test_client):
        """Test: Edge case - whitespace only"""
        # The API gracefully handles whitespace by stripping and treating as empty
        # which returns a general intent with low confidence (better than rejecting)
        result = test_client.detect_intent("   ")
        intent_result = result["intent_result"]
        
        assert intent_result["intent"] == "general", "Whitespace should default to general"
        assert intent_result["confidence"] <= 0.5, "Should have low confidence"
        assert intent_result["classification_method"] == "fallback", "Should use fallback"
    
    def test_confidence_scoring(self, test_client):
        """Test 6: Confidence scoring validation"""
        # Test with very clear query
        result = test_client.detect_intent("Set timer for 10 minutes")
        intent_result = result["intent_result"]
        
        # Validate confidence is in range
        assert 0.0 <= intent_result["confidence"] <= 1.0, "Confidence must be between 0 and 1"
        
        # For this clear query, should have high confidence
        assert intent_result["confidence"] >= 0.7, "Clear queries should have high confidence"
    
    def test_classification_methods(self, test_client):
        """Test: Different classification methods are used appropriately"""
        # Simple query should use rule-based
        result1 = test_client.detect_intent("Set a timer")
        assert result1["classification_method"] in ["rule_based", "llm_assisted", "fallback"]
        
        # Complex query might use LLM
        result2 = test_client.detect_intent("Can you help me figure out what to cook for dinner tonight?")
        assert result2["classification_method"] in ["rule_based", "llm_assisted", "fallback"]
    
    def test_intent_stats_endpoint(self, test_client):
        """Test: Intent statistics endpoint"""
        stats = test_client.get_intent_stats()
        
        assert "status" in stats
        assert stats["status"] == "operational"
        assert "statistics" in stats
        
        statistics = stats["statistics"]
        assert "patterns_loaded" in statistics
        assert "llm_available" in statistics
        
        # Should have loaded patterns
        assert statistics["patterns_loaded"] > 0, "Should have loaded intent patterns"
    
    def test_performance_latency(self, test_client):
        """Test: Response latency is acceptable"""
        import time
        
        queries = [
            "Set a timer for 5 minutes",
            "Add bread to shopping list",
            "Turn off the lights",
            "What's the weather?"
        ]
        
        latencies = []
        for query in queries:
            start = time.time()
            result = test_client.detect_intent(query)
            latency = (time.time() - start) * 1000  # Convert to ms
            latencies.append(latency)
            
            # Individual query should be reasonably fast
            assert result["processing_time_ms"] < 2000, f"Processing took {result['processing_time_ms']}ms"
        
        # Average latency should be good
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 1500, f"Average latency {avg_latency:.0f}ms exceeds target"


class TestIntentAccuracy:
    """Test suite for intent classification accuracy"""
    
    # Test dataset with expected intents
    TEST_CASES = [
        # Cooking queries
        ("Set a timer for 30 minutes", "cooking"),
        ("How do I make lasagna?", "cooking"),
        ("What temperature should I bake cookies?", "cooking"),
        ("Add vanilla to my ingredient list", "cooking"),
        
        # Household queries
        ("Add milk to the shopping list", "household"),
        ("What's on my calendar tomorrow?", "household"),
        ("Remind me to call mom at 3pm", "household"),
        ("Check my grocery list", "household"),
        
        # Smart home queries
        ("Turn on the living room lights", "smart_home"),
        ("Set thermostat to 70 degrees", "smart_home"),
        ("Lock the front door", "smart_home"),
        ("Check greenhouse humidity", "smart_home"),
        
        # General queries
        ("What's the weather today?", "general"),
        ("What time is it?", "general"),
        ("Hello", "general"),
        ("Thank you", "general"),
    ]
    
    @pytest.mark.parametrize("query,expected_intent", TEST_CASES)
    def test_intent_accuracy(self, test_client, query, expected_intent):
        """Test classification accuracy on known queries"""
        result = test_client.detect_intent(query)
        intent_result = result["intent_result"]
        
        actual_intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        assert actual_intent == expected_intent, (
            f"Query: '{query}'\n"
            f"Expected: {expected_intent}\n"
            f"Got: {actual_intent} (confidence: {confidence:.2f})"
        )


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
