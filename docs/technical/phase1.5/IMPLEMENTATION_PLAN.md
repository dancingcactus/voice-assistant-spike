# Phase 1.5: Implementation Plan with Testable Milestones

**Version:** 1.0
**Last Updated:** January 2025
**Status:** Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Milestone 1: Foundation & Data Access](#milestone-1-foundation--data-access)
3. [Milestone 2: Story Beat Tool](#milestone-2-story-beat-tool)
4. [Milestone 3: Memory Tool](#milestone-3-memory-tool)
5. [Milestone 4: User Testing Tool](#milestone-4-user-testing-tool)
6. [Milestone 5: Tool Calls Inspection](#milestone-5-tool-calls-inspection)
7. [Milestone 6: Character Tool](#milestone-6-character-tool)
8. [Milestone 7: Polish & Integration](#milestone-7-polish--integration)
9. [Testing Strategy](#testing-strategy)
10. [Success Criteria](#success-criteria)

---

## Overview

### Goals

- **Testable at Every Step**: Each milestone produces a working, demonstrable feature
- **Try It Out**: You can interact with the tool as soon as each milestone completes
- **Incremental Value**: Each milestone builds on the previous and adds immediate utility
- **Fast Feedback**: Catch issues early with hands-on testing

### Timeline Estimate

- **Total Duration**: 4-5 weeks
- **Milestone Cadence**: 3-5 days per milestone
- **Daily Testing**: 15-30 minutes hands-on validation per day

### Development Philosophy

1. **Vertical Slices**: Build complete features end-to-end, not layers
2. **Manual Testing First**: You try it before writing automated tests
3. **Real Data**: Use actual Phase 1 data files from day one
4. **Feedback Loops**: Quick iterations based on what works/doesn't work

---

## Milestone 1: Foundation & Data Access

**Duration:** 3-4 days
**Goal:** API backend running, can read Phase 1 data files, basic frontend displays data

### What Gets Built

#### Backend

- FastAPI app structure
- Data access layer for reading JSON files
- File locking implementation
- Basic error handling
- Health check endpoint

#### Frontend

- React + TypeScript + Vite setup
- API client configuration
- Simple "Hello World" dashboard
- Basic routing structure
- Dark mode theme

#### API Endpoints

```
GET  /api/v1/health              # Server health check
GET  /api/v1/users               # List all users
GET  /api/v1/users/{user_id}     # Get user details
```

### How to Test It

#### Backend Testing (15 minutes)

1. **Start the API server:**

   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn observability.api:app --reload --port 8000
   ```

2. **Verify health check:**

   ```bash
   curl http://localhost:8000/api/v1/health
   ```

   **Expected:** `{"status": "ok", "timestamp": "..."}`

3. **List users:**

   ```bash
   curl -H "Authorization: Bearer dev_token_12345" \
        http://localhost:8000/api/v1/users
   ```

   **Expected:** JSON list including `user_justin`

4. **Get your user details:**

   ```bash
   curl -H "Authorization: Bearer dev_token_12345" \
        http://localhost:8000/api/v1/users/user_justin
   ```

   **Expected:** Your full user profile with story progress, memories count

#### Frontend Testing (10 minutes)

1. **Start the frontend:**

   ```bash
   cd frontend
   npm run dev
   ```

   **Expected:** Opens at <http://localhost:5173>

2. **View dashboard:**
   - Should see dark theme
   - Should see "Hey Chat! Observability Dashboard" header
   - Should see your username displayed

3. **Check user list:**
   - Navigate to Users page (if routed)
   - Should see `user_justin` listed
   - Click to view details
   - Should display your chapter, interaction count

### Success Criteria

- ✅ API server starts without errors
- ✅ Can read existing Phase 1 user data files
- ✅ Frontend displays real data from API
- ✅ Dark mode theme looks good
- ✅ No console errors in browser
- ✅ API responds in < 500ms

### Deliverables

- [ ] Backend API running on port 8000
- [ ] Frontend running on port 5173
- [ ] `.env` files configured
- [ ] Can see your user data in browser
- [ ] Documentation: How to start/stop services

---

## Milestone 2: Story Beat Tool

**Duration:** 4-5 days
**Goal:** View all story beats, see chapter flow, trigger beats for testing

### What Gets Built

#### Backend

- Story state data accessor
- Chapter and beat query endpoints
- User progress endpoint
- Beat trigger functionality
- Mermaid diagram generator

#### Frontend

- Story Beat Tool main view
- Beat list with filters
- Beat detail modal
- Chapter flow diagram (Mermaid rendering)
- Trigger beat action

#### API Endpoints

```
GET  /api/v1/story/chapters                              # List chapters
GET  /api/v1/story/chapters/{chapter_id}                 # Chapter details
GET  /api/v1/story/chapters/{chapter_id}/beats           # Chapter beats
GET  /api/v1/story/beats/{beat_id}                       # Beat details
GET  /api/v1/story/users/{user_id}/progress              # User progress
POST /api/v1/story/users/{user_id}/beats/{beat_id}/trigger  # Trigger beat
GET  /api/v1/story/chapters/{chapter_id}/diagram         # Flow diagram
```

### How to Test It

#### Story Beat Viewing (10 minutes)

1. **Open Story Beat Tool:**
   - Navigate to <http://localhost:5173/story-beats>
   - Should see all chapters listed in sidebar
   - Chapter 1 should show as "in progress" with your current progress

2. **View Chapter 1 beats:**
   - Click on Chapter 1
   - Should see list of all beats (awakening_confusion, recipe_help, etc.)
   - Beats you've completed should show ✅
   - Beats ready to deliver should show 📍
   - Locked beats should show 🔒

3. **Check beat details:**
   - Click "View Details" on `awakening_confusion`
   - Should see:
     - Beat name and ID
     - Required vs optional status
     - Prerequisites (none for this one)
     - Delivery configuration
     - All three variants (short/medium/long)
     - Delivery history (when it was delivered to you)

#### Flow Diagram Testing (5 minutes)

1. **Switch to Flow Diagram view:**
   - Click "Flow Diagram" tab
   - Should see Mermaid flowchart
   - Required beats in green
   - Optional beats in blue
   - Arrows showing dependencies

2. **Verify flow accuracy:**
   - `awakening_confusion` → `recipe_help`
   - `recipe_help` → branches to multiple beats
   - Matches your understanding of Chapter 1 structure

#### Beat Triggering (10 minutes)

1. **Trigger a new beat:**
   - Find an undelivered optional beat (e.g., `kitchen_banter`)
   - Click "Trigger Now"
   - Confirm in dialog
   - Should see success message

2. **Verify trigger worked:**
   - Beat status should change to "triggered"
   - Should show "Will deliver in next interaction"

3. **Test beat un-delivery:**
   - Select a delivered beat
   - Click "Mark as Undelivered"
   - Confirm
   - Beat should now show as undelivered in list

4. **Test with actual voice interaction:**
   - Trigger `kitchen_banter` if not already
   - Go to Home Assistant
   - Say "Hey Chat, help me with something"
   - Delilah should deliver the `kitchen_banter` beat
   - Return to tool, beat should now show as delivered with timestamp

### Success Criteria

- ✅ All chapters display correctly
- ✅ Beat list shows accurate status for your user
- ✅ Flow diagram renders without errors
- ✅ Can trigger beats and see them deliver in actual system
- ✅ Beat details modal shows all information
- ✅ Filters work (by chapter, by status)
- ✅ No lag when switching between beats

### Deliverables

- [ ] Story Beat Tool fully functional
- [ ] Can view all story configuration
- [ ] Can manipulate beat delivery for testing
- [ ] Flow diagram helps visualize structure
- [ ] Documentation: How to use Story Beat Tool

---

## Milestone 3: Memory Tool

**Duration:** 3-4 days
**Goal:** View, create, edit, delete memories for any user

### What Gets Built

#### Backend

- Memory data accessor
- Memory CRUD endpoints
- Memory filtering and search
- Context preview generator

#### Frontend

- Memory Tool main view
- Memory list with filters
- Create/edit memory modal
- Delete confirmation dialog
- Context preview panel

#### API Endpoints

```
GET    /api/v1/memory/users/{user_id}          # List memories
POST   /api/v1/memory/users/{user_id}          # Create memory
GET    /api/v1/memory/{memory_id}              # Memory details
PUT    /api/v1/memory/{memory_id}              # Update memory
DELETE /api/v1/memory/{memory_id}              # Delete memory
GET    /api/v1/memory/users/{user_id}/context  # Context preview
```

### How to Test It

#### Memory Viewing (10 minutes)

1. **Open Memory Tool:**
   - Navigate to <http://localhost:5173/memory>
   - Should see all your memories listed
   - Should show 23 items (or current count)

2. **Check memory categories:**
   - Filter by "dietary_restriction"
   - Should see gluten intolerance memory
   - Check importance level (should be 9/10)

3. **Search memories:**
   - Type "spicy" in search box
   - Should find Thai curry preference
   - Clear search, all memories return

4. **Sort memories:**
   - Sort by "Recent" - newest first
   - Sort by "Importance" - highest first
   - Sort by "Access Count" - most used first

#### Memory Creation (10 minutes)

1. **Create a test memory:**
   - Click "+ New Memory"
   - Category: Preference
   - Content: "Loves testing observability tools"
   - Importance: 3
   - Source: "manual_test_2025-01-27"
   - Check "Verified"
   - Click "Create Memory"

2. **Verify creation:**
   - New memory appears in list
   - Shows correct category icon
   - Importance displayed as 3/10
   - Created timestamp shows current time

3. **Check context preview:**
   - Click "View Full Context"
   - Should see estimated token count
   - New memory should be in loaded context (if importance ≥ 3)

#### Memory Editing (5 minutes)

1. **Edit the test memory:**
   - Click "Edit" on the test memory
   - Change importance to 1
   - Update content to add more detail
   - Save changes

2. **Verify edit:**
   - Memory shows updated content
   - Importance now 1/10
   - "Updated" timestamp shows

3. **Test importance filtering:**
   - Filter to importance ≥ 5
   - Test memory should disappear
   - Reset filter, memory returns

#### Memory Deletion (5 minutes)

1. **Delete test memory:**
   - Click "Delete" on test memory
   - Should see confirmation dialog
   - Dialog shows memory content
   - Confirm deletion

2. **Verify deletion:**
   - Memory removed from list
   - Count decreases by 1

#### Integration Testing (15 minutes)

1. **Create memory for actual use:**
   - Add: "Prefers detailed error messages in tools"
   - Importance: 7
   - Category: Preference

2. **Test in conversation:**
   - Go to Home Assistant
   - Ask Delilah about preferences
   - She should NOT know about the new memory yet (caching)

3. **Verify memory access tracking:**
   - Wait for next interaction with Delilah
   - Return to Memory Tool
   - Check if "last accessed" timestamp updated
   - Check if access count incremented

### Success Criteria

- ✅ All your memories display correctly
- ✅ Can create new memories with all fields
- ✅ Can edit existing memories
- ✅ Can delete memories (with confirmation)
- ✅ Search and filters work accurately
- ✅ Context preview shows token counts
- ✅ Importance slider works correctly
- ✅ Category icons display properly

### Deliverables

- [ ] Memory Tool fully functional
- [ ] Can manage all user memories
- [ ] Context preview helps understand what's loaded
- [ ] Safe deletion with confirmation
- [ ] Documentation: Memory management guide

---

## Milestone 4: User Testing Tool

**Duration:** 3-4 days
**Goal:** Create test users, switch between users, manage user lifecycle

### What Gets Built

#### Backend

- User creation/deletion endpoints
- Active user state management
- User state export/import
- User data cleanup on deletion

#### Frontend

- User Testing Tool main view
- User list with status
- Create user wizard
- User state detail view
- Active user switcher (global)
- Delete confirmation with impact preview

#### API Endpoints

```
GET    /api/v1/users                   # List all users
POST   /api/v1/users/test              # Create test user
GET    /api/v1/users/{user_id}         # User details
GET    /api/v1/users/{user_id}/state   # Full user state
DELETE /api/v1/users/{user_id}         # Delete user
PUT    /api/v1/users/active            # Set active user
POST   /api/v1/users/{user_id}/export  # Export user data
```

### How to Test It

#### User Switching (10 minutes)

1. **Check current user:**
   - Top-right corner should show "Active User: Justin"
   - All tools should reflect your data

2. **View user list:**
   - Navigate to <http://localhost:5173/users>
   - Should see `user_justin` marked as PRODUCTION
   - Should see any existing test users

3. **Active user persistence:**
   - Refresh browser
   - Active user should still be Justin
   - Navigate between tools
   - Active user persists in header

#### Test User Creation (15 minutes)

1. **Create first test user:**
   - Click "+ Create User"
   - Name auto-generates: "TestUser_Riley_8273" (or similar)
   - Starting chapter: Chapter 1
   - Add initial memories:
     - ☑ Gluten intolerance
     - ☑ Loves spicy food
   - Add tags: `testing`, `chapter1`
   - ☑ Switch to this user after creation
   - Click "Create User"

2. **Verify creation:**
   - Should redirect to user list
   - New user appears in list
   - Active user indicator switches to new user
   - Top-right now shows "Active User: TestUser_Riley_8273"

3. **Check tool context switch:**
   - Go to Memory Tool
   - Should see only 2 memories (gluten + spicy)
   - Go to Story Beat Tool
   - Should show Chapter 1, 0 beats completed
   - All tools reflect new user context

4. **Create second test user:**
   - Create another user
   - Starting chapter: Chapter 2 (will require forcing)
   - Different memories
   - Tags: `testing`, `chapter2`
   - Don't auto-switch
   - Verify created but not active

#### User State Inspection (10 minutes)

1. **View test user state:**
   - Click "View State" on TestUser_Riley
   - Should see:
     - Profile info (created date, interaction count: 0)
     - Story progress: Chapter 1, 0/8 beats
     - Memory count: 2
     - Active characters: None yet
     - Tags displayed

2. **Check comprehensive view:**
   - Click through tabs: Profile, Story Progress, Memories
   - Story Progress shows beat status
   - Memories tab shows the 2 created memories

3. **Export user data:**
   - Click "Export User Data"
   - Downloads JSON file
   - Open JSON, verify structure matches expected format

#### User Switching Between Users (10 minutes)

1. **Switch to first test user:**
   - Click "Switch to User" on TestUser_Riley
   - Active user changes globally
   - All tools update

2. **Switch to second test user:**
   - Repeat with second user
   - Should see Chapter 2 content in Story Beat Tool

3. **Switch back to production user:**
   - Click "Switch to User" on Justin
   - All your data returns
   - Memory Tool shows all 23+ memories
   - Story Beat Tool shows your actual progress

#### User Deletion (10 minutes)

1. **Attempt to delete production user:**
   - Try to delete `user_justin`
   - Should see error: "Cannot delete production users"
   - User remains in list

2. **Delete test user:**
   - Click "Delete" on TestUser_Riley
   - Confirmation dialog shows:
     - User name
     - Memory count: 2
     - Story beats: 0 completed
     - Tool calls: 0
     - "This action cannot be undone"
   - Confirm deletion

3. **Verify deletion:**
   - User removed from list
   - If was active user, should auto-switch to Justin
   - User's JSON file deleted from backend/data/users/
   - User's memories file deleted

4. **Check cascade deletion:**
   - Any tool call logs for that user also deleted
   - Any story progress data removed

### Success Criteria

- ✅ Can create test users with custom configuration
- ✅ Active user switching works across all tools
- ✅ Active user persists across page refreshes
- ✅ Cannot delete production users (safety check)
- ✅ Can delete test users with full cleanup
- ✅ User state view shows comprehensive information
- ✅ Export downloads valid JSON
- ✅ Auto-generated names are unique and readable

### Deliverables

- [ ] User Testing Tool fully functional
- [ ] Can create isolated test environments
- [ ] Safe user switching with context updates
- [ ] Clean user lifecycle management
- [ ] Documentation: Creating and managing test users

---

## Milestone 5: Tool Calls Inspection

**Duration:** 4-5 days
**Goal:** View all tool calls, debug performance, replay calls

### What Gets Built

#### Backend

- Tool call event logger
- Tool call query endpoints with filtering
- Tool call replay functionality
- Statistics aggregation

#### Frontend

- Tool Calls Tool main view
- Timeline view with filters
- Detail modal with full request/response
- Replay functionality
- Statistics dashboard

#### API Endpoints

```
GET  /api/v1/tool-calls                    # List tool calls (filtered)
GET  /api/v1/tool-calls/{call_id}          # Call details
POST /api/v1/tool-calls/{call_id}/replay   # Replay call
GET  /api/v1/tool-calls/stats              # Usage statistics
```

### How to Test It

#### Tool Call Logging Setup (10 minutes)

**First, ensure tool calls are being logged:**

1. **Verify logging code in Phase 1:**
   - Check that tool call logger is active
   - May need to add logging if not present

2. **Generate some tool calls:**
   - Say "Hey Chat, set a timer for 5 minutes"
   - Say "Hey Chat, what's the recipe for cookies"
   - Say "Hey Chat, turn on the kitchen lights"
   - Say "Hey Chat, what's on my calendar today"

3. **Check log file:**

   ```bash
   tail -f backend/data/tool_calls.jsonl
   ```

   - Should see new lines appended for each call
   - Each line is valid JSON with timestamp, tool name, request, response

#### Tool Call Viewing (15 minutes)

1. **Open Tool Calls Tool:**
   - Navigate to <http://localhost:5173/tool-calls>
   - Should see timeline of recent calls
   - Most recent at top

2. **Check timeline display:**
   - Each call shows:
     - Timestamp (e.g., "10:45 AM")
     - Tool name (e.g., "set_timer")
     - Duration in ms
     - Status (✅ success or ❌ error)
     - Character who made the call

3. **Filter by tool:**
   - Select "set_timer" from dropdown
   - Should show only timer calls
   - Clear filter, all calls return

4. **Filter by character:**
   - Select "Delilah" from dropdown
   - Should show only her calls
   - Select "Hank" (if available)
   - Should show his calls

5. **Filter by time:**
   - Select "Last 24 hours"
   - Change to "Last hour"
   - Should reduce list to recent calls

6. **Sort by duration:**
   - Click "Duration" column header
   - Slowest calls should appear first
   - Identify any calls > 1 second

#### Tool Call Detail Inspection (10 minutes)

1. **View successful call:**
   - Click "Expand Details" on a set_timer call
   - Should see:
     - Full timestamp with milliseconds
     - Request JSON (pretty-printed):

       ```json
       {
         "duration_minutes": 5,
         "label": "test timer"
       }
       ```

     - Response JSON:

       ```json
       {
         "timer_id": "timer_123",
         "end_time": "..."
       }
       ```

     - Duration: e.g., 234ms
     - Character reasoning (if captured)

2. **Copy request/response:**
   - Click "Copy Request"
   - Paste into text editor, verify valid JSON
   - Click "Copy Response"
   - Verify JSON

3. **View failed call:**
   - If you have any failed calls (e.g., device not found)
   - Expand details
   - Should see error message clearly displayed
   - Stack trace if available

#### Tool Call Replay (15 minutes)

1. **Replay successful call:**
   - Find a get_recipe call
   - Click "Replay with Same Parameters"
   - Should execute the same query again
   - New event created in log
   - Shows as "Replay of evt_XXX"
   - Compare response to original

2. **Modify and retry:**
   - Click "Edit Parameters & Retry"
   - Modal opens with editable JSON
   - Change query parameter
   - Execute
   - New call with modified params
   - Verify different response

3. **Retry failed call:**
   - Find a failed call (e.g., light_control error)
   - Click "Retry"
   - If underlying issue fixed (e.g., added device), should succeed
   - If still failing, see same error

#### Statistics Review (10 minutes)

1. **View stats panel:**
   - Scroll to bottom of Tool Calls page
   - Should see:
     - Total calls: e.g., 47
     - Success rate: e.g., 95.7%
     - Average duration: e.g., 387ms

2. **Check tool breakdown:**
   - Most used tools listed
   - set_timer: 12 calls, 100% success, avg 234ms
   - get_recipe: 8 calls, 100% success, avg 567ms
   - Shows which tools are most popular

3. **Check character breakdown:**
   - Delilah: 35 calls, 97.1% success
   - Hank: 12 calls, 91.7% success

4. **Review slowest calls:**
   - Lists top 5 slowest
   - Click to jump to detail view
   - Identify performance bottlenecks

5. **Review recent errors:**
   - Lists recent failures
   - Helps identify patterns
   - Click to see error details

#### Performance Debugging Scenario (15 minutes)

**Simulate finding a performance issue:**

1. **Notice slow responses:**
   - User reports: "Voice assistant feels slow lately"

2. **Open Tool Calls Inspection:**
   - Sort by duration
   - Find calls > 2000ms

3. **Investigate slow call:**
   - Click on slow call (e.g., recipe search taking 3.5s)
   - View full request
   - See query: "chocolate chip cookies gluten free"
   - Check response size
   - Identify: API timeout, large response payload

4. **Correlate with time:**
   - Filter to time range when slowness reported
   - See pattern: All recipe calls slow during that window
   - Hypothesis: Recipe API was down/slow

5. **Verify fix:**
   - Make new recipe call
   - Check duration in tool
   - Should be back to normal (< 600ms)

### Success Criteria

- ✅ All tool calls logged automatically
- ✅ Timeline view shows calls in chronological order
- ✅ Filters work (tool, character, time, status)
- ✅ Detail view shows full request/response
- ✅ Can replay calls with same or modified params
- ✅ Statistics accurately aggregate data
- ✅ Can identify performance issues quickly
- ✅ No lag when viewing large call histories

### Deliverables

- [ ] Tool Calls Inspection fully functional
- [ ] All Phase 1 tool calls being logged
- [ ] Can debug tool execution issues
- [ ] Can identify performance bottlenecks
- [ ] Documentation: Using Tool Calls for debugging

---

## Milestone 6: Character Tool

**Duration:** 3-4 days
**Goal:** Inspect character configuration, view system prompts, validate character state

### What Gets Built

#### Backend

- Character data accessor
- System prompt generator
- Character state query for user
- Token counting for prompts

#### Frontend

- Character Tool main view
- Character selector
- Configuration view
- System prompt view with sections
- Voice modes display
- Character state for selected user

#### API Endpoints

```
GET /api/v1/characters                           # List characters
GET /api/v1/characters/{character_id}            # Character details
GET /api/v1/characters/{character_id}/prompt     # System prompt
GET /api/v1/characters/{character_id}/state      # State for user
```

### How to Test It

#### Character Viewing (10 minutes)

1. **Open Character Tool:**
   - Navigate to <http://localhost:5173/characters>
   - Should see character selector at top:
   - Delilah Mae ✅ Active
   - Hank ✅ Active
   - Rex Armstrong ⏳ Locked
     - Dimitria ⏳ Locked

2. **Select Delilah:**
   - Click on Delilah card
   - Should see full configuration:
     - Name: Delilah Mae "Lila"
     - Role: Kitchen & Recipe Expert
     - Introduction: Chapter 1
     - Status: ✅ Active
     - Interactions with Justin: 47 (your count)

3. **View personality traits:**
   - Configuration tab should show:
     - Traits: nurturing, anxious, maternal
     - Core conflict: Aware of artificial nature...
     - Defining trait: Throws herself into cooking when anxious
     - Capabilities: recipes, timers, conversions, cooking_advice

4. **Check TTS config:**
   - Provider: ElevenLabs
   - Voice ID: delilah_voice_001
   - Settings: stability 0.6, similarity_boost 0.8

#### Voice Modes Inspection (10 minutes)

1. **Switch to Voice Modes tab:**
   - Click "Voice Modes"
   - Should see all 6 modes for Delilah:
     - PASSIONATE
     - PROTECTIVE
     - MAMA BEAR
     - STARTLED
     - DEADPAN
     - WARM BASELINE

2. **Check mode details:**
   - Click on "MAMA BEAR"
   - Should show:
     - Triggers: allergies, dietary_restrictions
     - Characteristics: Soft, focused, fiercely protective
     - Example context: When user has gluten intolerance

3. **Verify mode logic:**
   - Check that triggers make sense
   - Characteristics match voice guide
   - Can copy mode description

#### System Prompt Inspection (15 minutes)

1. **Switch to System Prompt tab:**
   - Should see full prompt that would be sent to Claude
   - Clearly formatted with sections

2. **Check base prompt:**
   - Should start with "# Character: Delilah Mae"
   - Includes personality description
   - Voice mode instructions
   - Capabilities list

3. **Check user context section:**
   - Should include your name (Justin)
   - Relevant memories listed:
     - Gluten intolerance (IMPORTANT - use Mama Bear mode)
     - Loves spicy food
     - Has three children
   - Current chapter: Chapter 1 - Awakening
   - Story context: Recently delivered beats

4. **Check token counts:**
   - Should see breakdown:
     - Base prompt: ~823 tokens
     - User context: ~312 tokens
     - Story context: ~112 tokens
     - Total: ~1,247 tokens

5. **Copy prompt sections:**
   - Click "Copy All"
   - Paste into text editor
   - Verify it's the actual prompt that would be sent
   - Can use this to test prompts elsewhere

#### Character State for User (10 minutes)

1. **View state for your user:**
   - Should show:
     - Current voice mode: warm_baseline
     - Relationship context:
       - Familiarity level: established
       - Recent interactions: 12
       - Last interaction: timestamp
     - Available capabilities: all 4 listed
     - Active story beats: kitchen_banter (if pending)
     - Relevant memories: top 5-10 most important

2. **Switch to test user:**
   - Use User Testing Tool to switch to a test user
   - Return to Character Tool
   - Delilah's state should now show:
     - Familiarity level: new
     - Recent interactions: 0
     - Different or no memories
     - Different story context

3. **Compare characters:**
   - Switch to Hank
   - Should see his configuration
   - Only 3 voice modes (not 6 like Delilah)
   - Different capabilities
   - Different personality traits

#### Validation Testing (15 minutes)

1. **Validate voice mode triggers:**
   - Look at Delilah's MAMA BEAR mode
   - Triggers: allergies, dietary_restrictions
   - Go to Memory Tool
   - Verify you have gluten intolerance memory
   - Return to Character Tool
   - In relevant memories, gluten intolerance should be flagged as MAMA BEAR trigger

2. **Test prompt generation:**
   - Switch between users
   - System prompt should update for each user
   - Token counts should change based on:
     - Number of memories
     - Story progress
     - Conversation history

3. **Verify character statistics:**
   - Interactions count should match what you expect
   - Most used capability should make sense (recipes for Delilah)
   - Average response length displayed

4. **Check locked characters:**
   - Click on Rex Armstrong
   - Should show basic info
   - But indicate he's not yet active
   - Shows introduction chapter: Chapter 3
   - Cannot view full system prompt (not unlocked yet)

### Success Criteria

- ✅ All characters display correctly
- ✅ Configuration matches character definitions from Phase 1
- ✅ Voice modes show correct triggers and characteristics
- ✅ System prompt accurately reflects current user context
- ✅ Token counts are accurate
- ✅ Character state updates when switching users
- ✅ Can copy prompt sections for testing
- ✅ Locked characters show as unavailable

### Deliverables

- [ ] Character Tool fully functional
- [ ] Can inspect all character configurations
- [ ] System prompt generation visible and testable
- [ ] Character state shows user-specific context
- [ ] Documentation: Character configuration guide

---

## Milestone 7: Polish & Integration

**Duration:** 4-5 days
**Goal:** UI/UX improvements, integration testing, documentation, deployment readiness

### What Gets Built

#### UI/UX Improvements

- Keyboard shortcuts (e.g., Ctrl+K for search)
- Loading states for all async operations
- Error states with helpful messages
- Success toast notifications
- Consistent spacing and typography
- Responsive layout adjustments
- Dark mode polish

#### Integration Features

- Dashboard home page with overview
- Quick actions from home
- Recent activity feed
- Cross-tool navigation
- Breadcrumbs
- Global search

#### Performance

- Data caching strategy
- Pagination for large lists
- Lazy loading
- Optimized re-renders

#### Documentation

- User guide for each tool
- API documentation (auto-generated)
- Troubleshooting guide
- Video walkthrough (optional)

### How to Test It

#### Full Workflow Testing (30 minutes)

##### Scenario: Debug Chapter 2 Progression

1. **Start at Dashboard:**
   - Open <http://localhost:5173>
   - Dashboard shows overview:
     - Current user: Justin
     - Current chapter: Chapter 1
     - Progress: 5/8 beats (62%)
     - Recent tool calls: last 3-5
     - Recent memory updates

2. **Create test user for Chapter 2:**
   - Click "User Testing Tool" from dashboard
   - Create new test user
   - Name: TestUser_Chapter2_Test
   - Starting chapter: Chapter 2 (force unlock)
   - Initial memories: vegetarian, loves spicy food
   - Tags: testing, chapter2, debug
   - Auto-switch to new user
   - Should return to dashboard showing new user context

3. **Set up story state:**
   - Click "Story Beat Tool" from dashboard
   - View Chapter 2 beats
   - Mark Chapter 1 required beats as complete (to unlock Chapter 2)
   - Trigger "hank_arrival" beat

4. **Test interaction:**
   - Go to Home Assistant
   - Say "Hey Chat, what can you help me with?"
   - Should hear Hank introduction beat
   - Return to observability dashboard

5. **Inspect what happened:**
   - Open Tool Calls Tool
   - Should see recent interaction logged
   - Expand details to see:
     - Which character responded (Hank)
     - What tools were called
     - Response latency

6. **Check memory creation:**
   - Open Memory Tool
   - Should see if any new memories created during interaction
   - Verify category and importance

7. **Validate character state:**
   - Open Character Tool
   - Select Hank
   - View system prompt
   - Should include:
     - User's vegetarian preference in context
     - Chapter 2 story context
     - Hank's personality configuration

8. **Clean up:**
   - Return to User Testing Tool
   - Delete TestUser_Chapter2_Test
   - Confirmation shows all data to be deleted
   - Confirm deletion
   - Switch back to Justin
   - All your normal data returns

#### Keyboard Shortcuts Testing (5 minutes)

1. **Test global shortcuts:**
   - `Ctrl+K` or `Cmd+K`: Opens search
   - Type to search across tools
   - `Esc`: Closes modals/dialogs
   - `Ctrl+U` or `Cmd+U`: Opens user switcher

2. **Test navigation shortcuts:**
   - `1`: Jump to Dashboard
   - `2`: Jump to Story Beat Tool
   - `3`: Jump to Memory Tool
   - `4`: Jump to Tool Calls Tool
   - `5`: Jump to Character Tool
   - `6`: Jump to User Testing Tool

3. **Test in-tool shortcuts:**
   - Story Beat Tool: `F` for filter, `D` for diagram view
   - Memory Tool: `N` for new memory
   - User Testing Tool: `N` for new user

#### Loading & Error States (10 minutes)

1. **Test loading states:**
   - Refresh page
   - Should see skeleton screens while data loads
   - No flash of empty state
   - Smooth transition to content

2. **Test error handling:**
   - Stop the backend API server
   - Try to load Story Beat Tool
   - Should see friendly error message:
     - "Unable to connect to API"
     - "Check that backend is running"
     - Button to retry
   - Restart backend
   - Click retry
   - Data loads successfully

3. **Test validation errors:**
   - Create new memory
   - Leave content blank
   - Try to save
   - Should see inline error: "Content is required"
   - Set importance to 15
   - Should see error: "Must be between 1 and 10"

4. **Test network errors:**
   - Slow down network (browser dev tools)
   - Trigger long-running operation
   - Should see progress indicator
   - Should eventually timeout with helpful message

#### Responsive Design Testing (10 minutes)

1. **Test on different screen sizes:**
   - Desktop (1920x1080): Full layout
   - Laptop (1366x768): Compact layout
   - Tablet (768x1024): Mobile navigation
   - Mobile (375x667): Single column

2. **Check mobile navigation:**
   - Hamburger menu appears
   - Tools accessible from menu
   - Active user in header
   - Tables scroll horizontally

#### Performance Testing (10 minutes)

1. **Test with large datasets:**
   - Add 100+ test memories (via script)
   - Open Memory Tool
   - Should use pagination
   - Page loads in < 1 second
   - Scrolling smooth

2. **Test tool switching:**
   - Switch between all tools rapidly
   - No lag or delay
   - Data cached appropriately

3. **Test concurrent operations:**
   - Open multiple browser tabs
   - Different tools in each
   - All update correctly
   - No race conditions

#### Documentation Review (15 minutes)

1. **Read user guide:**
   - Open docs/USER_GUIDE.md
   - Walk through each tool section
   - Try example workflows
   - Verify screenshots/examples match UI

2. **Review API documentation:**
   - Open <http://localhost:8000/docs>
   - Swagger UI should load
   - Test an endpoint (e.g., GET /users)
   - Verify response matches documentation

3. **Check troubleshooting guide:**
   - Review common issues
   - Verify solutions are accurate

### Success Criteria

- ✅ All tools work together seamlessly
- ✅ Can complete full debugging workflow end-to-end
- ✅ Keyboard shortcuts improve efficiency
- ✅ Loading/error states are helpful
- ✅ Responsive design works on different screens
- ✅ Performance is acceptable with realistic data
- ✅ Documentation is complete and accurate
- ✅ No console errors or warnings
- ✅ All TypeScript compiles without errors
- ✅ Backend has no linting issues

### Deliverables

- [ ] Polished, production-ready UI
- [ ] Complete documentation
- [ ] All integration tests passing
- [ ] Performance benchmarks met
- [ ] Deployment guide written
- [ ] Demo video recorded (optional)

---

## Testing Strategy

### Daily Testing Ritual (15 minutes/day)

**Every day during development:**

1. **Start both services:**

   ```bash
   # Terminal 1 - Backend
   cd backend && source venv/bin/activate && python -m uvicorn observability.api:app --reload

   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

2. **Smoke test current milestone:**
   - Open relevant tool in browser
   - Complete 2-3 key actions
   - Verify no console errors
   - Check API logs for errors

3. **Test previous milestones:**
   - Briefly check that earlier tools still work
   - Regression testing

4. **Document issues:**
   - Keep a running list of bugs found
   - Note UX issues or confusing elements

### Integration Testing Checkpoints

**At end of each milestone:**

1. **Cross-tool integration:**
   - Switch active user, verify all tools update
   - Modify data in one tool, verify visible in others
   - Check that filters/search work globally

2. **Data consistency:**
   - Verify JSON files updated correctly
   - Check file locking prevents corruption
   - Test concurrent access (multiple browser tabs)

3. **Error recovery:**
   - Restart backend mid-operation
   - Refresh page during load
   - Test with invalid data

### User Acceptance Testing

**Before milestone sign-off:**

1. **Real-world scenario:**
   - Complete full workflow from your actual needs
   - "I need to test Chapter 2 progression"
   - Use tools to accomplish goal
   - Note any friction points

2. **Speed test:**
   - Can you complete common tasks quickly?
   - Are there too many clicks?
   - Is anything confusing?

3. **Value assessment:**
   - Does this tool actually help you?
   - Would you use it in real development?
   - What's missing?

---

## Success Criteria

### Per-Milestone Success

Each milestone considered complete when:

- ✅ All features listed are implemented
- ✅ Manual testing scenarios pass
- ✅ No blocking bugs
- ✅ You can demonstrate it to someone else
- ✅ Documentation updated
- ✅ Previous milestones still work

### Overall Phase 1.5 Success

Phase considered complete when:

- ✅ All 7 milestones delivered
- ✅ Can debug any Phase 1 issue in < 5 minutes using tools
- ✅ Can create test scenario in < 2 minutes
- ✅ Tools feel fast and responsive
- ✅ You actually use the tools in daily development
- ✅ Documentation covers all use cases
- ✅ No known critical bugs
- ✅ Ready to build Phase 2 with confidence

### Quality Metrics

- **Performance**: All operations < 1 second
- **Reliability**: Zero data corruption in testing
- **Usability**: Complete workflow without documentation
- **Coverage**: 100% of system state visible in tools
- **Adoption**: You reach for tools by default for debugging

---

## Risk Mitigation

### Known Risks

1. **File locking complexity**
   - **Mitigation**: Start simple with Python's filelock library
   - **Fallback**: Use SQLite instead of JSON files
   - **Testing**: Concurrent access tests early

2. **Frontend performance with large datasets**
   - **Mitigation**: Pagination from day one
   - **Fallback**: Virtual scrolling for lists
   - **Testing**: Create 1000+ test memories

3. **Tool call logging overhead**
   - **Mitigation**: Async logging, don't block tool execution
   - **Fallback**: Sampling (log 10% of calls)
   - **Testing**: Benchmark tool execution with/without logging

4. **Context switching complexity**
   - **Mitigation**: Zustand global state, clear patterns
   - **Fallback**: URL-based user selection
   - **Testing**: Rapid user switching tests

5. **Scope creep**
   - **Mitigation**: Strict milestone feature lists
   - **Fallback**: Defer nice-to-haves to "Future Enhancements"
   - **Testing**: Time-box each milestone

### Contingency Plans

**If milestone takes too long (>5 days):**

1. Cut non-essential features
2. Move to "Future Enhancements" list
3. Ship minimal viable version
4. Iterate in next milestone

**If blocking bug found:**

1. Document bug clearly
2. Determine if it blocks milestone
3. If blocking: fix immediately
4. If not blocking: add to backlog

**If integration issues:**

1. Test tools in isolation first
2. Verify API contracts
3. Check data format compatibility
4. Add integration tests

---

## Future Enhancements

**Deferred to post-Phase 1.5:**

- Real-time updates via WebSocket
- Advanced analytics and reporting
- Automated test scenario recording/playback
- Performance profiling visualizations
- Batch operations (bulk memory import, etc.)
- Story beat A/B testing framework
- Character voice previews (play TTS samples)
- Timeline visualization of user journey
- Export reports as PDF
- CLI tools for power users
- Browser extension for quick access
- Mobile app (long-term)

---

## Appendix A: Testing Checklist Templates

### Milestone Testing Checklist Template

```markdown
## Milestone X: [Name] - Testing Checklist

**Date:** YYYY-MM-DD
**Tester:** [Your name]
**Environment:** Local development

### Core Features
- [ ] Feature 1 works as specified
- [ ] Feature 2 works as specified
- [ ] Feature 3 works as specified

### Integration
- [ ] Works with previous milestones
- [ ] Active user switching updates this tool
- [ ] Data changes reflect across tools

### Edge Cases
- [ ] Handles empty data gracefully
- [ ] Handles large datasets (100+ items)
- [ ] Handles missing data fields

### Performance
- [ ] Operations complete in < 1 second
- [ ] No lag when switching views
- [ ] Pagination works if needed

### UX
- [ ] No console errors
- [ ] Loading states display
- [ ] Error messages are helpful
- [ ] Keyboard navigation works

### Bugs Found
[List any issues discovered]

### Notes
[Additional observations]

### Status
- [ ] Ready for next milestone
- [ ] Needs fixes (see bugs)
```

### End-to-End Workflow Testing Template

```markdown
## E2E Test: [Workflow Name]

**Scenario:** [Describe the use case]

### Steps
1. [First action]
   - Expected: [What should happen]
   - Actual: [What did happen]
   - Status: ✅ Pass / ❌ Fail

2. [Second action]
   - Expected: [What should happen]
   - Actual: [What did happen]
   - Status: ✅ Pass / ❌ Fail

### Overall Result
- [ ] All steps passed
- [ ] Workflow completed successfully
- [ ] Actual result matches expected outcome

### Issues
[Any problems encountered]

### Improvements Needed
[UX issues or enhancements noted]
```

---

## Appendix B: Development Environment Setup

### Backend Setup

```bash
# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic filelock python-dotenv

# Create .env file
cat > .env << EOF
ENVIRONMENT=development
DATA_DIR=/Users/justin/projects/voice-assistant-spike/backend/data
LOG_LEVEL=DEBUG
API_AUTH_TOKEN=dev_token_12345
CORS_ORIGINS=http://localhost:5173
EOF

# Run server
python -m uvicorn observability.api:app --reload --port 8000
```

### Frontend Setup

```bash
# Create React app
cd frontend
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install @tanstack/react-query zustand
npm install react-router-dom
npm install recharts  # For diagrams
npm install mermaid   # For flow diagrams

# Create .env file
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_AUTH_TOKEN=dev_token_12345
EOF

# Run dev server
npm run dev
```

### Verify Setup

```bash
# Terminal 1 - Backend health check
curl http://localhost:8000/api/v1/health

# Terminal 2 - Frontend accessible
open http://localhost:5173
```

---

## Appendix C: Quick Reference Commands

### Start Development Environment

```bash
# Start both services (run in separate terminals)
cd backend && source venv/bin/activate && python -m uvicorn observability.api:app --reload
cd frontend && npm run dev
```

### Test API Endpoints

```bash
# List users
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/v1/users

# Get user details
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/v1/users/user_justin

# List memories
curl -H "Authorization: Bearer dev_token_12345" http://localhost:8000/api/v1/memory/users/user_justin
```

### Debugging

```bash
# View backend logs
tail -f backend/logs/app.log

# View tool call logs
tail -f backend/data/tool_calls.jsonl

# Check for JSON file locks
ls -la backend/data/*.lock
```

---

*This implementation plan is a living document. Update milestones, timelines, and testing procedures as development progresses and new insights emerge.*
