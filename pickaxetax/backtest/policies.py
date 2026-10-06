"""Online context policies, replayed against a session's reference string.

An online policy decides what to keep before each call, knowing only the past.
When a call needs a segment the policy dropped, the segment is fetched back at
cost ``penalty`` (and counted as a miss: a step that would have run without
information it used). This is a standard trace-driven cache simulation; the
offline optimum from ``agent.bound`` is the yardstick.
"""

from __future__ import annotations

import math

from ..agent.bound import Trace

FAMILIES = ("full", "window", "recency", "pointer")


def simulate(t: Trace, family: str, n: float = math.inf, penalty: float = 1_000, stub: int = 20) -> dict:
    """Replay one policy. Costs are token-calls, comparable with ``bound``.

    full     keep everything (what the agent or chat actually did)
    window   keep a segment for ``n`` calls after it arrived
    recency  keep a segment while it was used within the last ``n`` calls
    pointer  like recency, but an evicted segment leaves a ``stub``-token pointer
    """
    measured = sum(t.contexts)
    resident = sum(s.tokens * max(0, s.end - s.birth) for s in t.segments)
    cost = float(measured - resident)  # base context: kept by every policy
    refs = misses = 0
    for s in t.segments:
        if s.end <= s.birth:
            continue
        if s.kind == "unattributed" or family == "full":
            cost += s.tokens * (s.end - s.birth)
            if family == "full":
                refs += max(0, len(s.refs) - 1)
            continue
        need = set(s.refs)
        last = s.birth
        cost += s.tokens  # it arrives and the next call consumes it
        for k in range(s.birth + 1, s.end):
            keep = (k - s.birth) < n if family == "window" else (k - last) <= n
            if k in need:
                refs += 1
                last = k
                if keep:
                    cost += s.tokens
                else:
                    cost += s.tokens + penalty
                    misses += 1
            elif keep:
                cost += s.tokens
            elif family == "pointer":
                cost += min(stub, s.tokens)
    return {"cost": cost, "measured": measured, "refs": refs, "misses": misses,
            "saved_pct": 100 * (measured - cost) / measured if measured else 0.0,
            "miss_rate": 100 * misses / refs if refs else 0.0}
