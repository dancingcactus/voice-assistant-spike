"""
E2E tests for Phase 4.5 Milestone 4: Coordination Tracking.

Tests the coordination event tracking system, including:
- Event logging (handoffs, multi-task, sign-up)
- Metrics calculation
- Milestone detection
- API endpoints
- Integration with DialogueSynthesizer
"""

import pytest
import requests
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
DEBUG_API = f"{BASE_URL}/api/debug"

# Test user IDs
TEST_USER_M4 = "test_milestone4_user"


class TestCoordinationEventLogging:
    """Test basic coordination event logging functionality."""
    
    def test_log_handoff_event(self):
        """Test logging a handoff event."""
        # Import and create tracker
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        from models.coordination import CoordinationEvent
        from datetime import datetime
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        # Log a handoff event
        tracker.log_handoff(
            user_id=TEST_USER_M4,
            from_character="delilah",
            to_character="hank",
            intent="household",
            template_used="delilah_to_hank_1",
            success=True,
            metadata={"query": "Set timer and add flour to list"}
        )
        
        # Verify event was logged
        events = tracker.get_recent_events(TEST_USER_M4, limit=1)
        assert len(events) == 1
        assert events[0].event_type == "handoff"
        assert events[0].from_character == "delilah"
        assert events[0].to_character == "hank"
        assert events[0].intent == "household"
        assert events[0].success is True
        
        print("✓ Handoff event logged successfully")
    
    def test_log_multi_task_event(self):
        """Test logging a multi-task completion event."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        # Log a multi-task event
        tracker.log_multi_task(
            user_id=TEST_USER_M4,
            query="Set timer and add eggs to shopping list",
            characters_involved=["delilah", "hank"],
            success=True
        )
        
        # Verify event was logged
        events = tracker.get_recent_events(TEST_USER_M4, event_type="multi_task")
        assert len(events) >= 1
        latest_event = events[0]
        assert latest_event.event_type == "multi_task"
        assert "delilah" in latest_event.metadata["characters_involved"]
        assert "hank" in latest_event.metadata["characters_involved"]
        
        print("✓ Multi-task event logged successfully")
    
    def test_log_sign_up_event(self):
        """Test logging a sign-up pattern event."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        # Log a sign-up event
        tracker.log_sign_up(
            user_id=TEST_USER_M4,
            characters=["delilah", "hank"],
            intents=["cooking", "household"]
        )
        
        # Verify event was logged
        events = tracker.get_recent_events(TEST_USER_M4, event_type="sign_up")
        assert len(events) >= 1
        latest_event = events[0]
        assert latest_event.event_type == "sign_up"
        
        print("✓ Sign-up event logged successfully")


class TestCoordinationMetrics:
    """Test metrics calculation from coordination events."""
    
    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly from events."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        # Log multiple events
        test_user = "test_metrics_user"
        
        # Log 3 delilah->hank handoffs
        for i in range(3):
            tracker.log_handoff(
                user_id=test_user,
                from_character="delilah",
                to_character="hank",
                intent="household",
                template_used=f"delilah_to_hank_{i}",
                success=True
            )
        
        # Log 2 hank->delilah handoffs
        for i in range(2):
            tracker.log_handoff(
                user_id=test_user,
                from_character="hank",
                to_character="delilah",
                intent="cooking",
                template_used=f"hank_to_delilah_{i}",
                success=True
            )
        
        # Get metrics
        metrics = tracker.get_metrics(test_user)
        
        # Verify counts
        assert metrics.total_handoffs == 5
        assert metrics.delilah_to_hank_count == 3
        assert metrics.hank_to_delilah_count == 2
        assert metrics.handoff_success_rate == 1.0
        
        # Verify template tracking
        assert len(metrics.template_usage) == 5
        
        print("✓ Metrics calculated correctly")
        print(f"  Total handoffs: {metrics.total_handoffs}")
        print(f"  Delilah→Hank: {metrics.delilah_to_hank_count}")
        print(f"  Hank→Delilah: {metrics.hank_to_delilah_count}")
        print(f"  Success rate: {metrics.handoff_success_rate * 100:.0f}%")


