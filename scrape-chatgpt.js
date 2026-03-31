// Playwright script to scrape a shared ChatGPT conversation
const { chromium } = require('playwright');
const fs = require('fs');

const URL = 'https://chatgpt.com/share/69cc1187-a858-832a-b867-93f3865248f8';
const OUT = '/app/projects/trading-explainer/chatgpt-conversation.txt';

(async () => {
  fs.mkdirSync('/app/projects/trading-explainer', { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('Navigating to shared ChatGPT conversation...');
  await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });

  // Wait for conversation content to render
  await page.waitForTimeout(5000);

  // Try multiple selectors for ChatGPT shared conversation content
  let content = '';

  // Attempt 1: article elements (common in shared conversations)
  content = await page.evaluate(() => {
    const articles = document.querySelectorAll('article, [data-message-author-role]');
    if (articles.length > 0) {
      return Array.from(articles).map(a => {
        const role = a.getAttribute('data-message-author-role') ||
                     (a.querySelector('.font-semibold') ? 'user' : 'assistant');
        return `[${role.toUpperCase()}]\n${a.innerText}\n`;
      }).join('\n---\n\n');
    }
    return '';
  });

  // Attempt 2: markdown/prose containers
  if (!content || content.length < 100) {
    content = await page.evaluate(() => {
      const containers = document.querySelectorAll('.markdown, .prose, .text-message, [class*="message"]');
      if (containers.length > 0) {
        return Array.from(containers).map(c => c.innerText).join('\n\n---\n\n');
      }
      return '';
    });
  }

  // Attempt 3: main content area
  if (!content || content.length < 100) {
    content = await page.evaluate(() => {
      const main = document.querySelector('main') || document.querySelector('[role="main"]');
      return main ? main.innerText : '';
    });
  }

  // Attempt 4: all conversation turns
  if (!content || content.length < 100) {
    content = await page.evaluate(() => {
      const turns = document.querySelectorAll('[data-testid*="conversation-turn"]');
      if (turns.length > 0) {
        return Array.from(turns).map(t => t.innerText).join('\n\n---\n\n');
      }
      return '';
    });
  }

  // Attempt 5: just get everything visible
  if (!content || content.length < 100) {
    content = await page.evaluate(() => document.body.innerText);
  }

  // Also take a screenshot for reference
  await page.screenshot({ path: '/app/projects/trading-explainer/chatgpt-screenshot.png', fullPage: true });

  fs.writeFileSync(OUT, content);
  console.log(`Saved: ${content.length} characters to ${OUT}`);
  console.log(`First 500 chars:\n${content.substring(0, 500)}`);
  console.log(`\nTotal conversation turns found: ${content.split('---').length}`);

  await browser.close();
})();
