require('dotenv').config();

console.log('🔍 API Key Diagnostic Tool\n');
console.log('================================\n');

// Check OpenAI key format
const openaiKey = process.env.OPENAI_API_KEY;

console.log('📋 OpenAI API Key Check:');
console.log('─────────────────────────────────');

if (!openaiKey) {
  console.log('❌ No OPENAI_API_KEY found in .env file');
} else {
  // Check for common formatting issues
  const issues = [];

  // Check for quotes
  if (openaiKey.startsWith('"') || openaiKey.startsWith("'")) {
    issues.push('Key has quotes around it - remove quotes');
  }

  // Check for spaces
  if (openaiKey.trim() !== openaiKey) {
    issues.push('Key has leading or trailing spaces - remove them');
  }

  // Check prefix
  if (!openaiKey.startsWith('sk-')) {
    issues.push('Key should start with "sk-"');
  }

  // Check length (OpenAI keys are typically 51+ characters)
  if (openaiKey.length < 40) {
    issues.push('Key seems too short - may be incomplete');
  }

  // Show results
  console.log(`Length: ${openaiKey.length} characters`);
  console.log(`Starts with: ${openaiKey.substring(0, 7)}...`);
  console.log(`Ends with: ...${openaiKey.substring(openaiKey.length - 4)}`);

  if (issues.length > 0) {
    console.log('\n⚠️  Issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
  } else {
    console.log('✅ Format looks correct');
  }

  // Show the exact line from .env (useful for spotting invisible characters)
  console.log('\n📄 Your .env line should look exactly like this:');
  console.log('   OPENAI_API_KEY=sk-proj-...');
  console.log('   (no quotes, no spaces before/after =)');
}

console.log('\n================================');
console.log('💡 Common 401 Error Causes:\n');
console.log('1. Key copied with quotes: Remove any " or \' characters');
console.log('2. Extra spaces: Make sure there are no spaces around the key');
console.log('3. Incomplete key: Make sure you copied the entire key');
console.log('4. Old key format: Try creating a new API key');
console.log('5. Project key vs Account key: Some keys are project-specific');
console.log('6. Billing not set up: Check https://platform.openai.com/settings/organization/billing');
console.log('\n================================\n');
