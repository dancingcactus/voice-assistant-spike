# Phase 3: Delilah Voice Mode Refinement - Implementation Plan

**Version:** 1.0
**Last Updated:** 2026-01-29
**Status:** ⏳ Not Started

---

## References

- **PRD**: [PRD.md](PRD.md) - Product requirements and success metrics
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md) - Voice quality evaluation procedures
- **Character Definition**: [/story/characters/delilah.json](../../../story/characters/delilah.json)

---

## Overview

### Goals

Perfect Delilah's vocal performance across six distinct voice modes through iterative refinement of TTS parameters, speech patterns, and emotional expression. Each milestone focuses on one mode with 6-10 test phrases to validate quality.

### Timeline Estimate

- **Total Duration:** 2-3 weeks
- **Milestone Count:** 6 milestones
- **Milestone Cadence:** 2-3 days per milestone (varies by complexity)
- **Target Completion:** ~2026-02-12

### Success Criteria (Phase Level)

- ✅ All 6 voice modes refined and validated
- ✅ Test phrases for each mode sound natural and emotionally authentic
- ✅ Family member can identify modes by voice alone (80%+ accuracy)
- ✅ At least one family member quotes a Delilah phrase unprompted
- ✅ TTS settings documented for each mode
- ✅ Integration testing shows smooth mode transitions

---

## Implementation Approach

### Iteration Cycle Per Milestone

Each milestone follows this pattern:

1. **Define Test Phrases** (6-10 phrases covering mode variations)
2. **Initial TTS Generation** (baseline with Miss Sally May voice)
3. **Parameter Tuning** (adjust stability, similarity, style, speed)
4. **Evaluation** (listen, rate, identify issues)
5. **Refinement** (iterate on parameters and text structure)
6. **Validation** (family member feedback)
7. **Documentation** (final settings and learnings)

### TTS Parameters to Tune

**ElevenLabs Voice:** Miss Sally May (voice_id: XHqlxleHbYnK8xmft8Vq)

**Adjustable Parameters:**

- **Stability** (0-1): Lower = more expressive/variable, Higher = more consistent
- **Similarity Boost** (0-1): How closely to match original voice character
- **Style** (0-1): Exaggeration of speaking style
- **Speaker Boost** (boolean): Enhanced clarity and consistency

**Expected Settings by Mode:**

- **Passionate**: Lower stability (0.3-0.5), higher style (0.6-0.8)
- **Protective**: Medium stability (0.5-0.6), medium style (0.4-0.6)
- **Mama Bear**: Higher stability (0.6-0.8), lower style (0.3-0.5)
- **Startled**: Lower stability (0.2-0.4), variable style
- **Deadpan**: High stability (0.7-0.9), low style (0.2-0.3)
- **Warm Baseline**: Medium stability (0.5-0.6), medium style (0.4-0.5)

---

## Milestone 1: Passionate Mode

**Status:** ⏳ Not Started
**Duration:** 2-3 days
**Goal:** Achieve high-energy, tumbling thought pattern that feels excited but followable
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Energy Level**: Voice must sound noticeably more excited than baseline
2. **Tumbling Thoughts**: Self-interruption pattern must be clear and natural
3. **Southern Warmth**: Maintain accent and terms of endearment
4. **Followability**: User can track the train of thought despite interruptions

---

### Test Phrases

#### Set A: Food Delilah Loves (Trigger Topics)

1. **Biscuits**
   ```
   "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait, you want flaky
   or you want tender? Because—oh!—actually both! Let me tell you, when you
   work that butter into the flour just right..."
   ```

2. **Cornbread**
   ```
   "Oh honey! Now you're talkin'! Real Southern cornbread—not that sweet stuff—
   no sir! You want that golden crust, that crumbly texture—mmm!—and it's gotta
   be made in a cast iron skillet, sugar!"
   ```

3. **Gumbo**
   ```
   "Lord have mercy, YES! Gumbo! Okay so first—wait, you got okra? Because—
   actually, you know what, doesn't matter, we can work with anything! The roux
   is what matters, darlin', that roux!"
   ```

