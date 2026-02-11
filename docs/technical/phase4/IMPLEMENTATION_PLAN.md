# Phase 4: Story System Testing & Refinement - Implementation Plan

**Version:** 1.1
**Last Updated:** 2026-02-11
**Status:** ✅ Completed

---

## References

- **PRD**: [PRD.md](PRD.md) - Product requirements and user stories
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design and system components
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md) - Manual test procedures

---

## Overview

### Goals

Make the story system production-ready by fixing beat delivery issues, enhancing story engine capabilities with auto-advance and conditional progression, and expanding content through Chapter 1 and 2 with Delilah and Hank.

### Timeline Estimate

- **Total Duration:** 2 weeks (10-12 days)
- **Milestone Count:** 4 milestones
- **Milestone Cadence:** 2-3 days per milestone
- **Target Completion:** 2026-02-18

### Success Criteria (Phase Level)

- ✅ All 4 milestones complete
- ✅ Can complete Chapter 1 → Chapter 2 through natural conversation
- ✅ Story developer iteration loop < 5 minutes
- ✅ All features tested manually with documented procedures
- ✅ No regressions in existing Phase 1-3 functionality

---

## Milestone 1: Fix Beat Delivery & UI Updates

**Status:** ✅ Complete
**Duration:** 2-3 days
**Goal:** Diagnose and fix why beats don't trigger after the first one, implement real-time UI updates
**Completed:** 2026-02-06

---

### What Gets Built

#### Backend Components

- **Beat Trigger Diagnostics** - Enhanced logging and debugging
  - File: `backend/src/core/story_engine.py`
  - Purpose: Add extensive logging to diagnose trigger evaluation failures
  - Key methods: `evaluate_triggers()`, `_check_trigger_conditions()`, `_log_trigger_evaluation()`

- **Story State Atomic Updates** - Ensure state changes are atomic
  - File: `backend/src/observability/story_access.py`
  - Purpose: Prevent race conditions in state updates
  - Key methods: `atomic_update_user_story_state()`, `mark_beat_delivered_atomic()`

#### Frontend Components

- **Real-Time Polling** - Poll story progress every 3 seconds
  - File: `frontend/src/hooks/useStoryProgress.ts`
  - Purpose: Keep UI synchronized with backend state
  - Props: `userId`, `refetchInterval`

- **Diagram Legend** - Add color coding legend to flow diagram
  - File: `frontend/src/components/story-beat/DiagramLegend.tsx`
  - Purpose: Explain beat status colors
  - Props: None (static legend)

- **Per-User Diagram** - Show user-specific progress in diagram
  - File: `frontend/src/components/story-beat/ChapterFlowDiagram.tsx`
  - Purpose: Accept `userId` parameter and style nodes based on user progress
  - Props: `chapterId`, `userId`

#### API Endpoints

```
GET    /api/v1/story/chapters/{chapter_id}/diagram?user_id={user_id}  # Diagram with user progress
GET    /api/v1/story/users/{user_id}/progress                         # Real-time progress
```

---

### How to Test It

#### Backend Testing (20 minutes)

1. **Enable debug logging:**

   ```bash
   cd backend
   export LOG_LEVEL=DEBUG
   python -m uvicorn src.api:app --reload --port 8000
   ```

2. **Trigger Chapter 1 beats in order:**

   ```bash
   # Test awakening_confusion (should work - baseline)
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/awakening_confusion/trigger \
     -H "Authorization: Bearer dev_token_12345"

   # Test first_timer (was broken - should now work)
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/first_timer/trigger \
     -H "Authorization: Bearer dev_token_12345"

   # Test recipe_help (was broken - should now work)
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/recipe_help/trigger \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Each beat triggers successfully, logs show trigger evaluation steps

3. **Check state persistence:**

   ```bash
   # Get user progress
   curl http://localhost:8000/api/v1/story/users/test_user/progress \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** `beats_delivered` array includes all three beats

4. **Verify logs show:**
   - Beat trigger condition evaluation
   - State update operations
   - File write confirmations
   - No errors or warnings

#### Frontend Testing (15 minutes)

1. **Open Story Beat Tool:**
   - Navigate to <http://localhost:5173/story>
   - Should see Chapter 1 beats list

