# Phase 1.5: Observability & Testing Tools - Product Requirements Document

**Version:** 1.0
**Last Updated:** January 2025
**Product Owner:** Justin
**Status:** Planning
**Phase Position:** Between Phase 1 and Phase 2

---

## Executive Summary

Phase 1.5 introduces comprehensive developer tooling to observe, inspect, and test the Hey Chat! voice assistant system at all levels. This phase creates the observability infrastructure needed to iterate rapidly on character behavior, story progression, and system functionality.

**Success Metric:** Developer can identify and debug any system behavior issue within 5 minutes using the provided tools.

---

## Product Vision

### Core Principle

Building a narrative-driven, multi-character AI system requires deep visibility into character behavior, story state, tool execution, and memory management. Phase 1.5 creates the developer experience infrastructure that makes rapid iteration possible.

### Developer Experience Goals

1. **Complete Visibility:** Every system decision and action is observable
2. **Easy Testing:** Can quickly set up, test, and tear down scenarios
3. **Fast Debugging:** Tools reveal issues immediately
4. **Story Validation:** Can verify narrative progression without full playthroughs
5. **Character Iteration:** Can test character variations in isolation

---

## Product Scope

### Phase 1.5: Observability & Testing Infrastructure

**Goal:** Comprehensive developer tools for testing, debugging, and validating system behavior

#### Functional Requirements

##### FR1: Story Beat Tool

**Purpose:** Inspect, navigate, and manipulate story progression

###### FR1.1: Story Beat Viewing

- Display all story beats for all chapters in the system
- Show beat configuration including:
  - Beat ID and name
  - Chapter association
  - Required vs optional status
  - Prerequisites (if any)
  - Completion status for current user
  - Available variants (short/medium/long)
- Filter beats by chapter
- Filter beats by completion status
- Search beats by name or ID

###### FR1.2: Chapter Flow Visualization

- Display chapter progression as Mermaid flow diagram
- Show dependencies between story beats
- Visualize required vs optional beats
- Indicate completion paths (which beats unlock which)
- Highlight current position in story
- Show chapter unlock criteria

###### FR1.3: Chapter Manipulation

- Change current active chapter
- Skip forward or backward through chapters
- Reset chapter progression to beginning
- Mark chapters as complete/incomplete
- Preview chapter unlock criteria

###### FR1.4: Story Beat Navigation

- Select any story beat to view details
- Jump to specific story beat (mark as current/next to deliver)
- Mark beats as delivered/undelivered
- Trigger beat delivery in next interaction
- Preview beat content (all variants)
- Test beat conditions (can this beat trigger now?)

---

##### FR2: Character Tool

**Purpose:** Inspect and validate character configuration and behavior

###### FR2.1: Character Configuration Display

- Show full character configuration for selected character:
  - Character name and role
  - Current voice mode/state
  - Personality traits and quirks
  - Voice characteristics (TTS settings)
  - Relationship states with other characters
  - Available capabilities/tools
- Display character metadata:
  - Introduction chapter
  - Active status (enabled/disabled)
  - Usage statistics (interaction count, average response length)

###### FR2.2: System Prompt Inspection

- Display the portion of system prompt related to selected character
- Show character-specific instructions
- View personality guidance
- See voice mode rules
- Display relationship context
- Highlight story beat injection points
- Copy prompt sections for testing/iteration

###### FR2.3: Character State Testing

- Preview how character would respond in different modes
- Test voice mode transitions
- Check tool access permissions

---

##### FR3: Tool Calls Inspection

**Purpose:** Observe and debug all tool interactions during conversations

###### FR3.1: Tool Call Timeline

- Display chronological list of all tool calls for current conversation
- Show for each call:
  - Timestamp
  - Tool name
  - Calling character (if applicable)
  - Request parameters (formatted JSON)
  - Response data (formatted JSON)
  - Execution duration
  - Success/error status
- Filter by tool type
- Filter by character
- Search tool calls by parameter or response content

###### FR3.2: Tool Call Detail View

