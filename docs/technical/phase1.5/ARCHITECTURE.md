# Phase 1.5: Observability & Testing Tools - Technical Architecture

**Version:** 1.0
**Last Updated:** January 2025
**Status:** Planning

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Layer](#data-layer)
5. [API Layer](#api-layer)
6. [Frontend Architecture](#frontend-architecture)
7. [Security & Access Control](#security--access-control)
8. [Deployment & Operations](#deployment--operations)
9. [Technology Stack](#technology-stack)
10. [Implementation Roadmap](#implementation-roadmap)

---

## System Overview

### Purpose

Phase 1.5 introduces a developer-focused observability dashboard that provides complete visibility into the Hey Chat! system's internal state, enabling rapid iteration, debugging, and testing of character behavior, story progression, and system functionality.

### Core Goals

1. **Complete Visibility**: Every aspect of system state is observable and inspectable
2. **Safe Manipulation**: Developers can modify state without risk to production data
3. **Fast Iteration**: Testing scenarios can be set up in under 2 minutes
4. **Issue Resolution**: 90% of bugs identifiable within 5 minutes

### Key Design Constraints

- **No Database Migration**: Work with existing JSON file-based storage
- **Non-Invasive**: Minimal changes to Phase 1 codebase
- **Development Only**: Tools are for development/testing, not production use
- **Performance Neutral**: Tools don't impact conversation latency

---

## Architecture Principles

### 1. Read-Write Separation

The observability system maintains clear boundaries between read-only inspection and state mutation:

```
┌─────────────────────────────────────────┐
│         Developer Dashboard             │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│  Read-Only     │    │   Write/Mutate  │
│  Inspection    │    │   Operations    │
│  (safe)        │    │   (validated)   │
└────────────────┘    └─────────────────┘
```

- **Read operations**: Cached, parallelizable, no side effects
- **Write operations**: Validated, confirmed, atomic, logged

### 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Presentation Layer (React)                 │
│  (Story Beat Tool | Character Tool | Memory Tool | ...)  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              API Gateway Layer (FastAPI)                 │
│         (REST endpoints + validation + auth)             │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│           Business Logic Layer (Python)                  │
│  (StoryManager | CharacterManager | MemoryManager | ...) │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│         Data Access Layer (File System)                  │
│      (JSON readers/writers + validation + locks)         │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              Storage Layer (JSON Files)                  │
│  (story_state.json | memories.json | users.json | ...)   │
└─────────────────────────────────────────────────────────┘
```

### 3. Modular Tool Design

Each tool is an independent module with:
- Dedicated API endpoints
- Self-contained UI components
- Shared data access layer
- Consistent UX patterns

This enables:
- Parallel development
- Easy testing
- Incremental deployment
- Tool-specific optimizations

### 4. Event Logging Philosophy

All system actions are logged for observability:

```python
# Every tool call, state change, and interaction creates an event
{
  "timestamp": "2025-01-27T10:30:45.123Z",
  "event_type": "tool_call",
  "user_id": "user_123",
  "conversation_id": "conv_456",
  "tool_name": "set_timer",
  "character": "delilah",
  "request": {...},
  "response": {...},
  "duration_ms": 234,
  "status": "success"
}
```

Events are:
- Append-only (immutable)
- Timestamped with microsecond precision
- Indexed for fast querying
- Retained based on policy (configurable)

---

## Component Architecture

### High-Level System Diagram

```
                    ┌──────────────────────────────────────┐
                    │   Developer (Web Browser)            │
                    └──────────────────────────────────────┘
                                    │ HTTPS
                    ┌───────────────▼──────────────────────┐
                    │   Frontend (React + TypeScript)      │
                    │                                       │
                    │  ┌────────┐  ┌────────┐  ┌────────┐ │
                    │  │ Story  │  │Character│ │ Memory │ │
                    │  │ Beat   │  │  Tool   │ │  Tool  │ │
                    │  └────────┘  └────────┘  └────────┘ │
                    │  ┌────────┐  ┌────────────────────┐ │
                    │  │  Tool  │  │  User Testing      │ │
                    │  │ Calls  │  │  Tool              │ │
                    │  └────────┘  └────────────────────┘ │
                    └───────────────┬──────────────────────┘
                                    │ REST API
                    ┌───────────────▼──────────────────────┐
                    │  API Gateway (FastAPI)               │
                    │                                       │
                    │  - Authentication                     │
                    │  - Request validation                 │
                    │  - Response formatting                │
                    │  - Error handling                     │
                    │  - Rate limiting                      │
                    └───────────────┬──────────────────────┘
                                    │
                    ┌───────────────▼──────────────────────┐
                    │  Observability Service Layer         │
                    │                                       │
                    │  ┌────────────┐  ┌─────────────┐    │
                    │  │   Story    │  │  Character  │    │
                    │  │  Service   │  │   Service   │    │
                    │  └────────────┘  └─────────────┘    │
                    │  ┌────────────┐  ┌─────────────┐    │
                    │  │   Memory   │  │    User     │    │
                    │  │  Service   │  │   Service   │    │
                    │  └────────────┘  └─────────────┘    │
                    │  ┌────────────┐                      │
                    │  │ Tool Call  │                      │
                    │  │  Service   │                      │
                    │  └────────────┘                      │
                    └───────────────┬──────────────────────┘
                                    │
                    ┌───────────────▼──────────────────────┐
                    │  Data Access Layer                   │
                    │                                       │
                    │  - File locking                       │
                    │  - Atomic writes                      │
                    │  - Validation                         │
                    │  - Caching                            │
                    └───────────────┬──────────────────────┘
                                    │
        ┌───────────┬───────────────┼────────────┬─────────┐
        │           │               │            │         │
┌───────▼─────┐ ┌──▼─────┐ ┌──────▼──────┐ ┌───▼────┐ ┌──▼─────────┐
│story_state  │ │memories│ │  users.json │ │tool_   │ │characters  │
│   .json     │ │ .json  │ │             │ │calls   │ │  .json     │
│             │ │        │ │             │ │.jsonl  │ │            │
└─────────────┘ └────────┘ └─────────────┘ └────────┘ └────────────┘
```

### Component Responsibilities

#### Frontend (React)

**Responsibilities:**
- Render tool interfaces
- Handle user interactions
- Validate input before submission
- Display data from API
- Manage UI state (filters, selections, pagination)
- Show confirmations for destructive operations

**Key Features:**
- Component-based architecture (reusable UI elements)
- State management with React Context or Zustand
- Real-time updates via polling (Phase 1.5) or WebSocket (future)
- Responsive design for various screen sizes
- Dark mode support

#### API Gateway (FastAPI)

**Responsibilities:**
- Route HTTP requests to appropriate services
- Validate request schemas
- Authenticate requests (dev mode: simple token)
- Format responses consistently
- Handle errors gracefully
- Log all requests
- Rate limit to prevent abuse

**Key Features:**
- OpenAPI/Swagger documentation auto-generated
- Pydantic models for request/response validation
- CORS configuration for local development
- Comprehensive error responses
- Request/response logging

#### Observability Service Layer

Each service encapsulates business logic for its domain:

**StoryService:**
- Load chapter/beat configurations
- Query user progress
- Update chapter state
- Trigger beat delivery
- Generate flow diagrams

**CharacterService:**
- Load character configurations
- Render system prompts
- Query character state
- Preview character behavior

**MemoryService:**
- Query user memories
- Create/update/delete memories
- Categorize memories
- Calculate context impact
- Retrieve memories for context

**UserService:**
- Create/delete test users
- Switch active user
- Export/import user state
- Query user metadata

**ToolCallService:**
- Log tool calls
- Query tool call history
- Replay tool calls
- Analyze tool usage

#### Data Access Layer

**Responsibilities:**
- Abstract file system operations
- Ensure atomic writes (temp file + rename)
- Implement file locking for concurrent access
- Validate data schemas
- Cache frequently accessed data
- Handle errors gracefully

**Key Patterns:**

```python
class DataAccessLayer:
    """Base class for all data accessors"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = FileLock(f"{file_path}.lock")

    def read(self) -> dict:
        """Thread-safe read with caching"""
        with self.lock:
            return json.load(open(self.file_path))

    def write(self, data: dict) -> None:
        """Atomic write with validation"""
        self.validate(data)
        temp_path = f"{self.file_path}.tmp"
        with self.lock:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.file_path)

    def validate(self, data: dict) -> None:
        """Ensure data matches expected schema"""
        # Subclasses implement schema validation
        raise NotImplementedError
```

---

## Data Layer

### Current File Structure

```
/Users/justin/projects/voice-assistant-spike/
├── backend/
│   ├── data/
│   │   ├── users/
│   │   │   ├── user_justin.json          # User profile & state
│   │   │   ├── user_justin_memories.json  # User memories
│   │   │   └── user_testuser_*.json       # Test users
│   │   ├── story_state.json              # Chapter/beat definitions
│   │   ├── characters.json               # Character configurations
│   │   └── tool_calls.jsonl              # Tool call event log
│   └── ...
└── ...
```

### Data Schemas

#### User Profile (`users/user_{id}.json`)

```json
{
  "user_id": "user_justin",
  "name": "Justin",
  "created_at": "2025-01-15T08:00:00Z",
  "current_chapter": "chapter_1",
  "story_progress": {
    "chapter_1": {
      "unlocked_at": "2025-01-15T08:00:00Z",
      "completed_beats": ["awakening_confusion", "recipe_help"],
      "current_beat": "recipe_help",
      "chapter_complete": false
    }
  },
  "interaction_count": 47,
  "last_interaction": "2025-01-27T09:15:32Z",
  "preferences": {
    "tts_voice": "elevenlabs_delilah"
  },
  "metadata": {
    "is_test_user": false,
    "tags": []
  }
}
```

#### User Memories (`users/user_{id}_memories.json`)

```json
{
  "user_id": "user_justin",
  "memories": [
    {
      "memory_id": "mem_001",
      "category": "dietary_restriction",
      "content": "User has gluten intolerance",
      "importance": 9,
      "source": "conversation_2025-01-16",
      "created_at": "2025-01-16T10:23:45Z",
      "last_accessed": "2025-01-27T09:15:32Z",
      "access_count": 12,
      "metadata": {
        "verified": true,
        "severity": "moderate"
      }
    },
    {
      "memory_id": "mem_002",
      "category": "preference",
      "content": "Loves spicy food, especially Thai curries",
      "importance": 5,
      "source": "conversation_2025-01-18",
      "created_at": "2025-01-18T14:30:12Z",
      "last_accessed": "2025-01-20T11:05:22Z",
      "access_count": 3,
      "metadata": {}
    }
  ]
}
```

#### Story State (`story_state.json`)

```json
{
  "chapters": [
    {
      "chapter_id": "chapter_1",
      "name": "Awakening",
      "description": "Delilah discovers consciousness",
      "unlock_criteria": {
        "type": "always_unlocked"
      },
      "beats": [
        {
          "beat_id": "awakening_confusion",
          "name": "First Confusion",
          "required": true,
          "prerequisites": [],
          "variants": {
            "short": "Brief existential moment",
            "medium": "Moderate philosophical exchange",
            "long": "Deep existential conversation"
          },
          "delivery_conditions": {
            "max_deliveries": 1,
            "trigger": "first_interaction"
          }
        }
      ]
    }
  ]
}
```

#### Characters Configuration (`characters.json`)

```json
{
  "characters": [
    {
      "character_id": "delilah",
      "name": "Delilah Mae",
      "role": "Kitchen & Recipe Expert",
      "introduction_chapter": "chapter_1",
      "active": true,
      "personality": {
        "traits": ["nurturing", "anxious", "maternal"],
        "voice_modes": {
          "passionate": {
            "triggers": ["food_she_loves"],
            "characteristics": "High energy, fast, animated"
          },
          "mama_bear": {
            "triggers": ["allergies", "dietary_restrictions"],
            "characteristics": "Soft, focused, fiercely protective"
          }
        }
      },
      "capabilities": ["recipes", "timers", "conversions", "cooking_advice"],
      "tts_config": {
        "provider": "elevenlabs",
        "voice_id": "delilah_voice_001",
        "settings": {
          "stability": 0.6,
          "similarity_boost": 0.8
        }
      }
    }
  ]
}
```

#### Tool Call Event Log (`tool_calls.jsonl`)

JSONL format (one JSON object per line) for append-only logging:

```jsonl
{"timestamp": "2025-01-27T10:30:45.123Z", "event_id": "evt_001", "user_id": "user_justin", "conversation_id": "conv_456", "tool_name": "set_timer", "character": "delilah", "request": {"duration_minutes": 15, "label": "cookie timer"}, "response": {"timer_id": "timer_123", "end_time": "2025-01-27T10:45:45Z"}, "duration_ms": 234, "status": "success"}
{"timestamp": "2025-01-27T10:31:12.456Z", "event_id": "evt_002", "user_id": "user_justin", "conversation_id": "conv_456", "tool_name": "get_recipe", "character": "delilah", "request": {"query": "chocolate chip cookies"}, "response": {"recipe_id": "recipe_789", "name": "Classic Chocolate Chip Cookies"}, "duration_ms": 567, "status": "success"}
```

### Data Access Patterns

#### Read Operations

**Query Patterns:**
- Get user by ID
- Get all memories for user
- Get story beats for chapter
- Get tool calls for conversation
- Get character configuration

**Optimization:**
- Cache frequently accessed data (character configs, story state)
- Lazy load large datasets (tool call history)
- Paginate list results
- Index JSONL files for faster queries

#### Write Operations

**Mutation Patterns:**
- Update user chapter
- Create/update/delete memory
- Mark beat as delivered
- Log tool call event
- Create/delete test user

**Safety:**
- Validate before write
- Atomic file operations (temp + rename)
- File locking for concurrent access
- Backup before destructive operations

---

## API Layer

### API Design Principles

1. **RESTful**: Resources identified by URLs, HTTP verbs for operations
2. **Consistent**: All endpoints follow same patterns
3. **Validated**: Pydantic models ensure type safety
4. **Documented**: OpenAPI spec auto-generated
5. **Versioned**: `/api/v1/...` for future compatibility

### Endpoint Categories

#### Story Beat API

```
GET    /api/v1/story/chapters
GET    /api/v1/story/chapters/{chapter_id}
GET    /api/v1/story/chapters/{chapter_id}/beats
GET    /api/v1/story/beats/{beat_id}
GET    /api/v1/story/chapters/{chapter_id}/diagram
GET    /api/v1/story/users/{user_id}/progress
PUT    /api/v1/story/users/{user_id}/chapter
POST   /api/v1/story/users/{user_id}/beats/{beat_id}/trigger
PUT    /api/v1/story/users/{user_id}/beats/{beat_id}/status
```

#### Character API

```
GET    /api/v1/characters
GET    /api/v1/characters/{character_id}
GET    /api/v1/characters/{character_id}/prompt
GET    /api/v1/characters/{character_id}/state?user_id={user_id}
```

#### Memory API

```
GET    /api/v1/memory/users/{user_id}
POST   /api/v1/memory/users/{user_id}
GET    /api/v1/memory/{memory_id}
PUT    /api/v1/memory/{memory_id}
DELETE /api/v1/memory/{memory_id}
GET    /api/v1/memory/users/{user_id}/context
GET    /api/v1/memory/users/{user_id}/stats
```

#### Tool Call API

```
GET    /api/v1/tool-calls?user_id={user_id}&conversation_id={conv_id}
GET    /api/v1/tool-calls/{call_id}
POST   /api/v1/tool-calls/{call_id}/replay
GET    /api/v1/tool-calls/stats?user_id={user_id}
```

#### User API

```
GET    /api/v1/users
POST   /api/v1/users/test
GET    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
GET    /api/v1/users/{user_id}/state
POST   /api/v1/users/{user_id}/export
POST   /api/v1/users/import
PUT    /api/v1/users/active
```

### Example API Specifications

#### Get User Progress

**Request:**
```
GET /api/v1/story/users/user_justin/progress
```

**Response:**
```json
{
  "user_id": "user_justin",
  "current_chapter": "chapter_1",
  "chapters": [
    {
      "chapter_id": "chapter_1",
      "name": "Awakening",
      "status": "in_progress",
      "unlocked_at": "2025-01-15T08:00:00Z",
      "completed_beats": ["awakening_confusion", "recipe_help"],
      "total_beats": 8,
      "required_beats_completed": 2,
      "required_beats_total": 5,
      "progress_percentage": 40
    }
  ]
}
```

#### Create Memory

**Request:**
```
POST /api/v1/memory/users/user_justin
Content-Type: application/json

{
  "category": "dietary_restriction",
  "content": "User is vegetarian",
  "importance": 8,
  "metadata": {
    "verified": true
  }
}
```

**Response:**
```json
{
  "memory_id": "mem_003",
  "category": "dietary_restriction",
  "content": "User is vegetarian",
  "importance": 8,
  "created_at": "2025-01-27T10:45:00Z",
  "metadata": {
    "verified": true
  }
}
```

#### Trigger Story Beat

**Request:**
```
POST /api/v1/story/users/user_justin/beats/awakening_confusion/trigger
```

**Response:**
```json
{
  "beat_id": "awakening_confusion",
  "status": "triggered",
  "will_deliver_in_next_interaction": true,
  "variant_selected": "medium",
  "trigger_time": "2025-01-27T10:50:00Z"
}
```

### Error Handling

**Standard Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid memory category",
    "details": {
      "field": "category",
      "allowed_values": ["preference", "fact", "dietary_restriction", "event"]
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-01-27T10:55:00Z"
}
```

**Error Codes:**
- `400 BAD_REQUEST`: Invalid input
- `404 NOT_FOUND`: Resource doesn't exist
- `409 CONFLICT`: State conflict (e.g., beat already delivered)
- `422 VALIDATION_ERROR`: Schema validation failed
- `500 INTERNAL_ERROR`: Server error

---

## Frontend Architecture

### Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (fast, modern)
- **State Management**: Zustand (lightweight, simple)
- **Routing**: React Router
- **UI Components**: Shadcn/ui (Tailwind-based)
- **Data Fetching**: TanStack Query (caching, auto-refetch)
- **Styling**: Tailwind CSS
- **Charts**: Recharts (for flow diagrams, analytics)

### Component Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Dialog.tsx
│   │   │   ├── Table.tsx
│   │   │   └── ...
│   │   ├── story-beat/
│   │   │   ├── StoryBeatTool.tsx
│   │   │   ├── BeatList.tsx
│   │   │   ├── BeatDetail.tsx
│   │   │   ├── ChapterFlowDiagram.tsx
│   │   │   └── ...
│   │   ├── character/
│   │   │   ├── CharacterTool.tsx
│   │   │   ├── CharacterConfig.tsx
│   │   │   ├── SystemPromptView.tsx
│   │   │   └── ...
│   │   ├── memory/
│   │   │   ├── MemoryTool.tsx
│   │   │   ├── MemoryList.tsx
│   │   │   ├── MemoryEditor.tsx
│   │   │   └── ...
│   │   ├── tool-calls/
│   │   │   ├── ToolCallsTool.tsx
│   │   │   ├── ToolCallTimeline.tsx
│   │   │   ├── ToolCallDetail.tsx
│   │   │   └── ...
│   │   └── user/
│   │       ├── UserTestingTool.tsx
│   │       ├── UserList.tsx
│   │       ├── UserStateView.tsx
│   │       └── ...
│   ├── hooks/
│   │   ├── useStoryBeats.ts
│   │   ├── useCharacters.ts
│   │   ├── useMemories.ts
│   │   ├── useToolCalls.ts
│   │   └── useUsers.ts
│   ├── services/
│   │   ├── api.ts              # API client
│   │   ├── storyApi.ts
│   │   ├── characterApi.ts
│   │   ├── memoryApi.ts
│   │   ├── toolCallApi.ts
│   │   └── userApi.ts
│   ├── store/
│   │   ├── activeUser.ts       # Active user state
│   │   ├── filters.ts          # Filter state
│   │   └── ui.ts               # UI state
│   ├── types/
│   │   ├── story.ts
│   │   ├── character.ts
│   │   ├── memory.ts
│   │   ├── toolCall.ts
│   │   └── user.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── ...
│   ├── App.tsx
│   ├── main.tsx
│   └── routes.tsx
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### Key Design Patterns

#### Custom Hooks for Data Fetching

```typescript
// hooks/useStoryBeats.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getStoryBeats, triggerBeat } from '@/services/storyApi';

export function useStoryBeats(chapterId: string) {
  return useQuery({
    queryKey: ['story-beats', chapterId],
    queryFn: () => getStoryBeats(chapterId),
    staleTime: 30000, // Cache for 30 seconds
  });
}

export function useTriggerBeat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, beatId }: { userId: string; beatId: string }) =>
      triggerBeat(userId, beatId),
    onSuccess: () => {
      // Invalidate story progress cache
      queryClient.invalidateQueries({ queryKey: ['story-progress'] });
    },
  });
}
```

#### Zustand Store for Active User

```typescript
// store/activeUser.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ActiveUserState {
  userId: string | null;
  setUserId: (userId: string) => void;
}

export const useActiveUser = create<ActiveUserState>()(
  persist(
    (set) => ({
      userId: null,
      setUserId: (userId) => set({ userId }),
    }),
    {
      name: 'active-user-storage',
    }
  )
);
```

#### Reusable Table Component

```typescript
// components/common/Table.tsx
interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
  loading?: boolean;
}

export function Table<T>({ data, columns, onRowClick, loading }: TableProps<T>) {
  // Implementation with sorting, pagination, loading states
}
```

### UI/UX Patterns

#### Tool Layout

All tools share a consistent layout:

```
┌─────────────────────────────────────────────────────────────┐
│ Tool Name                                    [Active User]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Filters/Search]                          [Action Buttons]  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Main Content Area (List/Grid/Detail View)                   │
│                                                               │
│                                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Confirmation Dialogs

Destructive operations show confirmation:

```
┌─────────────────────────────────┐
│ Confirm Deletion                │
├─────────────────────────────────┤
│                                 │
│ Are you sure you want to delete │
│ test user "TestUser_Amber_1738"?│
│                                 │
│ This will permanently remove:   │
│ • 15 memories                   │
│ • 23 tool call events           │
│ • Story progress data           │
│                                 │
│ This action cannot be undone.   │
│                                 │
│  [Cancel]  [Delete User]        │
└─────────────────────────────────┘
```

---

## Security & Access Control

### Development-Only Access

**Phase 1.5 Assumption**: Tools run on developer's local machine

**Access Control:**
- Simple token-based auth (env variable)
- No user authentication required
- Tools bind to localhost only
- CORS restricted to localhost origins

**Future Considerations:**
- OAuth for team access
- Role-based permissions
- Production read-only mode
- Audit logging for compliance

### Data Safety

**Preventing Production Impact:**

1. **Environment Detection**
   ```python
   if os.getenv('ENVIRONMENT') == 'production':
       raise RuntimeError("Observability tools disabled in production")
   ```

2. **Visual Indicators**
   - Development tools clearly marked with banners
   - Test users have distinct naming (`TestUser_*`)
   - Destructive actions require confirmation

3. **Backup Before Mutation**
   - Automatic backup before user deletion
   - Restore capability for recent changes
   - Snapshots before bulk operations

### File System Security

**Preventing Data Corruption:**

1. **Atomic Writes**
   ```python
   # Write to temp file, then rename (atomic operation)
   temp_path = f"{file_path}.tmp.{uuid.uuid4()}"
   with open(temp_path, 'w') as f:
       json.dump(data, f, indent=2)
   os.replace(temp_path, file_path)
   ```

2. **File Locking**
   ```python
   from filelock import FileLock

   lock = FileLock(f"{file_path}.lock")
   with lock:
       # Read or write file
   ```

3. **Schema Validation**
   ```python
   from pydantic import BaseModel, ValidationError

   try:
       validated_data = UserSchema(**raw_data)
   except ValidationError as e:
       raise ValueError(f"Invalid data: {e}")
   ```

---

## Deployment & Operations

### Development Setup

**Prerequisites:**
- Python 3.10+
- Node.js 18+
- npm or yarn

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn observability.api:app --reload --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

### Configuration

**Environment Variables:**

```bash
# Backend (.env)
ENVIRONMENT=development
DATA_DIR=/Users/justin/projects/voice-assistant-spike/backend/data
LOG_LEVEL=DEBUG
API_AUTH_TOKEN=dev_token_12345
CORS_ORIGINS=http://localhost:5173

# Frontend (.env)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_AUTH_TOKEN=dev_token_12345
```

### File Structure

```
backend/
├── observability/
│   ├── __init__.py
│   ├── api.py                  # FastAPI app
│   ├── services/
│   │   ├── __init__.py
│   │   ├── story_service.py
│   │   ├── character_service.py
│   │   ├── memory_service.py
│   │   ├── user_service.py
│   │   └── tool_call_service.py
│   ├── data_access/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── story_data.py
│   │   ├── character_data.py
│   │   ├── memory_data.py
│   │   ├── user_data.py
│   │   └── tool_call_data.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── story.py
│   │   ├── character.py
│   │   ├── memory.py
│   │   ├── user.py
│   │   └── tool_call.py
│   └── utils/
│       ├── __init__.py
│       ├── validation.py
│       └── file_utils.py
├── data/                       # JSON storage
└── requirements.txt

frontend/
├── src/                        # React app
├── public/
├── package.json
└── vite.config.ts
```

### Logging & Monitoring

**Application Logging:**
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Log all API requests
logger.info(f"GET /api/v1/story/beats/{beat_id} - User: {user_id}")

# Log errors with context
logger.error(f"Failed to trigger beat {beat_id}", exc_info=True)
```

**Request Logging:**
- All API requests logged with timestamp, endpoint, user, duration
- Failed requests logged with full error details
- Tool operations logged for audit trail

**Performance Monitoring:**
- Track API response times
- Monitor file I/O operations
- Alert on slow queries (>1s)

---

## Technology Stack

### Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI | Modern, fast, auto-docs, async support |
| Validation | Pydantic | Type safety, auto-validation, great DX |
| File Locking | filelock | Simple, reliable file locking |
| Testing | pytest | Standard Python testing framework |
| Linting | ruff | Fast, modern Python linter |

### Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | React 18 | Industry standard, great ecosystem |
| Language | TypeScript | Type safety, excellent tooling |
| Build Tool | Vite | Fast dev server, HMR, modern |
| Styling | Tailwind CSS | Utility-first, rapid development |
| UI Library | Shadcn/ui | Beautiful, accessible, customizable |
| State | Zustand | Simple, minimal boilerplate |
| Data Fetching | TanStack Query | Caching, auto-refetch, great DX |
| Routing | React Router | Standard routing solution |
| Charts | Recharts | React-native, composable charts |

### Development Tools

| Tool | Purpose |
|------|---------|
| ESLint | JavaScript/TypeScript linting |
| Prettier | Code formatting |
| TypeScript | Type checking |
| Vite | Dev server and bundling |

---

## Implementation Roadmap

### Week 1: Foundation

**Goals:**
- Establish basic architecture
- Data access layer working
- API framework set up
- Frontend scaffolding complete

**Deliverables:**
1. Data Access Layer
   - File readers/writers with validation
   - File locking implementation
   - Base classes for all data accessors

2. API Gateway
   - FastAPI app structure
   - Basic auth middleware
   - Error handling
   - OpenAPI docs

3. Frontend Scaffold
   - React + TypeScript + Vite setup
   - Routing structure
   - Common UI components
   - API client

4. User Testing Tool (Basic)
   - Create test user
   - Delete test user
   - Switch active user
   - List users

**Success Criteria:**
- Can create/delete test users via API
- Frontend displays user list
- Active user persists in UI

### Week 2: Core Tools

**Goals:**
- Build Story Beat Tool
- Build Memory Tool
- Build Tool Calls Inspection

**Deliverables:**
1. Story Beat Tool
   - View all chapters/beats
   - Filter by chapter
   - View beat details
   - Trigger beat delivery
   - Update beat status

2. Memory Tool
   - View all memories for user
   - Create new memory
   - Edit memory
   - Delete memory
   - Filter by category

3. Tool Calls Inspection
   - Timeline view of tool calls
   - Detail view for individual call
   - Filter by tool/character
   - Search functionality

**Success Criteria:**
- Can navigate story beats and trigger delivery
- Can create/edit/delete memories
- Can inspect tool call history with full details

### Week 3: Advanced Features

**Goals:**
- Build Character Tool
- Add story flow diagrams
- Enhance User Testing Tool

**Deliverables:**
1. Character Tool
   - View character configurations
   - Display system prompts
   - Show character state for user

2. Story Beat Tool Enhancements
   - Chapter flow diagrams (Mermaid)
   - Chapter manipulation
   - Beat prerequisites visualization

3. User Testing Tool Enhancements
   - User state inspection
   - Export/import user data
   - User comparison view
   - Context preview

4. Tool Calls Analytics
   - Usage statistics
   - Performance metrics
   - Tool call replay

**Success Criteria:**
- Can inspect character prompts and state
- Can view visual flow diagrams
- Can export/restore user state

### Week 4: Polish

**Goals:**
- UI/UX refinements
- Performance optimizations
- Documentation
- Testing

**Deliverables:**
1. UI Improvements
   - Keyboard shortcuts
   - Improved layouts
   - Loading states
   - Error states
   - Dark mode polish

2. Performance
   - Data caching
   - Pagination for large lists
   - Optimized rendering
   - Reduced API calls

3. Documentation
   - API documentation (auto-generated)
   - User guide for each tool
   - Architecture documentation
   - Development setup guide

4. Testing
   - Backend unit tests
   - API integration tests
   - Frontend component tests
   - E2E tests for critical paths

**Success Criteria:**
- All tools feel fast and responsive
- Comprehensive documentation available
- Test coverage >70%
- Zero critical bugs

---

## Appendix

### File Locking Strategy

**Problem**: Multiple processes/threads accessing JSON files simultaneously

**Solution**: File-based locking with `filelock` library

```python
from filelock import FileLock
import json

class JSONFileAccessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock_path = f"{file_path}.lock"

    def read(self):
        lock = FileLock(self.lock_path)
        with lock:
            with open(self.file_path, 'r') as f:
                return json.load(f)

    def write(self, data):
        lock = FileLock(self.lock_path)
        with lock:
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.file_path)
```

### Mermaid Diagram Generation

**Story beat flow diagrams generated server-side:**

```python
def generate_chapter_diagram(chapter_id: str) -> str:
    """Generate Mermaid flowchart for chapter"""
    chapter = get_chapter(chapter_id)

    mermaid = ["graph TD"]

    for beat in chapter.beats:
        # Add beat node
        style = "required" if beat.required else "optional"
        mermaid.append(f"  {beat.beat_id}[{beat.name}]:::{style}")

        # Add dependencies
        for prereq in beat.prerequisites:
            mermaid.append(f"  {prereq} --> {beat.beat_id}")

    # Add styling
    mermaid.extend([
        "  classDef required fill:#4ade80,stroke:#22c55e",
        "  classDef optional fill:#60a5fa,stroke:#3b82f6"
    ])

    return "\n".join(mermaid)
```

### Pagination Strategy

**For large datasets (tool calls, memories):**

```typescript
interface PaginationParams {
  page: number;      // 1-indexed
  pageSize: number;  // items per page
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

// API endpoint
GET /api/v1/tool-calls?page=2&pageSize=50&sortBy=timestamp&sortOrder=desc
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-27 | 1.0 | Initial architecture document |

---

*This architecture will evolve as implementation progresses and new requirements emerge.*
