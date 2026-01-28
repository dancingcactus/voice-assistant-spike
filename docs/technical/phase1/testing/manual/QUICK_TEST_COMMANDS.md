# Quick Test Commands - Phase 7

Copy/paste these commands for quick testing. No typing needed!

---

## Start the System

```bash
# Terminal 1 - Backend
cd /Users/justin/projects/voice-assistant-spike/backend && python src/main.py

# Terminal 2 - Frontend
cd /Users/justin/projects/voice-assistant-spike/frontend && npm run dev

# Terminal 3 - Keep open for commands below
cd /Users/justin/projects/voice-assistant-spike
```

**Browser:** http://localhost:5173

---

## Things to Say to Delilah

### Test Preferences
```
Hey Chat! I'm allergic to peanuts and shellfish
```

```
My favorite foods are biscuits and sweet tea
```

```
What are my dietary restrictions?
```

### Test Device Control
```
Hey Chat! Turn on the kitchen light to 75%
```

```
Set the bedroom thermostat to 72 degrees
```

```
What's the status of my kitchen light?
```

### Test Timers
```
Hey Chat! Set a timer for 5 minutes for the eggs
```

```
Set another timer for 10 minutes for the bread
```

```
What timers do I have running?
```

### Test Voice Modes

**PASSIONATE (food she loves):**
```
Tell me about making buttermilk biscuits from scratch
```

**PROTECTIVE (food done wrong):**
```
Can I substitute peanut butter in this recipe?
```

**MAMA BEAR (your allergies):**
```
I have a peanut allergy - what should I watch out for?
```

**DEADPAN (non-food tasks):**
```
Turn off the light
```

### Test Conversation Context
```
Hey Chat! Can you help me make biscuits?
```
Then: `What ingredients do I need?`
Then: `How long should I bake them?`
Then: `What temperature?`

---

## Check Saved Data

### View user data
```bash
cat data/users/default_user.json | python -m json.tool
```

### View just preferences
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 10 preferences
```

### View device states
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 20 device_preferences
```

### View story progress
```bash
cat data/users/default_user.json | python -m json.tool | grep -A 15 story_progress
```

### Watch file for changes (auto-refreshes)
```bash
watch -n 1 'cat data/users/default_user.json | python -m json.tool'
```

### List all user files
```bash
ls -lh data/users/
```

---

## Test Persistence

### Save data and check timestamp
```bash
ls -lh data/users/default_user.json
```

### Restart backend (Terminal 1)
```
Ctrl+C
python src/main.py
```

### Then ask Delilah if she remembers things
```
What are my dietary restrictions?
What are my favorite foods?
What devices have I controlled?
```

---

## Quick Script Tests

### Test adding preferences
```bash
cd /Users/justin/projects/voice-assistant-spike/backend
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
mm.add_user_preference('test_user', 'dietary_restrictions', 'gluten')
mm.add_user_preference('test_user', 'favorite_foods', 'tacos')
mm.save_user_state('test_user', force=True)
print('✅ Added preferences for test_user')

# Verify
state = mm.load_user_state('test_user')
print(f'Restrictions: {state.preferences.dietary_restrictions}')
print(f'Favorites: {state.preferences.favorite_foods}')
"
```

### Test device states
```bash
cd /Users/justin/projects/voice-assistant-spike/backend
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')
mm.update_device_state('test_user', 'patio_light', 'light', {'on': True, 'brightness': 100})
mm.save_user_state('test_user', force=True)
print('✅ Set patio light to 100%')

# Verify
device = mm.get_device_state('test_user', 'patio_light')
print(f'Patio light: {device.state}')
"
```

### Test interaction counting
```bash
cd /Users/justin/projects/voice-assistant-spike/backend
python -c "
import sys
sys.path.insert(0, 'src')
from core.memory_manager import MemoryManager

mm = MemoryManager(data_dir='data')

# Increment 5 times
for i in range(5):
    mm.increment_interaction_count('test_user')

mm.save_user_state('test_user', force=True)

state = mm.load_user_state('test_user')
print(f'✅ Interaction count: {state.story_progress.interaction_count}')
"
```

---

## Run Full Test Suite

```bash
cd /Users/justin/projects/voice-assistant-spike/backend
python test_memory.py
```

**Expected:** All 6 tests pass

---

## Interactive Test

```bash
cd /Users/justin/projects/voice-assistant-spike/backend
python interactive_memory_test.py
```

**Try these options:**
1. Add dietary restriction → peanuts
2. Add favorite food → biscuits
3. Update device → kitchen_light, light, on, 50
7. Save and reload (verify persistence)

---

## Clean Up Test Data

```bash
# Remove all test user data
rm data/users/test_*.json
rm data/users/demo_*.json
rm data/users/interactive_*.json

# List what's left
ls -la data/users/
```

---

## Useful Debugging

### Check if backend is running
```bash
lsof -i :8000
```

### Kill backend if stuck
```bash
lsof -ti:8000 | xargs kill -9
```

### Check backend logs for errors
```bash
# In Terminal 1 where backend is running, look for:
# - "ERROR" messages
# - "Traceback" for stack traces
# - "✅" for successful operations
```

### Check WebSocket connection
In browser console (F12):
```javascript
// Should see WebSocket connection messages
// Look for "WebSocket connected" in console
```

---

## Expected Behavior

✅ **After adding preferences:** They appear in JSON file immediately (or within 60s)
✅ **After restart:** All data preserved, no loss
✅ **Conversation context:** Delilah remembers what you just said
✅ **Voice modes:** Tone/length changes based on topic
✅ **Device states:** Last known state remembered
✅ **Story beats:** Delivered at appropriate times

---

**Pro Tips:**
- Keep Terminal 3 open with `watch -n 1 'cat data/users/default_user.json | python -m json.tool'` to see real-time updates
- Use browser DevTools Network tab to see WebSocket messages
- Look for `story_beat_injected: true` in response metadata
- File timestamps show when data was last saved
