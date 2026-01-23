// Test override functionality

console.log('🔍 Testing .env Override Functionality\n');
console.log('================================\n');

const shellEnv = process.env.OPENAI_API_KEY;
console.log('📋 Shell Environment (before dotenv):');
console.log('─────────────────────────────────');
if (shellEnv) {
  console.log(`✅ OPENAI_API_KEY set in shell`);
  console.log(`   Length: ${shellEnv.length}`);
  console.log(`   Last 10 chars: ${shellEnv.substring(shellEnv.length - 10)}`);
} else {
  console.log('❌ OPENAI_API_KEY not set in shell');
}

// Load .env with override
require('dotenv').config({ override: true });

const afterOverride = process.env.OPENAI_API_KEY;
console.log('\n📋 After .env Override:');
console.log('─────────────────────────────────');
if (afterOverride) {
  console.log(`✅ OPENAI_API_KEY is now set`);
  console.log(`   Length: ${afterOverride.length}`);
  console.log(`   Last 10 chars: ${afterOverride.substring(afterOverride.length - 10)}`);

  if (shellEnv && afterOverride !== shellEnv) {
    console.log('\n✅ SUCCESS: .env file overrode shell environment!');
    console.log('   The key from .env is now active.');
  } else if (shellEnv && afterOverride === shellEnv) {
    console.log('\n⚠️  .env file has same value as shell environment');
    console.log('   Or .env file is not configured yet.');
  } else {
    console.log('\n✅ Using .env file (no shell environment conflict)');
  }
} else {
  console.log('❌ OPENAI_API_KEY still not set');
}

console.log('\n================================\n');
console.log('💡 Next steps:');
console.log('1. Edit /home/user/voice-assistant-spike/.env');
console.log('2. Set your API keys (they will override shell environment)');
console.log('3. Run: npm test');
console.log('\n================================\n');
