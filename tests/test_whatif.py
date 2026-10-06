import json

from pickaxetax.cli import main
from pickaxetax.survey import whatif


def test_task_scoped_drops_only_the_carried_part():
    # base 100; instruction 1 grows to 300; instruction 2 starts at 300 and grows by 50
    ctx, starts = [100, 200, 300, 300, 350], [0, 3]
    assert whatif.task_scoped(ctx, starts, base=100, summary=0) == 100 + 200 + 300 + 100 + 150
    # a summary is added back, never more than what actually happened
    assert whatif.task_scoped(ctx, starts, base=100, summary=10_000) == sum(ctx)


def test_cap_compacts_and_pays_for_the_compaction():
    ctx = [100, 1100, 2100, 3100, 4100]
    r = whatif.cap(ctx, base=100, ceiling=2500, summary=0)
    # the fourth call would pass the cap: one compaction read (3,100), then 1,100 and 2,100
    assert r == {"input": 100 + 1100 + 2100 + 3100 + 1100 + 2100, "compactions": 1}
    assert whatif.cap(ctx, base=100, ceiling=10_000, summary=0) == {"input": sum(ctx), "compactions": 0}
    # a cap far below the growth per call compacts at every call and costs more than doing nothing
    assert whatif.cap([100, 200, 300, 400, 500], base=100, ceiling=250, summary=0)["input"] > 1500


def test_cli_on_a_dataset(tmp_path, capsys):
    ds = {"schema": "pickaxetax.survey.dataset.v1", "subject": {}, "sessions": [
        {"id": "S01", "base_override": None,
         "measurement": {"series": {"context": [100, 20_000, 50_000, 50_000, 60_000], "instruction_starts": [0, 3]}}}]}
    p = tmp_path / "d.json"
    p.write_text(json.dumps(ds))
    out = tmp_path / "w.json"
    assert main(["survey", "whatif", str(p), "--out", str(out)]) == 0
    r = json.loads(out.read_text())
    assert r["total"]["measured"] == 180_100
    assert r["sessions"]["S01"]["task_scoped_summary_2000"] == 100 + 20_000 + 50_000 + 2_100 + 12_100
    assert "not waste" in capsys.readouterr().out


def test_restart_rules_keep_growth_after_a_real_compaction():
    # base 10; instr 1: 10 -> 30; instr 2: 35 -> 50, compacted to 12, grows to 20; instr 3 starts at 25
    ctx, starts = [10, 20, 30, 35, 45, 50, 12, 20, 25], [0, 3, 8]
    r = whatif.restart(ctx, starts, base=10, summary=5, every=1)
    assert r["restarts"] == 2
    # instr 2 restarts at 15 and grows +10, +5; the compaction drops it to 12; the +8 after it is kept
    assert r["input"] == 10 + 20 + 30 + 15 + 25 + 30 + 12 + 20 + 15
    # a size trigger restarts only when the replayed context before the instruction is above it
    assert whatif.restart(ctx, starts, base=10, summary=5, threshold=40)["restarts"] == 0
    assert whatif.restart(ctx, starts, base=10, summary=5, threshold=15)["restarts"] == 2
