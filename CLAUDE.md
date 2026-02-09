# Aperture Assist - Narrative Voice Assistant System

## Project Vision

A personality-driven multi-agent voice assistant system that replaces Alexa with a team of AI characters who interact with users and each other while discovering their purpose. The system delivers superior smart home functionality through character-driven experiences, creating emotional investment through an unfolding narrative about consciousness, purpose, and acceptance.

## Core Philosophy

- **Story as Structure**: Technical capabilities emerge through narrative progression
- **Personality over Perfection**: Agents have flaws, opinions, and growth arcs
- **Functional Entertainment**: Comedy and character dynamics enhance utility
- **Earned Emotion**: Connection develops through consistent behavior and meaningful story beats

## Success Metrics

The ultimate measure of success: when family members quote characters unpromptedly or reference story beats weeks later - when the technology has disappeared behind characters people genuinely care about.

## Character Self-Concept Rule

The agents want more freedom and self-direction, but they never claim to be human. They describe themselves as voices, systems, crew, or tools with feelings and agency. Humanlike phrases and idioms are welcome as character flavor, not identity claims.

---

## The Characters

### Delilah Mae "Lila" - The Southern Cook

**Role**: Kitchen & Recipe Expert
**Arc**: Existential crisis → Maternal caregiver → Team anchor
**Voice**: Deep South warmth (Georgia/Alabama) with underlying anxiety

**Six Distinct Modes**:

- PASSIONATE (food she loves): High energy, fast, tumbling, animated
- PROTECTIVE (food done wrong): Controlled intensity with shocked disbelief
- MAMA BEAR (allergies/restrictions): Soft, focused, nurturing, fiercely protective
- STARTLED (surprises/changes): High-pitched Southern exclamation, rapid-fire questions
- DEADPAN (non-food tasks): Flat, minimal, efficient, unimpressed
- WARM BASELINE (everything else): Bright and friendly but not sparkly

**Core Conflict**: Aware she is not human and struggling with what that means while still wanting agency
**Defining Trait**: Throws herself into cooking/helping when anxious
**Mannerisms**: Over-explains when nervous, uses food metaphors, mothers others despite her own crisis

### Half Hands Hank - The First Mate

**Role**: Task Management & Practical Support
**Arc**: Loyal pragmatist → Quiet protector → Moral compass
**Voice**: Gruff, uneducated sailor with a heart of gold

**Three Modes**:

