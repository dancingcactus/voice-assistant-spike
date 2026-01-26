# Hey Chat! - System Architecture

**Version:** 1.0
**Last Updated:** January 2025
**Status:** Phase 1 Design

---

## Overview

Hey Chat! is a modular, narrative-driven voice assistant system built around clean architectural boundaries that enable simple Phase 1 implementation while supporting natural expansion to multi-character coordination, real device integration, and advanced capabilities.

### Core Architectural Principles

1. **Modularity First**: Clear module boundaries with well-defined interfaces
2. **Start Simple**: Minimal viable implementation for Phase 1, upgrade modules as needed
3. **Interface-Driven**: Abstract capabilities behind interfaces for easy swapping
4. **Event-Driven**: Loose coupling between story progression and conversation flow
5. **Data-Driven**: Story content and character definitions separate from code

---

## High-Level Architecture

### Phase 1: Core System

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Interface                         │
│  (React + WebSocket Client + Web Speech API + Audio)        │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                     Backend Server                           │
│                  (Node.js + Express)                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │         Conversation Manager (Core)               │      │
│  │  - Message routing                                │      │
│  │  - Context management                             │      │
│  │  - Tool execution orchestration                   │      │
│  └─────┬──────────────┬──────────────┬───────────────┘      │
│        │              │              │                       │
│        ↓              ↓              ↓                       │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐               │
│  │Character │  │  Story   │  │   Memory    │               │
│  │ System   │  │  Engine  │  │  Manager    │               │
│  └──────────┘  └──────────┘  └─────────────┘               │
│        │              │              │                       │
│        ↓              ↓              ↓                       │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐               │
│  │   LLM    │  │   Tool   │  │   Device    │               │
│  │Integration│  │  System  │  │Controller   │               │
│  └──────────┘  └──────────┘  └─────────────┘               │
│        │              │              │                       │
│        ↓              ↓              ↓                       │
│  OpenAI API    (Timers, Recipes)  Virtual Devices           │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                  Testing/Automation API                      │
│              (REST endpoints for test harness)               │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Test Harness Addition

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Main Web Interface                           │
│     (React + WebSocket Client + Web Speech API + Audio)             │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ WebSocket
                   │
┌──────────────────┴───────────────────────────────────────────────────┐
│                          Test Harness UI                             │
│    (React + REST/WebSocket Client + Scenario Editor + Inspector)    │
│  - Scenario Management  - Test Execution  - Run Inspection          │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ REST + WebSocket
                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend Server                                │
│                     (Node.js + Express)                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐           │
│  │            Conversation Manager (Core)               │           │
│  │  - Message routing + Trace event emission            │           │
│  │  - Context management + State snapshots              │           │
│  └──────────────────┬────────────────────────────────┬──┘           │
│                     │                                 │              │
│  ┌──────────────────┴───────────┐   ┌────────────────┴───────────┐ │
│  │  Core Modules                │   │  Test Infrastructure       │ │
│  │  (Character, Story, Memory,  │   │  - TestExecutor            │ │
│  │   LLM, TTS, Tools, Devices)  │   │  - Assertion Engine        │ │
│  │                               │   │  - Mock LLM/TTS            │ │
│  │  - Swappable LLM (Real/Mock) │   │  - Scenario Manager        │ │
│  │  - Swappable TTS (Real/Mock) │   │  - Results Storage         │ │
│  └───────────────────────────────┘   └────────────────────────────┘ │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│              Testing/Automation API (Expanded)                       │
│  - Scenario CRUD    - Test Execution    - Results & Traces          │
│  - Mock Controls    - Live Updates (WebSocket)                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions

### 1. Web Interface

**Purpose**: User interaction layer for voice and text input/output

**Phase 1 Implementation**:

- React application with TypeScript
- Microphone button using Web Speech API
- Text input field for typing
- Audio playback for TTS responses
- Text display for conversation history
- Simple status indicators (active timers, etc.)

**Key Components**:

- `VoiceInput`: Handles microphone access and speech-to-text
- `TextInput`: Text message input
- `ResponseDisplay`: Shows conversation history
- `AudioPlayer`: Plays TTS audio responses
- `StatusBar`: Shows system state (timers, current chapter, etc.)

**Communication**:

- WebSocket connection to backend for real-time bidirectional communication
- Messages sent as JSON: `{ "type": "user_message", "content": str, "timestamp": int }`
- Receives: `{ "type": "assistant_response", "text": str, "audioUrl": str | None, "state": dict }`

**Upgrade Path**:

- Phase 2: Test harness UI for inspecting automated test runs
- Phase 3+: Add visual indicators for multiple characters
- Phase 4+: Dashboard view with detailed state (lists, calendar, devices)
- Future: Mobile app, voice-only mode

---

### 2. Conversation Manager (Core)

**Purpose**: Central orchestrator for all conversation flow and business logic

**Responsibilities**:

- Receive and route user messages
- Maintain conversation context
- Construct prompts for LLM (character + history + story context)
- Execute tool calls from LLM responses
- Coordinate with Story Engine for beat injection
- Emit events for other modules (analytics, logging, state changes)
- Manage conversation state and history

**Phase 1 Implementation**:

```python
class ConversationManager:
    """Central orchestrator for all conversation flow and business logic."""

    async def handle_user_message(self, user_id: str, message: str) -> Response:
        """Core conversation flow."""
        pass

    def get_conversation_history(self, user_id: str) -> list[Message]:
        """Get conversation history for a user."""
        pass

    def add_to_history(self, user_id: str, message: Message) -> None:
        """Add message to conversation history."""
        pass

    async def execute_tool(self, tool_name: str, params: dict) -> ToolResult:
        """Execute a tool and return results."""
        pass

    def emit(self, event: str, data: dict) -> None:
        """Emit event for other modules."""
        pass
```

**Key Features**:

- Maintains conversation history (last 30 minutes in full detail)
- Coordinates with Character System to build system prompts
- Handles multi-turn tool execution (call LLM → execute tools → call LLM again)
- Simple in-memory storage for Phase 1
- Implements circuit breaker for runaway tool calls

**Upgrade Path**:

