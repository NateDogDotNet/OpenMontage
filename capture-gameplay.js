// Playwright script to capture Arrow Puzzle gameplay footage
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ASSETS = '/app/projects/arrow-puzzle-showcase/assets';
fs.mkdirSync(`${ASSETS}/images`, { recursive: true });
fs.mkdirSync(`${ASSETS}/video`, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    recordVideo: { dir: `${ASSETS}/video`, size: { width: 780, height: 1688 } }
  });
  const page = await context.newPage();

  await page.goto(`file:///app/arrow-puzzle-PWA/index.html`);
  await page.waitForTimeout(2000);

  // Screenshot: Home screen with animated arrows
  await page.screenshot({ path: `${ASSETS}/images/01-home.png` });
  console.log('Captured: home screen');

  // Click Play — starts level 1 directly
  await page.click('text=Play');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${ASSETS}/images/02-level1-start.png` });
  console.log('Captured: level 1 start');

  // Play through level 1 by clicking escapable arrows
  let moveCount = 0;
  for (let move = 1; move <= 30; move++) {
    const escapable = await page.evaluate(() => {
      if (typeof getFree === 'function' && typeof G !== 'undefined') {
        const free = getFree(G.grid, G.mask, G.locks, G.frozen, G.escaped);
        if (free.length > 0) return free[0]; // [r, c]
      }
      return null;
    });

    if (!escapable) break;
    moveCount++;

    const cell = await page.$(`#grid [data-r="${escapable[0]}"][data-c="${escapable[1]}"]`);
    if (cell) {
      await cell.click();
      await page.waitForTimeout(500);
      if (move === 2) {
        await page.screenshot({ path: `${ASSETS}/images/03-level1-mid.png` });
        console.log('Captured: level 1 mid-game');
      }
    }
  }

  // Win screen
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${ASSETS}/images/04-level1-win.png` });
  console.log('Captured: level 1 win');

  // Go to next level via Next Level button or navigate
  await page.waitForTimeout(500);
  const nextBtn = await page.$('text=Next Level');
  if (nextBtn) await nextBtn.click();
  else await page.evaluate(() => startLevel(2));
  await page.waitForTimeout(1200);

  // Play levels 2-4 quickly
  for (let lvl = 2; lvl <= 4; lvl++) {
    console.log(`Playing level ${lvl}...`);
    for (let move = 1; move <= 40; move++) {
      const esc = await page.evaluate(() => {
        if (typeof getFree === 'function' && typeof G !== 'undefined') {
          const free = getFree(G.grid, G.mask, G.locks, G.frozen, G.escaped);
          return free.length > 0 ? free[0] : null;
        }
        return null;
      });
      if (!esc) break;
      const cell = await page.$(`#grid [data-r="${esc[0]}"][data-c="${esc[1]}"]`);
      if (cell) { await cell.click(); await page.waitForTimeout(350); }
    }
    await page.waitForTimeout(1500);
    if (lvl === 3) {
      await page.screenshot({ path: `${ASSETS}/images/05-level3-win.png` });
      console.log('Captured: level 3 win');
    }
    // Move to next level
    const nb = await page.$('text=Next Level');
    if (nb) await nb.click();
    else await page.evaluate((n) => startLevel(n), lvl + 1);
    await page.waitForTimeout(1000);
  }

  // Level 5: capture the start
  await page.screenshot({ path: `${ASSETS}/images/06-level5-start.png` });
  console.log('Captured: level 5 start');

  // Play level 5 with pauses for dramatic captures
  for (let move = 1; move <= 50; move++) {
    const esc = await page.evaluate(() => {
      if (typeof getFree === 'function' && typeof G !== 'undefined') {
        const free = getFree(G.grid, G.mask, G.locks, G.frozen, G.escaped);
        return free.length > 0 ? free[0] : null;
      }
      return null;
    });
    if (!esc) break;
    const cell = await page.$(`#grid [data-r="${esc[0]}"][data-c="${esc[1]}"]`);
    if (cell) {
      await cell.click();
      await page.waitForTimeout(450);
      if (move === 3) {
        await page.screenshot({ path: `${ASSETS}/images/07-level5-mid.png` });
        console.log('Captured: level 5 mid');
      }
    }
  }
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${ASSETS}/images/08-level5-win.png` });
  console.log('Captured: level 5 win');

  // Navigate to Easy tier - level 9
  await page.evaluate(() => startLevel(9));
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${ASSETS}/images/09-easy-start.png` });
  console.log('Captured: easy tier start');

  // Play level 9
  for (let move = 1; move <= 60; move++) {
    const esc = await page.evaluate(() => {
      if (typeof getFree === 'function' && typeof G !== 'undefined') {
        const free = getFree(G.grid, G.mask, G.locks, G.frozen, G.escaped);
        return free.length > 0 ? free[0] : null;
      }
      return null;
    });
    if (!esc) break;
    const cell = await page.$(`#grid [data-r="${esc[0]}"][data-c="${esc[1]}"]`);
    if (cell) {
      await cell.click();
      await page.waitForTimeout(350);
    }
  }
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${ASSETS}/images/10-easy-win.png` });
  console.log('Captured: easy tier win');

  // Show levels screen
  await page.evaluate(() => showS('sLv'));
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${ASSETS}/images/11-levels-screen.png` });
  console.log('Captured: levels screen');

  // Back to home for closing shot
  await page.evaluate(() => showS('sHo'));
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${ASSETS}/images/12-home-final.png` });
  console.log('Captured: final home');

  await page.close();
  await context.close();
  await browser.close();

  // Rename recorded video
  const vids = fs.readdirSync(`${ASSETS}/video`);
  if (vids.length > 0) {
    const src = path.join(`${ASSETS}/video`, vids[0]);
    const dst = path.join(`${ASSETS}/video`, 'gameplay-raw.webm');
    fs.renameSync(src, dst);
    console.log(`Video saved: ${dst}`);
  }

  console.log('\nAll captures complete!');
  console.log(`Screenshots: ${fs.readdirSync(`${ASSETS}/images`).length} files`);
})();
