"""Survey layer 2 from the remote-session events API instead of a local transcript.

    python3 parse_events.py PAGE.json [PAGE.json ...]

Each PAGE.json is one saved `list_events` result (the tool's JSON text, or the
array the harness persists with a {"type": "text", "text": ...} wrapper). Events
are de-duplicated by uuid, ordered by time, rewritten as transcript lines and
measured with measure_session.py, so both sources give the same schema.
Numbers only, as in measure_session.py.
"""

import json
import os
import sys
import tempfile

from .measure import measure

KINDS = ("assistant", "user", "system")


def _pages(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    try:
        obj = json.loads(raw, strict=False)  # tool output may hold raw control characters
    except ValueError:
        obj = None
    texts = []
    if isinstance(obj, list):
        texts = [b.get("text", "") for b in obj if isinstance(b, dict)]
    elif isinstance(obj, dict):
        yield obj
        return
    else:
        texts = [raw]
    dec = json.JSONDecoder(strict=False)
    for t in texts:
        start = t.find('{"ccr"')
        if start >= 0:  # raw_decode stops where the object ends, ignoring braces inside strings
            yield dec.raw_decode(t[start:])[0]


def lines_from(paths):
    events = {}
    for p in paths:
        for page in _pages(p):
            for ev in (page.get("ccr") or {}).get("data", []):
                for kind in KINDS:
                    if kind not in ev:
                        continue
                    inner = ev[kind]
                    inner = inner.get("internal_anthropic_catchall", inner) if isinstance(inner, dict) else {}
                    uid = inner.get("uuid") or ev[kind].get("uuid") or f"{ev.get('created_at')}-{kind}-{len(events)}"
                    line = {"type": kind, "message": inner.get("message"), "timestamp": inner.get("timestamp") or ev.get("created_at"),
                            "isSidechain": bool(inner.get("parent_tool_use_id")), "agentId": inner.get("parent_tool_use_id"),
                            "subtype": inner.get("subtype"),
                            "isMeta": inner.get("isMeta") or inner.get("isSynthetic"), "isCompactSummary": inner.get("isCompactSummary"),
                            "requestId": inner.get("request_id")}
                    events[uid] = (str(line["timestamp"]), line)
    return [l for _, l in sorted(events.values(), key=lambda x: _when(x[0]))]


def _when(ts: str):
    """Sort key: parsed time, so mixed precisions (…07.840077Z, …08.3Z) order correctly."""
    from datetime import datetime
    try:
        return (0, datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp(), ts)
    except ValueError:
        return (1, 0.0, ts)


def _is_instruction(d):
    """A real user message on the main chain (the rule `measure` and `judge` use)."""
    m = d.get("message")
    if d.get("type") != "user" or not isinstance(m, dict) or d.get("isSidechain") or d.get("isMeta") or d.get("isCompactSummary"):
        return False
    content = m.get("content")
    blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
        return False
    text = " ".join(str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("type") == "text")
    return bool(text.strip()) and "<system-reminder>" not in text[:200] and not text.lstrip().startswith("<")


def cut(lines, limit_calls=None, limit_instructions=None):
    """The lines up to a snapshot: stop before the main chain's (limit_calls+1)-th API call or
    the (limit_instructions+1)-th instruction, for a session that kept going after it was measured."""
    out, calls, instr = [], set(), 0
    for d in lines:
        if limit_instructions is not None and _is_instruction(d):
            instr += 1
            if instr > limit_instructions:
                break
        m = d.get("message")
        if limit_calls is not None and d.get("type") == "assistant" and not d.get("isSidechain") and isinstance(m, dict):
            u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
            mid = str(m.get("id") or d.get("requestId"))
            if mid not in calls and any(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")):
                if len(calls) >= limit_calls:
                    break
                calls.add(mid)
        out.append(d)
    return out


def _measure_lines(lines, include_series=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
    try:
        return measure(f.name, include_series=include_series)
    finally:
        os.unlink(f.name)


def measure_pages(paths, include_series=False, subagents=True, limit_calls=None, limit_instructions=None):
    """Measure a session from saved events-API pages. Sub-agent (sidechain) calls are
    measured separately under "subagents", as local transcripts are (`with_subagents`).
    limit_calls / limit_instructions cut the session at a snapshot (see `cut`)."""
    lines = cut(lines_from(paths), limit_calls, limit_instructions)
    r = _measure_lines(lines, include_series)
    side = [{**l, "isSidechain": False} for l in lines if l.get("isSidechain")]
    if subagents and side:
        s = _measure_lines(side)
        r["subagents"] = {"api_calls": s["api_calls"], "tokens": s["tokens"], "user_instructions": 0}
    r["source"] = "events_api"
    r["pages"] = len(paths)
    return r


def main(argv):
    print(json.dumps(measure_pages(argv), separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1:])
