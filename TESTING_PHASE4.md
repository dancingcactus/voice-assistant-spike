# Phase 4 Testing Guide: Tool System & Function Calling

## Quick Start

**Backend**: http://localhost:8000
**Frontend**: http://localhost:5173
**API Docs**: http://localhost:8000/docs

---

## What You're Testing

Phase 4 adds **function calling** to Delilah, enabling her to:
- ✅ Set, query, and cancel timers
- ✅ Control 10 virtual smart home devices
- ✅ Maintain personality while executing tasks

---

## Test Scenarios

### 1. Timer Tests (Deadpan Mode → Functional)

Delilah should respond in **Deadpan Mode** for timers (flat, efficient tone).

**Test A: Set a Timer**
```
You: "Set a timer for 5 minutes"
Expected:
  - Delilah responds in deadpan: "Timer set. Five minutes."
  - Tool call: manage_timer(action="set", duration_minutes=5)
```

**Test B: Query Timer**
```
You: "How much time is left?"
Expected:
  - Delilah: "Four minutes and thirty seconds left, sugar."
  - Tool call: manage_timer(action="query")
```

**Test C: Cancel Timer**
```
You: "Cancel the timer"
Expected:
  - Delilah: "Timer cancelled."
  - Tool call: manage_timer(action="cancel")
```

**Test D: Labeled Timer**
```
You: "Set a timer for 10 minutes for the pasta"
Expected:
  - Delilah: "Timer set for ten minutes for pasta."
  - Tool call: manage_timer(action="set", duration_minutes=10, label="pasta")
```

---

### 2. Device Control Tests (Deadpan Mode)

Delilah should be efficient and flat when controlling devices.

**Test A: Turn On Light**
```
You: "Turn on the kitchen light"
Expected:
  - Delilah: "Kitchen light on, sugar."
  - Tool call: control_device(device_name="kitchen light", action="turn_on")
```

**Test B: Dim Light**
```
You: "Dim the living room light to 30%"
Expected:
  - Delilah: "Living room light set to 30%."
  - Tool call: control_device(device_name="living room light", action="set_brightness", value=30)
```

**Test C: Set Thermostat**
```
You: "Set the thermostat to 72 degrees"
Expected:
  - Delilah: "Thermostat set to 72."
  - Tool call: control_device(device_name="thermostat", action="set_temperature", value=72)
```

**Test D: Turn Off Light**
```
You: "Turn off the porch light"
Expected:
  - Delilah: "Porch light off."
  - Tool call: control_device(device_name="porch light", action="turn_off")
```

**Test E: Control Fan**
```
You: "Turn on the ceiling fan at high speed"
Expected:
  - Delilah responds efficiently
  - Tool call: control_device(device_name="ceiling fan", action="set_speed", value=3)
```

---

### 3. Voice Mode Tests (Character Consistency During Tool Use)

**Test A: Passionate Mode + Tool Use**
```
You: "Tell me about biscuits, then turn on the kitchen light"
Expected:
  - Delilah starts PASSIONATE about biscuits (high energy, Southern expressions)
  - Switches to DEADPAN for the light command
  - Tool call: control_device(device_name="kitchen light", action="turn_on")
```

**Test B: Protective Mode + Tool Use**
```
You: "Should I microwave this steak? Also set the timer for 2 minutes"
Expected:
  - Delilah is PROTECTIVE/shocked about microwaving steak
  - Still executes the timer (functional)
  - Tool call: manage_timer(action="set", duration_minutes=2)
```

**Test C: Mama Bear Mode + Device Control**
```
You: "I'm allergic to shellfish. Can you turn off the coffee maker?"
Expected:
  - Delilah is MAMA BEAR (soft, protective) about the allergy
  - Executes device control efficiently
  - Tool call: control_device(device_name="coffee maker", action="turn_off")
```

---

### 4. Multi-Step Tool Tests (Circuit Breaker)

