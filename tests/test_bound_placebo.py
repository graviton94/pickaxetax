"""The time-mirror placebo option of bound.link (cycle E5's "Tmirror"): reuse must beat the
session's own calls made before the segment existed. The default (lexical-v1) must not move."""

import json
import math

import pytest

from pickaxetax.agent import bound
from pickaxetax.agent.bound import Segment, Trace, analyze, link, read_trace
from pickaxetax.cli import main

from .test_agent import T

N = 20  # calls per synthetic trace


def trace(segments, uses):
    """N calls; ``uses`` maps call index -> distinctive tokens its output contained. Every token is
    used by at most three outputs, so none of them becomes session-common."""
    t = Trace(contexts=[1000] * N, outputs=[set() for _ in range(N)])
    for k, toks in uses.items():
        t.outputs[k].update(toks)
    t.segments = segments
    return t


def seg(kind, birth, terms):
    return Segment(kind, 100, birth, frozenset(terms))


def toks(prefix, n):
    return [f"{prefix}_token_{i}" for i in range(n)]


def test_unknown_placebo_is_rejected():
    with pytest.raises(ValueError):
        link(trace([], {}), placebo="shuffle")


def test_words_only_after_the_segment_are_kept():
    # tool result born at 10 (origin 9): window calls 11..19 (W = 9), mirror calls 0..8
    a = toks("after", 6)
    before = toks("before", 1)
    s = seg("tool_result", 10, a + before)
    t = trace([s], {12: {a[0]}, 13: {a[1]}, 14: {a[2]}, 15: {a[3]}, 17: {a[4]}, 19: {a[5]}, 3: {before[0]}})
    stats = link(t, placebo="mirror")
    # p = 1/9, threshold 1 + 2 sqrt(9 * 1/9 * 8/9) = 2.9 < 6 observed
    assert s.refs == [10, 12, 13, 14, 15, 17, 19]
    assert stats == {"reused": 1, "kept": 1, "dropped": 0, "fallback": 0}


def test_words_equally_before_and_after_are_dropped():
    a, b = toks("after", 3), toks("before", 3)
    s = seg("tool_result", 10, a + b)
    t = trace([s], {12: {a[0]}, 14: {a[1]}, 16: {a[2]}, 2: {b[0]}, 4: {b[1]}, 6: {b[2]}})
    link(t)
    assert s.refs == [10, 12, 14, 16]  # lexical-v1 sees three reuses
    stats = link(t, placebo="mirror")
    # p = 3/9, threshold 3 + 2 sqrt(2) = 5.8 > 3 observed: topic, not need; birth stays
    assert s.refs == [10]
    assert stats == {"reused": 1, "kept": 0, "dropped": 1, "fallback": 0}


def test_mirror_is_distance_matched_and_truncated_at_session_start():
    # prompt born at 15 (origin 15): window 16..19 (W = 4), mirror calls 11..14 only
    a = toks("after", 3)
    far, near = toks("far", 4), toks("near", 1)
    s = seg("user_prompt", 15, a + far + near)
    uses = {16: {a[0]}, 17: {a[1]}, 18: {a[2]}, 2: {far[0]}, 4: {far[1]}, 6: {far[2]}, 8: {far[3]}, 13: {near[0]}}
    link(trace([s], uses), placebo="mirror")
    # far-before uses are outside the mirror: p = 1/4, threshold 1 + 2 * 0.87 = 2.7 < 3 observed
    assert s.refs == [15, 16, 17, 18]
    # an output segment's mirror ends before its origin call (the call that produced it)
    o = seg("assistant_text", 2, a)  # origin 1: window 3..19 (W = 17), mirror truncated to call 0
    t = trace([o], {0: {a[0]}, 1: {a[1]}, 5: {a[0], a[1]}})
    link(t, placebo="mirror")
    assert o.refs == [2]  # p = 1/1: nothing can beat a mirror that always hits


def test_no_history_falls_back_to_the_kinds_pooled_mirror_rate():
    a = toks("first", 5)
    b = toks("second", 9)
    first = seg("user_prompt", 0, a)  # origin 0: no call before it, no mirror
    second = seg("user_prompt", 10, b)  # mirror calls 1..9, every one of them hits
    uses = {11: {a[0]}, 12: {a[1]}, 13: {a[2]}, 14: {a[3]}, 15: {a[4]}}
    uses.update({k: {b[k - 1]} for k in range(1, 10)})
    t = trace([first, second], uses)
    stats = link(t, placebo="mirror")
    # first: 5 uses in W = 19 against the user prompts' pooled rate 9/9 = 1 -> dropped
    assert first.refs == [0]
    assert stats["fallback"] == 1 and stats["dropped"] == 1
    # without any mirror for its kind the rate is 0, and observed use is kept
    alone = seg("user_prompt", 0, a)
    other = seg("tool_result", 10, b)
    stats = link(trace([alone, other], uses), placebo="mirror")
    assert alone.refs == [0, 11, 12, 13, 14, 15]
    assert stats["fallback"] == 1


