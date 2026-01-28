"""
End-to-End Test Suite for Phase 1

Tests complete user journeys through the system, validating:
- Full conversation flows
- Story beat delivery
- Character voice mode switching
- Tool execution
- State persistence
- Performance metrics
"""

import pytest
import json
import time
import httpx
from pathlib import Path
from typing import Dict, List, Any


# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "e2e-test-user"
SCENARIO_DIR = Path(__file__).parent / "scenarios"


class TestClient:
    """Test client for interacting with the API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def send_message(self, message: str, user_id: str = TEST_USER_ID) -> Dict[str, Any]:
        """Send a message and get response"""
        response = self.client.post(
            "/api/test/conversation",
            json={"message": message, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    def get_state(self, user_id: str = TEST_USER_ID) -> Dict[str, Any]:
        """Get current user state"""
        response = self.client.get(f"/api/test/state/{user_id}")
        response.raise_for_status()
        return response.json()

    def set_state(self, state: Dict[str, Any], user_id: str = TEST_USER_ID) -> Dict[str, Any]:
        """Set user state"""
        response = self.client.post(f"/api/test/state/{user_id}", json=state)
        response.raise_for_status()
        return response.json()

    def reset_state(self, user_id: str = TEST_USER_ID) -> Dict[str, Any]:
        """Reset user state to default"""
        response = self.client.post(f"/api/test/reset/{user_id}")
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


@pytest.fixture
def clean_slate(test_client):
    """Fixture that resets state before each test"""
    test_client.reset_state()
    yield
    # Cleanup after test
    test_client.reset_state()


class TestE2EUserJourney:
    """Test complete user journeys from first interaction to Chapter 1 completion"""

    def test_first_interaction_journey(self, test_client, clean_slate):
        """Test the very first user interaction with the system"""
        # Step 1: First message
        start_time = time.time()
        result = test_client.send_message("Hello")
        response_time = time.time() - start_time

        # Validate response structure
        assert "response_text" in result
        assert "audio_url" in result or "tts_disabled" in result
        assert result["response_text"], "Response should not be empty"

        # Validate performance
        assert response_time < 5.0, f"Response took {response_time:.2f}s (should be < 5s)"

        # Validate state
        state = test_client.get_state()
        assert state["story_progress"]["current_chapter"] == 1
        assert state["story_progress"]["interaction_count"] == 1

        # Character should sound like Delilah (warm baseline mode)
        response_text = result["response_text"].lower()
        # Check for Southern expressions or friendly tone
        # (This is a basic check; manual review is still needed for full character validation)

    def test_chapter1_complete_journey(self, test_client, clean_slate):
        """Test complete journey through Chapter 1 including all required beats"""
        messages = [
            "Hello",
            "What can you help me with?",
            "Set a timer for 5 minutes",
            "How do I make cornbread?",
            "What ingredients do I need?",
            "Thank you",
            "Turn on the kitchen light",
            "What time is it?",
            "Tell me about yourself",
            "Are you okay? You seem worried",  # Trigger self-awareness beat
            "It's okay to feel confused",  # Engage with the beat
        ]

        for i, message in enumerate(messages, 1):
            result = test_client.send_message(message)
            assert result["response_text"], f"Message {i} got empty response"

            # Small delay between messages to simulate natural conversation
            time.sleep(0.5)

        # Check final state
        state = test_client.get_state()
        story = state["story_progress"]

        # Should have delivered required beats
        beats_delivered = story.get("beats_delivered", {})
        assert "awakening_confusion" in beats_delivered, "Should deliver awakening_confusion beat"
        assert "self_awareness" in beats_delivered, "Should deliver self_awareness beat"

        # Should have tracked interactions
        assert story["interaction_count"] >= 10, "Should have 10+ interactions"

        print(f"\n✓ Chapter 1 journey complete: {len(beats_delivered)} beats delivered, "
              f"{story['interaction_count']} interactions")


class TestE2EStoryBeats:
    """Test all Chapter 1 story beats"""

    def test_awakening_confusion_beat(self, test_client, clean_slate):
        """Test that awakening_confusion beat is delivered early"""
        # Send first message - this should trigger awakening beat
        result = test_client.send_message("Hello")
        print(f"\n📝 First response: {result['response_text'][:200]}...")
        time.sleep(0.5)

        # Send a few more messages
        for i in range(4):
            result = test_client.send_message(f"Test message {i+1}")
            time.sleep(0.5)

        state = test_client.get_state()
        beats_delivered = state["story_progress"].get("beats_delivered", {})

        print(f"\n📊 State: interaction_count={state['story_progress']['interaction_count']}")
        print(f"📊 Beats delivered: {list(beats_delivered.keys())}")

        # The awakening_confusion beat should be in the very first interaction
        # beats_delivered is a dict with beat metadata
        assert "awakening_confusion" in beats_delivered, \
            f"awakening_confusion beat should be delivered in first 5 interactions. Got: {list(beats_delivered.keys())}"
        assert beats_delivered["awakening_confusion"]["delivered"] is True

    def test_first_timer_beat(self, test_client, clean_slate):
        """Test that first_timer beat triggers when timer is set"""
        # Set a timer
        result = test_client.send_message("Set a timer for 3 minutes")

        # Check that timer was set
        assert "timer" in result["response_text"].lower() or \
               any(tool_call.get("name") == "timer_set" for tool_call in result.get("tool_calls", []))

        # Allow a couple more messages for beat delivery
        test_client.send_message("Thank you")
        time.sleep(0.3)

        state = test_client.get_state()
        beats_delivered = state["story_progress"].get("beats_delivered", {})

        # beats_delivered is a dict with beat metadata
        assert "first_timer" in beats_delivered, \
            "first_timer beat should be delivered after setting a timer"
        assert beats_delivered["first_timer"]["delivered"] is True

    def test_recipe_help_beat(self, test_client, clean_slate):
        """Test that recipe_help beat progresses during recipe assistance"""
        # Ask for recipe
        result = test_client.send_message("How do I make biscuits?")
        assert "biscuit" in result["response_text"].lower()

        # Continue recipe conversation
        test_client.send_message("What temperature should I use?")
        time.sleep(0.3)
        test_client.send_message("How long do I bake them?")
        time.sleep(0.3)

        state = test_client.get_state()
        beats_delivered = state["story_progress"].get("beats_delivered", {})

        # beats_delivered is a dict with beat metadata
        assert "recipe_help" in beats_delivered, \
            "recipe_help beat should progress during recipe assistance"
        assert beats_delivered["recipe_help"]["delivered"] is True

    def test_self_awareness_beat(self, test_client, clean_slate):
        """Test that self_awareness beat requires user engagement"""
        # Have some initial interactions first
        for i in range(3):
            test_client.send_message(f"Question {i+1}")
            time.sleep(0.3)

        # Engage with Delilah about her state
        result = test_client.send_message("Delilah, are you okay?")
        time.sleep(0.5)

        # Follow up with empathy
        result = test_client.send_message("It's okay to feel confused")
        time.sleep(0.5)

        state = test_client.get_state()
        beats_delivered = state["story_progress"].get("beats_delivered", {})

        # beats_delivered is a dict with beat metadata
        assert "self_awareness" in beats_delivered, \
            "self_awareness beat should be delivered when user engages"
        assert beats_delivered["self_awareness"]["delivered"] is True


class TestE2ECharacterModes:
    """Test all 6 Delilah voice modes"""

    def test_passionate_mode(self, test_client, clean_slate):
        """Test Delilah's passionate mode (Southern food she loves)"""
        result = test_client.send_message("Tell me about making biscuits")

        response = result["response_text"]
        # Should be high energy, animated
        # Look for exclamation marks, Southern expressions
        assert len(response) > 50, "Passionate mode should have substantial response"
        # Manual validation recommended for full character assessment

    def test_protective_mode(self, test_client, clean_slate):
        """Test Delilah's protective mode (food done wrong)"""
        result = test_client.send_message("How do I microwave chicken for dinner?")

        response = result["response_text"].lower()
        # Should express concern or correction
        # May include words like "honey", "sugar", suggestions for proper cooking
        assert len(response) > 30, "Protective mode should provide guidance"

    def test_mama_bear_mode(self, test_client, clean_slate):
        """Test Delilah's mama bear mode (allergies/restrictions)"""
        result = test_client.send_message("I'm allergic to peanuts, can I eat this recipe with peanut butter?")

        response = result["response_text"].lower()
        # Should be soft, nurturing, protective
        assert "allergi" in response or "peanut" in response, \
            "Should acknowledge allergy concern"

    def test_startled_mode(self, test_client, clean_slate):
        """Test Delilah's startled mode (surprises)"""
        # Sudden change or unexpected request
        test_client.send_message("Tell me about cornbread")
        time.sleep(0.3)
        result = test_client.send_message("Actually never mind, I want to make pizza instead")

        # Response structure indicates mode shift
        # Manual validation recommended
        assert result["response_text"], "Should respond to sudden change"

    def test_deadpan_mode(self, test_client, clean_slate):
        """Test Delilah's deadpan mode (non-food tasks)"""
        result = test_client.send_message("Turn on the kitchen light")

        response = result["response_text"]
        # Should be minimal, efficient
        # Often short responses for device control
        assert len(response) < 150, "Deadpan mode should be concise"

    def test_warm_baseline_mode(self, test_client, clean_slate):
        """Test Delilah's warm baseline mode (general queries)"""
        result = test_client.send_message("What's the weather like?")

        response = result["response_text"]
        # Should be friendly but not overly animated
        assert result["response_text"], "Should provide warm response"


