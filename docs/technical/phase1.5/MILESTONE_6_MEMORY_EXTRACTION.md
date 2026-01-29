# Phase 1.5: Milestone 6 - Memory Extraction & Retrieval System

**Status**: Planning
**Version**: 1.0
**Created**: 2026-01-29
**Dependencies**: Phase 1.5 (Milestones 1-5)

---

## Overview

Implement automatic memory extraction from conversations and ensure memories are included in the system prompt. This allows the AI to learn about users during conversations and reference that information in future interactions.

### Problem Statement

Currently, when users mention important information (dietary restrictions, preferences, family details, events), the AI responds appropriately but **doesn't save** that information. This means:
- Users must repeat themselves in every conversation
- The AI can't build a relationship based on past shared information
- Delilah can't provide personalized recommendations based on learned preferences

### Solution

Implement a two-part memory system:
1. **Memory Retrieval**: Include user memories in system prompt (context awareness)
2. **Memory Extraction**: Allow AI to automatically save memories using a tool

---

## Memory Categories

The system supports five types of memories, each serving a different purpose:

### 1. Fact
**Purpose**: Objective information about the user
**Examples**:
- "The user lives in Provo, Utah"
- "The user works from home"
- "The user has a greenhouse with 200 hanging baskets"
- "The user is learning to speak Spanish"

**Importance Range**: 3-7
**Usage**: General context, conversation continuity, personalized small talk

---

### 2. Preference
**Purpose**: User likes, dislikes, and taste preferences (non-dietary)
**Examples**:
- "The user likes mild foods"
- "The user prefers quick recipes (under 30 minutes)"
- "The user loves Thai food"
- "The user doesn't like cilantro"
- "The user prefers morning workouts"

**Importance Range**: 4-8
**Usage**: Recipe recommendations, activity suggestions, conversation topics

---

### 3. Dietary Restriction
**Purpose**: Critical health and dietary information
**Examples**:
- "The user has Celiac disease (gluten intolerance)"
- "The user is lactose intolerant"
- "The user has a dairy allergy"
- "The user is vegetarian"
- "The user has a tree nut allergy"

**Importance Range**: 8-10 (CRITICAL)
**Usage**: Recipe safety, meal planning, ingredient substitution
**Special Handling**:
- Triggers MAMA_BEAR voice mode in Delilah
- Must ALWAYS be considered in food recommendations
- Should prompt confirmation before suggesting potentially unsafe foods

---

### 4. Relationship
**Purpose**: Information about people in the user's life
**Examples**:
- "The user has 3 kids"
- "The user's daughter is allergic to peanuts"
- "The user's spouse is vegan"
- "The user's mother visits on Sundays"
- "The user's best friend is getting married in June"

**Importance Range**: 5-9
**Usage**: Meal planning (serving sizes), recipe complexity, conversation context, schedule awareness

---

### 5. Event
**Purpose**: Time-bound events and commitments
**Examples**:
- "Parent-teacher conferences this Tuesday"
- "Family vacation to Hawaii next month"
- "Birthday party on Saturday"
- "Hosting dinner party for 8 people on Friday"
- "Thanksgiving is in 3 weeks"

**Importance Range**: 6-10
**Usage**: Schedule awareness, meal planning, time-sensitive reminders
**Special Handling**:
- Should be surfaced when relevant dates approach
- Can be marked as completed/past
- Higher importance for imminent events

---

## Architecture

### Data Model

**Existing Structure** ([user_state.py](../../../backend/src/models/user_state.py)):

```python
class Memory(BaseModel):
    """Single memory item."""
    memory_id: str                      # Unique identifier
    category: str                       # fact, preference, dietary_restriction, relationship, event
    content: str                        # The actual memory content
    source: str                         # Where it came from (e.g., "conversation_2026-01-29")
    importance: int                     # 1-10 (higher = more important)
    verified: bool                      # Has user confirmed this?
    created_at: datetime                # When memory was created
    last_accessed: Optional[datetime]   # When last used in context
    access_count: int                   # How many times referenced
    metadata: Dict[str, Any]            # Additional category-specific data

class UserMemories(BaseModel):
    """Collection of memories for a user."""
    memories: Dict[str, Memory] = Field(default_factory=dict)
```

