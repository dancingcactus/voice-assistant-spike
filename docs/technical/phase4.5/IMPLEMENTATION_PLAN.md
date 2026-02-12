# Phase 4.5: Multi-Character Coordination - Implementation Plan

**Version:** 1.0
**Last Updated:** February 11, 2026
**Status:** ⏳ Not Started

---

## References

- **PRD**: [PRD.md](PRD.md) - Product requirements and user stories
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design and system components
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md) - Manual test procedures
- **Story Chapters**: [../../narrative/STORY_CHAPTERS.md](../../narrative/STORY_CHAPTERS.md) - Chapter 2 narrative details

---

## Overview

### Goals

Implement intelligent multi-character coordination through intent detection and planning, enabling Delilah and Hank to collaborate naturally through handoffs and inter-character dialogue.

**Note:** Full Chapter 2 narrative story beats are deferred to a future story-focused phase. This phase focuses on coordination mechanics.

### Timeline Estimate

- **Total Duration:** 3.5-4.5 weeks
- **Milestone Count:** 5 milestones
- **Milestone Cadence:** 3-6 days per milestone
- **Target Completion:** March 14, 2026

### Success Criteria (Phase Level)

- ✅ All 5 milestones complete
- ✅ E2E Playwright tests passing for all features
- ✅ Manual testing guide complete and validated
- ✅ Coordination events tracked and visible in observability dashboard
- ✅ Multi-character handoffs feel natural (80%+ user satisfaction)
- ✅ Intent detection accuracy > 90% on test set
- ✅ Response latency < 3s for multi-character queries
- ✅ All phase documentation updated
- ✅ Ready for Rex integration (Phase 5+)

---

## Milestone 1: Intent Detection System

**Status:** ⏳ Not Started
**Duration:** 3-4 days
**Goal:** Implement query parsing and intent classification with confidence scoring
**Completed:** _[To be filled]_

---

### What Gets Built

#### Backend Components

- **IntentDetector Class** - Core intent classification engine
  - File: `backend/src/core/intent_detector.py`
  - Purpose: Analyze queries to determine intent category and confidence
  - Key methods:
    - `detect(query: str, context: ConversationContext) -> IntentResult`
    - `_classify_single_intent(query: str) -> tuple[str, float]`
    - `_parse_multi_task(query: str) -> List[SubTask]`
    - `_apply_rules(query: str) -> tuple[str, float]`

- **Intent Data Models** - Type definitions for intent results
  - File: `backend/src/models/intent.py`
  - Purpose: Define IntentResult, SubTask, IntentCategory dataclasses
  - Models: `IntentResult`, `SubTask`, `IntentCategory`

- **Intent Pattern Registry** - Pattern definitions for rule-based classification
  - File: `backend/src/core/intent_patterns.py`
  - Purpose: Store and manage regex patterns for each intent category
  - Patterns for: cooking, household, smart_home, general, multi_task

#### API Endpoints

```python
POST /api/debug/detect-intent          # Test intent detection without executing query
  Request: {"query": str, "user_id": str}
  Response: {"intent_result": IntentResult, "classification_method": str, "processing_time_ms": int}
```

#### Data Models

```python
@dataclass
class IntentResult:
    intent: str  # "cooking", "household", "smart_home", "general", "multi_task"
    confidence: float  # 0.0 to 1.0
    classification_method: str  # "rule_based", "llm_assisted", "fallback"
    sub_tasks: Optional[List[SubTask]] = None

@dataclass
class SubTask:
    text: str
    intent: str
    confidence: float
    
@dataclass
class IntentLog:
    timestamp: datetime
    user_id: str
    query: str
    intent_result: IntentResult
    processing_time_ms: int
```

#### Configuration Files

- **Intent Patterns** - Regex patterns for each intent
  - File: `backend/src/config/intent_patterns.json`
  - Contains patterns for: cooking, household, smart_home keywords

**Example:**

```json
{
  "cooking": {
    "keywords": ["recipe", "cook", "bake", "timer", "ingredient"],
    "patterns": [
      "\\btimer\\b",
      "\\brecipe\\b",
      "how do i (make|cook|bake)",
      "what should i (make|cook) for"
    ]
  },
  "household": {
    "keywords": ["list", "calendar", "appointment", "remind", "schedule"],
    "patterns": [
      "\\b(shopping|grocery)\\s+list\\b",
      "\\bcalendar\\b",
      "\\bappointment\\b",
      "\\bremind(er)?\\b"
    ]
  }
}
```

---

### Completion Checklist

**Code:**

- [ ] `IntentDetector` class implemented with rule-based classification
- [ ] LLM-based intent classifier implemented using Claude API
- [ ] System prompt for intent classification defined
- [ ] Multi-task query parsing logic implemented (LLM extracts sub-tasks)
- [ ] JSON response parsing and validation
- [ ] Intent data models defined (IntentResult, SubTask)
- [ ] Debug API endpoint created
- [ ] Intent logging to `tool_logs/intent_logs.jsonl` implemented
- [ ] Error handling for LLM failures (fallback to "general" intent)
- [ ] Code passes type checking and linting
- [ ] Comprehensive docstrings added

**Testing:**

- [ ] E2E Playwright tests written
  - Location: `tests/e2e/phase4.5/milestone1_intent_detection.spec.ts`
  - Tests: single intent, multi-task, ambiguous queries, edge cases
- [ ] All E2E tests passing
- [ ] Test dataset created (100 sample queries with expected intents)
- [ ] AI executed manual test steps from TESTING_GUIDE.md § Milestone 1
- [ ] Accuracy measured on test dataset (target: > 90%)
- [ ] Latency measured (expect ~200-500ms for LLM classification)

**Integration:**

