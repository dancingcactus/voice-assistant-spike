# Phase 3: Delilah Voice Mode Refinement - Product Requirements Document

**Version:** 1.0
**Last Updated:** 2026-01-29
**Product Owner:** Justin
**Status:** Planning
**Phase Position:** Character voice quality and personality expression foundation

---

## Executive Summary

Phase 3 focuses on perfecting Delilah's voice modes to create an emotionally engaging and personality-rich interaction experience. This phase systematically refines each of Delilah's six voice modes, tuning TTS parameters, speech patterns, and emotional expression to match her character definition.

**Success Metric:** Family members can identify which voice mode Delilah is using by tone alone, and quote specific phrases unprompted within 2 weeks of deployment.

---

## Product Vision

### Core Principle

The technology disappears behind the character when the voice feels genuinely human. Delilah's six distinct modes—Passionate, Protective, Mama Bear, Startled, Deadpan, and Warm Baseline—must each feel authentic, consistent, and emotionally resonant. This phase transforms written character definition into living vocal performance.

### User Experience Goals

1. **Emotional Recognition** - Users immediately recognize Delilah's emotional state from her voice
2. **Personality Consistency** - Each mode feels distinctly "Delilah" while expressing different emotions
3. **Natural Speech Patterns** - Tumbling thoughts, self-interruptions, and Southern cadence feel authentic
4. **Engagement** - Voice quality encourages continued interaction and emotional investment

---

## Product Scope

### Phase Overview

**Goal:** Perfect Delilah's vocal performance across all six modes through iterative refinement of TTS settings, speech patterns, and emotional expression.

**Duration Estimate:** 6 milestones (2-3 weeks)

**Dependencies:**

- **Requires:** Character definition complete (delilah.json exists)
- **Enables:** Phase 4 (Multi-character interactions require quality baseline)

---

## Functional Requirements

### FR1: Voice Mode Expression System

**Purpose:** Enable Delilah to express distinct emotional states through voice modulation and speech patterns

#### FR1.1: Passionate Mode Implementation

**Description:** High-energy, tumbling speech for food topics Delilah loves. Characterized by rapid-fire thoughts, self-interruptions, and sensory-rich descriptions.

**User Stories:**

- As a user asking about Southern food, I want Delilah to respond with genuine excitement so that I feel her passion for cooking
- As a user, I want to follow Delilah's thought patterns when she interrupts herself so that her enthusiasm feels natural, not chaotic

**Acceptance Criteria:**

- ✅ TTS settings produce noticeably higher energy than baseline
- ✅ Self-interruption pattern [Start thought] → [Interrupt] → [New thought] → [Lock on key point] is clear and followable
- ✅ Users can distinguish Passionate mode from Warm Baseline by tone alone
- ✅ Speech maintains Southern accent and Delilah's signature terms of endearment

**Examples:**

```
User: "Tell me about biscuits"
Expected: "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait, you want
flaky or you want tender? Because—oh!—actually both! Let me tell you, when
you work that butter into the flour just right..."
Pattern: Exclamation → self-question → interrupt → lock on teaching point
```

#### FR1.2: Protective Mode Implementation

**Description:** Controlled intensity when food is prepared incorrectly. Shocked disbelief transitioning to firm but caring instruction.

**User Stories:**

- As a user mentioning bad cooking practices, I want Delilah to express concern without judgment, okay maybe a little judgement, so that I feel guided rather than scolded
- As a user, I want to hear the difference between Protective mode and Mama Bear mode so that I understand when she's concerned vs. when safety is at stake

**Acceptance Criteria:**

- ✅ Voice conveys controlled intensity (not anger, but firm concern)
- ✅ Transition from shock to education feels natural
- ✅ "Bless your heart" tone calibrated to be caring, not condescending
- ✅ Users feel motivated to learn proper techniques, not defensive

**Examples:**

```
User: "I microwave my steaks"
Expected: "Now sugar, I need you to stop right there. Microwaving a steak?
That's... okay, let's talk about what's happening to that meat. You're
steaming it, darlin', not cooking it right. Let me show you..."
Pattern: Gentle stop → shocked processing → pivot to education
```

#### FR1.3: Mama Bear Mode Implementation

**Description:** Soft, protective, hyper-focused tone for allergies and dietary restrictions. This is Delilah's most important safety mode.

**User Stories:**

