"""Regressions from the phase 2 code review (cycle E2): each test states the correct behaviour."""
import json

from pickaxetax.agent import bound
from pickaxetax.cli import main
from pickaxetax.survey import events, judge, rules, whatif
from tests.test_agent import T


def _lines(t):
    return [json.loads(json.dumps(l)) for l in t.lines]


# 1. judge_lines(limit_calls=N) stops in the middle of call N (after its first line), so the rest of
#    call N's content blocks (its tool_use) and the results after it are dropped; events.cut, which the
#    dataset (measure_pages) and `survey machine` use, keeps them. Same --limit-calls, different lines.
def test_judge_limit_calls_matches_cut(tmp_path):
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "build it"}})
    t.tool("a", "Bash", {"command": "make"}, ctx_read=1000).result("a", "error: boom " * 20, is_error=True)
    t.call(2000)
    lines = _lines(t)
    direct = judge.judge_lines(lines, limit_calls=1)
    via_cut = judge.judge_lines(events.cut(lines, limit_calls=1))
    assert direct["W2"] == via_cut["W2"]  # direct: 0 errors, via cut: 1


# 2. rules.detect counts instructions with events._is_instruction but takes "finished instruction"
#    boundaries from bound.read_trace_lines, which uses another rule (any non-reminder text block is a
#    prompt). A prompt preceded by an IDE context block (text starting with "<") is not an instruction
#    for events/judge/labeling but is one for the bound, so W5 is charged to an instruction that,
#    by the shared rule, has not finished.
def test_rules_w5_uses_the_same_instruction_boundaries():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read the loader"}})
    t.tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000).result("r1", "def parse_settings_block(): pass " * 300)
    t.call(5000, blocks=[{"type": "text", "text": "parse_settings_block found."}])
    t.raw({"type": "user", "message": {"role": "user", "content": [
        {"type": "text", "text": "<ide_opened_file>The user opened /p/notes.md in the IDE.</ide_opened_file>"},
        {"type": "text", "text": "now write the release notes"}]}})
    t.call(5100, blocks=[{"type": "text", "text": "Release notes drafted."}])
    t.call(5200, blocks=[{"type": "text", "text": "Done."}])
    lines = _lines(t)
    r = rules.detect(lines)
    starts = bound.read_trace_lines(lines).instruction_starts
    assert r["instructions"] == len(starts)  # 1 vs 2
    assert r["scores"][0]["W5"] == 0  # nothing finished yet by the shared rule; got > 0, flagged W5


# 2b. The other direction: a long prompt that quotes "<system-reminder>" after 200 chars is an
#     instruction for events but not a start for the bound, so its W5 is lost.
def test_rules_w5_long_prompt_quoting_a_reminder():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read the loader"}})
    t.tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000).result("r1", "def parse_settings_block(): pass " * 300)
    t.call(5000, blocks=[{"type": "text", "text": "parse_settings_block found."}])
    t.raw({"type": "user", "message": {"role": "user", "content": "now write the release notes. " * 10 + "Why does my log show <system-reminder>?"}})
    t.call(5100, blocks=[{"type": "text", "text": "Release notes drafted."}])
    t.call(5200, blocks=[{"type": "text", "text": "Done."}])
    lines = _lines(t)
    r = rules.detect(lines)
    assert r["instructions"] == len(bound.read_trace_lines(lines).instruction_starts)  # 2 vs 1
    assert r["scores"][1]["W5"] > 0  # same session as test_rules' W5 test, but 0 here


