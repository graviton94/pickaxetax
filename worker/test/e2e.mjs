// End-to-end check against a running worker (wrangler dev --local, or a deployed URL).
//   node worker/test/e2e.mjs http://127.0.0.1:8787
import { analyzeInput } from "../../site/engine.js";
import { skeletonContribution, solvePow } from "../../site/contrib.js";

const BASE = process.argv[2] || "http://127.0.0.1:8787";
const ORIGIN = "http://127.0.0.1:8800";
const fails = [];
const check = (c, m) => { console.log(`${c ? "PASS" : "FAIL"}  ${m}`); if (!c) fails.push(m); };
const call = (path, opts = {}) => fetch(BASE + path, { ...opts, headers: { Origin: ORIGIN, "Content-Type": "application/json", ...(opts.headers || {}) } });

async function contribute(payload, tamper = {}) {
  const ch = await (await call("/challenge")).json();
  const nonce = tamper.nonce ?? await solvePow(ch.seed, ch.bits);
  return call("/contribute", { method: "POST", body: JSON.stringify({ payload, pow: { ...ch, nonce, ...tamper.pow } }) });
}

const chat = (topic, extra) => `User: explain ${topic} replication and ${topic} indexing ${extra}\nAssistant: ${topic} replication copies data; ${topic} indexing speeds queries.\nUser: thanks!\nAssistant: You're welcome!`;
const payloadFor = (text, labels) => { const [sk] = analyzeInput(text); return skeletonContribution(sk, { labels: labels ? sk.agenda.slice(0, 3) : [], version: "0.2.0" }); };

const h = await call("/health");
check(h.status === 200 && h.headers.get("access-control-allow-origin") === ORIGIN, "health + CORS for allowed origin");
const bad = await fetch(BASE + "/health", { headers: { Origin: "https://evil.example" } });
check(!bad.headers.get("access-control-allow-origin"), "no CORS for other origins");

const t0 = Date.now();
const r = await contribute(payloadFor(chat("postgres", "alpha"), true));
const ok = await r.json();
check(r.status === 201 && /^[0-9a-f]{16}$/.test(ok.id) && ok.delete_token, `valid contribution accepted (${Date.now() - t0} ms incl. proof of work)`);

check((await contribute(payloadFor(chat("postgres", "beta"), true), { nonce: "0" })).status === 400, "wrong proof of work rejected");
const ch = await (await call("/challenge")).json();
const nonce = await solvePow(ch.seed, ch.bits);
const first = await call("/contribute", { method: "POST", body: JSON.stringify({ payload: payloadFor(chat("redis", "x"), false), pow: { ...ch, nonce } }) });
const replay = await call("/contribute", { method: "POST", body: JSON.stringify({ payload: payloadFor(chat("redis", "y"), false), pow: { ...ch, nonce } }) });
check(first.status === 201 && replay.status === 400, "challenge cannot be replayed");
check((await contribute(payloadFor(chat("redis", "z"), false), { pow: { exp: 1 } })).status === 400, "forged expiry rejected");

const smuggle = payloadFor(chat("mongo", "q"), false);
smuggle.data.note = "my private diary text";
const sm = await contribute(smuggle);
check(sm.status === 422, "free-text smuggling rejected (unknown key)");
const fake = payloadFor(chat("mongo", "w"), false);
fake.data.metrics.visible_tokens = 999999;
check((await contribute(fake)).status === 422, "fabricated numbers rejected (consistency)");

for (const extra of ["gamma", "delta"]) await contribute(payloadFor(chat("postgres", extra), true));
const labels = await (await call("/labels")).json();
const names = labels.labels.map((x) => x[0]);
check(names.includes("postgres") && labels.labels.every((x) => x[1] >= 3), `k-anonymous labels (k=${labels.k}): ${names.join(", ")}`);
check(labels.pairs.every((p) => p[2] >= 3), "pairs also k-anonymous");

const exp = await (await call("/export?limit=1000")).json();
check(exp.rows.length >= 4 && exp.rows.every((x) => !("labels" in x.payload.data) && !("token_hash" in x)), "export has no labels or tokens");

check((await call(`/contribute/${ok.id}`, { method: "DELETE", headers: { "X-Delete-Token": "wrong" } })).status === 404, "delete needs the token");
check((await call(`/contribute/${ok.id}`, { method: "DELETE", headers: { "X-Delete-Token": ok.delete_token } })).status === 200, "delete with token works");
const exp2 = await (await call("/export?limit=1000")).json();
check(exp2.rows.length === exp.rows.length - 1, "deleted row gone from export");

process.exit(fails.length ? 1 : 0);
