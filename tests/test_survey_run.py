import json

from pickaxetax.cli import main
from tests.test_agent import T


def project(tmp_path):
    t = T()
    t.raw({"type": "user", "timestamp": "2026-01-01T00:00:00Z", "message": {"role": "user", "content": "fix the loader"}})
    t.tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=40_000).result("r1", "def parse_settings_block(): pass " * 50)
    t.tool("r2", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=41_000).result("r2", "def parse_settings_block(): pass " * 50)
    t.call(42_000, blocks=[{"type": "text", "text": "parse_settings_block fixed"}])
    t.raw({"type": "user", "timestamp": "2026-01-01T00:10:00Z", "message": {"role": "user", "content": "now the docs"}})
    t.call(43_000, write=500, blocks=[{"type": "text", "text": "docs done"}])
    d = tmp_path / "proj"
    (d / "sess" / "subagents").mkdir(parents=True)
    t.write(d / "sess.jsonl")
    sub = T().call(5_000)
    for line in sub.lines:
        line.update(isSidechain=True, agentId="a1")
        line["message"]["id"] += "sub"
    sub.write(d / "sess" / "subagents" / "agent-a1.jsonl")
    return d


def test_run_writes_everything_and_skips_subagent_files_as_sessions(tmp_path, capsys):
    d = project(tmp_path)
    out = tmp_path / "out"
    assert main(["survey", "run", str(d), "--out-dir", str(out)]) == 0
    names = sorted(p.name for p in out.iterdir())
    assert names == ["dataset.json", "floor.json", "opportunity.json", "report.html"]
    ds = json.loads((out / "dataset.json").read_text())
    assert len(ds["sessions"]) == 1  # the sub-agent file is part of its session, not a session
    floor = json.loads((out / "floor.json").read_text())
    assert floor["total"]["W1"]["count"] == 1 and floor["sessions"]["S01"]["subagents"]["calls"] == 1
    opp = json.loads((out / "opportunity.json").read_text())
    assert "P=inf" in opp["merged"]["policies"] and opp["whatif"]["total"]["measured"] > 0
    printed = capsys.readouterr().out
    assert "mechanical floor" in printed and "numbers only" in printed


def test_measure_skips_subagent_files_as_sessions(tmp_path):
    d = project(tmp_path)
    out = tmp_path / "ds.json"
    assert main(["survey", "measure", str(d), "--out", str(out)]) == 0
    assert len(json.loads(out.read_text())["sessions"]) == 1
