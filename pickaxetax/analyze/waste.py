"""Token accounting: what the conversation actually cost and what it would
have cost without the waste.

Chat models re-read the whole history on every reply, so the billed input
of a conversation grows quadratically with its length. That re-reading,
rather than the visible text, is where most compute goes -- and where a
"thanks!" at turn 40 quietly costs tens of thousands of tokens.
"""

from __future__ import annotations

import os

from ..models import ASSISTANT, USER, TurnNode
from . import intent as I

# Input tokens are cheaper to process than generated ones (prefill vs decode).
# Public API price ratios put input at roughly 1/5-1/4 of output.
INPUT_WEIGHT = float(os.environ.get("PICKAXETAX_INPUT_WEIGHT", "0.25"))
# Illustrative energy factor per 1k weighted tokens. Published estimates vary
# by an order of magnitude; treat derived Wh figures as rough, not measured.
WH_PER_1K = float(os.environ.get("PICKAXETAX_WH_PER_1K", "0.5"))


def _units(inp: int, out: int) -> float:
    return inp * INPUT_WEIGHT + out


def _replay(pairs: list[tuple[TurnNode, TurnNode | None]]) -> tuple[int, int]:
    """Billed (input, output) for a sequence of (user, assistant) exchanges."""
    ctx = inp = out = 0
    for u, a in pairs:
        ctx += u.tokens
        if a is not None:
            inp += ctx
            out += a.tokens
            ctx += a.tokens
    return inp, out


def account(turns: list[TurnNode]) -> dict:
    # pair each user turn with the assistant reply that follows it
    pairs: list[tuple[TurnNode, TurnNode | None]] = []
    for t in turns:
        if t.role == USER:
            pairs.append((t, None))
        elif t.role == ASSISTANT and pairs and pairs[-1][1] is None:
            pairs[-1] = (pairs[-1][0], t)

    actual_in, actual_out = _replay(pairs)

    # --- waste attribution --------------------------------------------------
    ack_units = 0.0
    superseded_units = 0.0
    drag_tokens = 0  # off-topic history re-read on each reply
    ctx_tokens = 0
    history: list[TurnNode] = []
    superseded: set[int] = set()

    for k, (u, a) in enumerate(pairs):
        nxt = pairs[k + 1][0] if k + 1 < len(pairs) else None
        ctx_tokens += u.tokens
        history.append(u)
        if a is not None:
            reply_in = ctx_tokens
            drag_tokens += sum(h.tokens for h in history if h.branch != u.branch)
            if u.intent == I.ACK:
                u.redundant = a.redundant = True
                ack_units += _units(reply_in, a.tokens)
            elif nxt is not None and nxt.intent in (I.CORRECT, I.RETRY):
                a.redundant = True
                superseded.add(a.index)
                superseded_units += _units(reply_in, a.tokens)
            ctx_tokens += a.tokens
            history.append(a)
        if u.intent == I.RETRY:
            u.redundant = True

    # --- optimized replay: one focused chat per thread, no waste --------------
    by_branch: dict[int, list[tuple[TurnNode, TurnNode | None]]] = {}
    for k, (u, a) in enumerate(pairs):
        if u.intent == I.ACK:
            continue
        if a is not None and a.index in superseded:
            if pairs[k + 1][0].intent == I.RETRY:
                continue  # the retry restates this prompt; keep only that one
            a = None  # corrected: keep the prompt's info, drop the failed answer
        by_branch.setdefault(u.branch, []).append((u, a))
    opt_in = opt_out = 0
    for seq in by_branch.values():
        i_, o_ = _replay(seq)
        opt_in += i_
        opt_out += o_

    # lower bound: every useful prompt merged into one well-specified request
    useful_user = sum(u.tokens for seq in by_branch.values() for u, _ in seq)
    useful_out = sum(a.tokens for seq in by_branch.values() for _, a in seq if a is not None)

    actual_units = _units(actual_in, actual_out)
    opt_units = _units(opt_in, opt_out)
    one_shot_units = _units(useful_user, useful_out)

    users = [t for t in turns if t.role == USER]
    assistants = [t for t in turns if t.role == ASSISTANT]
    user_tok = sum(t.tokens for t in users)
    asst_tok = sum(t.tokens for t in assistants)
    counts = {k: sum(1 for t in turns if t.intent == k) for k in I.USER_INTENTS + I.ASSISTANT_INTENTS}

    def pct(x: float) -> float:
        return round(100.0 * x / actual_units, 1) if actual_units else 0.0

    return {
        "user_turns": len(users),
        "assistant_turns": len(assistants),
        "visible_tokens": user_tok + asst_tok,
        "user_tokens": user_tok,
        "assistant_tokens": asst_tok,
        "verbosity_ratio": round(asst_tok / user_tok, 2) if user_tok else None,
        "billed_input_tokens": actual_in,
        "billed_output_tokens": actual_out,
        "compute_units": round(actual_units),
        "optimized_compute_units": round(opt_units),
        "one_shot_compute_units": round(one_shot_units),
        "savings_pct": round(100.0 * (1 - opt_units / actual_units), 1) if actual_units else 0.0,
        "one_shot_savings_pct": round(100.0 * (1 - one_shot_units / actual_units), 1) if actual_units else 0.0,
        "waste": {
            "ack_units": round(ack_units),
            "ack_pct": pct(ack_units),
            "superseded_units": round(superseded_units),
            "superseded_pct": pct(superseded_units),
            "offtopic_context_tokens": drag_tokens,
            "offtopic_context_pct": pct(drag_tokens * INPUT_WEIGHT),
        },
        "intent_counts": {k: v for k, v in counts.items() if v},
        "max_depth": max((t.depth for t in turns), default=0),
        "branches": len({t.branch for t in users}),
        "depth_efficiency": round(max((t.depth for t in turns), default=0) / len(users), 2) if users else 0.0,
        "energy_wh_estimate": round(actual_units / 1000 * WH_PER_1K, 2),
        "energy_wh_avoidable": round((actual_units - opt_units) / 1000 * WH_PER_1K, 2),
        "assumptions": {"input_weight": INPUT_WEIGHT, "wh_per_1k_units": WH_PER_1K},
    }
