import io
import json
import os

import pytest

from pickaxetax.agent import audit_session, export, merge, parse, tips
from pickaxetax.agent import guard
from pickaxetax.agent.install import install, uninstall
from pickaxetax.cli import main


class T:
    """Builds a transcript in Claude Code's JSONL shape (one line per content block)."""

    def __init__(self):
        self.lines = []
        self.n = 0

    def call(self, ctx_read, write=0, inp=5, out=100, blocks=()):
        self.n += 1
        mid = f"msg_{self.n}"
        usage = {"input_tokens": inp, "cache_read_input_tokens": ctx_read, "cache_creation_input_tokens": write, "output_tokens": out}
        for b in blocks or [{"type": "text", "text": "ok"}]:  # same id + usage repeated per block, like the real thing
            self.lines.append({"type": "assistant", "sessionId": "s1", "requestId": f"req_{self.n}",
                               "message": {"id": mid, "role": "assistant", "content": [b], "usage": usage}})
        return self

    def tool(self, tid, name, inp, ctx_read=1000):
        return self.call(ctx_read, blocks=[{"type": "thinking", "thinking": ""}, {"type": "tool_use", "id": tid, "name": name, "input": inp}])

    def result(self, tid, content, is_error=False):
        self.lines.append({"type": "user", "sessionId": "s1", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "content": content, "is_error": is_error}]}})
        return self

    def raw(self, d):
        self.lines.append(d)
        return self

    def write(self, path):
        path.write_text("\n".join(json.dumps(l) for l in self.lines) + "\n{not json\n")
        return str(path)


def test_usage_counted_once_per_message(tmp_path):
    t = T().call(1000, blocks=[{"type": "thinking", "thinking": ""}, {"type": "text", "text": "a"}, {"type": "text", "text": "b"}])
    s = parse(t.write(tmp_path / "a.jsonl"))
    assert len(s.calls) == 1
    r = audit_session(s)
    assert r["tokens"]["cache_read"] == 1000 and r["tokens"]["output"] == 100


def test_duplicate_read_large_result_and_failed_repeat(tmp_path):
    big = "line of log output\n" * 1500
    t = (T()
         .tool("r1", "Read", {"file_path": "/p/a.py"}).result("r1", "code " * 300)
         .tool("r2", "Read", {"file_path": "/p/a.py"}).result("r2", "code " * 300)           # dup
         .tool("e1", "Edit", {"file_path": "/p/a.py"}).result("e1", "ok")
         .tool("r3", "Read", {"file_path": "/p/a.py"}).result("r3", "code " * 300)           # after edit: fine
         .tool("r4", "Read", {"file_path": "/p/a.py", "offset": 10}).result("r4", "x " * 50)  # different range: fine
         .tool("b1", "Bash", {"command": "npm test"}).result("b1", big)                     # large
         .tool("b2", "Bash", {"command": "make"}).result("b2", "error", is_error=True)
         .tool("b3", "Bash", {"command": "make"}).result("b3", "error", is_error=True)      # failed repeat
         .call(5000).call(6000))
    r = audit_session(parse(t.write(tmp_path / "b.jsonl")))
    assert r["duplicate_reads"]["count"] == 1
    assert r["large_results"]["count"] == 1 and r["large_results"]["tokens"] > 2000
    assert r["large_results"]["carried_tokens"] == r["large_results"]["tokens"] * 4  # 4 later calls
    assert r["failed_repeats"]["count"] == 1
    assert r["by_tool"]["Bash"]["calls"] == 3
    codes = [x["code"] for x in tips(merge([r]))]
    assert {"dup_read", "large_output", "failed_repeat"} <= set(codes)


