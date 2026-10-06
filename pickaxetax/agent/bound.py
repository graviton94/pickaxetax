"""Offline-optimal context bound: how far was a session from the least context it needed?

Every API call of a coding agent re-processes everything resident in its context.
This module asks what an oracle that knows the future would have kept. The model
is described in ``research/belady-bound.md``. In short:

* the context of call *k* is a fixed base (system prompt, tools) plus *segments*:
  user prompts, assistant text, tool inputs, tool results, harness reminders;
* segment *s* has ``n`` tokens and is resident from call ``birth`` until the next
  compaction or the end of the session (``end``, exclusive);
* *s* is **needed** at ``birth`` (the next call consumes it) and at every later
  call whose output reuses at least ``min_shared`` of its distinctive tokens;
* the oracle keeps *s* only where it is needed. Across a gap between two uses it
  either keeps *s* (``n`` per call in between) or drops and re-materializes it
  (cost ``P``), whichever is cheaper. Segments are independent and there is no
  capacity limit, so this per-gap choice is exactly optimal for the model.

``P = 0`` is the pure lower bound (an oracle that prefetches for free). ``P = inf``
never re-fetches: it only drops a segment after its last use, so it needs no
re-materialization at all and is the most defensible headline figure.

Reference detection is lexical. It misses use that leaves no verbatim trace
(reading code to understand it), which makes the bound optimistic, and it can
see coincidental reuse, which makes it pessimistic. ``min_shared`` and the
common-token cut-off are exposed so both directions can be tested.

Only aggregates leave this module; segment text is never stored.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from ..tokens import estimate_tokens

# distinctive tokens: identifiers/paths, long Hangul words, long numbers
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_./\-]{5,}|[가-힣]{3,}|\d{4,}")
DEFAULT_PENALTIES = (0, 1_000, 10_000, math.inf)


@dataclass
class Segment:
    kind: str
    tokens: int
    birth: int
    terms: frozenset
    end: int = -1
    refs: list[int] = field(default_factory=list)
    text: str = field(default="", repr=False)  # kept only for local validation labeling (keep_text=True)


@dataclass
class Trace:
    contexts: list[int] = field(default_factory=list)  # measured input processed per call
    outputs: list[set] = field(default_factory=list)  # distinctive tokens each call produced
    segments: list[Segment] = field(default_factory=list)
    compactions: list[int] = field(default_factory=list)
    written_tokens: int = 0  # Write content + Edit replacements: what persisted to disk


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def read_trace(path: str, keep_text: bool = False) -> Trace:
    """Parse a Claude Code transcript into calls, outputs and context segments."""
    t = Trace()
    call_of: dict[str, int] = {}
    skipped: set[str] = set()

    def add(kind: str, text: str, birth: int) -> None:
        n = estimate_tokens(text)
        if n:
            t.segments.append(Segment(kind, n, birth, frozenset(TOKEN_RE.findall(text)), text=text if keep_text else ""))

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("isSidechain"):
                continue
            if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                if not t.compactions or t.compactions[-1] != len(t.contexts):
                    t.compactions.append(len(t.contexts))
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if d.get("type") == "assistant":
                mid = str(msg.get("id") or d.get("requestId") or d.get("uuid"))
                if mid in skipped:
                    continue
                if mid not in call_of:
                    u = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                    ctx = (int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
                           + int(u.get("cache_creation_input_tokens") or 0))
                    if not ctx:  # synthetic message (API error, interruption): no model call happened
                        skipped.add(mid)
                        continue
                    call_of[mid] = len(t.contexts)
                    t.contexts.append(ctx)
                    t.outputs.append(set())
                k = call_of[mid]
                for b in content if isinstance(content, list) else []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text":
                        s, kind = str(b.get("text", "")), "assistant_text"
                    elif b.get("type") == "tool_use":
                        inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                        s, kind = json.dumps(inp, ensure_ascii=False), "tool_input"
                        if b.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                            kind = "persisted_write"
                            t.written_tokens += estimate_tokens(str(inp.get("content") or inp.get("new_string") or inp.get("new_source") or ""))
                    else:
                        continue  # thinking blocks are left to the unmodeled residual
                    t.outputs[k].update(TOKEN_RE.findall(s))
                    add(kind, s, k + 1)
            elif d.get("type") == "user":
                birth = len(t.contexts)
                if d.get("isCompactSummary"):
                    add("compact_summary", _text(content), birth)
                    continue
                for b in content if isinstance(content, list) else [{"type": "text", "text": content}]:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        add("tool_result", _text(b.get("content")), birth)
                    elif b.get("type") == "text":
                        s = str(b.get("text", ""))
                        add("harness" if d.get("isMeta") or "<system-reminder>" in s else "user_prompt", s, birth)
    return t


def link(t: Trace, min_shared: int = 1, common_frac: float = 0.02) -> None:
    """Set each segment's residency window and the calls that needed it."""
    n_calls = len(t.contexts)
    bounds = sorted(set(t.compactions)) + [n_calls]
    df = Counter(tok for out in t.outputs for tok in out)
    active = sum(1 for out in t.outputs if out) or 1
    common = {tok for tok, c in df.items() if c > max(3, common_frac * active)}  # floor for short sessions
    used_at: dict[str, list[int]] = defaultdict(list)
    for k, out in enumerate(t.outputs):
        for tok in out - common:
            used_at[tok].append(k)
    for s in t.segments:
        s.end = next(b for b in bounds if b > s.birth) if s.birth < n_calls else s.birth
        if s.birth >= s.end:
            s.refs = []
            continue
        if s.kind == "unattributed":  # nothing visible to match: pinned for its whole window
            s.refs = list(range(s.birth, s.end))
            continue
        hits = Counter(k for tok in s.terms - common for k in used_at.get(tok, ()) if s.birth < k < s.end)
        s.refs = [s.birth] + sorted(k for k, c in hits.items() if c >= min_shared)


