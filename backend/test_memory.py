#!/usr/bin/env python3
"""
Test script for Phase 7: Memory & State
Tests all acceptance criteria from the project plan
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.memory_manager import MemoryManager
from core.story_engine import StoryEngine
from models.message import Message


async def test_preferences_persistence():
    """Test that user preferences persist across sessions."""
    print("\n" + "="*60)
    print("TEST 1: User Preferences Persistence")
    print("="*60)

    # Create first memory manager instance
    mm1 = MemoryManager(data_dir="data")

    # Add allergy
    mm1.add_user_preference("test_user_prefs", "dietary_restrictions", "peanuts")
    mm1.save_user_state("test_user_prefs", force=True)
    print("✅ Added peanut allergy and saved")

    # Create new instance (simulating restart)
    mm2 = MemoryManager(data_dir="data")
    user_state = mm2.load_user_state("test_user_prefs")

    if "peanuts" in user_state.preferences.dietary_restrictions:
        print("✅ PASS: Preference persisted across 'restart'")
        return True
    else:
        print("❌ FAIL: Preference not found after restart")
        return False


async def test_story_state_persistence():
    """Test that story progress persists across sessions."""
    print("\n" + "="*60)
    print("TEST 2: Story State Persistence")
    print("="*60)

    # Create memory manager and story engine
    mm = MemoryManager(data_dir="data")
    story_dir = Path(__file__).parent.parent / "story"
    story_engine = StoryEngine(story_dir=str(story_dir), memory_manager=mm)

    # Simulate delivering a beat
    user_id = "test_story_user"
    state = story_engine.get_or_create_user_state(user_id)

    print(f"Initial state: Chapter {state.current_chapter}, Interactions: {state.total_interactions}")

    # Mark a beat as delivered
    story_engine.mark_beat_stage_delivered(user_id, "awakening_confusion", 1)
    print("✅ Marked 'awakening_confusion' beat as delivered")

    # Create new story engine (simulating restart)
    story_engine2 = StoryEngine(story_dir=str(story_dir), memory_manager=mm)
    state2 = story_engine2.get_or_create_user_state(user_id)

    # Check if beat was persisted in chapter progress
    beat_found = False
    if state2.current_chapter in state2.chapter_progress:
        chapter_prog = state2.chapter_progress[state2.current_chapter]
        if "awakening_confusion" in chapter_prog.beat_progress:
            beat_found = True

    if beat_found:
        print("✅ PASS: Story beat persisted across 'restart'")
        return True
    else:
        print("❌ FAIL: Story beat not found after restart")
        print(f"   Chapters: {list(state2.chapter_progress.keys())}")
        if state2.chapter_progress:
            for ch_id, ch_prog in state2.chapter_progress.items():
                print(f"   Chapter {ch_id} beats: {list(ch_prog.beat_progress.keys())}")
        return False


async def test_conversation_history():
    """Test that conversation history is maintained for 30 minutes."""
    print("\n" + "="*60)
    print("TEST 3: Conversation History Management")
    print("="*60)

    mm = MemoryManager(data_dir="data")
    user_id = "test_conv_user"

    # Add some messages
    for i in range(5):
        msg = Message(role="user", content=f"Message {i}", timestamp=datetime.now())
        mm.add_conversation_message(user_id, msg, "user")

    print("✅ Added 5 messages")

    # Get history
    history = mm.get_conversation_history(user_id)
    print(f"✅ Retrieved {len(history)} messages from history")

    if len(history) == 5:
        print("✅ PASS: All messages retrieved")
        return True
    else:
        print(f"❌ FAIL: Expected 5 messages, got {len(history)}")
        return False


async def test_device_state_persistence():
    """Test that device states persist across restarts."""
    print("\n" + "="*60)
    print("TEST 4: Device State Persistence")
    print("="*60)

    # Create first memory manager
    mm1 = MemoryManager(data_dir="data")

    # Set device state
    mm1.update_device_state(
        "test_device_user",
        "kitchen_light",
        "light",
        {"on": True, "brightness": 50}
    )
    mm1.save_user_state("test_device_user", force=True)
    print("✅ Set kitchen light to on, 50% brightness and saved")

    # Create new instance (simulating restart)
    mm2 = MemoryManager(data_dir="data")
    device_state = mm2.get_device_state("test_device_user", "kitchen_light")

    if device_state and device_state.state["on"] and device_state.state["brightness"] == 50:
        print("✅ PASS: Device state persisted across 'restart'")
        return True
    else:
        print("❌ FAIL: Device state not correct after restart")
        return False


async def test_interaction_count():
    """Test that interaction count increments and persists."""
    print("\n" + "="*60)
    print("TEST 5: Interaction Count Tracking")
    print("="*60)

    mm = MemoryManager(data_dir="data")
    user_id = "test_interaction_user"

    # Load initial state
    state1 = mm.load_user_state(user_id)
    initial_count = state1.story_progress.interaction_count
    print(f"Initial interaction count: {initial_count}")

    # Increment 5 times
    for _ in range(5):
        mm.increment_interaction_count(user_id)

    mm.save_user_state(user_id, force=True)
    print("✅ Incremented 5 times and saved")

    # Reload
    mm2 = MemoryManager(data_dir="data")
    state2 = mm2.load_user_state(user_id)
    new_count = state2.story_progress.interaction_count

    if new_count == initial_count + 5:
        print(f"✅ PASS: Count incremented correctly ({initial_count} → {new_count})")
        return True
    else:
        print(f"❌ FAIL: Expected {initial_count + 5}, got {new_count}")
        return False


async def test_periodic_flush():
    """Test that periodic flush works."""
    print("\n" + "="*60)
    print("TEST 6: Periodic Flush")
    print("="*60)

    mm = MemoryManager(data_dir="data")
    mm._flush_interval = 1  # Set to 1 second for testing

    # Start periodic flush
    await mm.start_periodic_flush()
    print("✅ Started periodic flush (1 second interval)")

    # Add a preference (marks as dirty)
    mm.add_user_preference("test_flush_user", "favorite_foods", "biscuits")
    print("✅ Added preference (user marked as dirty)")

    # Wait for flush
    await asyncio.sleep(2)
    print("✅ Waited 2 seconds for flush")

    # Stop flush
    mm.stop_periodic_flush()

    # Check if file exists
    user_file = Path("data/users/test_flush_user.json")
    if user_file.exists():
        print("✅ PASS: User file was flushed to disk")
        return True
    else:
        print("❌ FAIL: User file not found after periodic flush")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🧪 Phase 7: Memory & State - Acceptance Tests" + "\n")

    results = []

    results.append(await test_preferences_persistence())
    results.append(await test_story_state_persistence())
    results.append(await test_conversation_history())
    results.append(await test_device_state_persistence())
    results.append(await test_interaction_count())
    results.append(await test_periodic_flush())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED! Phase 7 is complete.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
