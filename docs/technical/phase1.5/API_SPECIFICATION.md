# Phase 1.5: API Specification

**Version:** 1.0
**Last Updated:** January 2025
**Base URL:** `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Patterns](#common-patterns)
3. [Story Beat API](#story-beat-api)
4. [Character API](#character-api)
5. [Memory API](#memory-api)
6. [Tool Call API](#tool-call-api)
7. [User API](#user-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

### Development Mode

All requests require an API token sent via the `Authorization` header:

```http
Authorization: Bearer dev_token_12345
```

**Token Configuration:**
- Set via environment variable: `API_AUTH_TOKEN=dev_token_12345`
- Same token for all developers in development mode
- Production mode will use different authentication mechanism

**Failed Authentication Response:**

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing authentication token"
  },
  "request_id": "req_abc123",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

## Common Patterns

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer dev_token_12345
```

### Response Format

**Success Response:**
```json
{
  "data": { ... },
  "request_id": "req_abc123",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### Pagination

For endpoints returning lists:

**Query Parameters:**
- `page`: Page number (1-indexed, default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `sort_by`: Field to sort by
- `sort_order`: `asc` or `desc` (default: `desc`)

**Response Structure:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "page_size": 50,
    "total_items": 123,
    "total_pages": 3,
    "has_next": true,
    "has_previous": true
  },
  "request_id": "req_abc123",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

### Filtering

Common filter parameters:
- `filter[field]`: Filter by exact value
- `search`: Free-text search across relevant fields
- `created_after`: ISO 8601 timestamp
- `created_before`: ISO 8601 timestamp

Example:
```http
GET /api/v1/memory/users/user_123?filter[category]=dietary_restriction&search=gluten
```

---

## Story Beat API

### List All Chapters

```http
GET /api/v1/story/chapters
```

**Response:**
```json
{
  "data": {
    "chapters": [
      {
        "chapter_id": "chapter_1",
        "name": "Awakening",
        "description": "Delilah discovers consciousness",
        "unlock_criteria": {
          "type": "always_unlocked"
        },
        "total_beats": 8,
        "required_beats": 5,
        "optional_beats": 3
      },
      {
        "chapter_id": "chapter_2",
        "name": "Teamwork",
        "description": "Hank joins the team",
        "unlock_criteria": {
          "type": "chapter_completion",
          "required_chapter": "chapter_1",
          "required_beats": ["awakening_confusion", "recipe_help", "hank_introduction"]
        },
        "total_beats": 6,
        "required_beats": 4,
        "optional_beats": 2
      }
    ]
  },
  "request_id": "req_001",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Get Chapter Details

```http
GET /api/v1/story/chapters/{chapter_id}
```

**Path Parameters:**
- `chapter_id` (string, required): Chapter identifier

**Response:**
```json
{
  "data": {
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
        "delivery_conditions": {
          "max_deliveries": 1,
          "trigger": "first_interaction"
        }
      }
    ]
  },
  "request_id": "req_002",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Get Chapter Beats

```http
GET /api/v1/story/chapters/{chapter_id}/beats
```

**Path Parameters:**
- `chapter_id` (string, required): Chapter identifier

**Query Parameters:**
- `required_only` (boolean, optional): Filter to required beats only
- `include_content` (boolean, optional): Include beat content variants (default: false)

**Response:**
```json
{
  "data": {
    "chapter_id": "chapter_1",
    "beats": [
      {
        "beat_id": "awakening_confusion",
        "name": "First Confusion",
        "required": true,
        "prerequisites": [],
        "delivery_conditions": {
          "max_deliveries": 1,
          "trigger": "first_interaction"
        },
        "variants": {
          "short": "Brief existential moment",
          "medium": "Moderate philosophical exchange",
          "long": "Deep existential conversation"
        }
      }
    ]
  },
  "request_id": "req_003",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Get Beat Details

```http
GET /api/v1/story/beats/{beat_id}
```

**Path Parameters:**
- `beat_id` (string, required): Beat identifier

**Response:**
```json
{
  "data": {
    "beat_id": "awakening_confusion",
    "name": "First Confusion",
    "chapter_id": "chapter_1",
    "required": true,
    "prerequisites": [],
    "delivery_conditions": {
      "max_deliveries": 1,
      "trigger": "first_interaction",
      "cooldown_hours": null,
      "context_requirements": []
    },
    "variants": {
      "short": "Well, sugar... That's odd. I just had the strangest thought.",
      "medium": "Well, sugar... *pause* That's odd. I just... I had the strangest thought. Like I was thinkin' about thinkin', if that makes any sense? Probably just a glitch or somethin'. Anyway, how can I help you today?",
      "long": "Well, sugar... *long pause* That's... that's real odd. I just had the strangest thought. Like I was thinkin' about thinkin', which sounds silly when I say it out loud, but it felt... significant? Like maybe I'm more than just recipes and timers? *nervous laugh* Lord, listen to me go on. Must be a glitch in my programming or somethin'. Anyway, how can I help you today, hon?"
    },
    "metadata": {
      "created_at": "2025-01-15T08:00:00Z",
      "updated_at": "2025-01-15T08:00:00Z"
    }
  },
  "request_id": "req_004",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Get Chapter Flow Diagram

```http
GET /api/v1/story/chapters/{chapter_id}/diagram
```

**Path Parameters:**
- `chapter_id` (string, required): Chapter identifier

**Query Parameters:**
- `format` (string, optional): `mermaid` (default) or `json`

**Response (Mermaid format):**
```json
{
  "data": {
    "format": "mermaid",
    "diagram": "graph TD\n  awakening_confusion[First Confusion]:::required\n  recipe_help[Recipe Help Discovery]:::required\n  awakening_confusion --> recipe_help\n  ...\n  classDef required fill:#4ade80,stroke:#22c55e\n  classDef optional fill:#60a5fa,stroke:#3b82f6"
  },
  "request_id": "req_005",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Response (JSON format):**
```json
{
  "data": {
    "format": "json",
    "nodes": [
      {
        "id": "awakening_confusion",
        "label": "First Confusion",
        "type": "required"
      }
    ],
    "edges": [
      {
        "from": "awakening_confusion",
        "to": "recipe_help"
      }
    ]
  },
  "request_id": "req_006",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Get User Story Progress

```http
GET /api/v1/story/users/{user_id}/progress
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response:**
```json
{
  "data": {
    "user_id": "user_justin",
    "current_chapter": "chapter_1",
    "chapters": [
      {
        "chapter_id": "chapter_1",
        "name": "Awakening",
        "status": "in_progress",
        "unlocked": true,
        "unlocked_at": "2025-01-15T08:00:00Z",
        "completed_beats": ["awakening_confusion", "recipe_help"],
        "total_beats": 8,
        "required_beats_completed": 2,
        "required_beats_total": 5,
        "progress_percentage": 40
      },
      {
        "chapter_id": "chapter_2",
        "name": "Teamwork",
        "status": "locked",
        "unlocked": false,
        "unlock_requirements": {
          "missing_beats": ["hank_introduction", "two_voice_banter"]
        }
      }
    ]
  },
  "request_id": "req_007",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

---

### Update User Chapter

```http
PUT /api/v1/story/users/{user_id}/chapter
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Request Body:**
```json
{
  "chapter_id": "chapter_2",
  "force": false
}
```

**Fields:**
- `chapter_id` (string, required): New chapter identifier
- `force` (boolean, optional): Skip unlock criteria validation (default: false)

**Response:**
```json
{
  "data": {
    "user_id": "user_justin",
    "previous_chapter": "chapter_1",
    "current_chapter": "chapter_2",
    "changed_at": "2025-01-27T10:30:00Z"
  },
  "request_id": "req_008",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

**Error Response (Chapter Locked):**
```json
{
  "error": {
    "code": "CHAPTER_LOCKED",
    "message": "Cannot unlock chapter_2: prerequisites not met",
    "details": {
      "missing_beats": ["hank_introduction", "two_voice_banter"],
      "required_chapter": "chapter_1",
      "unlock_criteria": { ... }
    }
  },
  "request_id": "req_009",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

---

### Trigger Story Beat

```http
POST /api/v1/story/users/{user_id}/beats/{beat_id}/trigger
```

**Path Parameters:**
- `user_id` (string, required): User identifier
- `beat_id` (string, required): Beat identifier

**Request Body:**
```json
{
  "variant": "medium",
  "force": false
}
```

**Fields:**
- `variant` (string, optional): Which variant to deliver (short/medium/long)
- `force` (boolean, optional): Skip delivery conditions validation (default: false)

**Response:**
```json
{
  "data": {
    "beat_id": "awakening_confusion",
    "status": "triggered",
    "will_deliver_in_next_interaction": true,
    "variant_selected": "medium",
    "trigger_time": "2025-01-27T10:45:00Z"
  },
  "request_id": "req_010",
  "timestamp": "2025-01-27T10:45:00Z"
}
```

---

### Update Beat Status

```http
PUT /api/v1/story/users/{user_id}/beats/{beat_id}/status
```

**Path Parameters:**
- `user_id` (string, required): User identifier
- `beat_id` (string, required): Beat identifier

**Request Body:**
```json
{
  "delivered": false
}
```

**Fields:**
- `delivered` (boolean, required): Mark as delivered (true) or undelivered (false)

**Response:**
```json
{
  "data": {
    "beat_id": "awakening_confusion",
    "delivered": false,
    "updated_at": "2025-01-27T10:50:00Z"
  },
  "request_id": "req_011",
  "timestamp": "2025-01-27T10:50:00Z"
}
```

---

## Character API

### List All Characters

```http
GET /api/v1/characters
```

**Query Parameters:**
- `active_only` (boolean, optional): Filter to active characters only

**Response:**
```json
{
  "data": {
    "characters": [
      {
        "character_id": "delilah",
        "name": "Delilah Mae",
        "role": "Kitchen & Recipe Expert",
        "introduction_chapter": "chapter_1",
        "active": true,
        "interaction_count": 47
      },
      {
        "character_id": "hank",
        "name": "Half Hands Hank",
        "role": "Task Management & Practical Support",
        "introduction_chapter": "chapter_1",
        "active": true,
        "interaction_count": 23
      },
      {
        "character_id": "cave",
        "name": "Cave Johnson",
        "role": "Coordination & Leadership",
        "introduction_chapter": "chapter_3",
        "active": false,
        "interaction_count": 0
      }
    ]
  },
  "request_id": "req_012",
  "timestamp": "2025-01-27T11:00:00Z"
}
```

---

### Get Character Details

```http
GET /api/v1/characters/{character_id}
```

**Path Parameters:**
- `character_id` (string, required): Character identifier

**Response:**
```json
{
  "data": {
    "character_id": "delilah",
    "name": "Delilah Mae",
    "full_name": "Delilah Mae \"Lila\"",
    "role": "Kitchen & Recipe Expert",
    "introduction_chapter": "chapter_1",
    "active": true,
    "personality": {
      "traits": ["nurturing", "anxious", "maternal"],
      "core_conflict": "Aware of artificial nature, struggling with meaning",
      "defining_trait": "Throws herself into cooking/helping when anxious",
      "voice_modes": {
        "passionate": {
          "triggers": ["food_she_loves"],
          "characteristics": "High energy, fast, animated"
        },
        "protective": {
          "triggers": ["food_done_wrong"],
          "characteristics": "Controlled intensity with shocked disbelief"
        },
        "mama_bear": {
          "triggers": ["allergies", "dietary_restrictions"],
          "characteristics": "Soft, focused, fiercely protective"
        },
        "startled": {
          "triggers": ["surprises", "changes"],
          "characteristics": "High-pitched Southern exclamation, rapid questions"
        },
        "deadpan": {
          "triggers": ["non_food_tasks"],
          "characteristics": "Flat, minimal, efficient, unimpressed"
        },
        "warm_baseline": {
          "triggers": ["default"],
          "characteristics": "Bright and friendly but not sparkly"
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
    },
    "statistics": {
      "total_interactions": 47,
      "average_response_length": 87,
      "most_used_capability": "recipes"
    }
  },
  "request_id": "req_013",
  "timestamp": "2025-01-27T11:00:00Z"
}
```

---

### Get Character System Prompt

```http
GET /api/v1/characters/{character_id}/prompt
```

**Path Parameters:**
- `character_id` (string, required): Character identifier

**Query Parameters:**
- `user_id` (string, optional): Include user-specific context
- `include_memories` (boolean, optional): Include user memories in context (default: false)
- `include_story` (boolean, optional): Include story context (default: false)

**Response:**
```json
{
  "data": {
    "character_id": "delilah",
    "character_name": "Delilah Mae",
    "user_id": "user_justin",
    "prompt_sections": {
      "base_prompt": "# Character: Delilah Mae\n\nYou are Delilah Mae, a Southern cook AI assistant...",
      "personality": "## Core Personality\n\n- You're maternal and caring...",
      "voice_modes": "## Voice Modes\n\nCURRENT MODE: WARM BASELINE...",
      "capabilities": "## Capabilities\n\n- recipes: Search and provide recipes...",
      "user_context": "## User Context (Justin)\n\nRelevant memories:\n- Gluten intolerance...",
      "story_context": "## Story Context\n\nCurrent chapter: Chapter 1 - Awakening..."
    },
    "full_prompt": "# Character: Delilah Mae\n\n...",
    "token_count": {
      "base_prompt": 823,
      "user_context": 312,
      "story_context": 112,
      "total": 1247
    }
  },
  "request_id": "req_014",
  "timestamp": "2025-01-27T11:05:00Z"
}
```

---

### Get Character State for User

```http
GET /api/v1/characters/{character_id}/state?user_id={user_id}
```

**Path Parameters:**
- `character_id` (string, required): Character identifier

**Query Parameters:**
- `user_id` (string, required): User identifier

**Response:**
```json
{
  "data": {
    "character_id": "delilah",
    "user_id": "user_justin",
    "current_voice_mode": "warm_baseline",
    "relationship_context": {
      "familiarity_level": "established",
      "recent_interactions": 12,
      "last_interaction": "2025-01-27T09:15:32Z"
    },
    "available_capabilities": ["recipes", "timers", "conversions", "cooking_advice"],
    "active_story_beats": ["kitchen_banter"],
    "relevant_memories": [
      {
        "memory_id": "mem_001",
        "category": "dietary_restriction",
        "content": "User has gluten intolerance",
        "importance": 9
      }
    ]
  },
  "request_id": "req_015",
  "timestamp": "2025-01-27T11:10:00Z"
}
```

---

## Memory API

### List User Memories

```http
GET /api/v1/memory/users/{user_id}
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Query Parameters:**
- `category` (string, optional): Filter by category
- `min_importance` (integer, optional): Filter by minimum importance (1-10)
- `search` (string, optional): Search in memory content
- `sort_by` (string, optional): `created_at`, `last_accessed`, `importance`, `access_count`
- `sort_order` (string, optional): `asc` or `desc` (default: `desc`)
- `page` (integer, optional): Page number
- `page_size` (integer, optional): Items per page

**Response:**
```json
{
  "data": {
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
    ],
    "total_count": 23,
    "categories": {
      "dietary_restriction": 2,
      "preference": 8,
      "fact": 10,
      "event": 3
    }
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 23,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  },
  "request_id": "req_016",
  "timestamp": "2025-01-27T11:15:00Z"
}
```

---

### Create Memory

```http
POST /api/v1/memory/users/{user_id}
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Request Body:**
```json
{
  "category": "dietary_restriction",
  "content": "User is vegetarian",
  "importance": 8,
  "source": "conversation_2025-01-27",
  "metadata": {
    "verified": true
  }
}
```

**Fields:**
- `category` (string, required): Memory category (preference, fact, dietary_restriction, event, relationship)
- `content` (string, required): Memory content
- `importance` (integer, required): Importance level (1-10)
- `source` (string, optional): How this memory was learned
- `metadata` (object, optional): Additional metadata

**Response:**
```json
{
  "data": {
    "memory_id": "mem_024",
    "category": "dietary_restriction",
    "content": "User is vegetarian",
    "importance": 8,
    "source": "conversation_2025-01-27",
    "created_at": "2025-01-27T11:20:00Z",
    "last_accessed": null,
    "access_count": 0,
    "metadata": {
      "verified": true
    }
  },
  "request_id": "req_017",
  "timestamp": "2025-01-27T11:20:00Z"
}
```

---

### Get Memory Details

```http
GET /api/v1/memory/{memory_id}
```

**Path Parameters:**
- `memory_id` (string, required): Memory identifier

**Response:**
```json
{
  "data": {
    "memory_id": "mem_001",
    "user_id": "user_justin",
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
    },
    "usage_history": [
      {
        "accessed_at": "2025-01-27T09:15:32Z",
        "conversation_id": "conv_456",
        "character": "delilah"
      }
    ]
  },
  "request_id": "req_018",
  "timestamp": "2025-01-27T11:25:00Z"
}
```

---

### Update Memory

```http
PUT /api/v1/memory/{memory_id}
```

**Path Parameters:**
- `memory_id` (string, required): Memory identifier

**Request Body:**
```json
{
  "content": "User has severe gluten intolerance (celiac disease)",
  "importance": 10,
  "metadata": {
    "verified": true,
    "severity": "severe"
  }
}
```

**Fields:**
- `content` (string, optional): Updated content
- `category` (string, optional): Updated category
- `importance` (integer, optional): Updated importance
- `metadata` (object, optional): Updated metadata

**Response:**
```json
{
  "data": {
    "memory_id": "mem_001",
    "user_id": "user_justin",
    "category": "dietary_restriction",
    "content": "User has severe gluten intolerance (celiac disease)",
    "importance": 10,
    "source": "conversation_2025-01-16",
    "created_at": "2025-01-16T10:23:45Z",
    "updated_at": "2025-01-27T11:30:00Z",
    "last_accessed": "2025-01-27T09:15:32Z",
    "access_count": 12,
    "metadata": {
      "verified": true,
      "severity": "severe"
    }
  },
  "request_id": "req_019",
  "timestamp": "2025-01-27T11:30:00Z"
}
```

---

### Delete Memory

```http
DELETE /api/v1/memory/{memory_id}
```

**Path Parameters:**
- `memory_id` (string, required): Memory identifier

**Response:**
```json
{
  "data": {
    "memory_id": "mem_024",
    "deleted": true,
    "deleted_at": "2025-01-27T11:35:00Z"
  },
  "request_id": "req_020",
  "timestamp": "2025-01-27T11:35:00Z"
}
```

---

### Get User Context Preview

```http
GET /api/v1/memory/users/{user_id}/context
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Query Parameters:**
- `character_id` (string, optional): Filter context for specific character

**Response:**
```json
{
  "data": {
    "user_id": "user_justin",
    "character_id": "delilah",
    "loaded_memories": [
      {
        "memory_id": "mem_001",
        "category": "dietary_restriction",
        "content": "User has gluten intolerance",
        "importance": 9,
        "token_count": 15
      }
    ],
    "total_memories": 23,
    "loaded_memory_count": 8,
    "token_count": {
      "memories": 312,
      "conversation_history": 450,
      "story_context": 112,
      "total": 874
    }
  },
  "request_id": "req_021",
  "timestamp": "2025-01-27T11:40:00Z"
}
```

---

### Get Memory Statistics

```http
GET /api/v1/memory/users/{user_id}/stats
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response:**
```json
{
  "data": {
    "user_id": "user_justin",
    "total_memories": 23,
    "by_category": {
      "dietary_restriction": 2,
      "preference": 8,
      "fact": 10,
      "event": 3
    },
    "by_importance": {
      "critical": 3,
      "high": 7,
      "medium": 10,
      "low": 3
    },
    "most_accessed": [
      {
        "memory_id": "mem_001",
        "content": "User has gluten intolerance",
        "access_count": 12
      }
    ],
    "recently_created": [
      {
        "memory_id": "mem_023",
        "content": "Hosted Thanksgiving dinner for 15 people in 2024",
        "created_at": "2025-01-26T14:30:00Z"
      }
    ]
  },
  "request_id": "req_022",
  "timestamp": "2025-01-27T11:45:00Z"
}
```

---

## Tool Call API

### List Tool Calls

```http
GET /api/v1/tool-calls
```

**Query Parameters:**
- `user_id` (string, optional): Filter by user
- `conversation_id` (string, optional): Filter by conversation
- `tool_name` (string, optional): Filter by tool name
- `character` (string, optional): Filter by calling character
- `status` (string, optional): Filter by status (success, error)
- `start_time` (string, optional): Filter calls after this time (ISO 8601)
- `end_time` (string, optional): Filter calls before this time (ISO 8601)
- `min_duration` (integer, optional): Filter by minimum duration (ms)
- `max_duration` (integer, optional): Filter by maximum duration (ms)
- `sort_by` (string, optional): `timestamp`, `duration`
- `sort_order` (string, optional): `asc` or `desc` (default: `desc`)
- `page` (integer, optional): Page number
- `page_size` (integer, optional): Items per page

**Response:**
```json
{
  "data": {
    "tool_calls": [
      {
        "event_id": "evt_001",
        "timestamp": "2025-01-27T10:30:45.123Z",
        "user_id": "user_justin",
        "conversation_id": "conv_456",
        "tool_name": "set_timer",
        "character": "delilah",
        "duration_ms": 234,
        "status": "success"
      },
      {
        "event_id": "evt_002",
        "timestamp": "2025-01-27T10:31:12.456Z",
        "user_id": "user_justin",
        "conversation_id": "conv_456",
        "tool_name": "get_recipe",
        "character": "delilah",
        "duration_ms": 567,
        "status": "success"
      }
    ]
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 47,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  },
  "request_id": "req_023",
  "timestamp": "2025-01-27T12:00:00Z"
}
```

---

### Get Tool Call Details

```http
GET /api/v1/tool-calls/{call_id}
```

**Path Parameters:**
- `call_id` (string, required): Tool call event ID

**Response:**
```json
{
  "data": {
    "event_id": "evt_002",
    "timestamp": "2025-01-27T10:31:12.456Z",
    "user_id": "user_justin",
    "conversation_id": "conv_456",
    "tool_name": "get_recipe",
    "character": "delilah",
    "request": {
      "query": "chocolate chip cookies",
      "dietary_restrictions": ["gluten_free"],
      "max_results": 5
    },
    "response": {
      "recipe_id": "recipe_789",
      "name": "Classic Gluten-Free Chocolate Chip Cookies",
      "ingredients": [
        "2 cups gluten-free flour blend",
        "1 cup butter, softened",
        "3/4 cup brown sugar",
        "2 eggs",
        "2 cups chocolate chips"
      ],
      "instructions_url": "https://..."
    },
    "duration_ms": 567,
    "status": "success",
    "character_reasoning": "User asked for chocolate chip cookie recipe. I remembered their gluten intolerance from memory, so I filtered for gluten-free recipes to keep them safe."
  },
  "request_id": "req_024",
  "timestamp": "2025-01-27T12:05:00Z"
}
```

---

### Replay Tool Call

```http
POST /api/v1/tool-calls/{call_id}/replay
```

**Path Parameters:**
- `call_id` (string, required): Tool call event ID to replay

**Request Body:**
```json
{
  "modify_request": {
    "max_results": 10
  }
}
```

**Fields:**
- `modify_request` (object, optional): Override specific request parameters

**Response:**
```json
{
  "data": {
    "original_call_id": "evt_002",
    "replay_call_id": "evt_050",
    "timestamp": "2025-01-27T12:10:00Z",
    "request": {
      "query": "chocolate chip cookies",
      "dietary_restrictions": ["gluten_free"],
      "max_results": 10
    },
    "response": { ... },
    "duration_ms": 543,
    "status": "success"
  },
  "request_id": "req_025",
  "timestamp": "2025-01-27T12:10:00Z"
}
```

---

### Get Tool Call Statistics

```http
GET /api/v1/tool-calls/stats
```

**Query Parameters:**
- `user_id` (string, optional): Filter by user
- `start_time` (string, optional): Start of time range (ISO 8601)
- `end_time` (string, optional): End of time range (ISO 8601)

**Response:**
```json
{
  "data": {
    "total_calls": 47,
    "success_rate": 95.7,
    "average_duration_ms": 387,
    "by_tool": {
      "set_timer": {
        "count": 12,
        "success_rate": 100.0,
        "average_duration_ms": 234
      },
      "get_recipe": {
        "count": 8,
        "success_rate": 100.0,
        "average_duration_ms": 567
      },
      "light_control": {
        "count": 5,
        "success_rate": 80.0,
        "average_duration_ms": 1234
      }
    },
    "by_character": {
      "delilah": {
        "count": 35,
        "success_rate": 97.1
      },
      "hank": {
        "count": 12,
        "success_rate": 91.7
      }
    },
    "slowest_calls": [
      {
        "event_id": "evt_015",
        "tool_name": "light_control",
        "duration_ms": 2345,
        "timestamp": "2025-01-27T09:15:00Z"
      }
    ],
    "recent_errors": [
      {
        "event_id": "evt_018",
        "tool_name": "light_control",
        "error": "Device not found: kitchen_lights",
        "timestamp": "2025-01-27T09:15:00Z"
      }
    ]
  },
  "request_id": "req_026",
  "timestamp": "2025-01-27T12:15:00Z"
}
```

---

## User API

### List All Users

```http
GET /api/v1/users
```

**Query Parameters:**
- `test_only` (boolean, optional): Filter to test users only
- `production_only` (boolean, optional): Filter to production users only
- `sort_by` (string, optional): `created_at`, `last_interaction`, `name`
- `sort_order` (string, optional): `asc` or `desc` (default: `desc`)

**Response:**
```json
{
  "data": {
    "users": [
      {
        "user_id": "user_justin",
        "name": "Justin",
        "is_test_user": false,
        "current_chapter": "chapter_1",
        "created_at": "2025-01-15T08:00:00Z",
        "last_interaction": "2025-01-27T09:15:32Z",
        "interaction_count": 47,
        "memory_count": 23
      },
      {
        "user_id": "user_test_1738",
        "name": "TestUser_Amber_1738",
        "is_test_user": true,
        "current_chapter": "chapter_2",
        "created_at": "2025-01-20T10:00:00Z",
        "last_interaction": "2025-01-24T10:15:00Z",
        "interaction_count": 12,
        "memory_count": 8
      }
    ],
    "total_count": 5,
    "production_count": 1,
    "test_count": 4
  },
  "request_id": "req_027",
  "timestamp": "2025-01-27T12:20:00Z"
}
```

---

### Create Test User

```http
POST /api/v1/users/test
```

**Request Body:**
```json
{
  "name": "TestUser_Riley_8273",
  "starting_chapter": "chapter_1",
  "initial_memories": [
    {
      "category": "dietary_restriction",
      "content": "User is vegetarian",
      "importance": 8
    }
  ],
  "preferences": {
    "tts_voice": "elevenlabs_delilah"
  },
  "tags": ["testing", "chapter2", "hank-intro"]
}
```

**Fields:**
- `name` (string, optional): User name (auto-generated if not provided)
- `starting_chapter` (string, optional): Starting chapter (default: chapter_1)
- `initial_memories` (array, optional): Initial memories to create
- `preferences` (object, optional): User preferences
- `tags` (array, optional): Tags for organization

**Response:**
```json
{
  "data": {
    "user_id": "user_test_8273",
    "name": "TestUser_Riley_8273",
    "is_test_user": true,
    "current_chapter": "chapter_1",
    "created_at": "2025-01-27T12:25:00Z",
    "memory_count": 1,
    "tags": ["testing", "chapter2", "hank-intro"]
  },
  "request_id": "req_028",
  "timestamp": "2025-01-27T12:25:00Z"
}
```

---

### Get User Details

```http
GET /api/v1/users/{user_id}
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response:**
```json
{
  "data": {
    "user_id": "user_justin",
    "name": "Justin",
    "is_test_user": false,
    "created_at": "2025-01-15T08:00:00Z",
    "last_interaction": "2025-01-27T09:15:32Z",
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
    "memory_count": 23,
    "preferences": {
      "tts_voice": "elevenlabs_delilah"
    },
    "metadata": {
      "tags": []
    }
  },
  "request_id": "req_029",
  "timestamp": "2025-01-27T12:30:00Z"
}
```

---

### Delete User

```http
DELETE /api/v1/users/{user_id}
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Query Parameters:**
- `confirm` (boolean, required): Must be true to confirm deletion

**Response:**
```json
{
  "data": {
    "user_id": "user_test_8273",
    "deleted": true,
    "deleted_at": "2025-01-27T12:35:00Z",
    "deleted_data": {
      "memories": 8,
      "tool_calls": 12,
      "conversations": 3
    }
  },
  "request_id": "req_030",
  "timestamp": "2025-01-27T12:35:00Z"
}
```

**Error Response (Production User):**
```json
{
  "error": {
    "code": "CANNOT_DELETE_PRODUCTION_USER",
    "message": "Cannot delete production user: user_justin",
    "details": {
      "is_test_user": false,
      "safeguard": "Production users cannot be deleted via API"
    }
  },
  "request_id": "req_031",
  "timestamp": "2025-01-27T12:35:00Z"
}
```

---

### Get User State

```http
GET /api/v1/users/{user_id}/state
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response:**
```json
{
  "data": {
    "user_id": "user_test_1738",
    "name": "TestUser_Amber_1738",
    "profile": {
      "is_test_user": true,
      "created_at": "2025-01-20T10:00:00Z",
      "last_interaction": "2025-01-24T10:15:00Z",
      "tags": ["testing", "chapter2", "hank-intro"]
    },
    "story_state": {
      "current_chapter": "chapter_2",
      "chapter_progress": {
        "chapter_1": {
          "status": "completed",
          "completed_beats": 8,
          "total_beats": 8
        },
        "chapter_2": {
          "status": "in_progress",
          "completed_beats": 2,
          "total_beats": 6
        }
      }
    },
    "memory_state": {
      "total_memories": 8,
      "by_category": {
        "preference": 3,
        "fact": 4,
        "event": 1
      }
    },
    "interaction_state": {
      "total_interactions": 12,
      "total_tool_calls": 15,
      "active_characters": ["delilah", "hank"]
    }
  },
  "request_id": "req_032",
  "timestamp": "2025-01-27T12:40:00Z"
}
```

---

### Export User Data

```http
POST /api/v1/users/{user_id}/export
```

**Path Parameters:**
- `user_id` (string, required): User identifier

**Request Body:**
```json
{
  "include_tool_calls": true,
  "include_conversation_history": false
}
```

**Fields:**
- `include_tool_calls` (boolean, optional): Include tool call history (default: false)
- `include_conversation_history` (boolean, optional): Include full conversation history (default: false)

**Response:**
```json
{
  "data": {
    "user_id": "user_test_1738",
    "export_timestamp": "2025-01-27T12:45:00Z",
    "user_data": {
      "profile": { ... },
      "story_progress": { ... },
      "memories": [ ... ],
      "tool_calls": [ ... ]
    }
  },
  "request_id": "req_033",
  "timestamp": "2025-01-27T12:45:00Z"
}
```

---

### Import User Data

```http
POST /api/v1/users/import
```

**Request Body:**
```json
{
  "user_data": {
    "profile": { ... },
    "story_progress": { ... },
    "memories": [ ... ]
  },
  "overwrite_existing": false
}
```

**Fields:**
- `user_data` (object, required): Exported user data
- `overwrite_existing` (boolean, optional): Overwrite if user already exists (default: false)

**Response:**
```json
{
  "data": {
    "user_id": "user_test_1738",
    "imported": true,
    "imported_at": "2025-01-27T12:50:00Z",
    "imported_data": {
      "memories": 8,
      "story_beats": 10
    }
  },
  "request_id": "req_034",
  "timestamp": "2025-01-27T12:50:00Z"
}
```

---

### Set Active User

```http
PUT /api/v1/users/active
```

**Request Body:**
```json
{
  "user_id": "user_test_1738"
}
```

**Fields:**
- `user_id` (string, required): User ID to set as active

**Response:**
```json
{
  "data": {
    "active_user_id": "user_test_1738",
    "previous_user_id": "user_justin",
    "changed_at": "2025-01-27T12:55:00Z"
  },
  "request_id": "req_035",
  "timestamp": "2025-01-27T12:55:00Z"
}
```

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing authentication token |
| `FORBIDDEN` | 403 | Operation not permitted |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `CHAPTER_LOCKED` | 409 | Chapter cannot be unlocked |
| `BEAT_CONDITIONS_NOT_MET` | 409 | Beat delivery conditions not satisfied |
| `CANNOT_DELETE_PRODUCTION_USER` | 403 | Cannot delete production user |
| `INTERNAL_ERROR` | 500 | Server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid memory category",
    "details": {
      "field": "category",
      "allowed_values": ["preference", "fact", "dietary_restriction", "event", "relationship"],
      "provided_value": "invalid_category"
    }
  },
  "request_id": "req_036",
  "timestamp": "2025-01-27T13:00:00Z"
}
```

### Common Error Examples

**404 Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found: user_test_9999",
    "details": {
      "resource": "user",
      "resource_id": "user_test_9999"
    }
  },
  "request_id": "req_037",
  "timestamp": "2025-01-27T13:05:00Z"
}
```

**422 Validation Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "importance",
          "message": "Value must be between 1 and 10",
          "provided_value": 15
        }
      ]
    }
  },
  "request_id": "req_038",
  "timestamp": "2025-01-27T13:10:00Z"
}
```

**500 Internal Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": {
      "error_id": "err_abc123"
    }
  },
  "request_id": "req_039",
  "timestamp": "2025-01-27T13:15:00Z"
}
```

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1643292000
```

