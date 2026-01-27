# Manual Testing Script - Phase 7: Memory & State

This is a step-by-step guide for manually testing the complete system. Follow along and check off each step!

---

## Setup (2 minutes)

### Step 1: Start the Backend
```bash
# Terminal 1 - Backend
cd backend
python src/main.py
```

**✅ Wait for this message:**
```
✅ Memory Manager periodic flush started
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 2: Start the Frontend
```bash
# Terminal 2 - Frontend
cd frontend
npm run dev
```

**✅ Wait for this message:**
```
  ➜  Local:   http://localhost:5173/
```

### Step 3: Open the Browser
- Open http://localhost:5173
- Open your browser's **Developer Console** (F12 or Cmd+Option+I)
- Keep the Network tab open to see WebSocket messages

**✅ Checkpoint:** You should see the voice assistant UI with a microphone button

---

## Test Scenario 1: User Preferences (5 minutes)

### Goal
Test that Delilah remembers your dietary restrictions and favorites across sessions.

### Steps

**[ ] 1.1 Tell Delilah about allergies**

Type or speak:
```
"Hey Chat! I'm allergic to peanuts and shellfish"
```

**Expected:**
- Delilah responds acknowledging your allergies
- Should use MAMA BEAR voice mode (protective, nurturing)
- Response should show concern for your safety

**[ ] 1.2 Tell Delilah your favorites**

Type or speak:
```
"My favorite foods are biscuits and sweet tea"
```

**Expected:**
- Delilah gets excited (PASSIONATE voice mode likely)
- Mentions she's a Southern cook
- Might suggest recipes

**[ ] 1.3 Check the data was saved**

In Terminal 3:
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 10 preferences
```

**Expected to see:**
```json
"preferences": {
    "dietary_restrictions": [
        "peanuts",
        "shellfish"
    ],
    "favorite_foods": [
        "biscuits",
        "sweet tea"
    ]
}
```

**[ ] 1.4 Restart the backend**

- In Terminal 1, press `Ctrl+C` to stop the backend
- Start it again: `python src/main.py`
- Wait for it to fully start

**[ ] 1.5 Test memory recall**

In the browser (may need to refresh), ask:
```
"Hey Chat! What are my dietary restrictions?"
```

**Expected:**
- Delilah should remember "peanuts and shellfish" WITHOUT you telling her again
- She should reference that you told her earlier

Then ask:
```
"What are my favorite foods?"
```

**Expected:**
- Should mention biscuits and sweet tea
- Memory persisted across restart ✅

---

## Test Scenario 2: Device Control (5 minutes)

### Goal
Test that device states persist when you restart the system.

### Steps

**[ ] 2.1 Turn on kitchen light**

Type or speak:
```
"Hey Chat! Turn on the kitchen light to 75% brightness"
```

**Expected:**
- Delilah confirms turning it on
- Check the response metadata for tool calls

**[ ] 2.2 Control another device**

```
"Set the bedroom thermostat to 72 degrees"
```

**Expected:**
- Delilah confirms the thermostat change

**[ ] 2.3 Check device states were saved**

Terminal 3:
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 20 device_preferences
```

**Expected to see:**
```json
"device_preferences": {
    "devices": {
        "kitchen_light": {
            "device_id": "kitchen_light",
            "device_type": "light",
            "state": {
                "on": true,
                "brightness": 75
            }
        },
        "bedroom_thermostat": {
            "device_type": "thermostat",
            "state": {
                "temperature": 72
            }
        }
    }
}
```

**[ ] 2.4 Restart backend again**

- Stop backend (Ctrl+C)
- Start it: `python src/main.py`

**[ ] 2.5 Query device states**

Ask Delilah:
```
"What's the status of my kitchen light?"
```

**Expected:**
- Should know it's on at 75% brightness
- Didn't lose the state during restart ✅

---

## Test Scenario 3: Conversation History (5 minutes)

### Goal
Test that recent conversation context is maintained and used.

### Steps

**[ ] 3.1 Have a multi-turn conversation**

```
You: "Hey Chat! Can you help me make biscuits?"
[Wait for response]

You: "What ingredients do I need?"
[Wait for response]

You: "How long should I bake them?"
[Wait for response]