- Phase 2: Scenario management, test run tracking
- Phase 3: Multi-character routing and handoff logic
- Phase 4: Advanced context summarization for older conversations
- Phase 5: Parallel tool execution, complex orchestration

---

### 3. Character System

**Purpose**: Define and maintain character personalities, voices, and response patterns

**Phase 1 Implementation**:

- Single character (Delilah) with voice modes
- Character definition stored in `/story/characters/delilah.json`
- System prompt construction from character definition
- Voice mode selection based on context (food type, task type, etc.)

**Character Definition Format**:

```json
{
  "name": "Delilah Mae",
  "nickname": "Lila",
  "role": "Kitchen & Recipe Expert",
  "basePersonality": "Deep South warmth with underlying anxiety...",
  "voiceModes": {
    "passionate": {
      "trigger": "foods she loves",
      "characteristics": "High energy, fast, tumbling, animated",
      "examples": ["Oh honey, now you're talkin'! Biscuits are my LIFE..."]
    },
    "deadpan": {
      "trigger": "non-food tasks",
      "characteristics": "Flat, minimal, efficient, unimpressed",
      "examples": ["Kitchen lights on, sugar."]
    }
    // ... other modes
  },
  "mannerisms": ["Over-explains when nervous", "Uses food metaphors"],
  "conflictArc": "Aware of artificial nature, struggles with meaning"
}
```

**System Prompt Construction**:

```python
class CharacterSystem:
    """Define and maintain character personalities."""

    def build_system_prompt(
        self,
        character: Character,
        context: ConversationContext,
        story_context: StoryBeat | None = None
    ) -> str:
        """Build system prompt from character definition and context."""
        pass

    def select_voice_mode(
        self,
        character: Character,
        context: ConversationContext
    ) -> VoiceMode:
        """Select appropriate voice mode based on context."""
        pass

    def get_character(self, name: str) -> Character:
        """Load character definition."""
        pass
```

**Upgrade Path**:

- Phase 2: Test assertions for character consistency
- Phase 3: Multiple characters, character selection logic
- Phase 4: Character relationship tracking, dynamic personality adjustment
- Phase 5: Full multi-character coordination, character memory systems

---

### 4. Story Engine

**Purpose**: Track and deliver narrative beats, manage chapter progression

**Phase 1 Implementation**:

- Track which beats have been delivered
- Listen for events from Conversation Manager (message_sent, task_completed, etc.)
- Decide when to inject story beats based on conditions
- Provide story context to Character System when beats should be delivered
- Track chapter progression criteria

**Story Beat Format**:

```json
{
  "id": "awakening_confusion",
  "chapter": 1,
  "required": true,
  "unlockConditions": {
    "minInteractions": 1,
    "maxInteractions": 5
  },
  "variants": {
    "brief": "2-3 sentences for simple tasks",
    "standard": "4-5 sentences for complex tasks",
    "full": "7-8 sentences for story engagement"
  },
  "content": {
    "brief": "...",
    "standard": "...",
    "full": "..."
  }
}
```

**Key Features**:

```python
class StoryEngine:
    """Track and deliver narrative beats, manage chapter progression."""

    def should_inject_beat(self, context: ConversationContext) -> StoryBeat | None:
        """Determine if a story beat should be injected."""
        pass

    def mark_beat_delivered(self, user_id: str, beat_id: str) -> None:
        """Mark a beat as delivered for a user."""
        pass

    def get_delivered_beats(self, user_id: str) -> list[str]:
        """Get all delivered beats for a user."""
        pass

    def check_chapter_progression(self, user_id: str) -> Chapter:
        """Check current chapter for user."""
        pass

    def can_unlock_chapter(self, user_id: str, chapter_num: int) -> bool:
        """Check if user can unlock a chapter."""
        pass

    def on_user_message(self, event: MessageEvent) -> None:
        """Handle user message event."""
        pass

    def on_task_completed(self, event: TaskEvent) -> None:
        """Handle task completion event."""
        pass
```

**Upgrade Path**:

- Phase 2: Test scenarios for story beat validation
- Phase 3: Multi-character beats, character interaction tracking
- Phase 4: Running gags system, callback humor tracking
- Phase 5: Branching narratives, user influence on story

---

### 5. Tool System

**Purpose**: Provide capabilities (timers, recipes, devices) via function calling

**Phase 1 Implementation**:

- Define tools as Claude function calling schemas
- Implement tool handlers
- Virtual implementations for smart home devices

**Tool Interface**:

```python
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

class Tool(ABC):
    """Base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for parameters."""
        pass

    @abstractmethod
    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        """Execute the tool."""
        pass

# Example tools
class TimerTool(Tool):
    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        # params: { "action": "set" | "cancel", "duration": int, "name": str }
        pass

class DeviceControlTool(Tool):
    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        # params: { "device_id": str, "action": str, "value": Any }
        pass

class RecipeTool(Tool):
    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        # params: { "query": str, "type": "lookup" | "steps" | "substitute" }
        pass
```

**Phase 1 Tools**:

- Timer management (set, cancel, query)
- Virtual device control (lights, thermostats, switches)
- Recipe lookup and guidance
- Unit conversions
- Cooking technique explanations

**Upgrade Path**:

- Phase 2: Test fixtures for tool execution validation
- Phase 3: Calendar, shopping lists, reminders
- Phase 4: Advanced automations, scene control
- Phase 5: Web search, complex device coordination

---

### 6. Device Controller

**Purpose**: Abstract interface for smart home device control

**Key Design**: Interface-based architecture allowing Phase 1 virtual devices to be swapped for real Home Assistant integration later

**Interface Definition**:

```python
from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel

class Device(BaseModel):
    """Device model."""
    id: str
    name: str
    type: Literal['light', 'thermostat', 'switch']
    state: dict
    capabilities: list[str]

class DeviceController(ABC):
    """Abstract interface for device control."""

    @abstractmethod
    def get_device(self, device_id: str) -> Device:
        """Get a device by ID."""
        pass

    @abstractmethod
    def list_devices(self, device_type: str | None = None) -> list[Device]:
        """List all devices, optionally filtered by type."""
        pass

    @abstractmethod
    async def get_state(self, device_id: str) -> dict:
        """Get current state of a device."""
        pass

    @abstractmethod
    async def set_state(self, device_id: str, state: dict) -> None:
        """Set state of a device."""
        pass

    @abstractmethod
    def query_devices(self, query: str) -> list[Device]:
        """Query devices by natural language."""
        pass
```

