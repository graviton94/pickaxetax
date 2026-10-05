// Pickaxe Tax contribution intake (Cloudflare Worker + D1, free tier).
//
// Anonymous by design: no accounts, no cookies, no IP stored. Abuse is made
// expensive with a proof-of-work challenge and a per-day limit keyed by a
// salted hash that changes daily. Only allowlisted structural data is
// accepted (site/contrib.js validator, shared with the browser).
//
//   GET    /health
//   GET    /challenge                 -> {seed, bits, exp, sig}
//   POST   /contribute                {payload, pow:{seed, bits, exp, sig, nonce}} -> {id, delete_token}
//   DELETE /contribute/:id            header X-Delete-Token
//   GET    /export?after=SEQ&limit=N  public anonymized rows (no labels)
//   GET    /labels                    k-anonymous label and pair counts

import { powValid, validateContribution } from "../../site/contrib.js";

const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
const today = () => new Date().toISOString().slice(0, 10);
const now = () => Math.floor(Date.now() / 1000);

async function sha256(s) { return hex(await crypto.subtle.digest("SHA-256", enc.encode(s))); }

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
}

function randomHex(n) {
  const b = new Uint8Array(n);
  crypto.getRandomValues(b);
  return hex(b);
}

async function secret(env) {
  const row = await env.DB.prepare("SELECT value FROM meta WHERE key='secret'").first();
  if (row) return row.value;
  const s = randomHex(32);
  await env.DB.prepare("INSERT OR IGNORE INTO meta(key, value) VALUES ('secret', ?)").bind(s).run();
  return (await env.DB.prepare("SELECT value FROM meta WHERE key='secret'").first()).value;
}

function cors(req, env) {
  const origin = req.headers.get("Origin") || "";
  const allowed = String(env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
  const h = {
    "Vary": "Origin",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Delete-Token",
    "Access-Control-Max-Age": "86400",
  };
  if (allowed.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

function json(req, env, body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...cors(req, env), ...extra },
  });
}

async function challenge(req, env) {
  const s = await secret(env);
  const seed = randomHex(16);
  const bits = Number(env.POW_BITS || 15);
  const exp = now() + 600;
  return json(req, env, { seed, bits, exp, sig: await hmac(s, `${seed}|${bits}|${exp}`) });
}

async function rateLimited(req, env) {
  // salted with the secret and the date: unlinkable across days, never stored raw
  const ip = req.headers.get("CF-Connecting-IP") || "unknown";
  const day = today();
  const key = await hmac(await secret(env), `rate|${day}|${ip}`);
  await env.DB.prepare("DELETE FROM rate WHERE day <> ?").bind(day).run();
  const row = await env.DB.prepare("SELECT n FROM rate WHERE key = ?").bind(key).first();
  const n = row ? row.n : 0;
  if (n >= Number(env.DAILY_LIMIT || 60)) return true;
  await env.DB.prepare("INSERT INTO rate(key, day, n) VALUES (?, ?, 1) ON CONFLICT(key) DO UPDATE SET n = n + 1").bind(key, day).run();
  return false;
}