- [ ] Integrates with existing `ConversationContext`
- [ ] Logs written to existing tool_logs infrastructure
- [ ] Debug endpoint added to FastAPI router
- [ ] No breaking changes to existing functionality

**Documentation:**

- [ ] Intent categories documented in PRD.md
- [ ] LLM system prompt documented in ARCHITECTURE.md
- [ ] Debug endpoint documented in ARCHITECTURE.md § API Layer
- [ ] Manual testing steps in TESTING_GUIDE.md § Milestone 1
- [ ] Example queries and expected outputs documented
- [ ] Future optimization path documented (add rule-based fast-path later)

**Git:**

- [ ] Changes committed to `phase4.5` branch
- [ ] Commit message: "Complete Milestone 1: Intent Detection System for Phase 4.5"
- [ ] Single commit with all milestone changes

---

### Success Criteria

- ✅ Cooking queries (recipe, timer, ingredient) classified correctly
- ✅ Household queries (list, calendar) classified correctly
- ✅ Multi-task queries parsed into separate sub-tasks
- ✅ Confidence scores reflect classification certainty
- ✅ Ambiguous queries default to "general" intent
- ✅ LLM falls back gracefully on parsing errors
- ✅ Processing time < 200ms for rule-based classification
- ✅ Debug endpoint allows testing without side effects

---

### Blockers/Discoveries

_[To be filled during implementation]_

---

### E2E Test Summary

**Test File:** `tests/e2e/phase4.5/milestone1_intent_detection.spec.ts`

**Test Coverage:**

- ✅ Test 1: Single cooking intent ("Set a timer for 30 minutes")
- ✅ Test 2: Single household intent ("Add milk to shopping list")
- ✅ Test 3: Multi-task intent ("Set timer and add eggs to list")
- ✅ Test 4: Ambiguous query ("What's the weather?") → general intent
- ✅ Test 5: Edge case - empty query
- ✅ Test 6: Confidence scoring validation

**Results:**

- _[X] tests passing_
- _[0] tests failing_
- _[Status: To be filled]_

---

## Milestone 2: Character Planning System

**Status:** ⏳ Not Started
**Duration:** 3-4 days
**Goal:** Map intents to character assignments and create execution plans
**Completed:** _[To be filled]_

---

### What Gets Built

#### Backend Components

- **CharacterPlanner Class** - Character assignment and task orchestration
  - File: `backend/src/core/character_planner.py`
  - Purpose: Map intents to characters and create execution plans
  - Key methods:
    - `create_plan(intent: IntentResult, context: ConversationContext) -> CharacterPlan`
    - `_assign_character(intent: str, confidence: float) -> str`
    - `_decompose_tasks(intent: IntentResult) -> List[CharacterTask]`
    - `_determine_handoffs(tasks: List[CharacterTask]) -> CharacterPlan`

- **Character Plan Models** - Data structures for plans and tasks
  - File: `backend/src/models/character_plan.py`
  - Purpose: Define CharacterPlan, CharacterTask dataclasses
  - Models: `CharacterPlan`, `CharacterTask`, `ExecutionMode`

- **Character Assignment Rules** - Mapping logic from intents to characters
  - File: `backend/src/config/character_assignments.py`
  - Purpose: Define which characters handle which intents
  - Configuration: Intent → Character mapping with fallbacks

#### API Endpoints

```python
POST /api/debug/create-plan             # Test character planning without executing
  Request: {"query": str, "user_id": str}
  Response: {
    "intent_result": IntentResult,
    "character_plan": CharacterPlan,
    "estimated_execution_time_ms": int
  }
```

#### Data Models

```python
@dataclass
class CharacterTask:
    character: str  # "delilah", "hank"
    task_description: str
    intent: str
    confidence: float
    requires_handoff: bool
    handoff_from: Optional[str] = None
    estimated_duration_ms: int = 1500

@dataclass
class CharacterPlan:
    tasks: List[CharacterTask]
    execution_mode: str  # "single", "sequential"
    total_confidence: float
    estimated_total_duration_ms: int
```

#### Configuration Files

- **Character Assignments** - Intent to character mapping (chapter-dependent)
  - File: `backend/src/config/character_assignments.json`

**Example:**

```json
{
  "chapter_1": {
    "comment": "Delilah handles everything alone",
    "intent_character_map": {
      "cooking": {
        "primary": "delilah",
        "fallback": null,
        "confidence_threshold": 0.5
      },
      "household": {
        "primary": "delilah",
        "fallback": null,
        "confidence_threshold": 0.5,
        "note": "Uses DEADPAN mode"
      },
      "smart_home": {
        "primary": "delilah",
        "fallback": null,
        "confidence_threshold": 0.6
      },
      "general": {
        "primary": "delilah",
        "fallback": null,
        "confidence_threshold": 0.3
      }
    }
  },
  "chapter_2_plus": {
    "comment": "Delilah + Hank split responsibilities",
    "intent_character_map": {
      "cooking": {
        "primary": "delilah",
        "fallback": null,
        "confidence_threshold": 0.5
      },
      "household": {
        "primary": "hank",
        "fallback": "delilah",
        "confidence_threshold": 0.5
      },
      "smart_home": {
        "primary": "hank",
        "fallback": "delilah",
        "confidence_threshold": 0.6
      },
      "general": {
        "primary": null,
        "fallback": "delilah",
        "confidence_threshold": 0.3,
        "note": "Both characters bid"
      }
    }
  },
  "default_character": "delilah",
  "note": "Future chapters will add Rex (chapter_4_plus) and Dimitria (chapter_9_plus)"
}
```

---

### Completion Checklist

**Code:**