**Test A: Multiple Actions in One Request**
```
You: "Set a timer for 10 minutes, turn on the kitchen light, and set the thermostat to 70"
Expected:
  - Delilah executes all three actions
  - 3 tool calls made
  - Natural response confirming all actions
```

**Test B: Complex Query**
```
You: "Turn off all the lights in the kitchen and living room, then set a 5 minute timer"
Expected:
  - Multiple tool calls (up to max 5)
  - Delilah confirms all actions naturally
```

---

### 5. Available Virtual Devices

You can control these 10 virtual devices:

**Lights (dimmable)**:
- Kitchen Light (0-100% brightness)
- Living Room Light (0-100% brightness)

**Lights (on/off only)**:
- Bedroom Light
- Porch Light

**Thermostats** (60-85°F):
- Main Floor Thermostat
- Upstairs Thermostat

**Greenhouse Thermostat** (50-90°F):
- Greenhouse Thermostat

**Other Devices**:
- Coffee Maker (on/off)
- Ceiling Fan (on/off, speed: low/medium/high)
- Garage Door (open/closed)

**Aliases work too**:
- "kitchen" → Kitchen Light
- "downstairs thermostat" → Main Floor Thermostat
- "garage" → Garage Door

---

## What to Look For

### ✅ Success Indicators

1. **Tool Calls Execute**: Check browser console or backend logs for tool calls
2. **Natural Responses**: Delilah responds naturally after executing tools
3. **Character Consistency**: Voice mode changes based on context
4. **Error Handling**: Graceful handling of invalid requests
5. **Circuit Breaker**: Max 5 tool calls per turn (check metadata)

### ❌ Failure Cases

1. **Tool not called**: Delilah talks about the action but doesn't execute it
2. **Wrong personality**: Always deadpan, or wrong voice mode for context
3. **Hallucinated devices**: Claims to control devices that don't exist
4. **Runaway tools**: More than 5 tool calls in one turn
5. **No response**: Blank response after tool execution

---

## Checking Logs

**Backend logs** (see tool execution):
```bash
tail -f /tmp/backend.log | grep -E "tool|Tool"
```

**Frontend console** (browser DevTools):
- Check for WebSocket messages
- Look for tool_calls_made in metadata

---

## Advanced Testing

### Test with Curl (bypass frontend)

```bash
# This won't work directly due to WebSocket, but you can test the conversation manager
# See backend logs for tool execution details
```

### Inspect Device State

Create a test script to check device states:

```bash
cd backend
venv/bin/python -c "
from backend.src.integrations.device_controller import VirtualDeviceController
controller = VirtualDeviceController()
for device in controller.list_devices():
    print(f'{device.name}: {device.state}')
"
```

---

## Expected Behavior Summary

| User Request | Voice Mode | Tool Called | Response Style |
|-------------|-----------|-------------|----------------|
| "Set timer" | Deadpan | manage_timer | Flat, efficient |
| "Turn on light" | Deadpan | control_device | Minimal words |
| "Tell me about biscuits" | Passionate | None | High energy, animated |
| "Microwave steak?" | Protective | None | Shocked, educating |
| "I have allergies" | Mama Bear | None | Soft, nurturing |
| "What's the weather?" | Warm Baseline | None | Friendly, conversational |

---

## Troubleshooting

**Issue**: Delilah doesn't call tools, just talks about the action
**Fix**: Check that tool_system is initialized in websocket.py and tools are registered

**Issue**: Tools execute but no response
**Fix**: Check LLM is getting tool results in follow-up call (see conversation_manager.py logs)

**Issue**: Always deadpan mode
**Fix**: Voice mode selection might be overriding - check character_system.py logs

**Issue**: Circuit breaker hits (5 tool calls)
**Fix**: This is expected for very complex queries - LLM might be looping unnecessarily

---

## Next Steps After Testing

If Phase 4 works well, the next phases are:
- **Phase 5**: Story Engine (narrative progression, story beats)
- **Phase 6**: TTS Integration (ElevenLabs voice synthesis for Delilah's voice)
- **Phase 7**: Final Integration & Polish

Enjoy testing! 🎉