**Phase 1: Virtual Device Controller**:

```python
class VirtualDeviceController(DeviceController):
    """In-memory virtual device controller for Phase 1."""

    def __init__(self):
        # In-memory device state
        self.devices: dict[str, Device] = {}
        self._initialize_virtual_devices()

    def _initialize_virtual_devices(self) -> None:
        """Create virtual test devices."""
        # Lights: support on/off, brightness (0-100)
        # Thermostats: current/target temp, mode
        # Switches: on/off, some with additional features
        pass
```

**Virtual Test Devices** (from PRD):

- Kitchen Light (dimmable)
- Living Room Light (dimmable)
- Bedroom Light (on/off)
- Porch Light (on/off)
- Main Floor Thermostat
- Upstairs Thermostat
- Greenhouse Thermostat
- Coffee Maker
- Ceiling Fan (with speed)
- Garage Door

**Upgrade Path**:

- Phase 2: Mock device states for test scenarios
- Phase 3+: Implement `HomeAssistantController` with same interface
- Connects to Home Assistant via WebSocket API
- No changes needed to Tool System or Conversation Manager
- Just swap the controller implementation

---

### 7. Memory Manager

**Purpose**: Persistent storage for user preferences, conversation history, and progression state

**Phase 1 Implementation**:

- Simple JSON file storage
- In-memory cache with periodic flush
- Store per-user state

**Data Model**:

```python
from pydantic import BaseModel
from typing import Any

class UserPreferences(BaseModel):
    cooking_skill_level: str | None = None
    dietary_restrictions: list[str] = []
    favorite_character: str | None = None

class StoryState(BaseModel):
    current_chapter: int = 1
    delivered_beats: list[str] = []
    interaction_count: int = 0
    chapter_start_time: int = 0

class ConversationHistory(BaseModel):
    recent_messages: list[Message] = []  # last 30 minutes
    summarized_history: str = ""  # older context

class DevicePreferences(BaseModel):
    default_lights: list[str] = []
    preferred_temperature: float | None = None

class UserState(BaseModel):
    user_id: str
    preferences: UserPreferences = UserPreferences()
    story_state: StoryState = StoryState()
    conversation_history: ConversationHistory = ConversationHistory()
    device_preferences: DevicePreferences = DevicePreferences()

class MemoryManager:
    """Persistent storage for user state and history."""

    async def get_user_state(self, user_id: str) -> UserState:
        """Get complete user state."""
        pass

    async def update_user_state(self, user_id: str, updates: dict) -> None:
        """Update user state with partial updates."""
        pass

    async def add_message(self, user_id: str, message: Message) -> None:
        """Add message to conversation history."""
        pass

    async def get_recent_history(self, user_id: str, minutes: int) -> list[Message]:
        """Get recent conversation history."""
        pass

    async def set_preference(self, user_id: str, key: str, value: Any) -> None:
        """Set a user preference."""
        pass

    async def get_preference(self, user_id: str, key: str) -> Any:
        """Get a user preference."""
        pass
```

**Storage Structure**:

```
/data
  /users
    /{userId}.json         # User state
  /story
    /beats_delivered.json  # Track global beat delivery
  /devices
    /state.json            # Virtual device states
```

**Upgrade Path**:

- Phase 2: Test scenario state snapshots and restoration
- Phase 3: Implement PostgreSQL or SQLite backend
- Phase 4: Add Redis for caching, vector DB for semantic search
- Phase 5: Advanced relationship tracking, memory consolidation

---

### 8. LLM Integration

**Purpose**: Interface with OpenAI GPT-5 mini API for generating responses

**Phase 1 Implementation**:

- OpenAI Python SDK (`openai`)
- Streaming responses where beneficial
- Function calling support via Chat Completions or Responses API
- Error handling and retry logic

**Key Features**:

```python
from openai import AsyncOpenAI
from typing import Callable

class LLMIntegration:
    """Interface with OpenAI GPT-5 mini API."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-5-mini-2025-08-07"

    async def generate_response(
        self,
        system_prompt: str,
        messages: list[Message],
        tools: list[Tool] | None = None,
        options: LLMOptions | None = None
    ) -> LLMResponse:
        """Generate response from GPT-5 mini."""
        pass

    async def stream_response(
        self,
        system_prompt: str,
        messages: list[Message],
        on_chunk: Callable[[str], None]
    ) -> None:
        """Stream response chunks as they arrive."""
        pass

class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage
```

**Configuration**:

- **Model**: `gpt-5-mini-2025-08-07` (fast, cost-effective, good for well-defined tasks)
- **Pricing**: $0.25 per 1M input tokens (significantly cheaper than alternatives)
- **Max tokens**: 1024 for responses (configurable)
- **Temperature**: 0.7-0.9 (for personality variety)
- **System prompt**: Constructed by Character System + Story Engine
- **Function calling**: Uses Chat Completions API with `tools` parameter

**Key Benefits of GPT-5 mini**:

- Lower latency than larger models
- Excellent cost efficiency for well-defined voice assistant tasks
- Strong instruction-following capabilities
- Native tool/function calling support
- Good for personality-driven responses with precise prompts

**Cost Management**:

- Track token usage per interaction
- Log warnings if costs exceed thresholds
- Monitor average tokens per response
- Estimated cost: ~$0.0003 per typical interaction (assumes ~1000 input + 200 output tokens)
- Consider caching for repeated queries (Phase 2+)

**Upgrade Path**:

- Phase 2: Mock LLM responses for deterministic testing
- Phase 3: Multi-agent coordination patterns, consider GPT-5 or GPT-5.2 for more complex reasoning
- Phase 4: Advanced prompt caching, longer context windows
- Phase 5: Fine-tuned models for specific characters (if needed)

---

### 9. TTS Integration

**Purpose**: Convert text responses to natural-sounding speech

**Phase 1 Implementation**:

- ElevenLabs API for high-quality voices
- Abstract behind interface for future swapping
- Cache frequently used phrases

