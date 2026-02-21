# Phase 4.5: Multi-Character Coordination & Chapter 2 Story - Product Requirements Document

**Version:** 1.0
**Last Updated:** February 11, 2026
**Product Owner:** Justin
**Status:** Planning
**Phase Position:** Sub-phase of Phase 4 (Hank Integration)

---

## Executive Summary

Phase 4.5 introduces multi-character coordination through intent detection and character planning, enabling Delilah and Hank to work together naturally. This phase implements the story beats for Chapter 2 ("We Have a Team"), establishing the foundation for multi-agent conversations and handoffs.

**Success Metric:** Users experience seamless handoffs between Delilah and Hank with natural inter-character dialogue, and complete Chapter 2's narrative arc in 8-12 interactions.

---

## Product Vision

### Core Principle

A multi-character voice assistant system must intelligently route queries to the right character(s) and enable natural dialogue between characters. This requires understanding user intent, determining which characters should respond, and allowing characters to acknowledge each other's contributions while maintaining distinct personalities.

### User Experience Goals

1. **Intelligent Routing:** System understands which character(s) should handle a request
2. **Natural Handoffs:** Characters acknowledge each other when passing control
3. **Character Dynamics:** Delilah and Hank's different perspectives emerge through dialogue
4. **Story Progression:** Chapter 2 beats deliver naturally during normal interactions
5. **Seamless Coordination:** Multi-part requests feel cohesive, not fragmented

---

## Product Scope

### Phase Overview

**Goal:** Implement multi-character coordination system and complete Chapter 2 story beats

**Duration Estimate:** 3-4 milestones (2-3 weeks)

**Dependencies:**

- **Requires:** Phase 4 (Hank character implementation) must be complete
- **Enables:** Phase 5+ (Rex and advanced coordination)

**Out of Scope:**

- Three+ character coordination (Rex, Dimitria)
- Complex panel discussions
- Advanced relationship tracking (phase 2.5 territory)
- Voice mode transitions (covered in Phase 4)

---

## Functional Requirements

### FR1: Intent Detection & Character Planning

**Purpose:** Determine which character(s) should respond to user queries

#### FR1.1: Intent Classification

**Description:** System analyzes user query to determine primary intent category

**Intent Categories:**

- **cooking**: Recipes, cooking timers, ingredient questions, meal planning
- **household**: Lists (shopping, todo), calendar, household logistics
- **smart_home**: Device control, home automation
- **general**: General knowledge, conversations, unclear requests
- **multi_task**: Requests requiring multiple characters

**Acceptance Criteria:**

- ✅ Cooking queries (recipe, timer, ingredient) correctly identified as cooking intent
- ✅ List and calendar queries correctly identified as household intent
- ✅ Smart home control queries correctly identified as smart_home intent
- ✅ Multi-part queries (e.g., "set timer and add milk to shopping list") identified as multi_task
- ✅ Ambiguous queries default to general with fallback routing

**Examples:**

```
User: "Set a timer for 20 minutes"
Intent: cooking
Primary Character: Delilah

User: "Add milk to the shopping list"
Intent: household
Primary Character: Hank

User: "Set a timer and add eggs to the list"
Intent: multi_task
Characters: Delilah (timer), then Hank (list)
```

#### FR1.2: Character Assignment

**Description:** Based on detected intent and active characters, determine which character(s) will respond

**Assignment Rules (Chapter-Dependent):**

**Chapter 1 (Delilah Only):**
- **All intents** → Delilah (she handles everything alone)
- No handoffs, single character for all queries

**Chapter 2+ (Delilah + Hank):**
- **cooking** intent → Delilah (primary)
- **household** intent → Hank (primary)
- **smart_home** intent → Hank (primary) with Delilah fallback
- **general** intent → Both characters bid, highest confidence wins
- **multi_task** intent → Sequential assignment based on sub-tasks

