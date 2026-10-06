import json

from pickaxetax.survey import events


def page(tmp_path, name, data, wrap=True):
    body = json.dumps({"ccr": {"data": data, "has_more": False}})
    if wrap:  # the harness saves a tool result as [{"type": "text", "text": ...}]
        body = json.dumps([{"type": "text", "text": "events:\n" + body}])
    p = tmp_path / name
    p.write_text(body)
    return str(p)


def ev(kind, uid, ts, message, parent=None):
    inner = {"uuid": uid, "timestamp": ts, "message": message}
    if parent:
        inner["parent_tool_use_id"] = parent
    return {kind: inner, "created_at": ts}


def call(mid, read, write=0):
    return {"id": mid, "role": "assistant", "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "cache_read_input_tokens": read, "cache_creation_input_tokens": write, "output_tokens": 1}}


def test_pages_dedupe_order_and_subagents(tmp_path):
    a = page(tmp_path, "a.json", [ev("assistant", "u2", "2026-01-01T00:00:02Z", call("m2", 200)),
                                  ev("user", "u1", "2026-01-01T00:00:01Z", {"role": "user", "content": "do it"})])
    b = page(tmp_path, "b.json", [ev("assistant", "u2", "2026-01-01T00:00:02Z", call("m2", 200)),
                                  ev("assistant", "u3", "2026-01-01T00:00:03Z", call("m3", 50), parent="toolu_x")], wrap=False)
    lines = events.lines_from([a, b])
    assert [l["type"] for l in lines] == ["user", "assistant", "assistant"]
    assert [l["isSidechain"] for l in lines] == [False, False, True]
    r = events.measure_pages([a, b])
    assert r["api_calls"] == 1 and r["subagents"]["api_calls"] == 1


def test_raw_control_characters_in_tool_output(tmp_path):
    # tool output can carry raw control characters that strict JSON rejects
    good = page(tmp_path, "c.json", [ev("user", "u1", "2026-01-01T00:00:01Z", {"role": "user", "content": "AxB"})])
    p = tmp_path / "c.json"
    p.write_text(p.read_text().replace("AxB", "A\\\\u0001B").replace("\\\\u0001", "\x01"))
    assert events.lines_from([good])[0]["message"]["content"] == "A\x01B"