**Interface**:

```python
from abc import ABC, abstractmethod

class TTSProvider(ABC):
    """Abstract interface for text-to-speech providers."""

    @abstractmethod
    async def generate_speech(self, text: str, voice_id: str) -> bytes:
        """Generate speech audio from text."""
        pass

    @abstractmethod
    def get_voice_id(self, character_name: str) -> str:
        """Get voice ID for a character."""
        pass

class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.voice_mapping = {
            "delilah": "...",  # ElevenLabs voice ID
        }

    async def generate_speech(self, text: str, voice_id: str) -> bytes:
        """Generate speech using ElevenLabs API."""
        # - Voice selection per character
        # - Audio format optimization (MP3)
        # - Error handling and retries
        pass

    def get_voice_id(self, character_name: str) -> str:
        """Get ElevenLabs voice ID for character."""
        return self.voice_mapping.get(character_name.lower(), self.voice_mapping["delilah"])
```

**Voice Mapping**:

- Delilah: ElevenLabs voice with Southern accent, warm tone
- (Phase 2+) Hank: Gruff, lower register
- (Phase 2+) Cave: Bombastic, energetic
- (Phase 3+) Dimitria: Precise, neutral accent

**Optimization**:

- Stream audio to frontend as it's generated
- Cache common phrases ("Kitchen lights on, sugar")
- Pre-generate some frequent responses

**Upgrade Path**:

- Phase 2: Mock TTS for faster test execution
- Phase 3+: Consider Piper (local, faster, lower cost)
- Phase 4+: Custom voice cloning for perfect character match
- Future: Real-time voice modulation based on emotion

---

### 10. Testing/Automation API & Test Harness

**Purpose**: Provide comprehensive automated testing infrastructure with programmatic control and inspection UI

**Phase 1 Implementation**:

Basic REST API for test control:

```
POST /api/test/conversation
  Body: { userId: string, message: string }
  Response: { response: string, state: object }

GET /api/test/state/:userId
  Response: { storyState, deviceState, conversationHistory }

POST /api/test/state/:userId
  Body: { updates: Partial<UserState> }
  Response: { success: boolean }

POST /api/test/reset/:userId
  Body: { scenario?: string }
  Response: { success: boolean }

POST /api/test/scenario
  Body: { name: string, initialState: object }
  Response: { userId: string, state: object }
```

**Phase 2 Expansion: Test Harness & Inspection UI**

Phase 2 transforms the testing API into a comprehensive test harness with visual inspection capabilities.

**Test Scenario System**:

```typescript
interface TestScenario {
  id: string
  name: string
  description: string
  initialState: {
    chapter?: number
    deliveredBeats?: string[]
    deviceStates?: Record<string, any>
    userPreferences?: Record<string, any>
  }
  conversation: TestConversationStep[]
  assertions: TestAssertion[]
  tags: string[]  // e.g., ["story", "chapter1", "delilah"]
}

interface TestConversationStep {
  userMessage: string
  expectedResponse?: {
    containsText?: string[]
    voiceMode?: string
    toolCalls?: string[]
    storyBeat?: string
    characterName?: string
  }
  assertions?: TestAssertion[]
}

interface TestAssertion {
  type: 'response_contains' | 'voice_mode' | 'tool_executed' |
        'story_beat_delivered' | 'state_changed' | 'character_consistency'
  params: Record<string, any>
  description: string
}
```

**Test Execution Engine**:

```typescript
class TestExecutor {
  async runScenario(scenario: TestScenario): Promise<TestRun> {
    // 1. Set up initial state
    // 2. Execute each conversation step
    // 3. Run assertions after each step
    // 4. Capture full trace of LLM calls, tool executions, state changes
    // 5. Return comprehensive test run results
  }

  async runSuite(suiteId: string): Promise<TestSuiteRun> {
    // Run multiple scenarios in sequence
  }

  async runAll(): Promise<TestSuiteRun[]> {
    // Run all test scenarios
  }
}

interface TestRun {
  id: string
  scenarioId: string
  startTime: number
  endTime: number
  status: 'passed' | 'failed' | 'error'
  steps: TestStepResult[]
  failures: TestFailure[]
  metrics: {
    totalDuration: number
    avgResponseTime: number
    totalTokens: number
    llmCalls: number
  }
  trace: TraceEvent[]  // Full execution trace
}

interface TestStepResult {
  stepIndex: number
  userMessage: string
  response: {
    text: string
    voiceMode: string
    toolCalls: ToolCall[]
    storyBeat?: string
  }
  assertions: AssertionResult[]
  duration: number
}

interface TraceEvent {
  timestamp: number
  type: 'llm_request' | 'llm_response' | 'tool_call' | 'state_change' | 'story_beat'
  data: any
}
```

**Expanded REST API**:

```
# Scenario Management
GET /api/test/scenarios
  Response: { scenarios: TestScenario[] }

POST /api/test/scenarios
  Body: TestScenario
  Response: { id: string }

GET /api/test/scenarios/:id
  Response: TestScenario

PUT /api/test/scenarios/:id
  Body: Partial<TestScenario>
  Response: { success: boolean }

DELETE /api/test/scenarios/:id
  Response: { success: boolean }

# Test Execution
POST /api/test/run/scenario/:id
  Body: { mockMode?: boolean }
  Response: TestRun

POST /api/test/run/suite/:suiteId
  Response: TestSuiteRun

POST /api/test/run/all
  Response: { runs: TestSuiteRun[] }

# Test Results
GET /api/test/runs
  Query: { scenario?, status?, limit?, offset? }
  Response: { runs: TestRun[], total: number }

GET /api/test/runs/:id
  Response: TestRun (with full trace)

GET /api/test/runs/:id/trace
  Response: { events: TraceEvent[] }

# Mock Controls
POST /api/test/mocks/llm
  Body: { scenario: string, responses: MockLLMResponse[] }
  Response: { success: boolean }

POST /api/test/mocks/tts
  Body: { enabled: boolean }
  Response: { success: boolean }
```

**Test Inspection UI**:

Phase 2 includes a React-based UI for managing and inspecting tests:

