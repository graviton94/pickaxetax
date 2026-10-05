import json

import httpx
import pytest

from pickaxetax.bench import TASKS, run, settings_key, summarize, validate, validate_files
from pickaxetax.bench.runner import grade
from pickaxetax.cli import main


def fake_model(verbose: bool, reasoning: int = 0):
    by_prompt = {t["prompt"]: t["answers"][0] for t in TASKS}

    def handler(request):
        body = json.loads(request.content)
        answer = by_prompt[body["messages"][0]["content"]]
        text = (f"Let me think about this carefully. The answer is **{answer}**. " * 5) if verbose else answer
        n = len(text.split()) + reasoning
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": n,
                      "completion_tokens_details": {"reasoning_tokens": reasoning}},
        })
    return httpx.MockTransport(handler)


def test_concise_vs_overthinking_model():
    lean = run("http://localhost:11434", "lean", transport=fake_model(False))
    fat = run("http://localhost:11434", "fat", transport=fake_model(True, reasoning=200))
    assert lean["summary"]["accuracy"] == fat["summary"]["accuracy"] == 1.0
    assert fat["summary"]["overcompute_ratio"] > 0.95
    assert lean["summary"]["overcompute_ratio"] < fat["summary"]["overcompute_ratio"]
    assert fat["summary"]["reasoning_share"] > 0.5
    assert lean["endpoint"] == "local"
    assert validate(lean) == []


@pytest.mark.parametrize("task_id,reply,ok", [
    ("arith-add", "The answer is 42.", True),
    ("arith-add", "41", False),
    ("cap-fr", "**Paris**", True),
    ("cap-fr", "Parisian", False),
    ("ko-cap", "서울입니다.", True),
    ("yesno-even", "No, 7 is odd.", True),
    ("conv-km", "3,000", True),
])
def test_grading(task_id, reply, ok):
    task = next(t for t in TASKS if t["id"] == task_id)
    assert grade(task, reply) is ok


def test_validate_catches_tampering():
    res = run("http://localhost:11434", "m", transport=fake_model(False))
    res["summary"]["accuracy"] = 0.5
    assert "summary does not match rows" in validate(res)
    res2 = dict(res, rows=res["rows"][:-1])
    assert any("task set" in e for e in validate(res2))


def test_validate_files_naming_and_duplicates(tmp_path):
    res = run("http://localhost:11434", "m", transport=fake_model(False))
    good = tmp_path / f"{settings_key('m', res['settings'])}.json"
    good.write_text(json.dumps(res))
    bad = tmp_path / "whatever.json"
    bad.write_text(json.dumps(res))
    out = validate_files([str(tmp_path / "*.json")])
    assert out[str(good)] == []
    assert any("must be named" in e for e in out[str(bad)])


def test_cli_refuses_rerun(tmp_path, monkeypatch, capsys):
    key = settings_key("m", {"temperature": 0})
    (tmp_path / f"{key}.json").write_text("{}")
    rc = main(["bench", "run", "--base-url", "http://localhost:1", "--model", "m", "--out", str(tmp_path)])
    assert rc == 3
    assert "already measured" in capsys.readouterr().err


def test_summary_empty():
    assert summarize([])["accuracy"] == 0.0
