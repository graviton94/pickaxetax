"""High-level entry point shared by the web app and the CLI."""

from __future__ import annotations

import json
import secrets

from .analyze import analyze
from .graph import GraphStore
from .ingest import ingest_text, parse_json
from .models import RawConversation

MAX_CONVERSATIONS_PER_UPLOAD = 200


def _process(convs: list[RawConversation], store: GraphStore | None, save: bool) -> list[dict]:
    if len(convs) > MAX_CONVERSATIONS_PER_UPLOAD:
        convs = convs[:MAX_CONVERSATIONS_PER_UPLOAD]
    results = []
    salt = store.salt if store is not None else b""
    for raw in convs:
        try:
            sk = analyze(raw, salt=salt)
        except ValueError:
            continue
        finally:
            raw.turns.clear()  # drop the text as soon as it has been analyzed
        entry = {"skeleton": sk.to_dict(), "saved": False, "delete_token": None}
        if save and store is not None:
            token = secrets.token_urlsafe(18)
            if store.save(sk, delete_token=token):
                entry.update(saved=True, delete_token=token)
            else:
                entry.update(saved=True, already_stored=True)
        results.append(entry)
    if not results:
        raise ValueError("no analyzable conversation found")
    return results


def process_text(text: str, store: GraphStore | None = None, save: bool = True) -> list[dict]:
    return _process(ingest_text(text), store, save)


def process_bytes(data: bytes, store: GraphStore | None = None, save: bool = True) -> list[dict]:
    text = data.decode("utf-8-sig", errors="replace")
    try:
        convs = parse_json(json.loads(text))
    except ValueError:
        return process_text(text, store, save)
    if not convs:
        raise ValueError("JSON did not contain a recognizable conversation")
    return _process(convs, store, save)