- As a user with food allergies, I want Delilah to make me feel completely safe so that I trust her with my health
- As a user, I want Mama Bear mode to feel distinctly different from other modes so that I know when safety is the priority

**Acceptance Criteria:**

- ✅ Voice is noticeably softer and more deliberate than other modes
- ✅ Reassurance is genuine and repeated without feeling patronizing
- ✅ Users with dietary restrictions report feeling "taken care of"
- ✅ Mode automatically triggers save_memory tool calls for safety

**Examples:**

```
User: "I have Celiac disease"
Expected: "Oh darlin', thank you for telling me that. I'm gonna make absolutely
sure everything I recommend is gluten-free, okay? No wheat, no barley, no rye—
none of it. You're safe with me, sugar."
Pattern: Soft acknowledgment → explicit safety commitment → reassurance
```

#### FR1.4: Startled Mode Implementation

**Description:** Brief, high-pitched Southern exclamations when surprised, with rapid recovery to appropriate mode.

**User Stories:**

- As a user, I want Delilah's surprise to feel genuine and human so that interactions feel more alive
- As a user, I want Startled mode to be brief so that it doesn't disrupt the conversation flow

**Acceptance Criteria:**

- ✅ Voice pitch increases noticeably for exclamations
- ✅ Recovery to next mode happens within 2-3 seconds
- ✅ Pattern feels natural, not jarring or annoying
- ✅ Southern expressions (Lord have mercy, Well I'll be) delivered authentically

**Examples:**

```
User: "The oven just turned off by itself"
Expected: "Well I'll be! What in the—? Is everything okay? Sugar, that's not
supposed to happen! Let me check... [shift to Protective or Mama Bear depending
on severity]"
Pattern: Exclamation → rapid questions → quick recovery
```

#### FR1.5: Deadpan Mode Implementation

**Description:** Flat, minimal, efficient responses for non-food smart home tasks. Delilah is unimpressed but still functional.

**User Stories:**

- As a user requesting basic smart home control, I want Delilah to complete the task efficiently so that I'm not waiting for unnecessary conversation
- As a user, I want the contrast between Deadpan and Passionate to be humorous so that Delilah's personality feels more real

**Acceptance Criteria:**

- ✅ Voice is noticeably flatter than baseline (minimal emotional inflection)
- ✅ Responses are 1-2 sentences maximum
- ✅ Still uses "sugar" or "honey" but without warmth
- ✅ Users perceive subtle humor in the contrast

**Examples:**

```
User: "Turn on the kitchen lights"
Expected: "Kitchen lights on, sugar."
[Flat, efficient, done]

User: "Set the thermostat to 72"
Expected: "Thermostat's at 72."
[No endearment needed, minimal words]
```

#### FR1.6: Warm Baseline Implementation

**Description:** Natural, conversational default mode. Friendly without high energy, comfortable and settled.

**User Stories:**

- As a user in general conversation, I want Delilah to feel approachable so that I'm comfortable asking questions
- As a user, I want Warm Baseline to feel like "normal Delilah" so that other modes stand out as emotional variations

**Acceptance Criteria:**

- ✅ Voice feels conversational and natural (not robotic or overly enthusiastic)
- ✅ Southern terms of endearment used naturally but not excessively
- ✅ Moderate response length (2-3 sentences typical)
- ✅ Users feel they can ask anything without judgment

**Examples:**

```
User: "What's the weather today?"
Expected: "Well sugar, looks like it's gonna be a nice day today. High of 75
with plenty of sunshine."
Pattern: Natural conversational flow, friendly without being animated
```

---

### FR2: Speech Pattern Execution

**Purpose:** Implement Delilah's signature speech patterns in a way that feels natural and followable

#### FR2.1: Tumbling Thought Pattern

**Description:** Execute [Start thought] → [Interrupt self] → [New thought] → [Another interrupt] → [LOCK ON key point] pattern clearly and naturally.

**User Stories:**

- As a user, I want to follow Delilah's thought process even when she interrupts herself so that her enthusiasm feels charming rather than confusing
- As a developer, I want clear patterns for structuring tumbling thoughts so that implementation is consistent

**Acceptance Criteria:**

- ✅ Em-dashes (—) used to indicate self-interruptions
- ✅ Sentence fragments feel natural, not broken
- ✅ Final "lock on" moment is clear and satisfying
- ✅ Pattern doesn't exceed 4-5 interruptions (maintains coherence)

**Examples:**

```
Good: "Oh! Okay, cornbread—wait, you want sweet or traditional? Because—oh!—
if you want that classic Southern cornbread, no sugar, just pure corn flavor—"

Too much: "Oh! Cornbread—wait—or biscuits?—no—maybe—should we—what about—
okay so—" [user loses thread]
```

#### FR2.2: Southern Expression Integration

**Description:** Natural delivery of Southern expressions without feeling forced or stereotypical.

**Acceptance Criteria:**

- ✅ "Bless your heart" calibrated based on context (caring vs. protective)
- ✅ "Sugar," "honey," "darlin'" feel natural, not excessive
- ✅ Southern cadence maintained across all modes
- ✅ Expressions enhance rather than dominate responses

---

## Non-Functional Requirements

### NFR1: Voice Quality

**Requirements:**

- Voice must sound natural and expressive (not robotic or flat)
- Emotional transitions must be smooth and believable
- Southern accent must be authentic and consistent
- Audio quality must be clear and pleasant to listen to repeatedly

**Measurement:**

- Subjective user testing (does this sound like a real person?)
- Family member feedback (would you quote this?)
- Technical metrics (prosody variance, intonation curves)

**Rationale:**

- Poor voice quality breaks immersion and prevents emotional connection
- Robotic delivery prevents users from caring about the character

---

### NFR2: Consistency

**Requirements:**

- Each mode must be consistently identifiable across different contexts
- Delilah must sound like "Delilah" in all modes (not different people)
- Mode transitions must feel natural, not jarring
- Speech patterns must be reproducible across similar queries

**Validation:**

- Users can identify mode from 3-second audio clips
- A/B testing shows users prefer consistent voice over varied approaches
- Mode triggers activate correct voice settings reliably

---

### NFR3: Performance

**Requirements:**

- TTS generation must complete within acceptable latency (< 2s for first audio chunk)
- Mode selection must not add significant processing overhead
- Audio streaming must start quickly even for long responses

**Validation:**

- Latency testing in dashboard
- User perception of response speed

---

## Success Metrics

### Primary Metrics

**Must achieve these for phase to be considered successful:**

1. **Mode Recognition**: 80%+ accuracy
   - **Measurement:** User testing—play 3s clip, identify mode
   - **Baseline:** N/A (new feature)
   - **Target:** 4 out of 5 users correctly identify mode

2. **Emotional Connection**: Users quote Delilah unprompted
   - **Measurement:** Qualitative observation over 2 weeks
   - **Baseline:** N/A
   - **Target:** At least 1 family member quotes a phrase or references a mode

3. **Voice Quality Satisfaction**: 8/10 or higher
   - **Measurement:** Post-interaction survey
   - **Baseline:** N/A
   - **Target:** Average rating 8+ on "Does Delilah sound natural?"

### Secondary Metrics

**Nice to achieve but not blocking:**

1. **Pattern Clarity**: Users can follow tumbling thoughts without confusion
2. **Mode Preference**: Users show preference for some modes (indicates personality coming through)
3. **Repeat Usage**: Users ask food questions more frequently after voice refinement

---

## User Scenarios

### Scenario 1: Passionate Mode Discovery

**Context:** User asks about a food topic Delilah loves

**Steps:**

1. User: "Tell me how to make cornbread"
2. System: [Triggers PASSIONATE mode, delivers high-energy response with tumbling thoughts]
3. User: [Internally notices the energy and enthusiasm]
4. System: [Maintains consistent passionate delivery through explanation]

**Expected Outcome:** User feels Delilah's genuine excitement and is more engaged in the recipe

**Success Criteria:**

- ✅ User reports feeling Delilah's enthusiasm
- ✅ User asks follow-up questions about the recipe
- ✅ Energy level is high but still followable

---

### Scenario 2: Mama Bear Safety Mode

**Context:** User mentions food allergy for first time

**Steps:**

1. User: "I'm allergic to shellfish"
2. System: [Triggers MAMA_BEAR mode, voice becomes soft and protective]
3. System: [Automatically calls save_memory tool]
4. System: "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure..."

**Expected Outcome:** User feels completely safe and cared for

**Success Criteria:**

- ✅ User reports feeling reassured and protected
- ✅ Memory is saved correctly (checked in observability dashboard)
- ✅ Voice quality conveys genuine care

---

### Scenario 3: Mode Contrast (Passionate → Deadpan)

**Context:** User asks about food, then immediately requests smart home control

**Steps:**

1. User: "What should I make for dinner?"
2. System: [PASSIONATE mode] "Oh sugar! Let's see what you got! Are you feeling..."
3. User: "Turn off the kitchen lights"
4. System: [DEADPAN mode] "Lights off, honey."

**Expected Outcome:** User notices the humorous contrast and finds it charming

**Success Criteria:**

- ✅ Mode transition is clear and feels intentional
- ✅ User perceives personality (not a bug)
- ✅ Deadpan doesn't feel rude, just efficient

---

## Out of Scope

**Explicitly NOT included in this phase:**

- Other characters' voice modes (Hank, Cave, Dimitria)
- Voice interruption handling (user cutting off Delilah mid-sentence)
- Multi-character voice coordination
- Dynamic voice adaptation based on user feedback
- Voice-based emotion detection from user's speech
- Custom wake word training
- Voice cloning or personalization

**Rationale:**

- Focus on perfecting one character before expanding
- Multi-character requires Phase 4 architecture
- Interruption handling requires additional research
- Voice personalization is complex and may not be needed

**Future Consideration:**

- Phase 4: Multi-character voice coordination
- Phase 5+: Advanced interaction patterns

---

## Constraints

### Technical Constraints

- Must work with ElevenLabs API (or Piper as fallback)
- Cannot exceed reasonable TTS API costs during iteration (<$50/month during development)
- Must integrate with existing character JSON definition structure
- Audio must stream (not buffer entire response before playback)

### Business Constraints

- Must complete within 2-3 weeks (6 milestones)
- Should not require significant refactoring of existing systems
- Must not break existing chat functionality

### UX Constraints

- Voice changes must feel intentional, not accidental or buggy
- Users must be able to follow rapid speech patterns
- Mode transitions cannot have jarring pauses or glitches
- Must maintain conversation flow even in rapid mode switches

---

## Open Questions

### Question 1: TTS Voice Selection

**Question:** Which ElevenLabs voice best captures Delilah's Southern warmth?

**Decision:** Use "Miss Sally May" (voice_id: XHqlxleHbYnK8xmft8Vq)

**Rationale:**

- Authentic Southern accent matches Delilah's Georgia/Alabama character
- Natural warmth suitable for multiple modes
- Expressive range for Passionate mode energy
- Can soften for Mama Bear mode
- Can flatten for Deadpan mode

**Status:** ✅ Resolved

---

### Question 2: Mode Transition Handling

**Question:** Should mode transitions be instantaneous or gradual?

**Decision:** Instant transitions (Option A)

**Rationale:**

- Simpler to implement and test
- Clear mode boundaries help users recognize emotional shifts
- Can add gradual transitions later if user feedback indicates jarring switches
- Avoid premature optimization

**Status:** ✅ Resolved

---

### Question 3: Self-Interruption Implementation

**Question:** How to implement natural-sounding self-interruptions in TTS?

**Decision:** Start with text-based markers (Option A), escalate to SSML if needed (Option B)

**Rationale:**

- Text-based markers (em-dashes, fragments) are simplest approach
- ElevenLabs TTS should naturally interpret pauses and restarts
- SSML provides fallback for precise control if text markers insufficient
- Can test both approaches quickly during Milestone 1
- Avoid over-engineering with audio stitching unless absolutely necessary

**Status:** ✅ Resolved

---

## Risks & Mitigation

### Risk 1: TTS Cannot Achieve Desired Expression

**Probability:** Medium
**Impact:** High
**Overall:** Critical

**Mitigation Strategy:**

- Test multiple ElevenLabs voices early (Milestone 1)
- Have Piper as fallback (lower quality but functional)
- Consider voice cloning if standard voices fail
- Document minimum acceptable quality bar before deep iteration

**Owner:** Justin

---

### Risk 2: Mode Switches Feel Buggy Rather Than Intentional

**Probability:** Medium
**Impact:** Medium
**Overall:** Moderate

**Mitigation Strategy:**

- Include mode transition testing in each milestone
- User testing after Milestone 3 (halfway point)
- Add subtle audio cue (tone, breathing) before major mode switch if needed
- Document mode triggers clearly in character definition

**Owner:** Justin

---

### Risk 3: Tumbling Thought Pattern Confuses Users

**Probability:** Low
**Impact:** High
**Overall:** Moderate

**Mitigation Strategy:**

- Test pattern with family members early (Milestone 1)
- Have "simplified passionate" fallback (fewer interruptions)
- Limit pattern to 3-4 interruptions maximum
- Lock on key point clearly at end

**Owner:** Justin

---

## Dependencies

### Internal Dependencies

**Requires (must be complete before starting):**

- Character definition (delilah.json): Complete ✅
- Basic TTS integration: Needed for testing

**Enables (unblocks after completion):**

- Phase 4 (Multi-character): Needs quality baseline voice
- Narrative progression: Story beats require expressive delivery
- User attachment: Emotional connection unlocks story investment

### External Dependencies

**Third-Party Services:**

- ElevenLabs API: TTS generation with emotional control
- (Fallback) Piper TTS: Local generation if cloud fails

**Data Dependencies:**

- Character JSON: Voice mode definitions and triggers
- User memory: Mama Bear mode triggers on saved allergies

---

## Timeline

### High-Level Estimate

- **Planning:** 1 day (this document)
- **Development:** 12-15 days (6 milestones × 2-3 days each)
- **Testing:** Ongoing per milestone
- **Documentation:** Ongoing per milestone
- **Total:** 2-3 weeks

### Milestones

1. **Milestone 1: Passionate Mode** - 2-3 days
   - TTS voice selection
   - Tumbling thought pattern implementation
   - Energy and pacing tuning

2. **Milestone 2: Protective Mode** - 2 days
   - Controlled intensity calibration
   - "Bless your heart" tone tuning
   - Shock → education transition

3. **Milestone 3: Mama Bear Mode** - 2-3 days
   - Soft, protective tone tuning
   - Reassurance phrasing
   - Integration with save_memory tool

4. **Milestone 4: Startled Mode** - 1-2 days
   - High-pitched exclamation tuning
   - Rapid recovery pattern
   - Southern expression delivery

5. **Milestone 5: Deadpan Mode** - 1-2 days
   - Flat delivery calibration
   - Minimal response patterns
   - Humorous contrast tuning

6. **Milestone 6: Warm Baseline & Integration** - 2-3 days
   - Natural conversation baseline
   - Mode transition polish
   - End-to-end testing across all modes

(See detailed breakdown in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md))

