"""Turn user input (share URL, JSON export, pasted text) into RawConversations."""

from __future__ import annotations

import json

from ..models import RawConversation
from .exports import parse_json
from .share import ShareFetchError, fetch_share
from .transcript import parse_transcript

MAX_INPUT_CHARS = 4_000_000


def ingest_text(text: str) -> list[RawConversation]:
    """Pasted content: a share URL, a JSON document, or a role-marked transcript."""
    text = text.strip()
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError("input too large")
    if text.startswith("https://") and "\n" not in text:
        return fetch_share(text)
    if text[:1] in "[{":
        try:
            obj = json.loads(text)
        except ValueError:
            obj = None
        if obj is not None:
            convs = parse_json(obj)
            if not convs:
                raise ValueError("JSON did not contain a recognizable conversation")
            return convs
    return [parse_transcript(text)]


__all__ = ["ingest_text", "fetch_share", "parse_json", "parse_transcript", "ShareFetchError"]
