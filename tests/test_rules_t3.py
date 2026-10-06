import json

from pickaxetax.cli import main
from pickaxetax.survey import labeling, rules
from tests.test_agent import T


def ask(t, text):
    return t.raw({"type": "user", "message": {"role": "user", "content": text}})


def say(t, text, ctx=1000):
    return t.call(ctx, blocks=[{"type": "text", "text": text}])


def side(t, agent, text):
    """A sub-agent (sidechain) line of the run launched by tool call `agent`."""
    t.n += 1
    return t.raw({"type": "assistant", "isSidechain": True, "agentId": agent,
                  "message": {"id": f"msg_{t.n}", "role": "assistant", "content": [{"type": "text", "text": text}],
                              "usage": {"input_tokens": 5, "cache_read_input_tokens": 900, "output_tokens": 10}}})


def two_turns(first_prompt, next_prompt, extra=None):
    t = ask(T(), first_prompt)
    t.tool("w1", "Edit", {"file_path": "/repo/src/config_loader.py", "old_string": "a", "new_string": "b"}).result("w1", "ok")
    say(t, "Updated config_loader.py as asked.")
    ask(t, next_prompt)
    if extra:
        extra(t)
    say(t, "Done.")
    return rules.detect_t3(t.lines)


# --- phrase classes ------------------------------------------------------------------------

def test_prompt_signals_korean_and_english():
    s = rules.prompt_signals
    assert s("되돌려 줘") == {"undo"} and s("please revert that") == {"undo"} and s("roll back the change") == {"undo"}
    assert "undo" in s("원래대로 해줘") and "undo" in s("Undo it")
    assert s("아니 그거 말고") == {"correction"} and "correction" in s("그게 아니라 저쪽 파일")
    assert "correction" in s("That's wrong") and "correction" in s("still broken after that")
    assert "correction" in s("여전히 안 돼") and "correction" in s("Not what I meant") and "correction" in s("다시 해봐")
    assert s("하지 말라고 했잖아") == {"unrequested"} and "unrequested" in s("I didn't ask for tests")
    assert "unrequested" in s("왜 README를 고쳤어? 그건 왜 수정했어") and "unrequested" in s("That was unnecessary")
    assert s("좋아") == {"accept"} and "accept" in s("고마워, 완벽해") and "accept" in s("Thanks!")
    assert "accept" in s("OK, next: the parser") and "accept" in s("이제 배포하자")
    # words that only look like the signals
    assert s("아니면 다른 방법도 있어?") == set()      # "or else", not "no"
    assert s("다음과 같이 바꿔줘") == set()            # "as follows", not "next"
    assert s("내가 좋아하는 색으로") == set()           # "like", not "good"
    assert s("upgrade next.js to 15") == set()
    assert "accept" not in s("아직 안 됐다")
    assert s("bookkeeping undone okapi") == set()      # no whole-word match
    # fenced code is not read
    assert s("fix this\n```\nError: wrong type\n```") == set()


# --- W7 / outcome --------------------------------------------------------------------------

def test_correction_gives_not_met_korean():
    r = two_turns("config_loader 고쳐줘", "아니 그게 아니라 timeout 값을 바꾸라고")
    assert r["flags"][0] == {"W3": "no", "W7": "unsure", "outcome": "not_met"}
    assert "correction" in r["signals"][0]


def test_acceptance_gives_met_and_no_w7_english():
    r = two_turns("fix the config_loader timeout", "Great, thanks. Next the parser")
    assert r["flags"][0] == {"W3": "no", "W7": "no", "outcome": "met"}
    assert "accept" in r["signals"][0]


def test_unrequested_gives_w7_yes():
    r = two_turns("fix the config_loader timeout", "I didn't ask you to touch the loader")
    assert r["flags"][0]["W7"] == "yes" and "unrequested" in r["signals"][0]
    r = two_turns("config_loader 타임아웃 고쳐줘", "왜 로더까지 바꿨어? 그건 하지 말고")
    assert r["flags"][0]["W7"] == "yes"


def test_undo_by_git_restore_of_a_written_file():
    r = two_turns("fix the config_loader timeout", "hmm",
                  extra=lambda t: t.tool("b1", "Bash", {"command": "git restore src/config_loader.py"}).result("b1", ""))
    assert "undo_files" in r["signals"][0]
    assert r["flags"][0]["W7"] == "yes" and r["flags"][0]["outcome"] == "not_met"
    # restoring a file this instruction did not write is not an undo of its work
    r = two_turns("fix the config_loader timeout", "hmm",
                  extra=lambda t: t.tool("b1", "Bash", {"command": "git checkout -- docs/other_file.md"}).result("b1", ""))
    assert "undo_files" not in r["signals"][0] and r["flags"][0]["W7"] == "unsure"
    # --staged alone only unstages
    r = two_turns("fix the config_loader timeout", "hmm",
                  extra=lambda t: t.tool("b1", "Bash", {"command": "git restore --staged src/config_loader.py"}).result("b1", ""))
    assert "undo_files" not in r["signals"][0]


