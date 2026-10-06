import json

from pickaxetax.cli import main
from pickaxetax.survey.dataset import decompose, derive

from .test_agent import T


def transcript(tmp_path):
    t = T()
    t.raw({"type": "user", "message": {"role": "user", "content": "first instruction"}})
    t.call(1000).call(1500).call(2000)
    t.raw({"type": "user", "message": {"role": "user", "content": "second instruction"}})
    t.call(2600).call(3000)
    return t.write(tmp_path / "s.jsonl")


def test_decompose_splits_fixed_carried_current():
    d = decompose([100, 150, 200, 260, 300], [0, 3], base=100)
    # instruction 1 starts at 100: all growth is current; instruction 2 starts at 260: 160 carried per call
    assert d == {"fixed": 500, "carried": 160 * 2, "current": 50 + 100 + 0 + 40}


def test_measure_and_report_are_deterministic(tmp_path, capsys):
    path = transcript(tmp_path)
    ds_path, r1, r2 = tmp_path / "ds.json", tmp_path / "r1.html", tmp_path / "r2.html"
    assert main(["survey", "measure", path, "--out", str(ds_path)]) == 0
    ds = json.loads(ds_path.read_text())
    s = ds["sessions"][0]["measurement"]
    assert s["user_instructions"] == 2 and s["series"]["instruction_starts"] == [0, 3]
    assert "first instruction" not in ds_path.read_text()  # numbers only
    assert main(["survey", "report", str(ds_path), "--out", str(r1)]) == 0
    assert main(["survey", "report", str(ds_path), "--out", str(r2)]) == 0
    assert r1.read_bytes() == r2.read_bytes()
    dv = derive(ds)
    assert dv["instructions"] == 2 and abs(sum(dv["top_shares"].values()) - sum(dv["top_shares"].values())) == 0
    assert "<title>" in r1.read_text()