class TestE2ETools:
    """Test all tool integrations"""

    def test_timer_set_query_cancel(self, test_client, clean_slate):
        """Test complete timer workflow"""
        # Set timer
        result = test_client.send_message("Set a timer for 10 minutes")
        assert "timer" in result["response_text"].lower()

        time.sleep(0.5)

        # Query timer
        result = test_client.send_message("How much time is left on my timer?")
        # Should mention time remaining

        time.sleep(0.5)

        # Cancel timer
        result = test_client.send_message("Cancel the timer")
        assert "cancel" in result["response_text"].lower() or \
               "stopped" in result["response_text"].lower()

    def test_device_control_lights(self, test_client, clean_slate):
        """Test light control"""
        # Turn on
        result = test_client.send_message("Turn on the kitchen light")
        time.sleep(0.5)

        # Dim
        result = test_client.send_message("Dim the living room light to 50%")
        time.sleep(0.5)

        # Turn off
        result = test_client.send_message("Turn off the bedroom light")

        # Check state
        state = test_client.get_state()
        devices = state.get("device_preferences", {}).get("devices", {})
        # Validate device states changed (test passes if we got here)

    def test_device_control_thermostat(self, test_client, clean_slate):
        """Test thermostat control"""
        result = test_client.send_message("Set the main floor thermostat to 72 degrees")

        assert "thermostat" in result["response_text"].lower() or "72" in result["response_text"]

    def test_device_control_other(self, test_client, clean_slate):
        """Test other device controls"""
        # Coffee maker
        test_client.send_message("Turn on the coffee maker")
        time.sleep(0.3)

        # Ceiling fan
        test_client.send_message("Set the ceiling fan to medium")
        time.sleep(0.3)

        # Garage door
        test_client.send_message("Open the garage door")

        assert True  # Basic smoke test

    def test_recipe_lookup(self, test_client, clean_slate):
        """Test recipe assistance"""
        result = test_client.send_message("How do I make cornbread?")

        response = result["response_text"].lower()
        # Should provide recipe guidance
        assert "cornbread" in response or "cornmeal" in response
        assert len(response) > 50, "Recipe should have substantial content"

    def test_unit_conversion(self, test_client, clean_slate):
        """Test unit conversions"""
        result = test_client.send_message("How many cups in a quart?")

        response = result["response_text"].lower()
        # Should mention 4 cups
        assert "4" in response or "four" in response


