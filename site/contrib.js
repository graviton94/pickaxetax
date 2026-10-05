// Contribution payloads: builders, the validator, and the proof-of-work solver.
//
// Shared by the static site (browser) and the Cloudflare Worker (worker/),
// mirrored in Python by pickaxetax/contrib.py -- tests/test_contrib.py checks
// that both validators accept and reject exactly the same payloads.
//
// The validator is an allowlist: only known keys, enumerated strings, bounded
// numbers and (opt-in) short topic labels pass. Free text cannot be smuggled
// into a contribution, and internal consistency checks reject most fabricated
// numbers.

export const SCHEMA = "pickaxetax.contribution.v1";
export const MAX_BYTES = 32768;
export const MAX_LABELS = 7;

const SOURCES = ["chatgpt", "claude", "gemini", "copilot", "grok", "perplexity", "deepseek", "openai-messages", "text", "html", "page", "other"];
const LANGUAGES = ["ko", "en", "ja", "zh", "und"];
const INTENTS = ["ask", "instruct", "clarify", "correct", "retry", "continue", "ack", "context",
  "answer", "code", "followup_question", "apology_fix", "refusal"];
const EDGE_TYPES = ["NEXT", "ANSWERS", "DEEPENS", "REVISITS", "PIVOTS", "RETURNS", "CORRECTS", "RETRIES", "CONTINUES"];
const LEDGER_PROVIDERS = ["openai", "anthropic", "claude-code"];
const LEDGER_ACTIONS = ["forwarded", "forwarded+compacted", "cache_hit", "gratitude_local", "error", "agent_dup_read_blocked"];
const SKELETON_METRICS = ["user_turns", "assistant_turns", "visible_tokens", "billed_input_tokens", "billed_output_tokens",
  "compute_units", "optimized_compute_units", "one_shot_compute_units", "savings_pct", "one_shot_savings_pct", "max_depth", "branches"];
const WASTE = ["ack_units", "superseded_units", "offtopic_context_tokens"];
const LEDGER_NUMS = ["requests", "input_tokens", "output_tokens", "reasoning_tokens", "history_tokens", "avoided_input", "avoided_output", "measured_requests"];
const AGENT_NUMS = ["sessions", "api_calls", "subagent_calls", "compactions", "tool_calls", "cache_hit_pct", "peak_context", "carried_share_pct"];
const AGENT_TOKENS = ["input", "cache_read", "cache_write", "output", "processed_input"];
const AGENT_COST = ["count", "tokens", "carried_tokens"];
const AGENT_TOOL = ["calls", "result_tokens", "carried_tokens", "errors", "images"];

