"""RawConversation -> Skeleton. The raw text does not leave this function."""

from __future__ import annotations

import hashlib
import hmac
from collections import Counter
from datetime import datetime, timezone

from ..models import ASSISTANT, USER, RawConversation, Skeleton, TurnNode
from ..text import detect_language, jaccard, rank_keywords, simhash, simhash_similarity, split_code, words
from ..tokens import estimate_tokens
from . import intent as I
from .depth import build_structure
from .suggest import suggest
from .waste import account

AGENDA_SIZE = 7
USER_TOPICS = 5
ASSISTANT_TOPICS = 3


def analyze(raw: RawConversation, salt: bytes = b"") -> Skeleton:
    turns_raw = [t for t in raw.turns if t.role in (USER, ASSISTANT) and t.text.strip()]
    if not any(t.role == USER for t in turns_raw):
        raise ValueError("conversation has no user turns")

    language = detect_language(" ".join(t.text[:2000] for t in turns_raw))
    ranked = rank_keywords(
        [t.text for t in turns_raw if t.role == USER],
        [t.text for t in turns_raw if t.role == ASSISTANT],
    )
    score = dict(ranked)
    agenda = [w for w, _ in ranked[:AGENDA_SIZE]]

    nodes: list[TurnNode] = []
    user_prints: list[tuple[int, int, set]] = []  # (index, simhash, word set)
    retry_of: dict[int, int] = {}
    cues: dict[int, set[str]] = {}  # transient, never stored

    for idx, rt in enumerate(turns_raw):
        tokens = estimate_tokens(rt.text)
        _, has_code = split_code(rt.text)
        ws = words(rt.text)
        wset = set(ws)
        limit = USER_TOPICS if rt.role == USER else ASSISTANT_TOPICS
        topics = sorted((w for w in wset if w in score), key=lambda w: (-score[w], w))[:limit]
        fp = simhash(rt.text, key=salt)
        cues[idx] = wset if rt.role == USER else {w for w, _ in Counter(ws).most_common(8)}

        if rt.role == USER:
            first = not user_prints
            similar = False
            if len(wset) >= 3:
                for j, jfp, jset in reversed(user_prints):
                    if simhash_similarity(fp, jfp) >= 0.9 or jaccard(wset, jset) >= 0.8:
                        retry_of[idx] = j
                        similar = True
                        break
            user_prints.append((idx, fp, wset))
            kind = I.classify_user(rt.text, tokens, similar, has_code, first=first)
        else:
            kind = I.classify_assistant(rt.text, tokens, has_code)

        nodes.append(
            TurnNode(index=idx, role=rt.role, tokens=tokens, intent=kind, topics=topics,
                     has_code=has_code, fingerprint=f"{fp:016x}")
        )

    edges = build_structure(nodes, retry_of, cues)
    cues.clear()
    metrics = account(nodes)

    digest = hmac.new(salt, "|".join(f"{n.role}:{n.fingerprint}:{n.tokens}" for n in nodes).encode(),
                      hashlib.blake2b).hexdigest()[:20]
    sk = Skeleton(
        id=digest,
        source=raw.source,
        language=language,
        agenda=agenda,
        turns=nodes,
        edges=edges,
        metrics=metrics,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    sk.suggestion = suggest(sk)
    return sk


__all__ = ["analyze"]
