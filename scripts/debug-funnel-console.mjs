// One-off debug: print all browser console messages from the funnel page.
import { chromium } from '@playwright/test';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.addInitScript(() => {
  localStorage.setItem('hr_role', 'admin');
  localStorage.setItem('hr_user', '测试用户');
});
page.on('console', (msg) => console.log('[console]', msg.type(), msg.text()));
page.on('pageerror', (err) => console.log('[pageerror]', err.message));
await page.goto('http://127.0.0.1:5173/recruit-dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(3000);
await browser.close();
