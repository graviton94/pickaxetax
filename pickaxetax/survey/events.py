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
                            "isSidechain": bool(inner.get("parent_tool_use_id")), "subtype": inner.get("subtype"),
                            "isMeta": inner.get("isMeta") or inner.get("isSynthetic"), "isCompactSummary": inner.get("isCompactSummary"),
                            "requestId": inner.get("request_id")}
                    events[uid] = (str(line["timestamp"]), line)
    return [l for _, l in sorted(events.values(), key=lambda x: x[0])]


def _measure_lines(lines, include_series=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
    try:
        return measure(f.name, include_series=include_series)
    finally:
        os.unlink(f.name)


def measure_pages(paths, include_series=False, subagents=True):
    """Measure a session from saved events-API pages. Sub-agent (sidechain) calls are
    measured separately under "subagents", as local transcripts are (`with_subagents`)."""
    lines = list(lines_from(paths))
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
