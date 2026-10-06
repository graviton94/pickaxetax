"""The mechanical tier (T1) of the waste codebook v1: what the logs alone decide.

research/protocol/waste-codebook-v1.md, §2-§3. These counts need no human judgment, so
together they are the floor of waste that nobody can dispute. Everything here is input-side
(tokens that entered a context): output counts are left out because event-API logs record
output at stream start, before it is final, so they cannot be compared across sources.

  W1 Duplication   a tool call repeated with the same input and the same result, in the same
                   context (main session or one sub-agent), with no compaction in between.
                   Counted: the repeated result's tokens where it arrives.
  W2 Failure       tool calls whose result is an error. Counted: the error result's tokens.
  W6 Cache churn   on the main chain, the part of the previous call's context that the next
                   call had to write to the cache again instead of reading it (a resume, a
                   model switch, an expired cache). Counted: those cache-write tokens. They
                   would have been processed anyway (as cache reads), so they are not removable
                   tokens: the waste is the price of writing over reading, and the prefill compute.

Two views: removable tokens (W1 + W2) as a share of all input processed, and the
removable cost (W1 + W2 at the cache-write price, W6 at the write price minus the read
price) as a share of the input-side cost.

Carrying any of these into later calls is W5 (stale context), a rule-tier category judged
only after blind validation, so it is not included here.
"""

from __future__ import annotations

import glob
import hashlib
import heapq
import json
import os
from datetime import datetime

from ..tokens import estimate_tokens
from .events import lines_from

SCHEMA = "pickaxetax.survey.judge.v1"
CODEBOOK = "v1"
# price ratios relative to uncached input, for the price-weighted view (Anthropic list prices)
PRICE = {"input": 1.0, "cache_read": 0.1, "cache_write": 1.25}
CHURN_TOLERANCE = 0.02  # ignore re-writes under 2% of the previous context (block alignment)
# W6 is broken down by what preceded the re-write (descriptive only; the floor is unchanged):
# a model switch, or the idle gap since the previous call against the cache lifetimes (5 min, 1 h)
GAPS = (("model_switch", None), ("gap_under_5m", 300), ("gap_5m_to_1h", 3600), ("gap_over_1h", float("inf")))


def _jsonl(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                yield d


def _ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _with_subagents(path):
    """A local transcript plus the sub-agent transcripts Claude Code keeps beside it
    (<session>/subagents/*.jsonl), merged in time order. Sub-agent lines are sidechain lines."""
    files = sorted(glob.glob(os.path.join(os.path.splitext(path)[0], "subagents", "*.jsonl")))
    if not files:
        yield from _jsonl(path)
        return

    def keyed(lines, rank):
        last = ""
        for i, d in enumerate(lines):
            last = str(d.get("timestamp") or last)  # a line without a time keeps its place
            yield (last, rank, i, d)

    streams = [keyed(_jsonl(path), 0)] + [keyed(_jsonl(f), r + 1) for r, f in enumerate(files)]
    for *_, d in heapq.merge(*streams, key=lambda x: x[:3]):
        yield d


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) if isinstance(b, dict) else str(b) for b in content)
    return json.dumps(content, ensure_ascii=False, sort_keys=True)


