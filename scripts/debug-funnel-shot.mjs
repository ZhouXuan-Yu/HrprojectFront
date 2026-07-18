// One-off debug screenshot straight to a stable folder.
import { chromium } from '@playwright/test';

const out = process.argv[2] || '.playwright-mcp/shots/debug.png';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.addInitScript(() => {
  localStorage.setItem('hr_role', 'admin');
  localStorage.setItem('hr_user', '测试用户');
});
page.on('console', (msg) => {
  const t = msg.text();
  if (t.includes('funnel-debug')) console.log('[console]', t);
});
page.on('pageerror', (err) => console.log('[pageerror]', err.message));
await page.goto('http://127.0.0.1:5173/recruit-dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
await page.locator('.funnel-hero-card').scrollIntoViewIfNeeded();
await page.waitForTimeout(1500);
await page.screenshot({ path: out, fullPage: false });
await browser.close();
console.log('saved', out);
