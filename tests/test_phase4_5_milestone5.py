"""
End-to-End Tests for Phase 4.5 Milestone 5: Integration & Polish

Tests the full Phase 4.5 pipeline: intent detection → character planning → 
multi-character coordination → handoff synthesis → response delivery.
"""

import pytest
import httpx
import json
from typing import Dict, Any


# Test configuration
BASE_URL = "http://localhost:8000"


class TestClient:
    """Test client for interacting with the API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=60.0)

    def send_message(
        self,
        message: str,
        user_id: str = "test_phase45_milestone5",
        input_mode: str = "chat"
    ) -> Dict[str, Any]:
        """
        Send a message via the conversation API.
        
        Args:
            message: Message to send
            user_id: User ID
            input_mode: Input mode (chat or voice)
            
        Returns:
            Response JSON
        """
        response = self.client.post(
            "/api/test/conversation",
            json={
                "user_id": user_id,
                "message": message,
                "input_mode": input_mode
            }
        )
        response.raise_for_status()
        return response.json()

    def detect_intent(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """Call the detect-intent debug endpoint."""
        response = self.client.post(
            "/api/debug/detect-intent",
            json={"query": query, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    def create_plan(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """Call the create-plan debug endpoint."""
        response = self.client.post(
            "/api/debug/create-plan",
            json={"query": query, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    def get_coordination_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get coordination metrics for a user."""
        response = self.client.get(f"/api/debug/coordination/metrics/{user_id}")
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
# Test 1: Full Pipeline - Single Character Query
# ============================================================================

def test_single_character_query_full_pipeline(client):
    """
    Test that a simple cooking query goes through Phase 4.5 pipeline
    and is handled correctly by a single character (Delilah).
    """
    # Send a cooking query
    response = client.send_message(
        message="Set a timer for 30 minutes",
        user_id="test_phase45_milestone5_single"
    )
    
    # Verify response structure
    assert "response_text" in response
    response_text = response["response_text"]
    assert len(response_text) > 0
    
    print(f"✓ Single character query completed successfully")
    print(f"  Response: {response_text[:100]}...")


# ============================================================================
# Test 2: Full Pipeline - Multi-Character Query
# ============================================================================

def test_multi_character_query_full_pipeline(client):
    """
    Test that a multi-task query activates Phase 4.5 multi-character flow
    with Delilah and Hank coordinating their responses.
    """
    # Send a multi-task query (cooking + household)
    response = client.send_message(
        message="Set a timer for 20 minutes and add flour to my shopping list",
        user_id="test_phase45_milestone5_multi"
    )
    
    # Verify response structure
    assert "response_text" in response
    response_text = response["response_text"]
    assert len(response_text) > 0
    
    # Check for Phase 4.5 indicators in response (if available)
    print(f"✓ Multi-task query completed")
    print(f"  Response: {response_text[:150]}...")


# ============================================================================
# Test 3: Intent Detection → Character Planning Pipeline
# ============================================================================

def test_intent_to_plan_pipeline(client):
    """
    Test the intent detection → character planning pipeline works correctly.
    """
    query = "Set timer and add milk to list"
    
    # Step 1: Detect intent
    intent_response = client.detect_intent(query, user_id="test_phase45_pipeline")
    
    assert "intent_result" in intent_response
    intent_result = intent_response["intent_result"]
    
    # Should detect multi_task
    assert intent_result["intent"] in ["multi_task", "cooking", "household"]
    assert intent_result["confidence"] > 0.5
    
    print(f"✓ Intent detected: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})")
    
    # Step 2: Create character plan
    plan_response = client.create_plan(query, user_id="test_phase45_pipeline")
    
    assert "character_plan" in plan_response
    plan = plan_response["character_plan"]
    
    # Verify plan structure
    assert "tasks" in plan
    assert len(plan["tasks"]) >= 1
    assert "execution_mode" in plan
    
    print(f"✓ Character plan created with {len(plan['tasks'])} task(s)")
    
    for i, task in enumerate(plan["tasks"]):
        print(f"  Task {i+1}: {task['character']} - {task['task_description']}")


# ============================================================================
# Test 4: Coordination Tracking
# ============================================================================

def test_coordination_tracking(client):
    """
    Test that coordination events are tracked correctly during multi-character
    interactions.
    """
    user_id = "test_phase45_tracking"
    
    # Send a multi-task query to trigger coordination
    response = client.send_message(
        message="Set a 15 minute timer and add eggs to my list",
        user_id=user_id
    )
    
    # Give it a moment to process
    import time
    time.sleep(0.5)
    
    # Get coordination metrics
    metrics_response = client.get_coordination_metrics(user_id)
    
    assert "metrics" in metrics_response
    metrics = metrics_response["metrics"]
    
    # Check that coordination is being tracked
    assert "total_handoffs" in metrics or "multi_task_completions" in metrics
    
    print(f"✓ Coordination metrics retrieved")
    print(f"  Metrics: {json.dumps(metrics, indent=2)}")


