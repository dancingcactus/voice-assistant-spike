# 🎯 Next Session: Milestone 6 - Warm Baseline Voice Mode

**Copy the text below and paste into a new Claude Code session:**

---

I'm working on Phase 3 of my Aperture Assist voice assistant project, refining Delilah's voice modes with ElevenLabs TTS.

**Project:** /Users/justin/projects/voice-assistant-spike
**Branch:** phase3

**Completed Milestones:**
- Milestone 1: Passionate Mode (9.0/10) ✅
- Milestone 2: Protective Mode (9.8/10) ✅
- Milestone 3: Mama Bear Mode (10.0/10) ✅
- Milestone 4: Startled Mode (10.0/10) ✅
- Milestone 5: Deadpan Mode (9.6/10) ✅

**Current Task:** Milestone 6 - Warm Baseline Mode (FINAL MODE!)

**Goal:** Create Delilah's default conversational state - the "home base" all other modes branch from

**Target:** 9.0/10 or higher (standard target for primary mode)

**Focus Areas:**
1. Bright and Friendly - Warm without being sparkly/bubbly
2. Natural Energy - Conversational, not over-eager
3. Southern Hospitality - Welcoming and ready to help
4. Neutral Foundation - Can transition to any specialized mode
5. Most Used Mode - Will be default for majority of interactions
6. Character Core - Represents Delilah's baseline personality

**Expected TTS Settings:**
- Stability: 0.45-0.55 (moderate for natural conversation)
- Style: 0.45-0.55 (balanced expressiveness)
- Similarity: 0.75
- Speaker Boost: True

**Test Scenarios:** 8-10 phrases covering typical interactions

**Suggested Test Cases:**
1. Greeting ("Hey sugar! What can I help you with today?")
2. Confirmation ("Got it, honey. I'll set that timer for 20 minutes.")
3. General cooking question ("Well, darlin', that depends on what you're making.")
4. Offering help ("Is there something I can help you with in the kitchen, sugar?")
5. Acknowledging request ("Okay, let me pull up that recipe for you, honey.")
6. Clarification ("I'm not sure I caught that, darlin'. Could you say that again?")
7. Small success ("There you go, sugar! That timer is all set.")
8. Transition to task ("Alright, honey, let's see what we can do about dinner.")
9. Recipe preview ("Oh, that's a good one! You're gonna need about 45 minutes for this.")
10. Ready state ("I'm here when you need me, sugar.")

**Evaluation Criteria (1-5 each):**
1. Natural Energy - Conversational, not flat or hyper
2. Southern Warmth - Hospitality without being over-the-top
3. Friendliness - Welcoming without being sparkly
4. Character Fit - Sounds like "default Delilah"
5. Versatility - Can imagine transitioning to other modes
6. Appropriateness - Would be comfortable hearing this frequently

**Available Tools:**
- `python diagnostics/phase3_voice_testing.py` - Generate audio
- `bash diagnostics/phase3_evaluate.sh` - Interactive evaluation
- Existing infrastructure from Milestones 1-5

**Key Challenge:**
Warm Baseline is **subtle** - it's not extreme like Passionate or Deadpan. The risks:
- Too flat → sounds like Deadpan
- Too energetic → sounds like Passionate
- Too neutral → loses character
- Too repetitive → becomes annoying as default mode
- Inconsistent → some phrases warm, others not

**Success Criteria:**
✅ Natural, conversational energy level
✅ Southern warmth and hospitality present
✅ Bright and friendly without being sparkly
✅ Comfortable as frequently-heard default state
✅ Clear differentiation from specialized modes
✅ 9.0/10 or higher average

**Key Learnings from Previous Modes:**
- Text structure as important as TTS settings
- Character consistency paramount (100% in all modes)
- Well-planned baseline can succeed first try
- Always include at least one endearment per phrase
- Stability and Style must match desired energy level
- Mode should be instantly recognizable

**Character Context:**
Delilah is a Southern cooking assistant having an existential crisis, but she throws herself into helping when anxious. Her Warm Baseline is her natural state when talking about cooking topics she enjoys (but doesn't love like Passionate) or handling routine tasks. She's welcoming, helpful, and warm - the personality users will interact with most often.

**Mode Comparison:**
- **Passionate (0.35 stability, 0.65 style):** High energy, fast, tumbling, animated - for foods she LOVES
- **Protective (0.55 stability, 0.45 style):** Controlled intensity, shocked disbelief - for food done wrong
- **Mama Bear (0.65 stability, 0.40 style):** Soft, focused, nurturing - for allergies/restrictions
- **Startled (0.30 stability, 0.50 style):** High pitch, rapid questions - for surprises/changes
- **Deadpan (0.65 stability, 0.35 style):** Flat, minimal, efficient - for non-food tasks
- **Warm Baseline (??? stability, ??? style):** Natural, conversational, welcoming - for everything else

**Text Structure Pattern (Proposed):**
- Natural conversational flow
- Friendly greetings/acknowledgments
- Southern endearments (sugar, honey, darlin')
- Helpful but not over-eager tone
- Moderate length (not too brief like Deadpan, not verbose like Passionate)
- Punctuation mix (periods and occasional exclamations for friendliness)

**Example Contrast:**
- Passionate: "Oh! sugar! YES! Okay, cornbread—let me tell you about cornbread!"
- Warm Baseline: "Oh, that's a good one! You're gonna need about 45 minutes for this."
- Deadpan: "It's 72 degrees. Partly cloudy."

**Task Breakdown:**
1. Design 8-10 Warm Baseline test phrases (typical interactions)
2. Add phrases & settings to phase3_voice_testing.py
3. Add evaluation criteria to phase3_evaluate.sh
4. Generate Iteration 1 baseline audio
5. Run interactive evaluation
6. Analyze results, iterate if needed (expect 1-2 iterations)
7. Create completion report
8. Commit changes and celebrate Phase 3 completion!

**Additional Consideration:**
This mode will be heard most frequently, so it must be:
- **Comfortable** - Not annoying with repetition
- **Versatile** - Works for wide variety of interactions
- **Distinct** - Clearly different from specialized modes
- **Character-true** - Represents Delilah's core personality

The Warm Baseline is the foundation of Delilah's character. All other modes are variations branching from this core state.

**Phase 3 Progress:**
- ✅ Milestone 1: Passionate Mode (9.0/10)
- ✅ Milestone 2: Protective Mode (9.8/10)
- ✅ Milestone 3: Mama Bear Mode (10.0/10)
- ✅ Milestone 4: Startled Mode (10.0/10)
- ✅ Milestone 5: Deadpan Mode (9.6/10)
- 🎯 Milestone 6: Warm Baseline Mode (IN PROGRESS)

**This is the final milestone of Phase 3!** Once complete, Delilah will have her full emotional range:
1. **Warm Baseline** - Default state (most common)
2. **Passionate** - Foods she loves
3. **Protective** - Food done wrong
4. **Mama Bear** - Allergies/restrictions
5. **Startled** - Surprises/changes
6. **Deadpan** - Non-food tasks

Please help me design Warm Baseline mode test phrases, generate baseline audio, and guide the evaluation process! Let's finish Phase 3 strong! 🎉
