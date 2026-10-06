"""Regressions for the second independent review (research/phase2/log.md, cycle E6)."""
import json
import os

import pytest

from pickaxetax.survey import whatif

DATASET = os.path.join(os.path.dirname(__file__), "..", "research", "survey", "user01", "dataset-v2.json")


def test_restart_replay_is_compacted_at_the_harness_ceiling():
    # instruction 2 restarts small, so the real compactions (780 -> 60) do not apply to the replay;
    # it must still be compacted at the session's ceiling, as the harness would, never carried past it
    ctx, starts = [10, 190, 200, 780, 60, 780, 60], [0, 2]
    r = whatif.restart(ctx, starts, base=10, summary=5, every=1)
    assert r["peak"] <= max(ctx)
    assert r["compactions"] == 1
    # without restarts the replay is the measured series
    assert whatif.restart(ctx, starts, base=10, summary=5)["input"] == sum(ctx)


@pytest.mark.skipif(not os.path.exists(DATASET), reason="public dataset not present")
def test_replay_at_todays_ceiling_reproduces_the_measured_input():
    d = json.load(open(DATASET))
    meas = rep = 0
    for s in d["sessions"]:
        ctx = s["measurement"]["series"]["context"]
        meas += sum(ctx)
        rep += whatif.cap(ctx, whatif.COMPACTION_PREFIX, 783_000, whatif.POST_COMPACTION_NEW)["input"]
    assert abs(rep / meas - 1) < 0.005


@pytest.mark.skipif(not os.path.exists(DATASET), reason="public dataset not present")
def test_ceiling_model_post_is_the_observed_post_compaction_size():
    d = json.load(open(DATASET))
    m = whatif.run(d)["ceiling_model"]
    assert abs(m["post_compaction"] - 64_000) <= 3_000
    posts = [whatif.observed_post(s["measurement"]["series"]["context"]) for s in d["sessions"]]
    assert 55_000 <= sorted(posts)[len(posts) // 2] <= 70_000


def test_ceiling_model_growth_is_per_call():
    ds = {"sessions": [{"id": "A", "base_override": None,
                        "measurement": {"series": {"context": [10, 40, 20, 60], "instruction_starts": [0]}}}]}
    assert whatif.run(ds)["ceiling_model"]["growth_per_call"] == round(70 / 4)


def test_cap_does_not_charge_compactions_that_do_not_shrink_the_context():
    assert whatif.cap([100, 100, 100, 100], base=100, ceiling=50, summary=0) == {"input": 400, "compactions": 0}


def test_run_skips_a_session_with_an_empty_series():
    ds = {"sessions": [
        {"id": "A", "base_override": None,
         "measurement": {"series": {"context": [100, 200, 300], "instruction_starts": [0]}}},
        {"id": "B", "base_override": None,
         "measurement": {"series": {"context": [], "instruction_starts": []}}}]}
    assert whatif.run(ds)["total"]["measured"] == 600