- Expand individual tool call to see:
  - Full request payload (pretty-printed)
  - Full response payload (pretty-printed)
  - Stack trace or execution path
  - Character reasoning (why this tool was called)
  - Impact on conversation state
- Copy request/response for debugging
- Replay tool call with same parameters
- Edit and retry tool call with modified parameters

---

##### FR4: Memory Tool

**Purpose:** Inspect and manipulate user memory and conversation context

###### FR4.1: Memory Viewing

- Display all memories for current user
- Show for each memory:
  - Memory ID
  - Category/type (preference, fact, relationship, event)
  - Content/value
  - Source (when/how it was learned)
  - Created timestamp
  - Last accessed timestamp
  - Importance/weight (if applicable)
- Filter memories by category
- Search memories by content
- Sort by recency, importance, or category

###### FR4.2: Memory Creation

- Add new memories manually
- Specify memory type/category
- Set importance/weight
- Add timestamp or source context
- Validate memory format
- Preview impact on character context

###### FR4.3: Memory Editing

- Modify existing memory content
- Change memory category
- Adjust importance/weight
- Update timestamps
- Add notes or metadata
- Track edit history

###### FR4.4: Memory Deletion

- Delete individual memories
- Bulk delete by filter (category, date range)
- Archive memories (soft delete)
- Restore archived memories
- Clear all memories for user (with confirmation)

###### FR4.5: Memory Impact Analysis

- Show which memories are currently loaded in context
- Display token count per memory
- Highlight memories referenced in recent conversations

---

##### FR5: User Testing & Management

**Purpose:** Manage test users and switch contexts for isolated testing

###### FR5.1: User Creation

- Create new test user with auto-generated name
- Generate realistic test names (e.g., "TestUser_Amber_1738", "Dev_Jordan_4829")
- Initialize clean user state (no memories, no progression)
- Set optional user attributes (preferences, restrictions)
- Choose starting chapter (default: Chapter 1)

###### FR5.2: User Deletion

- Delete test users
- Show confirmation with user stats (interactions, memories, chapter)
- Cascade delete all user data (conversations, memories, state)
- Cannot delete primary/production users (safety check)
- Bulk delete test users

###### FR5.3: User Switching

- Switch active user context
- All tools reflect selected user's state:
  - Story progression shows their chapter/beats
  - Memory tool shows their memories
  - Conversation history loads their sessions
  - Tool calls show their interaction history
- Clearly indicate which user is active
- Persist user selection across tool sessions

###### FR5.4: User State Inspection

- View comprehensive user profile:
  - User ID and name
  - Current chapter and story progress
  - Total interactions count
  - Memory count by category
  - Conversation count
  - Account created date
  - Last interaction timestamp
- Compare users side-by-side
- Export user state (for backup/testing)
- Import user state (restore scenarios)

###### FR5.5: User Context Preview

- See full context that would be sent to LLM for selected user
- Display:
  - Active memories
  - Recent conversation history
  - Story beat status
  - Character relationship states
  - Current chapter context
- Calculate token usage for context
- Validate context doesn't exceed limits

---

## Technical Requirements

### TR1: Tool Interface

- All tools accessible via web-based dashboard
- Responsive design for desktop development
- Real-time updates via WebSocket or polling
- RESTful API backend for all tool operations
- Keyboard shortcuts for common operations
- Dark mode support (developer friendly)

### TR2: Data Access Layer

- Unified API for accessing system state
- Read-only mode to prevent accidental changes
- Transaction support for multi-step operations
- Validation layer to prevent invalid state
- Audit logging of all tool operations

### TR3: Performance

- Tool operations complete within 1 second
- Large data sets (>100 items) use pagination
- Real-time updates don't impact conversation latency
- Tools can run alongside active conversations

### TR4: Safety & Validation

- Confirmation prompts for destructive operations
- Validation prevents invalid state transitions
- Read-only mode available for safe inspection
- Ability to snapshot/restore system state
- Tools clearly marked as "development only"

---

## User Stories

### As a developer, I want to

**Story Beat Tool:**

- View all story beats at a glance so I can understand narrative structure
- See chapter flow diagrams to validate story progression logic
- Jump to specific story beats to test narrative moments without full playthrough
- Change chapters to test different phases of the system

