"""Contributions: payload builders, validator (mirror of site/contrib.js),
anonymous sending, the GitHub (verified) path, and public aggregation.

tests/test_contrib.py runs the same accept/reject cases through this module
and the JavaScript validator and requires identical verdicts.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import statistics
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone

from . import __version__

SCHEMA = "pickaxetax.contribution.v1"
MAX_BYTES = 32768
MAX_LABELS = 7
REPO = "graviton94/pickaxetax"
CONFIG_URL = "https://graviton94.github.io/pickaxetax/config.json"
K_ANON = 3

SOURCES = ["chatgpt", "claude", "gemini", "copilot", "grok", "perplexity", "deepseek", "openai-messages", "text", "html", "page", "other"]
LANGUAGES = ["ko", "en", "ja", "zh", "und"]
INTENTS = ["ask", "instruct", "clarify", "correct", "retry", "continue", "ack", "context",
           "answer", "code", "followup_question", "apology_fix", "refusal"]
EDGE_TYPES = ["NEXT", "ANSWERS", "DEEPENS", "REVISITS", "PIVOTS", "RETURNS", "CORRECTS", "RETRIES", "CONTINUES"]
LEDGER_PROVIDERS = ["openai", "anthropic", "claude-code"]
LEDGER_ACTIONS = ["forwarded", "forwarded+compacted", "cache_hit", "gratitude_local", "error", "agent_dup_read_blocked"]
SKELETON_METRICS = ["user_turns", "assistant_turns", "visible_tokens", "billed_input_tokens", "billed_output_tokens",
                    "compute_units", "optimized_compute_units", "one_shot_compute_units", "savings_pct", "one_shot_savings_pct",
                    "max_depth", "branches"]
WASTE = ["ack_units", "superseded_units", "offtopic_context_tokens"]
LEDGER_NUMS = ["requests", "input_tokens", "output_tokens", "reasoning_tokens", "history_tokens", "avoided_input", "avoided_output", "measured_requests"]
AGENT_NUMS = ["sessions", "api_calls", "subagent_calls", "compactions", "tool_calls", "cache_hit_pct", "peak_context", "carried_share_pct"]
AGENT_TOKENS = ["input", "cache_read", "cache_write", "output", "processed_input"]
AGENT_COST = ["count", "tokens", "carried_tokens"]
AGENT_TOOL = ["calls", "result_tokens", "carried_tokens", "errors", "images"]
BOUND_METHODS = ["lexical-v1"]
BOUND_NUMS = ["sessions", "api_calls", "measured_input", "pinned_input", "written_tokens"]
BOUND_PCTS = ["P0", "P1000", "P10000", "Pinf"]
BOUND_ROWS = 200

LABEL_RE = re.compile(r"^[^\W_][\w+#.\-]{1,31}\Z")  # letters/digits first; \w here is Unicode like \p{L}\p{N}_
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/\-]{0,64}\Z")
TOOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,40}\Z")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\Z", re.ASCII)
VERSION_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\Z", re.ASCII)
BIG = 1e12


def _label_ok(s) -> bool:
    # JS: /^[\p{L}\p{N}][\p{L}\p{N}+#.\-]{1,31}$/u -- no underscore anywhere
    return isinstance(s, str) and "_" not in s and bool(LABEL_RE.match(s))


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _is_int(x) -> bool:
    return _is_num(x) and float(x).is_integer()


# ------------------------------------------------------------------ builders

def source_enum(src) -> str:
    s = str(src or "").lower()
    if s in SOURCES:
        return s
    for k in ("chatgpt", "claude", "gemini", "copilot", "grok", "perplexity", "deepseek"):
        if k in s:
            return k
    if "openai" in s:
        return "chatgpt"
    if "x.com" in s:
        return "grok"
    return "other"


def skeleton_contribution(sk: dict, labels: list[str] | None = None, client: str = "cli") -> dict:
    m = sk["metrics"]
    edges: dict[str, int] = {}
    for e in sk["edges"]:
        edges[e["type"]] = edges.get(e["type"], 0) + 1
    data = {
        "source": source_enum(sk.get("source")),
        "language": sk.get("language") if sk.get("language") in LANGUAGES else "und",
        "metrics": {k: m[k] for k in SKELETON_METRICS},
        "waste": {k: m["waste"][k] for k in WASTE},
        "turns": [["u" if t["role"] == "user" else "a", t["intent"], t["depth"], t["branch"], t["tokens"], 1 if t["redundant"] else 0]
                  for t in sk["turns"][:400]],
        "edges": edges,
    }
    clean = [l for l in (labels or []) if _label_ok(l)][:MAX_LABELS]
    if clean:
        data["labels"] = clean
    return {"schema": SCHEMA, "kind": "skeleton", "client": client, "version": __version__, "data": data}


def from_export(obj: dict, labels: bool = False, client: str = "cli") -> dict:
    """Wrap a local export (skeleton JSON, `pxt ledger --export`, `pxt agent audit --export`)."""
    if obj.get("schema") == SCHEMA:
        return obj
    if obj.get("schema") == "pickaxetax.ledger.v1":
        return {"schema": SCHEMA, "kind": "ledger", "client": client, "version": __version__, "data": {"rows": obj["rows"]}}
    if obj.get("schema") == "pickaxetax.agent.v1":
        data = {k: v for k, v in obj.items() if k != "schema"}
        return {"schema": SCHEMA, "kind": "agent", "client": client, "version": __version__, "data": data}
    if "turns" in obj and "metrics" in obj:
        return skeleton_contribution(obj, obj.get("agenda", [])[:3] if labels else None, client)
    raise ValueError("not a recognized export (skeleton, ledger or agent)")


# ------------------------------------------------------------------ validator

def _check_keys(obj, allowed, where, errs, required=None) -> bool:
    if not isinstance(obj, dict):
        errs.append(f"{where}: must be an object")
        return False
    for k in obj:
        if k not in allowed:
            errs.append(f"{where}: unknown key {json.dumps(k)}")
    for k in (allowed if required is None else required):
        if k not in obj:
            errs.append(f"{where}: missing {k}")
    return True


def _check_nums(obj, keys, where, errs, ints=True, lo=0, hi=BIG):
    for k in keys:
        v = obj.get(k)
        if not _is_num(v) or v < lo or v > hi or (ints and not _is_int(v)):
            errs.append(f"{where}.{k}: bad number")


def _validate_skeleton(d, errs):
    if not _check_keys(d, ["source", "language", "metrics", "waste", "turns", "edges", "labels"], "data", errs,
                       ["source", "language", "metrics", "waste", "turns", "edges"]):
        return
    if d.get("source") not in SOURCES:
        errs.append("data.source: unknown")
    if d.get("language") not in LANGUAGES:
        errs.append("data.language: unknown")
    pct = ["savings_pct", "one_shot_savings_pct"]
    if _check_keys(d.get("metrics"), SKELETON_METRICS, "data.metrics", errs):
        _check_nums(d["metrics"], [k for k in SKELETON_METRICS if k not in pct], "data.metrics", errs)
        _check_nums(d["metrics"], pct, "data.metrics", errs, ints=False, lo=-100, hi=100)
    if _check_keys(d.get("waste"), WASTE, "data.waste", errs):
        _check_nums(d["waste"], WASTE, "data.waste", errs)
    turns = d.get("turns")
    if not isinstance(turns, list) or not 1 <= len(turns) <= 400:
        errs.append("data.turns: 1..400 entries")
    else:
        for i, t in enumerate(turns):
            ok = (isinstance(t, list) and len(t) == 6 and t[0] in ("u", "a") and t[1] in INTENTS
                  and all(_is_int(x) and 0 <= x <= BIG for x in t[2:5]) and t[5] in (0, 1) and not isinstance(t[5], bool))
            if not ok:
                errs.append(f"data.turns[{i}]: bad turn")
    edges = d.get("edges")
    if isinstance(edges, dict):
        for k, v in edges.items():
            if k not in EDGE_TYPES:
                errs.append(f"data.edges: unknown type {json.dumps(k)}")
            elif not _is_int(v) or v < 0 or v > BIG:
                errs.append(f"data.edges.{k}: bad number")
    else:
        errs.append("data.edges: must be an object")
    if "labels" in d:
        lb = d["labels"]
        if not isinstance(lb, list) or len(lb) > MAX_LABELS or not all(_label_ok(l) for l in lb) or len(set(lb)) != len(lb):
            errs.append("data.labels: up to 7 distinct short words")
    if not errs:
        m = d["metrics"]
        users = sum(1 for t in turns if t[0] == "u")
        assts = len(turns) - users
        tok = sum(t[4] for t in turns)
        if m["user_turns"] + m["assistant_turns"] <= 400:
            if users != m["user_turns"] or assts != m["assistant_turns"]:
                errs.append("consistency: turn counts")
            if tok != m["visible_tokens"]:
                errs.append("consistency: visible tokens")
        elif len(turns) != 400 or users > m["user_turns"] or assts > m["assistant_turns"] or tok > m["visible_tokens"]:
            errs.append("consistency: truncated turns")
        if m["user_turns"] < 1:
            errs.append("consistency: no user turns")
        if m["optimized_compute_units"] > m["compute_units"] or m["one_shot_compute_units"] > m["compute_units"]:
            errs.append("consistency: optimized > actual")
        if m["billed_output_tokens"] > m["visible_tokens"]:
            errs.append("consistency: billed output")


def _validate_ledger(d, errs):
    if not _check_keys(d, ["rows"], "data", errs):
        return
    rows = d.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        errs.append("data.rows: 1..1000 entries")
        return
    for i, r in enumerate(rows):
        where = f"data.rows[{i}]"
        if not _check_keys(r, ["day", "provider", "model", "action", *LEDGER_NUMS], where, errs):
            continue
        if not isinstance(r.get("day"), str) or not DAY_RE.match(r["day"]):
            errs.append(f"{where}.day: bad")
        if r.get("provider") not in LEDGER_PROVIDERS:
            errs.append(f"{where}.provider: unknown")
        if not isinstance(r.get("model"), str) or not MODEL_RE.match(r["model"]):
            errs.append(f"{where}.model: bad")
        if r.get("action") not in LEDGER_ACTIONS:
            errs.append(f"{where}.action: unknown")
        _check_nums(r, LEDGER_NUMS, where, errs)
        if not errs and r["measured_requests"] > r["requests"]:
            errs.append(f"{where}: measured > requests")


def _pct_ok(x) -> bool:
    return _is_num(x) and 0 <= x <= 100


def _validate_bound(b, errs):
    keys = ["method", *BOUND_NUMS, "tokenizer_factor", "avoidable_pct", "per_session"]
    if not _check_keys(b, keys, "data.bound", errs):
        return
    if b.get("method") not in BOUND_METHODS:
        errs.append("data.bound.method: unknown")
    _check_nums(b, BOUND_NUMS, "data.bound", errs)
    _check_nums(b, ["tokenizer_factor"], "data.bound", errs, ints=False, hi=20)
    if _check_keys(b.get("avoidable_pct"), BOUND_PCTS, "data.bound.avoidable_pct", errs):
        _check_nums(b["avoidable_pct"], BOUND_PCTS, "data.bound.avoidable_pct", errs, ints=False, hi=100)
    rows = b.get("per_session")
    if not isinstance(rows, list) or not 1 <= len(rows) <= BOUND_ROWS:
        errs.append(f"data.bound.per_session: 1..{BOUND_ROWS} rows")
        return
    for i, r in enumerate(rows):
        ok = (isinstance(r, list) and len(r) == 7 and _is_int(r[0]) and 1 <= r[0] <= BIG and _is_int(r[1]) and 0 <= r[1] <= BIG
              and all(_pct_ok(x) for x in r[2:]) and r[3] >= r[4] >= r[5] >= r[6] and r[3] <= 100 - r[2] + 0.1)
        if not ok:
            errs.append(f"data.bound.per_session[{i}]: bad row")
    if errs:
        return
    a = b["avoidable_pct"]
    if not a["P0"] >= a["P1000"] >= a["P10000"] >= a["Pinf"]:
        errs.append("consistency: bound policies out of order")
    if b["pinned_input"] > b["measured_input"]:
        errs.append("consistency: pinned > measured")
    elif b["measured_input"] and a["P0"] > 100 * (b["measured_input"] - b["pinned_input"]) / b["measured_input"] + 0.1:
        errs.append("consistency: bound above ceiling")
    if len(rows) != min(b["sessions"], BOUND_ROWS):
        errs.append("consistency: bound session rows")
    elif len(rows) == b["sessions"] and (sum(r[0] for r in rows) != b["api_calls"] or sum(r[1] for r in rows) != b["measured_input"]):
        errs.append("consistency: bound session totals")


def _validate_agent(d, errs):
    keys = ["agent", *AGENT_NUMS, "tokens", "duplicate_reads", "large_results", "failed_repeats", "by_tool", "bound"]
    if not _check_keys(d, keys, "data", errs, keys[:-1]):
        return
    if d.get("agent") != "claude-code":
        errs.append("data.agent: unknown")
    _check_nums(d, [k for k in AGENT_NUMS if not k.endswith("_pct")], "data", errs)
    _check_nums(d, [k for k in AGENT_NUMS if k.endswith("_pct")], "data", errs, ints=False, hi=100)
    if _check_keys(d.get("tokens"), AGENT_TOKENS, "data.tokens", errs):
        _check_nums(d["tokens"], AGENT_TOKENS, "data.tokens", errs)
    for k in ("duplicate_reads", "large_results", "failed_repeats"):
        if _check_keys(d.get(k), AGENT_COST, f"data.{k}", errs):
            _check_nums(d[k], AGENT_COST, f"data.{k}", errs)
    bt = d.get("by_tool")
    if isinstance(bt, dict):
        if len(bt) > 60:
            errs.append("data.by_tool: too many tools")
        for n, b in bt.items():
            if not TOOL_RE.match(n) or n.startswith("mcp__"):
                errs.append(f"data.by_tool: bad tool name {json.dumps(n)}")
            elif _check_keys(b, AGENT_TOOL, f"data.by_tool.{n}", errs):
                _check_nums(b, AGENT_TOOL, f"data.by_tool.{n}", errs)
    else:
        errs.append("data.by_tool: must be an object")
    if "bound" in d:
        _validate_bound(d["bound"], errs)
    if not errs:
        t = d["tokens"]
        if t["processed_input"] != t["input"] + t["cache_read"] + t["cache_write"]:
            errs.append("consistency: processed_input")


def validate(p) -> list[str]:
    try:
        size = len(json.dumps(p, ensure_ascii=False, separators=(",", ":")).encode())
    except (TypeError, ValueError):
        return ["not serializable"]
    if size > MAX_BYTES:
        return [f"too large ({size} bytes > {MAX_BYTES})"]
    errs: list[str] = []
    if not _check_keys(p, ["schema", "kind", "client", "version", "data"], "payload", errs):
        return errs
    if p.get("schema") != SCHEMA:
        errs.append("payload.schema: unknown")
    if p.get("client") not in ("web", "cli"):
        errs.append("payload.client: unknown")
    if not isinstance(p.get("version"), str) or not VERSION_RE.match(p["version"]):
        errs.append("payload.version: bad")
    if errs:
        return errs
    kind = p.get("kind")
    if kind == "skeleton":
        _validate_skeleton(p.get("data"), errs)
    elif kind == "ledger":
        _validate_ledger(p.get("data"), errs)
    elif kind == "agent":
        _validate_agent(p.get("data"), errs)
    else:
        errs.append("payload.kind: unknown")
    return errs


# ------------------------------------------------------------------ anonymous send

def _lzb(h: bytes) -> int:
    n = 0
    for b in h:
        if b == 0:
            n += 8
            continue
        return n + 8 - b.bit_length()
    return n


def solve_pow(seed: str, bits: int) -> str:
    i = 0
    while True:
        if _lzb(hashlib.sha256(f"{seed}:{i}".encode()).digest()) >= bits:
            return str(i)
        i += 1


def _http(method: str, url: str, body: dict | None = None, headers: dict | None = None, timeout: float = 30) -> tuple[int, dict]:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", "User-Agent": f"pickaxetax/{__version__}", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def contrib_url() -> str:
    env = os.environ.get("PICKAXETAX_CONTRIB_URL")
    if env:
        return env.rstrip("/")
    try:
        status, cfg = _http("GET", CONFIG_URL, timeout=10)
        return str(cfg.get("contribUrl") or "").rstrip("/") if status == 200 else ""
    except OSError:
        return ""


def send(payload: dict, base: str | None = None) -> dict:
    errs = validate(payload)
    if errs:
        raise ValueError("invalid contribution: " + "; ".join(errs[:5]))
    base = base or contrib_url()
    if not base:
        raise ValueError("anonymous contributions are not configured yet; use --github")
    status, ch = _http("GET", base + "/challenge")
    if status != 200:
        raise ValueError(f"challenge failed (HTTP {status})")
    nonce = solve_pow(ch["seed"], int(ch["bits"]))
    status, res = _http("POST", base + "/contribute", {"payload": payload, "pow": {**ch, "nonce": nonce}})
    if status != 201:
        raise ValueError(f"contribution rejected (HTTP {status}): {res.get('error')} {res.get('details') or ''}".strip())
    return res


# ------------------------------------------------------------------ GitHub (verified)

def github_issue_url(payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    q = urllib.parse.urlencode({"template": "contribution.yml", "title": f"[contribution] {payload['kind']}", "payload": body})
    return f"https://github.com/{REPO}/issues/new?{q}"


_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.S)


def payload_from_issue(body: str) -> dict:
    for block in _FENCE.findall(body or "") + [body or ""]:
        try:
            obj = json.loads(block.strip())
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("no JSON payload found in the issue")


# ------------------------------------------------------------------ aggregation

def _quartiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    if len(xs) < 2:
        return {"median": xs[0], "q1": xs[0], "q3": xs[0]}
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return {"median": round(q[1], 1), "q1": round(q[0], 1), "q3": round(q[2], 1)}


def aggregate(records: list[dict], labels: dict | None = None, k: int = K_ANON) -> dict:
    """records: [{"payload": ..., "verified": bool}] -> public aggregate.

    Sums for totals, medians for typical values (robust to a few bad actors),
    labels only when they appear in >= k contributions.
    """
    by_kind = Counter(r["payload"]["kind"] for r in records)
    sk = [r["payload"]["data"] for r in records if r["payload"]["kind"] == "skeleton"]
    led = [row for r in records if r["payload"]["kind"] == "ledger" for row in r["payload"]["data"]["rows"]]
    ag = [r["payload"]["data"] for r in records if r["payload"]["kind"] == "agent"]

    def total(items, key):
        return sum(x[key] for x in items)

    out = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "contributions": {"total": len(records), "verified": sum(1 for r in records if r.get("verified")),
                          "anonymous": sum(1 for r in records if not r.get("verified")), "by_kind": dict(by_kind)},
    }
    if sk:
        mets = [x["metrics"] for x in sk]
        cu, opt = total(mets, "compute_units"), total(mets, "optimized_compute_units")
        intents = Counter(t[1] for x in sk for t in x["turns"])
        out["skeleton"] = {
            "conversations": len(sk),
            "compute_units": cu,
            "optimized_compute_units": opt,
            "avoidable_pct": round(100 * (1 - opt / cu), 1) if cu else 0.0,
            "median_savings_pct": round(statistics.median(m["savings_pct"] for m in mets), 1),
            "billed_input_tokens": total(mets, "billed_input_tokens"),
            "visible_tokens": total(mets, "visible_tokens"),
            "waste": {w: sum(x["waste"][w] for x in sk) for w in WASTE},
            "intents": dict(intents.most_common()),
            "languages": dict(Counter(x["language"] for x in sk).most_common()),
            "sources": dict(Counter(x["source"] for x in sk).most_common()),
        }
    if led:
        out["ledger"] = {k2: sum(r[k2] for r in led) for k2 in LEDGER_NUMS}
        out["ledger"]["actions"] = dict(Counter(r["action"] for r in led for _ in range(r["requests"])).most_common())
    if ag:
        out["agent"] = {
            "sessions": total(ag, "sessions"),
            "api_calls": total(ag, "api_calls"),
            "processed_input": sum(x["tokens"]["processed_input"] for x in ag),
            "median_cache_hit_pct": round(statistics.median(x["cache_hit_pct"] for x in ag), 1),
            "median_peak_context": statistics.median(x["peak_context"] for x in ag),
            "duplicate_reads": sum(x["duplicate_reads"]["count"] for x in ag),
            "large_results": sum(x["large_results"]["count"] for x in ag),
            "carried_tokens": sum(x["duplicate_reads"]["carried_tokens"] + x["large_results"]["carried_tokens"] for x in ag),
        }
        rows = [r for x in ag if "bound" in x for r in x["bound"]["per_session"]]
        if rows:  # the session is the unit: medians and quartiles over sessions, not pooled tokens
            out["agent"]["bound"] = {
                "method": BOUND_METHODS[0],
                "sessions": len(rows),
                "pinned_pct": _quartiles([r[2] for r in rows]),
                **{k: _quartiles([r[3 + i] for r in rows]) for i, k in enumerate(BOUND_PCTS)},
            }
    # labels: verified contributions are counted here; anonymous ones arrive pre-filtered from the worker
    lab = Counter()
    pairs = Counter()
    for x in sk:
        ls = sorted(set(x.get("labels", [])))
        lab.update(ls)
        pairs.update((a, b) for i, a in enumerate(ls) for b in ls[i + 1:])
    for name, n in (labels or {}).get("labels", []):
        lab[name] += n
    for a, b, n in (labels or {}).get("pairs", []):
        pairs[tuple(sorted((a, b)))] += n
    out["topics"] = {
        "k": k,
        "nodes": [{"label": l, "count": n} for l, n in lab.most_common(100) if n >= k],
        "links": [{"source": a, "target": b, "count": n} for (a, b), n in pairs.most_common(300) if n >= k],
    }
    return out