def calibrate(t: Trace, min_tokens: int = 2_000) -> float:
    """Rescale segments so they add up to the context growth the API measured.

    The text estimator undercounts the provider's tokenizer, and some context is
    invisible in the transcript (thinking, harness framing). The tokenizer factor is
    the median measured/estimated growth over calls that added at least
    ``min_tokens`` estimated tokens, where invisible overhead is small. Each call's
    visible segments are scaled by that factor (never past the measured growth),
    and whatever growth is left becomes an ``unattributed`` segment that the
    oracle must keep for its whole window: it can never be dropped.
    """
    n_calls = len(t.contexts)
    born: dict[int, list[Segment]] = defaultdict(list)
    for s in t.segments:
        born[s.birth].append(s)
    est = {k: sum(s.tokens for s in segs) for k, segs in born.items()}
    restarts = {0, *t.compactions}
    ratios = sorted((t.contexts[k] - t.contexts[k - 1]) / est[k] for k in range(1, n_calls)
                    if k not in restarts and est.get(k, 0) >= min_tokens and t.contexts[k] > t.contexts[k - 1])
    factor = ratios[len(ratios) // 2] if len(ratios) >= 5 else 1.0
    for k in range(n_calls):
        e = est.get(k, 0)
        if k == 0:
            grown, scale = 0, 0.0  # the first call's context is the fixed base, first prompt included
        else:
            # growth since the previous call; after a compaction, re-base on the call-0 floor
            grown = t.contexts[k] - (t.contexts[0] if k in restarts else t.contexts[k - 1])
            scale = min(factor, grown / e) if e and grown > 0 else factor
        for s in born.get(k, ()):
            s.tokens = s.tokens * scale
        rest = grown - e * scale
        if rest:
            # a negative rest is context the harness removed without a compaction (e.g. a
            # cleared tool result); it is applied to the actual and the oracle alike
            t.segments.append(Segment("unattributed", rest, k, frozenset()))
    return factor


def needed(s: Segment, penalty: float) -> float:
    """Token-calls the oracle spends on one segment for a given re-fetch cost."""
    if not s.refs:
        return 0.0
    cost = s.tokens * len(s.refs)
    for a, b in zip(s.refs, s.refs[1:]):
        cost += min(s.tokens * (b - a - 1), penalty)
    return cost


def bound(t: Trace, penalties=DEFAULT_PENALTIES) -> dict:
    """Aggregate report. All figures are input tokens processed (token-calls)."""
    measured = sum(t.contexts)
    resident = sum(s.tokens * max(0, s.end - s.birth) for s in t.segments)
    out: dict = {
        "api_calls": len(t.contexts),
        "compactions": len(t.compactions),
        "segments": len(t.segments),
        "measured_input": measured,
        "modeled_resident": round(resident),
        "unmodeled_input": round(measured - resident),
        "pinned_input": round(measured - resident + sum(s.tokens * max(0, s.end - s.birth)
                                                         for s in t.segments if s.kind == "unattributed")),
        "written_tokens": t.written_tokens,
        "policies": {},
        "by_kind": {},
    }
    for p in penalties:
        need = sum(needed(s, p) for s in t.segments)
        saved = resident - need
        out["policies"][_label(p)] = {
            "needed_resident": round(need),
            "bound_input": round(measured - saved),
            "avoidable_pct": round(100 * saved / measured, 1) if measured else 0.0,
        }
    kinds: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for s in t.segments:
        k = kinds[s.kind]
        k[0] += s.tokens
        k[1] += s.tokens * max(0, s.end - s.birth)
        k[2] += needed(s, 0)
        k[3] += needed(s, math.inf)
    for name, (tok, res, n0, ninf) in sorted(kinds.items(), key=lambda kv: -kv[1][1]):
        out["by_kind"][name] = {
            "tokens": int(tok),
            "resident": int(res),
            "share_of_resident_pct": round(100 * res / resident, 1) if resident else 0.0,
            "dead_after_last_use_pct": round(100 * (res - ninf) / res, 1) + 0.0 if res else 0.0,  # no "-0.0"
            "unneeded_pct": round(100 * (res - n0) / res, 1) + 0.0 if res else 0.0,
        }
    return out


def merge(reports: list[dict]) -> dict:
    """Sum per-session reports; percentages are recomputed from the sums."""
    m: dict = {"sessions": len(reports), "policies": {}, "by_kind": {}}
    for key in ("api_calls", "compactions", "segments", "measured_input", "modeled_resident",
                "unmodeled_input", "pinned_input", "written_tokens"):
        m[key] = sum(r[key] for r in reports)
    measured = m["measured_input"]
    for label in reports[0]["policies"] if reports else ():
        need = sum(r["policies"][label]["needed_resident"] for r in reports)
        b = sum(r["policies"][label]["bound_input"] for r in reports)
        m["policies"][label] = {"needed_resident": need, "bound_input": b,
                                "avoidable_pct": round(100 * (measured - b) / measured, 1) if measured else 0.0}
    kinds: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for r in reports:
        for name, k in r["by_kind"].items():
            acc = kinds[name]
            acc[0] += k["tokens"]
            acc[1] += k["resident"]
            acc[2] += k["resident"] * k["dead_after_last_use_pct"] / 100
            acc[3] += k["resident"] * k["unneeded_pct"] / 100
    total = m["modeled_resident"]
    for name, (tok, res, dead, unneeded) in sorted(kinds.items(), key=lambda kv: -kv[1][1]):
        m["by_kind"][name] = {
            "tokens": int(tok),
            "resident": int(res),
            "share_of_resident_pct": round(100 * res / total, 1) if total else 0.0,
            "dead_after_last_use_pct": round(100 * dead / res, 1) if res else 0.0,
            "unneeded_pct": round(100 * unneeded / res, 1) if res else 0.0,
        }
    return m


METHOD = "lexical-v1"  # bump when detection or calibration changes, so results stay comparable
PCT_KEYS = {"P=0": "P0", "P=1000": "P1000", "P=10000": "P10000", "P=inf": "Pinf"}
MAX_SESSIONS = 200


def export(reports: list[dict]) -> dict:
    """Anonymous contribution block: counts and percentages only, one row per session."""
    m = merge(reports)
    factors = sorted(r["tokenizer_factor"] or 1.0 for r in reports)
    rows = [[r["api_calls"], r["measured_input"],
             round(100 * r["pinned_input"] / r["measured_input"], 1) if r["measured_input"] else 0.0,
             *(r["policies"][k]["avoidable_pct"] for k in PCT_KEYS)] for r in reports[:MAX_SESSIONS]]
    return {
        "method": METHOD,
        "sessions": m["sessions"],
        "api_calls": m["api_calls"],
        "measured_input": m["measured_input"],
        "pinned_input": m["pinned_input"],
        "written_tokens": m["written_tokens"],
        "tokenizer_factor": factors[len(factors) // 2] if factors else 1.0,
        "avoidable_pct": {short: m["policies"][k]["avoidable_pct"] for k, short in PCT_KEYS.items()},
        "per_session": rows,
    }


def _label(p: float) -> str:
    return "P=inf" if p == math.inf else f"P={int(p)}"


def analyze(path: str, min_shared: int = 1, common_frac: float = 0.02, penalties=DEFAULT_PENALTIES,
            calibrated: bool = True) -> dict:
    t = read_trace(path)
    factor = calibrate(t) if calibrated else None
    link(t, min_shared, common_frac)
    out = bound(t, penalties)
    out["tokenizer_factor"] = round(factor, 2) if factor else None
    return out
