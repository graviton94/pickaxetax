"""Regressions for the third independent review (research/phase2/log.md, cycle E9)."""

import json

import pytest

from pickaxetax.agent.bound import Segment, Trace, link, read_trace_lines
from pickaxetax.cli import main
from pickaxetax.survey import compare, rules
from pickaxetax.survey.dataset import build

N = 20


def trace(segments, uses):
    t = Trace(contexts=[1000] * N, outputs=[set() for _ in range(N)])
    for k, toks in uses.items():
        t.outputs[k].update(toks)
    t.segments = segments
    return t


def seg(kind, birth, terms):
    return Segment(kind, 100, birth, frozenset(terms))


def toks(prefix, n):
    return [f"{prefix}_token_{i}" for i in range(n)]


# --- bound._mirror_test: a tool result born at call 0 has origin -1 ---------------------------

def test_tool_result_born_at_call_0_has_no_mirror_and_uses_the_pooled_rate():
    """A tool result born at call 0 (a transcript that starts with a tool result) has origin -1,
    so no call precedes it: per the docstring it must use the kind's pooled mirror rate and be
    counted as a fallback. Today ``avail = o - lo = -1 - 0 = -1`` is truthy, so p = 0 / -1 = 0 and
    every later ref is kept, and the pool's denominator is reduced by one."""
    a, b = toks("first", 5), toks("second", 9)
    first = seg("tool_result", 0, a)  # origin -1: no mirrored call exists
    second = seg("tool_result", 10, b)  # origin 9, W = 9: mirror calls 0..8, every one hits
    uses = {11: {a[0]}, 12: {a[1]}, 13: {a[2]}, 14: {a[3]}, 15: {a[4]}}
    uses.update({k: {b[k]} for k in range(0, 9)})
    stats = link(trace([first, second], uses), placebo="mirror")
    # pooled tool_result rate = 9/9 = 1: nothing can beat it
    assert stats["fallback"] == 1
    assert first.refs == [0]


def test_tool_results_born_at_call_0_do_not_break_the_pooled_rate():
    """The pooled rate is a share of mirrored calls and must lie in [0, 1]. Each tool result
    born at call 0 adds -1 to the pool's denominator, so the pooled rate can exceed 1 and
    sqrt(W p (1 - p)) raises 'math domain error'."""
    pre = toks("pre", 2)
    z = seg("tool_result", 0, toks("zero", 1))  # origin -1, adds avail -1 to the pool
    a = seg("tool_result", 3, pre)  # origin 2: mirror calls 0..1, both hit -> pool [2, 2]
    later = toks("later", 3)
    c = seg("tool_result", 1, later)  # origin 0: no mirror, falls back to the pool
    uses = {0: {pre[0]}, 1: {pre[1]}, 5: {later[0]}, 6: {later[1]}, 7: {later[2]}}
    t = trace([z, a, c], uses)
    stats = link(t, placebo="mirror")  # today: ValueError: math domain error (p = 2/1)
    assert c.refs == [1]  # pooled rate 2/2 = 1: dropped
    assert stats["fallback"] == 1


def test_transcript_that_starts_with_a_tool_result_end_to_end():
    """The same through the transcript reader and the rule tier: a session cut so that it starts
    with tool results. detect(lines, "mirror") must not crash."""
    def call(n, blocks, ctx):
        return {"type": "assistant", "message": {"id": f"m{n}", "role": "assistant", "content": blocks,
                "usage": {"input_tokens": 5, "cache_read_input_tokens": ctx, "cache_creation_input_tokens": 0,
                          "output_tokens": 10}}}

    def result(tid, text):
        return {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "content": text}]}}

    def tool(n, tid, inp, ctx):
        return call(n, [{"type": "tool_use", "id": tid, "name": "Bash", "input": inp}], ctx)

    lines = [result("x0", "zero_marker_text"),  # born 0, origin -1: adds avail -1 to the pool
             tool(1, "t1", {"command": "prior_marker_one"}, 1000),  # call 0
             result("t1", "later_marker_aaa later_marker_bbb later_marker_ccc"),  # born 1, origin 0: no mirror
             call(2, [{"type": "text", "text": "prior_marker_two"}], 1100),  # call 1
             tool(3, "t3", {"command": "ls"}, 1200),  # call 2
             result("t3", "prior_marker_one prior_marker_two"),  # born 3, origin 2: mirror calls 0..1, both hit
             call(4, [{"type": "text", "text": "later_marker_aaa"}], 1300),  # call 3
             call(5, [{"type": "text", "text": "later_marker_bbb"}], 1400),  # call 4
             call(6, [{"type": "text", "text": "later_marker_ccc"}], 1500)]  # call 5
    t = read_trace_lines(lines)
    link(t, placebo="mirror")  # today: ValueError: math domain error (pooled tool_result rate 2/1)
    rules.detect(lines, "mirror")


# --- compare: the CI when the point ratio is undefined ----------------------------------------

def _session(sid, inputs):
    return {"id": sid, "model": "m", "source": "local", "base_override": None,
            "measurement": {"api_calls": len(inputs), "user_instructions": len(inputs), "compactions": 0,
                            "per_instruction": {"input": list(inputs), "calls": [1] * len(inputs)}}}


def test_no_ci_when_the_before_median_is_zero():
    """With a before median of 0 the ratio is undefined (compare reports ratio None). The CI must
    then be None too; today it is computed from only the resamples whose before median happened
    to be non-zero (a conditional CI), and printed next to a blank ratio."""
    before = build({}, [_session(f"B{i}", [0, 0, 0]) for i in range(5)] + [_session("B5", [10, 10, 10, 10])])
    after = build({}, [_session(f"A{i}", [5, 5, 5]) for i in range(6)])
    r = compare.compare(before, after, reps=500)
    assert r["primary"]["ratio"] is None
    assert r["primary"]["ci"] is None


# --- compare CLI: malformed floor.json ---------------------------------------------------------

def test_malformed_floor_json_is_an_error_not_a_traceback(tmp_path, capsys):
    """`pxt survey compare` refuses bad input with exit 2 and 'error: ...' (it does so for a bad
    dataset). A floor.json that is valid JSON but not an object raises AttributeError today."""
    ds = build({}, [_session(f"S{i}", [1, 2, 3, 4, 5, 6]) for i in range(6)])
    d = tmp_path / "before"
    d.mkdir()
    (d / "dataset.json").write_text(json.dumps(ds))
    (d / "floor.json").write_text(json.dumps(["not", "a", "floor"]))
    assert main(["survey", "compare", str(d), str(d), "--reps", "10"]) == 2
    assert "error" in capsys.readouterr().err