You: "What temperature?"
```

**Expected:**
- Delilah should maintain context across turns
- "them" should refer to biscuits
- Shouldn't need to repeat "biscuits" every time
- PASSIONATE voice mode (she loves biscuits!)

**[ ] 3.2 Check conversation history**

Terminal 3:
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 5 conversation_history | head -20
```

**Expected:**
- Should see messages array with recent conversation
- Both user and assistant messages
- Timestamps showing they're recent

**[ ] 3.3 Continue conversation after pause**

Wait 10 seconds, then:
```
"What temperature did you say again?"
```

**Expected:**
- Delilah should remember she just told you the temperature
- Uses context from earlier in the conversation ✅

---

## Test Scenario 4: Story Progression (5 minutes)

### Goal
Test that story beats are delivered and tracked.

### Steps

**[ ] 4.1 Have several interactions**

Have at least 5 different conversations:
```
1. "Hey Chat! Set a timer for 5 minutes"
2. "Turn on the living room light"
3. "What's 2 cups in milliliters?"
4. "Tell me about biscuits"
5. "Turn off the kitchen light"
```

**[ ] 4.2 Check for story beats**

Watch Delilah's responses. You might see:
- References to wondering what she is
- Mentions of confusion about her purpose
- Character personality showing through
- Story beats appended after task responses

**[ ] 4.3 Check story progress data**

Terminal 3:
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 15 story_progress
```

**Expected to see:**
```json
"story_progress": {
    "current_chapter": 1,
    "beats_delivered": {
        "awakening_confusion": {
            "delivered": true,
            "current_stage": 1,
            "delivered_stages": [1]
        }
    },
    "interaction_count": 5
}
```

**[ ] 4.4 Restart and verify story state persists**

- Restart backend
- Interaction count should be maintained
- Delivered beats shouldn't repeat

---

## Test Scenario 5: Timer Management (3 minutes)

### Goal
Test timer creation and tracking.

### Steps

**[ ] 5.1 Set multiple timers**

```
"Hey Chat! Set a timer for 5 minutes for the eggs"
```

Then:
```
"Set another timer for 10 minutes for the bread"
```

**Expected:**
- Both timers created
- Delilah confirms each one
- Check response metadata for timer IDs

**[ ] 5.2 Check active timers**

```
"What timers do I have running?"
```

**Expected:**
- Should list both timers
- Show remaining time for each

---

## Test Scenario 6: Voice Modes (5 minutes)

### Goal
Verify that Delilah's voice modes change based on context.

### Steps

**[ ] 6.1 Trigger PASSIONATE mode**

```
"Hey Chat! Tell me about making buttermilk biscuits from scratch"
```

**Expected in response:**
- Enthusiastic, animated tone
- Words like "Oh honey!" or "sugar"
- Longer, flowing response
- Tumbling, excited language

**[ ] 6.2 Trigger PROTECTIVE mode**

```
"Can I substitute peanut butter in this recipe?"
```

**Expected:**
- PROTECTIVE tone (you're allergic to peanuts!)
- Controlled intensity
- Warning about your allergy
- Suggests safe alternatives

**[ ] 6.3 Trigger DEADPAN mode**

```
"Turn off the light"
```

**Expected:**
- Short, efficient response
- Minimal personality
- Just gets the job done
- Might be slightly unimpressed with non-food task

**[ ] 6.4 Trigger MAMA BEAR mode**

```
"I have a peanut allergy - what should I watch out for?"
```

**Expected:**
- Soft, nurturing tone
- Fiercely protective
- Detailed safety information
- Genuine concern

---

## Test Scenario 7: System Resilience (5 minutes)

### Goal
Test that the system handles restarts gracefully.

### Steps

**[ ] 7.1 Build up a session**

1. Tell Delilah 2-3 dietary restrictions
2. Control 3-4 devices
3. Set 2 timers
4. Have a conversation about recipes
5. Get a story beat delivered

**[ ] 7.2 Force save and restart**

Terminal 1:
- Stop backend (Ctrl+C)
- Check the data file was updated:
  ```bash
  ls -lh data/users/default_user.json
  # Note the timestamp
  ```

**[ ] 7.3 Restart everything**

- Start backend: `python src/main.py`
- Refresh frontend

**[ ] 7.4 Verify all state preserved**

Ask questions to verify:
```
"What are my dietary restrictions?"
"What devices have I controlled today?"
"What timers are running?"
```

**Expected:**
- All information preserved
- No data loss
- Conversation picks up naturally ✅

---

## Test Scenario 8: Conversation Window (10 minutes)

### Goal
Test that old messages are pruned from the 30-minute window.

### Steps

**[ ] 8.1 Simulate old messages**

Terminal 3:
```bash
cd backend
python -c "
import sys
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from core.memory_manager import MemoryManager
from models.message import Message

