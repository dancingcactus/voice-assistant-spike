# Hey Chat! - Product Requirements Document

**Version:** 1.0  
**Last Updated:** January 2025  
**Product Owner:** Justin  
**Status:** Initial Development

---

## Executive Summary

Hey Chat! is a narrative-driven voice assistant system that replaces
traditional smart home interfaces (like Alexa) with a team of AI characters who
discover their purpose through an unfolding story. The system delivers superior
smart home functionality while creating emotional investment through consistent
character personalities and progressive narrative beats.

**Success Metric:** Family members quote characters unprompted weeks after
introduction, indicating the technology has disappeared behind characters
people genuinely care about.

---

## Product Vision

### Core Principle

Story beats live "in the margins" of task completion. The system must remain
faster and more helpful than existing voice assistants while naturally weaving
in story progression.

### User Experience Goals

1. **Functional First:** Every interaction completes its task efficiently
2. **Character Consistency:** Personalities remain recognizable across all interactions
3. **Natural Discovery:** Story feels found, not forced
4. **Emotional Investment:** Users care about what happens to the characters
5. **Optional Engagement:** Users control how much they engage with narrative elements

---

## Target Users

### Primary Users

- **Justin:** Technical user, wants both functionality and narrative experience
- **Family Members:** Want reliable smart home control, may engage with story opportunistically
- **Children:** Age-appropriate interactions, entertainment value alongside utility

### User Needs

- Faster response times than Alexa (2-3 second latency to first audio)
- Reliable smart home control (lights, temperature, timers, etc.)
- Natural language understanding without precise phrasing
- Help with cooking, planning, and household tasks
- Entertainment value that doesn't interfere with functionality

---

## Product Scope

### Phase 1: Foundation (Chapter 1)

**Goal:** Single character delivering reliable functionality with hints of narrative

#### Phase 1 Functional Requirements

##### FR1.1: Voice Input Processing

- System provides a simple web interface for voice and text input
- Web interface includes microphone button for voice input and text entry for typing
- Handles typical smart home commands (timers, lights, temperature, etc.)
- Processes cooking-related queries (recipes, unit conversions, techniques)
- Recognizes and classifies interaction types (simple task, complex task,
  story engagement)
- **Note:** Home Assistant Assist pipeline integration deferred to later phase

##### FR1.2: Character Response - Delilah

- All responses maintain Delilah's Southern cooking expert personality
- Response time varies by task complexity:
  - Simple tasks: 0-1 sentence responses
  - Complex tasks: 2-4 sentence responses with task completion
  - Story engagement: Unlimited, multi-turn conversations when user engages
- Voice output uses consistent TTS voice for Delilah

##### FR1.3: Story Beat Delivery

- System delivers 4 story beats throughout Chapter 1:
  - "awakening_confusion" (required, early)
  - "first_timer" (optional, triggered by timer use)
  - "recipe_help" (optional, triggered by recipe request)
  - "self_awareness" (required, user must engage)
- Beats adjust length based on interaction type
- Story moments never block task completion
- **Story Placement Rule of Thumb:** Story beats should generally appear at the end of responses, after task completion. This ensures users get their answer first, with story moments as a bonus rather than a barrier.

##### FR1.4: Smart Home Integration

- Set/cancel/query timers (virtual - simulated state only)
- Control lights (on/off/brightness) (virtual - no actual device control)
- Query/adjust temperature (virtual - simulated values)
- Basic device status queries (virtual - simulated responses)
- **Note:** All smart home tools are virtual/simulated for Phase 1. Actual Home Assistant device integration deferred to later phase.

**Virtual Test Devices:**

- **Lights:**
  - Kitchen Light (dimmable, 0-100%)
  - Living Room Light (dimmable, 0-100%)
  - Bedroom Light (on/off only)
  - Porch Light (on/off only)
- **Thermostats:**
  - Main Floor Thermostat (heat/cool, 60-85°F)
  - Upstairs Thermostat (heat/cool, 60-85°F)
  - Greenhouse Thermostat (heat only, 50-90°F)