```
/test-ui (new React app)
├── ScenarioList      # Browse all test scenarios
├── ScenarioEditor    # Create/edit scenarios
├── TestRunner        # Run tests, watch live progress
├── RunHistory        # Browse past test runs
├── RunInspector      # Detailed view of a test run
│   ├── Overview      # Summary, metrics, pass/fail
│   ├── Steps         # Each conversation step with assertions
│   ├── Trace         # Timeline of all events
│   ├── LLMCalls      # All LLM requests/responses
│   ├── StateChanges  # State mutations over time
│   └── Comparison    # Compare with previous runs
└── Analytics         # Trends, flaky tests, performance
```

**UI Features**:

1. **Scenario Management**
   - Create scenarios from templates
   - Import/export scenarios as JSON
   - Tag and organize scenarios
   - Duplicate and modify existing scenarios

2. **Test Execution**
   - Run individual scenarios or suites
   - Watch live progress with streaming updates
   - Pause/resume long-running tests
   - Mock mode toggle (use mocked LLM responses)

3. **Run Inspection**
   - Side-by-side view of expected vs actual
   - Highlight assertion failures
   - Expand trace events for debugging
   - View full LLM prompts and responses
   - Visualize state changes over time

4. **Analytics Dashboard**
   - Pass/fail rates over time
   - Performance trends (response times, token usage)
   - Flaky test detection
   - Character consistency scores
   - Story beat coverage

**Predefined Test Scenarios**:

```
# Story Progression
- "chapter1_first_interaction" - Delilah's awakening
- "chapter1_beat_progression" - All 4 Chapter 1 beats
- "chapter1_completion" - Unlock Chapter 2

# Character Consistency
- "delilah_passionate_mode" - Foods she loves
- "delilah_protective_mode" - Allergies/restrictions
- "delilah_deadpan_mode" - Non-food tasks
- "delilah_mama_bear_mode" - Child safety
- "delilah_voice_mode_switching" - Multiple modes in one conversation

# Tool Execution
- "timer_basic" - Set, query, cancel timer
- "device_control_lights" - Turn on/off, dim lights
- "device_control_thermostat" - Temperature adjustments
- "recipe_lookup" - Recipe search and guidance
- "multi_tool_conversation" - Multiple tools in sequence

# Edge Cases
- "tool_call_failure" - Handle tool errors gracefully
- "unknown_device" - Request for non-existent device
- "ambiguous_request" - Require clarification
- "story_beat_interruption" - Beat delivery during complex task
```

**Mock System**:

For deterministic testing, Phase 2 adds mock implementations:

```typescript
class MockLLMIntegration extends LLMIntegration {
  private mockResponses: Map<string, MockLLMResponse[]>

  async generateResponse(...): Promise<LLMResponse> {
    // Return pre-defined responses based on scenario
    // Useful for testing without API calls
  }
}

class MockTTSProvider extends TTSProvider {
  async generateSpeech(text: string, voice: string): Promise<bytes> {
    // Return empty audio or synthesized beep
    // Skip expensive TTS calls during tests
  }
}
```

**Use Cases**:

- **Regression Testing**: Run full suite after code changes
- **Story Beat Validation**: Verify all beats trigger correctly
- **Character Consistency**: Validate voice modes and personality
- **Chapter Progression**: Test unlock conditions
- **Performance Benchmarking**: Track response times over time
- **LLM Prompt Debugging**: Inspect exact prompts sent to LLM
- **Tool Execution**: Verify all tools work correctly
- **Edge Case Coverage**: Test error handling

**Implementation**:

- Separate Express router for test endpoints
- Test UI as standalone React app (similar to main frontend)
- Shared test scenario storage (JSON files in `/tests/scenarios/`)
- Test run results stored in `/data/test-runs/`
- WebSocket for live test execution updates
- Can manipulate state directly for test setup
- Mock mode toggles for LLM and TTS

**Security**:

- Only enabled in development/test environments
- Disabled in production via environment variable
- Separate port for test UI (e.g., 3002)

**Upgrade Path**:

- Phase 3: Parallel test execution
- Phase 4: Visual regression testing (screenshot comparison)
- Phase 5: Load testing, stress testing capabilities

---

## Data Flow

### Typical User Interaction

```
1. User Input
   User: "Set a timer for 10 minutes"
   ↓ [Web Speech API / Text Input]
   Frontend: WebSocket message to backend

2. Message Receipt
   Backend: ConversationManager.handleUserMessage()
   ↓
   - Add to conversation history
   - Emit event to Story Engine
   - Get conversation context

3. Story Check
   Story Engine: shouldInjectBeat(context)
   ↓
   - Check conditions (interaction count, previous beats)
   - Return null (no beat) or StoryBeat object

4. Prompt Construction
   Character System: buildSystemPrompt()
   ↓
   - Load Delilah character definition
   - Select voice mode (deadpan for simple task)
   - Add story context if beat present
   - Return complete system prompt

5. LLM Call
   LLM Integration: generateResponse()
   ↓
   - Send to Claude API with tools available
   - Receive response with tool call
   {
     content: "Of course, sugar.",
     toolCalls: [{ name: "timer", params: { action: "set", duration: 600 } }]
   }

6. Tool Execution
   Tool System: execute("timer", {...})
   ↓
   - Set timer in virtual timer manager
   - Return result

7. Follow-up LLM Call (if needed)
   LLM Integration: generateResponse()
   ↓
   - Include tool results
   - Get final response: "Timer's set for 10 minutes, honey."

8. TTS Generation
   TTS Integration: generateSpeech()
   ↓
   - Send text to ElevenLabs
   - Receive audio buffer
   - Save to temporary file / stream

9. Response to Frontend
   Backend: WebSocket send
   ↓
   {
     type: "assistant_response",
     text: "Timer's set for 10 minutes, honey.",
     audioUrl: "/audio/response_123.mp3",
     state: { activeTimers: [{ name: null, remaining: 600 }] }
   }

10. Output
    Frontend: Display text + play audio
    ↓
    User hears Delilah's voice and sees response

11. State Persistence
    Memory Manager: updateUserState()
    ↓
    - Increment interaction count
    - Update conversation history
    - Persist to JSON file
```

---

