# 🧪 Start Testing Here - Phase 7

**5-Minute Quick Start Guide**

---

## Option 1: Automated Test (30 seconds)

Just want to verify everything works?

```bash
cd backend
python test_memory.py
```

✅ All 6 tests should pass. Done!

---

## Option 2: Manual Full System Test (10 minutes)

Want to actually use the UI and test manually?

### Step 1: Start Everything

**Terminal 1:**
```bash
cd backend
python src/main.py
```
Wait for: `✅ Memory Manager periodic flush started`

**Terminal 2:**
```bash
cd frontend
npm run dev
```
Wait for: `Local: http://localhost:5173/`

**Terminal 3:** (keep open for checking data)
```bash
cd /Users/justin/projects/voice-assistant-spike
```

### Step 2: Open Browser
Go to: http://localhost:5173

### Step 3: Follow the Script
Open **[MANUAL_TEST_SCRIPT.md](MANUAL_TEST_SCRIPT.md)** and follow scenarios 1-4.

Each scenario takes 5 minutes and tests a different feature:
1. **User Preferences** - Allergies and favorites
2. **Device Control** - Lights and thermostats
3. **Conversation History** - Multi-turn context
4. **Story Progression** - Beat delivery

---

## Option 3: Interactive Exploration (5 minutes)

Want to play around with the system?

```bash
cd backend
python interactive_memory_test.py
```

Try these in order:
1. Add dietary restriction: `peanuts`
2. Add favorite food: `biscuits`
3. Add a conversation message
4. Update device: `kitchen_light`, type `light`, on: `y`, brightness: `75`
5. **Option 7: Save and reload** ← This tests persistence!
6. View full state (option 6)

Exit when done (option 0).

---

## Quick Reference

Need commands? → **[QUICK_TEST_COMMANDS.md](QUICK_TEST_COMMANDS.md)**
Full testing guide? → **[TESTING_PHASE7.md](TESTING_PHASE7.md)**
Step-by-step script? → **[MANUAL_TEST_SCRIPT.md](MANUAL_TEST_SCRIPT.md)**

---

## The Key Test: Does Memory Persist?

This is what you're really testing:

1. **Tell Delilah:** "I'm allergic to peanuts"
2. **Check it saved:** `cat data/users/default_user.json | grep peanuts`
3. **Restart backend:** Ctrl+C, then `python src/main.py`
4. **Ask Delilah:** "What are my dietary restrictions?"
5. **She should remember!** ✅

If she remembers, Phase 7 works!

---

## Recommended First Test

**Do this right now (2 minutes):**

1. Start backend: `cd backend && python src/main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Say: **"Hey Chat! I'm allergic to peanuts"**
5. Restart backend (Ctrl+C, then restart)
6. Say: **"Hey Chat! What are my dietary restrictions?"**

If Delilah says "peanuts" - **Phase 7 works!** 🎉

---

## Help!

**Backend won't start?**
```bash
lsof -ti:8000 | xargs kill -9
```

**Want to see the data?**
```bash
cat data/users/default_user.json | python -m json.tool
```

**Want to reset everything?**
```bash
rm data/users/*.json
```

---

**Happy Testing!**

Pick your path above and go! 🚀