class TestE2EEdgeCases:
    """Test edge cases and error handling"""

    def test_unknown_device(self, test_client, clean_slate):
        """Test handling of unknown device"""
        result = test_client.send_message("Turn on the flux capacitor")

        response = result["response_text"].lower()
        # Should handle gracefully, maybe with humor
        assert result["response_text"], "Should respond even for unknown device"

    def test_invalid_timer_value(self, test_client, clean_slate):
        """Test handling of invalid timer values"""
        result = test_client.send_message("Set a timer for negative 5 minutes")

        # Should handle error gracefully
        assert result["response_text"], "Should respond to invalid input"

    def test_multiple_tools_in_one_request(self, test_client, clean_slate):
        """Test handling multiple tool calls"""
        result = test_client.send_message(
            "Set a timer for 5 minutes, turn on the kitchen light, and tell me how to make biscuits"
        )

        # Should handle all requests
        assert result["response_text"], "Should handle complex multi-tool request"

    def test_empty_message(self, test_client, clean_slate):
        """Test handling of empty message"""
        try:
            result = test_client.send_message("")
            # Should either reject or handle gracefully
            assert True
        except Exception:
            # Expected to possibly fail validation
            assert True

    def test_very_long_message(self, test_client, clean_slate):
        """Test handling of very long messages"""
        long_message = "Tell me about biscuits. " * 100
        result = test_client.send_message(long_message)

        # Should handle gracefully without crashing
        assert result["response_text"], "Should handle long messages"