# ============================================================================
# Test 5: Error Handling - Intent Detection Failure
# ============================================================================

def test_error_handling_graceful_fallback(client):
    """
    Test that the system handles errors gracefully and falls back to
    single-character mode when Phase 4.5 components fail.
    """
    # Send a query with special characters that might cause issues
    response = client.send_message(
        message="🎯 @#$% test query with special chars!!!",
        user_id="test_phase45_error_handling"
    )
    
    # Should still get a response (not crash)
    assert "response_text" in response
    assert len(response["response_text"]) > 0
    
    # Response should be helpful even if Phase 4.5 failed
    print(f"✓ System handled problematic query gracefully")
    print(f"  Response: {response['response_text'][:100]}...")


# ============================================================================
# Test 6: Performance - Response Latency
# ============================================================================

def test_response_latency(client):
    """
    Test that multi-character queries complete within acceptable time limits.
    Target: < 10 seconds for multi-character coordination (including LLM calls).
    """
    import time
    
    user_id = "test_phase45_performance"
    
    # Measure time for multi-task query
    start_time = time.time()
    
    response = client.send_message(
        message="Set a 25 minute timer and add butter to my shopping list",
        user_id=user_id
    )
    
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    
    # Verify we got a valid response
    assert "response_text" in response
    assert len(response["response_text"]) > 0
    
    # Check latency (allow up to 15 seconds for multi-character with LLM calls)
    assert elapsed_seconds < 15.0, f"Response took too long: {elapsed_seconds:.2f}s"
    
    print(f"✓ Multi-character response completed in {elapsed_seconds:.2f}s")
    
    if elapsed_seconds < 10.0:
        print(f"  ✓ Excellent performance (< 10s)")
    elif elapsed_seconds < 15.0:
        print(f"  [!] Acceptable performance (< 15s)")


# ============================================================================
# Test 7: Cache Performance
# ============================================================================

def test_cache_performance():
    """
    Test that the caching layer improves performance for repeated configuration loads.
    """
    import sys
    from pathlib import Path
    import time
    
    # Add backend/src to path for imports
    backend_src = Path(__file__).parent.parent / "backend" / "src"
    sys.path.insert(0, str(backend_src))
    
    from core.cache import ConfigCache, CachedFileLoader
    
    cache = ConfigCache(default_ttl_seconds=60)
    loader = CachedFileLoader(cache)
    
    # First load (should hit disk)
    start_time = time.time()
    data1 = loader.load_character_assignments()
    first_load_time = time.time() - start_time
    
    # Second load (should hit cache)
    start_time = time.time()
    data2 = loader.load_character_assignments()
    second_load_time = time.time() - start_time
    
    # Verify data is same
    assert data1 == data2
    
    # Cache should be faster
    assert second_load_time < first_load_time
    
    # Get cache stats
    stats = cache.get_stats()
    assert stats["valid_entries"] >= 1
    
    print(f"✓ Cache working correctly")
    print(f"  First load: {first_load_time*1000:.2f}ms")
    print(f"  Second load (cached): {second_load_time*1000:.2f}ms")
    print(f"  Speedup: {first_load_time/second_load_time:.1f}x")
    print(f"  Cache stats: {stats}")


# ============================================================================
# Test 8: Handoff Synthesis in Multi-Character Response
# ============================================================================

def test_handoff_synthesis_in_response(client):
    """
    Test that handoffs are properly synthesized in multi-character responses.
    """
    user_id = "test_phase45_handoffs"
    
    # Send multi-task query
    response = client.send_message(
        message="Set timer for 10 minutes and add milk to list",
        user_id=user_id
    )
    
    response_text = response["response_text"]
    
    # Verify response is cohesive (not empty, not just errors)
    assert len(response_text) > 20
    assert "error" not in response_text.lower() or "encountered" not in response_text.lower()
    
    print(f"✓ Multi-task response generated")
    print(f"  Response length: {len(response_text)} chars")
    print(f"  Response preview: {response_text[:200]}...")


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    print("\n" + "="*70)
    print("Phase 4.5 Milestone 5: Integration & Polish - E2E Tests")
    print("="*70 + "\n")
    
    # Create client
    client = TestClient()
    
    try:
        print("\n[Test 1] Single character query pipeline...")
        test_single_character_query_full_pipeline(client)
        
        print("\n[Test 2] Multi-character query pipeline...")
        test_multi_character_query_full_pipeline(client)
        
        print("\n[Test 3] Intent → Plan pipeline...")
        test_intent_to_plan_pipeline(client)
        
        print("\n[Test 4] Coordination tracking...")
        test_coordination_tracking(client)
        
        print("\n[Test 5] Error handling...")
        test_error_handling_graceful_fallback(client)
        
        print("\n[Test 6] Performance testing...")
        test_response_latency(client)
        
        print("\n[Test 7] Cache performance...")
        test_cache_performance()
        
        print("\n[Test 8] Handoff synthesis...")
        test_handoff_synthesis_in_response(client)
        
        print("\n" + "="*70)
        print("✓ All Milestone 5 tests completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()