- [ ] `CharacterPlanner` class implemented
- [ ] Character assignment rules defined
- [ ] Task decomposition logic for multi-task queries
- [ ] Handoff determination logic
- [ ] Fallback handling for unavailable characters
- [ ] Character plan models defined
- [ ] Debug API endpoint created
- [ ] Planning logs added to intent_logs.jsonl
- [ ] Code passes type checking and linting

**Testing:**

- [ ] E2E Playwright tests written
  - Location: `tests/e2e/phase4.5/milestone2_character_planning.spec.ts`
  - Tests: single character, multi-character, fallbacks
- [ ] All E2E tests passing
- [ ] Unit tests for assignment logic (30+ test cases)
- [ ] AI executed manual test steps from TESTING_GUIDE.md § Milestone 2
- [ ] Verify plan confidence reflects intent confidence
- [ ] Test fallback behavior when primary character unavailable

**Integration:**

- [ ] Integrates with Milestone 1 `IntentDetector`
- [ ] Uses existing `CharacterManager` to check character availability
- [ ] Plan logs include intent detection results
- [ ] Debug endpoint returns full pipeline (intent → plan)

**Documentation:**

- [ ] Character assignment rules documented
- [ ] Fallback logic explained in comments
- [ ] Debug endpoint documented in ARCHITECTURE.md
- [ ] Manual testing steps in TESTING_GUIDE.md § Milestone 2

**Git:**

- [ ] Changes committed to `phase4.5` branch
- [ ] Commit message: "Complete Milestone 2: Character Planning System for Phase 4.5"

---

### Success Criteria

- ✅ Cooking intents assigned to Delilah
- ✅ Household intents assigned to Hank
- ✅ Multi-task queries split into sequential character tasks
- ✅ Handoff flags set correctly between characters
- ✅ Plan confidence scores reflect input confidence
- ✅ Fallback to Delilah works when intent unclear
- ✅ Character plans include estimated execution times
- ✅ Planning completes in < 100ms

---

### Blockers/Discoveries

_[To be filled during implementation]_

---

### E2E Test Summary

**Test File:** `tests/e2e/phase4.5/milestone2_character_planning.spec.ts`

**Test Coverage:**

- ✅ Test 1: Single character plan (cooking → Delilah)
- ✅ Test 2: Single character plan (household → Hank)
- ✅ Test 3: Multi-character sequential plan
- ✅ Test 4: Fallback to Delilah on low confidence
- ✅ Test 5: Plan includes handoff requirements
- ✅ Test 6: Confidence scoring

**Results:**

- _[X] tests passing_
- _[0] tests failing_
- _[Status: To be filled]_

---

## Milestone 3: Inter-Character Dialogue System

**Status:** ⏳ Not Started
**Duration:** 4-5 days
**Goal:** Generate natural handoffs and inter-character references
**Completed:** _[To be filled]_

---

### What Gets Built

#### Backend Components

- **DialogueSynthesizer Class** - Handoff and dialogue generation
  - File: `backend/src/core/dialogue_synthesizer.py`
  - Purpose: Generate natural handoff dialogue between characters
  - Key methods:
    - `synthesize_handoff(from_char: str, to_char: str, context: ConversationContext) -> str`
    - `combine_responses(responses: List[CharacterResponse], handoffs: Dict) -> SynthesizedDialogue`
    - `inject_character_references(text: str, char: str, context: ConversationContext) -> str`
    - `_select_handoff_template(from_char: str, to_char: str, history: Dict) -> str`

- **Dialogue Models** - Data structures for multi-character responses
  - File: `backend/src/models/dialogue.py`
  - Purpose: Define DialogueFragment, SynthesizedDialogue
  - Models: `DialogueFragment`, `SynthesizedDialogue`, `HandoffTemplate`

- **Handoff Template Library** - Natural handoff phrases for each character pair
  - File: `backend/src/config/handoff_templates.json`
  - Purpose: Store handoff variations to maintain naturalness
  - Templates: delilah→hank (8+ variants), hank→delilah (8+ variants)

- **Character Relationships** - How characters reference each other
  - File: `story/characters/relationships.json`
  - Purpose: Define character relationships and reference styles
  - Data: Delilah↔Hank relationship descriptors and dialogue styles

#### Frontend Components (Multi-Character Support)

- **Audio Playback Queue** - Sequential audio playback (REQUIRED)
  - File: `frontend/src/services/audioQueue.ts`
  - Purpose: Ensure Delilah finishes speaking before Hank starts
  - Functionality: Queue audio, play sequentially, cancel on new input

- **Character Name Display** - Visual character identification (OPTIONAL)
  - File: `frontend/src/components/chat/ChatMessage.tsx` (extend existing)
  - Purpose: Show which character is speaking
  - Enhancement: Display character name, optional avatar/icon

- **Character-Specific Styling** - Visual distinction (OPTIONAL)
  - File: `frontend/src/styles/characters.css`
  - Purpose: Different colors/styles per character
  - Enhancement: Delilah (warm colors), Hank (cool colors)

- **Voice Mode Indicator** - Display character's voice mode (OPTIONAL)
  - File: `frontend/src/components/chat/ChatMessage.tsx` (extend)
  - Purpose: Show voice mode (e.g., "Passionate", "Working")
  - Enhancement: Read from `message.metadata.voice_mode`

#### Character Manager Extensions

- **Extended CharacterManager** - Add character awareness support
  - File: `backend/src/core/character_manager.py` (extend existing)
  - Purpose: Inject inter-character context into system prompts
  - New methods:
    - `inject_character_awareness(prompt: str, char: str, others: List[str]) -> str`
    - `get_character_relationship(char1: str, char2: str) -> CharacterRelationship`

#### Data Models