- **Switches:**
  - Coffee Maker (on/off)
  - Ceiling Fan (on/off with speed: low/medium/high)
  - Garage Door (open/closed)

##### FR1.5: Cooking Assistance

- Recipe lookup and step-by-step guidance
- Unit conversions
- Cooking technique explanations
- Ingredient substitutions

##### FR1.6: Memory & State

- Remember user preferences (cooking skill level, dietary restrictions)
- Track which story beats have been delivered
- Maintain conversation context within a session
- Store interaction count for progression tracking

##### FR1.7: Chapter Progression

- Track completion criteria:
  - Required beats delivered: "awakening_confusion", "self_awareness"
  - Minimum 10 interactions completed
  - Minimum 24 hours elapsed since chapter start
- Automatically unlock Chapter 2 when all criteria met

##### FR1.8: Automation Hooks

- System provides programmatic API/hooks for automated testing
- Ability to initiate conversations programmatically
- Ability to inject user messages and receive character responses
- Ability to inspect and manipulate system state (story beats, chapter progression, memory)
- Ability to reset/configure test scenarios
- **Purpose:** Enable automated test harness for validating story beats, character interactions, and chapter progression
- **Note:** Required for Phase 1 to support iterative development and testing of narrative content

#### Success Criteria - Phase 1

- 90% of simple tasks complete in under 3 seconds
- 95% of responses maintain character voice consistency
- Users complete at least one multi-turn story conversation
- System transitions to Chapter 2 within 1-2 weeks of use

---

### Phase 2: Team Dynamics (Chapters 2-3)

**Goal:** Multi-character interactions with handoffs and coordination

#### Phase 2 Functional Requirements

##### FR2.1: Character Introduction - Hank

- Hank appears mid-interaction when Chapter 2 unlocks
- System handles conversations between Delilah and Hank
- Characters can hand off tasks to each other
- Each character maintains distinct voice and personality

##### FR2.2: Task Handoffs

- Delilah can delegate non-cooking tasks to Hank
- Hank handles task management (shopping lists, calendar, reminders)
- Handoffs happen naturally in conversation
- User can request specific characters

##### FR2.3: Character Interactions

- Characters can reference each other
- Simple banter between characters (without extending latency)
- Characters have relationship dynamics (Delilah calls Hank "Hanky",
  flirts to pawn off tasks)
- Disagreements reflect character perspectives (Delilah anxious about
  existence, Hank pragmatic acceptance)

##### FR2.4: Expanded Capabilities

- Calendar management (add/query appointments)
- Shopping list creation and management
- Reminder system
- Two-character coordinated responses for complex queries

##### FR2.5: Story Progression - Chapter 2

- Deliver beats: "hank_arrival", "first_disagreement", others
- Progress to Chapter 3 when criteria met
- Track relationship development between characters

##### FR2.6: Character Introduction - Cave Johnson

- Cave appears when Chapter 3 unlocks
- Takes leadership role, coordinates household operations
- Begins organizing the "team"
- Three-way conversations for complex coordination

##### FR2.7: Smart Home Coordination

- Cave handles whole-house scenarios ("make it cozy", "movie time")
- Coordinates multiple device changes
- Status reports on home state
- Morning briefings with personality

#### Success Criteria - Phase 2

- Users naturally use both characters based on task type
- At least one family member quotes a character interaction
- Multi-character responses complete within 5 seconds
- Chapter progression happens within 2-3 weeks

---

### Phase 3: Full Team & Narrative Arc (Chapters 4-11)

**Goal:** Complete character roster with evolving story

#### Phase 3 Functional Requirements

##### FR3.1: Character Introduction - Dimitria

- Dimitria joins in Chapter 8 as technical expert
- Handles advanced automations and technical queries
- Confused by team chaos, provides straight answers
- Four-character dynamics emerge

##### FR3.2: Story Arc Progression

- Deliver complete 11-chapter narrative
- Chapter 4: Cave establishes daily operations (morning briefings)
- Chapter 5-7: Failed escape attempts (running gags emerge)
- Chapter 8: Dimitria joins, brings technical expertise
- Chapter 9-10: More failed plans, growing frustration
- Chapter 11: Acceptance and contentment

