# Phase 3 Voice Testing - Quick Start

## ✅ Setup Complete

All baseline audio has been generated and the evaluation tools are ready to use!

## 🎧 Start Evaluating Now

**Important:** Run all commands from the project root directory:

```bash
cd /Users/justin/projects/voice-assistant-spike
```

### Option 1: Interactive Evaluation (Recommended)

Play all 8 phrases with automatic rating prompts:

```bash
./diagnostics/phase3_evaluate.sh passionate iteration_1_baseline
```

**Note:** No virtual environment activation needed! The script loads `.env` automatically.

This will:
- Play each phrase sequentially
- Ask you to rate 1-10
- Collect your notes
- Save results automatically

### Option 2: Manual Evaluation

Play individual files and rate separately:

```bash
# Play a phrase
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_biscuits.mp3

# Rate it
python diagnostics/phase3_voice_testing.py \
  --mode passionate \
  --iteration iteration_1_baseline \
  --phrase 1 \
  --rate 7 \
  --notes "Good energy but needs more warmth"
```

## 📊 View Results

```bash
python diagnostics/phase3_voice_testing.py --mode passionate --show-results
```

## 🎯 What to Listen For

The evaluation script will ask you to rate each phrase on **6 criteria** using a **1-5 scale**:

### 1. Southern Authenticity (1-5)
How well does this represent the Southern accent?
- 1 = Generic/no accent
- 3 = Some Southern qualities
- 5 = Authentic, natural Southern accent

### 2. Character Fit (1-5)
How well does the phrasing fit Delilah's character?
- 1 = Doesn't sound like Delilah at all
- 3 = Somewhat fits her personality
- 5 = Perfect match for her character

### 3. Energy Matching Mode (1-5)
How well does the energy match the Passionate mode?
- 1 = Too flat/no excitement
- 3 = Some energy but not passionate
- 5 = Perfect passionate energy level

### 4. Followability (1-5)
How easily can you follow what she is saying and her thought process?
- 1 = Confusing, can't track thoughts
- 3 = Mostly followable with some confusion
- 5 = Easy to follow despite interruptions

### 5. Speed (1-5)
How well does the speed match the energy level she should have?
- 1 = Too slow or too fast
- 3 = Decent speed but not quite right
- 5 = Perfect pacing for passionate mode

### 6. Timing and Emphasis (1-5)
Do the pauses and emphasis feel natural?
- 1 = Awkward pauses or wrong emphasis
- 3 = Mostly natural with some issues
- 5 = Perfect timing and emphasis

**Average Rating:** The script calculates the average automatically

## 🔄 After Evaluation

Once you've rated all phrases, we'll:

1. **Analyze Ratings**: Identify what needs improvement
2. **Adjust Parameters**: Tune stability/style for Iteration 2
3. **Regenerate**: Create new audio with updated settings
4. **Compare**: Side-by-side with baseline
5. **Iterate**: Repeat until we hit 7/10+ naturalness

## 📁 All Available Phrases

1. **biscuits** - Flaky vs tender decision
2. **cornbread** - Not-sweet Southern style
3. **gumbo** - Roux is everything
4. **fried_chicken** - Two secrets buildup
5. **pot_roast** - Praising user's success
6. **collard_greens** - Low and slow technique
7. **recipe_help** - Open-ended exploration
8. **technique_enthusiasm** - Cold butter revelation

## 🚀 Next Iteration

To generate Iteration 2 (after updating settings):

```bash
# Edit settings in diagnostics/phase3_voice_testing.py
# Then generate:
python diagnostics/phase3_voice_testing.py --mode passionate --iteration iteration_2_energy
```

## 🆘 Troubleshooting

**"ELEVENLABS_API_KEY not found":**
- Fixed! Script now loads `.env` automatically
- Verify: `grep ELEVENLABS_API_KEY .env` shows your key

**No audio files found:**
- Run: `ls diagnostics/phase3_audio/`
- Should show 8 MP3 files + evaluation_results.json

**Can't play audio:**
- macOS: Use `afplay` (built-in)
- Linux: Use `mpg123` or `vlc`
- Windows: Use any MP3 player

---

**Ready?** Run `./diagnostics/phase3_evaluate.sh` and start listening! 🎵