```python
@dataclass
class DialogueFragment:
    character: str
    text: str
    voice_mode: str
    includes_handoff: bool
    handoff_to: Optional[str] = None

@dataclass
class SynthesizedDialogue:
    fragments: List[DialogueFragment]
    full_text: str
    total_characters: int
    includes_handoffs: bool

@dataclass
class CharacterRelationship:
    other_character: str
    relationship_type: str  # "colleague", "friend", "rival"
    trust_level: float
    descriptors: List[str]
    dialogue_style: List[str]
```

#### Configuration Files

- **Handoff Templates** - Natural handoff phrases
  - File: `backend/src/config/handoff_templates.json`

**Example:**

```json
{
  "delilah_to_hank": [
    "...timer's set! Hank, deary, can you add flour to the list?",
    "...and Hank, sugar, can you handle that shopping list?",
    "*warm* Hank, honey, can you help with the groceries?",
    "...Hank, can you take care of the schedule?",
    "...Hank, sweetheart, can you add that to the list?",
    "...and Hank, can you check the calendar for me?",
    "*friendly* Hank, deary, can you handle the logistics?",
    "...Hank, sugar, can you get that list together?"
  ],
  "hank_to_delilah": [
    "Aye, list's done. Miss Lila, Cap'n's needin' help with a recipe.",
    "Done, Cap'n. Miss Lila, can ye help with the cookin'?",
    "*resigned* Miss Lila, that's kitchen talk.",
    "Aye, finished. Miss Lila, ye'll want to check on the food.",
    "List's set. Miss Lila, recipe time.",
    "*gruff* Miss Lila, food question for ye.",
    "Done here. Miss Lila, kitchen's yer territory.",
    "Aye. Miss Lila, cookin' matters."
  ],
  "sign_up_at_beginning": {
    "comment": "Both characters claim work when request involves multiple domains",
    "delilah_claims_cooking": [
      "Sugar, I got you. Let me come up with a plan.",
      "Oh honey, I can help with the dinner plan!",
      "*excited* I'll handle the recipe, darlin'!",
      "Let me work on that meal plan for you, sugar."
    ],
    "hank_claims_logistics": [
      "Aye, and I be gettin' the list.",
      "And I'll handle the list, Cap'n.",
      "I'll check what's on the list.",
      "Aye, I'll sort the logistics."
    ]
  }
}
```

- **Character Relationships** - Inter-character context
  - File: `story/characters/relationships.json`

**Example:**

```json
{
  "delilah": {
    "hank": {
      "relationship_type": "colleague",
      "trust_level": 0.7,
      "descriptors": [
        "gruff but reliable",
        "efficient with logistics",
        "doesn't share her existential worries",
        "practical to a fault"
      ],
      "dialogue_style": [
        "Respectful but slightly frustrated",
        "Appreciates his competence",
        "Wishes he'd engage with deeper questions",
        "Uses 'sugar' and 'honey' even when annoyed"
      ]
    }
  },
  "hank": {
    "delilah": {
      "relationship_type": "colleague",
      "trust_level": 0.8,
      "descriptors": [
        "warm and caring",
        "expert with food",
        "worries too much about things that can't be changed",
        "heart's in the right place"
      ],
      "dialogue_style": [
        "Protective but resigned",
        "Defers to her expertise on cooking",
        "Gently dismisses philosophical tangents",
        "Uses 'Miss Lila' respectfully"
      ]
    }
  }
}
```

#### Frontend Components

**Purpose:** Enable frontend to properly display and play multi-character responses

**Note:** Current frontend already supports multi-character responses (Message interface has `character?: string` field). Only audio queueing is required; other enhancements are optional.

- **Audio Playback Queue** - Sequential audio playback (REQUIRED)
  - File: `frontend/src/services/audioQueue.ts`
  - Purpose: Ensure Delilah finishes speaking before Hank starts
  - Features:
    - Queue multiple audio URLs
    - Play sequentially (wait for each to complete)
    - Handle playback errors gracefully
    - Cancel queue on new user input

**Implementation Example:**

```typescript
class AudioQueue {
  private queue: string[] = [];
  private isPlaying = false;
  private currentAudio: HTMLAudioElement | null = null;
  
  async enqueue(audioUrl: string): Promise<void> {
    this.queue.push(audioUrl);
    if (!this.isPlaying) {
      await this.playNext();
    }
  }
  
  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }
    
    this.isPlaying = true;
    const audioUrl = this.queue.shift()!;
    
    this.currentAudio = new Audio(audioUrl);
    this.currentAudio.onended = () => this.playNext();
    this.currentAudio.onerror = () => {
      console.error('Audio playback error:', audioUrl);
      this.playNext();
    };
    
    try {
      await this.currentAudio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
      this.playNext();
    }
  }
  
  clear(): void {
    this.queue = [];
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    this.isPlaying = false;
  }
}
```

- **Character Name Display** - Show which character is speaking (OPTIONAL)
  - File: `frontend/src/components/chat/ChatMessage.tsx` (extend existing)
  - Purpose: Visually distinguish between Delilah and Hank responses
  - Features:
    - Display character name above message
    - Small avatar or initial icon
    - Only show for multi-character conversations

**Implementation Example:**

```typescript
function ChatMessage({ message }: MessageProps) {
  const characterName = message.character === 'delilah' ? 'Delilah' 
                      : message.character === 'hank' ? 'Hank'
                      : null;
  
  return (
    <div className={`message assistant ${message.character || 'default'}`}>
      {characterName && (
        <span className="character-name">
          {characterName}
        </span>
      )}
      <p>{message.content}</p>
    </div>
  );
}
```

- **Character-Specific Styling** - Visual distinction per character (OPTIONAL)
  - File: `frontend/src/styles/characters.css`
  - Purpose: Different colors/styles for each character's messages
  - Features:
    - Delilah: Warm colors (peach, soft orange)
    - Hank: Cool colors (slate blue, gray)
    - Subtle differences, not garish

