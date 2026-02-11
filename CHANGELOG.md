# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Phase 2: Multi-character coordination with Hank
- Phase 3: Three-way panel discussions with Rex
- Advanced context management and memory retrieval

### Recent Changes (unreleased)

- Rename: Replaced canonical character name "Cave" / "Cave Johnson" with "Rex" / "Rex Armstrong" across non-historical docs, UI text, and story data to standardize the leader identity.
- New: Added canonical character guide `docs/narrative/CHARACTER_REX.md` describing voice modes, TTS guidance, and interaction notes for Rex Armstrong.
- Story: Updated `story/chapters.json` and `docs/narrative/STORY_CHAPTERS.md` to use `rex_*` beat IDs and to reflect Rex's arrival and beats.
- Docs/UI: Updated multiple PRDs, architecture docs, milestone reports, and frontend components to reference Rex (non-historical content only).
- Note: Historical logs, diagnostics, and append-only tool call records were preserved unchanged to maintain auditability.
 - Release: Phase 4 — Hank voice tuning completed (2026-02-11). Refined `working` mode (iteration_5_final), tuned SSML breaks and stability/style parameters; diagnostics saved to `diagnostics/phase4_audio` and status added in `docs/PHASE4_STATUS.md`.

## [1.5.0] - 2026-01-29

### Added

#### Phase 1.5: Observability & Testing Tools

Complete developer dashboard for inspecting, testing, and debugging the voice assistant system.

#### Milestone 4: User Testing Tool

- User lifecycle management (create, switch, delete test users)
- Test user creation with auto-generated IDs and customizable starting state
- Production user protection (cannot delete production users like user_justin)
- User state summary displaying profile, story progress, memories, and activity
- User data export to JSON for backup or migration
- Multi-user support across all observability tools
- Active user switcher in dashboard header with persistence

#### Milestone 5: Tool Calls Inspection

- JSONL-based tool call logging system for append-only event tracking
- Timeline view with chronological display of all tool executions
- Advanced filtering by tool name, character, status (success/error), and time range
- Detailed request/response inspection with full JSON display
- Copy-to-clipboard functionality for debugging
- Statistics dashboard with aggregate metrics
- Per-tool breakdown (calls, success rate, average duration)
- Per-character usage patterns and preferences
- Performance metrics including slowest calls identification
- Recent error tracking for troubleshooting

#### Milestone 6: Memory Extraction & Retrieval System

- Automatic memory extraction from conversations using AI
- `save_memory` tool for characters to capture user information
- Memory retrieval in system prompts with category grouping
- Support for 5 memory categories:
  - dietary_restriction (allergies, intolerances)
  - preference (likes, dislikes, preferences)
  - fact (user attributes, capabilities, background)
  - relationship (inter-character or user relationships)
  - event (significant past events, milestones)
- Comprehensive tool instructions for Delilah character
- Importance-based memory loading (1-10 scale)
- Memory access tracking (last_accessed, access_count)
- Integration with conversation flow for context enrichment

#### Milestone 7: Character Tool

- Character configuration inspection for all defined characters
- System prompt viewing with full user context
- Voice mode triggers and characteristics display
- Character state for selected user showing:
  - Current voice mode and relationship context
  - Available capabilities and active story beats
  - Relevant memories filtered by importance
- Token counting for prompt planning and optimization
- Character personality trait viewing
- TTS configuration display
- Locked vs unlocked character indication

#### Infrastructure & Foundation

- FastAPI observability API with Bearer token authentication
- React + TypeScript frontend with Vite
- React Query for data fetching and caching
- Dark theme consistent across all tools
- File locking for safe concurrent access to JSON data
- CORS configuration for multiple development ports
- Dashboard navigation with tab-based tool switching
- Comprehensive error handling and loading states
- Responsive design for various screen sizes

### Changed

- Observability dashboard now supports multi-user context switching
- All tools respect active user selection and update dynamically
- Memory system migrated from simple preferences to structured Memory objects
- System prompts now include user-specific memory context
- Character system enhanced to render tool instructions in prompts
- API authentication improved with consistent token handling across endpoints
- User state model expanded to include UserMemories collection

### Fixed

- Chat interface API connectivity issues resolved
- Observability dashboard navigation improved with proper routing
- Memory tool context preview token estimation accuracy
- Story Beat Tool display of delivery timestamps and variants
- Tool call logging file permissions and concurrent access
- WebSocket message handling for multi-user scenarios

## [1.0.0] - 2026-01-27

### Added

#### Phase 1: Core Voice Assistant System

Foundation for narrative-driven voice assistant with character Delilah Mae.

#### Core Systems

- FastAPI backend with WebSocket communication
- React frontend for chat interface
- User state management with JSON persistence
- Configuration system for characters, story, and tools

#### Character System

- Character model with personality traits and voice modes
- Delilah Mae "Lila" character with 6 distinct voice modes:
  - PASSIONATE: High energy for foods she loves
  - PROTECTIVE: Controlled intensity when food done wrong
  - MAMA_BEAR: Soft, protective for allergies/restrictions
  - STARTLED: High-pitched reactions to surprises
  - DEADPAN: Flat, minimal for non-food tasks
  - WARM_BASELINE: Bright and friendly default
- Voice mode selection based on conversation context
- Character-specific capabilities and specializations
- TTS integration with ElevenLabs for natural speech

#### Story Engine

- Story beat tracking and delivery system
- Chapter progression with unlock criteria
- Beat types: one_shot and progression
- Variant support: brief, standard, full
- Prerequisite checking and conditional delivery
- User story progress persistence
- Beat delivery history with timestamps

#### Tool System

- Function calling integration with Claude API
- Tool registration and execution framework
- Built-in tools:
  - `set_timer`: Create timers with labels and durations
  - `get_recipe`: Search and retrieve recipe information
  - `unit_conversion`: Convert between measurement units
  - `cooking_advice`: Provide cooking tips and techniques
- Tool result handling and error management

#### Conversation Flow

- LLM integration with Claude API (claude-3-5-sonnet)
- System prompt generation with character context
- Message history management with token budgeting
- Voice mode instructions in prompts
- Story beat integration in responses
- Tool call orchestration

#### Memory & State

- User profile management
- Interaction tracking and statistics
- Persistent state across conversations
- Chapter and beat progress tracking
- Memory migration from preferences

#### Testing Infrastructure

- Comprehensive E2E testing suite
- API endpoint tests
- WebSocket communication tests
- Story progression tests
- Tool execution tests
- Memory persistence tests

### Technical Details

#### Backend Stack

- Python 3.11+
- FastAPI for REST and WebSocket APIs
- Anthropic Claude API for LLM
- ElevenLabs API for TTS
- Pydantic for data validation
- File-based JSON storage

#### Frontend Stack

- React 18
- TypeScript
- Vite for build tooling
- WebSocket for real-time communication

#### Development Tools

- pytest for testing
- shell scripts for E2E validation
- Virtual environment for Python dependencies
- npm for JavaScript dependencies

## [0.1.0] - 2026-01-20

### Added

- Initial project structure
- Character design documents
- Story arc planning (11 chapters)
- Voice guides for Delilah and Hank
- Project vision and requirements (CLAUDE.md)

---

[Unreleased]: https://github.com/username/repo/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/username/repo/compare/v1.0.0...v1.5.0
[1.0.0]: https://github.com/username/repo/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/username/repo/releases/tag/v0.1.0
