"""Run the over-computation benchmark against any OpenAI-compatible endpoint
(Ollama, llama.cpp, vLLM, LM Studio, OpenRouter, OpenAI, ...).

Built for crowd compute at zero cost to the project: contributors run it
on their own machine or key and submit the result file by pull request.
Each (model, settings, task set) is run once -- an existing result blocks
a re-run, so the benchmark never becomes the waste it measures.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import platform
import re
from datetime import datetime, timezone

import httpx

from ..tokens import estimate_tokens
from .tasks import TASKS, TASKSET_VERSION

RESULT_SCHEMA = "pickaxetax.bench.v1"
HARNESS_VERSION = "0.1.0"
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def grade(task: dict, reply: str) -> bool:
    text = re.sub(r"[*_`\"'“”‘’]", "", reply or "").strip().lower()
    if task["kind"] == "number":
        nums = _NUM.findall(text.replace(",", ""))
        return bool(nums) and any(n in task["answers"] for n in nums[:3])
    # Latin answers must be whole words; CJK/Hangul answers take attached endings ("서울입니다")
    return any(
        (a in text) if not a.isascii() else bool(re.search(rf"(?<!\w){re.escape(a)}(?!\w)", text))
        for a in task["answers"]
    )


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", s.lower()).strip("-")[:80]


def settings_key(model: str, settings: dict) -> str:
    h = hashlib.sha256(json.dumps({"model": model, **settings}, sort_keys=True).encode()).hexdigest()[:8]
    return f"{slug(model)}__{h}__{TASKSET_VERSION}"


def existing_result(results_dir: str, key: str) -> str | None:
    path = os.path.join(results_dir, f"{key}.json")
    return path if os.path.exists(path) else None


def run(
    base_url: str,
    model: str,
    api_key: str | None = None,
    settings: dict | None = None,
    max_tokens: int = 1024,
    transport: httpx.BaseTransport | None = None,
    progress=None,
) -> dict:
    settings = {"temperature": 0, **(settings or {})}
    url = base_url.rstrip("/")
    url = url + ("/chat/completions" if url.endswith("/v1") else "/v1/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    rows = []
    with httpx.Client(transport=transport, timeout=300) as client:
        for task in TASKS:
            body = {"model": model, "messages": [{"role": "user", "content": task["prompt"]}],
                    "max_tokens": max_tokens, **settings}
            r = client.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            reply = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            usage = data.get("usage") or {}
            measured = "completion_tokens" in usage
            completion = int(usage.get("completion_tokens") or estimate_tokens(reply))
            reasoning = int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
            minimal = max(1, estimate_tokens(task["answers"][0]))
            rows.append({
                "id": task["id"], "correct": grade(task, reply), "completion_tokens": completion,
                "reasoning_tokens": reasoning, "min_tokens": minimal, "measured": measured,
                "reply_head": reply.strip()[:80],
            })
            if progress:
                progress(task, rows[-1])
    return build_result(model, settings, max_tokens, rows, endpoint=_endpoint_kind(base_url))


def _endpoint_kind(base_url: str) -> str:
    host = httpx.URL(base_url).host or ""
    return "local" if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1") else "remote"


def summarize(rows: list[dict]) -> dict:
    correct = [r for r in rows if r["correct"]]
    spent = sum(r["completion_tokens"] for r in correct)
    minimal = sum(r["min_tokens"] for r in correct)
    reasoning = sum(r["reasoning_tokens"] for r in correct)
    return {
        "tasks": len(rows),
        "accuracy": round(len(correct) / len(rows), 3) if rows else 0.0,
        "completion_tokens_per_correct": round(spent / len(correct), 1) if correct else None,
        "overcompute_ratio": round(1 - minimal / spent, 3) if spent else None,
        "reasoning_share": round(reasoning / spent, 3) if spent else None,
        "measured_share": round(sum(r["measured"] for r in rows) / len(rows), 3) if rows else 0.0,
    }


def build_result(model: str, settings: dict, max_tokens: int, rows: list[dict], endpoint: str) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "harness_version": HARNESS_VERSION,
        "taskset": TASKSET_VERSION,
        "model": model,
        "settings": settings,
        "max_tokens": max_tokens,
        "endpoint": endpoint,
        "run_at": datetime.now(timezone.utc).date().isoformat(),
        "platform": platform.system().lower(),
        "summary": summarize(rows),
        "rows": rows,
    }


# --- validation (used by CI on contributed result files) -------------------

def validate(result: dict) -> list[str]:
    errs = []
    for k in ("schema", "harness_version", "taskset", "model", "settings", "summary", "rows"):
        if k not in result:
            errs.append(f"missing field: {k}")
    if errs:
        return errs
    if result["schema"] != RESULT_SCHEMA:
        errs.append(f"unknown schema {result['schema']!r}")
    if result["taskset"] != TASKSET_VERSION:
        errs.append(f"task set {result['taskset']} does not match current {TASKSET_VERSION}")
    ids = [r.get("id") for r in result["rows"]]
    if sorted(ids) != sorted(t["id"] for t in TASKS):
        errs.append("rows do not cover exactly the task set")
    for r in result["rows"]:
        if not isinstance(r.get("completion_tokens"), int) or r["completion_tokens"] < 0:
            errs.append(f"{r.get('id')}: bad completion_tokens")
    if not errs and summarize(result["rows"]) != result["summary"]:
        errs.append("summary does not match rows")
    return errs


def validate_files(paths: list[str]) -> dict[str, list[str]]:
    out = {}
    seen = {}
    expanded = (glob.glob(pat) if any(ch in pat for ch in "*?[") else [pat] for pat in paths)
    for p in sorted({x for group in expanded for x in group}):
        try:
            with open(p, encoding="utf-8") as f:
                res = json.load(f)
        except (OSError, ValueError) as e:
            out[p] = [f"unreadable: {e}"]
            continue
        errs = validate(res)
        if not errs:
            key = settings_key(res["model"], res["settings"])
            if os.path.basename(p) != f"{key}.json":
                errs.append(f"file must be named {key}.json")
            if key in seen:
                errs.append(f"duplicate of {seen[key]}")
            seen[key] = p
        out[p] = errs
    return out