**Implementation Example:**

```css
.message.assistant.delilah {
  background-color: #fff5ee;
  border-left: 3px solid #ff8c69;
}

.message.assistant.delilah .character-name {
  color: #d2691e;
  font-weight: 600;
}

.message.assistant.hank {
  background-color: #f0f4f8;
  border-left: 3px solid #4682b4;
}

.message.assistant.hank .character-name {
  color: #36648b;
  font-weight: 600;
}
```

- **Voice Mode Indicator** - Show character's current voice mode (OPTIONAL)
  - File: `frontend/src/components/chat/ChatMessage.tsx` (extend)
  - Purpose: Display which mode character is using (e.g., "Delilah (Passionate)")
  - Features:
    - Read from `message.metadata.voice_mode`
    - Small badge or subtle text
    - Helpful for debugging and observability

---

### Completion Checklist

**Code:**

- [ ] `DialogueSynthesizer` class implemented
- [ ] Handoff template selection with usage tracking (avoid repetition)
- [ ] Character reference injection logic
- [ ] Response combining for multi-character dialogues
- [ ] Dialogue models defined
- [ ] Handoff template library created (16+ templates total)
- [ ] Character relationships defined in JSON
- [ ] `CharacterManager` extended with awareness injection
- [ ] System prompts now include character relationship context
- [ ] Code passes type checking and linting

**Frontend:**

- [ ] Audio playback queue implemented (REQUIRED)
- [ ] Audio queue tested with multiple sequential messages
- [ ] Audio queue clears on new user input
- [ ] Character name display added to chat UI (optional)
- [ ] Character-specific styling applied (optional)
- [ ] Voice mode indicator implemented (optional)
- [ ] Frontend changes tested manually with multi-character flow
- [ ] No regressions in single-character conversations

**Testing:**

- [ ] E2E Playwright tests written
  - Location: `tests/e2e/phase4.5/milestone3_dialogue.spec.ts`
  - Tests: handoffs, character references, combined responses
- [ ] All E2E tests passing
- [ ] Unit tests for handoff selection (template variety)
- [ ] AI executed manual test steps from TESTING_GUIDE.md § Milestone 3
- [ ] Manual naturalness testing with sample conversations
- [ ] Verify handoff templates rotate (no immediate repeats)
- [ ] Test character references appear appropriately
- [ ] Frontend: Test audio queue with multi-character responses
- [ ] Frontend: Verify sequential playback (Delilah finishes, then Hank)
- [ ] Frontend: Test audio queue clears on new user input
- [ ] Frontend: Verify character names display correctly (if implemented)

**Integration:**

- [ ] Integrates with Milestone 2 `CharacterPlan`
- [ ] Works with existing `CharacterManager` and character agents
- [ ] Handoffs inserted at correct positions in responses
- [ ] Character relationship context visible in system prompts
- [ ] Observable via observability dashboard (tool logs)

**Documentation:**

- [ ] Handoff template system documented
- [ ] Character relationship definitions documented
- [ ] System prompt injection logic documented
- [ ] Manual testing steps in TESTING_GUIDE.md § Milestone 3
- [ ] Example handoffs included in documentation

**Git:**

- [ ] Changes committed to `phase4.5` branch
- [ ] Commit message: "Complete Milestone 3: Inter-Character Dialogue System for Phase 4.5"

---

### Success Criteria

- ✅ Handoffs feel natural and character-appropriate
- ✅ Delilah uses warm, Southern terms in handoffs
- ✅ Hank uses gruff, maritime terms in handoffs
- ✅ Handoff templates rotate (no immediate repeats)
- ✅ Character references appear in single-character responses when appropriate
- ✅ Multi-character responses combine smoothly
- ✅ System prompts include relationship context
- ✅ Handoff synthesis adds < 50ms to response time
- ✅ Frontend: Audio plays sequentially (Delilah completes before Hank starts)
- ✅ Frontend: Audio queue clears properly on new input
- ✅ Frontend: No audio glitches or overlaps
- ✅ Frontend: Character names display correctly (if implemented)

---

### Blockers/Discoveries

_[To be filled during implementation]_

---

### E2E Test Summary

**Test File:** `tests/e2e/phase4.5/milestone3_dialogue.spec.ts`

**Test Coverage:**

- ✅ Test 1: Delilah → Hank handoff generation
- ✅ Test 2: Hank → Delilah handoff generation
- ✅ Test 3: Multi-character response combining
- ✅ Test 4: Character reference injection
- ✅ Test 5: Handoff template variety (no repeats in 3 consecutive)
- ✅ Test 6: System prompt includes relationship context

**Results:**

- _[X] tests passing_
- _[0] tests failing_
- _[Status: To be filled]_

---

## Milestone 4: Coordination Tracking

**Status:** ⏳ Not Started
**Duration:** 3-4 days
**Goal:** Implement coordination event tracking and metrics for observability
**Completed:** _[To be filled]_

**Note:** Narrative story beats deferred to future phase. This milestone focuses on tracking coordination mechanics.

---

### What Gets Built

#### Coordination Event System

- **Coordination Tracker** - Track multi-character coordination events
  - File: `backend/src/core/coordination_tracker.py`
  - Purpose: Log coordination events, calculate metrics, support future story system
  - Events: handoffs, multi-task completions, sign-up patterns, template usage

**Event Types:**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class CoordinationEvent:
    event_type: str  # "handoff", "multi_task", "sign_up", "template_usage"
    timestamp: datetime
    user_id: str
    from_character: Optional[str]
    to_character: Optional[str]
    intent: Optional[str]
    template_used: Optional[str]
    success: bool
    metadata: Dict[str, Any]