const LABEL_RE = /^[\p{L}\p{N}][\p{L}\p{N}+#.\-]{1,31}$/u;
const MODEL_RE = /^[A-Za-z0-9._:\/\-]{0,64}$/;
const TOOL_RE = /^[A-Za-z][A-Za-z0-9_]{0,40}$/;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;
const VERSION_RE = /^\d{1,3}\.\d{1,3}\.\d{1,3}$/;
const BIG = 1e12;

const isObj = (x) => x !== null && typeof x === "object" && !Array.isArray(x);
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isInt = (x) => Number.isInteger(x);

// ------------------------------------------------------------------ builders

export function sourceEnum(src) {
  const s = String(src || "").toLowerCase();
  if (SOURCES.includes(s)) return s;
  for (const k of ["chatgpt", "claude", "gemini", "copilot", "grok", "perplexity", "deepseek"]) if (s.includes(k)) return k;
  if (s.includes("openai")) return "chatgpt";
  if (s.includes("x.com")) return "grok";
  return "other";
}

/** Skeleton (from the engine) -> contribution. Labels only when the user opted in. */
export function skeletonContribution(sk, { labels = [], client = "web", version = "0.0.0" } = {}) {
  const m = sk.metrics;
  const data = {
    source: sourceEnum(sk.source),
    language: LANGUAGES.includes(sk.language) ? sk.language : "und",
    metrics: Object.fromEntries(SKELETON_METRICS.map((k) => [k, m[k]])),
    waste: Object.fromEntries(WASTE.map((k) => [k, m.waste[k]])),
    turns: sk.turns.slice(0, 400).map((t) => [t.role === "user" ? "u" : "a", t.intent, t.depth, t.branch, t.tokens, t.redundant ? 1 : 0]),
    edges: {},
  };
  for (const e of sk.edges) data.edges[e.type] = (data.edges[e.type] || 0) + 1;
  const clean = labels.filter((l) => LABEL_RE.test(l)).slice(0, MAX_LABELS);
  if (clean.length) data.labels = clean;
  return { schema: SCHEMA, kind: "skeleton", client, version, data };
}

// ------------------------------------------------------------------ validator

function checkKeys(obj, allowed, where, errs, required = allowed) {
  if (!isObj(obj)) { errs.push(`${where}: must be an object`); return false; }
  for (const k of Object.keys(obj)) if (!allowed.includes(k)) errs.push(`${where}: unknown key ${JSON.stringify(k)}`);
  for (const k of required) if (!(k in obj)) errs.push(`${where}: missing ${k}`);
  return true;
}

function checkNums(obj, keys, where, errs, { ints = true, min = 0, max = BIG } = {}) {
  for (const k of keys) {
    const v = obj[k];
    if (!isNum(v) || v < min || v > max || (ints && !isInt(v))) errs.push(`${where}.${k}: bad number`);
  }
}

function validateSkeleton(d, errs) {
  if (!checkKeys(d, ["source", "language", "metrics", "waste", "turns", "edges", "labels"], "data", errs,
    ["source", "language", "metrics", "waste", "turns", "edges"])) return;
  if (!SOURCES.includes(d.source)) errs.push("data.source: unknown");
  if (!LANGUAGES.includes(d.language)) errs.push("data.language: unknown");
  if (checkKeys(d.metrics, SKELETON_METRICS, "data.metrics", errs)) {
    const pct = ["savings_pct", "one_shot_savings_pct"];
    checkNums(d.metrics, SKELETON_METRICS.filter((k) => !pct.includes(k)), "data.metrics", errs);
    checkNums(d.metrics, pct, "data.metrics", errs, { ints: false, min: -100, max: 100 });
  }
  if (checkKeys(d.waste, WASTE, "data.waste", errs)) checkNums(d.waste, WASTE, "data.waste", errs);
  if (!Array.isArray(d.turns) || d.turns.length < 1 || d.turns.length > 400) errs.push("data.turns: 1..400 entries");
  else {
    d.turns.forEach((t, i) => {
      const ok = Array.isArray(t) && t.length === 6 && (t[0] === "u" || t[0] === "a") && INTENTS.includes(t[1])
        && [t[2], t[3], t[4]].every((x) => isInt(x) && x >= 0 && x <= BIG) && (t[5] === 0 || t[5] === 1);
      if (!ok) errs.push(`data.turns[${i}]: bad turn`);
    });
  }
  if (isObj(d.edges)) {
    for (const [k, v] of Object.entries(d.edges)) {
      if (!EDGE_TYPES.includes(k)) errs.push(`data.edges: unknown type ${JSON.stringify(k)}`);
      else if (!isInt(v) || v < 0 || v > BIG) errs.push(`data.edges.${k}: bad number`);
    }
  } else errs.push("data.edges: must be an object");
  if ("labels" in d) {
    if (!Array.isArray(d.labels) || d.labels.length > MAX_LABELS || !d.labels.every((l) => typeof l === "string" && LABEL_RE.test(l))
      || new Set(d.labels).size !== d.labels.length) errs.push("data.labels: up to 7 distinct short words");
  }
  // consistency: rejects most fabricated numbers
  if (!errs.length) {
    const m = d.metrics;
    const users = d.turns.filter((t) => t[0] === "u").length;
    const assts = d.turns.length - users;
    const tok = d.turns.reduce((s, t) => s + t[4], 0);
    if (m.user_turns + m.assistant_turns <= 400) {
      if (users !== m.user_turns || assts !== m.assistant_turns) errs.push("consistency: turn counts");
      if (tok !== m.visible_tokens) errs.push("consistency: visible tokens");
    } else if (d.turns.length !== 400 || users > m.user_turns || assts > m.assistant_turns || tok > m.visible_tokens) {
      errs.push("consistency: truncated turns");
    }
    if (m.user_turns < 1) errs.push("consistency: no user turns");
    if (m.optimized_compute_units > m.compute_units || m.one_shot_compute_units > m.compute_units) errs.push("consistency: optimized > actual");
    if (m.billed_output_tokens > m.visible_tokens) errs.push("consistency: billed output");
  }
}

function validateLedger(d, errs) {
  if (!checkKeys(d, ["rows"], "data", errs)) return;
  if (!Array.isArray(d.rows) || d.rows.length < 1 || d.rows.length > 1000) { errs.push("data.rows: 1..1000 entries"); return; }
  d.rows.forEach((r, i) => {
    const where = `data.rows[${i}]`;
    if (!checkKeys(r, ["day", "provider", "model", "action", ...LEDGER_NUMS], where, errs)) return;
    if (typeof r.day !== "string" || !DAY_RE.test(r.day)) errs.push(`${where}.day: bad`);
    if (!LEDGER_PROVIDERS.includes(r.provider)) errs.push(`${where}.provider: unknown`);
    if (typeof r.model !== "string" || !MODEL_RE.test(r.model)) errs.push(`${where}.model: bad`);
    if (!LEDGER_ACTIONS.includes(r.action)) errs.push(`${where}.action: unknown`);
    checkNums(r, LEDGER_NUMS, where, errs);
    if (!errs.length && r.measured_requests > r.requests) errs.push(`${where}: measured > requests`);
  });
}

function validateAgent(d, errs) {
  const keys = ["agent", ...AGENT_NUMS, "tokens", "duplicate_reads", "large_results", "failed_repeats", "by_tool"];
  if (!checkKeys(d, keys, "data", errs)) return;
  if (d.agent !== "claude-code") errs.push("data.agent: unknown");
  checkNums(d, AGENT_NUMS.filter((k) => !k.endsWith("_pct")), "data", errs);
  checkNums(d, AGENT_NUMS.filter((k) => k.endsWith("_pct")), "data", errs, { ints: false, max: 100 });
  if (checkKeys(d.tokens, AGENT_TOKENS, "data.tokens", errs)) checkNums(d.tokens, AGENT_TOKENS, "data.tokens", errs);
  for (const k of ["duplicate_reads", "large_results", "failed_repeats"]) {
    if (checkKeys(d[k], AGENT_COST, `data.${k}`, errs)) checkNums(d[k], AGENT_COST, `data.${k}`, errs);
  }
  if (isObj(d.by_tool)) {
    const names = Object.keys(d.by_tool);
    if (names.length > 60) errs.push("data.by_tool: too many tools");
    for (const n of names) {
      if (!TOOL_RE.test(n) || n.startsWith("mcp__")) errs.push(`data.by_tool: bad tool name ${JSON.stringify(n)}`);
      else if (checkKeys(d.by_tool[n], AGENT_TOOL, `data.by_tool.${n}`, errs)) checkNums(d.by_tool[n], AGENT_TOOL, `data.by_tool.${n}`, errs);
    }
  } else errs.push("data.by_tool: must be an object");
  if (!errs.length && d.tokens.processed_input !== d.tokens.input + d.tokens.cache_read + d.tokens.cache_write) errs.push("consistency: processed_input");
}

/** Returns a list of errors; empty means valid. */
export function validateContribution(p) {
  const errs = [];
  let size = 0;
  try { size = new TextEncoder().encode(JSON.stringify(p)).length; } catch { return ["not serializable"]; }
  if (size > MAX_BYTES) return [`too large (${size} bytes > ${MAX_BYTES})`];
  if (!checkKeys(p, ["schema", "kind", "client", "version", "data"], "payload", errs)) return errs;
  if (p.schema !== SCHEMA) errs.push("payload.schema: unknown");
  if (p.client !== "web" && p.client !== "cli") errs.push("payload.client: unknown");
  if (typeof p.version !== "string" || !VERSION_RE.test(p.version)) errs.push("payload.version: bad");
  if (errs.length) return errs;
  if (p.kind === "skeleton") validateSkeleton(p.data, errs);
  else if (p.kind === "ledger") validateLedger(p.data, errs);
  else if (p.kind === "agent") validateAgent(p.data, errs);
  else errs.push("payload.kind: unknown");
  return errs;
}

// ------------------------------------------------------------------ proof of work

function leadingZeroBits(bytes) {
  let n = 0;
  for (const b of bytes) {
    if (b === 0) { n += 8; continue; }
    n += Math.clz32(b) - 24;
    break;
  }
  return n;
}

export async function powValid(seed, nonce, bits) {
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${seed}:${nonce}`)));
  return leadingZeroBits(h) >= bits;
}

/** Find a nonce; ~2^bits hashes. onProgress(tries) is called now and then. */
export async function solvePow(seed, bits, onProgress) {
  const enc = new TextEncoder();
  for (let i = 0; ; i++) {
    const h = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(`${seed}:${i}`)));
    if (leadingZeroBits(h) >= bits) return String(i);
    if (onProgress && i % 4096 === 0) onProgress(i);
  }
}
