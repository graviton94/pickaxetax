import json
import math

from pickaxetax.agent.bound import link
from pickaxetax.backtest import MIN_CALLS, PROTOCOL
from pickaxetax.backtest import label as bl
from pickaxetax.backtest import run as br
from pickaxetax.backtest.policies import simulate
from pickaxetax.backtest.stats import bootstrap_ci, wilson
from pickaxetax.backtest.trace import from_conversation, load
from pickaxetax.cli import main
from pickaxetax.ingest import parse_json
from pickaxetax.models import RawConversation, RawTurn

from .test_bound import session as agent_session


def chat(n=6, topic="postgres_replication_lag"):
    turns = []
    for i in range(n):
        turns.append(RawTurn("user", f"question {i} about {topic} and vacuum_settings_{i}"))
        turns.append(RawTurn("assistant", f"answer {i}: {topic} depends on vacuum_settings_{max(0, i - 2)} " + "detail " * 30))
    return RawConversation(turns, "chatgpt")


def test_chat_trace_re_reads_history():
    t = from_conversation(chat(3))
    assert len(t.contexts) == 3
    # every reply processes all earlier turns: the context only grows
    assert t.contexts[0] < t.contexts[1] < t.contexts[2]
    assert sum(s.tokens for s in t.segments if s.birth <= 2) == t.contexts[2]


def test_policies_against_oracle():
    t = from_conversation(chat(8))
    link(t)
    full = simulate(t, "full")
    assert full["cost"] == full["measured"] and full["saved_pct"] == 0
    for fam in ("window", "recency", "pointer"):
        r = simulate(t, fam, 2, penalty=1000)
        assert 0 <= r["miss_rate"] <= 100 and r["cost"] > 0
    assert simulate(t, "recency", math.inf)["cost"] <= full["cost"]  # never-evict recency keeps at most everything


def test_stats_are_deterministic():
    xs = [1.0, 2, 3, 4, 50]
    assert bootstrap_ci(xs, seed=1, b=500) == bootstrap_ci(xs, seed=1, b=500)
    p, lo, hi = wilson(8, 10)
    assert lo < p < hi and round(p, 1) == 0.8


def test_gemini_api_format():
    convs = parse_json({"contents": [{"role": "user", "parts": [{"text": "hi there"}]},
                                     {"role": "model", "parts": [{"text": "hello"}]}]})
    assert convs and convs[0].source == "gemini" and [t.role for t in convs[0].turns] == ["user", "assistant"]


def test_run_report_is_anonymous_and_complete(tmp_path):
    exports = []
    for i, src in enumerate(["chatgpt", "claude"]):
        conv = chat(6 + i, topic=f"secret_project_name_{i}")
        f = tmp_path / f"private_name_{i}.json"
        f.write_text(json.dumps({"messages": [{"role": t.role, "content": t.text} for t in conv.turns]}))
        exports.append(str(f))
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]}))
    report, manifest = br.run(exports + [str(short), agent_session(tmp_path)], source=None)
    assert report["protocol"] == PROTOCOL and report["sessions"]["excluded_short"] == 1
    assert report["sessions"]["kept"] == 3 and len(manifest) == 3
    text = json.dumps(br.nan_to_none(report))
    assert "secret_project_name" not in text and "private_name" not in text and str(tmp_path) not in text
    agg = report["aggregate"]
    assert agg["all_sessions"]["sessions"] == 3 and agg["all_sessions"]["insufficient"]
    assert set(agg["by_source"]) == {"openai-messages", "claude-code"}
    cells = agg["sensitivity"]
    assert len(cells) == 18 and {c["variant"] for c in cells} == {"primary", "agents_uncalibrated"}
    assert [c["sessions"] for c in cells if c["variant"] == "primary"] == [3] * 9
    assert isinstance(agg["paging_beats_forgetting_in_every_cell"], bool)
    for r in report["per_session"]:
        assert r["oracle"]["P0"] >= r["oracle"]["P1000"] >= r["oracle"]["P10000"] >= r["oracle"]["Pinf"]
        assert set(r["online"]) == {"window", "recency", "pointer"}


def test_source_override_and_split_is_stable(tmp_path):
    f = tmp_path / "g.json"
    f.write_text(json.dumps({"messages": [{"role": t.role, "content": t.text} for t in chat(4).turns]}))
    s1 = load(str(f), source="grok")
    s2 = load(str(f), source="grok")
    assert s1[0].source == "grok" and s1[0].fingerprint == s2[0].fingerprint
    assert br.split_of(s1[0].fingerprint) in ("dev", "test")


def test_label_summary_reweights_strata():
    store = {"hit": {"a": True, "b": True, "c": False, "d": True}, "miss": {"e": False, "f": False, "g": True, "h": False},
             "population": {"hit": 100, "miss": 900}}
    s = bl.summarize(store)
    assert s["precision_pct"][0] == 75.0 and s["needed_but_not_detected_pct"][0] == 25.0
    assert s["recall_pct_estimate"] == round(100 * 75 / (75 + 225), 1)


def test_label_pairs_need_text(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"messages": [{"role": t.role, "content": t.text} for t in chat(5).turns]}))
    hit, miss = bl.pairs(load(str(f), keep_text=True))
    assert hit and miss and all(len(k) == 16 for k, _, _ in hit + miss)
    assert bl.pairs(load(str(f))) == ([], [])  # without keep_text nothing is shown or labeled


def test_cli_backtest(tmp_path, capsys):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"messages": [{"role": t.role, "content": t.text} for t in chat(MIN_CALLS + 2).turns]}))
    out, man = tmp_path / "r.json", tmp_path / "m.txt"
    assert main(["backtest", "run", str(f), "--source", "gemini", "--out", str(out), "--manifest", str(man)]) == 0
    assert "source: gemini" in capsys.readouterr().out
    assert json.loads(out.read_text())["aggregate"]["by_source"]["gemini"]["sessions"] == 1
