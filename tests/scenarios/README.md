# Test Scenarios

This directory contains test scenarios for automated validation of the Aperture Assist system.

## Scenario Structure

Test scenarios are JSON files with the following structure:

```json
{
  "name": "scenario_name",
  "description": "What this scenario tests",
  "initial_state": {
    "current_chapter": 1,
    "beats_delivered": [],
    "interaction_count": 0,
    "preferences": {},
    "device_states": {}
  },
  "conversation_flow": [
    {
      "step": 1,
      "user_message": "User input",
      "expected_behavior": {
        "contains_text": ["keyword1", "keyword2"],
        "voice_mode": "passionate",
        "tool_calls": ["timer_set"],
        "state_changes": {
          "interaction_count": 1
        }
      }
    }
  ],
  "success_criteria": [
    "Delilah responds in passionate mode",
    "Timer is set correctly",
    "State persists across interactions"
  ]
}
```

## Scenario Types

### Story Scenarios (`story/`)

Test story progression, beat delivery, and chapter unlocks.

### Character Scenarios (`character/`)

Test character consistency, voice modes, and personality.

### Tool Scenarios (`tools/`)

Test tool execution (timers, devices, recipes).

### Edge Case Scenarios (`edge-cases/`)

Test error handling, edge cases, and recovery.

## Running Scenarios

Use the Test API to load and validate scenarios:

```bash
# Load a scenario
curl -X POST http://localhost:8000/api/test/scenario \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "chapter1_first_interaction",
    "user_id": "test-user"
  }'

# Run conversation steps
curl -X POST http://localhost:8000/api/test/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "message": "Hello",
    "include_state": true
  }'

# Check state
curl http://localhost:8000/api/test/state/test-user

# Reset state
curl -X POST http://localhost:8000/api/test/reset/test-user
```

## Automated Test Runners

(To be implemented in future phases)

Test runners can:

- Load scenarios from JSON
- Execute conversation flows
- Validate responses against expectations
- Generate test reports
