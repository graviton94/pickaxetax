"""Run the pre-registered backtest over many sessions and build the report."""

from __future__ import annotations

import hashlib
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..agent.bound import METHOD, PCT_KEYS, bound, link
from . import (BOOTSTRAP, DEFAULT_N, DEV_SHARE, GRID, LENGTH_BUCKETS, MAX_MISS_RATE, MIN_CALLS, MIN_CELL, MIN_DEV,
               PENALTIES, PRIMARY_PENALTY, PROTOCOL, SEED, SENSITIVITY_COMMON, SENSITIVITY_MIN_SHARED, STUB_TOKENS)
from .policies import simulate
from .stats import median, summary
from .trace import Session, load

ONLINE = ("window", "recency", "pointer")


def bucket(calls: int) -> str:
    for lo, hi in LENGTH_BUCKETS:
        if calls >= lo and (hi is None or calls <= hi):
            return f"{lo}-{hi}" if hi else f"{lo}+"
    return "excluded"


def split_of(fingerprint: str) -> str:
    return "dev" if hashlib.sha256(fingerprint.encode()).digest()[0] < DEV_SHARE else "test"


def sensitivity(s: Session, raw: Session | None) -> list[list[float]]:
    """[variant, min_shared, common_frac, P0, Pinf] per pre-registered cell; variant 0 = agent without calibration."""
    cells = []
    for variant, sess in ((1, s), (0, raw)):
        if sess is None:
            continue
        for ms in SENSITIVITY_MIN_SHARED:
            for cf in SENSITIVITY_COMMON:
                link(sess.trace, ms, cf)
                p = bound(sess.trace, (0, math.inf))["policies"]
                cells.append([variant, ms, cf, p["P=0"]["avoidable_pct"], p["P=inf"]["avoidable_pct"]])
    return cells


def measure(s: Session, raw: Session | None = None) -> dict:
    """Every per-session number the protocol defines. ``raw``: the same agent session without calibration."""
    t = s.trace
    cells = sensitivity(s, raw)
    link(t)  # primary detection settings, after the sensitivity cells
    b = bound(t, PENALTIES)
    calls = len(t.contexts)
    row = {
        "source": s.source, "kind": s.kind, "calls": calls, "bucket": bucket(calls), "split": split_of(s.fingerprint),
        "measured_input": b["measured_input"],
        "pinned_pct": round(100 * b["pinned_input"] / b["measured_input"], 2) if b["measured_input"] else 0.0,
        "oracle": {PCT_KEYS[k]: v["avoidable_pct"] for k, v in b["policies"].items()},
        "online": {},
    }
    row["paging_minus_forgetting"] = round(row["oracle"]["P0"] - row["oracle"]["Pinf"], 2)
    row["_sensitivity"] = cells
    oracle_p = bound(t, (PRIMARY_PENALTY,))["policies"][f"P={PRIMARY_PENALTY}"]["avoidable_pct"]
    for fam in ONLINE:
        for n in GRID:
            r = simulate(t, fam, n, PRIMARY_PENALTY, STUB_TOKENS)
            row["online"][f"{fam}-{n}"] = {
                "saved_pct": round(r["saved_pct"], 2), "miss_rate": round(r["miss_rate"], 2),
                "gap_closed_pct": round(100 * r["saved_pct"] / oracle_p, 1) if oracle_p > 0 else None,
            }
    return row


def tune(dev: list[dict]) -> dict[str, dict]:
    """Pick N per family on the dev split: lowest median cost with median miss rate <= MAX_MISS_RATE."""
    chosen = {}
    for fam in ONLINE:
        if len(dev) < MIN_DEV:
            chosen[fam] = {"n": DEFAULT_N, "why": f"dev split has {len(dev)} < {MIN_DEV} sessions: pre-registered default"}
            continue
        ok = []
        for n in GRID:
            saved = median([r["online"][f"{fam}-{n}"]["saved_pct"] for r in dev])
            miss = median([r["online"][f"{fam}-{n}"]["miss_rate"] for r in dev])
            if miss <= MAX_MISS_RATE:
                ok.append((saved, -n, n, miss))
        if ok:
            saved, _, n, miss = max(ok)
            chosen[fam] = {"n": n, "why": f"dev median saved {saved:.1f}%, miss rate {miss:.1f}%"}
        else:
            chosen[fam] = {"n": GRID[-1], "why": f"no N met the {MAX_MISS_RATE}% miss-rate limit on dev: largest N"}
    return chosen


