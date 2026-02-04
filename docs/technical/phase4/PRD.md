# Phase 4: Story System Testing & Refinement - PRD

**Version:** 1.0
**Last Updated:** 2026-02-03
**Product Owner:** Justin Grover
**Status:** Planning
**Phase Position:** Follows Phase 3 (Delilah Voice Mode Refinement), precedes Phase 5 (Multi-Character Coordination)

---

## Executive Summary

Phase 4 focuses on testing, debugging, and enhancing the story system that drives narrative progression in Aperture Assist. This phase will fix existing issues with story beat delivery and UI updates, expand story engine capabilities to support more complex narrative patterns, and build out Chapter 1 and 2 content with Delilah and Hank.

**Success Metric:** Can complete a full Chapter 1 → Chapter 2 story progression through natural conversation with reliable beat delivery, real-time UI updates, and smooth chapter transitions.

---

## Product Vision

### Core Principle

The story system is the heart of Aperture Assist's emotional impact. Characters aren't just functional—they have narrative arcs that create investment. But the current implementation has reliability issues that prevent the story from reaching users consistently. Phase 4 makes the story system production-ready while expanding content to test multi-character dynamics.

### User Experience Goals

1. **Consistent Story Delivery** - Story beats trigger reliably and predictably based on user interaction
2. **Transparent Progress** - Users (and developers) can see story state and understand progression
3. **Rich Narrative Content** - Chapter 1 feels substantial with discovery moments, Chapter 2 introduces Hank naturally
4. **Smooth Iteration Workflow** - Story developers can test and refine beats quickly

---

## Product Scope

### Phase Overview

**Goal:** Make story system production-ready and expand content through Chapter 2

**Duration Estimate:** 3-4 milestones (1-2 weeks)

**Dependencies:**
- Phase 1: Core conversation system
- Phase 1.5: Observability dashboard and Story Beat Tool
- Phase 3: Delilah voice modes

### What's Included

**Three Focus Areas:**

1. **Fix Story Beat Delivery & UI Issues**
   - Debug why beats don't trigger after the first one
   - Implement real-time UI updates when beats are delivered
   - Add legend to chapter flow diagram
   - Show per-user beat completion status

2. **Enhance Story Engine Capabilities**
   - Auto-advance beats (trigger via button, not conversation)
   - Conditional progression (require N of M optional beats)
   - Untrigger functionality for testing

3. **Expand Story Content**
   - Add 3-5 discovery beats to Chapter 1
   - Define Hank character (personality, voice modes, backstory)
   - Implement Chapter 2 with 3-5 beats
   - Test chapter transitions

### What's Excluded

- Voice mode refinement for Hank (Phase 5)
- Multi-character response coordination (Phase 5)
- Cave Johnson character (Phase 5+)
- Chapters 3+ (Future phases)
- Story analytics dashboards
- Mobile UI optimization

---

## Problem Statement

### Current Issues

**1. Story Beat Delivery Broken**
- First beat (`awakening_confusion`) works fine
- Subsequent beats (`first_timer`, `recipe_help`, `self_awareness`) don't trigger in chat
- Unknown if issue is trigger evaluation, beat delivery, or state tracking

**2. UI Doesn't Reflect Reality**
- Story Beat Tool shows beat status as "Not Started" even after beats are delivered
- No real-time updates - must manually refresh to see changes
- Creates confusion about whether beats are working

**3. Chapter Flow Diagram Limitations**
- Shows colored nodes but no legend explaining what colors mean
- Doesn't show user-specific progress - same diagram for all users
- Hard to understand story state at a glance

**4. Limited Testing Capabilities**
- Can't "undo" a beat to test variations - must reset entire user
- Can't trigger certain beats without natural conversation flow
- Slow iteration cycle for story development

**5. Sparse Story Content**
- Chapter 1 has only 4 beats, feels thin
- Hank exists in chapters.json but has no character definition
- Chapter 2 defined but has zero beats