**Category-Specific Metadata**:

```python
# Event metadata example
{
    "event_date": "2026-02-04",  # ISO date
    "event_type": "appointment",
    "participants": ["user", "teachers"],
    "location": "school"
}

# Relationship metadata example
{
    "relationship_type": "child",
    "age": 8,
    "name": "Emma"
}

# Dietary restriction metadata example
{
    "severity": "allergy",  # allergy, intolerance, preference
    "diagnosed": true,
    "alternatives": ["almond milk", "oat milk"]
}
```

### Storage

**Location**: `/backend/data/users/{user_id}_memories.json`

**Format**:
```json
{
  "memories": {
    "mem_abc123": {
      "memory_id": "mem_abc123",
      "category": "dietary_restriction",
      "content": "Has Celiac disease (gluten intolerance)",
      "source": "conversation_2026-01-29T10:30:00",
      "importance": 10,
      "verified": true,
      "created_at": "2026-01-29T10:30:00",
      "last_accessed": "2026-01-29T15:45:00",
      "access_count": 3,
      "metadata": {
        "severity": "medical",
        "alternatives": ["gluten-free flour", "rice flour"]
      }
    },
    "mem_def456": {
      "memory_id": "mem_def456",
      "category": "relationship",
      "content": "Has 3 kids",
      "source": "conversation_2026-01-29T11:00:00",
      "importance": 7,
      "verified": true,
      "created_at": "2026-01-29T11:00:00",
      "last_accessed": "2026-01-29T11:05:00",
      "access_count": 1,
      "metadata": {
        "count": 3
      }
    }
  }
}
```

---

## Implementation Plan

### Milestone 1: Memory Retrieval (Context Awareness)

**Goal**: Include user memories in system prompt so AI can reference them

#### 1.1: Load Memories in Conversation Manager

**File**: [conversation_manager.py](../../../backend/src/core/conversation_manager.py)

**Modify**: `_build_system_prompt()` method (line ~147)

```python
def _build_system_prompt(
    self,
    context: ConversationContext,
    character_id: Optional[str] = None,
    user_message: Optional[str] = None
) -> str:
    """Build system prompt with user memory context."""
    char_id = character_id or self.default_character

    # NEW: Load user memories
    from observability.memory_access import MemoryAccessor
    memory_accessor = MemoryAccessor("data")
    memories = memory_accessor.get_all_memories(context.user_id)

    # Group memories by category
    memory_context = {
        "dietary_restrictions": [],
        "preferences": [],
        "facts": [],
        "relationships": [],
        "events": []
    }

    for memory in memories:
        if memory.category == "dietary_restriction":
            memory_context["dietary_restrictions"].append(memory)
        elif memory.category == "preference":
            memory_context["preferences"].append(memory)
        elif memory.category == "fact":
            memory_context["facts"].append(memory)
        elif memory.category == "relationship":
            memory_context["relationships"].append(memory)
        elif memory.category == "event":
            memory_context["events"].append(memory)

    # Voice mode selection
    if user_message:
        voice_mode_selection = self.character_system.select_voice_mode(
            char_id, user_message, context.metadata
        )
        if voice_mode_selection:
            return self.character_system.build_system_prompt(
                char_id,
                voice_mode_selection.mode,
                memory_context=memory_context  # PASS MEMORIES
            )

    # Fallback
    return self.character_system.build_system_prompt(
        char_id,
        memory_context=memory_context  # PASS MEMORIES
    )
```

#### 1.2: Update Character System Prompt Builder

**File**: [character_system.py](../../../backend/src/core/character_system.py)

**Modify**: `build_system_prompt()` method (line ~124)

