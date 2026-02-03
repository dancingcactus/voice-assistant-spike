# Phase 3 - Milestone 5: Deadpan Mode - Task Prompt

I'm working on Phase 3 of my Aperture Assist voice assistant project, refining Delilah's voice modes with ElevenLabs TTS.

**Project:** /Users/justin/projects/voice-assistant-spike
**Branch:** phase3

**Completed Milestones:**
- Milestone 1: Passionate Mode (9.0/10) ✅
- Milestone 2: Protective Mode (9.8/10) ✅
- Milestone 3: Mama Bear Mode (10.0/10) ✅
- Milestone 4: Startled Mode (10.0/10) ✅

**Current Task:** Milestone 5 - Deadpan Mode

**Goal:** Achieve flat, minimal engagement for non-food tasks without being rude

**Target:** 7/10 or higher (challenging mode, higher bar than Startled)

**Focus Areas:**
1. Flat Affect - Noticeably less enthusiastic without sounding robotic
2. Minimal Engagement - Brief, efficient responses
3. Character Maintenance - Still recognizably Delilah
4. Not Rude - Disinterested but not hostile or dismissive
5. Southern Markers - Endearments remain but delivered flatly
6. Clear Boundary - "That's not really my thing, sugar"

**Expected TTS Settings:**
- Stability: 0.60-0.70 (higher for controlled, flat delivery)
- Style: 0.30-0.40 (lower to reduce expressiveness)
- Similarity: 0.75
- Speaker Boost: True

**Test Scenarios:** 6-8 phrases covering non-food tasks

**Suggested Test Cases:**
1. Weather queries ("It's 72 degrees, sugar.")
2. Sports scores ("Cowboys won. 24 to 17.")
3. Math/calculations ("That's 47.5, darlin'.")
4. General knowledge ("Abraham Lincoln. 1865.")
5. Device control (non-kitchen) ("Lights are on.")
6. Time/date queries ("It's 3:42 PM, honey.")
7. Music requests ("Playing that now.")
8. Traffic/directions ("Take I-35 North.")

**Evaluation Criteria (1-5 each):**
1. Flat Affect - Reduced energy/enthusiasm
2. Brevity - Short, efficient responses
3. Not Rude - Helpful despite disinterest
4. Character Retention - Still sounds like Delilah
5. Southern Markers - Endearments present but flat
6. Clear Boundaries - Makes disinterest obvious

**Available Tools:**
- `python diagnostics/phase3_voice_testing.py` - Generate audio
- `bash diagnostics/phase3_evaluate.sh` - Interactive evaluation
- Existing infrastructure from Milestones 1-4

**Key Challenge:**
Deadpan is **harder** than it seems. The risks:
- Too flat → sounds robotic/loses character
- Too much personality → not deadpan enough
- Rude tone → breaks character warmth
- Inconsistent → some phrases engaged, others not

**Success Criteria:**
✅ Noticeably different from other modes
✅ Brief and efficient
✅ Not hostile or dismissive
✅ Character voice maintained (accent, endearments)
✅ User understands "this isn't her passion"
✅ 7/10 or higher average

**Key Learnings from Previous Modes:**
- Lower stability = more expressive (so higher for deadpan)
- Text structure as important as TTS settings
- Character consistency paramount (100% in all modes)
- Well-planned baseline can succeed first try
- Story integration should be considered

**Character Context:**
Delilah is a cooking assistant who's having an existential crisis. When asked about non-food topics, she helps (because it's her job) but clearly isn't interested. She's not mean about it—just... flat. Like someone asked to do paperwork when they'd rather be cooking.

**Text Structure Pattern (Proposed):**
- Direct answer first (no preamble)
- Optional brief endearment (flat delivery)
- No elaboration or follow-up questions
- Period instead of exclamation
- Shorter than other modes

**Example:**
- Passionate: "Oh! sugar! YES! Okay, cornbread—let me tell you about cornbread!"
- Deadpan: "It's 72 degrees. Partly cloudy."

**Task Breakdown:**
1. Design 6-8 Deadpan test phrases (non-food topics)
2. Add phrases & settings to phase3_voice_testing.py
3. Add evaluation criteria to phase3_evaluate.sh
4. Generate Iteration 1 baseline audio
5. Run interactive evaluation
6. Analyze results, iterate if needed (expect 2-3 iterations)
7. Create completion report
8. Commit changes

**Additional Consideration:**
Consider adding 1-2 "boundary" phrases where Delilah explicitly states she's not interested in the topic:
- "Sugar, that's not really my thing."
- "I'm a cooking assistant, darlin'. Let me know if you need recipes."

These help establish the mode's purpose while maintaining character.

Please help me set up Deadpan mode test phrases, generate baseline audio, and guide the evaluation process!