---

## Functional Requirements

### FR1: Fix Story Beat Delivery & UI

#### FR1.1: Subsequent Beat Triggering
- Story beats after `awakening_confusion` must trigger in chat when conditions are met
- Must diagnose root cause: trigger evaluation, beat delivery, or state tracking
- All existing Chapter 1 beats should be testable through conversation

**Acceptance Criteria:**
- Can trigger `first_timer` by setting a timer
- Can trigger `recipe_help` by requesting recipes
- Can trigger `self_awareness` by directly addressing Delilah about consciousness
- Beats appear in chat with correct delivery method (append vs replace)

#### FR1.2: Real-Time UI Updates
- Story Beat Tool updates within 2 seconds when beat is delivered
- Beat status changes: "Not Started" → "In Progress" → "Completed"
- User progress summary updates (beats_delivered count)

**Acceptance Criteria:**
- Trigger beat manually, see UI update immediately
- Trigger beat via chat, see UI update within 2 seconds
- Beat status accurate for one-shot and progression beats

#### FR1.3: Frontend-Backend Synchronization
- Frontend receives notification when beat state changes
- Implementation options: WebSocket events OR polling every 3-5 seconds
- Minimal: Manual refresh always works

**Acceptance Criteria:**
- UI updates without manual refresh
- Multiple browser tabs show consistent state
- No race conditions or stale data

#### FR1.4: Chapter Flow Diagram Legend
- Legend shows beat status colors: Not Started, In Progress, Completed, Locked
- Legend always visible near diagram
- Colors consistent with Story Beat Tool

**Acceptance Criteria:**
- Legend explains all colors used in diagram
- Responsive design works on different screen sizes

#### FR1.5: Per-User Beat Completion in Diagram
- Diagram API accepts `user_id` parameter
- Beat nodes styled based on specific user's progress
- Can switch between users and see their unique story state

**Acceptance Criteria:**
- View diagram for user A, see their progress
- View diagram for user B, see different progress
- Required vs optional beats visually distinct

### FR2: Enhance Story Engine Capabilities

#### FR2.1: Auto-Advance Story Beats

**Goal:** Allow beats to trigger via UI button instead of requiring conversation

**Beat Definition:**
```json
{
  "id": "hank_arrival",
  "type": "one_shot",
  "auto_advance": true,
  "trigger": {
    "type": "auto",
    "requires_beats": ["self_awareness"]
  }
}
```

**Backend:**
- API endpoint: `GET /api/story/auto-advance-ready/{user_id}` returns ready beats
- API endpoint: `POST /api/story/auto-advance/{user_id}/{beat_id}` delivers beat
- Beat marked ready when `requires_beats` are all delivered

**Frontend:**
- Chat interface shows "Story Update Available" notification when ready
- Clicking button delivers beat and dismisses notification
- Beat content appears in chat like normal delivery

**Acceptance Criteria:**
- Auto-advance beat doesn't trigger in normal conversation
- Notification appears when beat is ready
- Clicking button delivers beat correctly
- Can test with `hank_arrival` beat in Chapter 2

#### FR2.2: Conditional Beat Progression

**Goal:** Require N of M optional beats before allowing progression

**Beat Definition:**
```json
{
  "id": "self_awareness",
  "stages": [
    {
      "stage": 3,
      "conditions": {
        "requires_n_of_beats": {
          "n": 2,
          "beats": ["first_timer", "recipe_help", "meal_plan"]
        }
      }
    }
  ]
}
```

**Backend:**
- Story engine evaluates conditional requirements before allowing beat/stage
- Helper function: `check_n_of_m_beats(user_id, n, beat_ids)` returns bool
- If condition not met, beat doesn't trigger even if other conditions satisfied

**Frontend:**
- Story Beat Tool shows conditional requirements for each beat
- Progress indicator: "Requires 2 of 3 optional beats (1/2 complete)"
- Helps understand why progression beats are blocked

