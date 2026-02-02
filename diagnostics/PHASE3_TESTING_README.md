# Phase 3 Voice Testing Workflow

## Overview

This directory contains tools for iteratively refining Delilah's six voice modes through systematic TTS parameter tuning.

## Quick Start

**Prerequisites:** Ensure your `.env` file contains:
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key
- `ELEVENLABS_VOICE_ID` - Miss Sally May voice ID (XHqlxleHbYnK8xmft8Vq)

The script automatically loads environment variables from `.env`.

### 1. Generate Test Phrases

Generate all phrases for a mode and iteration:

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --iteration iteration_1_baseline
```

Generate a single phrase:

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --phrase 1 --iteration iteration_1_baseline
```

List available phrases:

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --list-phrases
```

### 2. Evaluate Audio Quality

Play all phrases and rate them interactively:

```bash
./diagnostics/phase3_evaluate.sh passionate iteration_1_baseline
```

Or play a single file manually:

```bash
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_biscuits.mp3
```

Then rate it:

```bash
python diagnostics/phase3_voice_testing.py \
  --mode passionate \
  --iteration iteration_1_baseline \
  --phrase 1 \
  --rate 7 \
  --notes "Good energy but needs more variation"
```

### 3. View Results

Show ratings for all iterations:

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --show-results
```

Show ratings for specific iteration:

```bash
python diagnostics/phase3_voice_testing.py \
  --mode passionate \
  --iteration iteration_1_baseline \
  --show-results
```

## Iteration Workflow

Each milestone (voice mode) follows this cycle:

### Iteration 1: Baseline

1. Generate all phrases with baseline settings
2. Listen and rate each phrase (1-10) on:
   - Energy level (appropriate for mode?)
   - Clarity (words clear and understandable?)
   - Followability (easy to track thought flow?)
3. Document what works and what doesn't

### Iteration 2: Energy Tuning

1. Adjust stability and style parameters
2. Regenerate phrases with new settings
3. Compare side-by-side with baseline
4. Rate improvements

### Iteration 3: Pattern Refinement

1. Fine-tune specific aspects (pauses, emphasis, etc.)
2. May involve text adjustments (SSML, punctuation)
3. Focus on mode-specific characteristics

### Iteration 4: Polish

1. Final tweaks to accent delivery
2. Terms of endearment naturalness
3. Overall consistency check

### Iteration 5: Validation

1. Family member listening test
2. Mode identification test
3. Naturalness rating
4. Collect qualitative feedback

## TTS Parameter Reference

### Stability (0-1)

- **Lower (0.2-0.4)**: More expressive, variable delivery
  - Use for: Passionate, Startled modes
  - Risk: May lose consistency
- **Medium (0.5-0.6)**: Balanced expression
  - Use for: Warm Baseline, Protective modes
- **Higher (0.7-0.9)**: Consistent, controlled delivery
  - Use for: Mama Bear, Deadpan modes

### Similarity Boost (0-1)

- Generally keep at **0.75** for Miss Sally May voice
- Adjusting this changes how closely it matches the original voice character

### Style (0-1)

- **Lower (0.2-0.3)**: Minimal style exaggeration
  - Use for: Deadpan mode
- **Medium (0.4-0.6)**: Natural expression
  - Use for: Warm Baseline, Protective, Mama Bear
- **Higher (0.7-0.8)**: Exaggerated style
  - Use for: Passionate, Startled modes

### Speaker Boost

- Keep **enabled** for clarity and consistency
- Only disable if testing specific edge cases

## File Organization

```
diagnostics/
├── phase3_voice_testing.py      # Main testing script
├── phase3_evaluate.sh           # Interactive evaluation helper
├── PHASE3_TESTING_README.md     # This file
└── phase3_audio/                # Generated audio files
    ├── evaluation_results.json  # Ratings and notes
    └── [mode]_[iteration]_[phrase_id].mp3
```

## Adding New Iterations

Edit [phase3_voice_testing.py](phase3_voice_testing.py:56-72) and add to `ITERATION_SETTINGS`:

```python
ITERATION_SETTINGS = {
    "passionate": {
        "iteration_3_pattern": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.65,
            "use_speaker_boost": True,
            "notes": "Slightly increased stability for consistency"
        }
    }
}
```

## Comparing Iterations

Play two iterations side-by-side:

```bash
# Terminal 1
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_biscuits.mp3

# Terminal 2
afplay diagnostics/phase3_audio/passionate_iteration_2_energy_biscuits.mp3
```

## Evaluation Criteria (1-5 Scale)

The evaluation script asks for ratings on 6 criteria:

### 1. Southern Authenticity (1-5)
How well does this represent the Southern accent?
- Does the accent sound genuine?
- Are terms of endearment ("sugar", "honey", "darlin'") natural?
- Any moments that break character?

### 2. Character Fit (1-5)
How well does the phrasing fit Delilah's character?
- Does this sound like Delilah specifically?
- Are the word choices and mannerisms right?
- Would she say this?

### 3. Energy Matching Mode (1-5)
How well does the energy match the mode (e.g., Passionate)?
- Is the energy level appropriate for this mode?
- Compare to what Warm Baseline should sound like
- Not too extreme (jarring/overwhelming) or too flat

### 4. Followability (1-5)
How easily can you follow what she is saying and her thought process?
- Can you track the train of thought?
- Do interruptions enhance or confuse?
- Would you be able to cook from this?

### 5. Speed (1-5)
How well does the speed match the energy level she should have?
- Too fast/rapid-fire and incomprehensible?
- Too slow and boring?
- Just right for the mode?

### 6. Timing and Emphasis (1-5)
Do the pauses and emphasis feel natural?
- Do em-dashes (—) create enough pause?
- Are words emphasized correctly?
- Does pacing feel conversational?

**The script calculates the average rating automatically**

## Current Status

### Milestone 1: Passionate Mode

- [x] Iteration 1 baseline complete (8 phrases generated)
- [ ] Baseline evaluation and ratings
- [ ] Iteration 2 parameter tuning
- [ ] Iteration 3 pattern refinement
- [ ] Iteration 4 polish
- [ ] Iteration 5 family validation

## Next Steps

1. **Listen to all baseline phrases** using `./diagnostics/phase3_evaluate.sh`
2. **Rate each phrase** on energy, clarity, and followability
3. **Document findings** in implementation plan
4. **Adjust parameters** for Iteration 2
5. **Regenerate and compare**
