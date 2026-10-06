"""Assemble per-session measurements into one survey dataset, and the derived numbers the report shows.

Everything the report prints is computed here from the dataset, so the same
dataset always gives the same report.
"""

from __future__ import annotations

import hashlib
import json

SCHEMA = "pickaxetax.survey.dataset.v1"
TYPICAL_BASE = 50_000  # a fresh Claude Code session's first call; used when a series starts mid-session


def build(subject: dict, sessions: list[dict]) -> dict:
    """sessions: [{"id", "type", "model", "origin", "span_hours", "session_list": {"input", "output"} | None,
    "measurement": <measure() output, optionally with "series">, "partial": bool, "base_override": int | None,
    "source": str}]"""
    return {"schema": SCHEMA, "subject": subject, "sessions": sessions}


def digest(dataset: dict) -> str:
    return hashlib.sha256(json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def input_of(s: dict) -> int:
    m = s["measurement"]
    return m["tokens"]["input_processed"] + (m.get("subagents") or {}).get("tokens", {}).get("input_processed", 0)


def decompose(ctx: list[int], starts: list[int], base: int) -> dict:
    """Split every call's context into the fixed base, what was already there when the
    instruction began (carried over from earlier instructions), and what grew during it."""
    fixed = carried = current = 0
    bounds = sorted(set([0] + [s for s in starts if s < len(ctx)])) + [len(ctx)]
    for a, b in zip(bounds, bounds[1:]):
        if b <= a:
            continue
        start = ctx[a]
        for x in ctx[a:b]:
            f = min(x, base)
            c = max(0, min(x, start) - base)
            fixed += f
            carried += c
            current += x - f - c
    return {"fixed": fixed, "carried": carried, "current": current}


def derive(dataset: dict) -> dict:
    ss = dataset["sessions"]
    total_in = sum(input_of(s) for s in ss)
    instructions = sum(s["measurement"]["user_instructions"] for s in ss)
    calls = sum(s["measurement"]["api_calls"] + (s["measurement"].get("subagents") or {}).get("api_calls", 0) for s in ss)
    listed = sum(s["session_list"]["input"] for s in ss if s.get("session_list"))
    active = sum(s["measurement"]["active_hours"] for s in ss)
    # output share: only sources that record final output tokens (local transcripts)
    out_src = [s for s in ss if s["source"] != "events_api"]
    out_ratio = [s["measurement"]["tokens"]["output"] / s["measurement"]["tokens"]["input_processed"] for s in out_src
                 if s["measurement"]["tokens"]["input_processed"]]
    dec = {"fixed": 0, "carried": 0, "current": 0}
    per_dec = {}
    for s in ss:
        ser = s["measurement"].get("series")
        if not ser or not ser.get("context"):
            continue
        base = s.get("base_override") or ser["context"][0]
        d = decompose(ser["context"], ser["instruction_starts"], base)
        per_dec[s["id"]] = d
        for k in dec:
            dec[k] += d[k]
    instr = sorted((x for s in ss for x in s["measurement"]["per_instruction"].get("input", [])), reverse=True)
    tot_i = sum(instr)
    cum, acc = [], 0
    for x in instr:
        acc += x
        cum.append(acc / tot_i if tot_i else 0)

    def top(frac):
        k = max(1, round(frac * len(instr)))
        return sum(instr[:k]) / tot_i if tot_i else 0

    ranked = sorted(ss, key=input_of, reverse=True)
    top5 = sum(input_of(s) for s in ranked[:5]) / total_in if total_in else 0
    return {
        "total_input": total_in, "listed_input": listed, "instructions": instructions, "calls": calls,
        "active_hours": active, "per_instruction_mean": total_in / instructions if instructions else 0,
        "output_ratio_range": (min(out_ratio), max(out_ratio)) if out_ratio else None,
        "decomposition": dec, "decomposition_by_session": per_dec,
        "instruction_inputs": instr, "instruction_cum": cum,
        "top_shares": {f: top(f) for f in (0.01, 0.05, 0.10, 0.20, 0.50)},
        "top5_sessions_share": top5, "ranked": [s["id"] for s in ranked],
        "partial": [s["id"] for s in ss if s.get("partial")],
    }
