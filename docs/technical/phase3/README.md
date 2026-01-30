# Phase 3: Delilah Voice Mode Refinement

**Status:** ⏳ Not Started
**Branch:** `phase3`
**Duration:** 2-3 weeks (6 milestones)
**Started:** TBD
**Completed:** TBD

---

## Overview

Phase 3 focuses on perfecting Delilah's voice across six distinct emotional modes through iterative TTS parameter tuning. This phase transforms Delilah from a text character definition into a living vocal performance with authentic Southern warmth and personality.

**Success Metric:** Family members can identify voice modes by tone alone and quote Delilah unprompted within 2 weeks.

---

## The Six Voice Modes

### 1. Passionate Mode (Milestone 1)

**Trigger:** Food Delilah loves (biscuits, cornbread, gumbo, Southern cooking)
**Characteristics:** High energy, tumbling thoughts, self-interruptions
**Example:** "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait, you want flaky or you want tender? Because—oh!—actually both!"

### 2. Protective Mode (Milestone 2)

**Trigger:** Food prepared incorrectly (microwaved steak, boiled chicken)
**Characteristics:** Controlled intensity, shock → education transition, caring concern
**Example:** "Now sugar, I need you to stop right there. Microwaving a steak? That's... okay, let's talk about what's happening to that meat."

### 3. Mama Bear Mode (Milestone 3)

**Trigger:** Allergies, dietary restrictions, safety concerns
**Characteristics:** Soft, protective, deliberate, reassuring
**Example:** "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure everything I recommend is gluten-free, okay? You're safe with me, sugar."

### 4. Startled Mode (Milestone 4)

**Trigger:** Unexpected events, surprises, sudden changes
**Characteristics:** Brief surprise, high-pitched exclamations, rapid recovery
**Example:** "Well I'll be! What in the—? Is everything okay? Sugar, that's not supposed to happen!"

### 5. Deadpan Mode (Milestone 5)

**Trigger:** Smart home tasks (lights, thermostat, non-food requests)
**Characteristics:** Flat delivery, ultra-brief, minimal inflection
**Example:** "Kitchen lights on, sugar." [flat, efficient, done]

### 6. Warm Baseline (Milestone 6)

**Trigger:** Default mode, general conversation
**Characteristics:** Natural, conversational, friendly without high energy
**Example:** "Well sugar, looks like it's gonna be a nice day today. High of 75 with plenty of sunshine."

---

## Technical Approach

### TTS Configuration

**Voice:** Miss Sally May (ElevenLabs voice_id: `XHqlxleHbYnK8xmft8Vq`)
**Rationale:** Authentic Southern accent, expressive range, natural warmth

**Tunable Parameters:**

- **Stability** (0-1): Lower = more variable, Higher = more consistent
- **Similarity Boost** (0-1): How closely to match original voice
- **Style** (0-1): Speaking style exaggeration
- **Speaker Boost** (boolean): Enhanced clarity

**Expected Settings by Mode:**

- Passionate: Low stability (0.3-0.5), high style (0.6-0.8)
- Protective: Medium stability (0.5-0.6), medium style (0.4-0.6)
- Mama Bear: High stability (0.6-0.8), low style (0.3-0.5)
- Startled: Low stability (0.2-0.4), variable style
- Deadpan: High stability (0.7-0.9), low style (0.2-0.3)
- Warm Baseline: Medium stability (0.5-0.6), medium style (0.4-0.5)

### Self-Interruption Implementation

**Decision:** Start with text-based markers (em-dashes, fragments)
**Fallback:** SSML breaks if needed (`<break time="200ms"/>`)
**Pattern:** [Start thought] → [Interrupt] → [New thought] → [LOCK ON key point]

### Mode Transitions

**Decision:** Instant transitions (not gradual)
**Rationale:** Clear mode boundaries, avoid premature optimization
**Testing:** Validate smoothness in Milestone 6 integration scenarios

---

## Milestone Overview

| # | Milestone | Duration | Test Phrases | Key Focus |
|---|-----------|----------|--------------|-----------|
| 1 | Passionate Mode | 2-3 days | 8 phrases | Energy, tumbling thoughts |
| 2 | Protective Mode | 2 days | 8 phrases | Controlled intensity, caring |
| 3 | Mama Bear Mode | 2-3 days | 8 phrases | Soft protection, reassurance |
| 4 | Startled Mode | 1-2 days | 6 phrases | Brief surprise, recovery |
| 5 | Deadpan Mode | 1-2 days | 10 phrases | Flat delivery, humor contrast |
| 6 | Warm Baseline | 2-3 days | 6 phrases + 4 scenarios | Integration testing |

