# Evaluation Workflow Example

This document shows what the evaluation process looks like when you run the script.

## Running the Evaluation

```bash
./diagnostics/phase3_evaluate.sh passionate iteration_1_baseline
```

## Example Evaluation Flow

```
=== Phase 3 Voice Evaluation ===
Mode: passionate
Iteration: iteration_1_baseline

Playing all phrases. Press Ctrl+C to skip to next phrase.
Press Ctrl+C twice to exit.

[1] Playing: biscuits
File: passionate_iteration_1_baseline_biscuits.mp3

[Audio plays: "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait,
you want flaky or you want tender? Because—oh!—actually both! Let me tell
you, when you work that butter into the flour just right..."]

=== Evaluation Criteria (1-5 scale) ===

Southern Authenticity (1-5) - How well does this represent the Southern accent: 4
Character Fit (1-5) - How well does the phrasing fit the character: 4
Energy Matching Mode (1-5) - How well does the energy match the mode: 3
Followability (1-5) - How easily can you follow what she is saying: 4
Speed (1-5) - How well the speed matches the energy level she should have: 3
Timing and Emphasis (1-5) - Do the pauses and emphasis feel natural: 4

Additional Notes (optional): Good accent and character but needs more energy,
feels a bit too measured for passionate mode

Average rating: 3.7/5

[2] Playing: cornbread
File: passionate_iteration_1_baseline_cornbread.mp3

[Audio plays: "Oh honey! Now you're talkin'! Real Southern cornbread—not
that sweet stuff—no sir! You want that golden crust, that crumbly texture—
mmm!—and it's gotta be made in a cast iron skillet, sugar!"]

=== Evaluation Criteria (1-5 scale) ===

Southern Authenticity (1-5) - How well does this represent the Southern accent: 5
Character Fit (1-5) - How well does the phrasing fit the character: 5
Energy Matching Mode (1-5) - How well does the energy match the mode: 4
Followability (1-5) - How easily can you follow what she is saying: 5
Speed (1-5) - How well the speed matches the energy level she should have: 4
Timing and Emphasis (1-5) - Do the pauses and emphasis feel natural: 4

Additional Notes (optional): This one is much better! Energy is good,
accent shines through

Average rating: 4.5/5

[Continues for all 8 phrases...]

=== Evaluation Complete ===

To see results:
  python diagnostics/phase3_voice_testing.py --mode passionate --show-results
```

## Viewing Results

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --show-results
```

Output:
```
=== PASSIONATE - iteration_1_baseline ===
Generated: 2026-02-01T20:01:00.001219
Settings: {
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0.5,
  "use_speaker_boost": true,
  "notes": "Baseline with default settings"
}

Phrases:
  1. biscuits: 7/10
     Notes: Southern:4/5, Character:4/5, Energy:3/5, Followability:4/5,
            Speed:3/5, Timing:4/5 | Good accent and character but needs
            more energy, feels a bit too measured for passionate mode

  2. cornbread: 9/10
     Notes: Southern:5/5, Character:5/5, Energy:4/5, Followability:5/5,
            Speed:4/5, Timing:4/5 | This one is much better! Energy is
            good, accent shines through

  3. gumbo: 8/10
     Notes: Southern:4/5, Character:5/5, Energy:4/5, Followability:4/5,
            Speed:4/5, Timing:3/5 | ...

  [... etc ...]

Average rating: 8.0/10 (8/8 rated)
```

## Interpreting Results

### High Scores (4-5/5 in a category)
- This aspect is working well
- Keep these parameters for this criterion

### Medium Scores (3/5 in a category)
- Needs improvement
- Adjust parameters for next iteration

### Low Scores (1-2/5 in a category)
- Significant issue
- Major parameter change needed

## Parameter Adjustment Guide

Based on your ratings, here's what to adjust:

### If Energy is Low (2-3/5)
**Problem:** Not excited enough for Passionate mode

**Adjustments:**
- Decrease stability: `0.5` → `0.3` (more variation)
- Increase style: `0.5` → `0.7` (more expression)

### If Speed is Wrong (2-3/5)
**Problem:** Too fast or too slow

**Note:** ElevenLabs doesn't have a direct speed parameter, but:
- Lower stability can increase variation in pacing
- May need to adjust text (shorter sentences, more breaks)

### If Timing is Off (2-3/5)
**Problem:** Pauses or emphasis feel unnatural

**Adjustments:**
- Add SSML breaks: `<break time="300ms"/>`
- Adjust punctuation (commas, em-dashes)
- May need to rewrite phrase structure

### If Southern Authenticity is Low (2-3/5)
**Problem:** Accent not coming through

**Note:** This is mostly about the voice model itself, but:
- Increase similarity_boost: `0.75` → `0.85` (closer to Miss Sally May)
- May indicate voice model limitation

### If Character Fit is Low (2-3/5)
**Problem:** Doesn't sound like Delilah

**Adjustments:**
- Review phrase text (word choice, mannerisms)
- Ensure terms of endearment are included
- Check for character-specific speech patterns

### If Followability is Low (2-3/5)
**Problem:** Hard to track thought process

**Adjustments:**
- Simplify sentence structure
- Add clearer pause markers
- Reduce number of interruptions
- Increase stability for more consistency

## Next Steps After Evaluation

1. **Identify Patterns**: Which criteria scored lowest across all phrases?
2. **Adjust Parameters**: Focus on 1-2 key areas for Iteration 2
3. **Regenerate**: Create new audio with updated settings
4. **Compare**: Listen to baseline vs Iteration 2 side-by-side
5. **Iterate**: Continue refining until average rating is 4.0+/5 (8+/10)

## Success Criteria

From the Implementation Plan:
- ✅ Average rating of **3.5+/5** (7+/10) = Good
- ✅ Average rating of **4.0+/5** (8+/10) = Very Good
- ✅ Average rating of **4.5+/5** (9+/10) = Excellent

**Goal:** Achieve 4.0+/5 average with no single criterion below 3/5