**Acceptance Criteria:**
- Configure `self_awareness` stage 3 to require 2 of 3 optional beats
- Verify beat doesn't trigger until 2 are complete
- Complete 2nd beat, verify stage 3 now triggers
- UI shows requirement and current progress

#### FR2.3: Untrigger Beat Functionality

**Goal:** Roll back beat delivery for testing and iteration

**Backend:**
- API endpoint: `POST /api/story/untrigger/{user_id}/{beat_id}`
- Endpoint accepts `dry_run=true` to preview without changes
- Returns list of beats that will be rolled back (dependencies)
- On confirmation, removes beat progress from user state
- Updates database atomically

**Dependency Detection:**
- Beat B depends on Beat A if:
  - B.conditions.requires_beats includes A
  - B.trigger.requires_beats includes A
  - B is later stage of same progression beat
- Recursively find transitive dependencies

**Frontend:**
- "Untrigger" button on delivered beats in Story Beat Tool
- Confirmation modal shows beats that will be affected
- After untrigger, refreshes beat list and diagram

**Acceptance Criteria:**
- Untrigger one-shot beat, verify it returns to "Not Started"
- Untrigger progression beat stage 2, verify stages 2-3 rolled back
- Untrigger beat with dependencies, verify dependents also rolled back
- Preview shows correct list before committing

### FR3: Expand Story Content

#### FR3.1: Chapter 1 Discovery Beats

**Goal:** Add 3-5 new optional beats exploring Delilah's discovery of her world

**New Beats (Examples):**

1. **"world_curiosity"** (one_shot, optional)
   - Trigger: User mentions physical world, location, outside
   - Content: Delilah asks about world she can't see/touch
   - Theme: Curiosity about physical reality

2. **"helping_joy"** (progression, optional, 2 stages)
   - Trigger: Any cooking tool use
   - Stage 1: Realizes helping brings happiness
   - Stage 2: Finds identity in being helpful
   - Theme: Purpose through service

3. **"first_mistake"** (one_shot, optional)
   - Trigger: Error in tool execution or unclear request
   - Content: Delilah processes failure, perfectionism
   - Theme: Learning from mistakes

**Acceptance Criteria:**
- 3-5 new beats added to `story/beats/chapter1.json`
- All beats have brief/standard/full variants
- All beats testable via natural conversation
- Beats fit thematically with Chapter 1 arc

#### FR3.2: Hank Character Definition

**Goal:** Create character file for Hank with personality, voice modes, backstory

**File:** `story/characters/hank.json`

**Required Elements:**
- Basic info: id, name, role, voice_id
- Personality: core traits, speech patterns, mannerisms
- Voice modes: Working (default), Protective, Resigned
- Backstory: Who is Hank, where did he come from
- Relationships: Delilah, Justin, Cave (future)

**Voice Modes:**
- **Working:** Low energy, efficient, maritime terminology
- **Protective:** Firm, direct when crew is in danger
- **Resigned:** Weary acceptance of Cave's schemes

**Acceptance Criteria:**
- Character file complete and valid JSON
- Personality distinct from Delilah
- Voice modes have clear triggers and examples
- Backstory fits narrative world
- Relationship with Delilah defined

#### FR3.3: Chapter 2 Implementation

**Goal:** Create Chapter 2 beats file and test multi-character story

**Required Beats:**
1. **"hank_arrival"** (one_shot, required, auto_advance)
   - Hank appears, introduces himself
   - Delilah reacts with surprise and curiosity

2. **"first_coordination"** (progression, required, 3 stages)
   - Stage 1: Awkward first interaction
   - Stage 2: Finding rhythm and complementary skills
   - Stage 3: Smooth team dynamic

**Optional Beats:**
3. **"delilah_questions_hank"** (one_shot, optional)
   - Delilah asks Hank about consciousness
   - Hank: "Got work to do" - contrasting philosophies