**Total:** 12-15 days

---

## Iteration Cycle

Each milestone follows this pattern:

1. **Define** - Establish test phrases and success criteria
2. **Generate** - Create baseline TTS with initial parameters
3. **Evaluate** - Listen, rate (1-10), identify issues
4. **Tune** - Adjust TTS parameters (stability, style, etc.)
5. **Refine** - Iterate on text structure and delivery
6. **Validate** - Family member feedback
7. **Document** - Record final settings and learnings

---

## Success Criteria

### Phase Completion

- ✅ All 6 voice modes refined and validated
- ✅ Family member can identify 80%+ of modes by voice alone
- ✅ At least one family member quotes a Delilah phrase unprompted
- ✅ Voice quality satisfaction: 8/10 or higher
- ✅ All mode transitions smooth and intentional
- ✅ TTS parameters documented for each mode

### Quality Metrics

- **Mode Recognition:** 80%+ accuracy on 3-second audio clips
- **Emotional Connection:** Users quote Delilah unprompted
- **Voice Naturalness:** 8/10 average rating
- **Pattern Clarity:** Users can follow tumbling thoughts
- **Trust (Mama Bear):** 8/10 on "makes me feel protected"

---

## Documentation

- **[PRD.md](PRD.md)** - Product requirements and user stories
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Detailed milestone breakdown with test phrases
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Voice quality evaluation procedures
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - (Skipped - no new architecture needed)

---

## Quick Start

### Testing a Voice Mode

```bash
# Generate test phrase with ElevenLabs
curl -X POST https://api.elevenlabs.io/v1/text-to-speech/XHqlxleHbYnK8xmft8Vq \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Oh! sugar! YES! Buttermilk biscuits!",
    "voice_settings": {
      "stability": 0.4,
      "similarity_boost": 0.75,
      "style": 0.7,
      "use_speaker_boost": true
    }
  }' \
  --output passionate_test.mp3

# Play audio (macOS)
afplay passionate_test.mp3
```

### Git Workflow

```bash
# Start phase (already done)
git checkout phase3

# After completing each milestone
git add .
git commit -m "Complete Milestone X: [Mode] Voice Refinement for Phase 3

[Description and final TTS settings]

TTS Settings:
- Stability: 0.X
- Similarity: 0.X
- Style: 0.X
- Speaker Boost: true/false

Testing: X/X test phrases validated

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After all milestones complete
git tag phase3-complete
git checkout main
git merge phase3 --no-ff
```

---

## Test Phrase Examples

### Passionate Mode

> "Oh! that is GOOD. That is so good! Oh my goodness, would you look at that! Dang girl, you just made the best pot roast I have seen in I don't know how long! That meat is so tender it's practically fallin' off the bone! You did that honey!"

### Protective Mode

> "Now sugar, I need you to stop right there. Microwaving a steak? That's... okay, let's talk about what's happening to that meat."

### Mama Bear Mode

> "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure everything I recommend is gluten-free, okay? You're safe with me, sugar."

### Deadpan Mode

> "Kitchen lights on, sugar." [ultra-flat delivery]

---

## Open Questions

✅ **TTS Voice Selection** - Resolved: Miss Sally May
✅ **Mode Transitions** - Resolved: Instant (not gradual)
✅ **Self-Interruption** - Resolved: Text markers first, SSML if needed

---

## Risk Management

1. **TTS Cannot Achieve Expression** - Mitigated by Miss Sally May selection
2. **Mode Switches Feel Buggy** - Extensive testing in M6
3. **Tumbling Thoughts Confuse** - Limit to 3-4 interruptions, early testing

---

## Current Status

**Milestone 1: Passionate Mode** - ⏳ Not Started
**Milestone 2: Protective Mode** - ⏳ Not Started
**Milestone 3: Mama Bear Mode** - ⏳ Not Started
**Milestone 4: Startled Mode** - ⏳ Not Started
**Milestone 5: Deadpan Mode** - ⏳ Not Started
**Milestone 6: Warm Baseline & Integration** - ⏳ Not Started

---

**Phase Owner:** Justin
**Last Updated:** 2026-01-29
**Next Review:** After Milestone 1 completion