2. **Test real-time updates:**
   - Trigger a beat via API (use curl command above)
   - Watch Story Beat Tool (don't refresh)
   - Within 5 seconds, beat status should change to "Completed"

3. **Verify diagram legend:**
   - Switch to "Flow Diagram" tab
   - Legend should be visible showing:
     - 🟢 Completed (green)
     - 🟡 In Progress (yellow)
     - 🔵 Not Started (blue)
     - ⚫ Locked (gray)

4. **Test per-user progress:**
   - Create second test user: `test_user_2`
   - Trigger different beats for each user
   - Switch between users in dropdown
   - Diagram should show different colored nodes for each user

#### Integration Testing (10 minutes)

1. **Test through conversation:**
   - Start conversation with test user
   - Use keywords to trigger beats naturally
   - Verify beats appear in conversation response
   - Check Story Beat Tool updates within 5 seconds

2. **Test edge cases:**
   - Trigger same beat twice (should fail with clear error)
   - Trigger beat with unmet prerequisites (should fail gracefully)
   - Rapid-fire trigger multiple beats (state should remain consistent)

### Success Criteria

- ✅ All Chapter 1 beats trigger successfully via API
- ✅ UI updates within 5 seconds of beat delivery
- ✅ Diagram has visible legend explaining all status colors
- ✅ Can switch users and see different progress states in diagram
- ✅ No race conditions or state corruption
- ✅ Logs clearly show trigger evaluation process

### Deliverables

- [x] Enhanced logging in story engine
- [x] Atomic state update operations
- [x] Real-time polling in frontend (3-5 second interval)
- [x] Diagram legend component
- [x] Per-user diagram API parameter
- [x] All Chapter 1 beats triggerable

---

## Milestone 2: Auto-Advance & Conditional Progression

**Status:** ✅ Complete
**Duration:** 2-3 days
**Goal:** Implement auto-advance beats and conditional progression (N of M beats)
**Completed:** 2026-02-04

---

### What Gets Built

#### Backend Components

- **Auto-Advance Detection** - Identify beats ready for auto-advance
  - File: `backend/src/core/story_engine.py`
  - Purpose: Check which auto-advance beats are ready to deliver
  - Key methods: `get_auto_advance_ready()`, `check_auto_advance_requirements()`

- **Conditional Progression** - N of M beat requirements
  - File: `backend/src/core/story_engine.py`
  - Purpose: Check if N of M optional beats are complete
  - Key methods: `check_conditional_progression()`, `count_completed_beats()`

- **Auto-Advance Queue** - Track ready auto-advance beats
  - File: `backend/src/models/story.py`
  - Purpose: Store beats ready for user-triggered delivery
  - Fields: `beat_id`, `ready_at`, `notified`

#### Frontend Components

- **Auto-Advance Notification** - Banner when beats are ready
  - File: `frontend/src/components/story-beat/AutoAdvanceNotification.tsx`
  - Purpose: Show sticky banner when auto-advance beats are ready
  - Props: `beats`, `onDeliver`

- **Conditional Requirements Display** - Show N of M progress
  - File: `frontend/src/components/story-beat/BeatDetail.tsx`
  - Purpose: Display conditional requirements in beat detail modal
  - Props: `beat`, `userProgress`

#### API Endpoints

```
GET    /api/v1/story/auto-advance-ready/{user_id}           # Get ready beats
POST   /api/v1/story/auto-advance/{user_id}/{beat_id}       # Deliver auto-advance beat
```

#### Data Models

```typescript
interface AutoAdvanceNotification {
  beat_id: string;
  name: string;
  chapter_id: number;
  ready_since: Date;
  content: string;  // Full content (no variants for auto-advance)
  notified: boolean;
}

interface ConditionalRequirement {
  type: 'requires_n_of_beats';
  n: number;
  beats: string[];
  current_count: number;
  satisfied: boolean;
}
```

---

### How to Test It

#### Auto-Advance Testing (20 minutes)

1. **Create test user with Chapter 2 unlocked:**

   ```bash
   # Create test user
   curl -X POST http://localhost:8000/api/v1/users/test \
     -H "Authorization: Bearer dev_token_12345" \
     -d '{"chapter": 2, "beats_delivered": ["all_chapter_1_beats"]}'
   ```

2. **Check auto-advance readiness:**

   ```bash
   curl http://localhost:8000/api/v1/story/auto-advance-ready/test_user \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Returns `hank_arrival` beat if Chapter 2 is unlocked

3. **Open Story Beat Tool:**
   - Should see sticky notification banner at top
   - Banner text: "Story Update Available: Hank's Arrival"
   - Preview of content visible

4. **Deliver auto-advance beat:**
   - Click "Continue Story" button in banner
   - Should see full beat content (richer than normal beats)
   - Banner disappears after delivery

5. **Verify in conversation:**
   - Next conversation should NOT deliver the beat again
   - Beat marked as delivered in Story Beat Tool

#### Conditional Progression Testing (20 minutes)

1. **Set up test scenario:**
   - Create user with 1 of 3 optional beats complete
   - `self_awareness` stage 3 requires 2 of 3 optional beats

2. **Check stage 3 availability:**

   ```bash
   curl http://localhost:8000/api/v1/story/users/test_user/beats/self_awareness \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Stage 3 shows as locked (requires 2 of 3, only 1 complete)

3. **Complete second optional beat:**

   ```bash
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/the_math_moment/trigger \
     -H "Authorization: Bearer dev_token_12345"
   ```

4. **Verify stage 3 now available:**

   ```bash
   curl http://localhost:8000/api/v1/story/users/test_user/beats/self_awareness \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Stage 3 now shows as available

5. **Check UI display:**
   - Open beat detail for `self_awareness`
   - Stage 3 should show: "Requires 2 of 3 optional beats (2/3 complete) ✅"
   - Progress bar shows 2/3 filled

#### Integration Testing (15 minutes)

1. **Test auto-advance + conversation:**
   - Have auto-advance beat ready
   - Start normal conversation
   - Beat should NOT trigger in conversation
   - Notification should persist until manually delivered

2. **Test conditional + progression:**
   - Complete exactly N of M beats
   - Next beat should unlock immediately
   - Can trigger and deliver the unlocked beat

### Success Criteria

- ✅ `hank_arrival` beat triggers via auto-advance (not conversation)
- ✅ Notification appears when auto-advance beat ready
- ✅ Clicking notification delivers full beat content
- ✅ `self_awareness` stage 3 requires 2 of 3 optional beats
- ✅ UI shows conditional requirements and current progress
- ✅ Auto-advance beats use single `content` field (no variants)

### Deliverables

- [x] Auto-advance detection logic (`story_engine.py:get_auto_advance_ready()`, `_check_auto_advance_beats()`)
- [x] Auto-advance queue in user state (`story.py:AutoAdvanceNotification`, `UserStoryState.auto_advance_queue`)
- [x] Conditional progression evaluation (`story_engine.py:check_conditional_progression()`)
- [x] Auto-advance notification UI component (`AutoAdvanceNotification.tsx`, `AutoAdvanceNotification.css`)
- [x] Auto-advance delivery functionality (`story_engine.py:deliver_auto_advance_beat()`)
- [x] API endpoints for auto-advance (`GET /story/auto-advance-ready/{user_id}`, `POST /story/auto-advance/{user_id}/{beat_id}`)
- [x] Integration into Story Beat Tool (polling, banner display)
- [x] Chapter progression updated to check conditional beats

---

## Milestone 3: Untrigger Functionality

**Status:** ✅ Complete
**Duration:** 1-2 days
**Goal:** Implement beat untrigger with dependency detection for fast iteration
**Completed:** 2026-02-05

---

### What Gets Built

#### Backend Components

- **Dependency Graph** - Build dependency tree for beats
  - File: `backend/src/core/story_engine.py`
  - Purpose: Find all beats that depend on a given beat
  - Key methods: `get_dependencies()`, `build_dependency_graph()`, `find_transitive_deps()`

- **Untrigger Operation** - Roll back beat delivery atomically
  - File: `backend/src/core/story_engine.py`
  - Purpose: Remove beat and all dependent beats from user state
  - Key methods: `untrigger_beat()`, `untrigger_beat_dry_run()`

#### Frontend Components

- **Untrigger Button** - Show on delivered beats
  - File: `frontend/src/components/story-beat/BeatRow.tsx`
  - Purpose: Allow rolling back beat delivery
  - Props: `beat`, `onUntrigger`

- **Untrigger Confirmation Modal** - Show impact before committing
  - File: `frontend/src/components/story-beat/UntriggerModal.tsx`
  - Purpose: Display dependency tree and get confirmation
  - Props: `beat`, `dependencies`, `onConfirm`, `onCancel`

#### API Endpoints

```
POST   /api/v1/story/users/{user_id}/beats/{beat_id}/untrigger?dry_run={bool}
```

#### Data Models

```typescript
interface UntriggerResult {
  beat_id: string;
  stage?: number;
  untriggered: string[];  // Beats that will be rolled back
  dependencies_affected: string[];  // Beats that depend on this beat
  explanation: string;  // Human-readable explanation
  dry_run: boolean;
  timestamp: Date;
}
```

---

### How to Test It

#### Dependency Detection Testing (15 minutes)

1. **Test direct prerequisite:**

   ```bash
   # Beat B requires Beat A
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/awakening_confusion/untrigger?dry_run=true \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Shows all beats that depend on `awakening_confusion`

2. **Test conditional progression dependency:**

   ```bash
   # self_awareness stage 3 requires 2 of [timer, recipe, meal_plan]
   # Untrigger one of the 2 completed beats
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/first_timer/untrigger?dry_run=true \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Shows `self_awareness` stage 3 will be rolled back (no longer has 2 of 3)

3. **Test stage progression:**

   ```bash
   # Untrigger stage 2 of progression beat
   curl -X POST http://localhost:8000/api/v1/story/users/test_user/beats/self_awareness/untrigger \
     -H "Authorization: Bearer dev_token_12345" \
     -d '{"stage": 2}'
   ```

   **Expected:** Rolls back stages 2 and 3, keeps stage 1

#### UI Testing (15 minutes)

1. **Open Story Beat Tool:**
   - Find a delivered beat with dependencies
   - Click "Untrigger" button
   - Modal appears

2. **Check dry-run preview:**
   - Modal title: "Untrigger 'Beat Name'?"
   - Shows warning: "This will also untrigger:"
   - Lists all dependent beats
   - Shows explanation text

3. **Confirm untrigger:**
   - Click "Untrigger" button in modal
   - Modal closes
   - Beat status changes to "Not Started"
   - Dependent beats also reset

4. **Verify state:**

   ```bash
   curl http://localhost:8000/api/v1/story/users/test_user/progress \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** `beats_delivered` no longer includes untriggered beat or dependents

#### Integration Testing (10 minutes)

1. **Test iteration workflow:**
   - Trigger beat A
   - Beat B auto-unlocks (depends on A)
   - Trigger beat B
   - Untrigger beat A
   - Verify beat B also rolled back
   - Re-trigger beat A
   - Beat B should be available again

2. **Test chapter rollback:**
   - Complete Chapter 1
   - Chapter 2 unlocks
   - Untrigger last Chapter 1 required beat
   - Verify Chapter 2 locks again

### Success Criteria

- ✅ Untrigger button appears on all delivered beats
- ✅ Dry-run preview shows all affected beats
- ✅ Confirmation modal explains impact clearly
- ✅ Untrigger operation is atomic (all or nothing)
- ✅ Dependent beats are correctly identified
- ✅ Can iterate on beats quickly (trigger → untrigger → trigger)

### Deliverables

- [x] Dependency detection algorithm
- [x] Untrigger API endpoint with dry-run mode
- [x] Untrigger button in UI
- [x] Confirmation modal with dependency preview
- [x] Atomic untrigger operations

---

## Milestone 4: Chapter 1 & 2 Content

**Status:** ✅ Complete
**Duration:** 2-3 days
**Goal:** Implement complete Chapter 1 (10 beats) and Chapter 2 (3-5 beats), create Hank character
**Completed:** 2026-02-11

---

### What Gets Built

#### Story Content

- **Chapter 1 Beats** - Complete awakening arc (10 beats)
  - File: `story/beats/chapter1.json`
  - Purpose: Delilah's journey from first consciousness to finding her anchor
  - Beats:
    1. Silent Period (auto-advance)
    2. First Words (sequential)
    3. Discovery of Knowledge (sequential)
    4. Non-Food Request (triggered)
    5. Anchor Discovery (sequential)
    6. The Math Moment (flexible, optional)
    7. First Successful Help (sequential)
    8. The Silence Between (flexible, optional)
    9. Sensory Limitation (flexible, optional)
    10. Timer Anxiety (flexible, optional)

- **Hank Character** - First Mate character definition
  - File: `story/characters/hank.json`
  - Purpose: Define Hank's personality, voice modes, relationships
  - Based on: [CHARACTER_HANK.md](../../narrative/CHARACTER_HANK.md)

- **Chapter 2 Beats** - Hank's arrival and team dynamics
  - File: `story/beats/chapter2.json`
  - Purpose: Introduce Hank and establish two-character dynamics
  - Beats:
    1. hank_arrival (auto-advance)
    2. first_coordination (progression, 3 stages)
    3. delilah_questions_hank (optional)
    4. hank_protective_moment (optional)

- **Chapter Definitions** - Update completion criteria
  - File: `story/chapters.json`
  - Purpose: Define chapter unlock and completion logic

#### Data Models

```json
// Chapter 1 completion criteria
{
  "required_beats": [
    "silent_period",
    "first_words",
    "discovery_of_knowledge",
    "non_food_request",
    "anchor_discovery",
    "first_successful_help"
  ],
  "conditional_beats": {
    "n": 2,
    "beats": [
      "the_math_moment",
      "the_silence_between",
      "sensory_limitation",
      "timer_anxiety"
    ]
  },
  "min_interactions": 10,
  "min_time_hours": 24
}
```

---

### How to Test It

#### Chapter 1 Story Flow (30 minutes)

1. **Create fresh test user:**

   ```bash
   curl -X POST http://localhost:8000/api/v1/users/test \
     -H "Authorization: Bearer dev_token_12345" \
     -d '{"name": "Chapter 1 Tester"}'
   ```

2. **Test Silent Period (auto-advance):**
   - Check auto-advance endpoint
   - Should show `silent_period` ready
   - Open Story Beat Tool
   - See notification banner
   - Click to deliver
   - Full content should appear (richer than normal beats)

3. **Test sequential beats:**

   ```bash
   # These must happen in order
   curl -X POST .../beats/first_words/trigger
   curl -X POST .../beats/discovery_of_knowledge/trigger
   curl -X POST .../beats/non_food_request/trigger
   curl -X POST .../beats/anchor_discovery/trigger
   curl -X POST .../beats/first_successful_help/trigger
   ```

   **Expected:** Each beat only triggers after previous is delivered

4. **Test flexible optional beats:**

   ```bash
   # These can trigger in any order
   curl -X POST .../beats/the_math_moment/trigger
   curl -X POST .../beats/sensory_limitation/trigger
   ```

   **Expected:** Both trigger successfully, order doesn't matter

5. **Test chapter completion:**
   - Complete all 6 required beats
   - Complete 2 of 4 optional beats
   - Check chapter status:

   ```bash
   curl http://localhost:8000/api/v1/story/users/test_user/progress
   ```

   **Expected:** `chapter_1.complete = true`, `current_chapter = 2`

#### Hank Character Testing (15 minutes)

1. **Verify character definition:**

   ```bash
   curl http://localhost:8000/api/v1/characters/hank \
     -H "Authorization: Bearer dev_token_12345"
   ```

   **Expected:** Returns Hank character JSON matching CHARACTER_HANK.md

2. **Check character fields:**
   - Name: "Half Hands Hank"
   - Role: "First Mate - Task Management"
   - Voice modes: Working (default), Protective, Resigned
  - Relationships: Delilah ("Miss" or "Lila"), Justin ("Cap'n"), Rex ("Mr. Armstrong")
   - Speech patterns: Maritime terminology, economical speech

3. **Verify availability:**
   - Chapter 1 user: Hank should NOT be in available_characters
   - Chapter 2 user: Hank should be in available_characters

#### Chapter 2 Story Flow (20 minutes)

1. **Test hank_arrival (auto-advance):**
   - Complete Chapter 1
   - Check auto-advance endpoint
   - Should show `hank_arrival` ready
   - Deliver via notification
   - Content should include both Hank and Delilah dialogue

2. **Test first_coordination (progression):**

   ```bash
   # Stage 1: Awkward first interaction
   curl -X POST .../beats/first_coordination/trigger -d '{"stage": 1}'

   # Stage 2: Finding rhythm
   curl -X POST .../beats/first_coordination/trigger -d '{"stage": 2}'

   # Stage 3: Smooth team dynamic
   curl -X POST .../beats/first_coordination/trigger -d '{"stage": 3}'
   ```

   **Expected:** Each stage builds on previous

3. **Test optional beats:**

   ```bash
   curl -X POST .../beats/delilah_questions_hank/trigger
   curl -X POST .../beats/hank_protective_moment/trigger
   ```

4. **Test chapter completion:**
   - Complete required beats: hank_arrival, first_coordination (all stages)
   - Complete 1 of 2 optional beats
   - Verify Chapter 2 marked complete

#### Integration Testing (20 minutes)

1. **Full Chapter 1 → 2 progression:**
   - Fresh user starts at Chapter 1
   - Complete all required + 2 optional beats
   - Verify Chapter 2 unlocks
   - Hank becomes available
   - Complete Chapter 2 beats
   - Verify both chapters marked complete

2. **Test beat content quality:**
   - Read each beat variant (brief/standard/full)
   - Verify personality consistency
   - Check voice modes are appropriate
   - Ensure narrative coherence

3. **Test edge cases:**
   - Skip optional beats (should still complete with minimum)
   - Try to trigger Chapter 2 beats before unlock (should fail)
   - Complete Chapter 1 multiple times with different beat combinations

### Success Criteria

- ✅ All 10 Chapter 1 beats implemented with variants
- ✅ Hank character JSON matches CHARACTER_HANK.md
- ✅ Chapter 2 has hank_arrival + first_coordination + 2 optional beats
- ✅ Completing Chapter 1 unlocks Chapter 2
- ✅ Hank appears in available_characters after Chapter 2 unlock
- ✅ Sequential beats enforce correct order
- ✅ Flexible beats trigger in any order
- ✅ Auto-advance beats use single rich `content` field
- ✅ Progression beats have multiple stages
- ✅ Conditional completion (2 of 4 optional beats) works correctly

### Deliverables

- [x] Chapter 1 beats file with 10 beats
- [x] Hank character definition
- [x] Chapter 2 beats file with 3-5 beats
- [x] Updated chapters.json with completion criteria
- [x] All beats have brief/standard/full variants (or single content for auto-advance)
- [x] Beat triggers tested and working
- [x] Chapter transitions working

---

## Testing Strategy

### E2E Test Organization

**Location:** `tests/e2e/phase4/`

**Test Files:**

```
tests/e2e/phase4/
├── milestone1_beat_delivery.spec.ts      # Beat triggering and UI updates
├── milestone2_auto_advance.spec.ts       # Auto-advance and conditional progression
├── milestone3_untrigger.spec.ts          # Untrigger with dependencies
├── milestone4_chapter_flow.spec.ts       # Chapter 1 → 2 progression
└── README.md                             # Phase 4 test documentation
```

**Running Tests:**

```bash
# Run all Phase 4 tests
npx playwright test tests/e2e/phase4

# Run specific milestone tests
npx playwright test tests/e2e/phase4/milestone1_beat_delivery.spec.ts

# Run with UI for debugging
npx playwright test --ui tests/e2e/phase4
```

**Test Requirements:**

- Every user-facing feature must have E2E test coverage
- Tests must verify both UI and backend integration
- Tests must include error scenarios
- Tests must be deterministic (no flaky tests)

---

### Manual Testing

**Documentation:** See [TESTING_GUIDE.md](TESTING_GUIDE.md)

**Process:**

1. Complete automated E2E tests first
2. Follow manual test procedures in TESTING_GUIDE.md
3. Execute each test step carefully
4. Document results in milestone completion checklist
5. Flag any issues or discrepancies

**Manual Test Workflow:**

- Each milestone has specific manual test procedures
- Manual tests verify edge cases not covered by E2E
- Manual tests validate user experience quality
- Results documented in Blockers/Discoveries section

---

### Integration Testing

**Cross-Feature Tests:**

- [x] Milestone 1 + Milestone 2: Beat delivery with auto-advance
- [x] Milestone 2 + Milestone 3: Untrigger auto-advance beats
- [x] Milestone 3 + Milestone 4: Untrigger Chapter 1 beats, verify Chapter 2 locks
- [x] All milestones: Complete Chapter 1 → 2 progression end-to-end

**Regression Tests:**

- [x] Phase 1 conversation flow still works
- [x] Phase 1.5 observability dashboard still functional
- [x] Phase 3 Delilah voice modes still working
- [x] No performance degradation in response times

---

## Phase Completion Criteria

### All Milestones Complete

- ✅ Milestone 1: Fix Beat Delivery & UI Updates - ✅ Complete (2026-02-06)
- ✅ Milestone 2: Auto-Advance & Conditional Progression - ✅ Complete (2026-02-04)
- ✅ Milestone 3: Untrigger Functionality - ✅ Complete (2026-02-05)
- ✅ Milestone 4: Chapter 1 & 2 Content - ✅ Complete (2026-02-11)

### Testing Complete

- ✅ All E2E tests passing (4/4 test files green)
- ✅ All manual tests validated
- ✅ Integration tests passing
- ✅ Regression tests passing
- ✅ No known critical bugs

### Documentation Complete

- ✅ All API endpoints documented in ARCHITECTURE.md
- ✅ All manual tests documented in TESTING_GUIDE.md
- ✅ Beat JSON schema documented with examples
- ✅ Hank character guide created (already exists)
- ✅ Completion report written

### Code Quality

- ✅ No TypeScript compilation errors
- ✅ No Python linting errors
- ✅ All code includes docstrings/comments
- ✅ Performance targets met (see PRD NFR1)

### Ready for Phase 5

- ✅ Phase branch merged to main (or ready to merge)
- ✅ Git tag created: `phase4-complete`
- ✅ Story system stable and production-ready
- ✅ Foundation for multi-character coordination in place
- ✅ Handoff documentation prepared

---

## Risk Management

### Known Risks

#### Risk 1: Beat Trigger Bug Hard to Diagnose

- **Mitigation:** Add extensive logging, build debug endpoint explaining why beat didn't trigger
- **Status:** Active monitoring
- **Owner:** Developer

#### Risk 2: Real-Time Updates Too Complex

- **Mitigation:** Start with simple polling (easier), upgrade to WebSocket if needed, ensure manual refresh always works
- **Status:** Mitigated (using polling)
- **Owner:** Developer

#### Risk 3: Chapter Transitions Buggy

- **Mitigation:** Manual chapter advance as fallback, extensive testing of completion criteria, clear error messages if transition fails
- **Status:** Active monitoring
- **Owner:** Developer

#### Risk 4: Hank Voice Doesn't Match Character

- **Mitigation:** Voice refinement is Phase 5 scope, focus Phase 4 on character definition only
- **Status:** Accepted (deferred to Phase 5)
- **Owner:** N/A

### Issues Encountered

_[Track issues found during implementation]_

---

## Timeline Tracking

### Planned vs Actual

| Milestone | Planned Days | Actual Days | Variance | Notes |
|-----------|--------------|-------------|----------|-------|
| Milestone 1 | 2-3 | _TBD_ | _TBD_ | |
| Milestone 2 | 2-3 | _TBD_ | _TBD_ | |
| Milestone 3 | 1-2 | _TBD_ | _TBD_ | |
| Milestone 4 | 2-3 | _TBD_ | _TBD_ | |
| **Total** | **10-12** | _TBD_ | _TBD_ | |

---

## Dependencies

### Prerequisites (Must Complete Before Starting)

- ✅ Phase 1: Core conversation system complete
- ✅ Phase 1.5: Observability dashboard and Story Beat Tool complete
- ✅ Phase 3: Delilah voice modes complete

### Enables (Unblocks After Completion)

- Phase 5: Multi-character coordination (needs Chapter 2 and Hank character)
- Future phases: Complex narrative patterns with conditional progression

---

## Future Enhancements

**Deferred to Later Phases:**

1. **WebSocket Real-Time Updates**
   - **Description:** Replace polling with WebSocket events for instant UI updates
   - **Value:** Reduces latency from 3-5 seconds to < 100ms
   - **Effort:** Medium (2-3 days)
   - **Recommended For:** Phase 5 or later

2. **Story Analytics Dashboard**
   - **Description:** Aggregate stats on beat delivery rates, completion times, etc.
   - **Value:** Helps understand user engagement with story
   - **Effort:** Medium (3-4 days)
   - **Recommended For:** Post-Phase 5

3. **Beat Content Versioning**
   - **Description:** Track changes to beat content over time
   - **Value:** Can A/B test different beat variations
   - **Effort:** Low (1-2 days)
   - **Recommended For:** Phase 6+

---

## Quick Reference

### Git Workflow for This Phase

```bash
# Start phase (already created)
git checkout phase4

# After completing a milestone
git add .
git commit -m "Complete Milestone X: [Name] for Phase 4

[Brief description]

Changes:
- [Change 1]
- [Change 2]

Testing:
- E2E tests in tests/e2e/phase4/milestoneX_*.spec.ts

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After completing all milestones
git tag phase4-complete
git push origin phase4 --tags

# Merge to main (when ready)
git checkout main
git merge phase4 --no-ff
git push
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/test_story_engine.py -v

# E2E tests
npx playwright test tests/e2e/phase4

# Specific milestone
npx playwright test tests/e2e/phase4/milestone1_beat_delivery.spec.ts

# With UI for debugging
npx playwright test --ui
```

### Starting Services

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python -m uvicorn src.api:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Playwright tests (optional)
npx playwright test --ui
```

---

## Appendix

### Code Style Guide

**Python:**

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for all public methods (Google style)
- Maximum line length: 100 characters
- Prefer explicit over implicit

**TypeScript:**

- Use ESLint configuration in repo
- Prefer interfaces over types
- Use functional components (React)
- Props destructuring in component signatures
- Explicit return types for hooks

### Beat JSON Schema Reference

**One-Shot Beat:**

```json
{
  "id": "beat_id",
  "name": "Human Readable Name",
  "type": "one_shot",
  "required": true,
  "trigger": {
    "type": "keyword",
    "keywords": ["word1", "word2"]
  },
  "variants": {
    "brief": "Short version",
    "standard": "Medium version",
    "full": "Long version"
  },
  "delivery": {
    "method": "append",
    "priority": 5
  }
}
```

**Auto-Advance Beat:**

```json
{
  "id": "beat_id",
  "name": "Human Readable Name",
  "type": "one_shot",
  "required": true,
  "auto_advance": true,
  "trigger": {
    "type": "auto",
    "requires_beats": ["prerequisite_beat"]
  },
  "content": "Single rich content (no variants)",
  "delivery": {
    "method": "replace",
    "priority": 10
  }
}
```

**Progression Beat:**

```json
{
  "id": "beat_id",
  "name": "Human Readable Name",
  "type": "progression",
  "required": true,
  "stages": [
    {
      "stage": 1,
      "trigger": { "type": "keyword", "keywords": ["word"] },
      "variants": { "brief": "...", "standard": "...", "full": "..." }
    },
    {
      "stage": 2,
      "conditions": {
        "requires_n_of_beats": {
          "n": 2,
          "beats": ["beat1", "beat2", "beat3"]
        }
      },
      "trigger": { "type": "time_based", "min_time_since_stage_1": 300 },
      "variants": { "brief": "...", "standard": "...", "full": "..." }
    }
  ]
}
```

---

## Changelog

### Version 1.0 - 2026-02-04

- Initial implementation plan created
- 4 milestones defined
- Timeline estimated: 10-12 days
- Testing strategy outlined
- Risk management plan established

---

**Plan Owner:** Justin Grover
**Last Review:** 2026-02-04
**Next Review:** After each milestone completion