def test_compaction_resets_duplicates_and_carry(tmp_path):
    t = (T()
         .tool("r1", "Read", {"file_path": "/p/a.py"}).result("r1", "code " * 300)
         .raw({"type": "system", "subtype": "compact_boundary", "sessionId": "s1"})
         .tool("r2", "Read", {"file_path": "/p/a.py"}).result("r2", "code " * 300)
         .call(100))
    s = parse(t.write(tmp_path / "c.jsonl"))
    r = audit_session(s)
    assert r["compactions"] == 1 and r["duplicate_reads"]["count"] == 0
    assert r["by_tool"]["Read"]["carried_tokens"] == s.tools[1].result_tokens * 1  # first read carried 0 calls


def test_sidechain_kept_separate(tmp_path):
    t = T().call(1000)
    t.raw({"type": "assistant", "isSidechain": True, "message": {"id": "side1", "content": [], "usage": {"input_tokens": 1, "output_tokens": 1}}})
    r = audit_session(parse(t.write(tmp_path / "d.jsonl")))
    assert r["api_calls"] == 1 and r["subagent_calls"] == 1


def test_export_has_no_paths_or_commands(tmp_path):
    t = (T().tool("r1", "Read", {"file_path": "/home/alice/secret-project/plan.md"}).result("r1", "x " * 3000)
         .tool("m1", "mcp__acme_internal__search", {"q": "salary data"}).result("m1", "y")
         .tool("m2", "mcp__other__tool", {}).result("m2", "z")
         .tool("b1", "Bash", {"command": "cat ~/.ssh/id_rsa"}).result("b1", "no")
         .call(10))
    m = merge([audit_session(parse(t.write(tmp_path / "e.jsonl")))])
    blob = json.dumps(export(m))
    for secret in ("alice", "secret-project", "plan.md", "acme", "salary", "id_rsa", "s1"):
        assert secret not in blob
    assert export(m)["by_tool"]["mcp"]["calls"] == 2


