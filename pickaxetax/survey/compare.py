"""Before/after comparison of two survey datasets (experiment E1, research/protocol/e1-before-after.md).

Numbers only. The primary measure is the median main-session input per instruction; its CI comes
from a bootstrap that resamples whole sessions, because instructions are clustered in sessions
(one long session's instructions rise and fall together). Each side is resampled on its own: the
two sets of sessions are different sessions, not pairs.
"""

from __future__ import annotations

import json
import os
import random

from . import dataset

SCHEMA = "pickaxetax.survey.compare.v1"
SEED = 20261006
REPS = 2000
CI = 0.90
MIN_SESSIONS, MIN_INSTRUCTIONS = 5, 30
NOTE = ("Before/after comparison, not randomized: task mix and model version (and anything else that "
        "changed between the two periods) are confounded with the change.")


def load(path: str) -> tuple[dict, dict | None]:
    """A dataset file, or a `pxt survey run` folder (its dataset.json and, when present, floor.json)."""
    floor = None
    if os.path.isdir(path):
        fp = os.path.join(path, "floor.json")
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                floor = json.load(f)
            if not isinstance(floor, dict):
                raise ValueError(f"{fp}: not a floor report (expected a JSON object)")
        path = os.path.join(path, "dataset.json")
    with open(path, encoding="utf-8") as f:
        ds = json.load(f)
    if not isinstance(ds, dict) or ds.get("schema") != dataset.SCHEMA or not isinstance(ds.get("sessions"), list):
        raise ValueError(f"{path}: not a survey dataset ({dataset.SCHEMA})")
    return ds, floor