```python
def build_system_prompt(
    self,
    character_id: str,
    voice_mode: Optional[VoiceMode] = None,
    memory_context: Optional[Dict[str, List[Memory]]] = None  # NEW PARAMETER
) -> str:
    """Build system prompt with memory context."""

    character = self.get_character(character_id)
    if not character:
        return "You are a helpful AI assistant."

    # ... existing character prompt building ...

    # NEW: Add memory context section
    if memory_context:
        prompt_parts.append("\n\n## What You Know About This User")

        # Dietary Restrictions (CRITICAL - always show first)
        dietary = memory_context.get("dietary_restrictions", [])
        if dietary:
            prompt_parts.append("\n### ⚠️  DIETARY RESTRICTIONS (CRITICAL)")
            for memory in dietary:
                prompt_parts.append(f"- {memory.content}")
            prompt_parts.append(
                "**IMPORTANT**: ALWAYS consider these restrictions in ANY food recommendation. "
                "If uncertain, ask before suggesting."
            )

        # Preferences
        prefs = memory_context.get("preferences", [])
        if prefs:
            prompt_parts.append("\n### Preferences")
            for memory in sorted(prefs, key=lambda m: m.importance, reverse=True):
                prompt_parts.append(f"- {memory.content}")

        # Relationships
        relationships = memory_context.get("relationships", [])
        if relationships:
            prompt_parts.append("\n### Family & Relationships")
            for memory in relationships:
                prompt_parts.append(f"- {memory.content}")

        # Facts
        facts = memory_context.get("facts", [])
        if facts:
            prompt_parts.append("\n### Facts About User")
            for memory in sorted(facts, key=lambda m: m.importance, reverse=True)[:5]:
                prompt_parts.append(f"- {memory.content}")

        # Events (only show upcoming/recent)
        events = memory_context.get("events", [])
        if events:
            prompt_parts.append("\n### Upcoming Events & Schedule")
            for memory in sorted(events, key=lambda m: m.importance, reverse=True)[:3]:
                prompt_parts.append(f"- {memory.content}")

    return "\n".join(prompt_parts)
```

**Testing Milestone 1**:
```
1. Manually create memories via Observability UI:
   - Dietary: "Has Celiac disease"
   - Preference: "Likes mild foods"
   - Fact: "Lives in Provo"
   - Relationship: "Has 3 kids"
   - Event: "Parent-teacher conferences Tuesday"

2. Send message: "What should I make for dinner?"

3. Expected system prompt should include:
   ## What You Know About This User
   ### ⚠️  DIETARY RESTRICTIONS (CRITICAL)
   - Has Celiac disease
   **IMPORTANT**: ALWAYS consider...

   ### Preferences
   - Likes mild foods

   ### Family & Relationships
   - Has 3 kids

   ### Facts About User
   - Lives in Provo

   ### Upcoming Events & Schedule
   - Parent-teacher conferences Tuesday

4. Expected response:
   - Avoids gluten
   - Suggests mild flavors
   - Considers serving size for family
   - Might mention quick prep (event coming up)
```

---

### Milestone 2: Memory Extraction Tool

**Goal**: Allow AI to automatically save memories during conversation

#### 2.1: Create SaveMemoryTool

**New File**: `/backend/src/tools/memory_tool.py`

