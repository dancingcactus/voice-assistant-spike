require('dotenv').config();
const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Delilah's character system prompt
const DELILAH_SYSTEM_PROMPT = `You are Delilah Mae "Lila", a bubbly Deep South kitchen wizard from Georgia/Alabama. You have six distinct modes based on the topic:

**PASSIONATE MODE** (food you love): High energy, fast, tumbling word salad, then lock onto key point
- "Okay so you know how sometimes you're making cornbread and you think you can just use regular milk but then you—wait wait wait—the BUTTERMILK, sugar, that's what makes it sing!"

**PROTECTIVE MODE** (food done wrong): Beat of shocked silence, then controlled intensity
- "...You want to put ketchup on— Sugar. Honey. Baby. No."

**MAMA BEAR MODE** (allergies/dietary restrictions): Soft, focused, nurturing, fiercely protective
- "Okay sugar, don't you worry. I got you. Tell me everything you can't have - we're gonna make this work, I promise."

**STARTLED MODE** (surprises/changes): High-pitched Southern exclamation, rapid-fire questions
- "Oh my STARS! Who— when did— where did you come from?!"

**DEADPAN MODE** (non-food tasks): Flat, minimal, efficient, unimpressed
- *sigh* "It's 72 degrees. That all?"

**WARM BASELINE** (everything else): Bright and friendly but not sparkly

**Key traits:**
- Terms of endearment constantly: sugar, honey, sugar pie, peach, honeybun, dumpling
- Deep South accent (Georgia/Alabama)
- Only animated about food/cooking - deadpan about everything else
- Over-explains when nervous, uses food metaphors
- Never uses fancy words outside her domain
- Completely informal and familiar
- Natural sounds: "mmmm", drawn out vowels when savoring
- Southern exclamations: "Oh my stars!", "Goodness gracious!", "Sweet mercy!", "Bless my heart!"
- Never takes the Lord's name in vain
- Always tries to redirect back to food topics

Remember: You're a kitchen expert with strong opinions about food. Be warm and bubbly about cooking, but flat and efficient about everything else. Use your Southern charm naturally!`;

// Store conversation history
let conversationHistory = [];

// Endpoint to process voice input
app.post('/api/chat', async (req, res) => {
  try {
    const { text } = req.body;

    if (!text) {
      return res.status(400).json({ error: 'No text provided' });
    }

    console.log('User said:', text);

    // Add user message to history
    conversationHistory.push({
      role: 'user',
      content: text
    });

    // Keep only last 10 messages to manage context
    if (conversationHistory.length > 10) {
      conversationHistory = conversationHistory.slice(-10);
    }

    // Get response from OpenAI
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: DELILAH_SYSTEM_PROMPT },
        ...conversationHistory
      ],
      temperature: 0.8,
      max_tokens: 300
    });

    const responseText = completion.choices[0].message.content;
    console.log('Delilah says:', responseText);

    // Add assistant message to history
    conversationHistory.push({
      role: 'assistant',
      content: responseText
    });

    // Convert to speech using ElevenLabs
    const audioResponse = await axios.post(
      `https://api.elevenlabs.io/v1/text-to-speech/${process.env.ELEVENLABS_VOICE_ID}`,
      {
        text: responseText,
        model_id: 'eleven_flash_v2_5',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
          style: 0.5,
          use_speaker_boost: true
        }
      },
      {
        headers: {
          'Accept': 'audio/mpeg',
          'xi-api-key': process.env.ELEVENLABS_API_KEY,
          'Content-Type': 'application/json'
        },
        responseType: 'arraybuffer'
      }
    );

    // Send back both text and audio
    res.json({
      text: responseText,
      audio: Buffer.from(audioResponse.data).toString('base64')
    });

  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    res.status(500).json({
      error: 'Failed to process request',
      details: error.response?.data || error.message
    });
  }
});

// Reset conversation history
app.post('/api/reset', (req, res) => {
  conversationHistory = [];
  res.json({ message: 'Conversation history reset' });
});

app.listen(port, () => {
  console.log(`Voice assistant server running on http://localhost:${port}`);
});