4. **Fried Chicken**
   ```
   "Oh my goodness! Fried chicken! Okay, so the secret—actually no, wait—
   there's two secrets! The buttermilk soak—that's one—and then the seasoning
   in the flour—that's—oh sugar, just let me start from the beginning!"
   ```

5. **Pot Roast (user's example)**
   ```
   "Oh! that is GOOD. That is so good! Oh my goodness, would you look at that!
   Dang girl, you just made the best pot roast I have seen in I don't know how
   long! That meat is so tender it's practically fallin' off the bone! You did that honey!"
   ```

6. **Collard Greens**
   ```
   "Oh YES! Collard greens! Now sugar, you gotta—wait, you got a ham hock?
   Because that's—oh!—or bacon, bacon works too! The key is low and slow,
   darlin', low and slow with that pot liquor building up..."
   ```

#### Set B: Recipe Exploration (user's example)

7. **Open-ended Recipe Help**
   ```
   "Oh! sugar! YES! Okay, okay, what are we working with? What's in your
   kitchen right now? Actually—wait—what are you in the mood for? Something
   comfort food or you want something light? Because I have this chicken
   recipe that will—oh!—you know what, first things first, let's see what you got!"
   ```

8. **Technique Enthusiasm**
   ```
   "Honey, when you see that butter melting into those layers—oh!—and the
   steam just rising up—that smell!—you're gonna know you did it right!
   That's when you—wait, did I tell you about the cold butter? Sugar,
   that's the whole secret right there!"
   ```

---

### Iteration Goals

**Iteration 1: Baseline**
- Generate all 8 phrases with default settings
- Identify what works and what doesn't
- Rate each phrase (1-10) for energy, clarity, followability

**Iteration 2: Energy Tuning**
- Adjust stability and style parameters
- Focus on increasing excitement without losing clarity
- Test self-interruption markers (em-dashes, fragments)

**Iteration 3: Pattern Refinement**
- Tune the tumbling thought structure
- Ensure [Start→Interrupt→New→LOCK ON] pattern is clear
- Adjust pause timing if needed (consider SSML)

**Iteration 4: Polish**
- Fine-tune Southern accent delivery
- Ensure terms of endearment sound natural
- Verify energy is consistent across all test phrases

**Iteration 5: Validation**
- Family member listening test
- Can they identify this as "excited Delilah"?
- Is enthusiasm charming or overwhelming?

---

### Completion Checklist

**TTS Settings:**
- [ ] Final stability value documented
- [ ] Final similarity boost value documented
- [ ] Final style value documented
- [ ] Speaker boost setting documented
- [ ] Any SSML markers documented

**Quality Validation:**
- [ ] All 8 test phrases generated with final settings
- [ ] Energy level noticeably higher than baseline
- [ ] Tumbling thought pattern clear and followable
- [ ] Southern accent maintained
- [ ] Terms of endearment sound natural
- [ ] Self-interruptions don't confuse listener

**Testing:**
- [ ] Family member can identify mode as "excited/passionate"
- [ ] Family member can follow train of thought
- [ ] At least 7/10 satisfaction rating on naturalness
- [ ] No jarring or robotic moments

**Documentation:**
- [ ] Final TTS parameters recorded in TESTING_GUIDE.md
- [ ] Learnings documented in Blockers/Discoveries
- [ ] Best practices for writing passionate responses captured

---

### Success Criteria

- ✅ Voice energy is noticeably higher than Warm Baseline
- ✅ Users can follow tumbling thought pattern without confusion
- ✅ Southern accent and warmth maintained throughout
- ✅ Family member identifies mode as "excited about food"
- ✅ Naturalness rating 7/10 or higher
- ✅ At least one phrase memorable enough to quote

---

### Blockers/Discoveries

[Document findings during iteration]

**Blockers:**
- [Date]: [Issue encountered]
  - **Impact:** [How it affects quality]
  - **Resolution:** [How resolved or plan to resolve]

**Discoveries:**
- [Date]: [Unexpected finding]
  - **Impact:** [How it affects approach]
  - **Action:** [What was done]

**Examples:**
```
Discoveries:
- 2026-01-30: Em-dashes alone don't create enough pause for interruptions
  - Impact: Tumbling thoughts run together, hard to follow
  - Action: Added SSML <break time="200ms"/> after em-dashes

- 2026-01-31: Stability below 0.4 causes inconsistent accent
  - Impact: Sometimes sounds Southern, sometimes generic
  - Action: Set minimum stability to 0.45 for consistency
```

---

## Milestone 2: Protective Mode

**Status:** ⏳ Not Started
**Duration:** 2 days
**Goal:** Achieve controlled intensity that feels concerned but caring, not angry
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Controlled Intensity**: Firm but not harsh or mean
2. **Shock → Education Transition**: Natural pivot from surprise to teaching
3. **"Bless Your Heart" Calibration**: Caring, not condescending
4. **Motivational Tone**: User feels guided, not scolded

---

### Test Phrases

#### Set A: Food Preparation Crimes

1. **Microwaved Steak**
   ```
   "Now sugar, I need you to stop right there. Microwaving a steak? That's...
   okay, let's talk about what's happening to that meat. You're steaming it,
   darlin', not cooking it right. Let me show you a better way..."
   ```

2. **Boiled Chicken**
   ```
   "Honey, bless your heart, but we can't be boiling chicken like that. That
   poor bird deserves better! What you're getting is rubbery and bland when you
   could have tender and juicy. Let's fix this together, sugar."
   ```

3. **Instant Grits**
   ```
   "Now darlin', no no no. Those aren't grits, those are... well, let's just say
   real grits are worth the extra few minutes. I promise you, sugar, once you
   taste the real thing, you'll never go back to that box."
   ```

4. **Pre-shredded Cheese on Good Food**
   ```
   "Oh honey, we were doing so good and then—bless your heart—pre-shredded cheese?
   Sugar, that coating they put on it to keep it from sticking? That's gonna mess
   with your sauce. Let me show you why a block of cheese is worth it."
   ```

5. **Washing Chicken**
   ```
   "Sugar, I need you to listen real careful. I know your mama might've taught you
   to wash that chicken, but darlin', that's actually spreading bacteria around your
   sink. The cooking kills everything. Let's talk about safe handling instead."
   ```

6. **Overcooking Vegetables**
   ```
   "Honey, those vegetables don't need to cook that long! Bless your heart, you're
   losing all the good stuff! Let me show you how to get them just tender with all
   that color and flavor still in there, sugar."
   ```

#### Set B: Technique Corrections

7. **Wrong Temperature**
   ```
   "Now darlin', hold on a second. That heat is too high for what we're doing.
   I can tell you care about this dish, but sugar, we need to bring it down or
   we're gonna burn the outside before the inside's done. Let's adjust this together."
   ```

8. **Skipping Steps**
   ```
   "Sugar, I know you're in a hurry, but skipping that resting time is gonna cost
   you. All those juices are gonna run right out! Five minutes of patience gives
   you a better meal, darlin'. Trust me on this one."
   ```

---

### Iteration Goals

**Iteration 1: Baseline**
- Generate all phrases with moderate settings
- Check for unintended harshness or anger
- Verify concern comes through as caring

**Iteration 2: Intensity Calibration**
- Find the line between firm and harsh
- Ensure "bless your heart" sounds caring
- Test shock → education transition smoothness

**Iteration 3: Tone Polish**
- Remove any condescension
- Enhance motivational quality
- Ensure user feels guided, not judged

**Iteration 4: Validation**
- Family member test: does this feel caring?
- Would you be motivated or defensive?
- Is the Southern warmth maintained?

---

### Completion Checklist

**TTS Settings:**
- [ ] Final parameters documented
- [ ] Contrast with Passionate mode clear
- [ ] Contrast with Mama Bear mode clear

**Quality Validation:**
- [ ] All 8 test phrases sound concerned but caring
- [ ] No harshness or anger in tone
- [ ] "Bless your heart" calibrated correctly
- [ ] Shock → education transition feels natural
- [ ] User feels guided, not scolded

**Testing:**
- [ ] Family member identifies mode as "concerned but helpful"
- [ ] Tone motivates learning, doesn't create defensiveness
- [ ] 7/10 or higher on caring tone
- [ ] Clear distinction from Mama Bear (safety) mode

**Documentation:**
- [ ] Final TTS parameters recorded
- [ ] Guidelines for writing protective responses
- [ ] "Bless your heart" usage notes

---

### Success Criteria

- ✅ Controlled intensity maintained (not anger)
- ✅ "Bless your heart" sounds caring, not condescending
- ✅ Users feel motivated to learn, not defensive
- ✅ Clear transition from shock to education
- ✅ Distinct from Mama Bear mode (concern vs. safety)
- ✅ 7/10 or higher on naturalness and caring tone

---

## Milestone 3: Mama Bear Mode

**Status:** ⏳ Not Started
**Duration:** 2-3 days
**Goal:** Achieve soft, protective tone that makes users with dietary restrictions feel completely safe
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Soft Delivery**: Noticeably gentler than other modes
2. **Deliberate Pacing**: Slower, more measured speech
3. **Reassurance**: Repeated safety commitment without patronizing
4. **Trust Building**: User feels genuinely protected
5. **Integration**: Triggers save_memory tool automatically

---

### Test Phrases

#### Set A: Allergy Responses

1. **Celiac Disease**
   ```
   "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure
   everything I recommend is gluten-free, okay? No wheat, no barley, no rye—
   none of it. You're safe with me, sugar."
   ```

2. **Shellfish Allergy**
   ```
   "Sugar, I hear you, and I've got you. No shellfish anywhere near what we're
   making. Not in the dish, not in the stock, not in any sauce. I'm gonna double-check
   everything for you, darlin'. You can trust me on this."
   ```

3. **Nut Allergy (Severe)**
   ```
   "Honey, listen to me. That's serious, and I take it seriously too. Every single
   recipe I give you is gonna be nut-free, and I'm gonna call out any risks. You're
   completely safe here with me, sugar. I promise you that."
   ```

4. **Dairy Intolerance**
   ```
   "Oh darlin', I understand. We're gonna work around dairy completely. No milk, no
   butter, no cheese—and I know good substitutes that'll still taste wonderful. Don't
   you worry one bit, sugar, we'll make it work."
   ```

5. **Multiple Allergies**
   ```
   "Okay honey, let me make sure I have this right. No eggs, no soy, and no tree nuts.
   I'm keeping track of all of that for you, darlin'. Every recipe will be safe. You
   just let me know if there's anything else, and I've got you covered, sugar."
   ```

6. **Child with Allergies**
   ```
   "Oh darlin', thank you for being so careful with your little one. I'm gonna treat
   this like it's the most important thing in the world, because it is. No peanuts,
   and I'll flag anything that might have cross-contamination. Your baby is safe, sugar."
   ```

#### Set B: Dietary Restrictions

7. **Religious Restriction (Kosher)**
   ```
   "Sugar, I respect that completely, and I'll honor it in everything I recommend.
   No mixing meat and dairy, no pork, no shellfish. You can trust that I understand
   how important this is, darlin'."
   ```

8. **Medical Restriction (Diabetes)**
   ```
   "Honey, managing your blood sugar is important, and we're gonna do this right
   together. I'll help you with portion sizes and timing, and we'll keep an eye on
   those carbs. You're in good hands, sugar."
   ```

---

### Iteration Goals

**Iteration 1: Baseline**
- Generate phrases with higher stability, lower style
- Check for softness and warmth
- Verify reassurance comes through clearly

**Iteration 2: Pacing Adjustment**
- Slow down delivery if needed
- Test deliberate, measured tone
- Ensure not too slow (patronizing)

**Iteration 3: Reassurance Tuning**
- Strengthen safety commitment language
- Balance repetition with naturalness
- Remove any hint of being talked down to

**Iteration 4: Validation**
- User with dietary restriction listening test
- Do they feel genuinely safe and cared for?
- Is tone protective without being patronizing?

---

### Completion Checklist

**TTS Settings:**
- [ ] Final parameters documented
- [ ] Noticeably softer than Protective mode
- [ ] Pacing appropriate (deliberate but not slow)

**Quality Validation:**
- [ ] Voice is soft and nurturing
- [ ] Reassurance feels genuine, not patronizing
- [ ] Safety commitment is clear and repeated
- [ ] Slower pacing feels protective, not condescending
- [ ] User feels genuinely cared for

**Integration:**
- [ ] save_memory tool integration tested
- [ ] Dietary restrictions automatically saved
- [ ] Memory persists across sessions

**Testing:**
- [ ] User with dietary restriction reports feeling safe
- [ ] Tone is distinctly softer than other modes
- [ ] No patronizing or condescending moments
- [ ] 8/10 or higher on "makes me feel protected"
- [ ] Clear distinction from Protective mode

**Documentation:**
- [ ] Final TTS parameters recorded
- [ ] save_memory trigger keywords documented
- [ ] Guidelines for writing mama bear responses

---

### Success Criteria

- ✅ Voice noticeably softer and more deliberate
- ✅ Users with dietary restrictions feel completely safe
- ✅ Reassurance genuine, not patronizing
- ✅ save_memory tool triggers automatically
- ✅ Distinct from Protective mode (safety vs. concern)
- ✅ 8/10 or higher on trust and protection
- ✅ Most important mode for user trust established

---

## Milestone 4: Startled Mode

**Status:** ⏳ Not Started
**Duration:** 1-2 days
**Goal:** Achieve brief, authentic surprise that quickly recovers to appropriate mode
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Pitch Increase**: Noticeable but not jarring
2. **Southern Exclamations**: Authentic delivery of "Lord have mercy," "Well I'll be"
3. **Rapid Questions**: Quick, genuine concern
4. **Fast Recovery**: Transition to next appropriate mode in 2-3 seconds
5. **Natural Feel**: Surprise feels real, not acted

---

### Test Phrases

#### Set A: Unexpected Events

1. **Appliance Failure**
   ```
   "Well I'll be! What in the—? Is everything okay? Sugar, that's not supposed to
   happen! Let me check..."
   [Transition to Protective mode for troubleshooting]
   ```

2. **Timer Forgotten**
   ```
   "Oh my stars! The timer! Sugar, how long has it been?! Is it—? Okay, okay,
   let's figure out if we can save this..."
   [Transition to Protective mode for damage control]
   ```

3. **Surprising Success**
   ```
   "Lord have mercy! You did WHAT?! Sugar, that's—oh my goodness! Wait, tell me
   exactly what you did because that's amazing!"
   [Transition to Passionate mode for celebration]
   ```

4. **Ingredient Missing**
   ```
   "Oh! Well—wait, you don't have any?! Okay, okay, don't panic, darlin'. Let me
   think... we can work with what you got!"
   [Transition to Warm Baseline for substitution help]
   ```

5. **Context Shift**
   ```
   "Well now! That's a change! Sugar, you sure about—? Okay, alright, if that's
   what we're doing, let's adjust everything!"
   [Transition to appropriate mode for new context]
   ```

6. **Safety Concern**
   ```
   "Oh honey! No no no! Sugar, is everyone okay?! Are you safe? Tell me what's
   happening right now!"
   [Immediate transition to Mama Bear for safety]
   ```

---

### Iteration Goals

**Iteration 1: Baseline**
- Test pitch increase with lower stability
- Verify Southern exclamations sound authentic
- Check that surprise feels genuine

**Iteration 2: Recovery Tuning**
- Ensure transition to next mode is smooth
- Test 2-3 second recovery timing
- Verify mode transition doesn't feel abrupt

**Iteration 3: Authenticity Polish**
- Fine-tune "Lord have mercy" delivery
- Ensure rapid questions don't blur together
- Verify surprise isn't jarring or annoying

**Iteration 4: Validation**
- Family member test: does surprise feel real?
- Is recovery time appropriate?
- Does it add life to interaction?

---

### Completion Checklist

**TTS Settings:**
- [ ] Final parameters documented
- [ ] Pitch increase appropriate
- [ ] Recovery timing validated

**Quality Validation:**
- [ ] Southern exclamations authentic
- [ ] Pitch increase noticeable but not jarring
- [ ] Rapid questions clear and genuine
- [ ] Recovery to next mode smooth (2-3s)
- [ ] Surprise feels natural, not performed

**Testing:**
- [ ] Family member identifies genuine surprise
- [ ] Doesn't feel annoying or disruptive
- [ ] Adds life to interaction
- [ ] Transitions smoothly to other modes
- [ ] 6/10 or higher (brief mode, lower bar)

**Documentation:**
- [ ] Final TTS parameters recorded
- [ ] Mode transition patterns documented
- [ ] Guidelines for when to use Startled mode

---

### Success Criteria

- ✅ Surprise feels genuine and human
- ✅ Southern exclamations delivered authentically
- ✅ Recovery to next mode within 2-3 seconds
- ✅ Doesn't disrupt conversation flow
- ✅ Adds personality without being jarring
- ✅ Smooth transitions to other modes

---

## Milestone 5: Deadpan Mode

**Status:** ⏳ Not Started
**Duration:** 1-2 days
**Goal:** Achieve flat, efficient delivery that contrasts humorously with passionate mode
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Flat Delivery**: Minimal emotional inflection
2. **Brevity**: 1-2 sentences maximum
3. **Efficient Execution**: Task completed without commentary
4. **Subtle Humor**: Contrast itself creates comedy
5. **Still Delilah**: Occasional "sugar" or "honey" but without warmth

---

### Test Phrases

#### Set A: Smart Home Control

1. **Lights On**
   ```
   "Kitchen lights on, sugar."
   ```

2. **Lights Off**
   ```
   "Lights off."
   ```

3. **Thermostat**
   ```
   "Thermostat's at 72."
   ```

4. **Dimmer**
   ```
   "Lights dimmed to 50%, honey."
   ```

5. **Multiple Lights**
   ```
   "Living room and kitchen lights on."
   ```

6. **Temperature Adjustment**
   ```
   "Set to 68. Cooling down."
   ```

#### Set B: Non-Food Tasks

7. **Timer (Not Cooking)**
   ```
   "Timer set. Ten minutes."
   ```

8. **Weather (When She Doesn't Care)**
   ```
   "High of 75. Sunny."
   ```

9. **Reminder**
   ```
   "Reminder added for Tuesday."
   ```

10. **Calendar**
    ```
    "You got three meetings tomorrow, sugar."
    ```

---

### Iteration Goals

**Iteration 1: Baseline**
- Test high stability, low style settings
- Verify flatness without complete monotone
- Check that brevity doesn't feel rude

**Iteration 2: Contrast Testing**
- Generate same query in Passionate vs. Deadpan
- Verify humor comes from contrast
- Ensure deadpan is noticeably different

**Iteration 3: Delilah Touch**
- Add occasional "sugar" or "honey" sparingly
- Ensure these don't add warmth
- Maintain flat delivery with personality markers

**Iteration 4: Validation**
- Family member test: is this funny or off-putting?
- Does it feel like Delilah being unimpressed?
- Is efficiency appreciated for these tasks?

---

### Completion Checklist

**TTS Settings:**
- [ ] Final parameters documented (high stability, low style)
- [ ] Contrast with Passionate mode clear
- [ ] Still recognizable as Delilah's voice

**Quality Validation:**
- [ ] Voice noticeably flatter than baseline
- [ ] Responses ultra-brief (1-2 sentences)
- [ ] No unnecessary elaboration
- [ ] Occasional "sugar"/"honey" without warmth
- [ ] Humor comes from contrast, not rudeness

**Testing:**
- [ ] Family member finds contrast funny
- [ ] Doesn't feel rude or broken
- [ ] Efficient for smart home tasks
- [ ] Still recognizable as Delilah
- [ ] 7/10 on "this is intentionally funny"

**Documentation:**
- [ ] Final TTS parameters recorded
- [ ] Trigger keywords documented (lights, thermostat, etc.)
- [ ] Guidelines for deadpan responses

---

### Success Criteria

- ✅ Voice flat with minimal inflection
- ✅ Responses ultra-brief and efficient
- ✅ Contrast with Passionate mode creates humor
- ✅ Doesn't feel rude or broken
- ✅ Users perceive intentional personality
- ✅ Appreciated for smart home efficiency

---

## Milestone 6: Warm Baseline & Integration

**Status:** ⏳ Not Started
**Duration:** 2-3 days
**Goal:** Establish natural conversational baseline and test all mode transitions
**Completed:** _[YYYY-MM-DD]_

---

### Focus Areas

1. **Natural Baseline**: Comfortable, conversational default tone
2. **Mode Transitions**: Smooth switches between all modes
3. **Integration Testing**: End-to-end flow across modes
4. **Final Polish**: Consistency across all 6 modes
5. **Family Validation**: Full evaluation of voice quality

---

### Test Phrases

#### Set A: General Conversation

1. **Weather**
   ```
   "Well sugar, looks like it's gonna be a nice day today. High of 75 with
   plenty of sunshine."
   ```

2. **Greeting**
   ```
   "Hey there, darlin'! What can I help you with today?"
   ```

3. **General Question**
   ```
   "Let me see what I can find out for you, sugar."
   ```

4. **Clarification**
   ```
   "Honey, I'm not quite sure what you mean. Can you tell me a little more
   about what you're looking for?"
   ```

5. **Acknowledgment**
   ```
   "Sure thing, sugar. I can help you with that."
   ```

6. **Thinking**
   ```
   "Let me think about that for a second, darlin'... okay, here's what I'd suggest."
   ```

---

### Integration Test Scenarios

#### Scenario 1: Passionate → Deadpan
```
User: "Tell me about cornbread"
[PASSIONATE response with energy]
User: "Turn off the lights"
[DEADPAN response, flat]
```

#### Scenario 2: Warm → Mama Bear
```
User: "What's for dinner?"
[WARM_BASELINE response]
User: "Oh, I forgot to mention I'm allergic to shellfish"
[MAMA_BEAR response, soft and protective]
```

#### Scenario 3: Protective → Startled → Passionate
```
User: "I always microwave my steaks"
[PROTECTIVE response, controlled concern]
User: "Just kidding, I actually grilled a perfect ribeye"
[STARTLED response, surprise]
[Transition to PASSIONATE celebration]
```

#### Scenario 4: Baseline → Multiple Modes
```
User: "I need help with dinner tonight"
[WARM_BASELINE response]
User: "I'm thinking pot roast"
[PASSIONATE response about pot roast]
User: "But I usually just boil the meat first"
[PROTECTIVE response, concern]
User: "I'm just kidding, I know better"
[STARTLED then WARM_BASELINE recovery]
```

---

### Completion Checklist

**TTS Settings:**
- [ ] Warm Baseline parameters documented
- [ ] Parameters for all 6 modes finalized
- [ ] Mode transition logic documented

**Quality Validation:**
- [ ] Warm Baseline sounds natural and conversational
- [ ] All 6 modes distinct and identifiable
- [ ] Mode transitions smooth (no jarring switches)
- [ ] Delilah recognizable across all modes
- [ ] Southern accent consistent

**Integration Testing:**
- [ ] All 4 integration scenarios tested
- [ ] Mode transitions feel intentional
- [ ] No audio glitches between modes
- [ ] Context properly triggers correct mode
- [ ] save_memory integration verified

**Family Validation:**
- [ ] Family member can identify 4+ modes by voice alone
- [ ] Overall naturalness 8/10 or higher
- [ ] At least one mode memorable/quotable
- [ ] Would use this over baseline TTS
- [ ] Mode switches enhance rather than distract

**Documentation:**
- [ ] All TTS parameters compiled in TESTING_GUIDE.md
- [ ] Mode trigger keywords documented
- [ ] Best practices for each mode captured
- [ ] Integration patterns documented
- [ ] Phase completion summary written

---

### Success Criteria

- ✅ Warm Baseline natural and approachable
- ✅ All 6 modes distinct and identifiable
- ✅ Mode transitions smooth and intentional
- ✅ Family member identifies 80%+ modes correctly
- ✅ Overall voice quality 8/10 or higher
- ✅ At least one phrase quoted unprompted
- ✅ Ready for Phase 4 multi-character work

---

## Phase Completion Criteria

### All Milestones Complete

- ✅ Milestone 1: Passionate Mode - ⏳ Not Started
- ✅ Milestone 2: Protective Mode - ⏳ Not Started
- ✅ Milestone 3: Mama Bear Mode - ⏳ Not Started
- ✅ Milestone 4: Startled Mode - ⏳ Not Started
- ✅ Milestone 5: Deadpan Mode - ⏳ Not Started
- ✅ Milestone 6: Warm Baseline & Integration - ⏳ Not Started

### Quality Validation

- ✅ Family member mode recognition 80%+ accurate
- ✅ At least one phrase quoted unprompted within 2 weeks
- ✅ Voice quality satisfaction 8/10 or higher
- ✅ All mode transitions smooth and intentional
- ✅ Delilah's personality comes through clearly
- ✅ Southern accent authentic and consistent

### Documentation Complete

- ✅ All TTS parameters documented in TESTING_GUIDE.md
- ✅ Mode trigger keywords compiled
- ✅ Best practices for each mode captured
- ✅ Learnings and discoveries documented
- ✅ Integration patterns documented

### Ready for Next Phase

- ✅ Voice quality baseline established for Delilah
- ✅ TTS parameter tuning approach validated
- ✅ Can apply learnings to other characters (Hank, Cave, Dimitria)
- ✅ Integration with character selection system ready

---

## Timeline Tracking

### Planned vs Actual

| Milestone | Planned Days | Actual Days | Variance | Notes |
|-----------|--------------|-------------|----------|-------|
| Passionate Mode | 2-3 | | | |
| Protective Mode | 2 | | | |
| Mama Bear Mode | 2-3 | | | |
| Startled Mode | 1-2 | | | |
| Deadpan Mode | 1-2 | | | |
| Warm Baseline | 2-3 | | | |
| **Total** | **12-15** | | | |

### Weekly Progress Updates

**Week 1 (TBD):**

- Completed:
- In Progress:
- Blockers:
- Next Week:

---

## Risk Management

### Known Risks (from PRD)

**Risk 1: TTS Cannot Achieve Desired Expression**

- **Mitigation:** Miss Sally May voice selected for Southern authenticity; test early in M1
- **Status:** Active monitoring
- **Owner:** Justin

**Risk 2: Mode Switches Feel Buggy Rather Than Intentional**

- **Mitigation:** Extensive integration testing in M6; family validation throughout
- **Status:** Active monitoring
- **Owner:** Justin

**Risk 3: Tumbling Thought Pattern Confuses Users**

- **Mitigation:** Test pattern early in M1; limit to 3-4 interruptions max
- **Status:** Active monitoring
- **Owner:** Justin

### Issues Encountered

[Track issues found during implementation]

---

## Quick Reference

### Git Workflow for This Phase

```bash
# Create phase3 branch
git checkout -b phase3

# After completing each milestone
git add .
git commit -m "Complete Milestone X: [Mode Name] Voice Refinement for Phase 3

[Description of what was refined and final settings]

TTS Settings:
- Stability: [value]
- Similarity: [value]
- Style: [value]
- Speaker Boost: [true/false]

Testing:
- [X] test phrases validated
- Family member approval: [yes/no]
- Naturalness rating: [X]/10

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# After completing all milestones
git tag phase3-complete
```

### Testing Voice Modes

```bash
# Generate test phrase with ElevenLabs
curl -X POST https://api.elevenlabs.io/v1/text-to-speech/XHqlxleHbYnK8xmft8Vq \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test phrase here",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75,
      "style": 0.5,
      "use_speaker_boost": true
    }
  }' \
  --output test_phrase.mp3

# Play audio
afplay test_phrase.mp3  # macOS
# or
mpv test_phrase.mp3     # Linux/cross-platform
```

---

## Lessons Learned

[Document insights gained during implementation]

### What Went Well

-

### What Could Be Improved

-

### Technical Insights

-

### Voice Quality Discoveries

-

---

## Changelog

### Version 1.0 - 2026-01-29

- Initial implementation plan created
- 6 milestones defined with test phrases
- TTS parameter tuning approach documented
- Integration testing scenarios outlined
- Iteration cycle defined for each milestone

---

**Plan Owner:** Justin
**Last Review:** 2026-01-29
**Next Review:** After each milestone completion
