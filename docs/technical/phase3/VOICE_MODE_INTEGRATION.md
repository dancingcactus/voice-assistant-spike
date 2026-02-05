# Voice Mode Integration Guide

**Phase 3 Complete** - All 6 voice modes integrated into production (9.72/10 avg quality)

---

## Overview

This guide explains how Phase 3 voice mode research is integrated into the Aperture Assist application. Delilah now has 6 distinct voice modes that automatically activate based on user input, providing superior voice quality (9.72/10 average) validated through extensive testing.

---

## How Voice Modes Work in the Application

### Architecture Flow

```
User Input
    ↓
CharacterSystem.select_voice_mode()
    ↓
System Prompt (with mode-specific instructions)
    ↓
LLM Generation (Claude generates response in character)
    ↓
TTS Generation (ElevenLabsTTS applies mode-specific settings)
    ↓
Audio Delivery (with mode metadata)
```

### Step-by-Step Example

**User says:** "I'm allergic to shellfish"

1. **Input Reception**
   - [ConversationManager.handle_user_message()](../../../backend/src/core/conversation_manager.py#L280) receives message
   - Session and user context loaded

2. **Mode Selection**
   - [CharacterSystem.select_voice_mode()](../../../backend/src/core/character_system.py#L56) called with message
   - High-priority keyword check: `'allerg'` found in input
   - Returns `VoiceModeSelection(mode=mama_bear, confidence=0.95, reasoning="Selected 'Mama Bear Mode' due to allergy/dietary concern")`

3. **System Prompt Construction**
   - [CharacterSystem.build_system_prompt()](../../../backend/src/core/character_system.py#L125) called with mama_bear mode
   - Includes mode-specific characteristics: "Soft, nurturing tone", "Hyper-focused on safety"
   - Example phrases provided: "Oh darlin', thank you for telling me about that allergy..."

4. **LLM Generation**
   - Claude generates response matching mama_bear characteristics
   - Response: "Oh darlin', thank you for telling me that. I'm gonna make absolutely sure everything I recommend is shellfish-free, okay? You're safe with me, sugar."

5. **TTS Generation**
   - [ElevenLabsTTS.generate_speech()](../../../backend/src/integrations/tts_integration.py#L176) called with `voice_mode="mama_bear"`
   - Applies Phase 3 settings: `stability=0.65, style=0.40`
   - Generates audio with 10.0/10 Phase 3 quality

6. **Audio Delivery**
   - Audio URL returned: `/audio/delilah_abc123.mp3`
   - Metadata includes: `voice_mode: "mama_bear"`
   - Client plays audio with soft, nurturing delivery

---

## Phase 3 Settings Reference

All settings validated through Phase 3 testing (February 2026).

| Mode | Stability | Style | Quality Score | Trigger Examples | Characteristics |
|------|-----------|-------|---------------|------------------|-----------------|
| **Warm Baseline** | 0.50 | 0.50 | **9.9/10** ⭐ | General conversation, "What should I make for dinner?" | Natural, conversational, friendly - default state |
| **Passionate** | 0.35 | 0.65 | **9.0/10** | Southern foods: biscuits, cornbread, gumbo, fried chicken | High energy, tumbling thoughts, animated |
| **Protective** | 0.55 | 0.45 | **9.8/10** | Microwaved steak, boiled chicken, instant grits | Controlled intensity, firm but caring |
| **Mama Bear** | 0.65 | 0.40 | **10.0/10** ⭐ | "I'm allergic to...", dietary restrictions | Soft, nurturing, protective, deliberate |
| **Startled** | 0.30 | 0.50 | **10.0/10** ⭐ | "Oh no!", unexpected events, surprises | High pitch, rapid questions, quick recovery |
| **Deadpan** | 0.65 | 0.35 | **9.6/10** | "Turn on lights", smart home commands | Flat, minimal, efficient, unimpressed |

**Phase 3 Average: 9.72/10**

**Common Settings (all modes):**
- `similarity_boost`: 0.75
- `use_speaker_boost`: True
- Voice: Miss Sally May (XHqlxleHbYnK8xmft8Vq)
- Model: eleven_flash_v2_5

---

## Testing Voice Modes

### Quick Test with Live Script

```bash
# 1. Start server with test API enabled
export ENABLE_TEST_API=true
python backend/src/main.py

# 2. In another terminal, test all modes
python diagnostics/test_voice_modes_live.py --mode all

# Or test specific mode:
python diagnostics/test_voice_modes_live.py --mode passionate

# Or test custom query:
python diagnostics/test_voice_modes_live.py --mode mama_bear --query "I'm allergic to peanuts"
```

**Output:**
```
==========================================================================
Testing PASSIONATE Mode (3 queries)
==========================================================================

======================================================================
Query: Tell me about cornbread
Expected Mode: passionate
Selected Mode: passionate mode
Match: ✅

Response (first 150 chars):
  Oh honey! Now you're talkin'! Real Southern cornbread—not that sweet stuff—no sir! You want that golden crust, that crumbly texture—mmm!...

Audio saved: diagnostics/phase3_audio/live_passionate_20260202_143022.mp3
Play with: afplay diagnostics/phase3_audio/live_passionate_20260202_143022.mp3

Expected characteristics: high energy, tumbling thoughts, animated
```

### Manual Testing via WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Send message
ws.send(JSON.stringify({
  type: 'user_message',
  userId: 'test_user',
  message: 'Tell me about cornbread',
  inputMode: 'voice'  // Enable TTS generation
}));

// Response includes:
// - text: LLM response
// - audio_url: Path to generated audio
// - metadata.voice_mode: "passionate mode"
```

### Verifying Mode Selection

**Check server logs:**
```
INFO - Selected voice mode: passionate mode (confidence: 0.80) - Selected 'Passionate Mode' due to keyword: 'cornbread'
INFO - Generating speech for delilah (mode: passionate mode, length: 147 chars)
INFO - Generated audio file: delilah_f7e8d9c2.mp3
```

**Check API response metadata:**
```json
{
  "text": "Oh honey! Now you're talkin'!...",
  "audio_url": "/audio/delilah_f7e8d9c2.mp3",
  "metadata": {
    "voice_mode": "passionate mode",
    "character_id": "delilah"
  }
}
```

---

## Mode Selection Logic

### Priority Levels

Mode selection uses a priority system:

**1. High-Priority Keywords (override everything)**
- **Mama Bear:** `allerg`, `dietary`, `restriction`, `cant eat`, `can't eat`, `health concern`
- **Startled:** `oh no`, `oh my`, `unexpected`, `surprise`, `suddenly`, `went wrong`

**2. Character-Defined Triggers**
- Loaded from [delilah.json](../../../story/characters/delilah.json)
- Trigger matching uses keyword detection

**3. Fallback**
- If no triggers match → **Warm Baseline** (default)

### Mode Selection Code

See [CharacterSystem.select_voice_mode()](../../../backend/src/core/character_system.py#L56):

```python
def select_voice_mode(
    self, character_id: str, user_input: str, context: Optional[Dict] = None
) -> Optional[VoiceModeSelection]:
    """Select appropriate voice mode based on user input."""

    # High-priority: Mama Bear (allergies/dietary)
    if any(kw in user_input.lower() for kw in ['allerg', 'dietary', ...]):
        return mama_bear_mode

    # High-priority: Startled (unexpected events)
    if any(kw in user_input.lower() for kw in ['oh no', 'oh my', ...]):
        return startled_mode

    # Character-defined triggers
    return character.find_matching_voice_mode(user_input)
```

---

## Troubleshooting

### Issue: Wrong Mode Selected

**Symptoms:**
- User says "Tell me about biscuits" but Warm Baseline selected
- Expected Passionate mode

**Diagnosis:**
1. Check server logs for mode selection reasoning
2. Verify trigger keywords in [delilah.json](../../../story/characters/delilah.json)
3. Check if high-priority keywords overriding

**Solution:**
- Add/adjust trigger keywords in character definition
- Ensure keyword matching is case-insensitive
- Consider adding query to TEST_QUERIES in test script

### Issue: No Audio Generated

**Symptoms:**
- Response received but `audio_url` is null
- Logs show "TTS generation returned no audio path"

**Diagnosis:**
1. Check `ELEVENLABS_API_KEY` environment variable
2. Check `ELEVENLABS_VOICE_ID` environment variable
3. Verify ElevenLabs API quota
4. Check `input_mode` parameter (must be "voice" for auto-TTS)

**Solution:**
```bash
# Verify environment variables
echo $ELEVENLABS_API_KEY
echo $ELEVENLABS_VOICE_ID

# Test TTS directly
curl -X POST http://localhost:8000/api/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "character_id": "delilah", "voice_mode": "warm_baseline"}'
```

### Issue: Audio Quality Doesn't Match Phase 3

**Symptoms:**
- Audio sounds different from Phase 3 test samples
- Mode characteristics not coming through

**Diagnosis:**
1. Verify TTS settings match Phase 3 values
2. Check if using correct voice ID (Miss Sally May)
3. Verify model is eleven_flash_v2_5

**Solution:**
1. Review [tts_integration.py](../../../backend/src/integrations/tts_integration.py#L90) settings
2. Compare with Phase 3 completion reports in [docs/milestones/](../../milestones/)
3. Regenerate audio and compare side-by-side

### Issue: Mode Selection Confidence Too Low

**Symptoms:**
- Logs show mode selected with low confidence (<0.6)
- Inconsistent mode selection for similar queries

**Solution:**
- Improve trigger keywords specificity
- Add more trigger examples to character definition
- Consider implementing fuzzy matching for keywords

---

## Customization Guide

### Adding a New Voice Mode

1. **Define Mode in Character JSON**

Edit [delilah.json](../../../story/characters/delilah.json):

```json
{
  "id": "new_mode",
  "name": "New Mode Name",
  "triggers": [
    "Trigger phrase 1",
    "Trigger phrase 2"
  ],
  "characteristics": [
    "Characteristic 1",
    "Characteristic 2"
  ],
  "example_phrases": [
    "Example response 1",
    "Example response 2"
  ],
  "response_style": "Description of how to respond"
}
```

2. **Add TTS Settings**

Edit [tts_integration.py](../../../backend/src/integrations/tts_integration.py#L90):

```python
"new_mode": {
    "stability": 0.50,  # Adjust based on desired energy
    "similarity_boost": 0.75,
    "style": 0.50,  # Adjust based on desired expressiveness
    "use_speaker_boost": True
}
```

3. **Add Test Queries**

Edit [test_voice_modes_live.py](../../../diagnostics/test_voice_modes_live.py):

```python
TEST_QUERIES = {
    "new_mode": [
        "Test query 1",
        "Test query 2"
    ]
}
```

4. **Test the New Mode**

```bash
python diagnostics/test_voice_modes_live.py --mode new_mode
```

5. **Iterate Using Phase 3 Methodology**

Follow the Phase 3 process:
- Generate test phrases
- Evaluate audio (1-5 scale on 6 criteria)
- Iterate settings if needed
- Document final settings and quality score

### Adjusting Existing Mode Settings

If mode quality needs improvement:

1. **Identify Issues**
   - Generate test audio: `python diagnostics/test_voice_modes_live.py --mode <mode>`
   - Listen for specific problems (too flat, too energetic, etc.)

2. **Adjust Settings**
   - **Too energetic/variable** → Increase stability (0.05 increments)
   - **Too flat/monotone** → Decrease stability, increase style
   - **Wrong emotional tone** → Adjust style parameter
   - **Character lost** → Check similarity_boost (should stay at 0.75)

3. **Test Changes**
   ```bash
   # Edit tts_integration.py
   # Restart server
   python diagnostics/test_voice_modes_live.py --mode <mode>
   ```

4. **Document Changes**
   - Update comments in tts_integration.py
   - Note iteration in character JSON
   - Update this guide if significant changes

### Adding High-Priority Keywords

To add triggers that override normal mode selection:

Edit [character_system.py](../../../backend/src/core/character_system.py#L80):

```python
# Example: Add "emergency" as high-priority for startled
startled_keywords = [
    'oh no', 'oh my', 'unexpected', 'surprise',
    'emergency', 'help', 'urgent'  # New additions
]
```

---

## Phase 3 Testing Methodology Reference

The Phase 3 testing process that validated these settings:

### Iteration Cycle (Per Mode)

1. **Define 8-10 Test Phrases** - Cover mode variations
2. **Generate Baseline Audio** - Apply initial TTS settings
3. **Evaluate** - Score on 6 criteria (1-5 scale each)
4. **Iterate** - Adjust settings if average < 9.0/10
5. **Document** - Create completion report

### Evaluation Criteria (Mode-Specific)

Each mode has 6 evaluation dimensions scored 1-5:

**Passionate:**
- Southern Authenticity
- Character Fit
- Energy Matching Mode
- Followability
- Speed
- Timing and Emphasis

**Mama Bear:**
- Softness
- Deliberate Pacing
- Reassurance
- Trust Building
- Non-Patronizing
- Character Fit

*(See individual milestone completion reports for all modes)*

### Tools Used

- [phase3_voice_testing.py](../../../diagnostics/phase3_voice_testing.py) - Audio generation
- [phase3_evaluate.sh](../../../diagnostics/phase3_evaluate.sh) - Interactive evaluation
- Test audio saved to: `diagnostics/phase3_audio/`

### Results Achieved

- **6 modes** completed in **6 days** (2.5x faster than planned)
- **9.72/10** average quality across all modes
- **5 of 6 modes** succeeded on first iteration
- **100% character consistency** across all modes

---

## Integration Points

### Backend Components

1. **[tts_integration.py](../../../backend/src/integrations/tts_integration.py)**
   - Lines 90-138: Phase 3 validated settings
   - `ElevenLabsTTS.generate_speech()` - Applies mode-specific settings

2. **[character_system.py](../../../backend/src/core/character_system.py)**
   - Lines 56-123: Mode selection logic
   - Lines 125-324: System prompt building with mode instructions

3. **[conversation_manager.py](../../../backend/src/core/conversation_manager.py)**
   - Lines 194-209: Mode selection during prompt building
   - Lines 300-306: Mode selection for TTS
   - Lines 548-569: TTS generation with mode

4. **[delilah.json](../../../story/characters/delilah.json)**
   - Lines 32-173: Complete voice mode definitions

### API Endpoints

1. **WebSocket: `/ws`**
   - Real-time conversation with auto mode selection
   - Set `inputMode: "voice"` to enable TTS

2. **POST `/api/test/conversation`**
   - Full conversation flow testing
   - Returns mode selection in metadata

3. **POST `/api/tts/generate`**
   - Manual TTS generation
   - Specify `voice_mode` parameter

---

## Next Steps

### Completed ✅
- Phase 3 settings integrated
- Live testing script created
- Documentation complete

### In Progress ⏳
- Mode transition testing (multi-turn conversations)
- Edge case validation
- Mode switching within conversation

### Planned 📋
- User feedback collection
- A/B testing vs baseline TTS
- Mode selection ML improvements
- Additional character voices (Hank, Rex, Dimitria)

---

## Additional Resources

### Phase 3 Documentation
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Complete Phase 3 execution
- [PRD.md](PRD.md) - Phase 3 requirements and success criteria
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Voice quality evaluation procedures

### Milestone Completion Reports
- [Milestone 1: Passionate](../../milestones/phase3_milestone1_passionate_complete.md) (9.0/10)
- [Milestone 2: Protective](../../milestones/phase3_milestone2_protective_complete.md) (9.8/10)
- [Milestone 3: Mama Bear](../../milestones/phase3_milestone3_mama_bear_complete.md) (10.0/10)
- [Milestone 4: Startled](../../milestones/phase3_milestone4_startled_complete.md) (10.0/10)
- [Milestone 5: Deadpan](../../milestones/phase3_milestone5_deadpan_complete.md) (9.6/10)
- [Milestone 6: Warm Baseline](../../milestones/phase3_milestone6_warm_baseline_complete.md) (9.9/10)

### Testing Tools
- [test_voice_modes_live.py](../../../diagnostics/test_voice_modes_live.py) - End-to-end testing
- [phase3_voice_testing.py](../../../diagnostics/phase3_voice_testing.py) - Phase 3 audio generation
- [phase3_evaluate.sh](../../../diagnostics/phase3_evaluate.sh) - Phase 3 evaluation script

---

**Questions or Issues?**

- Check troubleshooting section above
- Review Phase 3 completion reports for detailed analysis
- Test with live script to validate setup
- Consult character definition for trigger examples

**Delilah is ready to serve with her full emotional range!** 🎉