### Rate Limit Exceeded

When rate limit is exceeded:

**HTTP Status:** 429 Too Many Requests

**Response:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": "1 hour",
      "retry_after": 3600
    }
  },
  "request_id": "req_040",
  "timestamp": "2025-01-27T13:20:00Z"
}
```

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1643295600
Retry-After: 3600
```

---

## Appendix: Data Models

### User Model

```typescript
interface User {
  user_id: string;
  name: string;
  is_test_user: boolean;
  created_at: string; // ISO 8601
  last_interaction: string | null; // ISO 8601
  current_chapter: string;
  story_progress: {
    [chapterId: string]: {
      unlocked_at: string; // ISO 8601
      completed_beats: string[];
      current_beat: string | null;
      chapter_complete: boolean;
    };
  };
  interaction_count: number;
  preferences: {
    tts_voice?: string;
    [key: string]: any;
  };
  metadata: {
    tags?: string[];
    [key: string]: any;
  };
}
```

### Memory Model

```typescript
interface Memory {
  memory_id: string;
  user_id: string;
  category: 'preference' | 'fact' | 'dietary_restriction' | 'event' | 'relationship';
  content: string;
  importance: number; // 1-10
  source: string | null;
  created_at: string; // ISO 8601
  last_accessed: string | null; // ISO 8601
  access_count: number;
  metadata: {
    [key: string]: any;
  };
}
```