def test_undo_phrase_without_action():
    r = two_turns("fix the config_loader timeout", "그거 되돌려줘")
    assert "undo" in r["signals"][0] and r["flags"][0] == {"W3": "no", "W7": "unsure", "outcome": "not_met"}


def test_new_topic_is_met_and_last_instruction_is_unknown():
    r = two_turns("fix the config_loader timeout handling", "write release_notes for version 20261006 deployment")
    assert "new_topic" in r["signals"][0] and r["flags"][0]["outcome"] == "met" and r["flags"][0]["W7"] == "unsure"
    assert r["signals"][1] == ["last"] and r["flags"][1] == {"W3": "no", "W7": "unsure", "outcome": "unknown"}
    # a follow-up on the same words is not a new topic, and with no signal the outcome is unknown
    r = two_turns("fix the config_loader timeout handling", "the config_loader timeout handling also needs logging")
    assert "new_topic" not in r["signals"][0] and r["flags"][0]["outcome"] == "unknown"


def test_interrupt_marker_is_skipped_and_counts_against_the_outcome():
    t = ask(T(), "refactor config_loader")
    say(t, "Working on it.")
    t.raw({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "[Request interrupted by user]"}]}})
    ask(t, "thanks, next")
    say(t, "Done.")
    r = rules.detect_t3(t.lines)
    assert r["instructions"] == 3
    assert {"interrupt", "accept"} <= set(r["signals"][0]) and r["flags"][0]["outcome"] == "not_met"


# --- W3 ------------------------------------------------------------------------------------

def subagent_session(result_text, answer):
    t = ask(T(), "survey the repository")
    t.tool("a1", "Agent", {"description": "survey", "prompt": "survey the repository"}).result("a1", "Async agent launched.")
    side(t, "a1", "looking")
    side(t, "a1", result_text)
    t.raw({"type": "user", "message": {"role": "user", "content": "<task-notification>a1 completed</task-notification>"}})
    say(t, answer)
    ask(t, "thanks")
    say(t, "ok")
    return rules.detect_t3(t.lines)


def test_subagent_result_never_used():
    report = " ".join(f"finding_number_{i} in module_{i}.py" for i in range(200))
    r = subagent_session(report, "I will just answer from memory: nothing to change.")
    assert r["scores"][0]["W3_unused"] >= 500 and r["flags"][0]["W3"] == "yes"
    assert "w3_unused_result" in r["signals"][0]
    # the same report, used by the parent's answer
    r = subagent_session(report, "As reported: finding_number_3 in module_3.py and finding_number_7 matter.")
    assert r["scores"][0]["W3"] == 0 and r["flags"][0]["W3"] == "no"


def test_errored_and_abandoned_delegation():
    t = ask(T(), "delegate it")
    t.tool("a1", "Task", {"description": "x", "prompt": "do x"}).result("a1", "agent crashed", is_error=True)
    say(t, "The sub-agent failed.")
    ask(t, "try once more")
    t.tool("a2", "Task", {"description": "x", "prompt": "do x"})  # never answered
    ask(t, "ok, leave it")
    say(t, "Left as is.")
    r = rules.detect_t3(t.lines)
    assert r["flags"][0]["W3"] == "yes" and r["scores"][0]["W3_failed"] == 1
    assert r["flags"][1]["W3"] == "yes" and "w3_failed_delegation" in r["signals"][1]
    assert r["flags"][2]["W3"] == "no"


