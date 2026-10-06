"""Survey layer 2: what happened inside a Claude Code session, as numbers only.

Run inside the environment that holds the session's transcript:

    python3 measure_session.py            # every top-level transcript in ~/.claude/projects
    python3 measure_session.py FILE.jsonl

Prints one compact JSON object per transcript. Standard library only. It never
prints text, file paths, commands or ids: only counts, token totals, tool
names (MCP tools collapsed to "mcp"), model names and a sampled context curve.
"""

import glob
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime

IDLE_GAP_S = 30 * 60  # gaps longer than this do not count as active time
CURVE_POINTS = 40


def _ts(d):
    try:
        return datetime.fromisoformat(str(d.get("timestamp")).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def measure(path, subagent=False):
    seen, skipped = {}, set()
    calls = []  # (context, output, model)
    side_calls = 0
    tools, models, types = Counter(), Counter(), Counter()
    prompts = compactions = tool_errors = images = 0
    calls_at_prompt = []
    stamps = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            types[str(d.get("type"))] += 1
            t = _ts(d)
            if t:
                stamps.append(t)
            if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                compactions += 1
                continue
            m = d.get("message")
            if not isinstance(m, dict):
                continue
            content = m.get("content")
            if d.get("type") == "assistant":
                mid = str(m.get("id") or d.get("requestId") or d.get("uuid"))
                if d.get("isSidechain") and not subagent:
                    if mid not in seen and isinstance(m.get("usage"), dict):
                        side_calls += 1
                    seen[mid] = -1
                    continue
                if mid not in seen and mid not in skipped:
                    u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
                    ctx = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                    if not ctx:
                        skipped.add(mid)
                    else:
                        seen[mid] = len(calls)
                        calls.append((ctx, int(u.get("output_tokens") or 0), int(u.get("cache_read_input_tokens") or 0),
                                      int(u.get("cache_creation_input_tokens") or 0)))
                        models[str(m.get("model") or "?")] += 1
                for b in content if isinstance(content, list) else []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        name = str(b.get("name") or "?")
                        tools["mcp" if name.startswith("mcp__") else name] += 1
            elif d.get("type") == "user" and (subagent or not d.get("isSidechain")):
                if d.get("isCompactSummary") or d.get("isMeta"):
                    continue
                blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
                has_result = False
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        has_result = True
                        if b.get("is_error"):
                            tool_errors += 1
                        c = b.get("content")
                        if isinstance(c, list):
                            images += sum(1 for x in c if isinstance(x, dict) and x.get("type") == "image")
                    elif b.get("type") == "image":
                        images += 1
                text = " ".join(str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("type") == "text")
                if not has_result and text.strip() and "<system-reminder>" not in text[:200] and not text.lstrip().startswith("<"):
                    prompts += 1
                    calls_at_prompt.append(len(calls))
    ctxs = [c[0] for c in calls]
    n = len(ctxs)
    # calls and input per user instruction
    bounds = calls_at_prompt + [n]
    per_calls = [b - a for a, b in zip(bounds, bounds[1:]) if b > a]
    per_input = [sum(ctxs[a:b]) for a, b in zip(bounds, bounds[1:]) if b > a]
    stamps.sort()
    active = sum(min(b - a, IDLE_GAP_S) for a, b in zip(stamps, stamps[1:]) if b - a <= IDLE_GAP_S)
    curve = [ctxs[min(n - 1, round(i * (n - 1) / (CURVE_POINTS - 1)))] for i in range(CURVE_POINTS)] if n else []
    q = lambda xs: [round(v) for v in statistics.quantiles(xs, n=4, method="inclusive")] if len(xs) > 1 else xs
    return {
        "schema": "pickaxetax.survey.session.v1",
        "lines": sum(types.values()),
        "event_types": dict(types.most_common(12)),
        "api_calls": n,
        "subagent_calls": side_calls,
        "user_instructions": prompts,
        "compactions": compactions,
        "tokens": {"input_processed": sum(ctxs), "cache_read": sum(c[2] for c in calls),
                   "cache_write": sum(c[3] for c in calls), "output": sum(c[1] for c in calls)},
        "context": {"first": ctxs[0] if n else 0, "peak": max(ctxs) if n else 0,
                    "quartiles": q(ctxs), "curve_40": curve},
        "per_instruction": {"calls_quartiles": q(per_calls), "calls_max": max(per_calls) if per_calls else 0,
                            "input_quartiles": q(per_input), "input_max": max(per_input) if per_input else 0,
                            "calls": per_calls, "input": per_input},  # one entry per instruction, in order
        "input_by_context": {f"ge_{k}k_pct": round(100 * sum(c for c in ctxs if c >= k * 1000) / sum(ctxs), 1) if ctxs else 0
                             for k in (200, 400, 600)},
        "tools": dict(tools.most_common(25)),
        "tool_calls": sum(tools.values()),
        "tool_errors": tool_errors,
        "images": images,
        "models": dict(models),
        "span_hours": round((stamps[-1] - stamps[0]) / 3600, 2) if stamps else 0,
        "active_hours": round(active / 3600, 2),
    }


def with_subagents(path):
    """The session plus its subagents, whose transcripts live in <session>/subagents/*.jsonl."""
    r = measure(path)
    subs = [measure(p, subagent=True) for p in glob.glob(os.path.join(path[:-6], "subagents", "*.jsonl"))]
    r["subagents"] = {"count": len(subs), "api_calls": sum(s["api_calls"] for s in subs),
                      "tokens": {k: sum(s["tokens"][k] for s in subs) for k in r["tokens"]},
                      "models": dict(sum((Counter(s["models"]) for s in subs), Counter()))}
    return r


def main(argv):
    files = argv or sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getsize, reverse=True)
    out = [with_subagents(p) for p in files]
    print(json.dumps(out, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1:])