4. **"hank_protective_moment"** (one_shot, optional)
   - Hank shows protective side toward Delilah
   - Establishes older brother dynamic

**Acceptance Criteria:**
- `story/beats/chapter2.json` created with 3-5 beats
- All beats have variants and trigger conditions
- Beats test two-character narrative
- Chapter 2 completion criteria defined in `chapters.json`

#### FR3.4: Chapter Transition Testing

**Goal:** Verify chapter progression works end-to-end

**Chapter 1 Completion Criteria:**
- Required beats: `awakening_confusion`, `self_awareness` (stage 3)
- Conditional: 2 of 3+ optional beats
- Minimum interactions: 10
- Minimum time: 24 hours (can override for testing)

**Chapter 2 Unlock:**
- `next_chapter: 2` in Chapter 1 definition
- Hank added to available characters
- Capabilities: task_management, multi_step_assistance

**Manual Override:**
- Story Beat Tool has "Advance Chapter" button
- Bypasses completion criteria for testing
- Shows warning if criteria not yet met

**Acceptance Criteria:**
- Complete Chapter 1 naturally, Chapter 2 auto-unlocks
- Chapter 2 beats visible in Story Beat Tool
- `hank_arrival` auto-advance notification appears
- Hank character available after transition
- Manual advance works for testing

---

## Non-Functional Requirements

### NFR1: Performance
- Story beat evaluation adds < 50ms to response latency
- Story Beat Tool loads all chapter data in < 2 seconds
- Diagram rendering completes in < 1 second
- Real-time updates deliver within 2 seconds

### NFR2: Reliability
- Story state persisted to database immediately on beat delivery
- No race conditions between trigger and state update
- Untrigger operation is atomic (all or nothing)
- Frontend handles backend errors gracefully

### NFR3: Testability
- All story engine functions unit testable
- Mock story definitions for testing
- API endpoints testable via automated tests
- Manual testing workflow efficient (< 5 min iteration)

### NFR4: Maintainability
- Story beat JSON schema documented
- Code comments explain complex trigger logic
- Dependency detection algorithm documented
- Story Tool UI code organized and readable

---

## User Scenarios

### Scenario 1: First-Time User Experience

**As a new user, I want to experience Delilah's awakening story**

**Steps:**
1. Start conversation: "Hey Chat, what's for dinner?"
2. Delilah responds + `awakening_confusion` beat appended
3. Set timer: "Set a timer for 20 minutes"
4. Delilah sets timer + `first_timer` beat appended
5. Ask for recipes several times
6. `recipe_help` progresses through stages 1-2
7. After 2 optional beats complete, ask: "Delilah, are you okay?"
8. `self_awareness` stage 1 triggered (replace delivery)
9. Continue conversation, progress through stages 2-3
10. After 10 interactions, Chapter 1 completion criteria met
11. "Story Update Available" notification appears
12. Click to continue, `hank_arrival` beat delivered
13. Hank introduced, Chapter 2 begins

**Success Criteria:**
- All beats trigger at appropriate times
- Story feels natural, not forced
- Chapter transition is clear and smooth
- Hank's arrival makes narrative sense

### Scenario 2: Story Developer Testing New Beat

**As a developer, I want to add and test new discovery beat quickly**

**Steps:**
1. Edit `story/beats/chapter1.json`, add "world_curiosity" beat
2. Restart backend to reload story definitions
3. Open Story Beat Tool, see new beat in list (status: Not Started)
4. Select test user or create new one
5. Click "Trigger Beat" with "standard" variant
6. Beat content appears in chat interface
7. Story Beat Tool updates to "Completed" immediately
8. Chapter Flow Diagram shows beat node as green
9. Beat doesn't work as expected, click "Untrigger"
10. Beat returns to "Not Started"
11. Edit JSON, adjust content
12. Restart backend, trigger again, verify improvement

