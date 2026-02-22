# Voice Assistant Prototype - Delilah

A simple web-based voice assistant prototype for testing the Delilah character personality. This prototype allows you to speak to Delilah and hear her responses using ElevenLabs TTS and OpenAI for natural language processing.

## Features

- **Push-to-Talk Interface**: Hold down a button to speak
- **Real-time Speech Recognition**: Uses browser's Web Speech API
- **Character-Driven Responses**: Delilah responds with her distinct Southern personality
- **High-Quality Voice**: ElevenLabs Flash v2.5 with Miss Sally May voice
- **Conversation History**: Maintains context across multiple interactions
- **Clean UI**: Simple, intuitive interface for testing

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Modern web browser (Chrome or Edge recommended for speech recognition)
- OpenAI API key
- ElevenLabs API key

## Setup

### 1. Install Dependencies

```bash
# Frontend
cd frontend && npm install

# Backend (Python)
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

#### Get OpenAI API Key

1. Go to <https://platform.openai.com/api-keys>
2. Create a new API key
3. Copy it to `OPENAI_API_KEY` in your `.env` file

#### Get ElevenLabs API Key

1. Go to <https://elevenlabs.io/app/settings/api-keys>
2. Create a new API key
3. Copy it to `ELEVENLABS_API_KEY` in your `.env` file

#### Voice ID (Already Configured)

The Miss Sally May voice ID is already set in `.env.example`:

- `ELEVENLABS_VOICE_ID=XHqlxleHbYnK8xmft8Vq`

Your `.env` file should look like:

```
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=XHqlxleHbYnK8xmft8Vq
PORT=3000
```

### 3. Start the Servers

Start the backend API (includes observability endpoints):

```bash
cd backend
source .venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000
```

Start the frontend (app + observability dashboard):

```bash
cd frontend
npm run dev
```

The frontend dev server runs at the URL shown by Vite (typically <http://localhost:5173>) and serves the observability UI at `/observability` on that host.

## Running the Backend, Observability, and Frontend

### Backend API (includes observability endpoints)

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000
```

### Frontend (app + observability dashboard)

```bash
cd frontend
npm run dev
```

Open:

-- The URL printed by `npm run dev` (Vite) — typically `http://localhost:5173/`
-- Observability: append `/observability` to that URL (e.g. `http://localhost:5173/observability`)

You can also use the included convenience script to start/stop both servers:

```bash
# From the repository root
chmod +x scripts/servers.sh
./scripts/servers.sh start    # start backend + frontend (backgrounded)
./scripts/servers.sh status   # show status of started processes
./scripts/servers.sh stop     # stop the servers
```

Logs and pidfile are written to `.tool_logs/` by the script:

- `.tool_logs/backend.log` — backend stdout/stderr
- `.tool_logs/frontend.log` — frontend stdout/stderr
- `.tool_logs/server_pids` — PIDs recorded when servers are started

Notes:

- The script will create a Python virtual environment at `backend/.venv` if one is missing and will try to install the backend requirements before starting the backend process.
- It backgrounds both processes using `nohup` and records their PIDs in `.tool_logs/server_pids` so `./scripts/servers.sh stop` can terminate them.
- Make the script executable with `chmod +x scripts/servers.sh`.

## Testing Your Setup

Before using the voice interface, run the test suite to ensure everything is configured correctly:

```bash
npm test
```

This will check:

- ✅ Environment variables are set
- ✅ OpenAI API connection works
- ✅ ElevenLabs API connection works
- ✅ Server is running
- ✅ End-to-end chat flow works

If any test fails, it will show you exactly what's wrong and how to fix it.

**Common issues:**

- **401 errors**: Check your API keys are correct in `.env`
- **Voice ID errors**: Verify `ELEVENLABS_VOICE_ID=XHqlxleHbYnK8xmft8Vq`
- **Network errors**: Check your internet connection

## Usage

1. Open your browser and navigate to the URL shown by Vite (commonly `http://localhost:5173`)
2. Press and hold the "Hold to Talk" button
3. Speak your message (ask about cooking, recipes, or anything else!)
4. Release the button when you're done speaking
5. Wait for Delilah to respond - you'll hear her voice!

## Tips for Testing Delilah's Personality

Try these types of questions to see her different modes in action:

### Passionate Mode (food topics)

- "How do I make cornbread?"
- "What's the secret to good brisket?"
- "Tell me about buttermilk biscuits"

