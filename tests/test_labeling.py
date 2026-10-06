import json

import pytest

from pickaxetax.cli import main
from pickaxetax.survey import labeling
from tests.test_agent import T


def session(tmp_path, name, n_instr=6):
    t = T()
    for i in range(n_instr):
        t.raw({"type": "user", "message": {"role": "user", "content": f"task {i}: fix module {i} (secret-token-{i})"}})
        t.tool(f"r{i}", "Read", {"file_path": f"/repo/m{i}.py"}, ctx_read=1000 * (i + 1))
        t.result(f"r{i}", "x" * 50, is_error=(i == 2))
        if i % 2:
            t.tool(f"a{i}", "Task", {"description": f"explore {i}"}, ctx_read=2000)
            t.result(f"a{i}", "summary")
        t.call(500 * (i + 1), blocks=[{"type": "text", "text": f"done {i}"}])
        t.raw({"type": "user", "message": {"role": "user", "content": "<system-reminder>ignored</system-reminder>"}})
    return t.write(tmp_path / name)


def test_instructions_split_and_summarized(tmp_path):
    items = labeling.session_instructions(session(tmp_path, "a.jsonl"))
    assert len(items) == 6
    first = items[0]
    assert first["instruction"].startswith("task 0")
    assert first["steps"][0] == {"tool": "Read", "target": "/repo/m0.py", "result_chars": 50, "error": False}
    assert first["final"] == "done 0"
    assert first["stats"]["calls"] == 2 and first["stats"]["subagents"] == 0
    assert items[1]["stats"]["subagents"] == 1
    assert items[2]["stats"]["errors"] == 1


def test_packet_is_deterministic_stratified_and_disjoint(tmp_path):
    sessions = {"S01": labeling.session_instructions(session(tmp_path, "a.jsonl", 9)),
                "S02": labeling.session_instructions(session(tmp_path, "b.jsonl", 6))}
    p1 = labeling.build_packet(sessions, n=8, calibration=3, seed=5)
    p2 = labeling.build_packet(sessions, n=8, calibration=3, seed=5)
    assert p1 == p2 and p1["sha256"] == labeling.packet_digest(p1)
    ids = [x["id"] for x in p1["items"]] + [x["id"] for x in p1["calibration"]]
    assert len(ids) == len(set(ids)) == 11
    assert {x["session"] for x in p1["items"]} == {"S01", "S02"}
    assert labeling.build_packet(sessions, n=8, calibration=3, seed=6)["sha256"] != p1["sha256"]


def test_redaction(tmp_path):
    sessions = {"S01": labeling.session_instructions(session(tmp_path, "a.jsonl"))}
    p = labeling.build_packet(sessions, n=4, calibration=1, seed=1, redact=[r"secret-token-\d+", r"/repo/"])
    text = json.dumps(p, ensure_ascii=False)
    assert "secret-token" not in text and "/repo/" not in text and labeling.REDACTED in text
    assert p["redacted_patterns"] == 2


def test_kappa_known_values():
    # perfect agreement, chance-level, and a textbook 2x2 case (po=0.7, pe=0.5 -> 0.4)
    assert labeling.cohen_kappa(["yes", "no"], ["yes", "no"]) == 1
    assert labeling.cohen_kappa(["yes"] * 3, ["yes"] * 3) is None
    a = ["yes"] * 5 + ["no"] * 5
    b = ["yes"] * 4 + ["no"] + ["yes"] * 2 + ["no"] * 3
    assert labeling.cohen_kappa(a, b) == pytest.approx(0.4)


def labels(coder, choices, phase="main", packet="p1"):
    return {"schema": labeling.LABELS_SCHEMA, "codebook": "v1", "packet": packet, "phase": phase, "coder": coder,
            "labels": {f"i{k}": {**{c: v for c in labeling.CATEGORIES}, "outcome": "met"} for k, v in enumerate(choices)}}


def test_agreement_report_and_guards(tmp_path):
    a = labels("A", ["yes"] * 5 + ["no"] * 5)
    b = labels("B", ["yes"] * 4 + ["no"] + ["yes"] * 2 + ["no"] * 3)
    r = labeling.agreement(a, b)
    w1 = r["categories"]["W1"]
    assert w1["kappa"] == 0.4 and w1["passes"] is False and w1["disagree"] == ["i4", "i5", "i6"]
    assert r["categories"]["outcome"]["passes"] is None
    with pytest.raises(ValueError):
        labeling.agreement(a, labels("B", ["yes"] * 10, packet="other"))
    with pytest.raises(ValueError):
        labeling.agreement(a, labels("B", ["yes"] * 10, phase="calibration"))
    assert labeling.validate_labels(a) == []
    assert labeling.validate_labels({**a, "labels": {"i0": {"W1": "maybe"}}}) == ["i0.W1"]
    pa, pb = tmp_path / "a.json", tmp_path / "b.json"
    pa.write_text(json.dumps(a)); pb.write_text(json.dumps(b))
    assert main(["survey", "agreement", str(pa), str(pb)]) == 0


def test_cli_sample(tmp_path, capsys):
    path = session(tmp_path, "a.jsonl", 9)
    out = tmp_path / "packet.json"
    assert main(["survey", "sample", path, "--n", "5", "--calibration", "2", "--out", str(out)]) == 0
    p = json.loads(out.read_text())
    assert p["schema"] == labeling.PACKET_SCHEMA and len(p["items"]) == 5 and len(p["calibration"]) == 2
    assert "Do not commit" in capsys.readouterr().out