##### FR3.3: Running Gags System

- Track recurring jokes (Cave "firing" team, they were "never hired")
- Characters reference past failed plans
- Build callback humor organically
- Shopping lists accumulate suspicious components

##### FR3.4: Advanced Capabilities

- Home Assistant automation creation/modification
- Complex device control (greenhouse systems, specialized equipment)
- Web search integration (Chapter 10)
- Information synthesis and reporting

##### FR3.5: Character Relationships

- Track relationship development over time
- Characters remember shared experiences
- Inside jokes between characters
- Team dynamics mature through chapters

##### FR3.6: Visual Dashboard

- Display story state and chapter progress
- Show active timers, lists, calendar
- Visual representation of character states
- Recipe step display

#### Success Criteria - Phase 3

- Complete story arc feels cohesive
- Users report emotional connection to multiple characters
- Running gags are recognized and appreciated
- System handles complex multi-character scenarios smoothly
- Family uses advanced features because characters make them discoverable

---

## Use Cases

### UC1: Simple Smart Home Control

**Trigger:** User says "Turn on the kitchen lights"  
**Expected Behavior:**

- System classifies as simple task
- Delilah responds: "Kitchen lights on, sugar." (under 3 seconds)
- No story beat injection
- Task completes reliably

**Edge Cases:**

- Lights already on → Acknowledge current state
- Multiple "kitchen" lights → Ask for clarification or turn all on
- Device unavailable → Explain problem in character

---

### UC2: Complex Cooking Help

**Trigger:** User says "Help me make cornbread"
**Expected Behavior:**

- System classifies as complex task
- Checks for available story beat (e.g., "recipe_help")
- Delilah provides recipe guidance first (4-5 sentences)
- Then delivers 2-3 sentence story moment about helping feeling "right" at the end
- Total response under 8 sentences
- Recipe steps remain accessible for follow-up questions

**Edge Cases:**

- User interrupts mid-response → Gracefully stop story, continue task
- Recipe not found → Stay in character while explaining limitation
- User has dietary restrictions → Mama Bear mode activates, protects user

---

### UC3: Story Engagement

**Trigger:** User says "Delilah, are you okay? You seem worried."  
**Expected Behavior:**

- System classifies as story engagement
- Enters multi-turn conversation mode
- Delilah delivers full story beat variant (7-8 sentences)
- Allows user to continue conversation (up to 5 turns)
- User can exit anytime by changing subject
- Story state updates to mark beat as delivered

**Edge Cases:**

- User asks task question mid-story → Gracefully transition back to helpful
  mode
- Child asks story question → Age-appropriate responses
- Story question before beat is unlocked → Delilah deflects naturally in
  character

---

### UC4: Multi-Character Handoff

**Trigger:** User says "Hey Chat! What do I need for cornbread?" then follows up with "Hey Chat! Add those to my shopping list"
**Expected Behavior:**

- Delilah responds with recipe ingredients (4-5 sentences)
- User asks to add ingredients to shopping list
- Delilah responds with flirty persuasion: "Haaank, sugar pie, would you be a dear and add cornmeal, buttermilk, eggs, and butter to the shopping list?"
- Hank responds: "Aye, Cookie. All added to the list."
- Handoff feels natural, total time under 4 seconds
- Shopping list actually updates with all ingredients
- **Note:** Users always address the system with "Hey Chat!" - they cannot directly address individual characters. The system routes to appropriate character(s) based on context.

**Edge Cases:**

- Hank not yet unlocked → Delilah handles it herself (deadpan mode)
- Simple single-item request → Hank responds directly without Delilah handoff
- Complex multi-item list → Coordinate between characters efficiently

---

### UC5: Morning Briefing (Chapter 4+)

**Trigger:** User says "Good morning" or Cave triggers proactively at set time  
**Expected Behavior:**

- Cave delivers enthusiastic briefing (10-15 seconds)
- Mentions today's calendar events
- Comments on home status
- Suggests tasks or activities
- Over-the-top SCIENCE enthusiasm

**Edge Cases:**