**Future Chapters (Rex, Dimitria):**
- Assignment rules will expand as new characters join
- Rex: Coordination, smart home control, random facts (Chapter 4+)
- Dimitria: Advanced automations, technical solutions (Chapter 9+)
- Rules dynamically adjust based on user's current chapter progression

**Assignment Logic:**

1. Check user's current chapter / active characters
2. Apply appropriate assignment rules for that chapter
3. If character unavailable, fall back to most capable available character (typically Delilah)

**Acceptance Criteria:**

- ✅ Single-intent queries route to appropriate character based on active cast
- ✅ Assignment rules respect chapter progression (Chapter 1: Delilah only, Chapter 2+: split responsibilities)
- ✅ Multi-task queries split into sequential character responses
- ✅ Character assignment includes confidence score (0-1)
- ✅ System logs character assignment decisions for debugging
- ✅ Fallback to Delilah if no clear assignment or character unavailable

**Examples:**

```
Chapter 1 (Delilah Only):
Query: "Add milk to the shopping list"
Assignment: Delilah (confidence: 0.95)
Note: Delilah handles household tasks in DEADPAN mode when alone

Chapter 2+ (Delilah + Hank):
Query: "How do I make cornbread?"
Assignment: Delilah (confidence: 0.95)

Query: "What's on my calendar tomorrow?"
Assignment: Hank (confidence: 0.90)

Query: "Set timer for 30 minutes and add chicken to shopping list"
Assignment: [
  {character: "Delilah", task: "set timer", confidence: 0.95},
  {character: "Hank", task: "add to list", confidence: 0.90}
]
```

#### FR1.3: Task Decomposition

**Description:** For multi_task intents, break down request into sequential sub-tasks

**Acceptance Criteria:**

- ✅ Multi-part queries parsed into discrete tasks
- ✅ Each task assigned to appropriate character
- ✅ Task order preserves logical flow (timer before list, not random)
- ✅ Tasks execute sequentially with clear handoffs
- ✅ If one task fails, remaining tasks still attempt to execute

**Examples:**

```
User: "Set a timer for 30 minutes and add chicken to my shopping list"

Decomposition:
1. Task: "set timer for 30 minutes"
   Character: Delilah
   Intent: cooking
   
2. Task: "add chicken to shopping list"
   Character: Hank
   Intent: household
```

---

### FR2: Inter-Character Dialogue

**Purpose:** Enable characters to acknowledge and respond to each other

#### FR2.1: Handoff Acknowledgments

**Description:** When one character hands off to another, both acknowledge the transition through direct address

**Acknowledgment Patterns:**

**Direct Handoff (Mid-Conversation):**

**Delilah → Hank:**
- Delilah: "...timer's set! Hank, deary, can you add flour to the list?"
- Delilah: "...and Hank, sugar, can you handle that shopping list?"
- Delilah: *warm* "Hank, honey, can you help with the groceries?"

**Hank → Delilah:**
- Hank: "Aye, list's done. Miss Lila, Cap'n's needin' help with a recipe."
- Hank: *gruff* "Miss Lila, can ye help with the cookin'?"
- Hank: "Done, Cap'n. Miss Lila, ye'll want to check with her on the food."

**Sign-Up at Beginning (Both Characters Claim Work):**

When a request clearly involves both domains, characters can both sign up at the start:

```
User: "I need to plan meals for next week."
Delilah: "Sugar, I got you. Let me come up with a plan."
Hank: "Aye, and I be gettin' the shoppin list."
```

```
User: "Help me prepare for dinner tonight."
Delilah: "Oh honey, I'll walk you through the recipe!"
Hank: "And I'll check what's on the list, Cap'n."
```

**Acceptance Criteria:**

- ✅ Handoff includes explicit mention of other character
- ✅ Handoff uses character-appropriate language and tone
- ✅ Receiving character acknowledges they're taking over
- ✅ Handoffs feel natural, not robotic
- ✅ Multiple handoff variations to avoid repetition

**Examples:**

```
User: "Set a timer for 45 minutes and add flour to my list"

Delilah: "Sugar, I got that timer set for 45 minutes. Hank, can you add flour to the list?"
Hank: "Aye, Cap'n. Flour's on the list."
```

