// Check environment BEFORE loading .env
const beforeDotenv = {
  openai: process.env.OPENAI_API_KEY,
  elevenlabs: process.env.ELEVENLABS_API_KEY
};

// Now load .env
require('dotenv').config();

const afterDotenv = {
  openai: process.env.OPENAI_API_KEY,
  elevenlabs: process.env.ELEVENLABS_API_KEY
};

console.log('🔍 Environment Variable Source Check\n');
console.log('================================\n');

console.log('📋 BEFORE loading .env file:');
console.log('─────────────────────────────────');
if (beforeDotenv.openai) {
  console.log(`⚠️  OPENAI_API_KEY already set in environment!`);
  console.log(`   Length: ${beforeDotenv.openai.length}`);
  console.log(`   First 10: ${beforeDotenv.openai.substring(0, 10)}`);
  console.log(`   Last 10: ${beforeDotenv.openai.substring(beforeDotenv.openai.length - 10)}`);
  console.log('   Source: Shell environment (NOT from .env file)');
} else {
  console.log('✅ OPENAI_API_KEY not set in environment');
}

if (beforeDotenv.elevenlabs) {
  console.log(`⚠️  ELEVENLABS_API_KEY already set in environment!`);
  console.log(`   Source: Shell environment (NOT from .env file)`);
} else {
  console.log('✅ ELEVENLABS_API_KEY not set in environment');
}

console.log('\n📋 AFTER loading .env file:');
console.log('─────────────────────────────────');
if (afterDotenv.openai) {
  console.log(`✅ OPENAI_API_KEY is set`);
  console.log(`   Length: ${afterDotenv.openai.length}`);
  console.log(`   First 10: ${afterDotenv.openai.substring(0, 10)}`);
  console.log(`   Last 10: ${afterDotenv.openai.substring(afterDotenv.openai.length - 10)}`);
} else {
  console.log('❌ OPENAI_API_KEY not set');
}

console.log('\n🔍 Diagnosis:');
console.log('─────────────────────────────────');
if (beforeDotenv.openai) {
  console.log('⚠️  Your OPENAI_API_KEY is coming from your shell environment,');
  console.log('   NOT from the .env file!');
  console.log('\n💡 To fix this:');
  console.log('   Option 1: Unset the environment variable:');
  console.log('      unset OPENAI_API_KEY');
  console.log('      unset ELEVENLABS_API_KEY');
  console.log('   \n   Option 2: Check your shell config files:');
  console.log('      ~/.bashrc or ~/.zshrc or ~/.profile');
  console.log('      Remove any OPENAI_API_KEY exports');
  console.log('   \n   Then restart your terminal or run: source ~/.bashrc');
} else if (afterDotenv.openai && afterDotenv.openai.includes('your_')) {
  console.log('⚠️  Your .env file has not been updated yet');
  console.log('   Please edit .env and replace the placeholder with your actual API key');
} else if (afterDotenv.openai) {
  console.log('✅ API key is correctly loaded from .env file');
} else {
  console.log('❌ No API key found in environment or .env file');
}

console.log('\n================================\n');
