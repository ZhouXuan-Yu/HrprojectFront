// Quick screenshot straight to a stable folder. Usage: node scripts/shot.mjs <url-path> <out.png> [scrollSelector]
import { chromium } from '@playwright/test';

const urlPath = process.argv[2] || 'http://127.0.0.1:5173/recruit-dashboard';
const out = process.argv[3] || '.playwright-mcp/shots/shot.png';
const scrollSel = process.argv[4] || null;
const target = urlPath.startsWith('http') ? urlPath : 'http://127.0.0.1:5173' + urlPath;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.addInitScript(() => {
  localStorage.setItem('hr_role', 'admin');
  localStorage.setItem('hr_user', '测试用户');
});
page.on('pageerror', (err) => console.log('[pageerror]', err.message));
await page.goto(target, { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
if (scrollSel) {
  await page.locator(scrollSel).scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);
}
await page.screenshot({ path: out, fullPage: false });
await browser.close();
console.log('saved', out);