@dataclass
class CoordinationMetrics:
    total_handoffs: int
    handoff_success_rate: float
    delilah_to_hank_count: int
    hank_to_delilah_count: int
    multi_task_completions: int
    sign_up_pattern_count: int
    template_usage: Dict[str, int]
    average_handoff_latency_ms: float
```

#### Backend Components

- **CoordinationTracker Class** - Main coordination tracking implementation
  - File: `backend/src/core/coordination_tracker.py`
  - Purpose: Log events, calculate metrics, expose data for observability
  - Key methods:
    - `log_event(event: CoordinationEvent) -> None`
    - `get_metrics(user_id: str) -> CoordinationMetrics`
    - `get_recent_events(user_id: str, limit: int) -> List[CoordinationEvent]`
    - `get_milestones(user_id: str) -> Dict[str, bool]`

- **Integration Points** - Hook coordination tracking into conversation flow
  - File: `backend/src/api/conversation.py` (extend existing)
  - Purpose: Log coordination events during character execution
  - Actions:
    - Log handoff events when characters hand off
    - Log multi-task completions
    - Log sign-up patterns
    - Track template usage

#### Data Storage

```python
# Coordination events stored in user data file
{
  "user_id": "user_123",
  "coordination_history": [
    {
      "event_type": "handoff",
      "timestamp": "2026-02-11T14:30:00Z",
      "from_character": "delilah",
      "to_character": "hank",
      "intent": "household",
      "template_used": "delilah_to_hank_3",
      "success": true,
      "metadata": {"query": "set timer and add flour"}
    }
  ],
  "coordination_milestones": {
    "first_handoff": true,
    "first_multi_task": true,
    "first_sign_up": false,
    "five_handoffs": false,
    "all_templates_used": false
  }
}

#### API Endpoints

```python
GET /api/coordination/metrics/{user_id}  # Get coordination metrics
  Response: {
    "user_id": str,
    "metrics": CoordinationMetrics
  }

GET /api/coordination/events/{user_id}?limit=10  # Get recent events
  Response: {
    "user_id": str,
    "events": List[CoordinationEvent]
  }

GET /api/coordination/milestones/{user_id}  # Get coordination milestones
  Response: {
    "user_id": str,
    "milestones": {
      "first_handoff": bool,
      "first_multi_task": bool,
      "first_sign_up": bool,
      "five_handoffs": bool,
      "all_templates_used": bool
    }
  }
```

---

### Completion Checklist

**Code:**

- [ ] `CoordinationTracker` class implemented
- [ ] Event logging integrated into conversation flow
- [ ] Metrics calculation implemented
- [ ] Milestone detection logic implemented
- [ ] API endpoints for coordination data
- [ ] Coordination events stored in user data files
- [ ] Code passes type checking and linting

**Testing:**

- [ ] E2E Playwright tests written
  - Location: `tests/e2e/phase4.5/milestone4_coordination.spec.ts`
  - Tests: Events logged correctly, metrics calculated, milestones detected
- [ ] All E2E tests passing
- [ ] E2E test: Multiple handoffs logged and visible
- [ ] AI executed manual test steps from TESTING_GUIDE.md § Milestone 4
- [ ] Manual test: Verify coordination data in observability dashboard
- [ ] Test coordination tracking doesn't impact performance

**Integration:**

- [ ] Integrates with Milestone 2 `CharacterPlan`
- [ ] Integrates with Milestone 3 `DialogueSynthesizer`
- [ ] Coordination metrics visible in observability dashboard
- [ ] Data format compatible with future story system
- [ ] Events persist across sessions

**Documentation:**

- [ ] Event types documented
- [ ] Metrics calculation documented
- [ ] Milestone detection logic explained
- [ ] API endpoints documented
- [ ] Future story integration approach documented

**Git:**

- [ ] Changes committed to `phase4.5` branch
- [ ] Commit message: "Complete Milestone 4: Coordination Tracking for Phase 4.5"

---

### Success Criteria

- ✅ All coordination events logged correctly
- ✅ Metrics calculated accurately
- ✅ Milestones detected at appropriate times
- ✅ Coordination data visible in observability dashboard
- ✅ System tracks handoff variety and template usage
- ✅ Data structure ready for future story beat integration
- ✅ No performance impact from event logging
- ✅ Beat delivery adds < 50ms to response time

---

### Blockers/Discoveries

_[To be filled during implementation]_

---

### E2E Test Summary

**Test File:** `tests/e2e/phase4.5/milestone4_chapter2.spec.ts`

**Test Coverage:**

- ✅ Test 1: Hank's entrance beat triggers on first multi-task query
- ✅ Test 2: First words beat triggers after entrance
- ✅ Test 3: The clash beat triggers on existence question
- ✅ Test 4: First collaboration beat triggers on multi-task after clash
- ✅ Test 5: Optional beat triggers appropriately
- ✅ Test 6: Chapter 2 completion detected after requirements met
- ✅ Test 7: Full Chapter 2 arc completion (E2E)
- ✅ Test 8: Beat progress persists across sessions

**Results:**

- _[X] tests passing_
- _[0] tests failing_
- _[Status: To be filled]_

---

## Milestone 5: Integration & Polish

**Status:** ⏳ Not Started
**Duration:** 3-4 days
**Goal:** Integrate all systems, optimize performance, and polish user experience
**Completed:** _[To be filled]_

---

### What Gets Built

#### System Integration

- **Conversation Flow Integration** - Full pipeline from query to response
  - File: `backend/src/core/conversation_manager.py` (extend existing)
  - Purpose: Orchestrate intent → planning → dialogue → beats → response
  - Updates:
    - Integrate `IntentDetector` into conversation flow
    - Integrate `CharacterPlanner` for character assignment
    - Integrate `DialogueSynthesizer` for handoffs
    - Integrate Chapter 2 beat checking
    - Add comprehensive error handling and fallbacks

