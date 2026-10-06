"""What-if: the same work under a different context structure, from the per-call series alone.

These are counterfactuals, not waste judgments. Each one replays the measured context of every
call under a stated assumption and reports how much input it would have processed. They show
the size of what the structure decides, and they rest on assumptions the logs cannot check
(above all, that a short summary would have been enough). Waste is judged only under the
codebook (research/protocol/waste-codebook-v1.md).

  task_scoped  every instruction starts a fresh context: the fixed base, a summary of what came
               before, and what the instruction itself adds. (The carried-over part is replaced
               by the summary.)
  cap          compaction at a lower ceiling: when the context would pass the cap it is
               compacted to the base plus a summary; compacting reads the context once more.

Only numbers are read: dataset-v2's `series` (context per main-session call, instruction starts).
"""

from __future__ import annotations

SCHEMA = "pickaxetax.survey.whatif.v1"
SUMMARIES = (2_000, 10_000, 30_000)
CAPS = (100_000, 200_000, 400_000)


def _base(s: dict) -> int:
    ser = s["measurement"]["series"]
    return s.get("base_override") or ser["context"][0]


def task_scoped(ctx: list[int], starts: list[int], base: int, summary: int) -> int:
    """Input processed if each instruction after the first began from base + summary."""
    total = 0
    bounds = sorted(set([0] + [x for x in starts if x < len(ctx)])) + [len(ctx)]
    for n, (a, b) in enumerate(zip(bounds, bounds[1:])):
        start = ctx[a]
        carry = summary if n else 0
        for x in ctx[a:b]:
            fixed = min(x, base)
            carried = max(0, min(x, start) - base)
            current = x - fixed - carried
            total += min(x, fixed + current + carry)  # never more than what actually happened
    return total


def cap(ctx: list[int], base: int, ceiling: int, summary: int) -> dict:
    """Input processed if the context were compacted whenever it would pass `ceiling`."""
    total = compactions = 0
    s = ctx[0]
    for k, x in enumerate(ctx):
        if k:
            delta = x - ctx[k - 1]
            if delta < 0:  # a real compaction or clear: the replay shrinks at least as much
                s = min(s, x)
            else:
                s += delta
                if s > ceiling:
                    total += s  # the compaction call reads the full context once
                    compactions += 1
                    s = min(x, base + summary + min(delta, ceiling))
        total += min(s, x) if k else x
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
        out["sessions"][s["id"]] = r
        for k, v in r.items():
            if k not in ("calls", "base"):
                tot[k] = tot.get(k, 0) + v
    tot["saved_pct"] = {k: round(100 * (1 - v / tot["measured"]), 1) for k, v in tot.items() if k != "measured"}
    out["total"] = tot
    return out