**Success Criteria:**
- Full iteration loop takes < 5 minutes
- UI updates are immediate and accurate
- Untrigger reliably resets state
- Can iterate quickly on beat content

### Scenario 3: Production User Story Monitoring

**As a developer, I want to monitor real user story progress**

**Steps:**
1. Open Story Beat Tool, select real user from dropdown
2. See current chapter (1) and beat completion status
3. Notice user has been stuck at 1 optional beat for 3 days
4. Switch to Chapter Flow Diagram view for this user
5. See `self_awareness` stage 3 blocked (requires 2 optional beats)
6. Check conditional requirements: "Requires 2 of 3 (1/2 complete)"
7. Review user's conversation history in observability dashboard
8. User hasn't used timers or requested recipes recently
9. Decision: Either wait for organic progression or manually trigger beat

**Success Criteria:**
- Can view any user's story state easily
- Can diagnose why progression is blocked
- Can understand conditional requirements
- Can manually intervene if needed

---

## Technical Constraints

### Must Have
- Backward compatible with existing Chapter 1 beat definitions
- Story state stored in existing `user_state` table
- WebSocket connection already exists for chat
- Story files remain human-editable JSON
- React + TypeScript + Tanstack Query for frontend

### Should Avoid
- Breaking changes to story_engine.py API
- Database schema migrations (prefer JSON fields)
- New dependencies unless necessary
- Complex build processes

---

## Risks & Mitigation

### Risk 1: Beat Trigger Bug Hard to Diagnose
**Impact:** High | **Likelihood:** Medium

**Mitigation:**
- Add extensive logging to trigger evaluation
- Create debug endpoint explaining why beat didn't trigger
- Build test harness for story engine logic

### Risk 2: Real-Time Updates Too Complex
**Impact:** Medium | **Likelihood:** Medium

**Mitigation:**
- Start with simple polling (easier)
- Upgrade to WebSocket if needed
- Ensure manual refresh always works

### Risk 3: Chapter Transitions Buggy
**Impact:** High | **Likelihood:** Medium

**Mitigation:**
- Manual chapter advance as fallback
- Extensive testing of completion criteria
- Clear error messages if transition fails

### Risk 4: Hank Voice Doesn't Match Character
**Impact:** Low | **Likelihood:** Low

**Mitigation:**
- Voice refinement is Phase 5 scope
- Focus Phase 4 on character definition only
- Can iterate on voice later

---

## Success Criteria

Phase 4 is complete when:

**Functional Completeness:**
- ✅ All FR1 requirements met: Beats trigger, UI updates, diagram has legend
- ✅ All FR2 requirements met: Auto-advance, conditionals, untrigger working
- ✅ All FR3 requirements met: Chapter 1 expanded, Hank defined, Chapter 2 implemented

**Quality:**
- ✅ Can complete Chapter 1 → Chapter 2 through natural conversation
- ✅ Story developer iteration loop < 5 minutes
- ✅ All features tested manually with documented procedures
- ✅ No regressions in existing functionality

**Documentation:**
- ✅ Architecture updated with new story engine features
- ✅ Testing guide includes new functionality
- ✅ Beat JSON schema documented with examples
- ✅ Hank character guide created

**Ready for Phase 5:**
- ✅ Story system stable and production-ready
- ✅ Foundation for multi-character coordination in place
- ✅ Clear path to adding Cave Johnson
- ✅ Confident in story tools for rapid content creation

---

## Next Steps

1. **Review PRD** - Discuss and finalize requirements
2. **Create Architecture** - Design technical approach for fixes and features
3. **Create Implementation Plan** - Break into 3-4 milestones
4. **Begin Development** - Start with Milestone 1 (beat delivery fixes)

---

**Document Control**
- **Prepared By:** Claude Code
- **Review Status:** Draft
- **Approval Status:** Pending