def median(xs: list) -> float | None:
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return float(xs[n // 2]) if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def quantile(sorted_xs: list, q: float) -> float:
    """Linear interpolation between order statistics (the 'inclusive' method)."""
    pos = q * (len(sorted_xs) - 1)
    i = int(pos)
    j = min(i + 1, len(sorted_xs) - 1)
    return sorted_xs[i] + (sorted_xs[j] - sorted_xs[i]) * (pos - i)


def _m(s: dict) -> dict:
    return s.get("measurement") or {}


def instruction_inputs(ds: dict) -> list[list]:
    """Per session, its instructions' main-session input (one list per session, sessions without any left out)."""
    groups = [list((_m(s).get("per_instruction") or {}).get("input") or []) for s in ds["sessions"]]
    return [g for g in groups if g]


def bootstrap_ratio(before: list[list], after: list[list], reps: int = REPS, seed: int = SEED, ci: float = CI,
                    unit: str = "session") -> tuple[float, float] | None:
    """Percentile CI of median(after) / median(before).

    before/after: one list of per-instruction values per session. unit="session" resamples whole
    sessions (the clusters) with replacement on each side; unit="instruction" pools the instructions
    first and resamples them one by one (ignores the clustering; kept for comparison).
    """
    if unit == "instruction":
        before = [[x] for g in before for x in g]
        after = [[x] for g in after for x in g]
    elif unit != "session":
        raise ValueError(unit)
    if not before or not after:
        return None
    rng = random.Random(seed)
    ratios = []
    for _ in range(reps):
        b = median([x for g in rng.choices(before, k=len(before)) for x in g])
        a = median([x for g in rng.choices(after, k=len(after)) for x in g])
        if b:
            ratios.append(a / b)
    if not ratios:
        return None
    ratios.sort()
    tail = (1 - ci) / 2
    return quantile(ratios, tail), quantile(ratios, 1 - tail)


def summarize(ds: dict, floor: dict | None = None) -> dict:
    ss = ds["sessions"]
    groups = instruction_inputs(ds)
    steps = [x for s in ss for x in (_m(s).get("per_instruction") or {}).get("calls") or []]
    calls = sum(_m(s).get("api_calls", 0) for s in ss)
    sub_calls = sum((_m(s).get("subagents") or {}).get("api_calls", 0) for s in ss)
    comp = sum(_m(s).get("compactions", 0) for s in ss)
    ctx, dec, with_series = [], {"fixed": 0, "carried": 0, "current": 0}, 0
    for s in ss:
        ser = _m(s).get("series")
        if not ser or not ser.get("context"):
            continue
        with_series += 1
        ctx.extend(ser["context"])
        d = dataset.decompose(ser["context"], ser.get("instruction_starts") or [], s.get("base_override") or ser["context"][0])
        for k in dec:
            dec[k] += d[k]
    dec_total = sum(dec.values())
    n_instr = sum(len(g) for g in groups)
    per_session = [len((_m(s).get("per_instruction") or {}).get("input") or []) for s in ss]
    models: dict = {}
    for s in ss:
        models[s.get("model") or "?"] = models.get(s.get("model") or "?", 0) + 1
    tot = (floor or {}).get("total") or {}
    return {
        "digest": dataset.digest(ds),
        "counts": {"sessions": len(ss), "instructions": n_instr,
                   "user_instructions": sum(_m(s).get("user_instructions", 0) for s in ss),
                   "calls": calls, "subagent_calls": sub_calls, "sessions_with_series": with_series},
        "models": dict(sorted(models.items())),
        "median_input_per_instruction": median([x for g in groups for x in g]),
        "median_context_per_call": median(ctx),
        "median_steps_per_instruction": median(steps),
        "carried_share": dec["carried"] / dec_total if dec_total else None,
        "compactions_per_1000_calls": 1000 * comp / calls if calls else None,
        "instructions_per_session": n_instr / len(ss) if ss else None,
        "instructions_per_session_median": median(per_session),
        "removable_cost_pct": tot.get("floor_pct_price_weighted"),
        "removable_tokens_pct": tot.get("floor_pct_of_input"),
        # re-reads of unchanged content (codebook W1), over the floor's own calls (sub-agents included)
        "w1_per_1000_calls": 1000 * tot["W1"]["count"] / tot["calls"]
        if tot.get("calls") and isinstance(tot.get("W1"), dict) and "count" in tot["W1"] else None,
    }


SECONDARY = ("median_context_per_call", "median_steps_per_instruction", "carried_share", "compactions_per_1000_calls",
             "instructions_per_session", "instructions_per_session_median", "removable_cost_pct",
             "w1_per_1000_calls")


def _ratio(b, a):
    return a / b if (a is not None and b) else None


def compare(before: dict, after: dict, before_floor: dict | None = None, after_floor: dict | None = None,
            seed: int = SEED, reps: int = REPS) -> dict:
    sb, sa = summarize(before, before_floor), summarize(after, after_floor)
    for keys in (("removable_cost_pct", "removable_tokens_pct"), ("w1_per_1000_calls",)):
        if sb[keys[0]] is None or sa[keys[0]] is None:  # only when both sides have floor.json
            for x in (sb, sa):
                for k in keys:
                    x[k] = None
    b, a = sb["median_input_per_instruction"], sa["median_input_per_instruction"]
    ci = bootstrap_ratio(instruction_inputs(before), instruction_inputs(after), reps=reps, seed=seed) if b else None
    warnings = []
    for name, s in (("before", sb), ("after", sa)):
        c = s["counts"]
        if c["sessions"] < MIN_SESSIONS or c["instructions"] < MIN_INSTRUCTIONS:
            warnings.append(f"{name} has {c['sessions']} sessions and {c['instructions']} instructions, fewer than "
                            f"{MIN_SESSIONS} sessions or {MIN_INSTRUCTIONS} instructions: too few to read a result from.")
    return {
        "schema": SCHEMA,
        "before": sb, "after": sa,
        "primary": {"measure": "median main-session input per instruction", "before": b, "after": a,
                    "ratio": _ratio(b, a), "ci": list(ci) if ci else None, "ci_level": CI,
                    "ci_method": "percentile bootstrap, sessions resampled with replacement on each side",
                    "reps": reps, "seed": seed},
        "secondary": {k: {"before": sb[k], "after": sa[k], "ratio": _ratio(sb[k], sa[k])} for k in SECONDARY},
        "warnings": warnings,
        "note": NOTE,
    }


def compare_paths(before: str, after: str, seed: int = SEED, reps: int = REPS) -> dict:
    (bd, bf), (ad, af) = load(before), load(after)
    return compare(bd, ad, bf, af, seed=seed, reps=reps)


def _fmt(v, kind="int"):
    if v is None:
        return "—"
    if kind == "pct":
        return f"{100 * v:.1f}%"
    if kind == "pct_raw":
        return f"{v:.2f}%"
    if kind == "dec":
        return f"{v:.2f}"
    return f"{round(v):,}"


def render(r: dict) -> str:
    sb, sa, p = r["before"], r["after"], r["primary"]
    w = 34
    lines = [f"{'':{w}} {'before':>15} {'after':>15} {'after/before':>13}"]

    def row(label, b, a, kind="int", ratio=None):
        rt = f"{ratio:.3f}" if ratio is not None else ""
        lines.append(f"{label:{w}} {_fmt(b, kind):>15} {_fmt(a, kind):>15} {rt:>13}")

    for k, label in (("sessions", "sessions"), ("instructions", "instructions (with calls)"),
                     ("calls", "main-session calls"), ("subagent_calls", "sub-agent calls")):
        row(label, sb["counts"][k], sa["counts"][k])
    lines.append("primary")
    row("  median input per instruction", p["before"], p["after"], ratio=p["ratio"])
    ci = p["ci"]
    lines.append(f"  {int(100 * p['ci_level'])}% CI of the ratio: "
                 + (f"{ci[0]:.3f}–{ci[1]:.3f}" if ci else "—")
                 + f" (bootstrap over sessions, {p['reps']:,} resamples, seed {p['seed']})")
    lines.append("secondary")
    s = r["secondary"]
    for k, label, kind in (("median_context_per_call", "  median context per call", "int"),
                           ("median_steps_per_instruction", "  median steps per instruction", "dec"),
                           ("carried_share", "  input carried from finished instr.", "pct"),
                           ("compactions_per_1000_calls", "  compactions per 1,000 calls", "dec"),
                           ("instructions_per_session", "  instructions per session (mean)", "dec"),
                           ("instructions_per_session_median", "  instructions per session (median)", "dec"),
                           ("removable_cost_pct", "  removable cost (floor.json)", "pct_raw"),
                           ("w1_per_1000_calls", "  re-reads (W1) per 1,000 calls", "dec")):
        row(label, s[k]["before"], s[k]["after"], kind, s[k]["ratio"])
    lines.append(f"dataset sha256: before {sb['digest'][:16]}…, after {sa['digest'][:16]}…")
    for x in r["warnings"]:
        lines.append("warning: " + x)
    lines.append(r["note"])
    return "\n".join(lines)
