require('dotenv').config({ override: true });
const axios = require('axios');
const OpenAI = require('openai');

const SERVER_URL = process.env.SERVER_URL || 'http://localhost:3000';

console.log('🧪 Voice Assistant Test Suite\n');
console.log('================================\n');

// Test 1: Check environment variables
function testEnvironmentVariables() {
  console.log('📋 Test 1: Environment Variables');
  console.log('─────────────────────────────────');

  const checks = {
    'OPENAI_API_KEY': process.env.OPENAI_API_KEY,
    'ELEVENLABS_API_KEY': process.env.ELEVENLABS_API_KEY,
    'ELEVENLABS_VOICE_ID': process.env.ELEVENLABS_VOICE_ID
  };

  let allPresent = true;
  for (const [key, value] of Object.entries(checks)) {
    const present = value && value !== `your_${key.toLowerCase()}_here`;
    console.log(`${present ? '✅' : '❌'} ${key}: ${present ? 'Set' : 'Missing or not configured'}`);
    if (!present) allPresent = false;
  }

  console.log();
  return allPresent;
}

// Test 2: Check OpenAI API
async function testOpenAI() {
  console.log('🤖 Test 2: OpenAI API Connection');
  console.log('─────────────────────────────────');

  try {
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a test assistant.' },
        { role: 'user', content: 'Say "test successful" in 3 words or less.' }
      ],
      max_tokens: 10
    });

    const response = completion.choices[0].message.content;
    console.log('✅ OpenAI API connection successful');
    console.log(`   Response: "${response}"\n`);
    return true;
  } catch (error) {
    console.log('❌ OpenAI API connection failed');
    console.log(`   Error: ${error.message}`);
    if (error.status) console.log(`   Status: ${error.status}`);
    console.log();
    return false;
  }
}

// Test 3: Check ElevenLabs API
async function testElevenLabs() {
  console.log('🎤 Test 3: ElevenLabs API Connection');
  console.log('─────────────────────────────────');

  try {
    const response = await axios.post(
      `https://api.elevenlabs.io/v1/text-to-speech/${process.env.ELEVENLABS_VOICE_ID}`,
      {
        text: 'Test',
        model_id: 'eleven_flash_v2_5',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75
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

    const audioSize = response.data.byteLength;
    console.log('✅ ElevenLabs API connection successful');
    console.log(`   Generated ${audioSize} bytes of audio\n`);
    return true;
  } catch (error) {
    console.log('❌ ElevenLabs API connection failed');
    console.log(`   Error: ${error.message}`);
    if (error.response) {
      console.log(`   Status: ${error.response.status}`);
      console.log(`   Data: ${JSON.stringify(error.response.data)}`);
    }
    console.log();
    return false;
  }
}

// Test 4: Check server connection
async function testServerConnection() {
  console.log('🌐 Test 4: Server Connection');
  console.log('─────────────────────────────────');

  try {
    const response = await axios.get(SERVER_URL, {
      timeout: 5000
    });
    console.log('✅ Server is running and accessible\n');
    return true;
  } catch (error) {
    console.log('❌ Cannot connect to server');
    console.log(`   Make sure the server is running with: npm start`);
    console.log(`   Error: ${error.message}\n`);
    return false;
  }
}

// Test 5: End-to-end test
async function testEndToEnd() {
  console.log('🎯 Test 5: End-to-End Chat Test');
  console.log('─────────────────────────────────');

  try {
    const response = await axios.post(
      `${SERVER_URL}/api/chat`,
      {
        text: 'Tell me about cornbread in one sentence.'
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000
      }
    );

    console.log('✅ End-to-end test successful');
    console.log(`   Response text: "${response.data.text}"`);
    console.log(`   Audio data: ${response.data.audio ? 'Present' : 'Missing'}`);
    console.log(`   Audio size: ${response.data.audio ? Buffer.from(response.data.audio, 'base64').length : 0} bytes\n`);
    return true;
  } catch (error) {
    console.log('❌ End-to-end test failed');
    console.log(`   Error: ${error.message}`);
    if (error.response) {
      console.log(`   Status: ${error.response.status}`);
      console.log(`   Data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    console.log();
    return false;
  }
}

// Run all tests
async function runTests() {
  const results = {
    env: false,
    openai: false,
    elevenlabs: false,
    server: false,
    endToEnd: false
  };

  // Test environment variables first
  results.env = testEnvironmentVariables();

  if (!results.env) {
    console.log('⚠️  Please configure your .env file before proceeding with API tests.\n');
    console.log('Copy .env.example to .env and add your API keys:\n');
    console.log('   cp .env.example .env');
    console.log('   # Then edit .env with your keys\n');
    return;
  }

  // Test OpenAI
  results.openai = await testOpenAI();

  // Test ElevenLabs
  results.elevenlabs = await testElevenLabs();

  // Test server (only if we can't connect, we'll skip end-to-end)
  results.server = await testServerConnection();

  // Test end-to-end only if server is running
  if (results.server) {
    results.endToEnd = await testEndToEnd();
  } else {
    console.log('⚠️  Skipping end-to-end test (server not running)\n');
  }

  // Summary
  console.log('================================');
  console.log('📊 Test Summary');
  console.log('================================');
  console.log(`Environment Variables: ${results.env ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`OpenAI API: ${results.openai ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`ElevenLabs API: ${results.elevenlabs ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Server Running: ${results.server ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`End-to-End: ${results.endToEnd ? '✅ PASS' : results.server ? '❌ FAIL' : '⏭️  SKIPPED'}`);
  console.log();

  const allPassed = results.env && results.openai && results.elevenlabs &&
                    (results.server ? results.endToEnd : true);

  if (allPassed) {
    console.log('🎉 All tests passed! Your voice assistant is ready to use.\n');
  } else {
    console.log('⚠️  Some tests failed. Please fix the issues above and try again.\n');
    process.exit(1);
  }
}

// Run the test suite
runTests().catch(error => {
  console.error('❌ Test suite crashed:', error);
  process.exit(1);
});
