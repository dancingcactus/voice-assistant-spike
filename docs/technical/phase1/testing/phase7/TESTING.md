# Testing Phase 7: Memory & State

## Quick Start

### 1. Automated Tests (5 seconds)

```bash
cd backend
python test_memory.py
```

**Expected Output:** All 6 tests should pass

- ✅ User preferences persistence
- ✅ Story state persistence
- ✅ Conversation history management
- ✅ Device state persistence
- ✅ Interaction count tracking
- ✅ Periodic flush

---

## Interactive Testing (Recommended)

### Option A: Interactive CLI Test

```bash
cd backend
python interactive_memory_test.py
```

**What to try:**

1. Add a dietary restriction (e.g., "peanuts")
2. Add a favorite food (e.g., "biscuits")
3. Add some conversation messages
4. Update a device state (e.g., kitchen_light)
5. **Save and reload** (option 7) - This simulates a restart
6. Verify all your data persisted!

### Option B: Test Through the Web UI

**Start the system:**

```bash
# Terminal 1 - Backend
cd backend
python src/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Then test persistence:**

1. **Open** <http://localhost:5173>
2. **Have a conversation** with Delilah:
   - "Hey Chat! I'm allergic to peanuts"
   - "Can you turn on the kitchen light?"
   - "Set a timer for 5 minutes"
3. **Stop the backend** (Ctrl+C in Terminal 1)
4. **Check the data was saved:**

   ```bash
   cat data/users/default_user.json | python -m json.tool
   ```

5. **Restart the backend:**

   ```bash
   cd backend
   python src/main.py
   ```

6. **Refresh the frontend** and ask:
   - "What are my dietary restrictions?" - Should remember peanuts!
   - "What devices have I controlled?" - Should remember kitchen light

---

## What Gets Persisted?

### User Preferences

- Dietary restrictions (allergies, vegetarian, etc.)
- Cooking skill level
- Favorite/disliked foods
- Custom preferences

### Story Progress

- Current chapter
- Beats delivered (which story beats user has seen)
- Interaction count (for chapter progression)
- Chapter start times

### Conversation History

- **Last 30 minutes in full detail**
- Older messages automatically pruned
- Includes both user messages and assistant responses

### Device States

- Last known state of each device
- Brightness levels for lights
- Temperature for thermostats
- On/off states for switches

---

## Testing Specific Features

### Test 1: Dietary Restrictions Persist

```bash
# Add a restriction
cd backend
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
mm.add_user_preference('test_user', 'dietary_restrictions', 'shellfish')
mm.save_user_state('test_user', force=True)
print('Added shellfish allergy')
"

# Verify it persisted
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
state = mm.load_user_state('test_user')
print(f'Restrictions: {state.preferences.dietary_restrictions}')
"
```

**Expected:** Should show `['shellfish']`

### Test 2: Conversation History Window

```bash
cd backend
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager
from models.message import Message
from datetime import datetime, timedelta

mm = MemoryManager(data_dir='data')

# Add an old message (35 minutes ago)
old_msg = Message(
    role='user',
    content='This is an old message',
    timestamp=datetime.now() - timedelta(minutes=35)
)
mm.add_conversation_message('test_user', old_msg, 'user')

# Add a recent message (5 minutes ago)
recent_msg = Message(
    role='user',
    content='This is a recent message',
    timestamp=datetime.now() - timedelta(minutes=5)
)
mm.add_conversation_message('test_user', recent_msg, 'user')

# Check history
history = mm.get_conversation_history('test_user')
print(f'Messages in history: {len(history)}')
for msg in history:
    print(f'  - {msg.content}')
"
```

**Expected:** Should only show the recent message (old one pruned)

### Test 3: Device State Persistence

```bash
cd backend

# Set a device state
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
mm.update_device_state(
    'test_user',
    'bedroom_light',
    'light',
    {'on': True, 'brightness': 75}
)
mm.save_user_state('test_user', force=True)
print('Set bedroom light to 75%')
"