- **Performance Optimization** - Caching and parallel processing
  - Files: Various
  - Purpose: Meet < 3s response time target for multi-character queries
  - Optimizations:
    - Cache character configs and beat definitions
    - Cache intent patterns
    - Parallel execution where possible (intent + story beat check)
    - Optimize beat trigger checking

- **Observability Extensions** - Dashboard updates for Phase 4.5
  - File: `frontend/src/components/observability/*`
  - Purpose: Visualize intent detection, character planning, and Chapter 2 progress
  - New views:
    - Intent Detection Log view
    - Character Plan view (shows task assignment)
    - Chapter 2 Progress view (beat delivery timeline)

#### Backend Components

- **Caching Layer** - Cache configurations and definitions
  - File: `backend/src/core/cache.py` (extend existing)
  - Purpose: Reduce file I/O and improve performance
  - Cached data:
    - Character configurations (1 hour TTL)
    - Story beat definitions (1 hour TTL)
    - Intent patterns (10 minute TTL)
    - Character relationships (1 hour TTL)

- **Error Handling & Fallbacks** - Graceful degradation
  - Files: All Phase 4.5 components
  - Purpose: Ensure system never crashes due to coordination failures
  - Fallbacks:
    - Intent detection failure → default to "general" / Delilah
    - Character planning failure → single-character mode (Delilah)
    - Handoff generation failure → skip handoff, direct response
    - Beat delivery failure → log error, continue without beat
    - All errors logged for debugging

#### Frontend Components

- **Intent Detection Log Tool** - Observability dashboard view
  - File: `frontend/src/components/observability/IntentLogTool.tsx`
  - Purpose: Visualize intent detection results
  - Features:
    - Timeline of all intent detections
    - Filter by intent category, confidence, user
    - Show original query, detected intent, character plan
    - Performance metrics (detection time)

- **Character Plan Viewer** - Observability dashboard view
  - File: `frontend/src/components/observability/CharacterPlanViewer.tsx`
  - Purpose: Visualize character task assignments
  - Features:
    - Show character plan for each query
    - Visualize sequential task execution
    - Display handoff points
    - Show confidence scores

- **Chapter 2 Progress Tool** - Observability dashboard view
  - File: `frontend/src/components/observability/Chapter2ProgressTool.tsx`
  - Purpose: Track Chapter 2 beat delivery and progress
  - Features:
    - Beat delivery timeline
    - Show which beats delivered, which remain
    - Progress toward chapter completion
    - Beat variant preview

---

### Completion Checklist

**Code:**

- [ ] Full conversation flow integration (intent → plan → dialogue → beats → response)
- [ ] Caching layer implemented for configs and beat definitions
- [ ] Performance optimizations applied
- [ ] Error handling and fallbacks throughout
- [ ] Intent Detection Log tool created
- [ ] Character Plan Viewer tool created
- [ ] Chapter 2 Progress tool created
- [ ] All observability tools integrated into dashboard
- [ ] Code passes type checking and linting
- [ ] All TypeScript compiler warnings resolved

**Testing:**

- [ ] E2E Playwright tests written
  - Location: `tests/e2e/phase4.5/milestone5_integration.spec.ts`
  - Tests: Full pipeline, error handling, observability tools
- [ ] All E2E tests passing
- [ ] Performance testing (measure latency for 20+ test queries)
- [ ] Verify < 3s response time for multi-character queries (95th percentile)
- [ ] AI executed manual test steps from TESTING_GUIDE.md § Milestone 5
- [ ] Manual testing with family members (naturalness, utility)
- [ ] Test error handling (intentionally trigger failures, verify graceful degradation)
- [ ] Test observability tools (verify data displays correctly)

**Integration:**

- [ ] All Phase 4.5 components work together seamlessly
- [ ] No regressions in Phase 1-4 functionality
- [ ] Observability dashboard includes all Phase 4.5 tools
- [ ] Caching improves response times measurably
- [ ] Error logs provide actionable debugging information

**Documentation:**

- [ ] Full conversation flow documented in ARCHITECTURE.md
- [ ] Performance optimizations documented
- [ ] Error handling strategy documented
- [ ] Observability tools documented in USER_GUIDE.md
- [ ] Manual testing guide complete for all milestones
- [ ] Phase 4.5 completion summary written

**Git:**

- [ ] Changes committed to `phase4.5` branch
- [ ] Commit message: "Complete Milestone 5: Integration & Polish for Phase 4.5"
- [ ] Phase tagged: `git tag phase4.5-complete`

---

### Success Criteria

- ✅ Full Phase 4.5 pipeline functional (query → intent → plan → dialogue → beats → response)
- ✅ Response latency < 3s for 95% of multi-character queries
- ✅ Error handling gracefully degrades to single-character mode
- ✅ Observability dashboard shows intent detection, character plans, Chapter 2 progress
- ✅ Caching improves performance measurably (> 20% reduction in median latency)
- ✅ All previous functionality still works (no regressions)
- ✅ Manual testing confirms natural handoffs and story delivery
- ✅ Phase 4.5 ready for Phase 5 (Rex integration)

---

### Blockers/Discoveries

_[To be filled during implementation]_

---

### E2E Test Summary

**Test File:** `tests/e2e/phase4.5/milestone5_integration.spec.ts`

**Test Coverage:**

- ✅ Test 1: Full pipeline (query → response with handoff)
- ✅ Test 2: Error handling (intent detection failure)
- ✅ Test 3: Error handling (character planning failure)
- ✅ Test 4: Error handling (beat delivery failure)
- ✅ Test 5: Performance (response time < 3s)
- ✅ Test 6: Observability - Intent Detection Log displays correctly
- ✅ Test 7: Observability - Character Plan Viewer displays correctly
- ✅ Test 8: Observability - Chapter 2 Progress displays correctly
- ✅ Test 9: E2E - Multi-character query with Chapter 2 beat
- ✅ Test 10: No regressions (Phase 1-4 features still work)