async function contribute(req, env) {
  const len = Number(req.headers.get("Content-Length") || 0);
  if (len > 65536) return json(req, env, { error: "too large" }, 413);
  let body;
  try { body = await req.json(); } catch { return json(req, env, { error: "invalid JSON" }, 400); }
  const pow = body && body.pow;
  if (!pow || typeof pow.seed !== "string" || typeof pow.nonce !== "string" || pow.nonce.length > 20) {
    return json(req, env, { error: "missing proof of work" }, 400);
  }
  const s = await secret(env);
  if (pow.sig !== await hmac(s, `${pow.seed}|${pow.bits}|${pow.exp}`) || Number(pow.exp) < now()) {
    return json(req, env, { error: "challenge expired or invalid" }, 400);
  }
  if (!(await powValid(pow.seed, pow.nonce, Number(pow.bits)))) return json(req, env, { error: "proof of work failed" }, 400);
  await env.DB.prepare("DELETE FROM used_pow WHERE exp < ?").bind(now()).run();
  const used = await env.DB.prepare("INSERT OR IGNORE INTO used_pow(seed, exp) VALUES (?, ?)").bind(pow.seed, Number(pow.exp)).run();
  if (!used.meta || used.meta.changes !== 1) return json(req, env, { error: "challenge already used" }, 400);

  const errors = validateContribution(body.payload);
  if (errors.length) return json(req, env, { error: "invalid payload", details: errors.slice(0, 20) }, 422);
  if (await rateLimited(req, env)) return json(req, env, { error: "daily limit reached, thank you!" }, 429);

  const p = body.payload;
  const labels = p.kind === "skeleton" && p.data.labels ? JSON.stringify(p.data.labels) : null;
  const stored = JSON.parse(JSON.stringify(p));
  if (stored.kind === "skeleton") delete stored.data.labels;
  const id = randomHex(8);
  const token = randomHex(16);
  await env.DB.prepare("INSERT INTO contributions(id, day, kind, payload, labels, token_hash) VALUES (?, ?, ?, ?, ?, ?)")
    .bind(id, today(), p.kind, JSON.stringify(stored), labels, await sha256(token)).run();
  return json(req, env, { id, delete_token: token }, 201);
}

async function remove(req, env, id) {
  const token = req.headers.get("X-Delete-Token") || "";
  const row = await env.DB.prepare("SELECT token_hash FROM contributions WHERE id = ?").bind(id).first();
  if (!row || row.token_hash !== await sha256(token)) return json(req, env, { error: "not found" }, 404);
  await env.DB.prepare("DELETE FROM contributions WHERE id = ?").bind(id).run();
  return json(req, env, { deleted: id });
}

async function exportRows(req, env, url) {
  const after = Math.max(0, Number(url.searchParams.get("after") || 0) | 0);
  const limit = Math.min(1000, Math.max(1, Number(url.searchParams.get("limit") || 500) | 0));
  const { results } = await env.DB.prepare("SELECT seq, day, kind, payload FROM contributions WHERE seq > ? ORDER BY seq LIMIT ?")
    .bind(after, limit).all();
  const rows = results.map((r) => ({ seq: r.seq, day: r.day, kind: r.kind, payload: JSON.parse(r.payload) }));
  return json(req, env, { rows, next: rows.length === limit ? rows[rows.length - 1].seq : null }, 200, { "Cache-Control": "public, max-age=300" });
}

async function labels(req, env) {
  const k = Math.max(3, Number(env.K_ANON || 3));
  const single = await env.DB.prepare(
    "SELECT j.value AS label, COUNT(*) AS n FROM contributions c, json_each(c.labels) j WHERE c.labels IS NOT NULL GROUP BY j.value HAVING n >= ? ORDER BY n DESC LIMIT 500",
  ).bind(k).all();
  const pairs = await env.DB.prepare(
    "SELECT a.value AS a, b.value AS b, COUNT(*) AS n FROM contributions c, json_each(c.labels) a, json_each(c.labels) b " +
    "WHERE c.labels IS NOT NULL AND a.value < b.value GROUP BY a.value, b.value HAVING n >= ? ORDER BY n DESC LIMIT 2000",
  ).bind(k).all();
  return json(req, env, { k, labels: single.results.map((r) => [r.label, r.n]), pairs: pairs.results.map((r) => [r.a, r.b, r.n]) },
    200, { "Cache-Control": "public, max-age=300" });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try {
      if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req, env) });
      if (req.method === "GET" && url.pathname === "/health") return json(req, env, { ok: true });
      if (req.method === "GET" && url.pathname === "/challenge") return await challenge(req, env);
      if (req.method === "POST" && url.pathname === "/contribute") return await contribute(req, env);
      const m = url.pathname.match(/^\/contribute\/([0-9a-f]{16})$/);
      if (req.method === "DELETE" && m) return await remove(req, env, m[1]);
      if (req.method === "GET" && url.pathname === "/export") return await exportRows(req, env, url);
      if (req.method === "GET" && url.pathname === "/labels") return await labels(req, env);
      return json(req, env, { error: "not found" }, 404);
    } catch (e) {
      return json(req, env, { error: "internal error" }, 500);
    }
  },
};