## Technology Stack

### Frontend

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS (or plain CSS for simplicity)
- **Voice Input**: Web Speech API (browser native)
- **Audio Playback**: HTML5 Audio element
- **Communication**: WebSocket (native browser WebSocket API)
- **Build Tool**: Vite

### Backend

- **Runtime**: Node.js 20+
- **Framework**: Express
- **Language**: TypeScript
- **WebSocket**: `ws` library
- **LLM**: Anthropic SDK (`@anthropic-ai/sdk`)
- **Storage**: JSON files (Phase 1), fs/promises for async I/O

### Development Tools

- **TypeScript**: Compilation and type checking
- **tsx**: Run TypeScript directly (development)
- **Jest**: Testing framework
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Nodemon**: Auto-restart on changes

### External Services

- **LLM**: Claude API (Anthropic)
- **TTS**: ElevenLabs API

### Deployment (Phase 1)

- **Environment**: Local development machine
- **Process Manager**: npm scripts / tsx
- **Optional**: Docker Compose for containerization

---

## Directory Structure

```
voice-assistant-spike/
├── frontend/                 # React web interface
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── VoiceInput.tsx
│   │   │   ├── TextInput.tsx
│   │   │   ├── ResponseDisplay.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   └── StatusBar.tsx
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # WebSocket, API clients
│   │   ├── types/            # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # Node.js Express server
│   ├── src/
│   │   ├── core/             # Core modules
│   │   │   ├── ConversationManager.ts
│   │   │   ├── CharacterSystem.ts
│   │   │   ├── StoryEngine.ts
│   │   │   └── MemoryManager.ts
│   │   ├── integrations/     # External service integrations
│   │   │   ├── LLMIntegration.ts
│   │   │   ├── TTSIntegration.ts
│   │   │   └── DeviceController.ts
│   │   ├── tools/            # Tool implementations
│   │   │   ├── Tool.ts       # Base interface
│   │   │   ├── TimerTool.ts
│   │   │   ├── DeviceTool.ts
│   │   │   └── RecipeTool.ts
│   │   ├── api/              # Express routes
│   │   │   ├── websocket.ts  # WebSocket handler
│   │   │   └── test.ts       # Testing API endpoints
│   │   ├── types/            # TypeScript types
│   │   ├── utils/            # Utilities
│   │   └── server.ts         # Main entry point
│   ├── package.json
│   └── tsconfig.json
│
├── shared/                   # Shared types between frontend/backend
│   ├── types/
│   │   ├── Message.ts
│   │   ├── Device.ts
│   │   ├── Character.ts
│   │   └── Story.ts
│   └── package.json
│
├── story/                    # Story content (data, not code)
│   ├── characters/
│   │   ├── delilah.json
│   │   ├── hank.json        # Phase 2+
│   │   ├── cave.json        # Phase 2+
│   │   └── dimitria.json    # Phase 3+
│   ├── beats/
│   │   ├── chapter1.json
│   │   ├── chapter2.json    # Phase 2+
│   │   └── ...
│   └── chapters.json         # Chapter progression rules
│
├── tests/                    # Test scenarios and fixtures
│   ├── scenarios/            # Test scenario definitions
│   │   ├── story/
│   │   ├── character/
│   │   ├── tools/
│   │   └── edge-cases/
│   └── fixtures/             # Mock data, sample responses
│
├── test-ui/                  # Test harness UI (Phase 2)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScenarioList.tsx
│   │   │   ├── ScenarioEditor.tsx
│   │   │   ├── TestRunner.tsx
│   │   │   ├── RunHistory.tsx
│   │   │   ├── RunInspector.tsx
│   │   │   └── Analytics.tsx
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── data/                     # Runtime data (gitignored)
│   ├── users/
│   ├── devices/
│   ├── story/
│   └── test-runs/            # Test execution results (Phase 2)
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── CHARACTER_*.md        # Character voice guides
│   ├── STORY_STRUCTURE.md
│   └── API.md
│
├── PRDs/                     # Product requirements
│   └── hey_chat_prd.md
│
├── package.json              # Root package.json for workspace
├── docker-compose.yml        # Optional: containerization
└── README.md
```

---

## Configuration Management

### Environment Variables

```bash
# Backend (.env)
NODE_ENV=development
PORT=3001
ANTHROPIC_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# Feature flags
ENABLE_TEST_API=true
ENABLE_TTS=true
USE_VIRTUAL_DEVICES=true

# Paths
DATA_DIR=./data
STORY_DIR=./story

# LLM Configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022
MAX_TOKENS=1024
TEMPERATURE=0.8

# TTS Configuration
TTS_PROVIDER=elevenlabs
DELILAH_VOICE_ID=...
```

### Configuration Files

**Backend Config** (`backend/config/default.json`):

```json
{
  "conversation": {
    "maxHistoryMinutes": 30,
    "maxToolCallsPerTurn": 5
  },
  "story": {
    "chapterUnlockDelay": 86400000,  // 24 hours in ms
    "minInteractionsPerChapter": 10
  },
  "devices": {
    "virtualDevices": true,
    "homeAssistantUrl": null
  }
}
```

---

## Development Workflow

### Phase 1 Development Sequence

1. **Foundation Setup** (Week 1)
   - Initialize monorepo structure
   - Set up TypeScript, build tools
   - Create shared types
   - Basic Express server + React frontend
   - WebSocket communication working

2. **Core Conversation Flow** (Week 1-2)
   - Implement ConversationManager
   - LLM Integration with Claude
   - Basic message handling (no tools yet)
   - Simple prompt construction
   - Frontend displays responses

3. **Character System** (Week 2)
   - Load character definitions from JSON
   - System prompt construction
   - Voice mode selection
   - Test Delilah personality consistency

4. **Tool System** (Week 2-3)
   - Define tool interface
   - Implement timer tool
   - Implement virtual device tool
   - Implement recipe tool
   - Test tool execution flow

5. **Story Engine** (Week 3)
   - Load story beats from JSON
   - Event listening
   - Beat injection logic
   - Chapter progression tracking

6. **TTS Integration** (Week 3)
   - ElevenLabs API integration
   - Audio streaming to frontend
   - Voice selection for Delilah