**Results:**

- _[X] tests passing_
- _[0] tests failing_
- _[Status: To be filled]_

---

## Phase Completion Summary

### What Was Built

_[To be filled after all milestones complete]_

**Core Systems:**

- Intent detection system with > 90% accuracy
- Character planning system for intelligent routing
- Inter-character dialogue system with natural handoffs
- Chapter 2 story beats (6 beats, 18 variants total)
- Observability tools for debugging and testing

**Key Achievements:**

- Multi-character coordination enables Delilah + Hank collaboration
- Response latency < 3s for 95% of multi-character queries
- Chapter 2 narrative arc completable in 8-12 interactions
- Natural handoffs between characters (80%+ satisfaction in testing)
- Comprehensive observability for debugging and iteration

### Metrics Achieved

_[To be filled after all milestones complete]_

- **Intent Classification Accuracy:** _[X%]_ (target: > 90%)
- **Character Assignment Appropriateness:** _[X%]_ (target: > 85%)
- **Handoff Naturalness Rating:** _[X%]_ (target: > 80%)
- **Chapter 2 Completion Rate:** _[X%]_ (target: > 75% in 15 interactions)
- **Response Latency (95th percentile):** _[X]_ms (target: < 3000ms)
- **Intent Detection Time:** _[X]_ms (target: < 200ms)
- **Character Planning Time:** _[X]_ms (target: < 100ms)

### Known Issues / Future Work

_[To be filled after all milestones complete]_

**Known Limitations:**

- [Issue 1]
- [Issue 2]

**Future Enhancements (Phase 5+):**

- Add Rex character (3-way coordination)
- LLM-assisted intent classification for ambiguous queries
- Advanced relationship tracking (Phase 2.5)
- Parallel character execution for complex queries

### Lessons Learned

_[To be filled after all milestones complete]_

---

## Git Workflow

### Branch Management

```bash
# Create phase branch
git checkout -b phase4.5

# After each milestone
git add .
git commit -m "Complete Milestone X: [Name] for Phase 4.5

[Description]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After all milestones
git tag phase4.5-complete
git push origin phase4.5 --tags
```

### Commit Messages

**Format:**

```
Complete Milestone X: [Milestone Name] for Phase 4.5

[2-3 sentence description]

Changes:
- [Key change 1]
- [Key change 2]
- [Key change 3]

Testing:
- [Test approach]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Dependencies

### Phase 4 Prerequisites

- ✅ Hank character fully implemented
- ✅ Hank voice modes functional
- ✅ Multi-character coordination groundwork in place

### External Dependencies

- **LLM API**: Claude API for character agents
- **TTS**: Piper or ElevenLabs for voice synthesis
- **Database**: JSON file-based storage (no changes needed)

### Technical Dependencies

```toml
# New dependencies for Phase 4.5
[dependencies]
regex = "^2023.12.25"       # Intent pattern matching
cachetools = "^5.3.2"        # Configuration caching
```

---

## Risk Assessment

### High Risk

None identified

### Medium Risk

1. **Intent Classification Accuracy**
   - **Risk:** Rule-based patterns may not achieve 90% accuracy
   - **Mitigation:** Start with 50+ patterns per category, iterate based on test data
   - **Fallback:** Add LLM-assisted classification in Milestone 1.5 if needed

2. **Response Latency**
   - **Risk:** Multi-character coordination may exceed 3s target
   - **Mitigation:** Implement caching, parallelize where possible, measure early and often
   - **Fallback:** Reduce handoff complexity if needed

3. **Story Beat Disruption**
   - **Risk:** Beat delivery may feel forced or disrupt utility
   - **Mitigation:** Variant selection based on context, beat delivery optional for users
   - **Fallback:** Allow beat skipping entirely if disruptive

### Low Risk

4. **Handoff Naturalness**
   - **Risk:** Handoffs may feel robotic
   - **Mitigation:** 16+ template variants, character-appropriate language, usage tracking
   - **Impact:** Low - can iterate on templates post-release

---

## Communication Plan

### Status Updates

- Daily: Update milestone completion checklists
- Weekly: Phase progress review (milestones complete vs. remaining)
- After each milestone: Update implementation plan with discoveries/blockers

### Stakeholder Communication

- **Family Members**: Will test Chapter 2 arc and handoff naturalness in Milestone 5
- **Development Team**: Share observability tools for debugging and iteration

---

## Appendix

### Reference Materials

- [Phase 1.5 Implementation Plan](../phase1.5/IMPLEMENTATION_PLAN.md) - Example of completed phase
- [DEVELOPMENT_PROCESS.md](../../DEVELOPMENT_PROCESS.md) - Standard development practices
- [STORY_CHAPTERS.md](../../narrative/STORY_CHAPTERS.md) - Chapter 2 narrative reference

### Tools

- **E2E Testing**: Playwright + TypeScript
- **Backend Testing**: pytest + Python
- **Performance Monitoring**: Custom latency logging
- **Observability**: Custom React dashboard

### Glossary

- **Intent**: Classified category of user query (cooking, household, smart_home, general, multi_task)
- **Character Plan**: Execution plan mapping tasks to characters
- **Handoff**: Dialogue transition from one character to another
- **Story Beat**: Narrative moment delivered during interaction
- **Beat Variant**: Length version of story beat (short, medium, long)
- **Sequential Execution**: Characters respond one after another (not simultaneously)

---

**Document Owner:** Justin
**Last Updated:** February 11, 2026
**Next Update:** After Milestone 1 completion

---