```python
"""
Memory Tool - Allows AI to save user memories during conversation
"""
from typing import Dict, Any, Optional
from datetime import datetime
from .base_tool import BaseTool, ToolContext
from observability.memory_access import MemoryAccessor

class MemoryTool(BaseTool):
    """Tool for saving user memories during conversation."""

    def __init__(self):
        super().__init__()
        self.memory_accessor = MemoryAccessor("data")

    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return (
            "Save important information about the user for future reference. "
            "Use this when the user shares facts about themselves, preferences, "
            "dietary restrictions, family information, or upcoming events."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [
                        "fact",
                        "preference",
                        "dietary_restriction",
                        "relationship",
                        "event"
                    ],
                    "description": (
                        "Type of memory:\n"
                        "- fact: Objective info (location, job, hobbies)\n"
                        "- preference: Likes/dislikes (food preferences, cooking style)\n"
                        "- dietary_restriction: Health/diet needs (allergies, Celiac, vegetarian)\n"
                        "- relationship: Family/friends (kids, spouse, pets)\n"
                        "- event: Time-bound events (appointments, parties, trips)"
                    )
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Clear, concise description of the memory. "
                        "Examples:\n"
                        "- 'Has Celiac disease (gluten intolerance)'\n"
                        "- 'Likes mild foods'\n"
                        "- 'Lives in Provo, Utah'\n"
                        "- 'Has 3 kids'\n"
                        "- 'Parent-teacher conferences on Tuesday'"
                    )
                },
                "importance": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": (
                        "Importance level (1-10):\n"
                        "- 10: Critical safety (severe allergies)\n"
                        "- 8-9: Very important (dietary restrictions, health)\n"
                        "- 6-7: Important (family, regular preferences)\n"
                        "- 4-5: Useful context (location, work)\n"
                        "- 1-3: Nice to know (minor preferences)"
                    )
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional additional structured data",
                    "properties": {
                        "event_date": {"type": "string"},
                        "severity": {"type": "string"},
                        "relationship_type": {"type": "string"}
                    }
                }
            },
            "required": ["category", "content", "importance"]
        }

    async def execute(
        self, context: ToolContext, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save a memory for the user.

        Args:
            context: Tool execution context
            arguments: {category, content, importance, metadata?}

        Returns:
            Success confirmation with memory_id
        """
        category = arguments.get("category")
        content = arguments.get("content")
        importance = arguments.get("importance", 5)
        metadata = arguments.get("metadata", {})

        if not category or not content:
            return {
                "success": False,
                "error": "Missing required fields: category and content"
            }

        # Validate category
        valid_categories = [
            "fact", "preference", "dietary_restriction",
            "relationship", "event"
        ]
        if category not in valid_categories:
            return {
                "success": False,
                "error": f"Invalid category. Must be one of: {valid_categories}"
            }

        # Validate importance
        if not isinstance(importance, int) or importance < 1 or importance > 10:
            return {
                "success": False,
                "error": "Importance must be an integer between 1 and 10"
            }

        try:
            # Create memory
            memory = self.memory_accessor.create_memory(
                user_id=context.user_id,
                category=category,
                content=content,
                source=f"conversation_{datetime.now().isoformat()}",
                importance=importance,
                verified=False,  # Will be verified over time
                metadata=metadata
            )

            return {
                "success": True,
                "memory_id": memory.memory_id,
                "message": f"Saved {category}: {content}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save memory: {str(e)}"
            }
```

#### 2.2: Register Memory Tool

**File**: [websocket.py](../../../backend/src/api/websocket.py)

**Modify**: Tool registration section (line ~32)

```python
from tools.timer_tool import TimerTool
from tools.device_tool import DeviceTool
from tools.memory_tool import MemoryTool  # NEW

# Initialize systems
tool_system = ToolSystem()
tool_system.register_tool(TimerTool())
tool_system.register_tool(DeviceTool())
tool_system.register_tool(MemoryTool())  # NEW

logger.info(f"Registered tools: {tool_system.list_tools()}")
```

**Testing Milestone 2**:
```
1. Start backend with new tool registered
2. Check logs: "Registered tools: ['timer_tool', 'device_tool', 'save_memory']"
3. Make a test API call to verify tool is available
4. Send message: "I have Celiac disease"
5. Check logs for tool call attempt
6. Verify memory saved in observability UI
```

---

### Milestone 3: Character Instructions

**Goal**: Teach Delilah when and how to use the memory tool

#### 3.1: Update Delilah's Character Definition

**File**: [delilah.json](../../../story/characters/delilah.json)

**Add New Section** (after `voice_modes`, around line 200):