### Protective Mode (food done wrong)

- "I'm going to put ketchup on my steak"
- "Can I microwave this?"
- "I'll just use margarine instead of butter"

### Mama Bear Mode (dietary restrictions)

- "I'm allergic to dairy"
- "I have celiac disease"
- "I can't eat nuts"

### Deadpan Mode (non-food tasks)

- "What's the temperature?"
- "Turn on the lights"
- "What time is it?"

## Project Structure

```
voice-assistant-spike/
├── backend/            # Python FastAPI backend
│   ├── src/           # Source code (core, integrations, tools, models, api)
│   └── requirements.txt
├── frontend/          # React + TypeScript frontend
│   └── src/           # Components, services, types
├── docs/              # Documentation
│   ├── narrative/     # Character guides and story chapters
│   ├── technical/     # Architecture and planning docs
│   │   └── phase1/    # Phase 1 specific documentation
│   └── testing/       # Testing documentation
│       ├── manual/    # Manual testing guides and quick commands
│       ├── phase4/    # Phase 4 (Tool System) testing
│       ├── phase5/    # Phase 5 (Story Engine) testing
│       └── phase7/    # Phase 7 (Memory & State) testing
├── story/             # Story content (characters, beats, chapters)
├── diagnostics/       # Debug and demo scripts
├── tests/             # Automated test scenarios
├── data/              # Runtime data (gitignored)
├── shared/            # Shared schemas
├── CLAUDE.md          # Project vision and architecture
└── README.md          # This file
```

## Documentation Guide

- **Getting Started**: Read [docs/technical/phase1/PROJECT_PLAN_PHASE1.md](docs/technical/phase1/PROJECT_PLAN_PHASE1.md) for the development roadmap
- **Manual Testing**: Start with [docs/testing/manual/START_HERE.md](docs/testing/manual/START_HERE.md)
- **Quick Commands**: See [docs/testing/manual/QUICK_TEST_COMMANDS.md](docs/testing/manual/QUICK_TEST_COMMANDS.md)
- **Character Guides**: Find all character documentation in [docs/narrative/](docs/narrative/)
- **Architecture**: Review [docs/technical/phase1/ARCHITECTURE.md](docs/technical/phase1/ARCHITECTURE.md)

## Technical Details

### Backend (server.js)

- **Framework**: Express.js
- **LLM**: OpenAI GPT-4o-mini (cost-effective for testing)
- **TTS**: ElevenLabs Flash v2.5 model
- **Voice**: Miss Sally May (Southern accent)
- **Context Management**: Keeps last 10 messages for conversation continuity

### Frontend (public/index.html)

- **Speech Recognition**: Web Speech API (Chrome/Edge)
- **Audio Playback**: Native HTML5 Audio
- **UI**: Vanilla JavaScript with responsive design
- **Interaction**: Push-to-talk button with visual feedback

### Character System Prompt

The system prompt in `server.js` includes:

- Six distinct personality modes (Passionate, Protective, Mama Bear, Startled, Deadpan, Warm Baseline)
- Southern dialect markers
- Key phrases and mannerisms
- Food-centric behavior patterns

## Troubleshooting

### Speech Recognition Not Working

- Make sure you're using Chrome or Edge browser
- Check that microphone permissions are granted
- Try using HTTPS (localhost should work with HTTP)

### No Audio Playback

- Check browser console for errors
- Verify ElevenLabs API key and voice ID are correct
- Check your audio output settings

### API Errors

- Verify all API keys are correctly set in `.env`
- Check API key permissions and quotas
- Review server console logs for detailed error messages

### Slow Responses

- This is expected - we're prioritizing quality over speed
- Typical flow: Speech recognition → OpenAI → ElevenLabs → Audio playback
- Each step adds latency but provides better testing experience

## Next Steps

This prototype is designed for iterating on Delilah's personality. Once you're happy with her voice and responses, you can:

1. Test different ElevenLabs voices
2. Adjust the system prompt for better character consistency
3. Tune voice settings (stability, similarity, style)
4. Add more personality modes or refine existing ones
5. Experiment with different OpenAI models
6. Add visual feedback for different modes

## Cost Considerations

- **OpenAI**: Using GPT-4o-mini (~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
- **ElevenLabs**: Flash v2.5 is their most cost-effective model while maintaining quality
- Keep an eye on usage if testing extensively

## Contributing

This is a personal prototype, but feel free to fork and modify for your own character testing!

## License

MIT
