import { createRequire } from 'node:module';
// node render-slides.mjs <slides.html> <outdir>: one PNG per <section class="slide"> (1080x1350)
let chromium;
try { ({ chromium } = createRequire(import.meta.url)('playwright')); }
catch { ({ chromium } = createRequire('/opt/node-tools/node_modules/')('playwright')); }
const [, , html, outdir] = process.argv;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
await p.goto('file://' + (html.startsWith('/') ? html : process.cwd() + '/' + html));
await p.evaluate(() => document.fonts.ready);
const over = await p.$$eval('.slide', ss => ss.map(s => [s.id, s.scrollHeight, s.clientHeight, s.scrollWidth, s.clientWidth]));
console.log(JSON.stringify(over));
const ids = await p.$$eval('.slide', ss => ss.map(s => s.id));
for (const [i, id] of ids.entries()) {
  await p.locator('#' + id).screenshot({ path: `${outdir}/${String(i + 1).padStart(2, '0')}.png` });
}
await b.close();