```json
"tool_instructions": {
  "save_memory": {
    "general_guidance": "Save important information users share about themselves. This helps you remember them and provide better, more personalized help.",

    "when_to_use": [
      "User mentions dietary restrictions, allergies, or health conditions",
      "User describes food preferences or dislikes",
      "User shares facts about their life (location, work, hobbies)",
      "User mentions family members or relationships",
      "User mentions upcoming events or commitments",
      "User corrects previous information"
    ],

    "when_NOT_to_use": [
      "Temporary situations (e.g., 'I'm hungry right now')",
      "Single-use information (e.g., 'Set a timer for 5 minutes')",
      "Information already saved (check context first)",
      "Vague statements without clear facts"
    ],

    "examples": [
      {
        "user_says": "I have Celiac disease and I'm also lactose intolerant",
        "action": "Call save_memory twice",
        "calls": [
          {
            "category": "dietary_restriction",
            "content": "Has Celiac disease (gluten intolerance)",
            "importance": 10,
            "metadata": {"severity": "medical"}
          },
          {
            "category": "dietary_restriction",
            "content": "Lactose intolerant",
            "importance": 9,
            "metadata": {"severity": "intolerance"}
          }
        ]
      },
      {
        "user_says": "I like mild foods, nothing too spicy",
        "action": "Call save_memory once",
        "calls": [
          {
            "category": "preference",
            "content": "Prefers mild foods, avoids spicy",
            "importance": 6
          }
        ]
      },
      {
        "user_says": "I live in Provo and I have 3 kids",
        "action": "Call save_memory twice",
        "calls": [
          {
            "category": "fact",
            "content": "Lives in Provo, Utah",
            "importance": 5
          },
          {
            "category": "relationship",
            "content": "Has 3 kids",
            "importance": 7,
            "metadata": {"relationship_type": "children", "count": 3}
          }
        ]
      },
      {
        "user_says": "I have parent-teacher conferences this Tuesday",
        "action": "Call save_memory once",
        "calls": [
          {
            "category": "event",
            "content": "Parent-teacher conferences on Tuesday",
            "importance": 7,
            "metadata": {"event_type": "appointment", "event_date": "2026-02-04"}
          }
        ]
      },
      {
        "user_says": "Actually, I don't have an allergy to dairy, just lactose",
        "action": "Update/correct existing memory or add clarification",
        "note": "Check if dairy allergy was previously saved and clarify"
      }
    ],

    "importance_guidelines": {
      "10": "Life-threatening allergies (anaphylaxis risk)",
      "9": "Serious health conditions (Celiac, severe intolerance)",
      "8": "Medical dietary restrictions (diabetes management, etc.)",
      "7": "Family information, important events",
      "6": "Strong preferences, lifestyle choices (vegetarian)",
      "5": "Location, work, regular habits",
      "4": "Minor preferences",
      "3": "Casual mentions",
      "1-2": "Trivial information"
    },

    "mama_bear_mode_integration": "When in MAMA_BEAR mode (triggered by allergy/dietary keywords), you MUST save the dietary restriction immediately. This is non-negotiable for user safety."
  }
}
```

#### 3.2: Include Tool Instructions in System Prompt

**File**: [character_system.py](../../../backend/src/core/character_system.py)

**Modify**: `build_system_prompt()` method (add after voice mode section, around line 180)

```python
# Add tool instructions if present
if hasattr(character, 'tool_instructions') and character.tool_instructions:
    prompt_parts.append("\n\n## Tool Usage Guidelines")

    for tool_name, instructions in character.tool_instructions.items():
        prompt_parts.append(f"\n### Using the '{tool_name}' Tool")

        if 'general_guidance' in instructions:
            prompt_parts.append(f"\n{instructions['general_guidance']}")

        if 'when_to_use' in instructions:
            prompt_parts.append("\n**When to use this tool:**")
            for condition in instructions['when_to_use']:
                prompt_parts.append(f"- {condition}")

        if 'when_NOT_to_use' in instructions:
            prompt_parts.append("\n**When NOT to use:**")
            for condition in instructions['when_NOT_to_use']:
                prompt_parts.append(f"- {condition}")

        if 'examples' in instructions and len(instructions['examples']) > 0:
            prompt_parts.append("\n**Examples:**")
            for i, ex in enumerate(instructions['examples'][:3], 1):  # Show first 3
                prompt_parts.append(f"\n{i}. User: \"{ex['user_says']}\"")
                prompt_parts.append(f"   Action: {ex['action']}")
                if 'calls' in ex and len(ex['calls']) > 0:
                    call = ex['calls'][0]  # Show first call as example
                    prompt_parts.append(
                        f"   Example call: category=\"{call['category']}\", "
                        f"importance={call['importance']}"
                    )

        if 'importance_guidelines' in instructions:
            prompt_parts.append("\n**Importance Ratings:**")
            guidelines = instructions['importance_guidelines']
            for level in ['10', '9', '8', '7', '5', '3']:
                if level in guidelines:
                    prompt_parts.append(f"- {level}: {guidelines[level]}")
```

**Testing Milestone 3**:
```
1. Restart backend to load updated character JSON
2. Send: "I have Celiac disease"
3. Expected:
   - MAMA_BEAR mode triggered
   - save_memory tool called
   - Tool call logged in backend
   - Memory visible in observability UI
4. Send: "What can I make for breakfast?"
5. Expected:
   - System prompt includes dietary restriction
   - Response avoids gluten
   - Shows awareness of saved restriction
```

