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


def stamp(t, *times):
    """Give the assistant lines of T's calls these times (one per call, in order)."""
    calls = {}
    for line in t.lines:
        if line["type"] == "assistant":
            calls.setdefault(line["message"]["id"], []).append(line)
    for (mid, lines), ts in zip(calls.items(), times):
        for line in lines:
            line["timestamp"] = ts
    return t


def test_cache_churn_causes(tmp_path):
    t = T()
    t.call(10_000)
    t.call(0, write=10_100)               # 30 s later: churn inside the cache lifetime
    t.call(0, write=10_200)               # 2 h later: the cache had expired
    stamp(t, "2026-01-01T00:00:00Z", "2026-01-01T00:00:30Z", "2026-01-01T02:00:30Z")
    t.lines[-1]["message"]["model"] = "m2"
    t.lines[0]["message"]["model"] = t.lines[1]["message"]["model"] = "m1"
    c = run(t, tmp_path)["W6"]["by_cause"]
    assert c["gap_under_5m"]["count"] == 1 and c["model_switch"]["count"] == 1  # a switch wins over the gap
    assert c["gap_over_1h"]["count"] == 0
    t.lines[-1]["message"]["model"] = "m1"
    c = run(t, tmp_path, name="k.jsonl")["W6"]["by_cause"]
    assert c["gap_under_5m"]["count"] == 1 and c["gap_over_1h"]["count"] == 1
    assert judge.combine({"a": run(t, tmp_path, name="l.jsonl")})["total"]["W6"]["by_cause"]["gap_over_1h"]["count"] == 1


def test_local_subagent_transcripts_are_read_and_kept_apart(tmp_path):
    main = T()
    main.raw({"type": "user", "timestamp": "2026-01-01T00:00:00Z", "message": {"role": "user", "content": "go"}})
    main.call(1000)
    stamp(main, "2026-01-01T00:00:01Z")
    path = main.write(tmp_path / "s.jsonl")
    (tmp_path / "s" / "subagents").mkdir(parents=True)
    for name in ("a", "b"):  # two sub-agents read the same file: each needed it, no duplicate
        sub = T().tool("x" + name, "Read", {"file_path": "/f"}).result("x" + name, "same " * 40)
        for line in sub.lines:
            line.update(isSidechain=True, agentId=name, timestamp="2026-01-01T00:00:02Z")
            if "id" in line["message"]:
                line["message"]["id"] += name
        sub.write(tmp_path / "s" / "subagents" / f"agent-{name}.jsonl")
    r = judge.judge_source(path)
    assert r["main"]["calls"] == 1 and r["subagents"]["calls"] == 2
    assert r["W1"]["count"] == 0
    assert judge.judge_source(path, limit_calls=1)["subagents"]["calls"] == 0  # cut at the snapshot