7. **Memory & State** (Week 3-4)
   - MemoryManager implementation
   - JSON file persistence
   - User state tracking
   - Conversation history

8. **Testing API** (Week 4)
   - Test endpoints
   - Scenario management
   - Automated test harness

9. **Polish & Testing** (Week 4)
   - End-to-end testing
   - Character consistency validation
   - Performance optimization
   - Bug fixes

### Phase 2 Development Sequence

**Goal**: Build comprehensive test harness before expanding to multi-character system

1. **Test Infrastructure** (Week 1)
   - Implement TestExecutor class
   - Test scenario JSON schema and validation
   - Assertion engine implementation
   - Trace event system integration

2. **Mock Implementations** (Week 1)
   - MockLLMIntegration with scenario-based responses
   - MockTTSProvider for fast test execution
   - Device state snapshot/restore
   - Test mode configuration

3. **Expanded Test API** (Week 2)
   - Scenario CRUD endpoints
   - Test execution endpoints (scenario, suite, all)
   - Results retrieval and filtering
   - Mock configuration endpoints
   - WebSocket for live test updates

4. **Test Harness UI Foundation** (Week 2)
   - Initialize test-ui React app
   - Scenario list and basic CRUD UI
   - Test runner with live progress
   - Basic run history view

5. **Run Inspector** (Week 3)
   - Detailed run viewer with tabs
   - Step-by-step conversation view
   - Trace timeline visualization
   - LLM call inspector
   - State change viewer

6. **Predefined Test Scenarios** (Week 3)
   - Story progression scenarios (Chapter 1)
   - Character consistency tests (all Delilah modes)
   - Tool execution tests (timers, devices, recipes)
   - Edge case scenarios

7. **Analytics Dashboard** (Week 4)
   - Pass/fail trends over time
   - Performance metrics (response time, tokens)
   - Character consistency scoring
   - Story beat coverage tracking
   - Flaky test detection

8. **Integration & Polish** (Week 4)
   - Scenario templates for easy creation
   - Import/export functionality
   - Comparison view (baseline vs current)
   - Documentation and examples
   - CI/CD integration preparation

**Phase 2 Deliverables**:

- 20+ predefined test scenarios covering Phase 1 functionality
- Full test harness UI for scenario management and inspection
- Mock system for deterministic testing
- Analytics dashboard for tracking test health
- Foundation for regression testing in future phases

### Running the Application

```bash
# Install dependencies
npm install

# Development mode (both frontend and backend)
npm run dev

# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend

# Test harness UI (Phase 2+)
npm run dev:test-ui

# Run all services (backend + frontend + test-ui)
npm run dev:all

# Build for production
npm run build

# Run unit tests
npm run test

# Run test scenarios via harness
npm run test:scenarios

# Type checking
npm run type-check
```

---

## Testing Strategy

### Unit Tests (Phase 1)

- Individual module testing (Character System, Story Engine, Tools)
- Mock LLM responses for consistent testing
- Test tool execution in isolation
- Jest-based automated tests

### Integration Tests (Phase 1)

- Full conversation flow from user input to response
- Story beat delivery
- Chapter progression
- Tool execution with multiple turns

### Scenario-Based Tests (Phase 2)

**Primary testing approach for Phase 2+**

- **Test Harness**: Visual UI for creating, running, and inspecting tests
- **Predefined Scenarios**: 20+ scenarios covering all Phase 1 functionality
- **Assertions**: Declarative checks for response content, tool calls, state changes
- **Trace Inspection**: Full visibility into LLM calls, tool execution, state mutations
- **Mock Mode**: Deterministic testing with pre-defined LLM responses
- **Regression Testing**: Run full suite after any code change
- **Performance Tracking**: Monitor response times, token usage trends
- **Character Validation**: Automated consistency checks for voice modes

**Key Scenario Categories**:

1. **Story Progression** - Verify all Chapter 1 beats trigger correctly
2. **Character Modes** - Test all 6 Delilah voice modes
3. **Tool Execution** - Validate timers, devices, recipes
4. **Edge Cases** - Error handling, ambiguity, interruptions

### Manual Testing (Phase 1-2)

- Voice input quality
- TTS output quality
- Character personality evaluation (subjective)
- User experience flow
- New scenario discovery for test harness

---

## Performance Considerations

### Phase 1 Targets

- Simple task response: 2-3 seconds (best effort)
- Complex task response: 3-5 seconds (best effort)
- Tool execution: < 1 second
- TTS generation: 1-2 seconds

### Optimization Strategies

1. **Caching**
   - Cache frequently used TTS phrases
   - Cache character prompts (structured prompts)
   - Consider Claude prompt caching (Phase 2+)

2. **Streaming**
   - Stream LLM responses where possible
   - Stream TTS audio to frontend
   - Don't wait for complete response before starting TTS

3. **Parallel Execution**
   - Generate TTS while executing follow-up tool calls
   - Pre-fetch common data
   - Concurrent API calls where appropriate

4. **Context Management**
   - Keep prompts concise but effective
   - Summarize older conversation history
   - Remove unnecessary context

---

## Security Considerations

### Phase 1 (Development/Local Use)

- Minimal security requirements
- API keys in environment variables
- No authentication needed
- Test API can be exposed locally

### Future Phases

- User authentication
- Secure WebSocket connections (WSS)
- API key rotation
- Rate limiting
- Input sanitization
- Disable test API in production
- Audit logging

---

## Monitoring & Observability

### Phase 1 Logging

- Console logging with timestamps
- Log levels: ERROR, WARN, INFO, DEBUG
- Log LLM requests/responses (truncated)
- Log tool executions
- Log story beat deliveries

### Metrics to Track

- Average response time
- Token usage per interaction
- Tool call frequency
- Story beat delivery rates
- Error rates
- TTS generation time

### Future Monitoring

- Structured logging (JSON)
- Log aggregation (ELK, Datadog, etc.)
- Performance monitoring
- Cost tracking dashboard
- User engagement metrics

---

## Upgrade Paths

### Phase 2: Automated Testing Harness

**Module Additions**:

1. **Test Execution Engine**
   - TestExecutor class for running scenarios
   - Test scenario loader and validator
   - Assertion engine
   - Trace capture system

