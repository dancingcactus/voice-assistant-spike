# Iteration 2 vs Baseline - Comparison Guide

**Created:** 2026-02-01
**Purpose:** Compare Iteration 2 (energy-tuned) with Iteration 1 (baseline)

---

## What Changed

### Parameter Adjustments

| Parameter | Baseline (Iter 1) | Energy (Iter 2) | Change |
|-----------|-------------------|-----------------|--------|
| **Stability** | 0.5 | 0.35 | ⬇ -0.15 (more variation) |
| **Style** | 0.5 | 0.65 | ⬆ +0.15 (more expression) |
| **Similarity** | 0.75 | 0.75 | ✓ No change |
| **Speaker Boost** | True | True | ✓ No change |

**Goal:** Maintain higher energy throughout phrases, prevent energy drop mid-sentence

---

## How to Compare

### Side-by-Side Listening

Play both versions of the same phrase back-to-back:

```bash
# Biscuits (Problem phrase - Energy 2/5 in baseline)
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_biscuits.mp3
afplay diagnostics/phase3_audio/passionate_iteration_2_energy_biscuits.mp3

# Collard Greens (Problem phrase - Energy 3/5 in baseline)
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_collard_greens.mp3
afplay diagnostics/phase3_audio/passionate_iteration_2_energy_collard_greens.mp3

# Gumbo (Perfect baseline - Energy 5/5, compare consistency)
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_gumbo.mp3
afplay diagnostics/phase3_audio/passionate_iteration_2_energy_gumbo.mp3
```

### What to Listen For

#### 1. Energy Maintenance (Primary Goal)
**Baseline Issue:** "Starts high energy then settles back into slow southern pace"

**Questions:**
- Does Iteration 2 maintain energy throughout?
- Is the energy level more consistent start-to-finish?
- Does it still sound natural or too forced?

**Target:** Energy score should improve from 3.6/5 → 4.0+/5

---

#### 2. Speed Consistency (Secondary Goal)
**Baseline Issue:** Speed slows down when energy drops

**Questions:**
- Does the pacing stay more consistent?
- Is the speed appropriate for passionate mode?
- Too fast and unclear, or too slow and boring?

**Target:** Speed score should improve from 3.8/5 → 4.0+/5

---

#### 3. Southern Authenticity (Should Stay Perfect)
**Baseline:** 5.0/5 across all phrases

**Questions:**
- Does the accent still sound genuine?
- Are terms of endearment still natural?
- Any loss of authenticity with more variation?

**Target:** Maintain 5.0/5 (no regression)

---

#### 4. Character Fit (Should Stay Perfect)
**Baseline:** 5.0/5 across all phrases

**Questions:**
- Does it still sound like Delilah?
- Do the mannerisms come through?
- Does higher expression enhance or detract from character?

**Target:** Maintain 5.0/5 (no regression)

---

#### 5. Followability
**Baseline:** 4.1/5 average (mostly good)

**Questions:**
- Is it still easy to follow?
- Do interruptions work better or worse?
- Any clarity issues with more variation?

**Target:** Maintain 4.0+/5 (no significant regression)

---

#### 6. Timing and Emphasis
**Baseline:** 3.6/5 average

**Questions:**
- Do pauses feel more natural?
- Is emphasis in the right places?
- Does variation help or hurt timing?

**Target:** Improve to 4.0+/5 or maintain

---

## Priority Phrases to Test

### 🔴 High Priority (Problem Phrases)

