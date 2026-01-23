require('dotenv').config({ override: true });

console.log('🔍 Detailed API Key Diagnostic\n');
console.log('================================\n');

const openaiKey = process.env.OPENAI_API_KEY;

if (!openaiKey) {
  console.log('❌ No OPENAI_API_KEY found');
} else {
  console.log('📋 Raw Key Analysis:');
  console.log('─────────────────────────────────');
  console.log(`Length: ${openaiKey.length} characters`);
  console.log(`First 10 chars: ${openaiKey.substring(0, 10)}`);
  console.log(`Last 10 chars: ${openaiKey.substring(openaiKey.length - 10)}`);

  console.log('\n🔬 Character-by-Character (last 20):');
  console.log('─────────────────────────────────');
  const last20 = openaiKey.substring(openaiKey.length - 20);
  for (let i = 0; i < last20.length; i++) {
    const char = last20[i];
    const code = char.charCodeAt(0);
    let display;

    if (code === 10) display = '\\n (newline)';
    else if (code === 13) display = '\\r (carriage return)';
    else if (code === 32) display = '(space)';
    else if (code === 9) display = '\\t (tab)';
    else display = char;

    console.log(`  [${i}] code ${code}: ${display}`);
  }

  console.log('\n🔍 Hidden Character Check:');
  console.log('─────────────────────────────────');

  // Check for newlines
  if (openaiKey.includes('\n')) {
    console.log('⚠️  Found newline character (\\n)');
  }

  // Check for carriage returns
  if (openaiKey.includes('\r')) {
    console.log('⚠️  Found carriage return (\\r)');
  }

  // Check for tabs
  if (openaiKey.includes('\t')) {
    console.log('⚠️  Found tab character (\\t)');
  }

  // Check for leading/trailing spaces
  if (openaiKey !== openaiKey.trim()) {
    console.log('⚠️  Found leading or trailing whitespace');
    console.log(`   Trimmed length would be: ${openaiKey.trim().length}`);
  }

  console.log('\n💡 To fix:');
  console.log('─────────────────────────────────');
  console.log('1. Open your .env file');
  console.log('2. Make sure the line looks EXACTLY like this:');
  console.log('   OPENAI_API_KEY=sk-proj-yourkey');
  console.log('3. No quotes, no spaces, no extra lines');
  console.log('4. Make sure there is NO newline or space at the end');
  console.log('5. Save and try again\n');
}

console.log('================================\n');