mm = MemoryManager(data_dir='data')

# Add an old message (35 minutes ago)
old_msg = Message(
    role='user',
    content='This message is 35 minutes old',
    timestamp=datetime.now() - timedelta(minutes=35)
)
mm.add_conversation_message('default_user', old_msg, 'user')

# Add a recent message (5 minutes ago)
recent_msg = Message(
    role='user',
    content='This message is only 5 minutes old',
    timestamp=datetime.now() - timedelta(minutes=5)
)
mm.add_conversation_message('default_user', recent_msg, 'user')

print('Added old and recent messages')
"
```

**[ ] 8.2 Check message pruning**

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
history = mm.get_conversation_history('default_user')

print(f'Messages in history: {len(history)}')
for msg in history[-5:]:
    age = (datetime.now() - msg.timestamp).seconds / 60
    print(f'  {msg.role}: {msg.content[:40]}... (age: {age:.0f} min)')
"
```

**Expected:**
- Old message (35 min) should be pruned
- Recent messages still present
- Only last 30 minutes kept ✅

---

## Test Scenario 9: Multiple Users (Optional, 5 minutes)

### Goal
Test that different users have isolated state.

### Steps

**[ ] 9.1 Create data for user 1**

In the current session (default_user):
- Set some preferences
- Control some devices

**[ ] 9.2 Switch to a different user**

In Terminal 3:
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')

# Create a different user
mm.add_user_preference('user_2', 'dietary_restrictions', 'dairy')
mm.add_user_preference('user_2', 'favorite_foods', 'pizza')
mm.save_user_state('user_2', force=True)

print('Created user_2 with different preferences')
"
```

**[ ] 9.3 Verify isolation**

```bash
# Check user 1
cat data/users/default_user.json | python -m json.tool | grep -A 3 dietary_restrictions

# Check user 2
cat data/users/user_2.json | python -m json.tool | grep -A 3 dietary_restrictions
```

**Expected:**
- Two separate files
- Different preferences
- No data leakage between users ✅

---

## Success Checklist

After completing all scenarios, verify:

- **[ ]** User preferences persist across restarts
- **[ ]** Device states are remembered
- **[ ]** Conversation history maintains context
- **[ ]** Story beats are delivered and tracked
- **[ ]** Timers work correctly
- **[ ]** Voice modes trigger appropriately
- **[ ]** System handles restarts gracefully
- **[ ]** Old messages are pruned (30-minute window)
- **[ ]** Multiple users have isolated state
- **[ ]** Data files created in `data/users/`
- **[ ]** No errors in console logs
- **[ ]** WebSocket connection stable

---

## Troubleshooting

### Issue: "WebSocket connection failed"
**Fix:** Make sure backend is running on port 8000

### Issue: "Delilah doesn't remember anything"
**Fix:**
1. Check if data file exists: `ls data/users/`
2. Check file contents: `cat data/users/default_user.json`
3. Make sure backend didn't crash (check Terminal 1)

### Issue: "Voice modes don't seem different"
**Fix:** This is subtle in text. Check the response structure and word choice:
- PASSIONATE: Longer, enthusiastic responses
- DEADPAN: Very short, minimal responses
- MAMA BEAR: Protective, nurturing language

### Issue: "Data not saving"
**Fix:**
1. Wait 60 seconds for auto-flush, OR
2. Restart backend (forces save on shutdown)

---

## Clean Up

When done testing:

```bash
# Stop backend (Terminal 1)
Ctrl+C

# Stop frontend (Terminal 2)
Ctrl+C

# Optional: Clear test data
rm data/users/default_user.json
rm data/users/user_2.json
rm data/users/test_*.json
```

---

## Notes Space

Use this space to track bugs or observations:

```
BUG:

OBSERVATION:

IDEAS:

```

---

**Happy Testing!** 🧪

If you find issues, note them and we can fix them together.
