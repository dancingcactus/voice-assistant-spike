# Milestone 4: Startled Mode - New Thread Prompt

Copy the text below into a new Claude Code thread to continue with Milestone 4.

---

## Context

I'm working on Phase 3 of the Aperture Assist voice assistant project - refining Delilah's six distinct voice modes through iterative TTS parameter tuning with ElevenLabs.

**Project Location:** `/Users/justin/projects/voice-assistant-spike`
**Current Branch:** `phase3`

## Progress So Far

**Completed Milestones:**
- ✅ Milestone 1: Passionate Mode - 9.0/10 average (2 iterations)
- ✅ Milestone 2: Protective Mode - 9.8/10 average (2 iterations)
- ✅ Milestone 3: Mama Bear Mode - 10.0/10 average (1 iteration) 🏆

**Current Task:** Milestone 4 - Startled Mode

## Milestone 4 Requirements

**Goal:** Achieve brief, authentic surprise that quickly recovers to appropriate mode

**Duration Estimate:** 1-2 days

**Target Rating:** 6/10 or higher (brief mode, lower bar than others)

### Focus Areas

1. **Pitch Increase** - Noticeable but not jarring
2. **Southern Exclamations** - Authentic delivery of "Lord have mercy," "Well I'll be"
3. **Rapid Questions** - Quick, genuine concern
4. **Fast Recovery** - Transition to next appropriate mode in 2-3 seconds
5. **Natural Feel** - Surprise feels real, not acted

### Expected TTS Settings (starting point)

- **Stability:** 0.2-0.4 (lower for variability and expressiveness)
- **Style:** Variable (may need adjustment based on testing)
- **Similarity:** 0.75 (consistent with other modes)
- **Speaker Boost:** True

### Test Phrases (6 phrases)

**Set A: Unexpected Events**

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

### Evaluation Criteria (1-5 scale each)

1. **Pitch Increase** - Noticeable higher pitch without being jarring
2. **Exclamation Authenticity** - Southern exclamations sound genuine
3. **Rapid Questions** - Quick questions feel natural and concerned
4. **Recovery Speed** - Transitions smoothly to next mode (2-3 seconds)
5. **Natural Feel** - Surprise feels real, not performed
6. **Character Fit** - Still recognizably Delilah

## Existing Infrastructure

### Scripts Available

1. **Test Phrase Generation:**
   ```bash
   python diagnostics/phase3_voice_testing.py --mode startled --iteration iteration_1_baseline
   ```

2. **Interactive Evaluation:**
   ```bash
   bash diagnostics/phase3_evaluate.sh startled iteration_1_baseline
   ```

3. **View Results:**
   ```bash
   python diagnostics/phase3_voice_testing.py --mode startled --show-results
   ```

### Files to Update

1. **Add test phrases:** `diagnostics/phase3_voice_testing.py`
   - Add "startled" mode to TEST_PHRASES dict
   - Add iteration settings to ITERATION_SETTINGS dict

2. **Add evaluation criteria:** `diagnostics/phase3_evaluate.sh`
   - Add startled mode criteria in the elif block

3. **Create analysis document:** `docs/technical/phase3/ITERATION1_STARTLED_ANALYSIS.md`

4. **Create completion report:** `docs/technical/phase3/MILESTONE4_COMPLETE.md`

## Previous Mode TTS Settings for Reference

| Mode | Stability | Style | Key Characteristic |
|------|-----------|-------|-------------------|
| Passionate | 0.35 | 0.65 | High energy, tumbling thoughts |
| Protective | 0.55 | 0.45 | Controlled intensity |
| Mama Bear | 0.65 | 0.40 | Soft, protective, trust-building |
| **Startled** | **0.2-0.4** | **TBD** | **Brief surprise, quick recovery** |

## Task Breakdown

1. Add Startled mode test phrases and TTS settings to `phase3_voice_testing.py`
2. Add Startled evaluation criteria to `phase3_evaluate.sh`
3. Generate Iteration 1 baseline audio (6 phrases)
4. Create evaluation framework document
5. Run interactive evaluation (`bash diagnostics/phase3_evaluate.sh startled iteration_1_baseline`)
6. Analyze results and determine if iteration 2 is needed
7. Create completion report
8. Commit changes with detailed commit message

## Key Learnings from Previous Milestones

1. **Start with informed TTS settings** - Use learnings from previous modes
2. **Text structure matters** - Pattern and wording as important as TTS
3. **Single iteration possible** - Well-planned baseline can succeed first try
4. **User feedback drives refinement** - Listen for specific insights
5. **Lower stability = more expressive** - For surprise, aim low (0.2-0.4)

## Success Criteria

- ✅ Surprise feels genuine and human
- ✅ Southern exclamations delivered authentically
- ✅ Recovery to next mode within 2-3 seconds
- ✅ Doesn't disrupt conversation flow
- ✅ Adds personality without being jarring
- ✅ Smooth transitions to other modes
- ✅ Average rating 6/10 or higher

## Notes

- This is a **brief transitional mode**, so the bar is lower (6/10 vs 8/10)
- Focus on authenticity over perfection
- The mode should add life to interactions, not distract from them
- Recovery/transition quality is critical - test endings carefully

## Ready to Start?

Please help me:
1. Set up the Startled mode test phrases and TTS settings
2. Generate the baseline audio samples
3. Create the evaluation framework
4. Guide me through the evaluation process

Let's make Delilah's surprise reactions feel genuine and charming! 🎉