def test_polling_with_identical_results():
    status = "run 12345678 in_progress " + "step_waiting_for_runner " * 200

    def poll(t, k, results):
        for i, res in enumerate(results):
            t.tool(f"p{k}{i}", "Bash", {"command": "sleep 30 && gh run view 12345678"}).result(f"p{k}{i}", res)
        return t

    t = ask(T(), "wait for the build")
    poll(t, "a", [status] * 4)
    say(t, "Still running.")
    ask(t, "and the deploy?")
    poll(t, "b", [status + str(i) for i in range(4)])  # the state changes every time
    say(t, "Done.")
    ask(t, "now check twice")
    poll(t, "c", [status] * 2)  # too short a run
    say(t, "ok")
    r = rules.detect_t3(t.lines)
    assert r["scores"][0]["W3_poll"] >= 500 and r["flags"][0]["W3"] == "yes" and "w3_poll" in r["signals"][0]
    assert r["scores"][1]["W3_poll"] == 0 and r["scores"][2]["W3_poll"] == 0
    # a different call in between breaks the run
    t = ask(T(), "wait")
    for i in range(3):
        t.tool(f"q{i}", "Bash", {"command": "gh run view 1"}).result(f"q{i}", status)
        t.tool(f"e{i}", "Edit", {"file_path": "/repo/x.py"}).result(f"e{i}", "ok")
    say(t, "ok")
    assert rules.detect_t3(t.lines)["scores"][0]["W3_poll"] == 0


# --- alignment, labels, and the sealed v0 rules ----------------------------------------------

def test_machine_labels_tier_t3(tmp_path):
    from pickaxetax.survey import judge
    from tests.test_labeling import session
    path = session(tmp_path, "a.jsonl", 6)
    p = labeling.build_packet({"S01": labeling.session_instructions(path)}, n=6, calibration=0, seed=3)
    lines = list(judge._jsonl(path))
    m = labeling.machine_labels(p, {"S01": lines}, tier="t3")
    assert m["coder"] == "machine-t3" and m["machine"] == {"tier": "T3", "categories": ["W3", "W7", "outcome"]}
    assert labeling.validate_labels(m) == []
    assert all(set(v) == {"W3", "W7", "outcome"} for v in m["labels"].values())
    assert {v["outcome"] for v in m["labels"].values()} <= {"met", "not_met", "unsure"}
    assert rules.detect_t3(lines)["instructions"] == len(labeling.instructions(lines))
    pk, out = tmp_path / "p.json", tmp_path / "m.json"
    pk.write_text(json.dumps(p))
    assert main(["survey", "machine", str(pk), path, "--tier", "t3", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["labels"] == m["labels"]


def fixed_session():
    t = ask(T(), "look around and write the config")
    t.tool("r1", "Read", {"file_path": "/p/used_module.py"}, ctx_read=1000).result("r1", "def parse_settings_block(config_loader): pass " * 50)
    t.tool("r2", "Read", {"file_path": "/p/unused_module.py"}, ctx_read=2000).result("r2", "def totally_unrelated_helper(): pass " * 200)
    t.tool("w1", "Write", {"file_path": "/p/conf.toml", "content": "first_version_value = 1\n" * 100}, ctx_read=3000).result("w1", "ok")
    t.tool("a1", "Agent", {"description": "survey", "prompt": "survey the repository"}, ctx_read=3500).result("a1", "subagent_summary_report lists nothing_relevant_here")
    t.call(4000, blocks=[{"type": "text", "text": "parse_settings_block takes the config_loader as input"}])
    ask(t, "그게 아니라 redo the config")
    t.tool("w2", "Write", {"file_path": "/p/conf.toml", "content": "second_version_value = 2\n" * 100}, ctx_read=5000).result("w2", "ok")
    t.tool("b1", "Bash", {"command": "git restore /p/conf.toml"}, ctx_read=5200).result("b1", "")
    t.call(5400, blocks=[{"type": "text", "text": "Release notes drafted."}])
    ask(t, "thanks, next write the release notes")
    t.call(5500, blocks=[{"type": "text", "text": "Done."}])
    return t.lines


def test_sealed_v0_detect_output_unchanged():
    # computed with rules.detect before the t3 tier was added (cycle D8)
    expected = {"flags": [["W4", "W8"], ["W5"], ["W5"]], "instructions": 3,
                "scores": [{"W4": 600, "W5": 0, "W5_input": 13525, "W8": 1850, "W8_explore": 2425},
                           {"W4": 0, "W5": 5366, "W5_input": 15615, "W8": 0, "W8_explore": 0},
                           {"W4": 0, "W5": 2345, "W5_input": 5505, "W8": 0, "W8_explore": 0}],
                "totals": {"W4": 600, "W5": 7711, "W5_input": 34645, "W8": 1850, "W8_explore": 2425},
                "version": "rule-tier-v0"}
    lines = fixed_session()
    assert rules.detect(lines) == expected
    r = rules.detect_t3(lines)  # and t3 on the same lines aligns with it
    assert r["instructions"] == 3 and r["flags"][0]["outcome"] == "not_met" and "undo_files" in r["signals"][0]
    assert r["flags"][1]["outcome"] == "met" and r["flags"][2]["outcome"] == "unknown"