# 3. bound: a call's output is born at k+1, so the final answer of instruction j is born at the start
#    index of instruction j+1 and bisect_right attributes it to j+1: it is never "carried from a
#    finished instruction" while j+1 runs (W5 / carried_from_finished_instructions undercount).
def test_final_answer_counts_as_carried_into_next_instruction():
    answer = "The release_checklist_alpha covers deployment_window_beta. " * 40
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "summarize"}})
    t.call(1000, blocks=[{"type": "text", "text": answer}])
    t.raw({"type": "user", "message": {"role": "user", "content": "now something unrelated"}})
    t.call(2000, blocks=[{"type": "text", "text": "ok."}])
    t.call(2100, blocks=[{"type": "text", "text": "done."}])
    lines = _lines(t)
    tr = bound.read_trace_lines(lines)
    bound.link(tr)
    rep = bound.bound(tr)
    ans = next(s for s in tr.segments if s.kind == "assistant_text" and s.birth == 1)
    prompt1 = next(s for s in tr.segments if s.kind == "user_prompt" and s.birth == 0)
    # both were produced in instruction 1 and ride through the two calls of instruction 2
    assert rep["carried_from_finished_instructions"]["resident"]["tokens"] == round(2 * (prompt1.tokens + ans.tokens))


# 4. whatif.restart drops what the new instruction adds at its first call (cap() keeps the delta):
#    docstring says base + summary + "what the instruction itself adds".
def test_task_scoped_keeps_the_new_instructions_first_growth():
    ctx, starts = [100, 200, 300, 350, 400], [0, 3]
    # instruction 2 adds 50 at its first call and 50 more at the next
    assert whatif.task_scoped(ctx, starts, base=100, summary=0) == 100 + 200 + 300 + 150 + 200


# 5. Codebook v1 §3: "each token is assigned to at most one category; the earliest in this list wins".
#    An identical failing call repeated is W1 (identical retry) before W2; the judge books it as W2.
def test_identical_failing_retry_is_w1_by_precedence():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "build"}})
    t.tool("a", "Bash", {"command": "make"}).result("a", "error: boom " * 10, is_error=True)
    t.tool("b", "Bash", {"command": "make"}).result("b", "error: boom " * 10, is_error=True)
    r = judge.judge_lines(_lines(t))
    assert r["W1"]["count"] == 1 and r["W2"]["count"] == 1  # got W1 0, W2 2


# 6. The same tool_result delivered twice (same tool_use_id: one call, logged twice) is counted as a
#    duplicate call (W1) and its error twice (W2). Usage is de-duplicated by message id; results are not.
def test_same_tool_use_id_is_not_a_repeated_call():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read"}})
    t.tool("a", "Read", {"file_path": "/x"}).result("a", "body " * 30).result("a", "body " * 30)
    t.tool("e", "Bash", {"command": "make"}).result("e", "err", is_error=True).result("e", "err", is_error=True)
    r = judge.judge_lines(_lines(t))
    assert r["W1"]["count"] == 0 and r["W2"]["count"] == 1


# 7. `survey sample` numbers sessions over every file find_transcripts returns (sub-agent files
#    included when a directory is given); `survey judge`/`machine`/`measure` skip sub-agent files
#    first. The same directory gives different S-labels, so machine labels cannot be matched.
def test_sample_and_machine_number_sessions_alike(tmp_path):
    proj = tmp_path / "proj"
    (proj / "A" / "subagents").mkdir(parents=True)
    for name in ("A", "B"):
        t = T()
        t.raw({"type": "user", "message": {"role": "user", "content": f"task {name}"}})
        t.tool("x", "Bash", {"command": "make"}).result("x", "err", is_error=True)
        t.write(proj / f"{name}.jsonl")
    s = T()
    s.raw({"type": "user", "isSidechain": True, "message": {"role": "user", "content": "sub task"}})
    s.call(500)
    for l in s.lines:
        l["isSidechain"] = True
    s.write(proj / "A" / "subagents" / "agent-1.jsonl")
    packet = tmp_path / "p.json"
    assert main(["survey", "sample", str(proj), "--n", "10", "--calibration", "0", "--out", str(packet)]) == 0
    sessions = sorted({x["session"] for x in json.loads(packet.read_text())["items"]})
    assert sessions == ["S01", "S02"]  # got ["S01", "S03"]
    assert main(["survey", "machine", str(packet), str(proj), "--out", str(tmp_path / "m.json")]) == 0