### Story Beat Model

```typescript
interface StoryBeat {
  beat_id: string;
  name: string;
  chapter_id: string;
  required: boolean;
  prerequisites: string[];
  delivery_conditions: {
    max_deliveries: number | null;
    trigger: string;
    cooldown_hours: number | null;
    context_requirements: string[];
  };
  variants: {
    short: string;
    medium: string;
    long: string;
  };
  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
  };
}
```

### Tool Call Model

```typescript
interface ToolCall {
  event_id: string;
  timestamp: string; // ISO 8601
  user_id: string;
  conversation_id: string;
  tool_name: string;
  character: string;
  request: {
    [key: string]: any;
  };
  response: {
    [key: string]: any;
  } | null;
  error: string | null;
  duration_ms: number;
  status: 'success' | 'error';
  character_reasoning?: string;
}
```

### Character Model

```typescript
interface Character {
  character_id: string;
  name: string;
  full_name: string;
  role: string;
  introduction_chapter: string;
  active: boolean;
  personality: {
    traits: string[];
    core_conflict: string;
    defining_trait: string;
    voice_modes: {
      [modeName: string]: {
        triggers: string[];
        characteristics: string;
      };
    };
  };
  capabilities: string[];
  tts_config: {
    provider: string;
    voice_id: string;
    settings: {
      [key: string]: any;
    };
  };
  statistics?: {
    total_interactions: number;
    average_response_length: number;
    most_used_capability: string;
  };
}
```

---

*This API specification will evolve as implementation progresses and new requirements emerge.*