def test_min_shared_applies_to_the_mirror_too():
    a = toks("after", 4)
    s = seg("tool_result", 10, a)
    uses = {12: {a[0], a[1]}, 14: {a[2], a[3]}, 4: {a[0]}, 5: {a[1]}, 6: {a[2]}, 7: {a[3]}}
    link(t := trace([s], uses), min_shared=1, placebo="mirror")
    assert s.refs == [10]  # 2 of 9 vs 4 of 9 mirrored calls share one token
    link(t, min_shared=2, placebo="mirror")
    assert s.refs == [10, 12, 14]  # no mirrored call shares two


def session(tmp_path):
    t = (T()
         .tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000)
         .result("r1", "def parse_settings_block(): pass " * 40)
         .call(1400, blocks=[{"type": "text", "text": "Looking at the file next."}])
         .call(1450, blocks=[{"type": "text", "text": "Okay, continuing with load_defaults_table."}])
         .call(1500, blocks=[{"type": "text", "text": "parse_settings_block needs a default."}])
         .call(1550, blocks=[{"type": "text", "text": "load_defaults_table and parse_settings_block done."}]))
    return t.write(tmp_path / "s.jsonl")


def test_default_path_equals_explicit_none(tmp_path):
    path = session(tmp_path)
    t1, t2 = read_trace(path), read_trace(path)
    assert link(t1) is None and link(t2, placebo=None) is None
    assert [(s.end, s.refs) for s in t1.segments] == [(s.end, s.refs) for s in t2.segments]
    default, explicit = analyze(path), analyze(path, placebo=None)
    assert json.dumps(default) == json.dumps(explicit)
    assert "method" not in default and "placebo" not in default
    assert "method" not in bound.merge([default]) and bound.export([default])["method"] == "lexical-v1"
    # the placebo can only remove later refs, never add any or touch windows
    t3 = read_trace(path)
    link(t3, placebo="mirror")
    for a, b in zip(t1.segments, t3.segments):
        assert a.end == b.end and b.refs[:1] == a.refs[:1] and set(b.refs) <= set(a.refs)


def test_method_tag_is_reported(tmp_path, capsys):
    path = session(tmp_path)
    assert bound.method_tag() == "lexical-v1" and bound.method_tag("mirror") == "lexical-v1+mirror-2sigma"
    r = analyze(path, placebo="mirror")
    assert r["method"] == "lexical-v1+mirror-2sigma" and set(r["placebo"]) == {"reused", "kept", "dropped", "fallback"}
    assert r["placebo"]["reused"] >= 1
    m = bound.merge([r, r])
    assert m["method"] == r["method"] and m["placebo"]["reused"] == 2 * r["placebo"]["reused"]
    assert bound.export([r])["method"] == "lexical-v1+mirror-2sigma"
    with pytest.raises(ValueError):
        bound.merge([r, analyze(path)])
    p = r["policies"]
    assert p["P=0"]["bound_input"] <= p["P=1000"]["bound_input"] <= p["P=inf"]["bound_input"] <= r["measured_input"]
    assert analyze(path)["policies"]["P=inf"]["bound_input"] >= p["P=inf"]["bound_input"]

    assert main(["agent", "bound", path]) == 0
    assert "method" not in capsys.readouterr().out
    assert main(["agent", "bound", path, "--placebo", "mirror"]) == 0
    out = capsys.readouterr().out
    assert "method lexical-v1+mirror-2sigma" in out and "drop after last use" in out
    assert main(["agent", "bound", path, "--placebo", "mirror", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["method"] == "lexical-v1+mirror-2sigma" and "config_loader" not in json.dumps(data)
    assert main(["agent", "bound", path, "--placebo", "mirror", "--export"]) == 2
    assert math.isfinite(data["policies"]["P=inf"]["avoidable_pct"])


def test_rule_tier_machine_labels_take_the_placebo(tmp_path):
    import pytest
    from pickaxetax.survey import labeling, rules
    from tests.test_agent import T
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read the loader"}})
    t.tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000).result("r1", "def parse_settings_block(): pass " * 300)
    t.call(5000, blocks=[{"type": "text", "text": "parse_settings_block found."}])
    t.raw({"type": "user", "message": {"role": "user", "content": "now write the release notes"}})
    t.call(5100, blocks=[{"type": "text", "text": "Release notes drafted."}])
    lines = [json.loads(json.dumps(l)) for l in t.lines]
    assert rules.detect(lines)["instructions"] == rules.detect(lines, "mirror")["instructions"]
    with pytest.raises(ValueError):
        labeling.machine_labels({"items": [], "sha256": "x"}, {"S01": lines}, tier="t1", placebo="mirror")
