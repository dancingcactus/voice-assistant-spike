const { chromium } = require('playwright');

const url = process.env.PLAYWRIGHT_URL || 'http://localhost:5173';
const screenshotPath = 'tool_logs/chat_screenshot.png';

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const maxAttempts = 60;
  let loaded = false;
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 5000 });
      if (resp && (resp.status() === 200 || resp.status() === 304)) {
        loaded = true;
        break;
      }
    } catch (e) {
      // ignore and retry
    }
    await sleep(1000);
  }

  if (!loaded) {
    console.error('Timed out waiting for', url);
    await browser.close();
    process.exit(2);
  }

  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log('Saved screenshot to', screenshotPath);
  await browser.close();
})();