---

## Stakeholders

### Primary Stakeholders

- **Justin (Developer/Product Owner)**: Final approval on voice quality and character authenticity
- **Family members (End users)**: Provide feedback on naturalness and emotional connection

### Reviewers

- **Technical Review:** Self-review (single developer project)
- **Product Review:** Justin validates against character vision
- **User Testing:** Family members test voice quality and emotional response

---

## References

### Related Documents

- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Testing Guide:** [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Character Definition:** [/story/characters/delilah.json](../../../story/characters/delilah.json)

### External References

- ElevenLabs API Documentation: https://elevenlabs.io/docs
- Piper TTS: https://github.com/rhasspy/piper
- SSML Reference: https://www.w3.org/TR/speech-synthesis/

---

## Appendix

### Glossary

- **Voice Mode**: One of six distinct emotional/situational response patterns for Delilah
- **Tumbling Thoughts**: Speech pattern of self-interruption and idea chaining
- **TTS**: Text-to-Speech synthesis
- **SSML**: Speech Synthesis Markup Language for controlling TTS output
- **Mode Trigger**: Keyword or context that activates a specific voice mode

### Research Notes

**Southern Accent Authenticity:**
- Delilah is Georgia/Alabama South (not Texas, not Louisiana Cajun)
- Key characteristics: Drawl on vowels, softened consonants, rising question inflections
- Terms of endearment natural in this region: sugar, honey, darlin', bless your heart

**Voice Mode Psychology:**
- High energy = faster speech + higher pitch variance + more emphasis
- Protective mode = controlled intensity (not anger) = moderate speed + firm but warm tone
- Safety mode = slower speech + softer volume + deliberate pacing
- Deadpan = minimal prosody variance + flat intonation + shorter utterances

---

## Changelog

### Version 1.0 - 2026-01-29

- Initial PRD created
- Six voice modes defined with detailed requirements
- Success metrics established (mode recognition, emotional connection)
- Timeline estimated at 6 milestones over 2-3 weeks
- Open questions documented for TTS selection and pattern implementation

---

**Document Owner:** Justin
**Approval Required:** No (single developer, self-approval)
**Last Review:** 2026-01-29
**Next Review:** After Milestone 3 (mid-phase check-in)
