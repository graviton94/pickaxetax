from pickaxetax.survey import rules
from tests.test_agent import T


def lines_of(t):
    return [l for l in t.lines]


def test_w8_unreferenced_exploration_and_w4_rewrite():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "look around and write the config"}})
    t.tool("r1", "Read", {"file_path": "/p/used_module.py"}, ctx_read=1000).result("r1", "def parse_settings_block(config_loader): pass " * 50)
    t.tool("r2", "Read", {"file_path": "/p/unused_module.py"}, ctx_read=2000).result("r2", "def totally_unrelated_helper(): pass " * 200)
    t.tool("w1", "Write", {"file_path": "/p/conf.toml", "content": "first_version_value = 1\n" * 100}, ctx_read=3000).result("w1", "ok")
    t.call(4000, blocks=[{"type": "text", "text": "parse_settings_block takes the config_loader as input"}])
    t.raw({"type": "user", "message": {"role": "user", "content": "redo the config"}})
    t.tool("w2", "Write", {"file_path": "/p/conf.toml", "content": "second_version_value = 2\n" * 100}, ctx_read=5000).result("w2", "ok")
    r = rules.detect(lines_of(t))
    assert r["instructions"] == 2
    s1 = r["scores"][0]
    assert s1["W8_explore"] > s1["W8"] > 0  # one of the two reads was never echoed
    assert "W8" in r["flags"][0]
    assert s1["W4"] > 0 and "W4" in r["flags"][0] and "W4" not in r["flags"][1]


def test_read_only_shell_commands_count_as_exploration():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "inspect"}})
    t.tool("b1", "Bash", {"command": "cat /p/unused_module.py"}, ctx_read=1000).result("b1", "def totally_unrelated_helper(): pass " * 200)
    t.tool("b2", "Bash", {"command": "npm test"}, ctx_read=2000).result("b2", "all_tests_passed_marker " * 200)
    t.call(3000, blocks=[{"type": "text", "text": "Fine."}])
    s = rules.detect(t.lines)["scores"][0]
    assert s["W8_explore"] == s["W8"] > 0  # the cat counts, the test run does not


def test_w5_dead_carried_context_lands_on_the_later_instruction():
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read the loader"}})
    t.tool("r1", "Read", {"file_path": "/p/config_loader.py"}, ctx_read=1000).result("r1", "def parse_settings_block(): pass " * 300)
    t.call(5000, blocks=[{"type": "text", "text": "parse_settings_block found."}])
    t.raw({"type": "user", "message": {"role": "user", "content": "now write the release notes"}})
    t.call(5100, blocks=[{"type": "text", "text": "Release notes drafted."}])
    t.call(5200, blocks=[{"type": "text", "text": "Done."}])
    r = rules.detect(lines_of(t))
    assert r["scores"][0]["W5"] == 0 and r["scores"][1]["W5"] > 0
    assert "W5" in r["flags"][1]
