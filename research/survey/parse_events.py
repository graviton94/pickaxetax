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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure_session import measure  # noqa: E402

KINDS = ("assistant", "user", "system")


def _pages(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    try:
        obj = json.loads(raw)
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
    dec = json.JSONDecoder()
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


def main(argv):
    lines = lines_from(argv)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
    r = measure(f.name)
    os.unlink(f.name)
    r["source"] = "events_api"
    r["pages"] = len(argv)
    print(json.dumps(r, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1:])