def test_cli_audit_and_export(tmp_path, capsys):
    p = T().tool("r1", "Read", {"file_path": "/p/a"}).result("r1", "a " * 10).call(10).write(tmp_path / "f.jsonl")
    assert main(["agent", "audit", p]) == 0
    assert "API calls" in capsys.readouterr().out
    assert main(["agent", "audit", "--export", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "pickaxetax.agent.v1"


# --- guard hook ----------------------------------------------------------------

@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "STATE_DIR", tmp_path / "state")
    monkeypatch.setenv("PICKAXETAX_LEDGER", str(tmp_path / "ledger.sqlite3"))
    f = tmp_path / "src.py"
    f.write_text("print('hello')\n" * 200)
    return tmp_path, f


def read_event(path, session="sess-1", **extra):
    return {"session_id": session, "hook_event_name": "PreToolUse", "tool_name": "Read",
            "tool_input": {"file_path": str(path), **extra}, "cwd": "/", "transcript_path": "/dev/null"}


def run(event, kind="pre-tool-use"):
    out = io.StringIO()
    rc = guard.run_hook(kind, stdin=io.StringIO(json.dumps(event)), stdout=out)
    assert rc == 0
    return json.loads(out.getvalue()) if out.getvalue() else None


def test_guard_denies_unchanged_reread_once(isolated):
    tmp, f = isolated
    assert run(read_event(f)) is None                      # first read: allowed
    out = run(read_event(f))                               # unchanged re-read: denied
    hso = out["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse" and hso["permissionDecision"] == "deny"
    assert "unchanged" in hso["permissionDecisionReason"]
    assert run(read_event(f)) is None                      # model insists: allowed
    from pickaxetax.proxy import Ledger
    t = Ledger(str(tmp / "ledger.sqlite3")).summary()["totals"]
    assert t["avoided_input"] > 100 and t["requests"] == 1


def test_guard_allows_changed_file_other_range_other_session(isolated):
    tmp, f = isolated
    run(read_event(f))
    assert run(read_event(f, offset=50, limit=10)) is None   # different range
    assert run(read_event(f, session="sess-2")) is None      # other session
    f.write_text("changed\n")
    os.utime(f, ns=(1, 1))
    assert run(read_event(f)) is None                        # file changed


def test_guard_compaction_resets(isolated):
    tmp, f = isolated
    run(read_event(f))
    run({"session_id": "sess-1", "hook_event_name": "PreCompact", "trigger": "auto"}, kind="pre-compact")
    assert run(read_event(f)) is None


def test_guard_fails_open(isolated):
    tmp, f = isolated
    out = io.StringIO()
    assert guard.run_hook("pre-tool-use", stdin=io.StringIO("not json"), stdout=out) == 0 and out.getvalue() == ""
    assert run({"tool_name": "Read", "tool_input": {"file_path": "/does/not/exist"}, "session_id": "x"}) is None
    assert run({"tool_name": "Bash", "tool_input": {"command": "ls"}, "session_id": "x"}) is None


def test_guard_state_has_no_contents(isolated):
    tmp, f = isolated
    f.write_text("SECRET_TOKEN_VALUE=abc123\n")
    run(read_event(f))
    run(read_event(f))
    blob = "".join(p.read_text() for p in (tmp / "state").iterdir())
    assert "SECRET_TOKEN_VALUE" not in blob and "sess-1" not in blob


def test_install_merges_and_uninstalls(tmp_path):
    p = tmp_path / ".claude" / "settings.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mine.sh"}]}]}}))
    install(p)
    install(p)  # idempotent
    d = json.loads(p.read_text())
    assert d["model"] == "x"
    pre = d["hooks"]["PreToolUse"]
    assert len(pre) == 2 and pre[0]["hooks"][0]["command"] == "mine.sh"
    assert pre[1]["matcher"] == "Read" and "pickaxetax.cli agent hook pre-tool-use" in pre[1]["hooks"][0]["command"]
    assert "PreCompact" in d["hooks"]
    assert (tmp_path / ".claude" / "settings.json.bak-pickaxetax").exists()
    assert uninstall(p)
    d = json.loads(p.read_text())
    assert d["hooks"] == {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mine.sh"}]}]}


def test_installed_command_actually_runs(tmp_path, isolated):
    """The exact command written into settings.json works when executed by a shell."""
    import subprocess
    p = tmp_path / "settings.json"
    install(p)
    _, f = isolated
    cmd = json.loads(p.read_text())["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    env = dict(os.environ, PICKAXETAX_HOME=str(tmp_path / "home"), PICKAXETAX_LEDGER=str(tmp_path / "l.sqlite3"))
    ev = json.dumps(read_event(f, session="shell-test"))
    first = subprocess.run(cmd, shell=True, input=ev, capture_output=True, text=True, env=env)
    second = subprocess.run(cmd, shell=True, input=ev, capture_output=True, text=True, env=env)
    assert first.returncode == 0 and first.stdout == ""
    assert second.returncode == 0 and json.loads(second.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_plugin_manifests_consistent():
    from pathlib import Path
    import tomllib

    root = Path(__file__).resolve().parent.parent
    market = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    entry = market["plugins"][0]
    plugin_dir = root / entry["source"]
    manifest = json.loads((plugin_dir / ".claude-plugin/plugin.json").read_text())
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    assert manifest["name"] == entry["name"] == "pickaxetax"
    assert manifest["version"] == entry["version"] == version
    pre = manifest["hooks"]["PreToolUse"][0]
    assert pre["matcher"] == "Read" and "pxt agent hook pre-tool-use" in pre["hooks"][0]["command"]
    assert "pxt agent hook pre-compact" in manifest["hooks"]["PreCompact"][0]["hooks"][0]["command"]


def test_plugin_command_is_harmless_without_pxt(tmp_path):
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    cmd = json.loads((root / "claude-plugin/pickaxetax/.claude-plugin/plugin.json").read_text())["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    r = subprocess.run(cmd, shell=True, input="{}", capture_output=True, text=True, env={"PATH": str(tmp_path)})
    assert r.returncode == 0 and r.stdout == ""