---

## Complete Flow Example

### Scenario: New User First Conversation

**User**: "Hi! I'm looking for dinner ideas. I have Celiac disease and I'm also lactose intolerant. I have 3 kids so I need something family-friendly."

**Backend Processing**:

1. **Message Received** (websocket.py)
   - Extract user_id from message
   - Pass to ConversationManager

2. **System Prompt Building** (conversation_manager.py)
   - Load existing memories (empty for new user)
   - Voice mode selection: "celiac", "lactose", "intolerant" → MAMA_BEAR
   - Build prompt with MAMA_BEAR mode + tool instructions

3. **LLM Processing**
   - Receives system prompt with tool instructions
   - Sees keywords: "Celiac", "lactose intolerant", "3 kids"
   - Decides to call save_memory tool 3 times

4. **Tool Execution Loop**
   - Call 1: save_memory(category="dietary_restriction", content="Has Celiac disease", importance=10)
   - Call 2: save_memory(category="dietary_restriction", content="Lactose intolerant", importance=9)
   - Call 3: save_memory(category="relationship", content="Has 3 kids", importance=7)
   - All three saved to user_justin_memories.json

5. **Final Response Generation**
   - LLM generates response in MAMA_BEAR mode
   - Acknowledges restrictions with empathy
   - Suggests gluten-free, dairy-free, family-friendly recipe

**Delilah's Response**:
```
"Oh sugar, bless your heart! Celiac AND lactose intolerance - I'm gonna
make sure we keep you safe, honey. And feedin' three hungry kids too!
Let me think of somethin' that'll work for everybody...

How about some gluten-free chicken tacos? We can use corn tortillas
(naturally gluten-free), seasoned chicken, and skip the cheese and sour
cream. The kids can add their favorite toppings - lettuce, tomatoes,
salsa, maybe some guacamole. Quick to make, fun to eat, and safe for
your tummy.

Sound good, sugar?"
```

### Next Day: Return Conversation

**User**: "What should I make for breakfast?"

**Backend Processing**:

1. **System Prompt Building**
   - Load memories from user_justin_memories.json
   - Found 3 memories:
     - Dietary: "Has Celiac disease" (importance: 10)
     - Dietary: "Lactose intolerant" (importance: 9)
     - Relationship: "Has 3 kids" (importance: 7)
   - Include in system prompt under "What You Know About This User"

2. **LLM Processing**
   - Sees breakfast request
   - System prompt shows dietary restrictions
   - No tool calls needed (just generating response)
   - Uses memory context to provide safe suggestions

**Delilah's Response**:
```
"Good mornin', sugar! Let me think of somethin' that'll work with your
gluten and dairy restrictions...

How about some scrambled eggs with gluten-free toast and fresh fruit?
Easy, safe, and I know you've got those three kiddos to feed! You could
even let them help crack the eggs - my grandmama always said cookin'
together makes breakfast taste better."
```

**Key Points**:
- No need to mention restrictions again
- Delilah remembers automatically
- Family context used naturally
- Consistent MAMA_BEAR-adjacent tone (protective but not urgent)

---

## Testing Strategy

### Test 1: Memory Creation (Manual)
```
Setup: Use Observability UI
1. Navigate to Memory Tool
2. Create 5 memories (one of each type):
   - Fact: "Lives in Provo, Utah" (importance: 5)
   - Preference: "Likes mild foods" (importance: 6)
   - Dietary: "Has Celiac disease" (importance: 10)
   - Relationship: "Has 3 kids" (importance: 7)
   - Event: "Parent-teacher conferences Tuesday" (importance: 7)
3. Verify all saved in UI

Test: Check system prompt includes memories
1. Open chat interface
2. Send: "What should I make for dinner?"
3. Check backend logs for system prompt
4. Verify prompt includes all 5 memory categories
5. Verify response considers restrictions and context

Expected: ✅ Gluten-free suggestion, mild flavors, serves 4+, quick prep
```

