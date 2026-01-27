#!/usr/bin/env python3
"""
Interactive test for Phase 7: Memory & State
Run this to manually explore the memory system
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.memory_manager import MemoryManager
from models.message import Message


async def main():
    print("\n" + "="*60)
    print("🧪 Phase 7: Memory & State - Interactive Test")
    print("="*60)

    mm = MemoryManager(data_dir="data")
    user_id = "interactive_test_user"

    # Load current state
    state = mm.load_user_state(user_id)

    print(f"\n📊 Current State for '{user_id}':")
    print(f"  • Chapter: {state.story_progress.current_chapter}")
    print(f"  • Interactions: {state.story_progress.interaction_count}")
    print(f"  • Dietary restrictions: {state.preferences.dietary_restrictions}")
    print(f"  • Favorite foods: {state.preferences.favorite_foods}")
    print(f"  • Conversation messages: {len(state.conversation_history.messages)}")
    print(f"  • Devices tracked: {len(state.device_preferences.devices)}")

    while True:
        print("\n" + "-"*60)
        print("What would you like to test?")
        print("  1. Add dietary restriction")
        print("  2. Add favorite food")
        print("  3. Add conversation message")
        print("  4. Update device state")
        print("  5. Increment interaction count")
        print("  6. View full state")
        print("  7. Save and reload (test persistence)")
        print("  8. View conversation history")
        print("  9. Clear all data (reset user)")
        print("  0. Exit")

        choice = input("\nEnter choice (0-9): ").strip()

        if choice == "1":
            restriction = input("Enter dietary restriction (e.g., 'peanuts', 'dairy'): ").strip()
            if restriction:
                mm.add_user_preference(user_id, "dietary_restrictions", restriction)
                print(f"✅ Added restriction: {restriction}")

        elif choice == "2":
            food = input("Enter favorite food: ").strip()
            if food:
                mm.add_user_preference(user_id, "favorite_foods", food)
                print(f"✅ Added favorite: {food}")

        elif choice == "3":
            text = input("Enter message text: ").strip()
            if text:
                role = input("Role (user/assistant) [default: user]: ").strip() or "user"
                msg = Message(role=role, content=text, timestamp=datetime.now())
                mm.add_conversation_message(user_id, msg, role)
                print(f"✅ Added {role} message")

        elif choice == "4":
            device_id = input("Device ID (e.g., 'kitchen_light'): ").strip()
            if device_id:
                device_type = input("Device type (light/switch/thermostat): ").strip() or "light"

                if device_type == "light":
                    on = input("On? (y/n): ").strip().lower() == 'y'
                    brightness = int(input("Brightness (0-100): ").strip() or "50")
                    state_dict = {"on": on, "brightness": brightness}
                elif device_type == "thermostat":
                    temp = float(input("Temperature (°F): ").strip() or "72")
                    state_dict = {"temperature": temp, "mode": "heat"}
                else:
                    on = input("On? (y/n): ").strip().lower() == 'y'
                    state_dict = {"on": on}

                mm.update_device_state(user_id, device_id, device_type, state_dict)
                mm.save_user_state(user_id, force=True)
                print(f"✅ Updated {device_id}: {state_dict}")

        elif choice == "5":
            count = int(input("How many interactions to add? [default: 1]: ").strip() or "1")
            for _ in range(count):
                mm.increment_interaction_count(user_id)
            mm.save_user_state(user_id, force=True)
            new_state = mm.load_user_state(user_id)
            print(f"✅ Interactions: {new_state.story_progress.interaction_count}")

        elif choice == "6":
            import json
            state = mm.load_user_state(user_id)
            data = state.model_dump()

            # Convert datetime objects for display
            def serialize_for_display(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_for_display(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_for_display(i) for i in obj]
                else:
                    return obj

            data = serialize_for_display(data)
            print("\n" + json.dumps(data, indent=2))

        elif choice == "7":
            print("Saving state...")
            mm.save_user_state(user_id, force=True)
            print("✅ State saved to disk")

            print("Creating new Memory Manager instance...")
            mm = MemoryManager(data_dir="data")
            state = mm.load_user_state(user_id)
            print("✅ State reloaded from disk")
            print(f"  • Chapter: {state.story_progress.current_chapter}")
            print(f"  • Interactions: {state.story_progress.interaction_count}")
            print(f"  • Dietary restrictions: {state.preferences.dietary_restrictions}")
            print(f"  • Messages: {len(state.conversation_history.messages)}")

        elif choice == "8":
            history = mm.get_conversation_history(user_id)
            print(f"\n📜 Conversation History ({len(history)} messages):")
            for i, msg in enumerate(history[-10:], 1):  # Show last 10
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                print(f"  {i}. [{timestamp}] {msg.role}: {msg.content[:50]}...")

        elif choice == "9":
            confirm = input("⚠️  Are you sure? This will delete all data for this user (y/n): ")
            if confirm.strip().lower() == 'y':
                mm.reset_user_state(user_id)
                state = mm.load_user_state(user_id)
                print("✅ User state reset")
            else:
                print("Cancelled")

        elif choice == "0":
            # Save before exit
            mm.save_user_state(user_id, force=True)
            print("\n✅ State saved. Goodbye!")
            break
        else:
            print("❌ Invalid choice")

    print()


if __name__ == "__main__":
    asyncio.run(main())