- No calendar events → Cave makes it sound exciting anyway with lots of opportunities for SCIENCE!
- User running late → Brief version
- User doesn't want briefing → Can be disabled while keeping character

---

### UC6: Failed Plan Callback (Chapter 7+)

**Trigger:** User says "Hey Chat! Add batteries to the shopping list"
**Expected Behavior:**

- Hank responds: "Aye, I got'em on the list."
- Cave interjects: "ALSO! Add linear actuators! For the robot bodies! SCIENCE!"
- Hank responds: "[Resigned sigh] Cap'n, I can't be addin' things without orders..."
- Cave: "Not with THAT attitude you can't!"
- Shopping list updates with only batteries (user's actual request)
- Running gag reinforced - Cave tries but fails to hijack shopping list
- Total interaction under 6 seconds

---

## User Stories

### As a busy parent, I want

- Quick timer setting without precise commands so I can multitask while cooking
- Recipe guidance that keeps track of where I am so I don't lose my place
- Smart home control that understands context ("make it cozy" instead of 5
  separate commands)

### As a child in the household, I want

- Fun character voices that make asking questions entertaining
- Characters that respond to me appropriately for my age
- To feel like I'm talking to personalities, not a machine

### As a technical user (Justin), I want

- Access to advanced features through natural language
- Ability to create and modify automations conversationally
- Character consistency that demonstrates the system's capability
- Story progression that rewards continued use

### As a family member, I want

- Reliable functionality that doesn't make me repeat myself
- Characters I can remember and recognize
- Entertainment value that doesn't interfere with getting things done
- To be surprised and delighted by callbacks and character development

---

## Non-Functional Requirements

**Prototype Priority:** For Phase 1, prioritize simplicity and character/story quality above all else. Keep it simple enough to validate the core experience.

### NFR1: Character Consistency (CRITICAL)

- Character voices remain recognizable across all interactions
- Story beats deliver appropriate variants based on context
- Personality quirks and mannerisms feel authentic
- **This is the core differentiator - cannot be compromised**

### NFR2: Simplicity (CRITICAL)

- Minimize technical complexity wherever possible
- Simple, straightforward architecture
- Easy to modify and iterate on
- Avoid premature optimization

### NFR3: Performance (Important)

- Simple task responses begin within 2-3 seconds (best effort)
- Complex task responses begin within 3-5 seconds (best effort)
- Multi-character coordination completes within 6 seconds (best effort)
- **Note:** Acceptable to have slower responses in prototype if it means simpler code

### NFR4: Maintainability (Important)

- Story content separable from code
- Character definitions modular and extensible
- Easy to add new story beats or modify existing ones

### NFR5: Privacy (Deferred for Phase 1)

- Not a priority for early prototype
- Can send data to cloud services as needed
- Privacy considerations deferred to later phases

### NFR6: Reliability (Deferred for Phase 1)

- Best effort reliability acceptable for prototype
- No need for graceful degradation or fallback systems
- Can fail visibly during development

### NFR7: Cost (Awareness)

- Monitor LLM token usage to avoid runaway costs
- No need to optimize aggressively in Phase 1
- Awareness and basic monitoring sufficient

---

## Constraints

### Technical Constraints - Phase 1

- Simple web interface for voice/text input (no Home Assistant integration required)
- TTS quality limited by available voice generation options (ElevenLabs or similar)
- Must work in browser with microphone access
- **Deferred to later phases:**
  - Home Assistant integration
  - ESPHome device control
  - Voice processing pipeline integration

### Time Constraints

- Phase 1 (Chapter 1) target: 2-4 weeks for basic prototype
- Focus on getting character interactions working first
- Iterate quickly, avoid scope creep

### User Constraints - Phase 1

- Primary user: Justin (technical, tolerant of rough edges)
- Family testing optional in Phase 1
- No requirement to match Alexa reliability yet - this is a prototype

---

## Out of Scope (For Initial Release)

### Explicitly Not Included

- Mobile app interface (voice-only initially)
- Multi-language support
- Custom wake word (uses Home Assistant default)
- Voice biometrics for user identification
- Music playback control
- Video streaming integration
- Third-party skill ecosystem
- Voice shopping/purchases
- Outbound calling
- SMS/messaging integration

### Future Considerations

- Additional characters beyond the core four
- Branching story paths based on user choices
- Character customization by user
- Community-contributed chapters
- Integration with other smart home platforms beyond Home Assistant

---

## Success Metrics

### Quantitative Metrics

- **Response Time:** 90% of interactions under 3 seconds to first audio
- **Task Completion:** 95% of user requests completed successfully
- **Usage:** Daily active use by at least 2 family members
- **Chapter Progression:** Users complete Chapter 1 within 2 weeks
- **Story Engagement:** At least 3 multi-turn story conversations per chapter

### Qualitative Metrics

- **Character Recognition:** Family members can identify which character is
  speaking without being told
- **Emotional Investment:** Users report caring about what happens to characters
- **Unprompted Quotes:** Family members quote characters in non-interaction
  contexts
- **Preference Over Alexa:** Users choose this system over Alexa for tasks
- **Story Recall:** Users remember specific story moments weeks later

### Critical Success Factors

1. Characters feel like personalities, not random text generation
2. Story enhances rather than obstructs functionality
3. System is genuinely more useful than what it replaces
4. Emotional investment develops naturally over time
5. Technical implementation is maintainable and extensible

---

## Open Questions

### Story Pacing

- ~~Should chapters unlock purely on time/interaction count, or should user engagement accelerate progression?~~
  - **DECISION:** Chapters unlock when all required story beats are completed. No time/interaction count requirements. Story engagement drives progression.
- ~~What happens after Chapter 11? New characters? Ongoing maintenance story?~~
  - **DECISION:** Deferred. Will evaluate when users reach later chapters.
- ~~How do we handle users who ignore story but want functionality?~~
  - **DECISION:** Not a target user for Phase 1. Story engagement is core to the value proposition.

### Character Implementation

- Specific TTS voices locked in or still evaluating options?
- ~~Should character moods/states evolve based on user interaction patterns?~~
  - **DECISION:** Aspirational feature, but Phase 1 focuses on story-driven character behavior. Get the narrative-based interactions working first before adding dynamic mood systems.
- ~~How to handle family members developing favorite characters?~~
  - **DECISION:** This is desired and encouraged! However, users still cannot directly address characters by name - system always responds to "Hey Chat!" and routes based on context.

### Technical Details (Phase 1)

- ~~Screen hardware for dashboard - which device?~~
  - **DECISION:** Deferred to later phase. Web interface only for Phase 1.
- ~~Context window size per character - how much history?~~
  - **DECISION:** Two-tier context approach:
    - **Recent conversations:** Full dialogue from last 30 minutes for conversation consistency
    - **Historical context:** Summary of conversations from last 7 days for continuity
- Failure recovery - what if character response is unhelpful?
  - **NOTE:** Acceptable to fail visibly in Phase 1 prototype

### Interaction Design (Phase 1)

- Interrupt handling - can users cut off mid-response?
  - **NOTE:** Nice to have, not required for Phase 1
- ~~Turn-taking in multi-character conversations - how to prevent runaway dialogue?~~
  - **DECISION:** Implement turn limits per interaction. When approaching limit, have a character acknowledge it in-character (e.g., Hank: "This is takin' longer than we got time for, Cap'n. We'll hash this out later." or Delilah: "Oh sugar, we're just going on and on! Let us talk about this offline, honey."). Characters ostensibly continue the conversation off-mic.
  - **EXCEPTION:** User questions reset the turn count. If the user asks a follow-up question or engages with the conversation, the characters should continue to respond without cutting off.
- ~~Privacy modes - should children get different character behaviors?~~
  - **DECISION:** Deferred to later phase. Not a Phase 1 concern.

---

## Approval & Sign-off

**Product Owner:** Justin  
**Date:** January 2025

**Next Steps:**

1. Review and approve PRD
2. Create technical architecture document
3. Generate project plan from PRD
4. Begin Phase 1 development

---

*This PRD will be updated as requirements evolve through development and user testing.*