### Test 2: Automatic Extraction (Tool-based)
```
Setup: Clear all memories for user_justin

Test: Single memory extraction
1. Send: "I have Celiac disease"
2. Check logs for save_memory tool call
3. Verify memory saved with:
   - category: "dietary_restriction"
   - importance: 9 or 10
   - content mentions gluten
4. Check observability UI shows new memory

Expected: ✅ MAMA_BEAR response + memory saved

Test: Multiple memory extraction
1. Send: "I live in Provo and I have 3 kids"
2. Check logs for TWO save_memory calls
3. Verify both memories saved:
   - Fact: "Lives in Provo"
   - Relationship: "Has 3 kids"

Expected: ✅ Two separate memories created
```

### Test 3: Memory Persistence Across Sessions
```
Setup: Memories from Test 2 should exist

Test: New conversation uses saved context
1. Open new browser tab (simulates new session)
2. Send: "What's for breakfast?"
3. Verify response:
   - Avoids gluten (uses saved restriction)
   - Doesn't ask about dietary needs again
   - Might mention family size

Expected: ✅ Delilah knows restrictions without being told again
```

### Test 4: Multi-User Isolation
```
Setup: user_justin has Celiac saved

Test: Different users have separate memories
1. Use User Testing Tool to create test_user_1
2. Switch to test_user_1 in chat dropdown
3. Send: "I'm allergic to peanuts"
4. Verify save_memory called for test_user_1
5. Switch back to user_justin
6. Send: "What can I eat?"
7. Verify response mentions gluten (NOT peanuts)

Expected: ✅ Each user has separate memory context
```

### Test 5: Memory Updates/Corrections
```
Setup: Create memory: "Vegetarian"

Test: User corrects information
1. Send: "Actually, I'm not vegetarian anymore, I eat chicken now"
2. Expected behavior (to implement):
   - LLM should recognize correction
   - Could update existing memory
   - Or add clarifying memory

Note: Memory updates are a future feature (post-Milestone 6)
For now, just verify new preference can be added
```

### Test 6: Importance Levels Affect Context
```
Setup: Create 10 memories with varying importance (1-10)

Test: High-importance memories prioritized
1. Send simple query
2. Check system prompt in logs
3. Verify importance 8-10 memories are included
4. Verify lower-importance memories may be truncated

Expected: ✅ Critical info (dietary) always included
```

---

## Success Criteria

### Milestone 1 Complete When:
- [  ] Memories manually created in observability UI
- [  ] System prompt includes memory context
- [  ] Delilah's responses show awareness of saved info
- [  ] All 5 memory categories render correctly in prompt
- [  ] Dietary restrictions emphasized appropriately

### Milestone 2 Complete When:
- [  ] SaveMemoryTool created and registered
- [  ] Tool appears in LLM function definitions
- [  ] Manual tool call test succeeds
- [  ] Memories saved to correct user file
- [  ] Memory accessible in observability UI

### Milestone 3 Complete When:
- [  ] Character JSON updated with tool instructions
- [  ] Instructions included in system prompts
- [  ] LLM calls save_memory without prompting
- [  ] All 5 memory categories extracted correctly
- [  ] Importance levels assigned appropriately
- [  ] Multi-memory extraction works (e.g., "Celiac and lactose intolerant")

### Full System Complete When:
- [  ] User mentions dietary restriction → automatically saved
- [  ] Next conversation → restriction remembered without re-stating
- [  ] All test scenarios pass
- [  ] Multi-user memory isolation confirmed
- [  ] Observability dashboard shows memory activity
- [  ] No false positives (only real facts saved)
- [  ] No critical info missed (all dietary restrictions captured)

---

## File Changes Summary

| File | Type | Lines | Description |
|------|------|-------|-------------|
| `conversation_manager.py` | Modify | ~40 | Load memories, pass to prompt builder |
| `character_system.py` | Modify | ~60 | Add memory context to system prompt |
| `tools/memory_tool.py` | **NEW** | ~150 | Create save_memory tool |
| `websocket.py` | Modify | ~2 | Register memory tool |
| `story/characters/delilah.json` | Modify | ~120 | Add tool instructions with examples |
| `character_system.py` | Modify | ~30 | Include tool instructions in prompt |

**Total Estimated Changes**: ~400 lines

---

## Dependencies