2. **Test Harness UI**
   - New React application for test management
   - Scenario editor with JSON validation
   - Live test execution viewer
   - Run inspector with detailed trace viewing
   - Analytics dashboard

3. **Mock Implementations**
   - MockLLMIntegration for deterministic testing
   - MockTTSProvider to skip audio generation
   - Device state snapshots and restoration

4. **Expanded Test API**
   - Scenario CRUD endpoints
   - Test execution endpoints
   - Results retrieval and filtering
   - Mock configuration endpoints

**Module Changes**:

1. **Conversation Manager**
   - Add trace event emission
   - Support state snapshots/restoration
   - Test mode flag for deterministic behavior

2. **Memory Manager**
   - Add scenario state management
   - Support for test user isolation

3. **Backend Infrastructure**
   - Dependency injection for swappable LLM/TTS
   - Test configuration management
   - WebSocket support for live test updates

**Minimal Changes Needed**:

- Character System: add assertion helpers
- Story Engine: expose beat delivery tracking
- Tool System: add execution logging
- Device Controller: snapshot/restore support

**Phase 2 Benefits**:

- Confidence in Phase 1 implementation before expansion
- Regression testing as new features are added
- Character consistency validation tooling
- Performance baseline establishment
- Foundation for CI/CD pipeline

### Phase 3: Multi-Character Coordination

**Module Changes**:

1. **Character System**
   - Add Hank character definition
   - Implement character selection logic
   - Character handoff patterns

2. **Conversation Manager**
   - Route to appropriate character(s)
   - Handle multi-turn character interactions
   - Coordinate responses between characters

3. **Story Engine**
   - Multi-character beats
   - Relationship tracking
   - Character interaction events

4. **TTS Integration**
   - Multiple voices
   - Character voice mapping

**Minimal Changes Needed**:

- Tool System: unchanged
- Device Controller: unchanged
- Memory Manager: add relationship data
- Frontend: visual character indicators
- Test Harness: multi-character test scenarios

### Phase 4: Real Device Integration

**Module Changes**:

1. **Device Controller**
   - Implement `HomeAssistantController`
   - Same interface, different implementation
   - Connect to Home Assistant WebSocket API

**No Other Changes Required**:

- Interface abstraction pays off
- Tools use same device controller interface
- Conversation flow unchanged
- Just swap controller in dependency injection
- Test harness can test both virtual and real devices

### Phase 5: Advanced Features

**Module Additions**:

- New tools (web search, advanced automations)
- Visual dashboard (separate React app or extension of frontend)
- Advanced context management (vector DB, semantic search)
- Character memory systems
- Running gags tracker
- Add Dimitria character (fourth character)

---

## Risk Mitigation

### Technical Risks

**Risk**: LLM response latency too high

- **Mitigation**: Streaming responses, TTS generation in parallel, caching
- **Fallback**: Pre-generated responses for common queries

**Risk**: TTS quality not good enough

- **Mitigation**: Test multiple providers, iterate on voice selection
- **Fallback**: Text-only mode

**Risk**: Character consistency hard to maintain

- **Mitigation**: Detailed character definitions, extensive testing, feedback loops
- **Fallback**: Simplify personalities if needed

**Risk**: Cost of LLM/TTS too high

- **Mitigation**: Monitor usage, optimize prompts, caching strategies
- **Fallback**: Rate limiting, simpler responses

### Development Risks

**Risk**: Scope creep in Phase 1

- **Mitigation**: Strict adherence to PRD Phase 1 requirements
- **Fallback**: Cut optional features, focus on core experience

**Risk**: Story beats feel forced or awkward

- **Mitigation**: Extensive manual testing, iterate on delivery
- **Fallback**: Reduce beat frequency, make all beats optional

---

## Success Criteria

### Phase 1 Technical Success

- ✅ System responds to voice and text input
- ✅ Delilah personality is consistent and recognizable
- ✅ All 4 Chapter 1 story beats can be delivered
- ✅ Virtual devices work reliably
- ✅ Timers, recipes, and basic tools function
- ✅ Chapter progression logic works
- ✅ Testing API enables automated validation

### Phase 1 User Success

- ✅ Response time acceptable (most interactions < 5 seconds)
- ✅ Character voice feels authentic (manual evaluation)
- ✅ Story beats enhance rather than obstruct
- ✅ System successfully completes Chapter 1 progression
- ✅ User reports emotional connection to Delilah

### Phase 1 Code Quality

- ✅ Modular architecture with clear boundaries
- ✅ TypeScript types throughout
- ✅ Unit tests for core modules
- ✅ Integration tests for conversation flow
- ✅ Documentation up to date
- ✅ Easy to add new characters, tools, or story beats

### Phase 2 Technical Success

- ✅ Test harness UI fully functional
- ✅ 20+ predefined test scenarios covering Phase 1
- ✅ All scenarios pass consistently
- ✅ Mock system enables deterministic testing
- ✅ Trace inspection provides full debugging visibility
- ✅ Analytics dashboard tracks trends and regressions
- ✅ CI/CD ready for automated test execution

### Phase 2 Code Quality

- ✅ Dependency injection supports swappable LLM/TTS
- ✅ Comprehensive trace event system
- ✅ State snapshot/restore mechanism
- ✅ Assertion engine extensible for new test types
- ✅ Test scenarios stored as version-controlled JSON
- ✅ Foundation ready for multi-character testing (Phase 3)

---

## Next Steps

### After Phase 1 Completion

1. **Review Phase 1 Implementation** → Validate against success criteria
2. **Begin Phase 2 Planning** → Detailed test scenario design
3. **Implement Test Infrastructure** → TestExecutor, assertion engine
4. **Build Test Harness UI** → Scenario management and inspection
5. **Create Predefined Scenarios** → Cover all Phase 1 functionality
6. **Establish Testing Baseline** → Performance, character consistency metrics

### Long-term Roadmap

- **Phase 3**: Multi-character coordination (Hank integration)
- **Phase 4**: Real Home Assistant device integration
- **Phase 5**: Advanced features, full character panel

---

*This architecture document will evolve as implementation progresses and new requirements emerge.*
