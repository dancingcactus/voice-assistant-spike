"""
Generate sample tool call data for testing the Tool Calls Inspection feature.
"""

import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from datetime import datetime, timedelta
import random
import uuid

from observability.tool_call_access import ToolCallDataAccess
from observability.tool_call_models import ToolCallLog, ToolCallStatus


# Sample tool definitions
TOOLS = {
    "set_timer": {
        "sample_requests": [
            {"duration_minutes": 5, "label": "test timer"},
            {"duration_minutes": 10, "label": "pasta"},
            {"duration_minutes": 15, "label": "meditation"},
            {"duration_minutes": 30, "label": "laundry"},
        ],
        "sample_responses": [
            {"timer_id": "timer_001", "end_time": "2025-01-27T10:15:00", "status": "started"},
            {"timer_id": "timer_002", "end_time": "2025-01-27T10:20:00", "status": "started"},
        ],
        "success_rate": 1.0,
        "avg_duration_ms": (180, 250),
    },
    "get_recipe": {
        "sample_requests": [
            {"query": "chocolate chip cookies gluten free"},
            {"query": "pasta carbonara"},
            {"query": "thai curry"},
            {"query": "chicken soup"},
        ],
        "sample_responses": [
            {"recipe_id": "rec_001", "title": "Gluten-Free Chocolate Chip Cookies", "ingredients": ["almond flour", "chocolate chips", "butter"]},
            {"recipe_id": "rec_002", "title": "Classic Pasta Carbonara", "ingredients": ["pasta", "eggs", "parmesan", "bacon"]},
        ],
        "success_rate": 0.95,
        "avg_duration_ms": (400, 650),
    },
    "light_control": {
        "sample_requests": [
            {"device": "kitchen_lights", "action": "turn_on", "brightness": 100},
            {"device": "bedroom_lights", "action": "turn_off"},
            {"device": "living_room_lights", "action": "set_brightness", "brightness": 50},
        ],
        "sample_responses": [
            {"status": "success", "device": "kitchen_lights", "state": "on", "brightness": 100},
            {"status": "success", "device": "bedroom_lights", "state": "off"},
        ],
        "success_rate": 0.90,
        "avg_duration_ms": (150, 300),
    },
    "get_calendar_events": {
        "sample_requests": [
            {"date": "today"},
            {"date": "tomorrow"},
            {"date_range": {"start": "2025-01-27", "end": "2025-01-29"}},
        ],
        "sample_responses": [
            {"events": [{"title": "Team meeting", "time": "10:00 AM"}, {"title": "Dentist", "time": "2:00 PM"}]},
            {"events": []},
        ],
        "success_rate": 0.98,
        "avg_duration_ms": (300, 500),
    },
    "unit_conversion": {
        "sample_requests": [
            {"value": 2, "from_unit": "cups", "to_unit": "ml"},
            {"value": 350, "from_unit": "fahrenheit", "to_unit": "celsius"},
            {"value": 1.5, "from_unit": "pounds", "to_unit": "grams"},
        ],
        "sample_responses": [
            {"result": 473.176, "unit": "ml"},
            {"result": 176.67, "unit": "celsius"},
        ],
        "success_rate": 1.0,
        "avg_duration_ms": (80, 150),
    },
}

CHARACTERS = ["Delilah", "Hank", "Cave"]

CHARACTER_TOOL_PREFERENCES = {
    "Delilah": ["get_recipe", "set_timer", "unit_conversion"],
    "Hank": ["light_control", "set_timer"],
    "Cave": ["get_calendar_events", "light_control"],
}


def generate_tool_calls(user_id: str, count: int = 50):
    """Generate sample tool call logs"""
    data_dir = Path(__file__).parent.parent / "data"
    tool_call_dal = ToolCallDataAccess(data_dir=str(data_dir))

    print(f"Generating {count} sample tool calls for {user_id}...")

    now = datetime.now()

    for i in range(count):
        # Generate timestamp (distributed over last 7 days)
        hours_ago = random.uniform(0, 168)  # 7 days * 24 hours
        timestamp = now - timedelta(hours=hours_ago)

        # Pick character
        character = random.choice(CHARACTERS)

        # Pick tool (weighted by character preference)
        preferred_tools = CHARACTER_TOOL_PREFERENCES.get(character, list(TOOLS.keys()))
        if random.random() < 0.8:  # 80% use preferred tools
            tool_name = random.choice(preferred_tools)
        else:
            tool_name = random.choice(list(TOOLS.keys()))

        tool_def = TOOLS[tool_name]

        # Determine success/failure
        success = random.random() < tool_def["success_rate"]
        status = ToolCallStatus.SUCCESS if success else ToolCallStatus.ERROR

        # Generate request
        request = random.choice(tool_def["sample_requests"])

        # Generate response
        if success:
            response = random.choice(tool_def["sample_responses"])
        else:
            response = {
                "error": "Device not found" if tool_name == "light_control" else "Operation failed",
                "status": "error"
            }

        # Generate duration
        duration_range = tool_def["avg_duration_ms"]
        duration_ms = random.randint(duration_range[0], duration_range[1])

        # Optional: some calls are slower
        if random.random() < 0.05:  # 5% are slow
            duration_ms = random.randint(2000, 5000)

        # Create log entry
        log_entry = ToolCallLog(
            call_id=f"call_{uuid.uuid4().hex[:12]}",
            timestamp=timestamp,
            duration_ms=duration_ms,
            tool_name=tool_name,
            character=character,
            user_id=user_id,
            request=request,
            response=response,
            status=status,
            error_message=response.get("error") if not success else None,
            reasoning=generate_reasoning(character, tool_name) if random.random() < 0.3 else None,
        )

        # Save to JSONL
        tool_call_dal.append_tool_call(log_entry)

    print(f"✅ Generated {count} tool calls successfully")
    print(f"📁 Saved to: {data_dir}/tool_logs/{user_id}_tool_calls.jsonl")


def generate_reasoning(character: str, tool_name: str) -> str:
    """Generate sample reasoning text"""
    reasoning_templates = {
        "Delilah": [
            f"User needs help with {tool_name}, bless their heart",
            "This looks like a good opportunity to assist",
            "I should handle this one",
        ],
        "Hank": [
            f"Aye, I'll handle the {tool_name}",
            "Got it, Cap'n",
            "Right away",
        ],
        "Cave": [
            f"SCIENCE demands we execute {tool_name}!",
            "This is exactly what we're built for!",
            "Let's make this happen!",
        ]
    }

    templates = reasoning_templates.get(character, ["Processing user request"])
    return random.choice(templates)


if __name__ == "__main__":
    # Generate for user_justin
    generate_tool_calls("user_justin", count=50)

    print("\n✅ Sample data generation complete!")
    print("\nYou can now:")
    print("1. Start the API server: python -m uvicorn observability.api:app --reload")
    print("2. Query tool calls: curl -H 'Authorization: Bearer dev_token_12345' 'http://localhost:8000/tool-calls?user_id=user_justin'")
    print("3. View stats: curl -H 'Authorization: Bearer dev_token_12345' 'http://localhost:8000/tool-calls/stats?user_id=user_justin'")