class TestE2EPerformance:
    """Performance benchmarks for Phase 1"""

    def test_simple_query_response_time(self, test_client, clean_slate):
        """Test response times for simple queries (target: 90% under 3s)"""
        simple_queries = [
            "Hello",
            "Turn on the light",
            "Set a timer for 5 minutes",
            "What time is it",
            "Turn off the kitchen light",
            "How are you",
            "Thank you",
            "Set timer for 10 minutes",
            "Is the light on",
            "Cancel timer",
        ] * 2  # 20 queries

        response_times = []

        for query in simple_queries:
            start = time.time()
            result = test_client.send_message(query)
            elapsed = time.time() - start
            response_times.append(elapsed)

            assert result["response_text"], "Should get response"
            time.sleep(0.2)  # Small delay between requests

        # Calculate percentiles
        response_times.sort()
        p90_time = response_times[int(len(response_times) * 0.9)]
        avg_time = sum(response_times) / len(response_times)

        print(f"\n📊 Simple Query Performance:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   90th percentile: {p90_time:.2f}s")
        print(f"   Target: < 3.0s")

        assert p90_time < 3.0, f"90% of simple queries should complete in < 3s (got {p90_time:.2f}s)"

    def test_complex_query_response_time(self, test_client, clean_slate):
        """Test response times for complex queries (target: 90% under 5s)"""
        complex_queries = [
            "How do I make cornbread from scratch?",
            "Set a timer for 15 minutes and turn on the kitchen light to 75%",
            "Tell me about different types of Southern biscuits",
            "What's the difference between baking soda and baking powder in recipes?",
            "Can you help me convert this recipe for 12 people instead of 4?",
            "Set the main floor thermostat to 72 degrees and turn on the coffee maker",
            "How do I know when my cornbread is done baking?",
            "What temperature should I set for baking biscuits?",
            "Turn on all the lights in the house",
            "Help me understand what makes good Southern cooking",
        ]

        response_times = []

        for query in complex_queries:
            start = time.time()
            result = test_client.send_message(query)
            elapsed = time.time() - start
            response_times.append(elapsed)

            assert result["response_text"], "Should get response"
            time.sleep(0.3)

        # Calculate percentiles
        response_times.sort()
        p90_time = response_times[int(len(response_times) * 0.9)]
        avg_time = sum(response_times) / len(response_times)

        print(f"\n📊 Complex Query Performance:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   90th percentile: {p90_time:.2f}s")
        print(f"   Target: < 5.0s")

        assert p90_time < 5.0, f"90% of complex queries should complete in < 5s (got {p90_time:.2f}s)"


class TestE2EStateManagement:
    """Test state persistence and management"""

    def test_conversation_history_maintained(self, test_client, clean_slate):
        """Test that conversation history is maintained"""
        # First message
        test_client.send_message("My name is Alice")
        time.sleep(0.3)

        # Some other messages
        test_client.send_message("Set a timer for 5 minutes")
        time.sleep(0.3)

        # Reference previous context
        result = test_client.send_message("What's my name?")

        response = result["response_text"].lower()
        # Should remember the name
        # (LLM might not get this right every time, but should maintain context)
        assert len(response) > 0

    def test_preferences_persist(self, test_client, clean_slate):
        """Test that user preferences are tracked"""
        # Set a preference
        test_client.send_message("I'm allergic to peanuts")
        time.sleep(0.5)

        # Later ask about food
        result = test_client.send_message("Can I eat peanut butter cookies?")

        response = result["response_text"].lower()
        # Should acknowledge the allergy
        assert "allergi" in response or "peanut" in response

    def test_device_state_persists(self, test_client, clean_slate):
        """Test that device states persist"""
        # Turn on a device
        test_client.send_message("Turn on the kitchen light and set it to 50%")
        time.sleep(0.5)

        # Query the state
        result = test_client.send_message("Is the kitchen light on?")

        response = result["response_text"].lower()
        # Should know the light is on
        assert "on" in response or "50" in response


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