class TestCoordinationMilestones:
    """Test milestone detection logic."""
    
    def test_first_handoff_milestone(self):
        """Test that first handoff milestone is detected."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        test_user = "test_first_handoff"
        
        # Check initial state
        milestones = tracker.get_milestones(test_user)
        assert milestones["first_handoff"] is False
        
        # Log first handoff
        tracker.log_handoff(
            user_id=test_user,
            from_character="delilah",
            to_character="hank",
            intent="household",
            success=True
        )
        
        # Check milestone achieved
        milestones = tracker.get_milestones(test_user)
        assert milestones["first_handoff"] is True
        
        print("✓ First handoff milestone detected")
    
    def test_five_handoffs_milestone(self):
        """Test that five handoffs milestone is detected."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        test_user = "test_five_handoffs"
        
        # Log 5 handoffs
        for i in range(5):
            tracker.log_handoff(
                user_id=test_user,
                from_character="delilah",
                to_character="hank",
                intent="household",
                success=True
            )
        
        # Check milestone achieved
        milestones = tracker.get_milestones(test_user)
        assert milestones["first_handoff"] is True
        assert milestones["five_handoffs"] is True
        
        print("✓ Five handoffs milestone detected")
    
    def test_first_multi_task_milestone(self):
        """Test that first multi-task milestone is detected."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        
        test_user = "test_first_multi_task"
        
        # Check initial state
        milestones = tracker.get_milestones(test_user)
        assert milestones["first_multi_task"] is False
        
        # Log multi-task completion
        tracker.log_multi_task(
            user_id=test_user,
            query="Set timer and add flour",
            characters_involved=["delilah", "hank"],
            success=True
        )
        
        # Check milestone achieved
        milestones = tracker.get_milestones(test_user)
        assert milestones["first_multi_task"] is True
        
        print("✓ First multi-task milestone detected")


class TestCoordinationAPI:
    """Test coordination tracking API endpoints."""
    
    def test_get_coordination_metrics_endpoint(self):
        """Test GET /api/debug/coordination/metrics/{user_id} endpoint."""
        test_user = "test_api_metrics"
        
        response = requests.get(f"{DEBUG_API}/coordination/metrics/{test_user}")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "metrics" in data
        assert data["user_id"] == test_user
        
        metrics = data["metrics"]
        assert "total_handoffs" in metrics
        assert "handoff_success_rate" in metrics
        assert "delilah_to_hank_count" in metrics
        
        print("✓ Metrics API endpoint working")
        print(f"  Response: {metrics}")
    
    def test_get_coordination_events_endpoint(self):
        """Test GET /api/debug/coordination/events/{user_id} endpoint."""
        test_user = TEST_USER_M4
        
        response = requests.get(
            f"{DEBUG_API}/coordination/events/{test_user}",
            params={"limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "events" in data
        assert "total_count" in data
        assert data["user_id"] == test_user
        
        print("✓ Events API endpoint working")
        print(f"  Returned {data['total_count']} events")
    
    def test_get_coordination_milestones_endpoint(self):
        """Test GET /api/debug/coordination/milestones/{user_id} endpoint."""
        test_user = TEST_USER_M4
        
        response = requests.get(f"{DEBUG_API}/coordination/milestones/{test_user}")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "milestones" in data
        assert data["user_id"] == test_user
        
        milestones = data["milestones"]
        assert "first_handoff" in milestones
        assert "first_multi_task" in milestones
        assert "five_handoffs" in milestones
        
        print("✓ Milestones API endpoint working")
        print(f"  Milestones: {milestones}")
    
    def test_filter_events_by_type(self):
        """Test filtering events by type."""
        test_user = TEST_USER_M4
        
        response = requests.get(
            f"{DEBUG_API}/coordination/events/{test_user}",
            params={"limit": 10, "event_type": "handoff"}
        )
        assert response.status_code == 200
        
        data = response.json()
        events = data["events"]
        
        # All events should be handoffs
        for event in events:
            assert event["event_type"] == "handoff"
        
        print("✓ Event filtering working")


class TestDialogueSynthesizerIntegration:
    """Test integration of coordination tracking with DialogueSynthesizer."""
    
    def test_handoff_tracking_in_dialogue(self):
        """Test that handoffs are automatically tracked during dialogue synthesis."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.dialogue_synthesizer import DialogueSynthesizer
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        tracker = CoordinationTracker(memory_manager=memory_manager)
        synthesizer = DialogueSynthesizer(coordination_tracker=tracker)
        
        test_user = "test_dialogue_integration"
        
        # Get initial event count
        initial_events = tracker.get_recent_events(test_user)
        initial_count = len(initial_events)
        
        # Synthesize a handoff (should automatically log event)
        handoff = synthesizer.synthesize_handoff(
            from_character="delilah",
            to_character="hank",
            user_id=test_user,
            intent="household"
        )
        
        assert len(handoff) > 0
        
        # Verify event was logged
        events = tracker.get_recent_events(test_user)
        assert len(events) == initial_count + 1
        
        latest_event = events[0]
        assert latest_event.event_type == "handoff"
        assert latest_event.from_character == "delilah"
        assert latest_event.to_character == "hank"
        
        print("✓ Handoff automatically tracked during dialogue synthesis")
        print(f"  Handoff text: {handoff}")


class TestPersistence:
    """Test that coordination data persists across sessions."""
    
    def test_coordination_data_persists(self):
        """Test that coordination events persist to user state file."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
        
        from core.coordination_tracker import CoordinationTracker
        from core.memory_manager import MemoryManager
        
        test_user = "test_persistence"
        
        # Create first tracker instance and log events
        memory_manager1 = MemoryManager()
        tracker1 = CoordinationTracker(memory_manager=memory_manager1)
        
        tracker1.log_handoff(
            user_id=test_user,
            from_character="delilah",
            to_character="hank",
            intent="household",
            success=True
        )
        
        # Force save
        memory_manager1.save_user_state(test_user, force=True)
        
        # Create new tracker instance (simulates restart)
        memory_manager2 = MemoryManager()
        tracker2 = CoordinationTracker(memory_manager=memory_manager2)
        
        # Verify data persisted
        events = tracker2.get_recent_events(test_user)
        assert len(events) >= 1
        
        metrics = tracker2.get_metrics(test_user)
        assert metrics.total_handoffs >= 1
        
        print("✓ Coordination data persists across sessions")


if __name__ == "__main__":
    print("Running Phase 4.5 Milestone 4 Coordination Tracking Tests")
    print("=" * 70)
    
    # Run tests
    test_classes = [
        TestCoordinationEventLogging,
        TestCoordinationMetrics,
        TestCoordinationMilestones,
        TestCoordinationAPI,
        TestDialogueSynthesizerIntegration,
        TestPersistence
    ]
    
    for test_class in test_classes:
        print(f"\n{test_class.__doc__}")
        print("-" * 70)
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                method = getattr(instance, method_name)
                try:
                    method()
                except AssertionError as e:
                    print(f"✗ {method.__doc__} FAILED: {e}")
                except Exception as e:
                    print(f"✗ {method.__doc__} ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("All milestone 4 tests completed!")