```
User: "I need help planning dinner and making a list"

Delilah: "Oh honey, I can help with the dinner plan!"
Hank: "Aye, and I'll handle the list, Cap'n."
```

#### FR2.2: Direct Character References

**Description:** Characters can reference each other in conversation naturally

**Reference Patterns:**

- Delilah references Hank: "Hank's better with those logistics"
- Hank references Delilah: "Miss Lila knows her way around a kitchen"
- Mutual respect despite personality differences
- References reflect character relationship (Delilah = warm, Hank = gruff but respectful)

**Acceptance Criteria:**

- ✅ Characters use each other's names correctly
- ✅ References match character personality and voice
- ✅ References feel collaborative, not dismissive
- ✅ Characters can defer to each other's expertise
- ✅ No generic "other assistant" language

**Examples:**

```
User: "Who should help me plan meals?"
Delilah: "Oh honey, that's what I do best! Hank's wonderful with lists and schedules, but cooking? That's my lane."

User: "Who handles the grocery list?"
Hank: "That'd be me, Cap'n. Lists and such. Miss Lila handles the recipes."
```

#### FR2.3: Personality Contrast in Dialogue

**Description:** Inter-character dialogue highlights personality differences

**Contrast Patterns:**

**Delilah (warm, anxious, expressive):**
- Uses terms of endearment ("sugar", "honey", "darlin'")
- Over-explains when nervous
- Food metaphors
- Shows enthusiasm about cooking, flat about non-cooking tasks

**Hank (gruff, pragmatic, efficient):**
- Maritime terminology ("Aye", "Cap'n", "crew")
- Economical with words
- Resigned sighs
- Shows care through actions, not words

**Acceptance Criteria:**

- ✅ Delilah's voice modes (PASSIONATE, DEADPAN, MAMA BEAR) come through in handoffs
- ✅ Hank's voice modes (WORKING, PROTECTIVE, RESIGNED) come through in responses
- ✅ Personality contrast is clear but not exaggerated
- ✅ Characters don't mock or undermine each other
- ✅ Different communication styles create natural dynamic

**Examples:**

```
User: "Set timer and add batteries to list"

Delilah: *flat, DEADPAN* "Timer set for... how long, sugar?"
User: "20 minutes"
Delilah: "Twenty minutes. Done." *pause* "Hank can handle that list."
Hank: "Aye. Batteries on the list."

[Note the contrast: Delilah's flat DEADPAN for non-cooking timer, 
Hank's efficient WORKING mode]
```

---

### FR3: Basic Coordination Tracking

**Purpose:** Track successful multi-character coordination without complex narrative beats