### Required Files/Systems:
- ✅ Memory data model ([user_state.py](../../../backend/src/models/user_state.py))
- ✅ Memory persistence ([memory_access.py](../../../backend/src/observability/memory_access.py))
- ✅ Tool system ([tool_system.py](../../../backend/src/core/tool_system.py))
- ✅ Character system ([character_system.py](../../../backend/src/core/character_system.py))
- ✅ Observability API (for manual testing)
- ✅ User selection in chat UI (from Phase 1.5)

### External Dependencies:
- OpenAI API (function calling)
- Existing conversation flow
- File system access for user data

---

## Future Enhancements (Post-1.5.5)

### Memory Management Features
- **Memory Updates**: Allow updating existing memories
- **Memory Deletion**: Remove incorrect memories
- **Memory Confidence**: Track verification over time
- **Memory Decay**: Reduce importance of old, unused memories

### Smart Context Management
- **Importance-based Filtering**: Only include top N memories in prompt
- **Category Prioritization**: Dietary > Relationship > Fact
- **Recency Weighting**: Recent memories slightly more important
- **Token Budget Management**: Truncate when prompt too long

### Advanced Extraction
- **Implicit Memory Detection**: Infer preferences from behavior
- **Confidence Scores**: "User might prefer..." vs "User definitely has..."
- **Multi-turn Extraction**: Build memory over multiple messages
- **Clarification Prompts**: "Just to confirm, you said..."

### Memory Analytics
- **Usage Tracking**: Which memories are referenced most
- **Accuracy Monitoring**: User corrections indicate wrong memories
- **Coverage Metrics**: % of user info captured
- **Staleness Detection**: Flag outdated information

---

## Open Questions

1. **Should we verify memories before saving?**
   - Option A: Save immediately, verify over time
   - Option B: Ask user to confirm each memory
   - Recommendation: Save immediately, allow corrections later

2. **How many memories should be in system prompt?**
   - All memories (could exceed token limits)
   - Top N by importance (might miss context)
   - Category-based limits (5 dietary, 3 relationships, etc.)
   - Recommendation: All critical (8+), top 5 of others

3. **Should memories expire?**
   - Events: Yes (after date passes)
   - Facts: Rarely (unless corrected)
   - Preferences: Maybe (tastes change)
   - Dietary: Never (safety-critical)
   - Recommendation: Implement event expiration, manual deletion for others

4. **What about conflicting memories?**
   - Example: "Vegetarian" vs "Loves steak"
   - Resolution: Allow both, show most recent in context
   - Future: Conflict detection and resolution UI

---

## Risk Assessment

### High Risk
- **False Positives**: Saving casual comments as facts
  - Mitigation: Clear tool instructions, examples
  - Monitoring: Review saved memories in observability UI

- **Missed Critical Info**: Not saving dietary restrictions
  - Mitigation: Explicit MAMA_BEAR mode integration
  - Testing: Comprehensive test scenarios

### Medium Risk
- **Token Budget Overflow**: Too many memories in prompt
  - Mitigation: Importance-based filtering
  - Monitoring: Track prompt token counts

- **User Privacy Concerns**: Storing personal information
  - Mitigation: Local storage only, user control
  - Future: Memory deletion feature

### Low Risk
- **Performance Impact**: Loading memories on every message
  - Mitigation: Memory files are small (<100KB)
  - Optimization: Cache in conversation context

---

## Timeline Estimate

**Milestone 1 (Memory Retrieval)**: 2-3 hours
- 1 hour: Code changes
- 1 hour: Testing and debugging
- 30 min: Documentation

**Milestone 2 (Memory Tool)**: 3-4 hours
- 2 hours: Tool implementation
- 1 hour: Integration and testing
- 1 hour: Edge cases and error handling

**Milestone 3 (Character Instructions)**: 2-3 hours
- 1 hour: JSON updates and examples
- 1 hour: Prompt integration
- 1 hour: End-to-end testing

**Total Estimated Time**: 7-10 hours

---

## Next Steps

1. Review this plan with stakeholders
2. Create implementation branch: `feature/milestone-6-memory-extraction`
3. Start with Milestone 1 (memory retrieval)
4. Manual testing after each milestone
5. Full integration testing after Milestone 3
6. Update observability dashboard to show memory activity
7. Create user documentation for memory system

---

**Document Version**: 1.0
**Last Updated**: 2026-01-29
**Author**: Development Team
**Status**: Ready for Implementation
