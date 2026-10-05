"""Agenda structure: branches (topic threads) and depth (drill-down level).

Walks user turns in order and relates each one to the topic threads seen
so far. Assistant turns inherit the position of the prompt they answer.
"""

from __future__ import annotations

from ..models import ASSISTANT, USER, Edge, TurnNode
from . import intent as I

# structural edge types between turns
NEXT = "NEXT"  # chronological order
ANSWERS = "ANSWERS"  # assistant -> the user turn it responds to
DEEPENS = "DEEPENS"  # same thread, adds new sub-topics
REVISITS = "REVISITS"  # same thread, nothing new
PIVOTS = "PIVOTS"  # jumps to a new thread
RETURNS = "RETURNS"  # jumps back to an earlier thread
CORRECTS = "CORRECTS"  # user rejects the previous answer
RETRIES = "RETRIES"  # user re-asks an earlier prompt
CONTINUES = "CONTINUES"


def build_structure(turns: list[TurnNode], retry_of: dict[int, int],
                    cues: dict[int, set[str]] | None = None) -> list[Edge]:
    """``cues`` are per-turn content words used only to decide thread
    membership. They are wider than the stored topic labels (which are
    privacy-filtered) and are discarded after this call. Depth still counts
    only stored topics, so it reflects the persisted agenda."""
    cues = cues or {}
    edges: list[Edge] = []
    branches: list[dict] = []  # {"topics": set, "depth": int, "last": turn index}
    current = -1
    last_user: TurnNode | None = None

    for i, t in enumerate(turns):
        if i > 0:
            edges.append(Edge(turns[i - 1].index, t.index, NEXT))
        if t.role == ASSISTANT:
            if last_user is not None:
                t.branch, t.depth = last_user.branch, last_user.depth
                edges.append(Edge(t.index, last_user.index, ANSWERS))
                # users follow up on what the answer said, so its topics join the thread
                branches[t.branch]["topics"] |= set(t.topics)
                branches[t.branch]["cues"] |= cues.get(t.index, set())
            continue
        if t.role != USER:
            continue

        topics = set(t.topics)
        cue = cues.get(t.index, set()) | topics
        if current < 0:
            branches.append({"topics": set(topics), "cues": set(cue), "depth": 0, "last": t.index})
            current = 0
            t.branch, t.depth = 0, 0
        elif t.intent == I.RETRY:
            src = retry_of.get(t.index)
            src_turn = next((x for x in turns if x.index == src), last_user)
            t.branch, t.depth = src_turn.branch, src_turn.depth
            current = t.branch
            edges.append(Edge(t.index, src_turn.index, RETRIES))
        elif t.intent in (I.CORRECT, I.ACK, I.CONTINUE) or not cue:
            t.branch, t.depth = last_user.branch, last_user.depth
            etype = {I.CORRECT: CORRECTS, I.CONTINUE: CONTINUES}.get(t.intent, REVISITS)
            edges.append(Edge(t.index, last_user.index, etype))
            if t.intent == I.CORRECT:
                branches[t.branch]["topics"] |= topics
                branches[t.branch]["cues"] |= cue
        else:
            cur = branches[current]
            # a short clarification ("make it TypeScript") stays in the thread
            if cue & cur["cues"] or (t.intent == I.CLARIFY and t.tokens < 40):
                new = topics - cur["topics"]
                if new:
                    cur["depth"] += 1
                    edges.append(Edge(t.index, cur["last"], DEEPENS))
                else:
                    edges.append(Edge(t.index, cur["last"], REVISITS))
                cur["topics"] |= topics
                cur["cues"] |= cue
            else:
                # earlier thread with the best overlap?
                best, best_ov = -1, 0
                for bi, b in enumerate(branches):
                    ov = len(cue & b["cues"])
                    if bi != current and ov > best_ov:
                        best, best_ov = bi, ov
                if best >= 0:
                    current = best
                    cur = branches[best]
                    edges.append(Edge(t.index, cur["last"], RETURNS))
                    if topics - cur["topics"]:
                        cur["depth"] += 1
                    cur["topics"] |= topics
                    cur["cues"] |= cue
                else:
                    edges.append(Edge(t.index, last_user.index, PIVOTS))
                    branches.append({"topics": set(topics), "cues": set(cue), "depth": 0, "last": t.index})
                    current = len(branches) - 1
                    cur = branches[current]
            t.branch, t.depth = current, cur["depth"]
            cur["last"] = t.index
        last_user = t
    return edges