def aggregate(rows: list[dict], chosen: dict) -> dict:
    def block(rs: list[dict], salt: int) -> dict:
        out = {
            "sessions": len(rs),
            "insufficient": len(rs) < MIN_CELL,
            "oracle_P0": summary([r["oracle"]["P0"] for r in rs], SEED + salt, BOOTSTRAP),
            "oracle_Pinf": summary([r["oracle"]["Pinf"] for r in rs], SEED + salt + 1, BOOTSTRAP),
            "paging_minus_forgetting": summary([r["paging_minus_forgetting"] for r in rs], SEED + salt + 2, BOOTSTRAP),
            "pinned_pct": summary([r["pinned_pct"] for r in rs], SEED + salt + 3, BOOTSTRAP),
        }
        for i, fam in enumerate(ONLINE):
            key = f"{fam}-{chosen[fam]['n']}"
            out[f"online_{fam}"] = {
                "n": chosen[fam]["n"],
                "saved_pct": summary([r["online"][key]["saved_pct"] for r in rs], SEED + salt + 10 + i, BOOTSTRAP),
                "miss_rate": summary([r["online"][key]["miss_rate"] for r in rs], SEED + salt + 20 + i, BOOTSTRAP),
            }
        return out

    test = [r for r in rows if r["split"] == "test"]
    grid = {}
    for r in rows:
        for cal, ms, cf, p0, pinf in r["_sensitivity"]:
            grid.setdefault((cal, ms, cf), []).append((p0, pinf))
    sens = [{"variant": "primary" if cal else "agents_uncalibrated", "min_shared": ms, "common_frac": cf, "sessions": len(v),
             "median_P0": round(median([a for a, _ in v]), 1), "median_Pinf": round(median([b for _, b in v]), 1),
             "median_difference": round(median([a - b for a, b in v]), 1)} for (cal, ms, cf), v in sorted(grid.items())]
    agg = {"sensitivity": sens,
           "paging_beats_forgetting_in_every_cell": all(c["median_difference"] > 0 for c in sens),
           "all_sessions": block(rows, 0), "test_split": block(test, 100), "by_source": {}, "by_length": {}, "by_source_and_length": {}}
    for i, src in enumerate(sorted({r["source"] for r in rows})):
        agg["by_source"][src] = block([r for r in rows if r["source"] == src], 1000 + 100 * i)
    for i, bk in enumerate(sorted({r["bucket"] for r in rows})):
        agg["by_length"][bk] = block([r for r in rows if r["bucket"] == bk], 5000 + 100 * i)
    cells = sorted({(r["source"], r["bucket"]) for r in rows})
    for i, (src, bk) in enumerate(cells):
        agg["by_source_and_length"][f"{src}|{bk}"] = block([r for r in rows if r["source"] == src and r["bucket"] == bk], 9000 + 100 * i)
    return agg


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=Path(__file__).resolve().parent).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def run(paths: list[str], source: str | None = None, contributor: str = "1") -> tuple[dict, list[str]]:
    """Returns (publishable report, private manifest of session fingerprints)."""
    sessions, raws = [], {}
    for p in paths:
        loaded = load(p, source)
        sessions += loaded
        if any(s.kind == "agent" for s in loaded):
            raws.update({s.fingerprint: s for s in load(p, source, calibrated=False)})
    excluded = sum(1 for s in sessions if len(s.trace.contexts) < MIN_CALLS)
    kept = [s for s in sessions if len(s.trace.contexts) >= MIN_CALLS]
    rows = [measure(s, raws.get(s.fingerprint)) for s in kept]
    chosen = tune([r for r in rows if r["split"] == "dev"])
    manifest = sorted(s.fingerprint for s in kept)
    report = {
        "protocol": PROTOCOL,
        "method": METHOD,
        "tool_version": __version__,
        "git_sha": _git_sha(),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "manifest_digest": hashlib.sha256("\n".join(manifest).encode()).hexdigest(),
        "contributors": 1,
        "contributor_digest": hashlib.sha256(contributor.encode()).hexdigest()[:12],
        "sessions": {"loaded": len(sessions), "excluded_short": excluded, "kept": len(kept),
                     "dev": sum(1 for r in rows if r["split"] == "dev"), "test": sum(1 for r in rows if r["split"] == "test")},
        "tuned_on_dev": chosen,
        "aggregate": aggregate(rows, chosen) if rows else {},
        "per_session": [{k: v for k, v in r.items() if k not in ("online", "_sensitivity")} | {
            "online": {fam: r["online"][f"{fam}-{chosen[fam]['n']}"] for fam in ONLINE}} for r in rows],
    }
    return report, manifest


def nan_to_none(x):
    if isinstance(x, float) and math.isnan(x):
        return None
    if isinstance(x, dict):
        return {k: nan_to_none(v) for k, v in x.items()}
    if isinstance(x, list):
        return [nan_to_none(v) for v in x]
    return x
