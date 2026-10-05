"""Validate the lexical use detector against human judgement, locally.

Pairs (segment, later call) are sampled in two strata: pairs the detector
marked as a use and pairs it did not. A person reads each pair in the terminal
and answers whether the call needed the segment. Precision is estimated from
the first stratum, the miss rate of the detector from the second, and recall
by re-weighting with the stratum sizes. Only pair ids (hashes) and answers are
saved; the text is shown on screen and never written anywhere.
"""

from __future__ import annotations

import hashlib
import json
import random

from ..agent.bound import link
from .stats import wilson
from .trace import load

PREVIEW = 700


def pairs(sessions) -> tuple[list, list]:
    hit, miss = [], []
    for si, s in enumerate(sessions):
        t = s.trace
        link(t)
        outputs_text = _outputs_text(t)
        for gi, g in enumerate(t.segments):
            if g.kind == "unattributed" or g.end <= g.birth + 1 or not g.text:
                continue
            refs = set(g.refs)
            for k in range(g.birth + 1, g.end):
                key = hashlib.sha256(f"{s.fingerprint}|{gi}|{k}".encode()).hexdigest()[:16]
                (hit if k in refs else miss).append((key, g, outputs_text.get(k, "")))
    return hit, miss


def _outputs_text(t) -> dict[int, str]:
    # assistant_text and tool_input segments born at k+1 are the output of call k
    out: dict[int, list[str]] = {}
    for g in t.segments:
        if g.kind in ("assistant_text", "tool_input", "persisted_write") and g.text:
            out.setdefault(g.birth - 1, []).append(g.text)
    return {k: "\n".join(v) for k, v in out.items()}


def interactive(paths: list[str], n: int, labels_path: str, source: str | None = None, seed: int = 7) -> dict:
    sessions = [s for p in paths for s in load(p, source, keep_text=True)]
    hit, miss = pairs(sessions)
    try:
        with open(labels_path, encoding="utf-8") as f:
            store = json.load(f)
    except (OSError, ValueError):
        store = {"hit": {}, "miss": {}, "population": {}}
    store["population"] = {"hit": len(hit), "miss": len(miss)}
    rng = random.Random(seed)
    todo = [("hit", x) for x in rng.sample(hit, min(len(hit), n // 2))] + [("miss", x) for x in rng.sample(miss, min(len(miss), n - n // 2))]
    rng.shuffle(todo)  # the labeler does not know which stratum a pair came from
    for i, (stratum, (key, seg, out)) in enumerate(todo, 1):
        if key in store[stratum]:
            continue
        print(f"\n─── {i}/{len(todo)} ─── earlier context ({seg.kind}):\n{seg.text[:PREVIEW]}")
        print(f"\n─── what the model produced at this step:\n{out[:PREVIEW] or '(nothing visible)'}")
        ans = input("\nDid this step need that earlier context? [y]es / [n]o / [s]kip / [q]uit: ").strip().lower()[:1]
        if ans == "q":
            break
        if ans in ("y", "n"):
            store[stratum][key] = ans == "y"
            with open(labels_path, "w", encoding="utf-8") as f:
                json.dump(store, f)
    return summarize(store)


def summarize(store: dict) -> dict:
    h = list(store["hit"].values())
    m = list(store["miss"].values())
    prec = wilson(sum(h), len(h))  # P(needed | detected)
    fnr = wilson(sum(m), len(m))  # P(needed | not detected)
    pop = store.get("population", {})
    tp = prec[0] * pop.get("hit", 0) if h else float("nan")
    fn = fnr[0] * pop.get("miss", 0) if m else float("nan")
    recall = tp / (tp + fn) if h and m and (tp + fn) else float("nan")
    r = lambda v: None if v != v else round(100 * v, 1)
    return {"labeled": {"detected": len(h), "not_detected": len(m)},
            "precision_pct": [r(x) for x in prec], "needed_but_not_detected_pct": [r(x) for x in fnr],
            "recall_pct_estimate": r(recall), "population": pop}