def judge_lines(lines, limit_instructions: int | None = None, limit_calls: int | None = None) -> dict:
    seen_msg = set()
    calls = []  # main-chain calls: (ctx, cache_read, cache_write, time, model)
    totals = {"input": 0, "cache_read": 0, "cache_write": 0}
    by_ctx = {"main": {"calls": 0, "input": 0}, "side": {"calls": 0, "input": 0}}
    uses = {}  # tool_use_id -> (context key, signature)
    last_result = {}  # (context key, signature) -> (result hash, epoch)
    epoch = 0  # bumps at each compaction: a re-read after compaction is needed, not duplicate
    w1 = {"tokens": 0, "count": 0}
    w2 = {"tokens": 0, "count": 0}
    arrivals = []  # (category, tokens, index of the next main call, epoch) for W1/W2 on the main chain
    instructions = 0
    for d in lines:
        if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
            epoch += 1
            continue
        m = d.get("message")
        if not isinstance(m, dict):
            continue
        # each sub-agent runs in its own context; side lines without an agent id share one
        ctxkey = ("side", str(d.get("agentId") or "")) if d.get("isSidechain") else "main"
        bucket = "side" if d.get("isSidechain") else "main"
        content = m.get("content")
        if d.get("type") == "user":
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
            results = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_result"]
            if not results and not d.get("isSidechain") and not d.get("isMeta") and not d.get("isCompactSummary"):
                text = " ".join(str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("type") == "text")
                if text.strip() and "<system-reminder>" not in text[:200] and not text.lstrip().startswith("<"):
                    instructions += 1
                    if limit_instructions is not None and instructions > limit_instructions:
                        break
            for b in results:
                text = _result_text(b.get("content"))
                tok = estimate_tokens(text)
                if b.get("is_error"):
                    w2["tokens"] += tok
                    w2["count"] += 1
                    if bucket == "main":
                        arrivals.append(("W2", tok, len(calls), epoch))
                    continue
                use = uses.get(b.get("tool_use_id"))
                if not use:
                    continue
                h = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
                prev = last_result.get(use)
                if prev and prev == (h, epoch):
                    w1["tokens"] += tok
                    w1["count"] += 1
                    if bucket == "main":
                        arrivals.append(("W1", tok, len(calls), epoch))
                last_result[use] = (h, epoch)
        elif d.get("type") == "assistant":
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                    sig = (str(b.get("name")), json.dumps(b.get("input"), ensure_ascii=False, sort_keys=True))
                    uses[b["id"]] = (ctxkey, sig)
            mid = str(m.get("id") or d.get("requestId"))
            u = m.get("usage") if isinstance(m.get("usage"), dict) else None
            if not u or mid in seen_msg:
                continue
            seen_msg.add(mid)
            inp, cr, cw = (int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if not inp + cr + cw:
                continue
            totals["input"] += inp
            totals["cache_read"] += cr
            totals["cache_write"] += cw
            by_ctx[bucket]["calls"] += 1
            by_ctx[bucket]["input"] += inp + cr + cw
            if bucket == "main":
                calls.append((inp + cr + cw, cr, cw, _ts(d.get("timestamp")), m.get("model"), epoch))
                if limit_calls is not None and len(calls) >= limit_calls:
                    break
    w6 = {"tokens": 0, "count": 0, "by_cause": {k: {"tokens": 0, "count": 0} for k, _ in GAPS + (("unknown", None),)}}
    for (pctx, _, _, pt, pm, _), (ctx, cr, cw, t, mdl, _) in zip(calls, calls[1:]):
        if ctx < pctx:  # the context shrank: compaction or a cleared session, new content
            continue
        missed = min(cw, pctx - cr)
        if missed > CHURN_TOLERANCE * pctx:
            w6["tokens"] += missed
            w6["count"] += 1
            if pm and mdl and pm != mdl:
                cause = "model_switch"
            elif pt is None or t is None:
                cause = "unknown"
            else:
                cause = next(k for k, lim in GAPS[1:] if t - pt < lim)
            w6["by_cause"][cause]["tokens"] += missed
            w6["by_cause"][cause]["count"] += 1
    # descriptive, not in the floor: a W1/W2 result stays in the context and is processed again
    # by every later main-chain call until the next compaction (that carry is W5's to judge)
    carried = {"W1": 0, "W2": 0}
    for cat, tok, pos, ep in arrivals:
        carried[cat] += tok * sum(1 for c in calls[pos:] if c[5] == ep)
    processed = totals["input"] + totals["cache_read"] + totals["cache_write"]
    price_total = sum(totals[k] * PRICE[k] for k in PRICE)
    # W1/W2 arrive as new context (written to cache on the next call) and need not have;
    # W6 tokens would have been read anyway, so only the write premium over a read is waste
    removable = w1["tokens"] + w2["tokens"]
    floor_price = removable * PRICE["cache_write"] + w6["tokens"] * (PRICE["cache_write"] - PRICE["cache_read"])
    return {
        "instructions": min(instructions, limit_instructions) if limit_instructions is not None else instructions,
        "calls": by_ctx["main"]["calls"] + by_ctx["side"]["calls"],  # calls that processed input
        "input_processed": processed,
        "input_parts": totals,
        "main": by_ctx["main"], "subagents": by_ctx["side"],
        "W1": w1, "W2": w2, "W6": w6,
        "carried_by_later_calls": carried,
        "removable_tokens": removable,
        "floor_price_units": floor_price,
        "price_total_units": price_total,
        "floor_pct_of_input": round(100 * removable / processed, 4) if processed else 0,
        "floor_pct_price_weighted": round(100 * floor_price / price_total, 2) if price_total else 0,
    }


def judge_source(source, limit_instructions: int | None = None, limit_calls: int | None = None) -> dict:
    """A transcript file (.jsonl, with its sub-agent transcripts when they sit beside it) or a
    list of saved event-API pages for one session."""
    if isinstance(source, (list, tuple)):
        return judge_lines(lines_from(list(source)), limit_instructions, limit_calls)
    return judge_lines(_with_subagents(source), limit_instructions, limit_calls)


def combine(per_session: dict) -> dict:
    keys = ("input_processed", "removable_tokens", "floor_price_units", "price_total_units", "calls")
    tot = {k: sum(s[k] for s in per_session.values()) for k in keys}
    tot["subagent_input"] = sum(s["subagents"]["input"] for s in per_session.values())
    cats = {c: {"tokens": sum(s[c]["tokens"] for s in per_session.values()),
                "count": sum(s[c]["count"] for s in per_session.values())} for c in ("W1", "W2", "W6")}
    tot["carried_by_later_calls"] = {c: sum(s["carried_by_later_calls"][c] for s in per_session.values()) for c in ("W1", "W2")}
    cats["W6"]["by_cause"] = {k: {x: sum(s["W6"]["by_cause"][k][x] for s in per_session.values()) for x in ("tokens", "count")}
                              for k in next(iter(per_session.values()))["W6"]["by_cause"]} if per_session else {}
    parts = {k: sum(s["input_parts"][k] for s in per_session.values()) for k in PRICE}
    # sensitivity of the cost view to which W6 re-writes count (descriptive; v1 counts all of them)
    if cats["W6"].get("by_cause") and tot["price_total_units"]:
        base = tot["removable_tokens"] * PRICE["cache_write"]
        prem = PRICE["cache_write"] - PRICE["cache_read"]
        bc = cats["W6"]["by_cause"]
        views = {"all_w6 (v1)": list(bc), "without_gap_over_1h": [k for k in bc if k != "gap_over_1h"],
                 "only_gap_under_5m": ["gap_under_5m"]}
        tot["sensitivity_pct_price_weighted"] = {
            v: round(100 * (base + prem * sum(bc[k]["tokens"] for k in ks)) / tot["price_total_units"], 2) for v, ks in views.items()}
    return {"schema": SCHEMA, "codebook": CODEBOOK, "tier": "T1 mechanical (floor)",
            "sessions": per_session, "total": {**tot, "input_parts": parts, **cats,
            "floor_pct_of_input": round(100 * tot["removable_tokens"] / tot["input_processed"], 4) if tot["input_processed"] else 0,
            "floor_pct_price_weighted": round(100 * tot["floor_price_units"] / tot["price_total_units"], 2) if tot["price_total_units"] else 0},
            "not_in_floor": {"W3": "rule tier, pending validation", "W4": "rule/judgment tier", "W5": "rule tier, pending validation",
                             "W7": "judgment tier", "W8": "judgment tier"}}
