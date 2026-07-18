// One-off visual check for the Three.js funnel hero — not a test file.
// Requires dev server already running on 127.0.0.1:5173.
import { chromium, devices } from '@playwright/test';

const consoleErrors = [];

try {
  const browser = await chromium.launch();
  const initAuth = () => {
    localStorage.setItem('hr_role', 'admin');
    localStorage.setItem('hr_user', '测试用户');
  };

  // Desktop
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.addInitScript(initAuth);
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push('[desktop] ' + msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push('[desktop-pageerror] ' + err.message));
  await page.goto('http://127.0.0.1:5173/recruit-dashboard', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500); // allow reveal + a few seconds of animation
  await page.locator('.funnel-hero-card').scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'test-results/funnel-three-desktop.png', fullPage: false });
  await page.close();

  // Mobile (real device emulation so layout matches a phone)
  const mctx = await browser.newContext({ ...devices['iPhone 12'] });
  const mpage = await mctx.newPage();
  mpage.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push('[mobile] ' + msg.text());
  });
  mpage.on('pageerror', (err) => consoleErrors.push('[mobile-pageerror] ' + err.message));
  await mpage.addInitScript(initAuth);
  await mpage.goto('http://127.0.0.1:5173/recruit-dashboard', { waitUntil: 'networkidle' });
  await mpage.waitForTimeout(2000);
  await mpage.locator('.funnel-hero-card').scrollIntoViewIfNeeded();
  await mpage.waitForTimeout(3000); // let the staggered reveal finish
  // avoid sticky topbar being stitched repeatedly into the element screenshot
  await mpage.addStyleTag({ content: '.topbar{position:static!important}' });
  await mpage.locator('.funnel-hero-card').screenshot({ path: 'test-results/funnel-three-mobile.png' });
  await mpage.close();
  await mctx.close();

  await browser.close();
} finally {
}

if (consoleErrors.length) {
  console.log('CONSOLE ERRORS:');
  consoleErrors.forEach((e) => console.log('  ' + e));
  process.exit(1);
} else {
  console.log('Screenshots saved, no console errors.');
}
