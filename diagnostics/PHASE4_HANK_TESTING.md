# Phase 4 Hank Voice Testing Workflow

## Overview

This directory contains tools for iteratively refining Hank's four voice modes through systematic TTS parameter tuning.

## Quick Start

**Prerequisites:** Ensure your `.env` file contains:
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key
- `ELEVENLABS_HANK_VOICE_ID` - Hank voice ID

The script automatically loads environment variables from `.env`.

### 1. Generate Test Phrases

Generate all phrases for a mode and iteration:

```bash
python diagnostics/phase4_hank_voice_testing.py --mode working --iteration iteration_1_baseline
```

Generate a single phrase:

```bash
python diagnostics/phase4_hank_voice_testing.py --mode protective --phrase 1 --iteration iteration_1_baseline
```

List available phrases:

```bash
python diagnostics/phase4_hank_voice_testing.py --mode resigned --list-phrases
```

### 2. Evaluate Audio Quality

Play all phrases and rate them interactively:

```bash
./diagnostics/phase4_hank_evaluate.sh working iteration_1_baseline
```

Or play a single file manually:

```bash
afplay diagnostics/phase4_audio/working_iteration_1_baseline_lights_timer.mp3
```

Then rate it:

```bash
python diagnostics/phase4_hank_voice_testing.py \
  --mode working \
  --iteration iteration_1_baseline \
  --phrase 1 \
  --rate 8 \
  --notes "Good brevity; needs slightly more gravel"
```

### 3. View Results

Show ratings for all iterations:

```bash
python diagnostics/phase4_hank_voice_testing.py --mode working --show-results
```

Show ratings for a specific iteration:

```bash
python diagnostics/phase4_hank_voice_testing.py \
  --mode working \
  --iteration iteration_1_baseline \
  --show-results
```

## File Organization

```
diagnostics/
├── phase4_hank_voice_testing.py
├── phase4_hank_evaluate.sh
├── PHASE4_HANK_TESTING.md
└── phase4_audio/
    ├── evaluation_results.json
    └── [mode]_[iteration]_[phrase_id].mp3
```

## Notes

- Mode list: `working`, `protective`, `resigned`, `grumble`
- Default settings live inside `ITERATION_SETTINGS` in the script.
- The evaluation script stores ratings in `diagnostics/phase4_audio/evaluation_results.json`.