**Character Tool:**

- Inspect character configuration to debug personality inconsistencies
- View system prompts to understand character behavior
- Validate character states before testing conversations

**Tool Calls Inspection:**

- See all tool calls during a conversation to understand what the system did
- Debug failed tool calls with full request/response data
- Identify performance bottlenecks by execution time
- Replay tool calls to reproduce issues

**Memory Tool:**

- View all memories to understand what the system knows about a user
- Add test memories to create specific scenarios
- Delete incorrect memories that are affecting behavior
- Validate memory retrieval to ensure context relevance

**User Testing:**

- Create fresh test users to validate onboarding experience
- Switch between users to test different scenarios in isolation
- Delete test users to clean up after testing sessions
- Compare user states to understand differences in progression

---

## Use Cases

### UC1: Debug Story Beat Not Triggering

**Scenario:** Developer notices "recipe_help" beat never delivers
**Tool Flow:**

1. Open Story Beat Tool
2. Filter to Chapter 1 beats
3. Select "recipe_help" beat
4. Check prerequisites - sees it requires "awakening_confusion" first
5. Check user's beat status - "awakening_confusion" not delivered
6. Use Story Beat Tool to trigger "awakening_confusion"
7. Test "recipe_help" delivery in next interaction
8. Verify beat triggers correctly

**Expected Result:** Issue identified and resolved in <5 minutes

---

### UC2: Validate Character Voice Consistency

**Scenario:** Developer wants to ensure Delilah's Mama Bear mode is configured correctly
**Tool Flow:**

1. Open Character Tool
2. Select Delilah
3. View voice mode configurations
4. Read Mama Bear mode triggers and behavior
5. Check system prompt section for Mama Bear
6. Create test user with peanut allergy (Memory Tool)
7. Test conversation about recipe with peanuts
8. Verify Mama Bear mode activates via Tool Calls (character state change)

**Expected Result:** Voice mode validated without production testing

---

### UC3: Investigate Slow Response Times

**Scenario:** Developer notices conversation lagging
**Tool Flow:**

1. Open Tool Calls Inspection
2. View recent conversation
3. Sort by execution duration
4. Identify tool call taking 3+ seconds
5. Expand detail view
6. See full request/response
7. Identify inefficient query or API call
8. Make code changes to optimize

**Expected Result:** Performance bottleneck identified via timeline view

---

### UC4: Test Multi-Chapter Progression

**Scenario:** Developer wants to test Chapter 2 Hank introduction
**Tool Flow:**

1. Create new test user (User Testing)
2. Switch to test user context
3. Use Story Beat Tool to jump to Chapter 2
4. View Chapter 2 flow diagram
5. Mark Chapter 1 required beats as completed
6. Trigger "hank_arrival" beat
7. Test first Delilah-Hank interaction
8. Inspect memory to verify relationship context created
9. Delete test user when done

**Expected Result:** Chapter transition tested in isolation

---

### UC5: Recreate User-Reported Issue

**Scenario:** User reports Delilah "forgot" their gluten allergy
**Tool Flow:**

1. Create test user matching reporter
2. Use Memory Tool to add gluten allergy
3. Verify memory created with correct category
4. Start conversation about baking
5. Use Tool Calls Inspection to see if memory was retrieved
6. If not retrieved, check memory impact analysis
7. Identify memory retrieval bug or categorization issue
8. Fix code and retest

**Expected Result:** Issue reproduced and debugged with test user

---

## Non-Functional Requirements

### NFR1: Developer Productivity (CRITICAL)

- Tools reduce debugging time by 80% vs reading logs
- Common tasks completable with <5 clicks
- Zero-friction user switching and state manipulation
- Tools become primary development interface

### NFR2: Reliability (Important)

- Tools don't crash or freeze
- Invalid operations show helpful error messages
- Tools recover gracefully from backend errors
- State changes are atomic (no partial updates)

### NFR3: Usability (Important)

