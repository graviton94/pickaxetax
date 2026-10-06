// Production smoke test: leaves no data behind (contributes once, then deletes it).
//   node worker/test/smoke.mjs https://pickaxetax-contrib.<sub>.workers.dev
import { analyzeInput } from "../../site/engine.js";
import { skeletonContribution, solvePow } from "../../site/contrib.js";

const BASE = process.argv[2];
const ORIGIN = "https://graviton94.github.io";
const H = { Origin: ORIGIN, "Content-Type": "application/json" };
const fails = [];
const check = (c, m) => { console.log(`${c ? "PASS" : "FAIL"}  ${m}`); if (!c) fails.push(m); };

for (let i = 0; i < 30; i++) {  // a fresh workers.dev subdomain can take minutes to resolve
  try { if ((await fetch(BASE + "/health")).ok) break; } catch { /* not yet */ }
  await new Promise((r) => setTimeout(r, 10000));
}
const h = await fetch(BASE + "/health", { headers: H });
check(h.status === 200 && h.headers.get("access-control-allow-origin") === ORIGIN, "health + CORS for the site origin");
const [sk] = analyzeInput("User: what is a smoke test?\nAssistant: A quick check that the basics work.");
const payload = skeletonContribution(sk, { version: "0.3.1" });
const ch = await (await fetch(BASE + "/challenge", { headers: H })).json();
const r = await fetch(BASE + "/contribute", { method: "POST", headers: H, body: JSON.stringify({ payload, pow: { ...ch, nonce: await solvePow(ch.seed, ch.bits) } }) });
const res = await r.json();
check(r.status === 201 && res.id && res.delete_token, `contribution accepted (${r.status})`);
if (res.id) {
  const d = await fetch(`${BASE}/contribute/${res.id}`, { method: "DELETE", headers: { ...H, "X-Delete-Token": res.delete_token } });
  check(d.status === 200, "deleted again (no data left behind)");
}
const bad = await fetch(BASE + "/contribute", { method: "POST", headers: H, body: JSON.stringify({ payload, pow: { ...ch, nonce: "0" } }) });
check(bad.status === 400, "replayed/invalid proof of work rejected");
process.exit(fails.length ? 1 : 0);