# Verify it persisted (new MM instance)
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
device = mm.get_device_state('test_user', 'bedroom_light')
if device:
    print(f'Bedroom light state: {device.state}')
else:
    print('Device not found')
"
```

**Expected:** Should show `{'on': True, 'brightness': 75}`

### Test 4: Story Progress Persistence

```bash
cd backend
python -c "
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from core.memory_manager import MemoryManager
from core.story_engine import StoryEngine

mm = MemoryManager(data_dir='data')
story_dir = Path('..') / 'story'
story_engine = StoryEngine(story_dir=str(story_dir), memory_manager=mm)

# Increment interactions
for _ in range(10):
    mm.increment_interaction_count('test_user')

mm.save_user_state('test_user', force=True)

# Check progress
state = mm.load_user_state('test_user')
print(f'Interaction count: {state.story_progress.interaction_count}')
print(f'Current chapter: {state.story_progress.current_chapter}')
"
```

---

## Verifying Data Files

All user data is stored in `data/users/{user_id}.json`:

```bash
# List all users
ls -la data/users/

# View a specific user's data
cat data/users/default_user.json | python -m json.tool

# Watch for changes in real-time
watch -n 1 'cat data/users/default_user.json | python -m json.tool'
```

---

## Testing Periodic Flush

The memory manager automatically saves dirty state every 60 seconds:

```bash
cd backend
python -c "
import sys
import asyncio
sys.path.insert(0, 'src')

from core.memory_manager import MemoryManager

async def test_flush():
    mm = MemoryManager(data_dir='data')
    await mm.start_periodic_flush()

    # Add data but don't force save
    mm.add_user_preference('flush_test', 'favorite_foods', 'tacos')
    print('Added preference (marked as dirty)')
    print('Waiting 65 seconds for auto-flush...')

    await asyncio.sleep(65)
    mm.stop_periodic_flush()
    print('Check if data/users/flush_test.json exists')

asyncio.run(test_flush())
"

# Verify file was created
ls -la data/users/flush_test.json
```

---

## Common Issues & Solutions

### Issue: "No such file or directory: data/users"

**Solution:** The directories are auto-created on first use. Just run the test again.

### Issue: Old data interfering with tests

**Solution:** Clear test data:

```bash
rm data/users/test_*.json
rm data/users/interactive_test_user.json
```

### Issue: Changes not persisting

**Solution:** Make sure to call `save_user_state(user_id, force=True)` or wait 60 seconds for auto-flush.

---

## Integration Test (Full System)

Test the complete integration with all systems:

```bash
# Start backend
cd backend
python src/main.py &
BACKEND_PID=$!

# Wait for startup
sleep 3

# Run a conversation that triggers multiple systems
curl -X POST http://localhost:8000/api/test/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "integration_test",
    "messages": [
      "Hey Chat! I am allergic to peanuts and dairy",
      "Turn on the kitchen light to 50%",
      "Set a timer for 10 minutes"
    ]
  }'

# Stop backend
kill $BACKEND_PID

# Verify data persisted
cat data/users/integration_test.json | python -m json.tool

# Check that it contains:
# - dietary_restrictions: ["peanuts", "dairy"]
# - device state for kitchen_light
# - conversation history
```

---

## Success Criteria

✅ All automated tests pass
✅ User can have a conversation, restart the system, and context is preserved
✅ Dietary restrictions remembered across sessions
✅ Device states persist after restart
✅ Story progress (chapter, beats) persists
✅ Conversation history shows last 30 minutes
✅ Data files created in `data/users/`
✅ Periodic flush saves data automatically

---

## Next Steps

Once Phase 7 testing is complete:

- **Phase 8**: Testing/Automation API (programmatic control for test scenarios)
- **Phase 9**: Multi-character panel discussions
- **Phase 10**: Advanced context management and summarization