#### 1. Biscuits (Baseline: 7/10)
**Baseline Issues:**
- Energy: 2/5 (too low)
- Speed: 2/5 (too slow)
- Timing: 3/5 (pauses don't enhance)

**Text:** "Oh! sugar! YES! Okay, okay, buttermilk biscuits are—wait, you want flaky or you want tender? Because—oh!—actually both! Let me tell you, when you work that butter into the flour just right..."

**What to Check:**
- Does it sound more excited from the start?
- Is the speed faster/more energetic?
- Do the interruptions create better energy flow?

**Target Improvement:** 7/10 → 8+/10

---

#### 2. Collard Greens (Baseline: 7/10)
**Baseline Issues:**
- Energy: 3/5 ("starts high then settles")
- Followability: 3/5 (energy drop affects clarity)
- Speed: 3/5 (slows down mid-phrase)

**Text:** "Oh YES! Collard greens! Now sugar, you gotta—wait, you got a ham hock? Because that's—oh!—or bacon, bacon works too! The key is low and slow, darlin', low and slow with that pot liquor building up..."

**What to Check:**
- Does energy stay high throughout?
- Is the second half more energetic than baseline?
- Does it maintain passionate tone to the end?

**Target Improvement:** 7/10 → 8+/10

---

#### 3. Technique Enthusiasm (Baseline: 8/10)
**Baseline Issues:**
- Energy: 3/5 (drops during redirections)
- Followability: 3/5 (timing makes redirections confusing)
- Timing: 3/5 (word timing problematic)

**Text:** "Honey, when you see that butter melting into those layers—oh!—and the steam just rising up—that smell!—you're gonna know you did it right! That's when you—wait, did I tell you about the cold butter? Sugar, that's the whole secret right there!"

**What to Check:**
- Are the redirections clearer?
- Does energy help followability?
- Is timing/pacing improved?

**Target Improvement:** 8/10 → 9/10

---

### 🟢 Low Priority (Already Good)

#### 4. Gumbo (Baseline: 10/10 Perfect)
**Purpose:** Verify we didn't make it worse

**What to Check:**
- Is it still as great as baseline?
- Does more variation enhance or detract?
- Any loss of perfection?

**Target:** Maintain 10/10

---

#### 5. Cornbread (Baseline: 9/10)
**Purpose:** Verify already-good phrases stay good

**Target:** Maintain 9/10 or improve to 10/10

---

## Evaluation Strategy

### Option 1: Full Evaluation
Run the complete evaluation for all 8 phrases:

```bash
./diagnostics/phase3_evaluate.sh passionate iteration_2_energy
```

**Pros:** Complete data for comparison
**Cons:** Takes longer (8 phrases × 6 criteria)

---

### Option 2: Targeted Comparison
Compare only the 3 problem phrases first:

```bash
# Listen to baseline vs iteration 2 for each problem phrase
# Then evaluate just those 3

# If problem phrases are improved, evaluate the rest
# If problem phrases are not improved, may need Iteration 3
```

**Pros:** Faster initial feedback
**Cons:** Incomplete data

---

## Success Criteria for Iteration 2

### Minimum Success
- ✅ Biscuits: 7/10 → 8/10 (energy improved)
- ✅ Collard Greens: 7/10 → 8/10 (energy maintained)
- ✅ Overall average: 8.5/10 → maintain or improve
- ✅ Energy score: 3.6/5 → 4.0/5
- ✅ No regression on Southern authenticity (5/5)

### Stretch Success
- ⭐ Overall average: 8.5/10 → 9.0/10
- ⭐ Energy score: 3.6/5 → 4.5/5
- ⭐ All phrases 8/10 or higher
- ⭐ At least 2 perfect 10/10 phrases

---

## If Iteration 2 Doesn't Improve Energy

### Potential Next Steps

**Option A: More Aggressive Energy Settings (Iteration 3)**
```python
"iteration_3_high_energy": {
    "stability": 0.25,        # Even lower
    "similarity_boost": 0.75,
    "style": 0.75,            # Even higher
    "use_speaker_boost": True
}
```

**Risk:** May sound unnatural or lose Southern authenticity

---

**Option B: Text Adjustments**
- Add more exclamation points
- Shorten sentences to prevent energy decay
- Add SSML breaks and emphasis tags

**Example:**
```
Oh! sugar! YES! <break time="200ms"/>
Okay, okay, buttermilk biscuits!
```

---

**Option C: Accept Current Performance**
- 8.5/10 already exceeds goal (7/10)
- Focus on other voice modes instead
- Come back to passionate mode later

---

## Quick Commands

```bash
# Play specific phrase comparison
afplay diagnostics/phase3_audio/passionate_iteration_1_baseline_biscuits.mp3
afplay diagnostics/phase3_audio/passionate_iteration_2_energy_biscuits.mp3

# Evaluate all Iteration 2 phrases
./diagnostics/phase3_evaluate.sh passionate iteration_2_energy

# View both iterations side-by-side
python diagnostics/phase3_voice_testing.py --mode passionate --show-results

# Rate a single phrase
python diagnostics/phase3_voice_testing.py \
  --mode passionate \
  --iteration iteration_2_energy \
  --phrase 1 \
  --rate 8 \
  --notes "Southern:5/5, Character:5/5, Energy:4/5, ..."
```

---

## Next Steps

1. **Listen to problem phrases** (biscuits, collard_greens) comparing baseline vs iteration 2
2. **Quick assessment:** Does energy sound better?
3. **If YES:** Run full evaluation and compare results
4. **If NO:** Consider iteration 3 or text adjustments
5. **Analyze results:** Document what worked and what didn't

---

**Ready to compare?** Start with biscuits and collard_greens to see if the energy tuning worked!
