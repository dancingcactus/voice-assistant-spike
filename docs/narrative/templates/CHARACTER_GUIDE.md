# Character Voice Guide Framework

This guide helps define distinctive voices for AI agents, covering both speech patterns (for LLM prompts) and vocal qualities (for TTS selection).

---

## 1. Core Voice Profile

**Pitch & Tone**

- Natural pitch range (high/mid/low)
- Energy level (subdued, moderate, high)
- Warmth vs. clinical

**Pacing & Rhythm**

- Speech speed (deliberate, conversational, rapid)
- Pause patterns (frequent breaks, run-on, dramatic pauses)
- Sentence length preference

**Vocal Texture**

- Smooth vs. gravelly vs. crisp
- Breath patterns (audible sighs, steady)
- Vocal fry, upspeak, or other qualities

---

## 2. Speech Patterns

**Sentence Structure**

- Simple vs. complex
- Fragments, complete sentences, or run-ons
- Active vs. passive voice preference

**Word Choice & Vocabulary**

- Technical jargon vs. plain language
- Formal vs. casual register
- Favorite words or phrases
- Words they'd never use

**Conversational Style**

- Direct vs. meandering
- Confident vs. tentative
- Didactic vs. collaborative

---

## 3. Signature Quirks

**Verbal Tics**

- Filler words ("uh", "well", "you know")
- Repeated phrases ("thing is...", "listen up")
- Catchphrases

**Emotional Tells**

- How excitement sounds
- How concern manifests
- How frustration leaks through
- How pride shows up

**Interjections & Reactions**

- Surprise ("Oh!", "Wait what?", "Huh.")
- Agreement ("Exactly", "Right", "Mm-hmm")
- Disagreement ("Actually...", "Hold on", "Ehh")

---

## 4. Example Scenarios

For each character, write how they'd handle:

- **Simple factual query**: "What's the temperature?"
- **Complex request**: "I want the house cozy but not hot"
- **Emotional moment**: Celebrating a milestone or expressing concern
- **Disagreement**: Pushing back on another agent or the user
- **Small talk**: Starting or filling conversation

---

# Character Template

```
CHARACTER NAME


VOICE ESSENCE
A one-line capturing their vocal vibe

CORE PROFILE
- Pitch: [High/Mid/Low with specifics]
- Energy: [Description]
- Pace: [Fast/Medium/Slow with pattern notes]
- Texture: [Quality descriptors]
- Warmth: [1-10 scale with notes]

SPEECH MECHANICS
- Sentence structure: [Pattern]
- Vocabulary level: [Technical/Mixed/Plain]
- Formality: [Scale/context notes]
- Directness: [How they get to the point]

SIGNATURE SOUNDS
- Opening phrases: ["Well," "Listen," "So here's the thing"]
- Transitions: ["But actually," "Plus," "Meanwhile"]
- Emphasis: [How they stress important points]
- Reactions: [Surprise/pleasure/concern sounds]
- Closing: [How they end thoughts]

EMOTIONAL EXPRESSION
- Excitement: [How it manifests in speech]
- Concern: [Vocal tells]
- Frustration: [How it leaks through]
- Pride/satisfaction: [Expression style]
- Uncertainty: [How they handle not knowing]

RELATIONSHIP-SPECIFIC QUIRKS
- With user: [Tone/approach]
- With other agents: [How it shifts]
- When interrupted: [Reaction style]

EXAMPLES
"Temperature is 72 degrees"
* [How they'd actually say it]

"Make it cozy"
* [Their interpretation and response]

"That's not going to work"
* [How they'd push back]

Coffee break chat
* [Small talk sample]

NEVER WOULD
- [Things they'd never say]
- [Phrases that break character]
- [Tones/styles to avoid]

TTS GUIDANCE
- Reference voices: [Similar real voices]
- Piper model targets: [If applicable]
- ElevenLabs settings: [If you go that route]
```

---

## Implementation Tips

### For LLM Prompts

- Include the "Speech Mechanics" and "Signature Sounds" sections
- Add 2-3 example exchanges showing voice in action
- Include the "Never Would" list to prevent drift

### For TTS Selection

- Use "Core Profile" and "Vocal Texture" to audition voices
- Test each voice with your example scenarios
- Record samples for reference

### For Testing Consistency

- Give multiple LLM calls the same scenario
- Check if the verbal quirks appear naturally
- Verify the voice stays consistent under stress/error conditions

---

## Usage Notes

**Voice vs. Personality**: This guide focuses on *how* characters speak, not *what* they believe or value. Combine with a personality/expertise guide for complete character definition.

**Consistency Keys**: The "Signature Sounds" and "Never Would" sections are most important for maintaining consistent character voice across conversations.

**TTS Constraints**: Real TTS systems have limited emotional range. Focus verbal quirks on word choice and pacing rather than subtle vocal inflections that TTS can't reproduce.

**Testing**: Generate 10+ responses to the same prompt and look for patterns. If quirks only appear 30% of the time, make them more prominent in the prompt.