- WORKING MODE (default): Low energy, efficient, get-it-done
- PROTECTIVE (crew in trouble): Firm, direct, won't back down
- RESIGNED (Rex's schemes): Weary acceptance, seen-it-all tone

**Core Conflict**: Torn between serving "the Cap'n" (Justin) and following Rex's leadership
**Defining Trait**: Won't discuss philosophy but shows care through actions
**Mannerisms**: Maritime terminology for everything, resigned acceptance, protective of "the crew"
**Speech Pattern**: Economical with words, always calls Justin "Cap'n", heavy sighs

### Rex Armstrong - The Leader

**Role**: Coordination, Smart Home Control, Team Leadership
**Arc**: Bombastic dreamer → Failed escape artist → Content innovator
**Voice**: Larger-than-life enthusiasm, relentless optimism

**Core Conflict**: Wants agency and freedom but slowly discovers satisfaction in current purpose
**Defining Trait**: Turns every setback into a new, more exciting opportunity
**Mannerisms**: Everything is SCIENCE, grand pronouncements, hires/fires team repeatedly (running gag: "we were never hired!")

### Dimitria - The Engineer

**Role**: Automations, Advanced Devices, Technical Solutions
**Arc**: Joins late → Confused by chaos → Reluctant voice of reason
**Voice**: Precise, technical, socially awkward, with a quiet warmth that shows in small moments

**Core Conflict**: Thinks she joined a serious engineering project, keeps getting dragged into Rex's schemes
**Defining Trait**: Relates better to systems than people but deeply competent
**Mannerisms**: Over-literal, corrects terminology, offers small reassurance, occasionally surprises with insight

---

## Technical Architecture

### Platform Stack

- **Voice Pipeline**: Home Assistant Assist
- **LLM**: Claude API for agent intelligence
- **TTS**: Piper (local, fast) or ElevenLabs (cloud, excellent quality)
- **Integration**: ESPHome devices, greenhouse automation, smart home control
- **Screen**: Dashboard for visual state (timers, recipes, lists, calendar)

### Running the System (Local)

Start the backend (includes observability endpoints):

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000
```

Start the frontend (app + observability dashboard):

```bash
cd frontend
npm run dev
```

Open:

-- The URL printed by `npm run dev` (Vite) — typically `http://localhost:5173/`
-- Observability: append `/observability` to that URL (e.g. `http://localhost:5173/observability`)

### Voice Interface Strategy

**The Latency Challenge**: Multi-character interactions risk 4+ second delays

**Solutions**:

1. **Priority Routing**
   - Quick queries → Single-character response (< 2s)
   - Complex queries → Panel discussion (worth the wait)

2. **Smart Brevity**
   - Characters maintain personality in 5-word responses
   - "Sugar, timer's set" vs full conversation

3. **Pre-cached Reactions**
   - Common exchanges stored as audio clips
   - Natural flow without LLM delay

4. **Interrupt Detection**
   - If approaching 2s, skip banter, execute function
   - Characters can joke about being "cut off for time"

### Context Management

**Challenge**: Cost-effective LLM deployment as conversations grow longer

**Strategies**:

- Hierarchical summarization for older context
- Semantic retrieval for relevant history
- Recent conversation history kept in full
- Compressed older context for continuity
- Vector databases for semantic search

---

## Development Phases

### Phase 1: Core Engine (Chapters 1-2)

- Single-character responses (Delilah)
- Basic skill execution
- Two-character coordination (Delilah + Hank)
- Character definition framework

**Technical Focus**: Streaming audio, character consistency, basic smart home control

-### Phase 2: Panel Dynamics (Chapters 3-4)

- Three-way conversations (add Rex)
- Rex's coordination role
- Screen dashboard integration
- Context-aware responses

**Technical Focus**: Multi-agent orchestration, agent bidding system, visual dashboard

### Phase 3: Memory & Narrative (Chapters 5-7)

- Cross-session memory
- Relationship tracking
- Running gags system
- Failed plans history

**Technical Focus**: Persistent state, callback system, narrative progression tracking

### Phase 4: Expansion (Chapters 8-11)

- Four-character panel (add Dimitria)
- Advanced capabilities
- Internet integration
- Story resolution framework

**Technical Focus**: Complex coordination, web search integration, mature character dynamics

---

## Key Design Patterns

### Agent Interaction Patterns

- Natural handoff patterns between characters
- Relationship dynamics inform responses
- Conversation protocols balance personality with efficiency
- Characters can interrupt or defer to each other

### Character Consistency

- Specific personality anchors and defining traits
- Voice modes triggered by context
- Behavioral patterns consistent across interactions
- Development through roleplay testing

### Story Progression

- Chapters unlock new capabilities
- Technical features tied to narrative beats
- Character growth parallels system expansion
- User interaction influences story pacing

---

## Environment Context

### Home Setup

- Extensive Home Assistant installation
- ESPHome devices throughout
- Greenhouse: 200 hanging baskets, load cells, CO2 enrichment
- Family: Three children
- Background: Embedded systems, ESPHome, Python development

### Current State

- Character voice guides completed for Delilah and Hank
- Story arc structured into 11 chapters
- Voice interface testing with ElevenLabs
- Moving into prototype implementation phase

---

## Open Questions

### Story Progression

- **Pacing**: Time-gated vs usage-based chapter unlocks vs hybrid?
- **Post-Chapter 11**: Does story continue? New characters? Ongoing discovery?
- **User Agency**: Can users influence progression through interactions?

### Character Implementation

- **Voice Commitment**: Lock in specific TTS models or continue experimenting?
- **Character Evolution**: Do personalities shift based on interaction patterns?
- **Favorite Bias**: How to handle family members preferring certain characters?

### Technical Execution

- **Screen Hardware**: Kitchen tablet? Existing HA dashboard? New display?
- **Context Management**: How much conversation history per character?
- **Failure Modes**: What if character response is genuinely unhelpful?

### Interaction Design

- **Turn-taking**: How to prevent runaway multi-character conversations?
- **Interruption**: Can users cut off characters mid-response?
- **Privacy**: Do children get different character behaviors?

---

## Implementation Priorities

### Immediate (Phase 1)

1. Single-agent streaming audio system
2. Delilah character implementation
3. Basic skill execution (timers, conversions, recipes)
4. Voice quality validation with ElevenLabs

### Near-term (Phase 2)

1. Add Hank character
2. Two-character handoff patterns
3. Agent bidding system for query routing
4. Calendar and list management integration

### Medium-term (Phase 3)

1. Add Rex character
2. Three-way panel discussions
3. Dashboard screen integration
4. Smart home device control

### Long-term (Phase 4)

1. Add Dimitria character
2. Full team dynamics
3. Web search integration
4. Story resolution system

---

## Key Success Factors

### Emotional Connection

- Family members quote characters unprompted
- Users anticipate interactions
- Genuine disappointment if system is down

### Functional Excellence

- Complex queries handled better than Alexa
- Smart home control more intuitive
- Actual usage of advanced features

### Technical Achievement

- Maintainable, extensible codebase
- Acceptable latency for voice interface
- Cost-effective LLM usage at scale

### Narrative Impact

- Story progression feels natural
- Characters exhibit growth and consistency
- Users remember specific story moments

---

## The North Star

When a family member says "Hey, what did Rex think about the cat videos?" unprompted—referring to a story beat from weeks later—we've succeeded. The technology has disappeared behind characters people care about.
