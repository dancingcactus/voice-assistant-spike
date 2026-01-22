require('dotenv').config({ override: true });
const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3000;

// Validate environment variables on startup
function validateEnvironment() {
  const required = {
    'OPENAI_API_KEY': process.env.OPENAI_API_KEY,
    'ELEVENLABS_API_KEY': process.env.ELEVENLABS_API_KEY,
    'ELEVENLABS_VOICE_ID': process.env.ELEVENLABS_VOICE_ID
  };

  const missing = [];
  for (const [key, value] of Object.entries(required)) {
    if (!value || value.includes('your_') || value.includes('_here')) {
      missing.push(key);
    }
  }

  if (missing.length > 0) {
    console.error('❌ Missing or invalid environment variables:');
    missing.forEach(key => console.error(`   - ${key}`));
    console.error('\n💡 Please copy .env.example to .env and configure your API keys\n');
    process.exit(1);
  }

  console.log('✅ Environment variables validated');
}

validateEnvironment();

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

    const timings = {
      start: Date.now()
    };

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
    timings.openaiStart = Date.now();
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: DELILAH_SYSTEM_PROMPT },
        ...conversationHistory
      ],
      temperature: 0.8,
      max_tokens: 300
    });
    timings.openaiEnd = Date.now();
    timings.openaiDuration = timings.openaiEnd - timings.openaiStart;

    const responseText = completion.choices[0].message.content;
    console.log('Delilah says:', responseText);
    console.log(`⏱️  OpenAI took ${timings.openaiDuration}ms`);

    // Add assistant message to history
    conversationHistory.push({
      role: 'assistant',
      content: responseText
    });

    // Convert to speech using ElevenLabs
    timings.elevenlabsStart = Date.now();
    const audioResponse = await axios.post(
      `https://api.elevenlabs.io/v1/text-to-speech/${process.env.ELEVENLABS_VOICE_ID}`,
      {
        text: responseText,
        model_id: 'eleven_flash_v2_5',
        voice_settings: {
          stability: 0.3,
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
    timings.elevenlabsEnd = Date.now();
    timings.elevenlabsDuration = timings.elevenlabsEnd - timings.elevenlabsStart;
    timings.totalDuration = timings.elevenlabsEnd - timings.start;

    console.log(`⏱️  ElevenLabs took ${timings.elevenlabsDuration}ms`);
    console.log(`⏱️  Total processing time: ${timings.totalDuration}ms`);

    // Send back text, audio, and timings
    res.json({
      text: responseText,
      audio: Buffer.from(audioResponse.data).toString('base64'),
      timings: {
        openai: timings.openaiDuration,
        elevenlabs: timings.elevenlabsDuration,
        total: timings.totalDuration
      }
    });

  } catch (error) {
    console.error('❌ Error processing request:');

    // Detailed error logging
    if (error.response) {
      // API error (OpenAI or ElevenLabs)
      console.error('   API Error:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data
      });

      // Check if it's an authentication error
      if (error.response.status === 401) {
        console.error('   💡 Authentication failed - check your API keys in .env');
      }

      res.status(500).json({
        error: 'API request failed',
        details: error.response.data,
        status: error.response.status
      });
    } else if (error.request) {
      // Network error
      console.error('   Network Error:', error.message);
      console.error('   💡 Could not reach API - check your internet connection');

      res.status(500).json({
        error: 'Network error',
        details: 'Could not reach API service'
      });
    } else {
      // Other error
      console.error('   Error:', error.message);
      console.error('   Stack:', error.stack);

      res.status(500).json({
        error: 'Internal server error',
        details: error.message
      });
    }
  }
});

// Reset conversation history
app.post('/api/reset', (req, res) => {
  conversationHistory = [];
  res.json({ message: 'Conversation history reset' });
});

app.listen(port, () => {
  console.log('\n🎉 Voice Assistant Server Started');
  console.log('================================');
  console.log(`🌐 Server: http://localhost:${port}`);
  console.log(`🤖 Model: gpt-4o-mini (OpenAI)`);
  console.log(`🎤 Voice: Miss Sally May (ElevenLabs Flash v2.5)`);
  console.log(`👤 Character: Delilah Mae "Lila"`);
  console.log('================================');
  console.log('💡 Open http://localhost:' + port + ' in your browser to start\n');
});
