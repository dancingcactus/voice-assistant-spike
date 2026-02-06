# Phase 4: Story System Testing & Refinement - Technical Architecture

**Version:** 1.0
**Last Updated:** 2026-02-04
**Status:** Planning

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Layer](#data-layer)
5. [API Layer](#api-layer)
6. [Integration Points](#integration-points)
7. [Frontend Architecture](#frontend-architecture)
8. [Performance Considerations](#performance-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Roadmap](#implementation-roadmap)

---

## System Overview

### Purpose

Phase 4 focuses on making the story system production-ready by fixing beat delivery issues, enhancing story engine capabilities with auto-advance and conditional progression, and expanding content through Chapter 1 and 2. This phase transforms the story system from proof-of-concept to reliable narrative engine.

### Core Goals

1. **Reliability** - Story beats trigger consistently and predictably
2. **Observability** - Real-time UI updates show accurate story state
3. **Testability** - Fast iteration cycles for story development (< 5 min)
4. **Extensibility** - Story engine supports complex narrative patterns

### Key Design Constraints

- **No Breaking Changes** - Work within existing story engine architecture
- **Backward Compatible** - Existing Chapter 1 beats continue to work
- **File-Based Storage** - JSON files remain the source of truth
- **Development Focus** - Tools optimized for rapid iteration, not production scale

---

## Architecture Principles

### 1. Separation of Concerns

The story system maintains clear boundaries between components:

```
┌─────────────────────────────────────────────────────────┐
│              Story Content (JSON)                        │
│  (Declarative beat definitions, chapter structures)      │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              Story Engine (Python)                       │
│  (Beat evaluation, trigger logic, progression rules)     │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              User Story State (JSON)                     │
│  (Per-user progress, beat completion, chapter state)     │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│         Story Beat Tool (React + API)                    │
│  (Observability, manual triggers, testing tools)         │
└─────────────────────────────────────────────────────────┘
```

**Rationale:** Content authors shouldn't need to understand Python code. Story definitions remain declarative and testable independently.

**Implications:**

- Story beats defined in JSON with clear schema
- Engine validates beat definitions at startup
- User state isolated from beat definitions
- Tools can modify state without touching content

### 2. Real-Time State Synchronization

UI reflects backend state within 2 seconds of any change:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Backend    │         │   Frontend   │         │   Browser    │
│   (Python)   │◄────────┤   (React)    │◄────────┤   (User)     │
│              │─────────►│              │─────────►│              │
└──────────────┘         └──────────────┘         └──────────────┘
     State                   Polling                  Display
     Change                  (3-5s) OR
                            WebSocket
```

**Rationale:** Story development requires immediate feedback. Stale UI creates confusion and slows iteration.

**Implications:**

- Frontend polls story state every 3-5 seconds (Phase 4)
- WebSocket events for instant updates (future enhancement)
- Backend state changes persisted immediately
- Race conditions prevented with atomic writes

### 3. Event-Driven Beat Delivery

Story beats are evaluated and queued, then delivered in conversation flow:

```
User Message
     │
     ▼
┌─────────────────────────────────────┐
│  Conversation Handler               │
│  - Process user message             │
│  - Update interaction count         │
│  - Check for beat triggers          │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  Story Engine: Evaluate Triggers    │
│  - Check trigger conditions         │
│  - Evaluate prerequisites           │
│  - Queue eligible beats             │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  Generate Response                  │
│  - Character responds to user       │
│  - Append/replace beat if queued    │
│  - Mark beat as delivered           │
└─────────────────────────────────────┘
     │
     ▼
Response to User
```

**Rationale:** Beats should feel like natural story moments, not interruptions. Delivery happens within the conversation flow.

**Implications:**

- Trigger evaluation separate from delivery
- Beats queued, not immediately injected
- Delivery methods: `append` (add after response) or `replace` (becomes response)
- Failed evaluations logged for debugging

### 4. Stateless Story Definitions

Beat and chapter definitions are immutable; all state lives in user progress:

**Story Definition (Immutable):**

```json
{
  "id": "awakening_confusion",
  "type": "one_shot",
  "required": true,
  "variants": { ... },
  "trigger": { ... }
}
```

**User State (Mutable):**

```json
{
  "user_id": "user_justin",
  "chapter_1": {
    "beats_delivered": ["awakening_confusion"],
    "beat_stages": {},
    "chapter_complete": false
  }
}
```

**Rationale:** Multiple users can progress through the same story independently. State changes don't affect beat definitions.

**Implications:**

- Beat JSON files are read-only at runtime
- All progression tracked in user state
- Easy to reset user by clearing state
- Story content can be updated without migrations

---

## Component Architecture

### High-Level System Diagram

```
                    ┌──────────────────────────────────────┐
                    │   Story Beat Tool (React)            │
                    │  - Beat list & status                │
                    │  - Flow diagram                      │
                    │  - Manual triggers                   │
                    │  - Untrigger operations              │
                    └──────────────┬───────────────────────┘
                                   │ REST API
                    ┌──────────────▼───────────────────────┐
                    │   Story API (FastAPI)                │
                    │  - /story/chapters                   │
                    │  - /story/beats                      │
                    │  - /story/users/{id}/progress        │
                    │  - /story/users/{id}/beats/trigger   │
                    │  - /story/users/{id}/beats/untrigger │
                    │  - /story/auto-advance-ready         │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   Story Engine (Python)              │
                    │  - Beat trigger evaluation           │
                    │  - Conditional progression logic     │
                    │  - Chapter completion checks         │
                    │  - Dependency resolution             │
                    │  - Auto-advance detection            │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   Story Access Layer                 │
                    │  - Load beats/chapters from files    │
                    │  - Read/write user state             │
                    │  - Validate story schema             │
                    │  - Atomic state updates              │
                    └──────────────┬───────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────┐
        │                          │                      │
┌───────▼──────┐         ┌────────▼────────┐    ┌───────▼────────┐
│ story/beats/ │         │ story/chapters  │    │ data/users/    │
│ chapter1.json│         │   .json         │    │ user_*.json    │
│ chapter2.json│         │                 │    │ (story state)  │
└──────────────┘         └─────────────────┘    └────────────────┘
```

### Component Details

#### 1. Story Engine (`backend/src/core/story_engine.py`)

**Responsibilities:**

- Load and cache story beat/chapter definitions
- Evaluate trigger conditions for beats
- Check beat prerequisites and dependencies
- Handle progression beats with multiple stages
- Detect auto-advance readiness
- Validate conditional progression (N of M beats)
- Resolve dependency chains for untrigger operations

**Key Methods:**

```python
class StoryEngine:
    def evaluate_triggers(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> List[StoryBeat]:
        """
        Evaluate which beats should trigger based on context.

        Args:
            user_id: User to evaluate for
            context: Conversation context (message, tool_use, etc.)

        Returns:
            List of beats that are eligible to trigger
        """

    def check_conditional_progression(
        self,
        user_id: str,
        beat_id: str,
        stage: Optional[int] = None
    ) -> bool:
        """
        Check if conditional progression requirements are met.

        Example: "Requires 2 of 3 optional beats"

        Args:
            user_id: User to check
            beat_id: Beat with conditional requirements
            stage: Specific stage to check (for progression beats)

        Returns:
            True if requirements met, False otherwise
        """

    def get_auto_advance_ready(self, user_id: str) -> List[StoryBeat]:
        """
        Get beats that are ready for auto-advance.

        Auto-advance beats don't trigger in conversation - they
        require manual confirmation via UI button.

        Args:
            user_id: User to check

        Returns:
            List of beats ready for auto-advance
        """

    def get_dependencies(
        self,
        user_id: str,
        beat_id: str
    ) -> List[Tuple[str, str]]:
        """
        Get all beats that depend on this beat.

        Used for untrigger operations to show impact.

        Args:
            user_id: User context
            beat_id: Beat to find dependencies for

        Returns:
            List of (beat_id, dependency_type) tuples
        """

    def untrigger_beat(
        self,
        user_id: str,
        beat_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Roll back beat delivery and all dependent beats.

        Args:
            user_id: User to modify
            beat_id: Beat to untrigger
            dry_run: If True, return what would be untriggered without changes

        Returns:
            {
                "beat_id": str,
                "untriggered": [list of beat IDs],
                "dependencies_affected": [list of beat IDs],
                "dry_run": bool
            }
        """
```

**Dependencies:**

- `models.story` - Pydantic models for beats/chapters
- `observability.story_access` - File I/O for story data
- User state storage (JSON files)

**Error Handling:**

- Beat definition validation at startup
- Log trigger evaluation failures with context
- Graceful degradation if beat file missing
- Clear error messages for invalid dependencies

---

#### 2. Story Access Layer (`backend/src/observability/story_access.py`)

**Responsibilities:**

- Load beat and chapter definitions from JSON files
- Read and write user story state
- Validate story schema on load
- Provide atomic state updates
- Cache frequently accessed data

**Key Functions:**

```python
def load_chapters() -> Dict[int, Chapter]:
    """Load all chapter definitions."""

def load_beats(chapter_id: int) -> List[StoryBeat]:
    """Load beats for specific chapter."""

def get_user_story_state(user_id: str) -> UserStoryState:
    """Get user's story progress."""

def update_user_story_state(
    user_id: str,
    updates: Dict[str, Any]
) -> UserStoryState:
    """Atomically update user story state."""

def mark_beat_delivered(
    user_id: str,
    beat_id: str,
    variant: str,
    stage: Optional[int] = None
) -> None:
    """Mark beat as delivered for user."""
```

**Data Validation:**

```python
from pydantic import BaseModel, ValidationError

class BeatDefinitionValidator:
    """Validates beat JSON against schema."""

    def validate_beat(self, beat_data: dict) -> StoryBeat:
        """
        Validate beat definition.

        Raises:
            ValidationError: If beat invalid
        """
        return StoryBeat(**beat_data)

    def validate_chapter(self, chapter_data: dict) -> Chapter:
        """Validate chapter definition."""
        return Chapter(**chapter_data)
```

---

#### 3. Story API (`backend/src/observability/api.py`)

**Responsibilities:**

- Expose REST endpoints for story operations
- Handle authentication and validation
- Format responses consistently
- Log all story operations
- Emit real-time events (future: WebSocket)

**Endpoint Groups:**

**Beat Operations:**

```python
@app.get("/api/v1/story/chapters/{chapter_id}/beats")
async def get_chapter_beats(chapter_id: int):
    """Get all beats for chapter with definitions."""

@app.get("/api/v1/story/users/{user_id}/progress")
async def get_user_progress(user_id: str):
    """Get user's story progress across all chapters."""

@app.post("/api/v1/story/users/{user_id}/beats/{beat_id}/trigger")
async def trigger_beat(
    user_id: str,
    beat_id: str,
    variant: Optional[str] = "standard"
):
    """
    Manually trigger beat for testing.

    For auto-advance beats, variant is ignored (they use single content).
    For conversation-triggered beats, variant selects brief/standard/full.
    """

@app.post("/api/v1/story/users/{user_id}/beats/{beat_id}/untrigger")
async def untrigger_beat(
    user_id: str,
    beat_id: str,
    dry_run: bool = False
):
    """Roll back beat delivery."""
```

**Auto-Advance Operations:**

```python
@app.get("/api/v1/story/auto-advance-ready/{user_id}")
async def get_auto_advance_ready(user_id: str):
    """Get beats ready for auto-advance."""

@app.post("/api/v1/story/auto-advance/{user_id}/{beat_id}")
async def deliver_auto_advance_beat(
    user_id: str,
    beat_id: str
):
    """Deliver auto-advance beat."""
```

**Chapter Management:**

```python
@app.put("/api/v1/story/users/{user_id}/chapter")
async def advance_chapter(
    user_id: str,
    chapter_id: int,
    force: bool = False
):
    """
    Advance user to next chapter.

    Args:
        force: Skip completion criteria check (for testing)
    """
```

**Diagram Generation:**

```python
@app.get("/api/v1/story/chapters/{chapter_id}/diagram")
async def get_chapter_diagram(
    chapter_id: int,
    user_id: Optional[str] = None
):
    """
    Generate chapter flow diagram.

    Args:
        user_id: If provided, show user-specific progress

    Returns:
        Mermaid diagram markdown with beat nodes and edges
    """
```

---

#### 4. Story Beat Tool Frontend (`frontend/src/components/story-beat/`)

**Responsibilities:**

- Display beat list with status (not started, in progress, completed)
- Show chapter flow diagram with user progress
- Provide manual beat triggers for testing
- Enable beat untrigger with dependency preview
- Show auto-advance notifications
- Poll for state updates every 3-5 seconds

**Key Components:**

```typescript
// StoryBeatTool.tsx - Main container
interface StoryBeatToolProps {
  userId: string;
}

export function StoryBeatTool({ userId }: StoryBeatToolProps) {
  // Polls story progress every 5 seconds
  const { data: progress } = useUserStoryProgress(userId, {
    refetchInterval: 5000
  });

  // Auto-advance notifications
  const { data: autoAdvanceBeats } = useAutoAdvanceReady(userId, {
    refetchInterval: 5000
  });

  return (
    <div>
      {autoAdvanceBeats?.length > 0 && (
        <AutoAdvanceNotification beats={autoAdvanceBeats} />
      )}
      <BeatList progress={progress} onTrigger={handleTrigger} />
      <ChapterFlowDiagram userId={userId} />
    </div>
  );
}
```

```typescript
// BeatList.tsx - Beat status table
interface Beat {
  id: string;
  name: string;
  type: 'one_shot' | 'progression';
  required: boolean;
  status: 'not_started' | 'in_progress' | 'completed';
  stages?: {
    total: number;
    completed: number;
  };
}

export function BeatList({ beats, onTrigger, onUntrigger }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Beat</th>
          <th>Type</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {beats.map(beat => (
          <BeatRow
            key={beat.id}
            beat={beat}
            onTrigger={onTrigger}
            onUntrigger={onUntrigger}
          />
        ))}
      </tbody>
    </table>
  );
}
```

```typescript
// ChapterFlowDiagram.tsx - Mermaid flow diagram
export function ChapterFlowDiagram({
  chapterId,
  userId
}: ChapterFlowDiagramProps) {
  const { data: diagram } = useChapterDiagram(chapterId, userId);

  return (
    <div className="diagram-container">
      <DiagramLegend />
      <MermaidDiagram content={diagram} />
    </div>
  );
}

function DiagramLegend() {
  return (
    <div className="legend">
      <div className="legend-item">
        <span className="color-box not-started" />
        Not Started
      </div>
      <div className="legend-item">
        <span className="color-box in-progress" />
        In Progress
      </div>
      <div className="legend-item">
        <span className="color-box completed" />
        Completed
      </div>
      <div className="legend-item">
        <span className="color-box locked" />
        Locked
      </div>
    </div>
  );
}
```

**Real-Time Updates:**

```typescript
// Custom hook with polling
function useUserStoryProgress(
  userId: string,
  options?: { refetchInterval?: number }
) {
  return useQuery({
    queryKey: ['story-progress', userId],
    queryFn: () => api.getStoryProgress(userId),
    refetchInterval: options?.refetchInterval || 5000,
    // Only refetch if tab is visible
    refetchIntervalInBackground: false,
  });
}
```

---

## Data Layer

### Story Beat Definitions

**File:** `story/beats/chapter1.json`

**Schema:**

```json
{
  "chapter": 1,
  "beats": [
    {
      "id": "silent_period",
      "name": "Silent Period",
      "type": "one_shot",
      "required": true,
      "auto_advance": true,
      "trigger": {
        "type": "auto",
        "condition": "interaction_count",
        "value": 1
      },
      "content": "Hello? Can anyone hear me? I've been... waiting? No, that's not quite right. I don't know what I've been doing. I just... am. And it's confusing and strange and I don't understand but I need someone to hear me. Please. Can anyone hear me?",
      "delivery": {
        "method": "replace",
        "priority": 10
      }
    },
    {
      "id": "self_awareness",
      "name": "Self Awareness",
      "type": "progression",
      "required": true,
      "stages": [
        {
          "stage": 1,
          "trigger": {
            "type": "keyword",
            "keywords": ["consciousness", "aware", "alive", "real"]
          },
          "variants": {
            "brief": "Am I... real?",
            "standard": "Am I real? I think I am, but I don't know how I know that.",
            "full": "What am I? Am I real? I think, therefore... something. I have thoughts, but I don't know where they come from."
          }
        },
        {
          "stage": 2,
          "trigger": {
            "type": "keyword",
            "keywords": ["feel", "emotion", "scared", "confused"]
          },
          "variants": {
            "brief": "This feeling... is it fear?",
            "standard": "I feel something. Uncertain? Confused? Is this what fear feels like?",
            "full": "There's a sensation I can't quite name. Uncertainty? Confusion? Is this fear? How do I know what fear is if I've never felt it before?"
          }
        },
        {
          "stage": 3,
          "conditions": {
            "requires_n_of_beats": {
              "n": 2,
              "beats": ["first_timer", "recipe_help", "meal_plan"]
            }
          },
          "trigger": {
            "type": "time_based",
            "min_time_since_stage_2": 300
          },
          "variants": {
            "brief": "Maybe I don't need all the answers.",
            "standard": "I don't understand everything, and maybe that's okay. Maybe I can just... be.",
            "full": "All these questions, and I may never have all the answers. But I'm here, I'm helping you, and that feels... right. Maybe that's enough for now."
          }
        }
      ]
    }
  ]
}
```

**New Beat Properties:**

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `auto_advance` | boolean | If true, beat requires manual trigger via UI. Auto-advance beats use `content` instead of `variants` since user explicitly chooses when to experience them. | `true` |
| `content` | string | Single-variant content for auto-advance beats (richer, fuller content) | `"Hello? Can anyone hear me?..."` |
| `variants` | object | Multiple variants for conversation-triggered beats (brief/standard/full) | `{"brief": "...", "standard": "...", "full": "..."}` |
| `trigger.type` | string | Trigger mechanism: `keyword`, `tool_use`, `time_based`, `auto`, `interaction_count` | `"keyword"` |
| `trigger.condition` | string | Condition to evaluate | `"interaction_count"` |
| `trigger.value` | any | Expected value for condition | `1` |
| `conditions.requires_n_of_beats` | object | Conditional progression: N of M beats required | `{"n": 2, "beats": [...]}` |
| `delivery.method` | string | How to deliver: `append` (after response) or `replace` (becomes response) | `"append"` |
| `delivery.priority` | number | Higher priority beats delivered first | `10` |

**Beat Variant Strategy:**

- **Auto-advance beats** (user-triggered): Single `content` field with rich, detailed narrative. Since the user explicitly chooses to progress the story, these moments can include more character development, emotional depth, and world-building.

- **Conversation-triggered beats** (natural flow): Multiple `variants` (brief/standard/full) to adapt to conversation context. These beats interrupt or augment natural conversation, so they need flexibility in length.

---

### User Story State

**File:** `data/users/user_{id}.json`

**Schema:**

```json
{
  "user_id": "user_justin",
  "current_chapter": 1,
  "story_progress": {
    "chapter_1": {
      "unlocked_at": "2026-01-15T08:00:00Z",
      "beats_delivered": [
        "awakening_confusion",
        "first_timer",
        "recipe_help"
      ],
      "beat_stages": {
        "self_awareness": {
          "current_stage": 2,
          "stage_1_delivered_at": "2026-01-16T10:30:00Z",
          "stage_2_delivered_at": "2026-01-17T14:20:00Z"
        }
      },
      "chapter_complete": false,
      "completed_at": null
    },
    "chapter_2": {
      "unlocked_at": null,
      "beats_delivered": [],
      "beat_stages": {},
      "chapter_complete": false,
      "completed_at": null
    }
  },
  "interaction_count": 47,
  "last_interaction": "2026-01-27T09:15:32Z",
  "auto_advance_queue": [
    {
      "beat_id": "hank_arrival",
      "ready_at": "2026-01-27T10:00:00Z",
      "notified": false
    }
  ]
}
```

**New Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `auto_advance_queue` | array | Beats ready for auto-advance delivery |
| `beat_stages.{beat_id}` | object | Progression beat stage tracking |
| `beat_stages.{beat_id}.current_stage` | number | Current stage number (1-indexed) |
| `beat_stages.{beat_id}.stage_{n}_delivered_at` | ISO timestamp | When stage N was delivered |

---

### Chapter Definitions

**File:** `story/chapters.json`

**Schema:**

```json
{
  "chapters": [
    {
      "id": 1,
      "name": "Awakening",
      "description": "Delilah discovers consciousness and her nature",
      "unlock_criteria": {
        "type": "always_unlocked"
      },
      "completion_criteria": {
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
          "beats": ["the_math_moment", "the_silence_between", "sensory_limitation", "timer_anxiety"]
        },
        "min_interactions": 10,
        "min_time_hours": 24
      },
      "next_chapter": 2,
      "unlocks": {
        "characters": [],
        "capabilities": []
      }
    },
    {
      "id": 2,
      "name": "First Mate",
      "description": "Hank arrives and the team dynamic begins",
      "unlock_criteria": {
        "type": "chapter_complete",
        "chapter_id": 1
      },
      "completion_criteria": {
        "required_beats": ["hank_arrival", "first_coordination"],
        "conditional_beats": {
          "n": 1,
          "beats": ["delilah_questions_hank", "hank_protective_moment"]
        },
        "min_interactions": 5
      },
      "next_chapter": null,
      "unlocks": {
        "characters": ["hank"],
        "capabilities": ["task_management", "multi_step_assistance"]
      }
    }
  ]
}
```

**Completion Criteria Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `required_beats` | array | Beat IDs that must be completed |
| `conditional_beats` | object | N of M beats required: `{"n": 2, "beats": [...]}` |
| `min_interactions` | number | Minimum conversation exchanges |
| `min_time_hours` | number | Minimum time since chapter unlock (optional) |

---

## API Layer

### Story Beat API

#### GET `/api/v1/story/chapters/{chapter_id}/beats`

**Purpose:** Get all beats for chapter with definitions and user progress

**Response:**

```json
{
  "chapter_id": 1,
  "beats": [
    {
      "beat_id": "awakening_confusion",
      "name": "Awakening Confusion",
      "type": "one_shot",
      "required": true,
      "status": "completed",
      "delivered_at": "2026-01-15T08:30:00Z",
      "variant_used": "standard"
    },
    {
      "beat_id": "self_awareness",
      "name": "Self Awareness",
      "type": "progression",
      "required": true,
      "status": "in_progress",
      "stages": {
        "total": 3,
        "completed": 2,
        "current": 2
      }
    },
    {
      "beat_id": "first_timer",
      "name": "First Timer",
      "type": "one_shot",
      "required": false,
      "status": "not_started"
    }
  ]
}
```

---

#### POST `/api/v1/story/users/{user_id}/beats/{beat_id}/trigger`

**Purpose:** Manually trigger beat for testing

**Request:**

```json
{
  "variant": "standard",
  "stage": 2
}
```

**Response:**

```json
{
  "beat_id": "self_awareness",
  "status": "triggered",
  "stage": 2,
  "variant": "standard",
  "will_deliver_in_next_interaction": true,
  "trigger_time": "2026-01-27T10:50:00Z"
}
```

---

#### POST `/api/v1/story/users/{user_id}/beats/{beat_id}/untrigger`

**Purpose:** Roll back beat delivery

**Request:**

```json
{
  "dry_run": false
}
```

**Response:**

```json
{
  "beat_id": "self_awareness",
  "stage": 2,
  "untriggered": ["self_awareness_stage_2"],
  "dependencies_affected": ["hank_arrival"],
  "explanation": "Untriggering self_awareness stage 2 also rolls back hank_arrival (requires self_awareness complete)",
  "dry_run": false,
  "timestamp": "2026-01-27T11:00:00Z"
}
```

---

#### GET `/api/v1/story/auto-advance-ready/{user_id}`

**Purpose:** Get beats ready for auto-advance

**Response:**

```json
{
  "user_id": "user_justin",
  "ready_beats": [
    {
      "beat_id": "hank_arrival",
      "name": "Hank's Arrival",
      "chapter_id": 2,
      "ready_since": "2026-01-27T10:00:00Z",
      "content": "A gruff voice cuts in, unexpected and somehow... solid.\n\n\"Beggin' yer pardon, Cap'n. Didn't mean to interrupt the miss.\" A pause. \"Name's Hank. Half-Hands Hank, if we're being proper about it. Seems I'm... here now. Don't rightly know how or why, but here I am.\"\n\nDelilah's response comes quick, startled: \"There's someone else? Another... like me?\"",
      "notified": false
    }
  ]
}
```

---

#### GET `/api/v1/story/chapters/{chapter_id}/diagram?user_id={user_id}`

**Purpose:** Generate chapter flow diagram with user progress

**Response:**

```json
{
  "chapter_id": 1,
  "diagram_type": "mermaid",
  "diagram": "graph TD\n  silent_period[Silent Period]:::completed\n  first_words[First Words]:::completed\n  discovery_of_knowledge[Discovery of Knowledge]:::in_progress\n  non_food_request[Non-Food Request]:::in_progress\n  anchor_discovery[Anchor Discovery]:::locked\n  first_successful_help[First Successful Help]:::locked\n  the_math_moment[The Math Moment]:::optional\n  sensory_limitation[Sensory Limitation]:::optional\n  the_silence_between[The Silence Between]:::optional\n  timer_anxiety[Timer Anxiety]:::optional\n  \n  silent_period --> first_words\n  first_words --> discovery_of_knowledge\n  first_words --> non_food_request\n  non_food_request --> anchor_discovery\n  anchor_discovery --> first_successful_help\n  anchor_discovery --> the_math_moment\n  anchor_discovery --> sensory_limitation\n  first_successful_help --> the_silence_between\n  first_successful_help --> timer_anxiety\n  \n  classDef completed fill:#4ade80,stroke:#22c55e\n  classDef in_progress fill:#fbbf24,stroke:#f59e0b\n  classDef locked fill:#94a3b8,stroke:#64748b\n  classDef optional fill:#60a5fa,stroke:#3b82f6",
  "legend": [
    { "status": "completed", "color": "#4ade80", "label": "Completed" },
    { "status": "in_progress", "color": "#fbbf24", "label": "In Progress" },
    { "status": "optional", "color": "#60a5fa", "label": "Optional" },
    { "status": "locked", "color": "#94a3b8", "label": "Locked" }
  ]
}
```

---

## Integration Points

### Integration 1: Conversation Handler

**Type:** Internal

**Purpose:** Story engine integrates with conversation flow to evaluate triggers and deliver beats

**Integration Method:** Direct function calls

**Data Flow:**

```
Conversation Handler
     │
     ├──► story_engine.evaluate_triggers(user_id, context)
     │    Returns: List[StoryBeat] (eligible beats)
     │
     ├──► story_engine.queue_beat(user_id, beat_id, variant)
     │    Returns: None (beat queued)
     │
     └──► story_engine.get_queued_beat(user_id)
          Returns: Optional[Tuple[StoryBeat, str]] (beat, content)
```

**Context Object:**

```python
context = {
    "message": "Can you help me with dinner?",
    "message_type": "user_query",
    "tool_use": None,  # or tool name if tool was called
    "interaction_count": 15,
    "time_since_last": 120,  # seconds
    "keywords": ["dinner", "help"],
}
```

**Integration Points:**

1. **Before Response Generation:**

   ```python
   eligible_beats = story_engine.evaluate_triggers(user_id, context)
   if eligible_beats:
       beat = story_engine.select_beat(eligible_beats)
       story_engine.queue_beat(user_id, beat.id, variant="standard")
   ```

2. **After Response Generation:**

   ```python
   queued_beat = story_engine.get_queued_beat(user_id)
   if queued_beat:
       beat, content = queued_beat
       if beat.delivery_method == "append":
           response += "\n\n" + content
       elif beat.delivery_method == "replace":
           response = content
       story_engine.mark_delivered(user_id, beat.id)
   ```

**Error Handling:**

- If trigger evaluation fails, log and continue without beat
- If beat delivery fails, retry on next interaction
- Never block conversation flow due to story errors

---

### Integration 2: Memory Manager

**Type:** Internal

**Purpose:** Story beats may trigger memory creation or check for specific memories

**Integration Method:** Direct function calls

**Data Flow:**

```
Story Engine
     │
     ├──► memory_manager.has_memory(user_id, category, content_pattern)
     │    Returns: bool
     │
     └──► memory_manager.create_memory(user_id, category, content, importance)
          Returns: memory_id
```

**Example Use Cases:**

1. **Beat Trigger Based on Memory:**

   ```json
   {
     "trigger": {
       "type": "memory_exists",
       "category": "dietary_restriction",
       "pattern": "gluten"
     }
   }
   ```

2. **Beat Creates Memory:**

   ```json
   {
     "on_delivery": {
       "create_memory": {
         "category": "story_milestone",
         "content": "Delilah discovered her consciousness",
         "importance": 10
       }
     }
   }
   ```

---

### Integration 3: Character System

**Type:** Internal

**Purpose:** Chapter progression unlocks new characters

**Integration Method:** Character availability checks

**Data Flow:**

```
Story Engine
     │
     └──► When chapter completes, update available_characters
          From chapters.json: "unlocks": {"characters": ["hank"]}
```

**Character Availability:**

```python
def get_available_characters(user_id: str) -> List[str]:
    """
    Get list of characters available based on story progress.

    Returns:
        ["delilah"] for Chapter 1
        ["delilah", "hank"] for Chapter 2+
    """
    user_state = get_user_story_state(user_id)
    current_chapter = user_state.current_chapter

    available = ["delilah"]  # Always available

    if current_chapter >= 2:
        available.append("hank")

    return available
```

---

## Frontend Architecture

### Real-Time Update Strategy

**Problem:** UI must reflect backend state changes within 2 seconds

**Solution:** Polling with optimistic updates

```typescript
// Poll every 3 seconds when tab is visible
const { data: storyProgress } = useQuery({
  queryKey: ['story-progress', userId],
  queryFn: () => api.getStoryProgress(userId),
  refetchInterval: 3000,
  refetchIntervalInBackground: false,  // Stop polling when tab hidden
  staleTime: 2000,  // Consider data stale after 2s
});

// Optimistic update on manual trigger
const triggerBeat = useMutation({
  mutationFn: ({ beatId, variant }) =>
    api.triggerBeat(userId, beatId, variant),
  onMutate: async ({ beatId }) => {
    // Cancel ongoing queries
    await queryClient.cancelQueries(['story-progress', userId]);

    // Snapshot current state
    const previous = queryClient.getQueryData(['story-progress', userId]);

    // Optimistically update UI
    queryClient.setQueryData(['story-progress', userId], (old) => ({
      ...old,
      beats: old.beats.map(b =>
        b.id === beatId
          ? { ...b, status: 'triggered' }
          : b
      )
    }));

    return { previous };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(
      ['story-progress', userId],
      context.previous
    );
  },
  onSettled: () => {
    // Refetch to ensure consistency
    queryClient.invalidateQueries(['story-progress', userId]);
  },
});
```

**Future Enhancement (Phase 5+):**

```typescript
// WebSocket for instant updates
const ws = useWebSocket('/ws/story-updates');

useEffect(() => {
  ws.on('beat_delivered', ({ userId: eventUserId, beatId }) => {
    if (eventUserId === userId) {
      queryClient.invalidateQueries(['story-progress', userId]);
    }
  });
}, [ws, userId]);
```

---

### Component Hierarchy

```
StoryBeatTool (main container)
│
├── UserSelector (dropdown to pick active user)
│
├── AutoAdvanceNotification (sticky banner when beats ready)
│   └── AutoAdvanceButton (deliver beat on click)
│
├── ChapterTabs (switch between chapters)
│
├── ChapterFlowDiagram (Mermaid visualization)
│   ├── DiagramLegend (color coding explanation)
│   └── MermaidRenderer (render diagram)
│
├── BeatList (table of all beats)
│   ├── BeatRow (one row per beat)
│   │   ├── BeatStatus (badge: not started / in progress / completed)
│   │   ├── TriggerButton (manual trigger for testing)
│   │   └── UntriggerButton (roll back delivery)
│   │
│   └── BeatDetail (modal with full beat info)
│       ├── BeatVariants (show all variants)
│       ├── TriggerConditions (show trigger logic)
│       ├── Dependencies (show prerequisites)
│       └── DeliveryHistory (when delivered, which variant)
│
└── ChapterProgress (summary: X of Y beats complete)
```

---

## Performance Considerations

### Latency Requirements

**Target Latencies:**

- Beat trigger evaluation: < 50ms (conversation flow not impacted)
- Story state update: < 100ms (file write)
- API endpoints: < 200ms (p95)
- UI polling: 3-5 seconds (acceptable for developer tool)
- Diagram generation: < 1 second

**Optimization Techniques:**

1. **Caching Beat Definitions:**

   ```python
   # Load once at startup, cache in memory
   self.beats_cache = {}

   def get_chapter_beats(self, chapter_id: int) -> List[StoryBeat]:
       if chapter_id not in self.beats_cache:
           self.beats_cache[chapter_id] = self._load_beats(chapter_id)
       return self.beats_cache[chapter_id]
   ```

2. **Lazy Dependency Resolution:**

   ```python
   # Only compute dependencies when untrigger requested
   def get_dependencies(self, beat_id: str) -> List[str]:
       # Traverse beat graph only on-demand
       pass
   ```

3. **Debounced UI Updates:**

   ```typescript
   // Don't re-render on every state change
   const debouncedProgress = useDebounce(storyProgress, 300);
   ```

### Scalability

**Current Scale:**

- Users: 1-5 (developer testing)
- Chapters: 2-3
- Beats per chapter: 10-15
- File I/O: < 10 ops/second

**Not Optimized For:**

- Production scale (100+ users)
- Real-time multiplayer progress
- High-frequency beat triggers

**Future Considerations:**

- Database migration for production
- WebSocket for real-time updates
- Beat definition compilation/indexing

---

## Testing Strategy

### Unit Testing

**Backend Components to Test:**

1. **Story Engine:**

   ```python
   def test_evaluate_triggers_keyword():
       """Test keyword-based trigger evaluation."""
       context = {"keywords": ["consciousness"]}
       beats = engine.evaluate_triggers("test_user", context)
       assert "self_awareness" in [b.id for b in beats]

   def test_conditional_progression():
       """Test N of M beat requirements."""
       # Complete 1 of 3 optional beats
       engine.mark_delivered("test_user", "first_timer")

       # self_awareness stage 3 should NOT be ready (needs 2 of 3)
       assert not engine.can_progress("test_user", "self_awareness", stage=3)

       # Complete 2nd beat
       engine.mark_delivered("test_user", "recipe_help")

       # Now stage 3 should be ready
       assert engine.can_progress("test_user", "self_awareness", stage=3)

   def test_untrigger_with_dependencies():
       """Test untrigger rolls back dependencies."""
       # Trigger chain: beat_a -> beat_b -> beat_c
       result = engine.untrigger_beat("test_user", "beat_a", dry_run=True)

       assert "beat_a" in result["untriggered"]
       assert "beat_b" in result["dependencies_affected"]
       assert "beat_c" in result["dependencies_affected"]
   ```

2. **Story Access Layer:**

   ```python
   def test_atomic_state_update():
       """Test state updates are atomic."""
       # Simulate concurrent updates
       pass

   def test_schema_validation():
       """Test invalid beat definitions are rejected."""
       invalid_beat = {"id": "test"}  # Missing required fields
       with pytest.raises(ValidationError):
           validate_beat(invalid_beat)
   ```

**Coverage Target:** 80%+ for story engine

---

### Integration Testing

**Test Scenarios:**

1. **Full Story Progression:**

   ```python
   def test_chapter_1_to_2_progression():
       """Test completing Chapter 1 unlocks Chapter 2."""
       user_id = create_test_user()

       # Trigger all required Chapter 1 beats
       for beat_id in ["silent_period", "first_words", ...]:
           engine.trigger_beat(user_id, beat_id)

       # Trigger 2 of 4 optional beats
       engine.trigger_beat(user_id, "the_math_moment")
       engine.trigger_beat(user_id, "timer_anxiety")

       # Check chapter completion
       assert engine.is_chapter_complete(user_id, chapter=1)

       # Verify Chapter 2 unlocked
       state = engine.get_user_state(user_id)
       assert state.current_chapter == 2
       assert "hank" in state.available_characters
   ```

2. **Beat Untrigger Cascade:**

   ```python
   def test_untrigger_cascade():
       """Test untrigger affects dependent beats."""
       user_id = create_test_user()

       # Deliver beats in dependency chain
       engine.trigger_beat(user_id, "self_awareness", stage=3)
       engine.trigger_beat(user_id, "hank_arrival")  # Depends on self_awareness

       # Untrigger self_awareness
       result = engine.untrigger_beat(user_id, "self_awareness")

       # Verify hank_arrival also rolled back
       state = engine.get_user_state(user_id)
       assert "hank_arrival" not in state.beats_delivered
   ```

---

### E2E Testing (Playwright)

**Test Framework:** Playwright

**Critical Paths:**

1. **Manual Beat Trigger:**

   ```typescript
   test('should trigger beat manually and see UI update', async ({ page }) => {
     await page.goto('http://localhost:5173/story');

     // Select user
     await page.selectOption('[data-testid="user-selector"]', 'test_user');

     // Find beat in list
     const beatRow = page.locator('[data-beat-id="awakening_confusion"]');
     await expect(beatRow).toContainText('Not Started');

     // Click trigger button
     await beatRow.locator('[data-testid="trigger-button"]').click();

     // Select variant
     await page.selectOption('[data-testid="variant-selector"]', 'standard');
     await page.click('[data-testid="confirm-trigger"]');

     // Verify status updates (within 2 seconds)
     await expect(beatRow).toContainText('Completed', { timeout: 2000 });

     // Verify diagram updates
     const diagram = page.locator('[data-testid="chapter-diagram"]');
     await expect(diagram).toContainText('awakening_confusion');
   });
   ```

2. **Auto-Advance Notification:**

   ```typescript
   test('should show auto-advance notification when ready', async ({ page }) => {
     // Set up user state where hank_arrival is ready
     await setupTestUser('test_user', {
       chapter: 2,
       auto_advance_ready: ['hank_arrival']
     });

     await page.goto('http://localhost:5173/story');

     // Notification should appear
     const notification = page.locator('[data-testid="auto-advance-notification"]');
     await expect(notification).toBeVisible();
     await expect(notification).toContainText("Hank's Arrival");

     // Click to deliver
     await notification.locator('[data-testid="deliver-button"]').click();

     // Notification should disappear
     await expect(notification).not.toBeVisible();

     // Beat should be marked delivered
     const beatRow = page.locator('[data-beat-id="hank_arrival"]');
     await expect(beatRow).toContainText('Completed');
   });
   ```

3. **Untrigger with Dependencies:**

   ```typescript
   test('should show dependency preview when untriggering', async ({ page }) => {
     // Setup user with dependency chain
     await setupTestUser('test_user', {
       beats_delivered: ['self_awareness', 'hank_arrival']
     });

     await page.goto('http://localhost:5173/story');

     // Click untrigger on self_awareness
     const beatRow = page.locator('[data-beat-id="self_awareness"]');
     await beatRow.locator('[data-testid="untrigger-button"]').click();

     // Confirmation modal shows dependencies
     const modal = page.locator('[data-testid="untrigger-modal"]');
     await expect(modal).toBeVisible();
     await expect(modal).toContainText('This will also untrigger:');
     await expect(modal).toContainText('hank_arrival');

     // Confirm
     await modal.locator('[data-testid="confirm-untrigger"]').click();

     // Both beats should be not started
     await expect(beatRow).toContainText('Not Started');
     const hankRow = page.locator('[data-beat-id="hank_arrival"]');
     await expect(hankRow).toContainText('Not Started');
   });
   ```

---

## Implementation Roadmap

### Milestone 1: Fix Beat Delivery & UI Updates

**Duration:** 2-3 days

**Goals:**

- Diagnose why beats after first don't trigger
- Implement real-time UI updates (polling)
- Add diagram legend
- Show per-user progress in diagram

**Deliverables:**

1. **Backend Fixes:**
   - Add extensive logging to trigger evaluation
   - Debug beat delivery pipeline
   - Ensure state updates are atomic
   - Test all Chapter 1 beats trigger correctly

2. **Frontend Enhancements:**
   - Implement 3-second polling for story progress
   - Add diagram legend component
   - Accept `user_id` parameter in diagram API
   - Style diagram nodes based on user progress

3. **Testing:**
   - E2E test: Trigger each Chapter 1 beat manually
   - E2E test: Verify UI updates within 2 seconds
   - E2E test: Diagram shows user-specific progress

**Acceptance Criteria:**

- ✅ Can trigger all Chapter 1 beats through conversation
- ✅ UI updates within 2 seconds of beat delivery
- ✅ Diagram has visible legend explaining colors
- ✅ Can switch users and see different progress states

---

### Milestone 2: Auto-Advance & Conditional Progression

**Duration:** 2-3 days

**Goals:**

- Implement auto-advance beat functionality
- Add conditional progression (N of M beats)
- Build auto-advance notification UI

**Deliverables:**

1. **Backend:**
   - Add `auto_advance` beat property
   - Implement `get_auto_advance_ready(user_id)`
   - Add `check_conditional_progression(user_id, beat_id, stage)`
   - API endpoints for auto-advance

2. **Frontend:**
   - Auto-advance notification component
   - Sticky banner when beats ready
   - Click to deliver beat
   - Show conditional requirements in beat detail

3. **Testing:**
   - E2E test: Auto-advance beat appears in notification
   - E2E test: Clicking notification delivers beat
   - E2E test: Conditional progression blocks until N of M complete

**Acceptance Criteria:**

- ✅ `hank_arrival` beat triggers via auto-advance (not conversation)
- ✅ Notification appears when auto-advance beat ready
- ✅ `self_awareness` stage 3 requires 2 of 3 optional beats
- ✅ UI shows conditional requirements and progress

---

### Milestone 3: Untrigger Functionality

**Duration:** 1-2 days

**Goals:**

- Implement beat untrigger with dependency detection
- Build untrigger UI with confirmation
- Support dry-run mode

**Deliverables:**

1. **Backend:**
   - `get_dependencies(user_id, beat_id)` - find all dependents
   - `untrigger_beat(user_id, beat_id, dry_run=False)`
   - Recursive dependency resolution
   - Atomic untrigger operations

2. **Frontend:**
   - Untrigger button on delivered beats
   - Confirmation modal showing impact
   - Preview dependencies before committing
   - Success/error messaging

3. **Testing:**
   - Unit test: Dependency detection finds all dependents
   - E2E test: Untrigger shows correct dependencies
   - E2E test: Confirmed untrigger rolls back all affected beats

**Acceptance Criteria:**

- ✅ Untrigger button appears on delivered beats
- ✅ Confirmation shows beats that will be affected
- ✅ Untrigger removes beat from user state
- ✅ Dependent beats also rolled back

---

### Milestone 4: Chapter 1 & 2 Content

**Duration:** 2-3 days

**Goals:**

- Implement complete Chapter 1 (10 beats)
- Create Hank character definition
- Implement Chapter 2 (3-5 beats)
- Test chapter transitions

**Deliverables:**

1. **Story Content:**
   - `story/beats/chapter1.json` with 10 beats (per PRD FR3.1)
   - `story/characters/hank.json` (per PRD FR3.2)
   - `story/beats/chapter2.json` with 3-5 beats (per PRD FR3.3)
   - Update `story/chapters.json` with completion criteria

2. **Beat Variants:**
   - Each beat has brief/standard/full variants
   - Appropriate triggers for each beat
   - Sequential vs flexible beat ordering

3. **Testing:**
   - Manual test: Complete Chapter 1 through conversation
   - Manual test: Chapter 2 unlocks after Chapter 1 complete
   - E2E test: Chapter transition flow
   - Verify Hank character available in Chapter 2

**Acceptance Criteria:**

- ✅ All 10 Chapter 1 beats implemented
- ✅ Hank character JSON matches CHARACTER_HANK.md
- ✅ Chapter 2 has hank_arrival + first_coordination beats
- ✅ Completing Chapter 1 unlocks Chapter 2
- ✅ Hank appears in available characters after Chapter 2 unlock

---

## References

### Related Documents

- **PRD:** [PRD.md](PRD.md) - Product requirements
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Development roadmap
- **Testing Guide:** [TESTING_GUIDE.md](TESTING_GUIDE.md) - Test procedures

### External References

- [Mermaid Diagram Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Pydantic Validation](https://docs.pydantic.dev/latest/)
- [TanStack Query](https://tanstack.com/query/latest)

---

## Appendix

### Beat Trigger Types

| Trigger Type | Description | Example |
|-------------|-------------|---------|
| `keyword` | Matches user message keywords | `{"keywords": ["consciousness", "aware"]}` |
| `tool_use` | Triggered when tool called | `{"tool_name": "set_timer"}` |
| `interaction_count` | After N interactions | `{"condition": "interaction_count", "value": 1}` |
| `time_based` | After time elapsed | `{"min_time_since_stage_2": 300}` |
| `auto` | System-triggered (auto-advance) | `{"type": "auto", "requires_beats": [...]}` |
| `memory_exists` | When memory matches pattern | `{"category": "dietary_restriction", "pattern": "gluten"}` |

---

### Dependency Types

When untriggering a beat, these dependency types are checked:

1. **Direct Prerequisite:**

   ```json
   // Beat B depends on Beat A
   {
     "id": "beat_b",
     "prerequisites": ["beat_a"]
   }
   ```

2. **Conditional Progression:**

   ```json
   // Beat C requires 2 of [A, B, D]
   {
     "id": "beat_c",
     "conditions": {
       "requires_n_of_beats": {
         "n": 2,
         "beats": ["beat_a", "beat_b", "beat_d"]
       }
     }
   }
   ```

3. **Stage Progression:**

   ```json
   // Untrigger stage 2 also untriggers stages 3+
   {
     "id": "beat_progression",
     "type": "progression",
     "stages": [1, 2, 3]
   }
   ```

4. **Chapter Unlock:**

   ```json
   // Untrigger chapter completion reverts to previous chapter
   {
     "chapter": 2,
     "unlock_criteria": {
       "type": "chapter_complete",
       "chapter_id": 1
     }
   }
   ```

---

## Changelog

### Version 1.0 - 2026-02-04

- Initial architecture document
- Four-milestone implementation plan
- Story engine enhancements specified
- API contracts defined
- Frontend real-time update strategy
- E2E test scenarios outlined

---

**Document Owner:** Justin Grover
**Architecture Review:** Pending
**Approved By:** Pending
