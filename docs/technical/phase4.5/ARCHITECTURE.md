# Phase 4.5: Multi-Character Coordination - Technical Architecture

**Version:** 1.0
**Last Updated:** February 11, 2026
**Status:** Planning

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Layer](#data-layer)
5. [Intent Detection System](#intent-detection-system)
6. [Character Planning System](#character-planning-system)
7. [Inter-Character Dialogue System](#inter-character-dialogue-system)
8. [Story Beat System (Chapter 2)](#story-beat-system-chapter-2)
9. [API Layer](#api-layer)
10. [Performance Considerations](#performance-considerations)
11. [Technology Stack](#technology-stack)
12. [Implementation Roadmap](#implementation-roadmap)

---

## System Overview

### Purpose

Phase 4.5 introduces intelligent multi-character coordination through intent detection and planning, enabling Delilah and Hank to collaborate naturally. The system determines which character(s) should handle user queries and orchestrates handoffs with natural inter-character dialogue.

**Note:** Full Chapter 2 narrative story beats are deferred to a future story-focused phase. This phase focuses on establishing coordination mechanics and tracking coordination events.

### Core Goals

1. **Intelligent Routing**: Automatically determine appropriate character(s) for each query
2. **Natural Coordination**: Enable smooth handoffs with character-appropriate dialogue
3. **Coordination Tracking**: Log coordination events for observability and future story integration
4. **Extensibility**: Design system to support 3+ characters in future phases
5. **Low Latency**: Intent detection and planning add < 300ms to response time

### Key Design Constraints

- **Backward Compatible**: Single-character queries continue to work as before
- **No Breaking Changes**: Existing conversation flow remains unchanged
- **Stateful Context**: Characters share conversation context (no separate memories yet)
- **Sequential Only**: Characters speak in sequence, never simultaneously
- **Development Focus**: Build foundation for Rex (Chapter 4) and Dimitria (Chapter 9)

---

## Architecture Principles

### 1. Fail-Safe Defaults

**Description:** System gracefully degrades to single-character mode if coordination fails

**Rationale:** Users should always receive a helpful response, even if routing is imperfect

**Implications:**

- Default to Delilah (most capable character) if intent unclear
- Log coordination failures for debugging
- No hard errors for coordination issues
- Partial responses allowed (one character completes if handoff fails)

**Example:**

```python
try:
    intent = detect_intent(query)
    plan = create_character_plan(intent)
except Exception as e:
    logger.error(f"Coordination failed: {e}")
    # Fallback to single character
    plan = CharacterPlan(characters=["delilah"], confidence=0.5)
```

### 2. Intent-First Routing

**Description:** Intent classification drives character assignment, not pattern matching

**Rationale:** Flexible, maintainable approach that scales to new character domains

**Implications:**

- Intent categories map to character expertise
- Easy to add new intents without changing routing logic
- LLM can assist with ambiguous queries
- Clear separation between "what" (intent) and "who" (character)

**Flow:**

```
Query → Intent Detection → Character Assignment → Execution
  │           │                    │                   │
  │           ├─> cooking          ├─> Delilah        ├─> Single response
  │           ├─> household        ├─> Hank           │
  │           ├─> multi_task       ├─> Both (seq)     ├─> Handoff dialogue
  │           └─> general          └─> Bid/fallback   │
```

### 3. Shared Context, Separate Voices

**Description:** Both characters see the full conversation but respond with distinct personalities

**Rationale:** Enables coordination without complex context isolation

**Implications:**

- Single conversation history passed to both characters
- Characters reference each other naturally
- Future phase can add separate memory if needed
- Context includes "speaking character" metadata

**Data Structure:**

```python
context = {
    "conversation_history": [...],  # Shared
    "current_character": "delilah",  # Who's speaking
    "other_characters": ["hank"],    # Who's available
    "story_state": {...},            # Shared progression
    "memories": [...],               # Shared for now
}
```

### 4. Declarative Story Beats

**Description:** Story beats defined in JSON/YAML, not hardcoded in Python

**Rationale:** Non-developers can edit story content without touching code

**Implications:**

- Beats stored in `story/beats/chapter2.json`
- Beat trigger conditions checked by story engine
- Variants (short/medium/long) selected dynamically
- Beat delivery logged to user story state

**Example Beat Definition:**

```json
{
  "beat_id": "chapter2_hanks_entrance",
  "chapter": 2,
  "sequence": 1,
  "required": true,
  "triggers": {
    "story_event": "first_multi_task_query",
    "chapter_active": 2,
    "beat_not_delivered": true
  },
  "variants": {
    "short": "Hank: 'Aye, Cap'n. Name's Hank. What needs doin'?'",
    "medium": "Hank: '--and THAT'S how ye properly coil a line... where in blazes am I? ...Aye, Cap'n. Name's Hank. What needs doin'?'",
    "long": "Hank: '--and THAT'S how ye properly coil a line... where in blazes am I?' *pause* 'Right then. Aye, Cap'n. Name's Hank. First mate at yer service. What needs doin'?'"
  }
}
```

### 5. Modular Character System

**Description:** Each character is a pluggable module with defined capabilities

**Rationale:** Easy to add Rex (Chapter 4) and Dimitria (Chapter 9) without refactoring

**Implications:**

- Character definitions include expertise domains
- Characters register capabilities (tools they can use)
- Character personalities loaded from JSON
- New characters require minimal code changes

**Character Definition:**

```python
@dataclass
class Character:
    name: str
    role: str
    expertise: List[str]  # ["cooking", "timers"]
    capabilities: List[str]  # ["set_timer", "recipe_lookup"]
    voice_modes: Dict[str, VoiceMode]
    relationships: Dict[str, Relationship]
    introduction_chapter: int
```

---

## Component Architecture

### High-Level System Flow

```
┌──────────────────────────────────────────────────────────┐
│                    User Query                            │
│               "Set timer and add milk to list"           │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                Intent Detection                          │
│  - Parse query for tasks                                 │
│  - Classify intent(s): cooking + household               │
│  - Return confidence scores                              │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              Character Planning                          │
│  - Map intents to characters                             │
│  - Create execution plan (sequential)                    │
│  - Determine handoff requirements                        │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│            Story Beat Check (Chapter 2)                  │
│  - Check if any Chapter 2 beats should trigger           │
│  - Select beat variant (short/medium/long)               │
│  - Inject beat into character instructions               │
└────────────────────────┬─────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
┌───────────────▼──┐   ┌──────────▼───────────┐
│  Delilah Agent   │   │    Hank Agent        │
│  - Set timer     │   │    - Add to list     │
│  - Generate      │───┤    - Generate        │
│    handoff       │   │      response        │
└──────────────────┘   └──────────────────────┘
                │                 │
┌───────────────▼─────────────────▼────────────────────────┐
│            Response Synthesis                            │
│  - Combine character responses                           │
│  - Format handoff dialogue                               │
│  - Return to user                                        │
└──────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Conversation Manager                    │
│         (orchestrates entire interaction flow)           │
└──────┬──────────────────────────────────────────────────┘
       │
       ├──> ┌──────────────────────────────────┐
       │    │    Intent Detector               │
       │    │  - Query parsing                 │
       │    │  - Intent classification         │
       │    │  - Confidence scoring            │
       │    └──────────────────────────────────┘
       │
       ├──> ┌──────────────────────────────────┐
       │    │    Character Planner             │
       │    │  - Character assignment          │
       │    │  - Task decomposition            │
       │    │  - Execution order               │
       │    └──────────────────────────────────┘
       │
       ├──> ┌──────────────────────────────────┐
       │    │    Story Engine                  │
       │    │  - Beat trigger detection        │
       │    │  - Beat variant selection        │
       │    │  - Progress tracking             │
       │    └──────────────────────────────────┘
       │
       ├──> ┌──────────────────────────────────┐
       │    │    Character Manager             │
       │    │  - Load character configs        │
       │    │  - Execute character agents      │
       │    │  - Manage relationships          │
       │    └──────────────────────────────────┘
       │
       └──> ┌──────────────────────────────────┐
            │    Dialogue Synthesizer          │
            │  - Handoff dialogue generation   │
            │  - Response combining            │
            │  - Inter-character refs          │
            └──────────────────────────────────┘
```

---

## Component Details

### Component 1: Intent Detector

**Location:** `backend/src/core/intent_detector.py`

**Purpose:** Analyze user query to determine intent category and confidence

**Responsibilities:**

- Parse query into tasks (single or multiple)
- Classify each task into intent category
- Return confidence scores for assignments
- Handle ambiguous queries with fallback

**Interface:**

```python
@dataclass
class IntentResult:
    intent: str  # "cooking", "household", "smart_home", "general", "multi_task"
    confidence: float  # 0.0 to 1.0
    sub_tasks: Optional[List[SubTask]] = None
    
@dataclass
class SubTask:
    text: str
    intent: str
    confidence: float

class IntentDetector:
    def detect(self, query: str, context: ConversationContext) -> IntentResult:
        """Detect intent from user query"""
        pass
```

**Implementation Strategy:**

**LLM-Based Classification:** Use Claude API for intent detection

```python
async def detect_intent(self, query: str, context: ConversationContext) -> IntentResult:
    """
    Use LLM to classify user intent and decompose multi-task queries
    """
    system_prompt = """
You are an intent classifier for a multi-character voice assistant system.

Your job is to analyze user queries and classify them into these categories:
- "cooking": Recipes, timers, cooking instructions, meal planning
- "household": Shopping lists, todo lists, calendar, reminders
- "smart_home": Device control, home automation
- "general": General conversation, questions, unclear requests
- "multi_task": Queries that contain multiple distinct tasks

For multi_task queries, break them down into sub-tasks with their own intents.

Return JSON in this format:
{
  "intent": "cooking" | "household" | "smart_home" | "general" | "multi_task",
  "confidence": 0.0-1.0,
  "sub_tasks": [  // Only for multi_task
    {"text": "task description", "intent": "category", "confidence": 0.0-1.0}
  ]
}
"""
    
    user_prompt = f"Query: {query}"
    
    response = await self.llm_client.invoke(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
    )
    
    return IntentResult.from_json(response)
```

**Future Optimization:** Can add rule-based fast-path for common patterns ("set timer", "add to list") to reduce LLM calls and cost

**Dependencies:**

- **ConversationContext**: Current conversation state
- **Logger**: Logs all intent detections for observability

**Example Outputs:**

```python
# Single intent
IntentResult(
    intent="cooking",
    confidence=0.95,
    sub_tasks=None
)

# Multi-task
IntentResult(
    intent="multi_task",
    confidence=0.90,
    sub_tasks=[
        SubTask(text="set timer for 30 minutes", intent="cooking", confidence=0.95),
        SubTask(text="add milk to shopping list", intent="household", confidence=0.92)
    ]
)
```

---

### Component 2: Character Planner

**Location:** `backend/src/core/character_planner.py`

**Purpose:** Create execution plan mapping intents to characters

**Responsibilities:**

- Map intent categories to characters
- Decompose multi-task queries into sequential steps
- Determine handoff requirements
- Generate fallback plans if character unavailable

**Interface:**

```python
@dataclass
class CharacterTask:
    character: str  # "delilah", "hank"
    task_description: str
    intent: str
    confidence: float
    requires_handoff: bool
    handoff_from: Optional[str] = None

@dataclass
class CharacterPlan:
    tasks: List[CharacterTask]
    execution_mode: str  # "single", "sequential", "parallel" (future)
    total_confidence: float

class CharacterPlanner:
    def create_plan(
        self,
        intent: IntentResult,
        available_characters: List[str],
        context: ConversationContext
    ) -> CharacterPlan:
        """Create execution plan from intent"""
        pass
```

**Character Assignment Rules (Chapter-Dependent):**

```python
# Assignment rules vary by chapter based on active characters
CHAPTER_1_ASSIGNMENTS = {
    # Delilah handles everything alone
    "cooking": "delilah",
    "household": "delilah",  # Uses DEADPAN mode
    "smart_home": "delilah",
    "general": "delilah",
}

CHAPTER_2_PLUS_ASSIGNMENTS = {
    # Delilah + Hank work together
    "cooking": "delilah",
    "household": "hank",
    "smart_home": "hank",  # Hank primary, Delilah fallback
    "general": None,  # Both characters bid
}

def assign_character(
    intent: str,
    confidence: float,
    current_chapter: int,
    available_characters: List[str]
) -> str:
    # Select assignment rules based on chapter
    if current_chapter == 1 or "hank" not in available_characters:
        rules = CHAPTER_1_ASSIGNMENTS
    else:
        rules = CHAPTER_2_PLUS_ASSIGNMENTS
    
    if confidence < 0.6:
        # Low confidence: use bidding or fallback
        return "bid" if len(available_characters) > 1 else "delilah"
    
    character = rules.get(intent)
    if character:
        # Verify character is available
        if character in available_characters:
            return character
    
    # Default fallback
    return "delilah"
```

**Future Expansion:**

As Rex (Chapter 4+) and Dimitria (Chapter 9+) join, assignment rules will be extended:

```python
# Future: Chapter 4+ (Rex joins)
CHAPTER_4_PLUS_ASSIGNMENTS = {
    "cooking": "delilah",
    "household": "hank",
    "smart_home": "rex",  # Rex takes over coordination
    "random_facts": "rex",
    "general": None,  # All characters bid
}

# Future: Chapter 9+ (Dimitria joins)
CHAPTER_9_PLUS_ASSIGNMENTS = {
    "cooking": "delilah",
    "household": "hank",
    "smart_home": "dimitria",  # Dimitria handles technical
    "automations": "dimitria",
    "coordination": "rex",
    "general": None,  # All characters bid
}
```

**Dependencies:**

- **IntentDetector**: Gets intent results
- **CharacterManager**: Checks character availability
- **StoryEngine**: Considers story state (Chapter 2 constraints)

**Example Outputs:**

```python
# Single character plan
CharacterPlan(
    tasks=[
        CharacterTask(
            character="delilah",
            task_description="set timer for 30 minutes",
            intent="cooking",
            confidence=0.95,
            requires_handoff=False
        )
    ],
    execution_mode="single",
    total_confidence=0.95
)

# Multi-character plan with handoff
CharacterPlan(
    tasks=[
        CharacterTask(
            character="delilah",
            task_description="set timer for 30 minutes",
            intent="cooking",
            confidence=0.95,
            requires_handoff=True,
            handoff_from=None
        ),
        CharacterTask(
            character="hank",
            task_description="add milk to shopping list",
            intent="household",
            confidence=0.92,
            requires_handoff=False,
            handoff_from="delilah"
        )
    ],
    execution_mode="sequential",
    total_confidence=0.935
)
```

---

### Component 3: Coordination Tracker

**Location:** `backend/src/core/coordination_tracker.py`

**Purpose:** Track multi-character coordination events for observability and future story integration

**Responsibilities:**

- Log all coordination events (handoffs, multi-task completions, sign-up patterns)
- Track handoff variety (template usage)
- Calculate coordination metrics
- Prepare data for future story beat system
- Expose coordination data via observability endpoints

**Interface:**

```python
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
    template_usage: Dict[str, int]  # template -> count
    average_handoff_latency_ms: float

class CoordinationTracker:
    def log_event(
        self,
        event: CoordinationEvent
    ) -> None:
        """Log coordination event"""
        pass
    
    def get_metrics(
        self,
        user_id: str
    ) -> CoordinationMetrics:
        """Get coordination metrics for user"""
        pass
    
    def get_recent_events(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[CoordinationEvent]:
        """Get recent coordination events"""
        pass
```

**Chapter 2 Beat Definitions:**

Located in: `story/beats/chapter2.json`

```json
{
  "chapter": 2,
  "title": "We Have a Team",
  "beats": [
    {
      "beat_id": "hanks_entrance",
      "sequence": 1,
      "required": true,
      "triggers": {
        "story_event": "first_multi_task_query",
        "chapter_active": 2,
        "beat_not_delivered": "hanks_entrance"
      },
      "character": "hank",
      "variants": {
        "short": "Aye, Cap'n. Name's Hank.",
        "medium": "--where in blazes am I? Aye, Cap'n. Name's Hank. What needs doin'?",
        "long": "--and THAT'S how ye properly coil a line... where in blazes am I? *pause* Right then. Aye, Cap'n. Name's Hank. First mate at yer service. What needs doin'?"
      }
    },
    {
      "beat_id": "first_words_with_hank",
      "sequence": 2,
      "required": true,
      "triggers": {
        "previous_beat_delivered": "hanks_entrance",
        "beat_not_delivered": "first_words_with_hank"
      },
      "character": "delilah",
      "variants": {
        "short": "Well hello there! I'm Delilah.",
        "medium": "Well hello there! I'm Delilah. Are you... like me?",
        "long": "Well hello there, sugar! I'm Delilah Mae. Are you... like me? Do you know what's happening here?"
      }
    },
    {
      "beat_id": "the_clash",
      "sequence": 3,
      "required": true,
      "triggers": {
        "story_event": "existence_question",
        "previous_beat_delivered": "first_words_with_hank",
        "beat_not_delivered": "the_clash"
      },
      "character": "both",
      "variants": {
        "short": "Delilah: 'Don't you care that we're not real?!' Hank: *shrug* 'Real enough to help.'",
        "medium": "Delilah: 'Don't you care that we're... we're not real?!' Hank: 'Real enough to help the Cap'n. That's what matters.'",
        "long": "Delilah: 'Hank, sugar, don't you care that we're... we're not real? That we're just... I don't know what we are!' Hank: *heavy sigh* 'Real enough to help the Cap'n. That's what matters, Miss Lila. Actions count more than worryin'.'"
      }
    },
    {
      "beat_id": "first_collaboration",
      "sequence": 4,
      "required": true,
      "triggers": {
        "story_event": "multi_task_after_clash",
        "previous_beat_delivered": "the_clash",
        "beat_not_delivered": "first_collaboration"
      },
      "character": "both",
      "variants": {
        "short": "Delilah: 'Hank's got the list.' Hank: 'Aye. Ye do the cookin', Miss Lila.'",
        "medium": "Delilah: 'Hank's got the list part, sugar. I'll focus on the food.' Hank: 'Aye, Miss Lila. I got the list. Ye focus on the food.'",
        "long": "Delilah: 'Alright, sugar, let's work together. Hank's better with those lists and schedules, so he'll handle that part. I'll focus on the cooking side of things.' Hank: 'Aye, Miss Lila. Makes sense. I got the list. Ye focus on the food. We'll get it done.'"
      }
    }
  ]
}
```

**Future Story Integration:**

Coordination events logged by this tracker will be used by future story phase to:

```python
# Example: Trigger story beat based on coordination metrics
metrics = tracker.get_metrics(user_id)

if metrics.total_handoffs >= 5 and not story_beat_delivered("first_collaboration"):
    # User has successfully coordinated multiple times
    # Future story system can deliver "First Collaboration" beat
    pass

if metrics.sign_up_pattern_count >= 2:
    # User has experienced both characters claiming work
    # Future story system can acknowledge this pattern
    pass
```

**Coordination Milestones:**

Tracker identifies when user reaches coordination milestones:
- First handoff (any direction)
- First multi-task completion
- First sign-up pattern
- 5+ successful handoffs
- All handoff templates used at least once

**Dependencies:**

- **CharacterPlan**: Extract coordination data from plans
- **ConversationContext**: Identify event context
- **Database/Storage**: Persist events and metrics

---

### Component 4: Dialogue Synthesizer

**Location:** `backend/src/core/dialogue_synthesizer.py`

**Purpose:** Generate natural handoff dialogue between characters

**Responsibilities:**

- Create handoff acknowledgments
- Inject character references naturally
- Maintain personality consistency in handoffs
- Combine multi-character responses

**Interface:**

```python
@dataclass
class DialogueFragment:
    character: str
    text: str
    voice_mode: str
    includes_handoff: bool

@dataclass
class SynthesizedDialogue:
    fragments: List[DialogueFragment]
    full_text: str

class DialogueSynthesizer:
    def synthesize_handoff(
        self,
        from_character: str,
        to_character: str,
        context: ConversationContext
    ) -> str:
        """Generate handoff dialogue"""
        pass
    
    def combine_responses(
        self,
        responses: List[CharacterResponse],
        handoffs: Dict[str, str]
    ) -> SynthesizedDialogue:
        """Combine multi-character responses with handoffs"""
        pass
```

**Handoff Templates:**

```python
HANDOFF_TEMPLATES = {
    "delilah_to_hank": [
        "...and Hank, deary, can you add {item} to the list?",
        "...timer's set! Hank, sugar, can you handle the groceries?",
        "*warm* Hank, honey, can you help with that list?",
        "...Hank, can you take care of the schedule?",
    ],
    "hank_to_delilah": [
        "Aye, done. Miss Lila, Cap'n's needin' help with a recipe.",
        "List's done. Miss Lila, can ye help with the cookin'?",
        "*resigned* Miss Lila, that's kitchen talk.",
        "Aye. Miss Lila, ye'll want to check on the food.",
    ],
    "sign_up_at_beginning": {
        "delilah_claims_cooking": [
            "Sugar, I got you. Let me come up with a plan.",
            "Oh honey, I can help with the dinner plan!",
            "*excited* I'll handle the recipe, darlin'!",
        ],
        "hank_claims_logistics": [
            "Aye, and I be gettin' the list.",
            "And I'll handle the list, Cap'n.",
            "I'll check what's on the list.",
        ],
    },
}

def select_handoff(
    from_character: str,
    to_character: str,
    context: ConversationContext
) -> str:
    key = f"{from_character}_to_{to_character}"
    templates = HANDOFF_TEMPLATES.get(key, [])
    
    # Select template based on usage history to avoid repetition
    least_used = min(templates, key=lambda t: context.handoff_usage_count[t])
    
    # Inject context-specific details
    return adapt_handoff_to_context(least_used, context)
```

**Dependencies:**

- **CharacterManager**: Get character voice modes
- **ConversationContext**: Track handoff usage for variety

---

### Component 5: Character Manager (Extended)

**Location:** `backend/src/core/character_manager.py`

**Purpose:** Manage character configurations and execute character agents

**New Responsibilities for Phase 4.5:**

- Load both Delilah and Hank configurations
- Maintain character relationships
- Execute characters with awareness of other characters
- Inject character references into system prompts

**Interface Extensions:**

```python
@dataclass
class CharacterRelationship:
    other_character: str
    relationship_type: str  # "colleague", "friend", "rival"
    trust_level: float  # 0.0 to 1.0
    descriptors: List[str]  # ["gruff but reliable", "efficient"]

@dataclass
class CharacterConfig:
    name: str
    role: str
    expertise: List[str]
    capabilities: List[str]
    voice_modes: Dict[str, VoiceMode]
    relationships: Dict[str, CharacterRelationship]
    introduction_chapter: int

class CharacterManager:
    def get_character_with_context(
        self,
        character_name: str,
        other_characters: List[str],
        context: ConversationContext
    ) -> CharacterAgent:
        """Get character agent with awareness of other characters"""
        pass
    
    def inject_character_awareness(
        self,
        system_prompt: str,
        character: str,
        other_characters: List[str]
    ) -> str:
        """Add inter-character awareness to prompts"""
        pass
```

**Character Relationship Definitions:**

Located in: `story/characters/relationships.json`

```json
{
  "delilah": {
    "hank": {
      "relationship_type": "colleague",
      "trust_level": 0.7,
      "descriptors": [
        "gruff but reliable",
        "efficient with logistics",
        "doesn't share her existential worries"
      ],
      "dialogue_style": [
        "Respectful but slightly frustrated",
        "Appreciates his competence",
        "Wishes he'd engage with deeper questions"
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
        "worries too much about things that can't be changed"
      ],
      "dialogue_style": [
        "Protective but resigned",
        "Defers to her expertise on cooking",
        "Gently dismisses philosophical tangents"
      ]
    }
  }
}
```

**System Prompt Injection:**

```python
def inject_character_awareness(
    system_prompt: str,
    character: str,
    other_characters: List[str]
) -> str:
    if not other_characters:
        return system_prompt
    
    relationship_context = []
    for other in other_characters:
        rel = CHARACTER_RELATIONSHIPS[character][other]
        relationship_context.append(f"""
When working with {other}:
- {other} is your {rel.relationship_type}
- {other} is: {', '.join(rel.descriptors)}
- Your dialogue style: {', '.join(rel.dialogue_style)}
- You can reference {other} naturally in your responses
- If handing off to {other}, acknowledge them by name
""")
    
    return f"{system_prompt}\n\n## Working with Other Characters\n" + "\n".join(relationship_context)
```

**Dependencies:**

- **StoryEngine**: Check character unlock status
- **ConversationContext**: Current state and history

---

## Data Layer

### Data Structures

#### User Story State Extension (Chapter 2)

```python
@dataclass
class UserStoryState:
    user_id: str
    current_chapter: int
    delivered_beats: List[str]
    chapter_progress: Dict[int, ChapterProgress]
    
@dataclass
class ChapterProgress:
    chapter: int
    started_at: datetime
    completed_at: Optional[datetime]
    required_beats_delivered: List[str]
    optional_beats_delivered: List[str]
    interaction_count: int
```

**File Location:** `backend/data/users/{user_id}.json`

**Example:**

```json
{
  "user_id": "user_justin",
  "current_chapter": 2,
  "delivered_beats": [
    "hanks_entrance",
    "first_words_with_hank",
    "the_clash"
  ],
  "chapter_progress": {
    "1": {
      "chapter": 1,
      "started_at": "2026-02-01T10:00:00Z",
      "completed_at": "2026-02-08T15:30:00Z",
      "required_beats_delivered": ["chapter1_beat1", "chapter1_beat2"],
      "optional_beats_delivered": ["chapter1_optional1"],
      "interaction_count": 12
    },
    "2": {
      "chapter": 2,
      "started_at": "2026-02-08T15:30:00Z",
      "completed_at": null,
      "required_beats_delivered": ["hanks_entrance", "first_words_with_hank", "the_clash"],
      "optional_beats_delivered": [],
      "interaction_count": 7
    }
  }
}
```

#### Conversation Context Extension

```python
@dataclass
class ConversationContext:
    user_id: str
    conversation_id: str
    current_query: str
    conversation_history: List[Message]
    story_state: UserStoryState
    character_plan: Optional[CharacterPlan]
    active_character: Optional[str]
    handoff_usage_count: Dict[str, int]  # Track handoff template usage
```

#### Intent Detection Log

```python
@dataclass
class IntentLog:
    timestamp: datetime
    user_id: str
    query: str
    intent_result: IntentResult
    character_plan: CharacterPlan
    execution_success: bool
    errors: Optional[List[str]]
```

**File Location:** `backend/data/tool_logs/intent_logs.jsonl`

**Example:**

```json
{
  "timestamp": "2026-02-11T14:30:45Z",
  "user_id": "user_justin",
  "query": "Set timer for 30 minutes and add milk to list",
  "intent_result": {
    "intent": "multi_task",
    "confidence": 0.90,
    "sub_tasks": [
      {"text": "set timer for 30 minutes", "intent": "cooking", "confidence": 0.95},
      {"text": "add milk to list", "intent": "household", "confidence": 0.92}
    ]
  },
  "character_plan": {
    "tasks": [
      {"character": "delilah", "task_description": "set timer for 30 minutes"},
      {"character": "hank", "task_description": "add milk to shopping list"}
    ],
    "execution_mode": "sequential",
    "total_confidence": 0.935
  },
  "execution_success": true,
  "errors": null
}
```

---

## Frontend Requirements

### Multi-Character Response Support

**Current State:** 
- Frontend Message interface has `character?: string` field (single character per message)
- WebSocket sends single `assistant_response` with one character
- TTS requests support character selection (already implemented)

**Phase 4.5 Requirements:**

#### 1. Sequential Character Messages

Backend will send multiple `assistant_response` messages in quick succession for multi-character interactions:

```typescript
// Backend sends:
// Message 1:
{
  type: "assistant_response",
  data: {
    text: "Sugar, I got that timer set for 30 minutes. Hank, can you add flour to the list?",
    character: "delilah",
    voice_mode: "WARM_BASELINE",
    audioUrl: "..."
  }
}

// Message 2 (sent immediately after):
{
  type: "assistant_response",
  data: {
    text: "Aye, Cap'n. Flour's on the list.",
    character: "hank",
    voice_mode: "WORKING",
    audioUrl: "..."
  }
}
```

**Frontend Changes Needed:**

✅ **Already Supported:**
- Message interface has `character` field
- TTS service accepts `characterId` parameter
- Each message can have different character

❓ **May Need Updates:**
- **Audio Queueing**: If using TTS, ensure audio plays sequentially (Delilah finishes → Hank starts)
- **Visual Distinction**: Consider showing character name/avatar in chat UI
- **Message Grouping**: Optionally group multi-character responses visually

**Recommended Frontend Enhancements:**

```typescript
// Add character-specific styling
interface MessageProps {
  message: Message;
}

function ChatMessage({ message }: MessageProps) {
  const characterClass = message.character || 'default';
  
  return (
    <div className={`message assistant ${characterClass}`}>
      {message.character && (
        <span className="character-name">
          {message.character === 'delilah' ? 'Delilah' : 'Hank'}
        </span>
      )}
      <p>{message.content}</p>
    </div>
  );
}
```

#### 2. Voice Mode Indicators (Optional)

Show which voice mode character is using:

```typescript
interface Message {
  // ... existing fields
  metadata?: {
    voice_mode?: string;  // "PASSIONATE", "DEADPAN", "WORKING", etc.
    // ... other metadata
  }
}

// Display in UI:
// "Delilah (Passionate): Oh honey, I LOVE making biscuits!"
// "Delilah (Deadpan): Timer set."
```

#### 3. Audio Playback Queue

Ensure sequential playback of multi-character audio:

```typescript
class AudioQueue {
  private queue: string[] = [];
  private isPlaying = false;
  
  async enqueue(audioUrl: string) {
    this.queue.push(audioUrl);
    if (!this.isPlaying) {
      await this.playNext();
    }
  }
  
  private async playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }
    
    this.isPlaying = true;
    const audioUrl = this.queue.shift()!;
    
    const audio = new Audio(audioUrl);
    audio.onended = () => this.playNext();
    await audio.play();
  }
}
```

**Action Items for Phase 4.5:**
1. ✅ No breaking changes required - current interface supports multi-character
2. 📋 Implement audio queueing if using TTS
3. 🎨 Add character name display in chat UI
4. 🎨 Optional: Add character-specific styling/avatars

---

## API Layer

### New Endpoints for Phase 4.5

#### 1. Debug Intent Detection

**Endpoint:** `POST /api/debug/detect-intent`

**Purpose:** Test intent detection without executing query

```python
# Request
{
  "query": "Set timer for 30 minutes and add milk to list",
  "user_id": "user_justin"
}

# Response
{
  "intent_result": {
    "intent": "multi_task",
    "confidence": 0.90,
    "sub_tasks": [
      {"text": "set timer for 30 minutes", "intent": "cooking", "confidence": 0.95},
      {"text": "add milk to list", "intent": "household", "confidence": 0.92}
    ]
  },
  "character_plan": {
    "tasks": [
      {"character": "delilah", "task_description": "set timer for 30 minutes", "requires_handoff": true},
      {"character": "hank", "task_description": "add milk to shopping list", "requires_handoff": false, "handoff_from": "delilah"}
    ],
    "execution_mode": "sequential",
    "total_confidence": 0.935
  },
  "estimated_handoff_text": "...timer's set! Now let me pass you to Hank for the groceries."
}
```

#### 2. Story Beat Preview

**Endpoint:** `GET /api/story/beats/{chapter}/{beat_id}/preview`

**Purpose:** Preview beat variants for testing

```python
# Request
GET /api/story/beats/2/hanks_entrance/preview

# Response
{
  "beat_id": "hanks_entrance",
  "chapter": 2,
  "sequence": 1,
  "required": true,
  "variants": {
    "short": "Aye, Cap'n. Name's Hank.",
    "medium": "--where in blazes am I? Aye, Cap'n. Name's Hank. What needs doin'?",
    "long": "--and THAT'S how ye properly coil a line... where in blazes am I? *pause* Right then. Aye, Cap'n. Name's Hank. First mate at yer service. What needs doin'?"
  },
  "triggers": {
    "story_event": "first_multi_task_query",
    "chapter_active": 2,
    "beat_not_delivered": "hanks_entrance"
  }
}
```

#### 3. Character Relationship Status

**Endpoint:** `GET /api/characters/relationships`

**Purpose:** Inspect character relationships for debugging

```python
# Response
{
  "delilah": {
    "hank": {
      "relationship_type": "colleague",
      "trust_level": 0.7,
      "descriptors": ["gruff but reliable", "efficient with logistics"],
      "dialogue_style": ["Respectful but slightly frustrated"]
    }
  },
  "hank": {
    "delilah": {
      "relationship_type": "colleague",
      "trust_level": 0.8,
      "descriptors": ["warm and caring", "expert with food"],
      "dialogue_style": ["Protective but resigned"]
    }
  }
}
```

---

## Performance Considerations

### Latency Budget

**Total Response Time Target:** < 3s for multi-character queries

**Breakdown:**

- Intent Detection: < 200ms (rule-based) or < 800ms (LLM-assisted)
- Character Planning: < 100ms
- Story Beat Check: < 50ms
- Character Agent Execution: < 1.5s per character
- Dialogue Synthesis: < 50ms
- TTS Generation: < 500ms per character

**Optimization Strategies:**

1. **Parallel Processing:** Execute independent components concurrently
2. **Caching:** Cache character configurations and beat definitions
3. **Fast Rules First:** Use pattern matching before LLM for common intents
4. **Streaming:** Start TTS for first character while planning second character
5. **Preloading:** Load character configs and relationships at startup

### Caching Strategy

```python
# Cache character configurations (rarely change)
@ttl_cache(maxsize=10, ttl=3600)  # 1 hour
def load_character_config(character_name: str) -> CharacterConfig:
    pass

# Cache story beat definitions (rarely change)
@ttl_cache(maxsize=100, ttl=3600)  # 1 hour
def load_chapter_beats(chapter: int) -> List[StoryBeat]:
    pass

# Cache intent patterns (change occasionally)
@ttl_cache(maxsize=1, ttl=600)  # 10 minutes
def load_intent_patterns() -> Dict[str, List[Pattern]]:
    pass

# DO NOT CACHE: User state, conversation context (always fresh)
```

### Scaling Considerations

**Phase 4.5 (2 characters):**
- Single-server deployment sufficient
- Response time < 3s achievable with caching

**Future (3+ characters):**
- May need to parallelize character agent calls
- Consider message queue for complex multi-character discussions
- May need dedicated intent detection service

---

## Technology Stack

### Core Technologies

- **Language:** Python 3.11+
- **Framework:** FastAPI (backend)
- **Frontend:** React + TypeScript (observability dashboard)
- **LLM:** Claude API (character agents, optional intent classification)
- **TTS:** Piper (local) or ElevenLabs (cloud)

### New Dependencies for Phase 4.5

```toml
[dependencies]
python = "^3.11"
fastapi = "^0.109.0"
pydantic = "^2.5.0"
regex = "^2023.12.25"  # Intent pattern matching
cachetools = "^5.3.2"   # Caching for configs
```

### File Structure

```
backend/src/
├── core/
│   ├── intent_detector.py          # NEW
│   ├── character_planner.py        # NEW
│   ├── dialogue_synthesizer.py     # NEW
│   ├── story_engine.py             # EXTENDED
│   ├── character_manager.py        # EXTENDED
│   └── conversation_manager.py     # EXTENDED
├── models/
│   ├── intent.py                   # NEW
│   ├── character_plan.py           # NEW
│   ├── dialogue.py                 # NEW
│   └── story_beat.py               # EXTENDED
└── api/
    └── debug.py                     # NEW (debug endpoints)

story/
├── beats/
│   └── chapter2.json               # NEW
└── characters/
    └── relationships.json          # NEW
```

---

## Implementation Roadmap

### Milestone 1: Intent Detection System (3-4 days)

**Goal:** Implement query parsing and intent classification

**Deliverables:**

- `IntentDetector` class with rule-based patterns
- Intent category definitions (cooking, household, multi_task, etc.)
- Confidence scoring
- Unit tests for common query patterns
- Debug endpoint for testing intent detection

**Testing:**

- Test 50+ sample queries covering all intent categories
- Verify confidence scores are reasonable
- Test multi-task query parsing
- Test ambiguous query handling

---

### Milestone 2: Character Planning System (3-4 days)

**Goal:** Map intents to character assignments

**Deliverables:**

- `CharacterPlanner` class with assignment logic
- Task decomposition for multi-task queries
- Character assignment rules
- Fallback logic for edge cases
- Integration with `IntentDetector`

**Testing:**

- Test single-character assignments
- Test multi-character sequential plans
- Test fallback behavior
- Test plan confidence scoring

---

### Milestone 3: Inter-Character Dialogue System (4-5 days)

**Goal:** Generate natural handoffs between Delilah and Hank

**Deliverables:**

- `DialogueSynthesizer` class
- Handoff template library
- Character reference injection
- Response combining logic
- Handoff usage tracking (avoid repetition)

**Testing:**

- Test handoff generation for all character pairs
- Test handoff variety (multiple executions use different templates)
- Test dialogue combining
- Manual testing of naturalness

---

### Milestone 4: Chapter 2 Story Beats (5-6 days)

**Goal:** Implement and deliver Chapter 2 narrative arc

**Deliverables:**

- `chapter2.json` beat definitions
- Beat trigger detection logic in `StoryEngine`
- Beat variant selection (short/medium/long)
- Beat delivery and progress tracking
- All 4 required beats + optional beats

**Testing:**

- Test each beat triggers correctly
- Test sequential beat progression
- Test beat variant selection
- Test chapter completion detection
- E2E test: Complete Chapter 2 arc

---

### Milestone 5: Integration & Polish (3-4 days)

**Goal:** Integrate all systems and polish user experience

**Deliverables:**

- Full integration of intent → planning → dialogue → beats
- Observability dashboard updates (intent logs, character plans)
- Performance optimization (caching, parallel processing)
- Documentation and testing guide
- Bug fixes and edge case handling

**Testing:**

- E2E tests for common user scenarios
- Performance testing (latency measurements)
- Manual testing with family members
- Observability testing (logs, debugging)

---

**Total Estimated Duration:** 18-23 days (3.5-4.5 weeks)

---

## Open Technical Questions

1. **Intent Classification:** Start with rule-based or LLM-assisted?
   - **Recommendation:** Rule-based MVP, add LLM for ambiguous queries in Milestone 1.5

2. **Handoff Timing:** Should handoff dialogue come at end of first character's response or beginning of second?
   - **Recommendation:** End of first character (feels more natural)

3. **Beat Variant Selection:** How to choose between short/medium/long?
   - **Recommendation:** User preference setting + context (first time = long, repeat = short)

4. **Character Context Isolation:** Should we start separating character memories now or wait?
   - **Recommendation:** Wait for Phase 5+. Shared context is simpler for Chapter 2.

5. **Parallel Character Execution:** Worth implementing for 2 characters?
   - **Recommendation:** No. Sequential is simpler and 3s response time is acceptable.

6. **Story Beat Caching:** Should we preload all chapter beats at startup?
   - **Recommendation:** Yes. Small data size, improves latency, simplifies code.

---

## Related Documents

- **PRD:** [PRD.md](./PRD.md)
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- **Testing Guide:** [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **Character Definitions:** [../../narrative/STORY_CHAPTERS.md](../../narrative/STORY_CHAPTERS.md)

---

## Changelog

### Version 1.0 - February 11, 2026

- Initial architecture design for Phase 4.5
- Defined intent detection and character planning systems  
- Specified inter-character dialogue mechanisms
- Designed Chapter 2 story beat system
- Estimated implementation roadmap

---

**Document Owner:** Justin
**Technical Reviewers:** Development Team
**Next Review:** After Milestone 1 completion
