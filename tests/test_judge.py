from pickaxetax.survey import judge
from tests.test_agent import T


def run(t, tmp_path, name="j.jsonl", **kw):
    return judge.judge_source(t.write(tmp_path / name), **kw)


def test_duplicate_same_input_same_result(tmp_path):
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "read it"}})
    t.tool("a", "Read", {"file_path": "/x"}).result("a", "same text " * 20)
    t.tool("b", "Read", {"file_path": "/x"}).result("b", "same text " * 20)   # duplicate
    t.tool("c", "Read", {"file_path": "/x"}).result("c", "changed " * 20)     # changed: not a duplicate
    t.tool("d", "Read", {"file_path": "/y"}).result("d", "same text " * 20)   # other input: not a duplicate
    r = run(t, tmp_path)
    assert r["W1"]["count"] == 1 and r["W1"]["tokens"] > 0


def test_reread_after_compaction_is_not_duplicate(tmp_path):
    t = T()
    t.tool("a", "Read", {"file_path": "/x"}).result("a", "body " * 30)
    t.raw({"type": "system", "subtype": "compact_boundary"})
    t.tool("b", "Read", {"file_path": "/x"}).result("b", "body " * 30)
    assert run(t, tmp_path)["W1"]["count"] == 0


def test_errors_counted(tmp_path):
    t = T()
    t.tool("a", "Bash", {"command": "make"}).result("a", "error: boom " * 10, is_error=True)
    r = run(t, tmp_path)
    assert r["W2"]["count"] == 1 and r["W2"]["tokens"] > 0


def test_cache_churn(tmp_path):
    t = T()
    t.call(10_000, write=500)            # context 10.5k, mostly read from cache
    t.call(10_500, write=300)            # normal growth
    t.call(0, write=11_000, inp=5)       # cache lost: the whole prefix written again
    t.call(5_000, write=100)             # context shrank (compaction): not churn
    r = run(t, tmp_path)
    assert r["W6"]["count"] == 1
    assert r["W6"]["tokens"] == 10_805   # the previous context (10,500 + 300 + 5) re-written
    assert 0 < r["floor_pct_of_input"] < 100


def test_limit_instructions(tmp_path):
    t = T()
    for i in range(3):
        t.raw({"type": "user", "message": {"role": "user", "content": f"task {i}"}})
        t.tool(f"e{i}", "Bash", {"command": "x"}).result(f"e{i}", "err", is_error=True)
    assert run(t, tmp_path, limit_instructions=2)["W2"]["count"] == 2
