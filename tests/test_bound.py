import json
import math

from pickaxetax.agent import bound
from pickaxetax.agent.bound import Segment, analyze, calibrate, link, needed, read_trace
from pickaxetax.cli import main

from .test_agent import T


def session(tmp_path):
    """Four calls; a tool result is used again two calls after it arrived."""
    t = (T()
         .tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000)
         .result("r1", "def parse_settings_block(): pass " * 40)
         .call(1400, blocks=[{"type": "text", "text": "Looking at the file next."}])
         .call(1450, blocks=[{"type": "text", "text": "Okay, continuing."}])
         .call(1500, blocks=[{"type": "text", "text": "parse_settings_block needs a default."}]))
    return t.write(tmp_path / "s.jsonl")


def test_needed_per_gap_choice():
    s = Segment("tool_result", 100, 2, frozenset(), end=20, refs=[2, 3, 10])
    assert needed(s, 0) == 300  # present only where used
    assert needed(s, math.inf) == 900  # kept from first to last use
    assert needed(s, 200) == 300 + 0 + 200  # the 6-call gap is cheaper to re-fetch
    assert needed(Segment("x", 50, 1, frozenset(), end=1, refs=[]), 0) == 0


def test_lexical_reference_and_window(tmp_path):
    t = read_trace(session(tmp_path))
    link(t)
    assert len(t.contexts) == 4
    tr = next(s for s in t.segments if s.kind == "tool_result")
    assert tr.birth == 1 and tr.end == 4
    assert tr.refs == [1, 3]  # consumed at once, reused by the last answer, idle in between


def test_calibration_reconciles_with_measured_context(tmp_path):
    t = read_trace(session(tmp_path))
    calibrate(t)
    link(t)
    base = t.contexts[0]
    for k, ctx in enumerate(t.contexts):
        resident = sum(s.tokens for s in t.segments if s.birth <= k < s.end)
        assert abs(base + resident - ctx) < 1e-6


def test_compaction_ends_windows_and_shrink_is_applied(tmp_path):
    t = (T()
         .tool("r1", "Read", {"file_path": "/p/a.py"}, ctx_read=1000).result("r1", "alpha_unique_token " * 50)
         .call(2000)
         .call(1800)  # the harness cleared something: context shrank without a compaction
         .raw({"type": "system", "subtype": "compact_boundary"})
         .raw({"type": "user", "isCompactSummary": True, "message": {"role": "user", "content": "summary of work"}})
         .call(1200, blocks=[{"type": "text", "text": "alpha_unique_token again"}]))
    t = read_trace(t.write(tmp_path / "c.jsonl"))
    assert t.compactions == [3]
    calibrate(t)
    link(t)
    tr = next(s for s in t.segments if s.kind == "tool_result")
    assert tr.end == 3 and tr.refs == [1]  # the reuse after the compaction does not count
    base = t.contexts[0]
    for k, ctx in enumerate(t.contexts):
        assert abs(base + sum(s.tokens for s in t.segments if s.birth <= k < s.end) - ctx) < 1e-6


def test_synthetic_messages_are_not_calls(tmp_path):
    t = T().call(1000)
    t.raw({"type": "assistant", "message": {"id": "err", "content": [{"type": "text", "text": "API Error"}],
                                            "usage": {"input_tokens": 0, "output_tokens": 0}}})
    t.call(1100)
    tr = read_trace(t.write(tmp_path / "e.jsonl"))
    assert tr.contexts == [1005, 1105]


def test_report_shape_and_ordering(tmp_path):
    r = analyze(session(tmp_path))
    p = r["policies"]
    assert set(p) == {"P=0", "P=1000", "P=10000", "P=inf"}
    # a costlier re-fetch can only mean keeping more
    assert p["P=0"]["bound_input"] <= p["P=1000"]["bound_input"] <= p["P=10000"]["bound_input"] <= p["P=inf"]["bound_input"]
    assert p["P=inf"]["bound_input"] <= r["measured_input"]
    assert r["pinned_input"] <= r["measured_input"]
    m = bound.merge([r, r])
    assert m["measured_input"] == 2 * r["measured_input"]
    assert m["policies"]["P=0"]["avoidable_pct"] == r["policies"]["P=0"]["avoidable_pct"]


def test_cli_bound(tmp_path, capsys):
    path = session(tmp_path)
    assert main(["agent", "bound", path]) == 0
    out = capsys.readouterr().out
    assert "drop after last use" in out and "oracle, free re-fetch" in out
    assert main(["agent", "bound", path, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["sessions"] == 1 and "config_loader" not in json.dumps(data)  # aggregates only
