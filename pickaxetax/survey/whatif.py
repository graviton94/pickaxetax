"""What-if: the same work under a different context structure, from the per-call series alone.

These are counterfactuals, not waste judgments. Each one replays the measured context of every
call under a stated assumption and reports how much input it would have processed. They show
the size of what the structure decides, and they rest on assumptions the logs cannot check
(above all, that a short summary would have been enough). Waste is judged only under the
codebook (research/protocol/waste-codebook-v1.md).

  task_scoped  every instruction starts a fresh context: the fixed base, a summary of what came
               before, and what the instruction itself adds. (The carried-over part is replaced
               by the summary.)
  restart      the rules a user can follow: start a new session (base + summary) every N
               instructions, or at an instruction boundary once the context passes X tokens.
  cap          compaction at a lower ceiling: when the context would pass the cap it is
               compacted to the base plus a summary; compacting reads the context once more.

Only numbers are read: dataset-v2's `series` (context per main-session call, instruction starts).
"""

from __future__ import annotations

SCHEMA = "pickaxetax.survey.whatif.v1"
# the harness compacts at a ceiling: an observed compaction happens in a replay only if the replayed
# context had reached (nearly) the same size; otherwise the replay would not have compacted there
COMPACT_IF_AT_LEAST = 0.9


def _after_drop(s: int, prev: int, x: int) -> int:
    """An actual drop from `prev` to `x` (a compaction or a clear), seen by a replay at `s`."""
    return min(s, x) if s >= COMPACT_IF_AT_LEAST * prev else s
SUMMARIES = (2_000, 10_000, 30_000)
CAPS = (100_000, 200_000, 400_000)
EVERY = (3, 5, 10)
THRESHOLDS = (200_000, 400_000)


def _base(s: dict) -> int:
    ser = s["measurement"]["series"]
    return s.get("base_override") or ser["context"][0]


def restart(ctx: list[int], starts: list[int], base: int, summary: int, every: int | None = None,
            threshold: int | None = None) -> dict:
    """Replay with restarts at instruction boundaries: every `every`-th instruction, and/or once the
    replayed context before an instruction exceeds `threshold`. A restart sets the context to
    base + summary + what the new instruction's first call adds; afterwards the same growth happens
    call by call. An actual compaction applies only where the replay had reached about the same
    size (the harness compacts at its ceiling; a smaller replayed context would not have)."""
    bounds = sorted(set([0] + [x for x in starts if x < len(ctx)])) + [len(ctx)]
    total = restarts = 0
    s = ctx[0] if ctx else 0
    for n, (a, b) in enumerate(zip(bounds, bounds[1:])):
        go = n > 0 and ((every and n % every == 0) or (threshold is not None and s > threshold))
        for k in range(a, b):
            x = ctx[k]
            if k == 0:
                s = x
                total += s
                continue
            d = x - ctx[k - 1]
            cont = s + d if d >= 0 else _after_drop(s, ctx[k - 1], x)
            fresh = base + summary + max(0, d)  # a new session keeps what the new instruction adds
            if k == a and go and fresh < cont:  # nobody restarts into a bigger context
                s = fresh
                restarts += 1
            else:
                s = cont
            total += s
    return {"input": total, "restarts": restarts}


def task_scoped(ctx: list[int], starts: list[int], base: int, summary: int) -> int:
    """Input processed if each instruction after the first began from base + summary."""
    return restart(ctx, starts, base, summary, every=1)["input"]


def cap(ctx: list[int], base: int, ceiling: int, summary: int) -> dict:
    """Input processed if the context were compacted whenever it would pass `ceiling`."""
    total = compactions = 0
    s = ctx[0] if ctx else 0
    for k, x in enumerate(ctx):
        if k:
            delta = x - ctx[k - 1]
            if delta < 0:  # a real compaction or clear: applies only if the replay had reached that size
                s = _after_drop(s, ctx[k - 1], x)
            else:
                s += delta
                if s > ceiling:
                    total += s  # the compaction call reads the full context once
                    compactions += 1
                    s = base + summary + min(delta, ceiling)
        total += s
    return {"input": total, "compactions": compactions}


def run(dataset: dict) -> dict:
    out = {"schema": SCHEMA, "note": "counterfactuals from the per-call series; not waste judgments",
           "sessions": {}, "total": {}}
    tot = {"measured": 0}
    for s in dataset["sessions"]:
        ser = s["measurement"].get("series")
        if not ser:
            continue
        ctx, starts, base = ser["context"], ser["instruction_starts"], _base(s)
        r = {"measured": sum(ctx), "calls": len(ctx), "base": base}
        for m in SUMMARIES:
            r[f"task_scoped_summary_{m}"] = task_scoped(ctx, starts, base, m)
        for c in CAPS:
            r[f"cap_{c}_summary_10000"] = cap(ctx, base, c, 10_000)["input"]
        for n in EVERY:
            r[f"restart_every_{n}_summary_10000"] = restart(ctx, starts, base, 10_000, every=n)["input"]
        for x in THRESHOLDS:
            rr = restart(ctx, starts, base, 10_000, threshold=x)
            r[f"restart_above_{x}_summary_10000"] = rr["input"]
            r[f"restarts_above_{x}"] = rr["restarts"]
        out["sessions"][s["id"]] = r
        for k, v in r.items():
            if k not in ("calls", "base") and not k.startswith("restarts_"):
                tot[k] = tot.get(k, 0) + v
    tot["saved_pct"] = {k: round(100 * (1 - v / tot["measured"]), 1) for k, v in tot.items() if k != "measured"}
    out["total"] = tot
    return out