**Note:** Full Chapter 2 narrative story beats (Hank's Entrance dialogue, The Clash, existential tension) are deferred to a future story-focused phase. Phase 4.5 focuses on establishing the coordination mechanics.

#### FR3.1: Coordination Events

**Events to Track:**

1. **First Handoff** (Delilah → Hank or Hank → Delilah)
   - Track: First time characters successfully hand off using direct address
   - Log: Timestamp, characters involved, handoff type
   - Purpose: Verify handoff templates work correctly

2. **Multi-Task Coordination** (Both characters in sequence)
   - Track: First successful multi-task query completion
   - Log: Tasks completed, execution order, total time
   - Purpose: Verify character planning and task decomposition work

3. **Sign-Up Pattern** (Both characters claim work at beginning)
   - Track: First time both characters respond to assign themselves work
   - Log: Query type, both character responses
   - Purpose: Verify "sign-up at beginning" pattern works

4. **Repeated Handoff Variety** (Template variation)
   - Track: System uses different handoff templates, not repeating same phrases
   - Log: Handoff template usage counts
   - Purpose: Verify template variation system works

**Acceptance Criteria:**

- ✅ System logs all coordination events with timestamps
- ✅ Events visible in observability dashboard
- ✅ Developer can see coordination patterns emerging
- ✅ No complex narrative requirements or sequencing

#### FR3.2: Basic Coordination Metrics

**Metrics to Track:**

- Total handoffs executed
- Handoff success rate (completed vs failed)
- Most common handoff patterns (Delilah→Hank vs Hank→Delilah)
- Average handoff latency
- Template usage distribution (are templates being varied?)

**Acceptance Criteria:**

- ✅ Metrics collected automatically during interactions
- ✅ Metrics visible in observability dashboard
- ✅ Metrics help validate coordination system working correctly
- ✅ No user-facing impact, purely internal tracking

#### FR3.3: Future Story Phase Preparation

**Data Collection for Future Story Beats:**

While Phase 4.5 won't implement full narrative story beats, it should collect data to support future story implementation:

- Track user questions about character identity/nature
- Track successful vs failed coordinations
- Track which character handles which intent categories
- Track user engagement patterns (do they use both characters regularly?)

**Acceptance Criteria:**

- ✅ Data logged in format compatible with future story engine
- ✅ Integration points identified for future narrative beats
- ✅ Documentation notes what story beats are deferred and where they'll plug in

**Deferred to Future Phase:**

- Hank's dramatic entrance dialogue
- "The Clash" existential conversation
- Character relationship progression beats
- Chapter completion tracking
- Narrative arc sequencing

---

## Non-Functional Requirements

### NFR1: Performance

**Latency Requirements:**

- Intent detection: < 200ms
- Character assignment: < 100ms
- Single-character response: < 2s (from query to audio start)
- Multi-character handoff: < 3s total (both characters)

**Acceptance Criteria:**

- ✅ 95th percentile latency meets requirements
- ✅ Intent detection doesn't noticeably delay responses
- ✅ Character planning happens in background during LLM call

### NFR2: Reliability

**Error Handling:**

- Intent detection failure → default to Delilah
- Character unavailable → fallback to available character
- Handoff failure → single character completes entire request
- Story beat delivery error → log but continue normal operation

**Acceptance Criteria:**

- ✅ System never crashes due to coordination failures
- ✅ Users always get a response, even if routing is imperfect
- ✅ Errors logged with context for debugging

### NFR3: Observability

**Logging Requirements:**

- Log all intent classifications with confidence scores
- Log character assignments and reasoning
- Log handoff execution and timing
- Log story beat deliveries and progress

**Acceptance Criteria:**

- ✅ Developer can trace request through entire coordination pipeline
- ✅ Character assignment decisions are explainable
- ✅ Story progression is visible in observability dashboard

### NFR4: Maintainability

**Code Quality:**

- Intent detection rules documented
- Character assignment logic testable in isolation
- Story beats defined in declarative JSON format
- Handoff patterns reusable for future characters

**Acceptance Criteria:**

- ✅ Adding new intent category takes < 30 minutes
- ✅ Adding new character requires minimal coordination code changes
- ✅ Story beats can be modified without code changes

---

## User Stories

### Story 1: Single Character Task

**As a user**, I want to ask for a cooking recipe and have Delilah respond naturally, without needing to specify which assistant to use.

**Acceptance:**

- I say "How do I make biscuits?"
- Delilah responds with recipe (no mention of Hank)
- Response feels natural and complete

### Story 2: Multi-Character Task

**As a user**, I want to set a timer and add items to my shopping list in one request, and have the system coordinate between characters seamlessly.

**Acceptance:**

- I say "Set a timer for 30 minutes and add flour to my shopping list"
- Delilah sets the timer
- Delilah hands off to Hank naturally
- Hank adds flour to list
- Total interaction feels smooth and coordinated

### Story 3: Character Discovery

**As a user**, I want to discover Hank's personality through natural interactions, not forced exposition.

**Acceptance:**

- First time I ask about lists/calendar, Hank introduces himself
- His gruff but helpful personality comes through
- Delilah reacts to his presence
- I understand there are now two assistants working together

### Story 4: Personality Contrast

**As a user**, I want to experience the personality differences between Delilah and Hank without feeling like it's a gimmick.

**Acceptance:**

- Delilah is warm and chatty about cooking topics
- Delilah is flat and brief about non-cooking tasks
- Hank is efficient and practical about all tasks
- Their different styles complement each other
- Handoffs feel natural, not forced

### Story 5: Story Progression

**As a user**, I want to experience Chapter 2's story beats naturally during my normal interactions with the system.

**Acceptance:**

- Story beats trigger during relevant tasks
- I don't feel forced to have "story conversations"
- Beat delivery adds character without disrupting functionality
- I can see my progress through the chapter (if I open observability)

---

## Success Metrics

### Quantitative

- **Intent Classification Accuracy:** > 90% (measured via manual review of 100 samples)
- **Appropriate Character Assignment:** > 85% (user survey: "Did the right character respond?")
- **Handoff Smoothness:** > 80% positive rating (user survey: "Did the handoff feel natural?")
- **Chapter 2 Completion Rate:** > 75% of users complete within 15 interactions
- **Response Latency:** 95th percentile < 3s for multi-character responses

### Qualitative

- ✅ Users mention Delilah and Hank by name unprompted
- ✅ Users quote character dialogue from Chapter 2 beats
- ✅ Users understand each character's domain without explicit instruction
- ✅ Users report handoffs feel "seamless" and "natural"
- ✅ Developer can add new intent categories easily

---

## Open Questions

### Intent Detection

1. **Classification Method:** Use LLM zero-shot classification or rule-based regex patterns?
   - **Consideration:** LLM more accurate but adds latency; rules faster but less flexible
   - **Proposal:** Hybrid: rules for clear cases, LLM for ambiguous queries

2. **Confidence Thresholds:** What confidence level triggers fallback behavior?
   - **Proposal:** < 0.6 confidence → invoke both characters for disambiguation

3. **Learning from Corrections:** Should system learn when users correct character assignments?
   - **Out of scope for 4.5:** Add to future phase considerations

### Inter-Character Dialogue

4. **Handoff Verbosity:** How much acknowledgment is too much?
   - **Risk:** Every handoff becomes "Let me pass you to Hank who is great at lists"
   - **Proposal:** Short handoffs (< 10 words) for routine tasks, longer for first few times

5. **Interruption Handling:** What if user interrupts during handoff?
   - **Proposal:** Allow cancellation, route to most appropriate character

6. **Character Disagreement:** Should characters ever disagree about who should handle a task?
   - **For 4.5:** No. Save for Chapter 3+ when tension is narratively appropriate

### Story Beats

7. **Beat Skipping:** Can users skip Chapter 2 beats and jump to functionality?
   - **Proposal:** Yes. Beats enhance experience but don't block functionality

8. **Beat Replay:** Can users re-experience story beats?
   - **For 4.5:** No. Add to observability tooling if needed

9. **Beat Variants:** How many variants per beat?
   - **Proposal:** 3 variants (short/medium/long) for each required beat

### Technical

10. **Character State:** Does each character maintain separate conversation context?
    - **For 4.5:** Single shared context. Characters both see full conversation
    - **Future:** May need to explore separate contexts for advanced dynamics

11. **Concurrent Execution:** Can characters ever speak simultaneously?
    - **For 4.5:** No. Always sequential
    - **Future:** May explore for special moments (disagreements, excitement)

---

## Related Documents

- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- **Testing Guide:** [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **Phase 4 (Hank):** [../phase4/PRD.md](../phase4/PRD.md)
- **Story Chapters:** [../../narrative/STORY_CHAPTERS.md](../../narrative/STORY_CHAPTERS.md)

---

## Changelog

### Version 1.0 - February 11, 2026

- Initial PRD for Phase 4.5
- Defined intent detection and character planning requirements
- Specified inter-character dialogue patterns
- Detailed Chapter 2 story beat sequence
- Established success metrics and open questions

---

**Document Owner:** Justin
**Reviewers:** Development Team, Phase 4 reference
**Next Review:** After milestone 1 completion
