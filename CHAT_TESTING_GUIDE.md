# Chat Interface Testing Guide

## Overview

The chat interface at http://localhost:5173/ has **two working tools** that you can test:

1. **Timer Tool** (`manage_timer`) - Set, query, and cancel kitchen timers
2. **Device Control Tool** (`control_device`) - Control virtual smart home devices

## Available Tools

### 1. Timer Tool

**What it does**: Manages kitchen timers

**Test Commands**:
```
Set a timer for 5 minutes
Set a timer for 10 minutes for pasta
How much time is left on my timer?
Cancel the pasta timer
Cancel all timers
```

**Actions**:
- **Set**: Creates a new timer with optional label
- **Query**: Shows remaining time on active timers
- **Cancel**: Cancels specific timer or all timers

**Example Conversation**:
```
You: Set a timer for 3 minutes
Assistant: Timer set for 3 minutes

You: Set another timer for 10 minutes for bread
Assistant: Timer set for 10 minutes for bread

You: How much time is left?
Assistant: You have 2 active timers:
  - Timer: 2 minutes 45 seconds remaining
  - Bread timer: 9 minutes 45 seconds remaining

You: Cancel the bread timer
Assistant: Cancelled timer for bread
```

---

### 2. Device Control Tool

**What it does**: Controls virtual smart home devices

**Available Devices**:

#### Lights (with on/off and brightness)
- Kitchen Light
- Living Room Light
- Bedroom Light (on/off only)
- Porch Light (on/off only)

#### Thermostats (temperature control)
- Main Floor Thermostat (currently 68°F, target 70°F)
- Upstairs Thermostat (currently 65°F, target 72°F)

#### Switches
- Coffee Maker
- Lamp

#### Doors
- Garage Door

#### Fans (with speed control)
- Bedroom Fan
- Living Room Fan

**Test Commands**:

#### Lights
```
Turn on the kitchen light
Turn off the bedroom light
Set the living room light to 50%
Set the kitchen light brightness to 75
Dim the porch light to 20%
```

#### Thermostats
```
Set the main floor thermostat to 72 degrees
Set the upstairs thermostat to 68
What's the temperature upstairs?
Increase the thermostat to 75
```

#### Switches
```
Turn on the coffee maker
Turn off the lamp
```

#### Doors
```
Open the garage door
Close the garage door
```

#### Fans
```
Turn on the bedroom fan
Set the living room fan to speed 2
Turn off the fan
```

**Example Conversations**:

```
You: Turn on the kitchen light
Assistant: Turned on Kitchen Light

You: Set it to 50% brightness
Assistant: Set Kitchen Light brightness to 50%

You: Turn it off
Assistant: Turned off Kitchen Light
```

```
You: Set the thermostat to 72
Assistant: Set Main Floor Thermostat to 72°F

You: Open the garage door
Assistant: Opened Garage Door
```

---

## Testing Tips

### 1. Natural Language
The system should understand natural variations:
- "Turn on the kitchen light" = "Kitchen light on" = "Lights in kitchen"
- "Set a timer for 5 minutes" = "5 minute timer" = "Timer 5 min"

### 2. Context Awareness
Try follow-up commands:
```
You: Turn on the kitchen light
Assistant: [turns on light]

You: Set it to 50%
Assistant: [should understand "it" refers to kitchen light]
```

### 3. Multiple Actions
Try complex requests:
```
You: Turn on the kitchen and living room lights
You: Set all the thermostats to 70 degrees
```

### 4. Error Handling
Try invalid requests to test error handling:
```
You: Turn on the basement light (doesn't exist)
You: Set a timer for -5 minutes (invalid)
You: Set the thermostat to 150 (out of range)
```

### 5. State Queries
Ask about current state:
```
You: What timers are running?
You: What's the temperature set to?
You: Are the lights on in the kitchen?
```

---

## Checking Tool Calls in Dashboard

After testing, you can view the tool call logs:

1. Go to http://localhost:5173/observability
2. Click **"Tool Calls"** in the navigation
3. See your recent tool calls with:
   - Tool name and parameters
   - Success/failure status
   - Duration
   - Full request/response data

This lets you:
- Debug what parameters were sent
- See how the LLM interpreted your request
- Check timing and performance
- Identify any errors

---

## What to Look For

### ✅ Good Behavior
- Assistant understands natural language variations
- Tools execute correctly
- Response includes confirmation of action
- Multiple device names recognized (aliases work)
- Follow-up context works ("it", "that one")

### ❌ Issues to Report
- Tool not called when it should be
- Wrong parameters passed to tool
- Assistant ignores device names
- Errors in tool execution
- Confusing or unhelpful responses

---

## Advanced Testing

### Conversation Flow
```
You: Set a timer for 5 minutes for eggs
Assistant: [sets timer]

You: Also turn on the kitchen light
Assistant: [controls light]

You: How much time left on the timer?
Assistant: [queries timer]

You: Cancel it, the eggs are done
Assistant: [cancels timer]

You: Turn off the light
Assistant: [controls light]
```

### Edge Cases
```
You: Set 3 timers - 5 minutes for eggs, 10 for pasta, and 15 for bread
You: Turn on all the lights in the house
You: Set both thermostats to 70 degrees
You: Open the garage then turn on the porch light
```

---

## Known Limitations

1. **No Audio**: Voice input/output not yet implemented (text only for now)
2. **Virtual Devices**: These are simulated devices, not real hardware
3. **No Persistence**: Timer state is lost if server restarts
4. **Basic Context**: May not remember device names from many messages ago

---

## Troubleshooting

### Chat not connecting
**Problem**: WebSocket connection fails
**Check**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"development"}
```

### Tool not being called
**Check observability dashboard**:
1. Go to http://localhost:5173/observability
2. Click "Tool Calls"
3. See if tool was called but failed
4. Check request/response data

### Frontend errors
**Check browser console** (F12 → Console tab)
- Look for JavaScript errors
- Check network tab for failed requests

---

## Example Testing Session

```
# Test timers
Set a timer for 3 minutes
Set a timer for 10 minutes for pasta
How much time is left?
Cancel the pasta timer

# Test lights
Turn on the kitchen light
Set the brightness to 75%
Turn off the kitchen light
Turn on all the lights

# Test thermostat
Set the main floor thermostat to 72
What's the temperature?

# Test combinations
Turn on the kitchen light and set a timer for 5 minutes
Open the garage door and turn on the porch light

# Test context
Turn on the living room light
Set it to 50% brightness
Turn it off

# Check in observability dashboard
Go to http://localhost:5173/observability
Click "Tool Calls"
See all your test calls with timing and data
```

---

## Next Steps

After testing:
1. Note any issues or confusing behavior
2. Check tool call logs in observability dashboard
3. Try voice input (if available in your setup)
4. Test with different phrasings and variations
5. Report any bugs or unexpected behavior

Happy testing! 🎉
