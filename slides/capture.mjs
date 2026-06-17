// Capture all slides from presentation HTML using Playwright
// Usage: node capture.mjs <input.html> <output_dir>
import { chromium } from 'playwright';
import { resolve, join } from 'path';
import { mkdirSync } from 'fs';

const [,, htmlPath, outputDir] = process.argv;
if (!htmlPath || !outputDir) {
    console.error('Usage: node capture.mjs <input.html> <output_dir>');
    process.exit(1);
}

mkdirSync(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

await page.goto('file://' + resolve(htmlPath));
await page.waitForTimeout(2000);

const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
console.log(`Capturing ${total} slides from ${htmlPath}`);

for (let i = 0; i < total; i++) {
    await page.evaluate((idx) => {
        const slides = Array.from(document.querySelectorAll('.slide'));
        slides.forEach(s => s.classList.remove('active', 'visible'));
        slides[idx].classList.add('active', 'visible');
    }, i);

    // Wait for CSS transitions/animations
    await page.waitForTimeout(800);

    const outPath = join(resolve(outputDir), `slide-${String(i + 1).padStart(2, '0')}.png`);
    await page.screenshot({ path: outPath });
    console.log(`  [${i + 1}/${total}] ${outPath}`);
}

await browser.close();
console.log(`Done. ${total} slides saved to ${outputDir}`);
