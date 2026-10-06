import copy
import json
from pathlib import Path

import pytest

from pickaxetax.cli import main
from pickaxetax.survey import compare
from pickaxetax.survey.dataset import SCHEMA, build

DATASET_V2 = Path(__file__).resolve().parent.parent / "research" / "survey" / "user01" / "dataset-v2.json"


def session(sid, inputs, steps=4, compactions=0, model="m1"):
    """A synthetic session: per-instruction inputs, a per-call context series that matches them."""
    ctx, starts = [], []
    for x in inputs:
        starts.append(len(ctx))
        ctx.extend([x / steps] * steps)
    return {"id": sid, "model": model, "source": "local", "base_override": None,
            "measurement": {"api_calls": len(ctx), "user_instructions": len(inputs), "compactions": compactions,
                            "per_instruction": {"input": list(inputs), "calls": [steps] * len(inputs)},
                            "series": {"context": ctx, "instruction_starts": starts},
                            "subagents": {"api_calls": 1}}}


def ds(sessions):
    return build({"label": "synthetic"}, sessions)


def spread(n, base):
    return [base * (1 + 0.05 * (i % 7)) for i in range(n)]


def test_same_dataset_gives_ratio_one_and_a_ci_containing_one():
    x = ds([session(f"S{i}", spread(8, 1e6 * (i + 1))) for i in range(6)])
    r = compare.compare(x, x)
    assert r["primary"]["ratio"] == 1
    lo, hi = r["primary"]["ci"]
    assert lo <= 1 <= hi and lo < hi
    assert all(v["ratio"] in (None, 1) for v in r["secondary"].values())
    assert r["warnings"] == []


def test_same_dataset_on_the_public_before_set():
    x = json.loads(DATASET_V2.read_text(encoding="utf-8"))
    r = compare.compare(x, x, reps=500)
    assert r["primary"]["ratio"] == 1 and r["primary"]["ci"][0] <= 1 <= r["primary"]["ci"][1]
    assert r["before"]["counts"]["sessions"] == 10
    assert r["secondary"]["carried_share"]["before"] == pytest.approx(0.761, abs=0.001)


def test_halved_inputs_give_ratio_one_half():
    before = ds([session(f"S{i}", spread(7, 2e6 * (i + 1))) for i in range(5)])
    after = copy.deepcopy(before)
    for s in after["sessions"]:
        pi = s["measurement"]["per_instruction"]
        pi["input"] = [x / 2 for x in pi["input"]]
    r = compare.compare(before, after)
    assert r["primary"]["ratio"] == pytest.approx(0.5)
    lo, hi = r["primary"]["ci"]
    assert lo <= 0.5 <= hi


def test_bootstrap_resamples_sessions_not_instructions():
    # one huge session holds 40 of the 100 instructions; whether the median is huge depends on how
    # often that one session is drawn, which the pooled-instruction bootstrap cannot see
    before = [spread(40, 1e8)] + [spread(10, 1e6) for _ in range(6)]
    after = [spread(10, 1e6) for _ in range(7)]
    by_session = compare.bootstrap_ratio(before, after, reps=1000)
    pooled = compare.bootstrap_ratio(before, after, reps=1000, unit="instruction")
    assert (by_session[1] - by_session[0]) > 5 * (pooled[1] - pooled[0])
    # and compare() uses the session bootstrap
    r = compare.compare(ds([session(f"B{i}", g) for i, g in enumerate(before)]),
                        ds([session(f"A{i}", g) for i, g in enumerate(after)]), reps=1000)
    assert r["primary"]["ci"] == pytest.approx(list(by_session))


def test_secondary_measures():
    before = ds([session("S1", [100, 200, 300], steps=10, compactions=1), session("S2", [400], steps=10)])
    after = ds([session("S1", [50, 60], steps=2), session("S2", [70], steps=2), session("S3", [80], steps=2)])
    r = compare.compare(before, after, reps=50)
    s = r["secondary"]
    assert s["median_steps_per_instruction"]["before"] == 10 and s["median_steps_per_instruction"]["after"] == 2
    assert s["compactions_per_1000_calls"]["before"] == pytest.approx(1000 * 1 / 40)
    assert s["compactions_per_1000_calls"]["after"] == 0
    assert s["instructions_per_session"]["before"] == 2 and s["instructions_per_session"]["after"] == pytest.approx(4 / 3)
    assert r["before"]["counts"] == {"sessions": 2, "instructions": 4, "user_instructions": 4, "calls": 40,
                                     "subagent_calls": 2, "sessions_with_series": 2}
    # few sessions and instructions on both sides: a plain warning for each
    assert len(r["warnings"]) == 2 and "fewer than 5 sessions or 30 instructions" in r["warnings"][1]


def run_dir(path, dset, floor=None):
    path.mkdir()
    (path / "dataset.json").write_text(json.dumps(dset))
    if floor is not None:
        (path / "floor.json").write_text(json.dumps(floor))
    return path


def test_directory_input_with_floor(tmp_path, capsys):
    x = ds([session(f"S{i}", spread(8, 1e6 * (i + 1))) for i in range(6)])
    floor = {"total": {"floor_pct_price_weighted": 8.92, "floor_pct_of_input": 0.0008, "calls": 2000, "W1": {"count": 4}}}
    b = run_dir(tmp_path / "before", x, floor)
    a = run_dir(tmp_path / "after", x, {"total": {"floor_pct_price_weighted": 4.46, "floor_pct_of_input": 0.0004,
                                                  "calls": 1000, "W1": {"count": 4}}})
    out = tmp_path / "cmp.json"
    assert main(["survey", "compare", str(b), str(a), "--out", str(out), "--reps", "200"]) == 0
    r = json.loads(out.read_text())
    assert r["primary"]["ratio"] == 1 and r["primary"]["reps"] == 200
    assert r["secondary"]["removable_cost_pct"] == {"before": 8.92, "after": 4.46, "ratio": 0.5}
    assert r["secondary"]["w1_per_1000_calls"] == {"before": 2.0, "after": 4.0, "ratio": 2.0}
    printed = capsys.readouterr().out
    assert "removable cost" in printed and "not randomized" in printed and "confounded" in printed


def test_missing_floor_is_handled(tmp_path, capsys):
    x = ds([session(f"S{i}", spread(8, 1e6)) for i in range(6)])
    b = run_dir(tmp_path / "before", x, {"total": {"floor_pct_price_weighted": 8.92, "floor_pct_of_input": 0.0008}})
    a = run_dir(tmp_path / "after", x)  # no floor.json
    f = tmp_path / "plain.json"
    f.write_text(json.dumps(x))
    for after in (a, f):
        out = tmp_path / "cmp.json"
        assert main(["survey", "compare", str(b), str(after), "--out", str(out), "--reps", "50"]) == 0
        r = json.loads(out.read_text())
        assert r["secondary"]["removable_cost_pct"] == {"before": None, "after": None, "ratio": None}
        assert r["secondary"]["w1_per_1000_calls"]["before"] is None
    assert "removable cost" in capsys.readouterr().out


def test_seed_fixes_the_ci_and_bad_input_is_refused(tmp_path, capsys):
    x = ds([session(f"S{i}", spread(8, 1e6 * (i + 1))) for i in range(6)])
    assert compare.compare(x, x, seed=7)["primary"]["ci"] == compare.compare(x, x, seed=7)["primary"]["ci"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "something.else", "sessions": []}))
    assert main(["survey", "compare", str(bad), str(bad)]) == 2
    assert "not a survey dataset" in capsys.readouterr().err
    assert SCHEMA == x["schema"]
