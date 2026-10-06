"""Turn any supported session (agent transcript or chat export) into a Trace."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from ..agent.bound import TOKEN_RE, Segment, Trace, calibrate, read_trace
from ..ingest import parse_json, parse_transcript
from ..models import USER, RawConversation
from ..tokens import estimate_tokens


@dataclass
class Session:
    fingerprint: str  # sha256 of the file bytes + position: stable, reveals nothing
    source: str
    kind: str  # "agent" (measured usage, calibrated) | "chat" (estimated tokens)
    trace: Trace
    calibration: float | None = None


def from_conversation(conv: RawConversation, keep_text: bool = False) -> Trace:
    """A chat as a trace: every assistant reply is a call that re-reads all earlier turns.

    Chat exports carry no usage, so sizes are estimates and the (unknown) system
    prompt is left out. This is the full-history baseline: providers that trim or
    summarize long chats server-side process less than this.
    """
    t = Trace()
    for turn in conv.turns:
        n = estimate_tokens(turn.text)
        terms = frozenset(TOKEN_RE.findall(turn.text))
        text = turn.text if keep_text else ""
        if turn.role == USER:
            if n:
                t.segments.append(Segment("user_prompt", n, len(t.contexts), terms, text=text))
            continue
        t.contexts.append(sum(s.tokens for s in t.segments))
        t.outputs.append(set(terms))
        if n:
            t.segments.append(Segment("assistant_text", n, len(t.contexts), terms, text=text))
    return t


def _is_agent_jsonl(head: bytes) -> bool:
    for line in head.splitlines()[:50]:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and ("sessionId" in d or d.get("type") in ("assistant", "user", "system", "summary")):
            return True
    return False


def load(path: str, source: str | None = None, keep_text: bool = False, calibrated: bool = True) -> list[Session]:
    """Every session in a file. ``source`` overrides the detected provider."""
    with open(path, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    if path.endswith(".jsonl") and _is_agent_jsonl(raw[:200_000]):
        t = read_trace(path, keep_text=keep_text)
        factor = calibrate(t) if calibrated else None
        return [Session(digest + ":0", source or "claude-code", "agent", t, factor)]
    text = raw.decode("utf-8", errors="replace").strip()
    convs: list[RawConversation]
    if text[:1] in "[{":
        try:
            convs = parse_json(json.loads(text))
        except ValueError:
            convs = [parse_transcript(text)]
    else:
        convs = [parse_transcript(text)]
    out = []
    for i, c in enumerate(convs):
        out.append(Session(f"{digest}:{i}", source or c.source, "chat", from_conversation(c, keep_text)))
    return out
