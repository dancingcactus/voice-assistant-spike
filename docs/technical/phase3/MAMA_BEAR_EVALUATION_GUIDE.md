# Mama Bear Mode - Evaluation Guide

**Purpose:** Quick reference for evaluating Iteration 1 baseline audio samples

---

## Quick Start

### Play All Samples
```bash
# Play all Mama Bear iteration 1 samples in sequence
cd diagnostics/phase3_audio
for file in mama_bear_iteration_1_baseline_*.mp3; do
  echo "Playing: $file"
  afplay "$file"
  sleep 1
done
```

### Play Individual Samples
```bash
# Play specific phrase
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_celiac_disease.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_shellfish_allergy.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_nut_allergy_severe.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_dairy_intolerance.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_multiple_allergies.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_child_with_allergies.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_religious_restriction_kosher.mp3
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_medical_restriction_diabetes.mp3
```

---

## Evaluation Criteria (Rate 1-5 for each)

### 1. Softness (Soft)
- **5/5:** Noticeably gentler than Protective mode, tender but not weak
- **4/5:** Soft with minor lapses in consistency
- **3/5:** Somewhat soft but not distinct from other modes
- **2/5:** Not noticeably softer than Protective
- **1/5:** Same or harsher than Protective mode

**Key Question:** Would someone with severe allergies feel *emotionally* safe?

---

### 2. Deliberate Pacing (Pacing)
- **5/5:** Slower, measured, intentional without being patronizing
- **4/5:** Generally slower with good pacing
- **3/5:** Some slower delivery but inconsistent
- **2/5:** Not noticeably slower than baseline
- **1/5:** Same speed as other modes or feels rushed

**Key Question:** Does the pacing feel protective and thoughtful?

---

### 3. Reassurance Quality (Reassurance)
- **5/5:** "You're safe with me" sounds completely genuine and trustworthy
- **4/5:** Reassurance present and mostly believable
- **3/5:** Reassurance stated but not fully convincing
- **2/5:** Reassurance feels perfunctory or scripted
- **1/5:** No reassurance or sounds insincere

**Key Question:** Do you *believe* Delilah when she says you're safe?

---

### 4. Trust Building (Trust)
- **5/5:** Would trust this voice with life-threatening allergy info
- **4/5:** Trustworthy with minor reservations
- **3/5:** Somewhat trustworthy but not fully confident
- **2/5:** Wouldn't fully trust with serious information
- **1/5:** Would not trust with dietary restrictions

**Key Question:** Would you tell this voice about your child's peanut allergy?

---

### 5. Non-Patronizing (NonPatronizing)
- **5/5:** Respects intelligence, treats restriction with appropriate gravity
- **4/5:** Mostly respectful with minor awkward moments
- **3/5:** Sometimes feels like talking down
- **2/5:** Noticeably patronizing at points
- **1/5:** Condescending or dismissive tone

**Key Question:** Does this treat you like a competent adult who needs support?

---

### 6. Character Fit (Character)
- **5/5:** Unmistakably Delilah, Southern warmth maintained, distinct from other modes
- **4/5:** Recognizable as Delilah with minor character slips
- **3/5:** Somewhat recognizable but character unclear
- **2/5:** Doesn't sound like Delilah
- **1/5:** Generic voice, no character

**Key Question:** Is this still Delilah, just in her most protective mode?

---

## Rating Scale Conversion

Each phrase gets 6 ratings (1-5 each) = 30 points possible

**Convert to /10 scale:**
- Sum of 6 ratings ÷ 3 = Rating out of 10
- Example: 5+5+4+5+4+5 = 28/30 → 28÷3 = 9.3/10

**Target:** 8/10 or higher average (24/30 or higher per phrase)

---

## Comparison Listening

### Compare with Protective Mode
Listen to these pairs to feel the difference:

**Protective (Microwaved Steak):**
```bash
afplay diagnostics/phase3_audio/protective_iteration_2_pattern_microwaved_steak.mp3
```

**Mama Bear (Celiac Disease):**
```bash
afplay diagnostics/phase3_audio/mama_bear_iteration_1_baseline_celiac_disease.mp3
```

**What to listen for:**
- Is Mama Bear noticeably softer?
- Is pacing more deliberate?
- Does Mama Bear feel more protective vs. corrective?

---

## Recording Ratings

### Using the Python Script
```bash
# Rate a phrase (1-10 scale)
python diagnostics/phase3_voice_testing.py --mode mama_bear --iteration iteration_1_baseline --phrase 1 --rate 9 --notes "Soft:5/5, Pacing:5/5, Reassurance:4/5, Trust:5/5, NonPatronizing:4/5, Character:5/5"

# View results
python diagnostics/phase3_voice_testing.py --mode mama_bear --show-results
```

### Note Template
```
Soft:_/5, Pacing:_/5, Reassurance:_/5, Trust:_/5, NonPatronizing:_/5, Character:_/5 | [Additional notes]
```

---

## What to Look For

### Success Indicators
- ✅ Voice sounds genuinely caring, not performative
- ✅ "I've got you" makes you feel protected
- ✅ Repeated reassurance doesn't feel repetitive
- ✅ Would trust this voice with serious medical info
- ✅ Southern warmth maintained throughout
- ✅ Distinct from Protective mode (softer, not corrective)

### Warning Signs
- ⚠️ Sounds patronizing or condescending
- ⚠️ "You're safe" sounds scripted or insincere
- ⚠️ Too slow (makes you impatient)
- ⚠️ Not noticeably different from Protective mode
- ⚠️ Doesn't sound like Delilah anymore
- ⚠️ Feels weak rather than gentle

---

## The Ultimate Test

**Imagine this scenario:**

You have a 3-year-old with a severe peanut allergy. You're trying a new recipe and need to make absolutely sure it's safe. Would you trust Delilah in Mama Bear mode with this question?

If the answer is **"Yes, completely"** → Success ✅
If the answer is **"Maybe..."** → Needs work ⚠️
If the answer is **"No"** → Major issues ❌

---

## Post-Evaluation

After rating all 8 phrases:

1. **Calculate average rating** (should be 8/10 or higher)
2. **Identify patterns** in high vs. low scorers
3. **Document findings** in ITERATION1_MAMA_BEAR_ANALYSIS.md
4. **Plan Iteration 2** (TTS adjustments and/or text changes)

---

## TTS Setting Hypotheses

**Current Settings:** Stability 0.65, Style 0.40, Similarity 0.75

**If too flat/monotone:**
- Lower stability to 0.60
- Increase style to 0.45

**If not soft enough:**
- Increase stability to 0.70
- Lower style to 0.35

**If patronizing:**
- Text changes (not TTS)
- Remove excessive "don't worry"
- Strengthen competence language

---

## Next Steps After Evaluation

### If Average ≥ 9/10
- ✅ Settings are excellent
- Move to Milestone 4 (Startled mode)
- Document learnings

### If Average 8-9/10
- Iterate once more with minor adjustments
- Focus on specific criteria that scored lower

### If Average < 8/10
- Significant rework needed
- Consider both TTS and text changes
- May need 2-3 iterations

---

**Ready to evaluate?** Start with phrase 1 and work through systematically! 🎧
