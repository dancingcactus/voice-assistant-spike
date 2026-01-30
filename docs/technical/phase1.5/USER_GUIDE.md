# Observability Dashboard - User Guide

**Version:** 1.0
**Last Updated:** January 2026
**Phase:** 1.5 Complete

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Story Beat Tool](#story-beat-tool)
4. [Memory Tool](#memory-tool)
5. [User Testing Tool](#user-testing-tool)
6. [Tool Calls Inspector](#tool-calls-inspector)
7. [Character Tool](#character-tool)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Common Workflows](#common-workflows)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.9+ with virtual environment
- Node.js 18+ and npm
- Backend data files in `backend/data/`

### Starting the Dashboard

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m uvicorn src.observability.api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the Dashboard:**
- Open http://localhost:5173/observability (or the port shown by Vite)
- You should see the home page with quick actions

### First-Time Setup

1. **Verify Health**: Check top-right corner shows green "Connected" status
2. **Select User**: Use dropdown to select `user_justin` (default)
3. **Explore Tools**: Click any quick action card to start

---

## Dashboard Overview

### Home Page

The home page provides a high-level overview of the system:

**Quick Actions**
- Click any tool card to navigate
- Keyboard shortcuts: Press `1-6` for direct navigation

**Current User Profile**
- Shows selected user's chapter, interaction count
- Production users marked with green badge

**System Overview**
- Total users count
- Available tools count (6)
- Active characters count
- Milestones completion status

**All Users**
- Click any user card to switch context
- Production users cannot be deleted
- Test users show without badge

### Navigation

**Top Navigation Bar:**
- Home (1) - Dashboard overview
- Story Beats (2) - Story progression tool
- Memories (3) - Memory management
- User Testing (4) - Test user lifecycle
- Tool Calls (5) - API inspection
- Characters (6) - Character configuration

**Header Controls:**
- User selector dropdown
- Help button (?) - Shows keyboard shortcuts
- Health indicator (green = connected)

---

## Story Beat Tool

### Overview

View, trigger, and manage story beats for testing narrative progression.

### Key Features

**Beat List View**
- All beats for current chapter
- Status indicators:
  - ✅ Delivered
  - 📍 Ready to deliver
  - 🔒 Locked (prerequisites not met)
  - ⏸️ Not yet triggered

**Beat Details**
- Name and ID
- Required vs optional
- Prerequisites list
- Delivery configuration
- All variants (short/medium/long)
- Delivery history with timestamps

**Beat Triggers**
- Click "Trigger Now" to queue a beat
- Beat will deliver in next interaction
- Use "Mark as Undelivered" to reset

**Flow Diagram**
- Visual representation of chapter structure
- Shows dependencies between beats
- Required beats in green, optional in blue

### Common Tasks

**View Story Progress**
1. Navigate to Story Beats (press `2`)
2. See your current chapter and completion %
3. Check which beats you've experienced

**Test a New Beat**
1. Find an undelivered optional beat
2. Click "Trigger Now"
3. Go to main chat interface
4. Say "Hey Chat, help me with something"
5. Beat will be delivered in response
6. Return to tool, verify beat now shows as delivered

**Debug Beat Prerequisites**
1. Click on locked beat
2. View "Prerequisites" section
3. Check which beats must be delivered first
4. Use flow diagram to see dependency chain

---

## Memory Tool

### Overview

Create, view, edit, and delete user memories. Essential for testing memory-based interactions.

### Key Features

**Memory List**
- All memories for selected user
- Filterable by category, importance, verification status
- Searchable by content
- Sortable by recency, importance, access count

**Memory Categories**
- 📝 Fact - Objective information
- ❤️ Preference - User likes/dislikes
- ⚠️ Dietary Restriction - Allergies, food requirements
- 👨‍👩‍👧‍👦 Family - Relationships, people
- 🏠 Location - Home, work, places
- 💼 Event - Scheduled events, history
- 🎯 Goal - User objectives
- 📚 Knowledge - Skills, expertise

**Importance Scale**
- 1-10 rating
- Higher importance = more likely to load in context
- Importance ≥ 3 typically loaded

**Memory Fields**
- Content (required) - The actual memory text
- Category (required) - Classification
- Importance (1-10) - Priority
- Source - Where memory came from
- Verified - Checkbox for confirmed memories
- Tags - Optional categorization

### Common Tasks

**View All Memories**
1. Navigate to Memories (press `3`)
2. See complete list sorted by recency
3. Use search box to filter by text

**Create a New Memory**
1. Click "+ New Memory" button (or press `N`)
2. Fill in content: "Loves testing observability tools"
3. Select category: Preference
4. Set importance: 7
5. Add source: "manual_test_2026-01-29"
6. Check "Verified"
7. Click "Create Memory"
8. Memory appears in list

**Edit Existing Memory**
1. Find memory in list
2. Click "Edit" button
3. Update any fields
4. Save changes
5. Updated timestamp shown

**Delete Memory**
1. Click "Delete" on memory
2. Confirm in dialog (shows memory content)
3. Memory removed from list

**View Context Preview**
1. Click "View Context" button
2. See which memories would load in character prompt
3. Check estimated token count
4. Verify importance threshold working

---

## User Testing Tool

### Overview

Create isolated test users for testing different story scenarios without affecting production data.

### Key Features

**User List**
- All users (production + test)
- Production users have green "PRODUCTION" badge
- Test users can be deleted
- Click user card to view details or switch

**User Creation Wizard**
- Auto-generated unique names (e.g., TestUser_Riley_8273)
- Choose starting chapter
- Add initial memories from templates
- Tag for organization
- Auto-switch option

**User State Summary**
- Profile info (created date, interactions)
- Story progress (chapter, beats completed)
- Memory count
- Active characters
- Tags

**User Deletion**
- Shows impact preview (memories, story data, tool calls)
- Confirmation required
- Production users protected (cannot delete user_justin)
- Cascade deletion (all related data removed)

### Common Tasks

**Create Test User for Chapter 2**
1. Navigate to User Testing (press `4`)
2. Click "+ Create User"
3. Name auto-generates
4. Select starting chapter: Chapter 2
5. Add initial memories:
   - Check "Gluten intolerance"
   - Check "Loves spicy food"
6. Add tags: `testing`, `chapter2`
7. Check "Switch to this user after creation"
8. Click "Create User"
9. Context switches to new user across all tools

**Switch Between Users**
1. Open User Testing tool
2. Click "Switch to User" on desired user
3. All tools update to show that user's data
4. Top-right dropdown reflects change

**Export User Data**
1. Click "Export Data" on user
2. JSON file downloads
3. Contains complete user state:
   - Profile
   - Story progress
   - All memories
   - Tool call history

**Delete Test User**
1. Click "Delete" on test user
2. Confirmation shows:
   - User name
   - Memory count
   - Story beats completed
   - Tool calls made
3. Confirm deletion
4. If was active user, auto-switches to user_justin
5. All files removed from backend/data/

---

## Tool Calls Inspector

### Overview

Debug tool execution, inspect performance, and replay API calls.

### Key Features

**Tool Call Timeline**
- Chronological list of all tool calls
- Shows timestamp, tool name, duration, status
- Character who made the call

**Filters**
- By tool name (set_timer, get_recipe, etc.)
- By character (Delilah, Hank, etc.)
- By time range (last hour, last 24h, last week)
- By status (success, error)

**Call Details**
- Full request JSON (pretty-printed)
- Full response JSON
- Duration in milliseconds
- Character reasoning (if captured)
- Error messages with stack trace (if failed)

**Replay Functionality**
- Replay with same parameters
- Edit parameters and retry
- Creates new log entry marked as "Replay of evt_XXX"

**Statistics**
- Total calls
- Success rate
- Average duration
- Most used tools
- Character breakdown
- Top 5 slowest calls
- Recent errors

### Common Tasks

**Find Slow Tool Calls**
1. Navigate to Tool Calls (press `5`)
2. Sort by "Duration" column (click header)
3. Identify calls > 2000ms
4. Click to expand details
5. Inspect request to understand why slow

**Debug Failed Call**
1. Filter by status: "Error"
2. Find recent failure
3. Expand details
4. Read error message
5. Copy request JSON
6. Fix underlying issue
7. Click "Retry"
8. Verify now succeeds

**Analyze Tool Usage**
1. Scroll to Statistics section
2. Review "Most Used Tools"
3. Check success rates
4. Identify which character uses which tools
5. Find performance bottlenecks

---

## Character Tool

### Overview

Inspect character configurations, test voice modes, and debug system prompts.

### Key Features

**Character Selector**
- Browse all available characters
- Shows active vs locked status
- Interaction count per character

**Overview Tab**
- Personality traits
- Speech patterns and mannerisms
- Capabilities list
- Story arc context
- Character metadata

**Voice Modes Tab**
- Interactive voice mode tester
- Input test phrase, see which mode selected
- Confidence scoring
- Reasoning explanation
- All modes with triggers and characteristics
- Example phrases for each mode

**System Prompt Tab**
- Generate full system prompt
- Select specific voice mode or all modes
- Token count estimation
- Token breakdown by section:
  - Base character
  - Personality
  - Voice modes
  - Memory context
  - Tool instructions
- Full prompt preview

**Tool Instructions Tab**
- Character-specific tool guidelines
- When to use / when NOT to use
- Importance rating scales
- Usage examples with context

### Common Tasks

**Test Voice Mode Selection**
1. Navigate to Characters (press `6`)
2. Select "Delilah" from sidebar
3. Go to "Voice Modes" tab
4. Enter test phrase: "I have a severe peanut allergy"
5. Click "Test Voice Mode"
6. See result: Mama Bear Mode (95% confidence)
7. Read reasoning: "Selected due to allergy/dietary concern"

**Generate System Prompt**
1. Go to "System Prompt" tab
2. Select voice mode (or "All modes")
3. Click "Generate Prompt"
4. View token breakdown
5. Scroll to see full prompt
6. Copy sections for testing

**Review Tool Instructions**
1. Go to "Tool Instructions" tab
2. See list of available tools
3. Click tool card (e.g., save_memory)
4. Read when to use guidelines
5. Check importance scale
6. Review examples

---

## Keyboard Shortcuts

### Global Shortcuts

| Keys | Action |
|------|--------|
| `1` | Go to Home |
| `2` | Go to Story Beats |
| `3` | Go to Memories |
| `4` | Go to User Testing |
| `5` | Go to Tool Calls |
| `6` | Go to Characters |
| `Ctrl/Cmd + U` | Focus user selector |
| `Shift + ?` | Show keyboard shortcuts help |
| `Esc` | Close modal/dialog |

### In-Tool Shortcuts

**Memory Tool:**
- `N` - Create new memory (planned)

**User Testing Tool:**
- `N` - Create new user (planned)

**Story Beat Tool:**
- `F` - Open filters (planned)
- `D` - Switch to diagram view (planned)

### Tips

- Press `?` anytime to see all shortcuts
- Shortcuts don't work when typing in input fields
- Navigation shortcuts work from any page

---

## Common Workflows

### Workflow 1: Debug Chapter 2 Progression

**Goal:** Test if Chapter 2 beats deliver correctly

**Steps:**
1. **Create test user** (User Testing tool)
   - Starting chapter: Chapter 2
   - Initial memories: vegetarian, loves spicy
   - Tags: `testing`, `chapter2`
   - Auto-switch to new user

2. **Set up story state** (Story Beat tool)
   - Mark Chapter 1 required beats complete
   - Trigger "hank_arrival" beat

3. **Test interaction** (Main chat)
   - Say "Hey Chat, what can you help with?"
   - Verify Hank introduction plays

4. **Inspect results** (Tool Calls tool)
   - View recent interaction log
   - Check which character responded
   - Verify tool calls made
   - Check response latency

5. **Check memory creation** (Memory tool)
   - Look for any new memories
   - Verify categories and importance

6. **Validate character state** (Character tool)
   - Select Hank
   - View system prompt
   - Verify vegetarian preference in context
   - Check Chapter 2 story context included

7. **Clean up** (User Testing tool)
   - Delete test user
   - Switch back to production user

### Workflow 2: Test Memory Retrieval

**Goal:** Verify important memories load in character context

**Steps:**
1. **Create high-importance memory**
   - Content: "Prefers detailed error messages"
   - Importance: 9
   - Category: Preference

2. **View context preview**
   - Check token estimate
   - Verify memory in loaded context

3. **Generate system prompt**
   - Go to Character tool
   - Generate prompt with all modes
   - Search for your memory in prompt text
   - Verify it's included

4. **Lower importance**
   - Edit memory, set importance to 2
   - Regenerate prompt
   - Verify memory no longer included

### Workflow 3: Find Performance Issues

**Goal:** Identify slow tool calls affecting UX

**Steps:**
1. **Review statistics** (Tool Calls tool)
   - Check average duration
   - Look at "Top 5 Slowest Calls"

2. **Filter slow calls**
   - Sort by duration (descending)
   - Find calls > 2000ms

3. **Inspect slow call**
   - Expand details
   - View request parameters
   - Check response size
   - Note timestamp

4. **Correlate with issues**
   - Filter to time range when slowness reported
   - Look for patterns (all recipe calls slow?)
   - Form hypothesis

5. **Verify fix**
   - Make same call again
   - Check new duration
   - Compare to previous

---

## Troubleshooting

### Backend Won't Start

**Symptom:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Shows "Connection Error"

**Symptom:** Red error card, "Unable to connect to API"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS configuration in backend
3. Verify `.env` file has correct `VITE_API_BASE_URL`
4. Click "Retry" button after fixing

### Data Not Loading

**Symptom:** Empty lists, loading spinner indefinitely

**Solution:**
1. Check browser console for errors (F12)
2. Verify user has data files in `backend/data/users/`
3. Check API logs for errors
4. Try switching to different user
5. Refresh page (Ctrl/Cmd + R)

### Keyboard Shortcuts Not Working

**Symptom:** Pressing `1-6` doesn't navigate

**Solution:**
1. Make sure you're not focused in an input field
2. Click somewhere on the page to lose input focus
3. Try again
4. Press `?` to verify shortcuts are loaded

### User Selector Dropdown Empty

**Symptom:** No users in dropdown

**Solution:**
1. Verify `backend/data/users/` directory exists
2. Check at least one `.json` file exists
3. Restart backend
4. Refresh frontend

### Tool Call Logs Not Appearing

**Symptom:** Tool Calls tool shows no data

**Solution:**
1. Verify `backend/data/tool_calls.jsonl` exists
2. Check file has entries: `tail backend/data/tool_calls.jsonl`
3. Make a test tool call via main chat
4. Refresh Tool Calls tool

### Memory Edits Not Saving

**Symptom:** Click save but changes don't persist

**Solution:**
1. Check browser console for API errors
2. Verify file lock not stuck: `ls backend/data/*.lock`
3. Remove stale locks: `rm backend/data/*.lock`
4. Try again
5. Check API logs for permission errors

### Character Voice Modes Not Updating

**Symptom:** Wrong voice mode selected for test input

**Solution:**
1. Go to Character Tool > Voice Modes tab
2. Test with various inputs
3. Check triggers list for each mode
4. Verify keywords are spelled correctly
5. Check confidence scores (lower = less certain)

---

## Performance Tips

### Keep It Fast

1. **Use keyboard shortcuts** - Faster than clicking
2. **Stay on one user** - Switching users invalidates cache
3. **Filter before scrolling** - Reduces rendered items
4. **Close unused modals** - Frees up memory
5. **Refresh periodically** - Clears memory leaks

### Data Management

1. **Delete old test users** - Reduces user list clutter
2. **Archive old tool call logs** - Keep logs manageable
3. **Clean up test memories** - Don't accumulate junk data
4. **Use tags** - Organize test users for easy cleanup

### Browser Performance

1. **Use modern browser** - Chrome, Firefox, Safari latest
2. **Close other tabs** - Reduces memory pressure
3. **Enable hardware acceleration** - Better rendering
4. **Dark theme** - Already enabled, reduces eye strain

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
All requests require header:
```
Authorization: Bearer dev_token_12345
```

### Core Endpoints

**Health Check**
```
GET /health
Response: {"status": "ok", "timestamp": "...", "version": "1.0.0"}
```

**List Users**
```
GET /users
Response: [{"user_id": "user_justin", "current_chapter": 1, ...}, ...]
```

**User Details**
```
GET /users/{user_id}
Response: {"user_id": "...", "profile": {...}, "story_progress": {...}}
```

**List Memories**
```
GET /memory/users/{user_id}
Response: [{"id": "mem_123", "content": "...", "category": "fact", ...}, ...]
```

**Create Memory**
```
POST /memory/users/{user_id}
Body: {
  "content": "Loves spicy food",
  "category": "preference",
  "importance": 7,
  "source": "conversation",
  "verified": true
}
```

For complete API documentation, visit: http://localhost:8000/docs

---

## Best Practices

### Testing Story Progression

1. **Always use test users** - Never modify production user story state
2. **Tag your users** - `testing`, `chapter1`, `debug`, etc.
3. **Clean up after testing** - Delete test users when done
4. **Document findings** - Note what worked/didn't work
5. **Test one variable at a time** - Isolate story vs character vs memory

### Managing Memories

1. **Use consistent categories** - Makes filtering easier
2. **Set importance thoughtfully** - Too high = context bloat
3. **Verify important memories** - Checkbox for confidence
4. **Add sources** - Track where memories came from
5. **Review context preview** - Ensure most important memories load

### Debugging Tools

1. **Start with Tool Calls** - See what actually executed
2. **Check Character prompt** - Verify context sent to LLM
3. **Review Memory context** - Ensure relevant memories loaded
4. **Test voice modes** - Confirm right mode for scenario
5. **Compare across users** - Isolate user-specific issues

### Performance Monitoring

1. **Watch average duration** - Should be < 1 second for most tools
2. **Monitor success rates** - 95%+ is healthy
3. **Check token counts** - Optimize if consistently > 2000 tokens
4. **Review memory count** - 20-30 memories is reasonable
5. **Test with realistic data** - Don't use empty test users

---

## Advanced Features

### Context Preview Analysis

The Memory Tool's "View Context" feature shows exactly what memories load in the character's system prompt:

1. **Token estimation** - Helps stay under limits
2. **Importance threshold** - Usually loads memories ≥ 3
3. **Category distribution** - See balance of memory types
4. **Recency bias** - Recently accessed memories prioritized

### Voice Mode Tuning

Use the Character Tool to refine voice mode selection:

1. **Test trigger phrases** - Input real user queries
2. **Check confidence scores** - Lower = ambiguous
3. **Review reasoning** - Understand why mode chosen
4. **Iterate on triggers** - Adjust character definition
5. **Validate with real interactions** - Test in main chat

### Beat Delivery Control

Story Beat Tool gives fine-grained control over narrative:

1. **Force beat delivery** - Skip prerequisites for testing
2. **Mark as undelivered** - Re-test beat delivery
3. **Trigger multiple beats** - Queue up sequence
4. **View delivery history** - When each beat played

### Tool Call Replay

Tool Calls Inspector lets you replay API calls:

1. **Same parameters** - Verify idempotent behavior
2. **Modified parameters** - Test edge cases
3. **Compare responses** - Check for consistency
4. **Debug errors** - Fix underlying issue, then retry

---

## Tips & Tricks

### Efficiency

- **Use quick actions** on home page for one-click navigation
- **Keyboard shortcuts** are faster than mouse
- **Filter early** - Don't scroll through 100 items
- **Copy JSON** from tool call details for debugging
- **Export user data** before making risky changes

### Testing

- **Create test user templates** - Save common configurations
- **Tag everything** - Makes cleanup easy (`testing`, `milestone5`, etc.)
- **Test in isolation** - One change at a time
- **Compare with production** - Switch between users to verify differences
- **Document edge cases** - Note unusual scenarios in tags or notes

### Debugging

- **Check health first** - Green dot means API working
- **Review recent tool calls** - See what actually happened
- **Inspect system prompt** - Verify character context correct
- **Compare memory contexts** - Different users should have different memories
- **Look at timestamps** - Correlate events across tools

---

## Glossary

- **Beat** - A story event or narrative moment
- **Chapter** - A collection of story beats, represents story progression
- **Memory** - A piece of user context (fact, preference, etc.)
- **Context** - Information loaded in character's system prompt
- **Tool Call** - An API function execution (set timer, get recipe, etc.)
- **Voice Mode** - Character's emotional/tonal state (passionate, deadpan, etc.)
- **Character** - An AI personality (Delilah, Hank, etc.)
- **Test User** - Non-production user for isolated testing
- **Production User** - Real user (user_justin), protected from deletion

---

## Support

### Getting Help

- **Check this guide first** - Most common issues covered
- **Review API docs** - http://localhost:8000/docs
- **Check backend logs** - `tail -f backend/logs/app.log`
- **Browser console** - F12 > Console tab for frontend errors

### Reporting Issues

When reporting a bug, include:
1. **What you were doing** - Specific steps
2. **What you expected** - Desired behavior
3. **What actually happened** - Actual behavior
4. **Error messages** - From console or API logs
5. **Environment** - Browser, OS, backend/frontend versions
6. **Screenshots** - If UI issue

### Known Limitations

1. **Single character** - Only Delilah currently defined
2. **No real-time updates** - Must refresh to see changes from other sources
3. **No batch operations** - Must modify memories one at a time
4. **Limited statistics** - Character stats are placeholders
5. **No undo** - Deletions are permanent

---

## What's Next

### Immediate Improvements

- Add remaining characters (Hank, Cave, Dimitria)
- Real-time WebSocket updates
- Bulk memory import/export
- Advanced search across all tools

### Future Features

- Timeline visualization of user journey
- Performance profiling visualizations
- Automated test scenario recording
- Character interaction simulator
- Voice mode A/B testing
- Mobile responsive improvements

---

**Version 1.0** - January 2026
Phase 1.5 Complete ✅