- Intuitive interface requiring minimal documentation
- Consistent design patterns across all tools
- Visual hierarchy guides attention to relevant information
- Keyboard shortcuts for power users

### NFR4: Performance (Important)

- Tool UI remains responsive (<100ms interactions)
- Large data sets load progressively
- Real-time updates don't cause jank
- Tools don't slow down main system

### NFR5: Safety (Important)

- Destructive operations require confirmation
- Easy undo for state changes
- Clear visual indicators for test vs production data
- Read-only mode prevents accidental changes

---

## Technical Architecture Considerations

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Dashboard                   │
│                     (Web Interface)                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Story   │Character │  Tool    │  Memory  │    User     │
│  Beat    │  Tool    │  Calls   │  Tool    │  Testing    │
│  Tool    │          │          │          │             │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
           │
           ├─────────────────────────────────────────┐
           │         Observability API Layer         │
           │    (RESTful + WebSocket endpoints)      │
           └─────────────────────────────────────────┘
           │
           ├─────────────────────────────────────────┐
           │       System State Access Layer         │
           │  (Read/Write interfaces to all state)   │
           └─────────────────────────────────────────┘
           │
┌──────────┴──────────┬──────────┬──────────┬─────────────┐
│   Story State DB    │ Memory DB│  User DB │   Tool Call │
│  (chapters, beats)  │          │          │  Event Log  │
└─────────────────────┴──────────┴──────────┴─────────────┘
```

### Data Storage

**Current Implementation:** JSON file-based storage

All system state is currently stored in JSON files. The observability tools will read and write to these existing JSON files rather than introducing a database layer.

#### Story State (JSON)

- Chapter definitions with prerequisites
- Story beat configurations and variants
- User progress tracking (beat completion status)
- Chapter unlock criteria and history

#### Memory (JSON)

- User memories categorized and timestamped
- Memory retrieval metadata (access count, last used)
- Memory importance/weight scores
- Memory source tracking (how learned)

#### User Data (JSON)

- User profiles and preferences
- User-specific state (current chapter, stats)
- User metadata (created date, interaction count)
- User context snapshots

#### Tool Call Event Log (JSON)

- Timestamped tool call records
- Request/response payloads
- Execution metadata (duration, status)
- Associated conversation/user context

**Note:** Database migration is explicitly out of scope for Phase 1.5. Tools will work with the existing JSON file structure.

### API Endpoints (Examples)

**Story Beat Tool:**

- `GET /api/story/chapters` - List all chapters
- `GET /api/story/beats?chapter=1` - Get beats for chapter
- `GET /api/story/beats/:beatId` - Get beat details
- `PUT /api/story/user/:userId/chapter` - Change user's chapter
- `POST /api/story/user/:userId/beat/:beatId/trigger` - Trigger beat delivery
- `GET /api/story/chapter/:chapterId/diagram` - Get Mermaid diagram

**Character Tool:**

- `GET /api/characters` - List all characters
- `GET /api/characters/:characterId` - Get character config
- `GET /api/characters/:characterId/prompt` - Get prompt section
- `GET /api/characters/:characterId/state?user=:userId` - Get state for user

**Tool Calls:**

- `GET /api/tool-calls?conversation=:convId` - Get calls for conversation
- `GET /api/tool-calls/:callId` - Get call details
- `GET /api/tool-calls/stats?user=:userId` - Get usage analytics
- `POST /api/tool-calls/:callId/replay` - Replay tool call

**Memory Tool:**

- `GET /api/memory/user/:userId` - Get all memories
- `POST /api/memory/user/:userId` - Create memory
- `PUT /api/memory/:memoryId` - Update memory
- `DELETE /api/memory/:memoryId` - Delete memory
- `GET /api/memory/user/:userId/context` - Preview context

**User Testing:**

- `POST /api/users/test` - Create test user
- `DELETE /api/users/:userId` - Delete user
- `PUT /api/context/active-user` - Switch active user
- `GET /api/users/:userId/state` - Get user state
- `POST /api/users/:userId/export` - Export user data
- `POST /api/users/import` - Import user data

### Security Considerations

- Tools only accessible in development/testing environments
- Authentication required for tool access
- Rate limiting to prevent accidental damage
- Audit log of all tool operations
- Separate development and production databases

---

## Implementation Priorities

### Priority 1: Foundation (Week 1)

- Observability API Layer
- System State Access Layer
- Basic web dashboard framework
- User Testing Tool (core functionality)

**Rationale:** Can't build other tools without data access. User switching enables isolated testing immediately.

### Priority 2: Core Inspection (Week 2)

- Story Beat Tool (viewing and navigation)
- Memory Tool (viewing and editing)
- Tool Calls Inspection (timeline and detail view)

**Rationale:** Most frequently needed for debugging and validation. Enables iterative character development.

### Priority 3: Advanced Features (Week 3)

- Character Tool (configuration and prompt inspection)
- Story Beat Tool (chapter flow diagrams)
- Tool Calls Analytics
- Memory Impact Analysis

**Rationale:** Enhances productivity but not blocking for basic development work.

### Priority 4: Polish & Optimization (Week 4)

- Real-time updates
- Keyboard shortcuts
- Export/import functionality
- Performance optimizations
- UI/UX refinements

**Rationale:** Quality of life improvements after core functionality proven.

---

## Success Criteria

### Quantitative Metrics

- **Debugging Speed:** 90% of issues identified in <5 minutes using tools
- **Test Setup Time:** Create and configure test scenario in <2 minutes
- **Tool Performance:** All operations complete in <1 second
- **Test Coverage:** 100% of system state accessible via tools
- **Tool Adoption:** Developer uses tools for 100% of debugging sessions

### Qualitative Metrics

- **Developer Confidence:** Can test any scenario without production risk
- **Iteration Speed:** Character behavior changes testable in minutes
- **Issue Reproduction:** Can recreate user-reported bugs reliably
- **State Understanding:** Always know what system is doing and why
- **Testing Joy:** Tools make testing feel productive, not tedious

### Critical Success Factors

1. Tools provide complete visibility into system state
2. User switching enables true isolation for testing
3. Story navigation allows non-linear testing
4. Tool calls inspection reveals "why" not just "what"
5. Memory manipulation enables scenario creation

---

## Open Questions

### Tool Interface

- **DECISION:** Web dashboard is sufficient for Phase 1.5. CLI tools deferred to later phases.
- **DECISION:** Real-time updates not required. Standard HTTP polling or manual refresh acceptable since debugging doesn't require low latency like voice interactions.
- **DECISION:** Query/data export capabilities deferred to Phase 2 (automation phase).

### Data Management

- **DECISION:** Tool call event log retention not automated in Phase 1.5. Manual cleanup acceptable.
- **DECISION:** Memory edits not versioned/tracked. Too much complexity for this phase.
- **DECISION:** Export/import via direct JSON file system access. No special tooling needed in Phase 1.5.

### Testing Workflows

- **DECISION:** Test scenario templates deferred to next phase (automation/test suite).
- **DECISION:** Automated test runner integration deferred to next phase.
- **DECISION:** Screenshot/recording features deferred to next phase. Phase 1.5 provides conversation history viewing for selected user.

### Integration

- **DECISION:** Tools integrated into main dev interface (not separate application).
- **DECISION:** Observability tools kept separate from existing Python logging infrastructure for now. May integrate in future phase.
- **DECISION:** Story/character configuration version control via Git and pull requests. No special tooling needed.

---

## Dependencies

### Blocks

- Phase 2 development (need tools to debug multi-character interactions)
- Character iteration cycles (need visibility to validate changes)
- Story beat refinement (need flow diagrams to understand structure)

### Blocked By

- Phase 1 completion (need base system to observe)
- Data persistence layer (need state to inspect)
- Tool call infrastructure (need events to log)

---

## Approval & Sign-off

**Product Owner:** Justin
**Date:** January 2025

**Next Steps:**

1. Review and approve PRD
2. Create technical architecture document
3. Identify existing code that supports these tools
4. Plan implementation sprints
5. Begin Priority 1 implementation

---

*This PRD will be updated as tool requirements evolve through development and usage.*
