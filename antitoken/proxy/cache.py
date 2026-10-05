"""Exact-duplicate response cache, stored only on the user's machine.

By default only deterministic requests (temperature 0) are cached: with
sampling on, an identical request may be a deliberate regeneration.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time

_IGNORED = {"stream", "stream_options", "user", "metadata", "store"}


def request_key(provider: str, body: dict) -> str:
    canon = {k: v for k, v in body.items() if k not in _IGNORED}
    return hashlib.sha256(f"{provider}\n{json.dumps(canon, sort_keys=True, ensure_ascii=False)}".encode()).hexdigest()


def cacheable(body: dict, cache_all: bool) -> bool:
    if body.get("tools") or body.get("functions"):
        return False
    if cache_all:
        return True
    return body.get("temperature") == 0 and int(body.get("n") or 1) == 1


class ResponseCache:
    def __init__(self, path: str, ttl_seconds: int = 7 * 24 * 3600):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, ts REAL, body BLOB, output_tokens INTEGER)")
        self.ttl = ttl_seconds
        self.lock = threading.Lock()

    def get(self, key: str) -> tuple[bytes, int] | None:
        with self.lock:
            row = self.db.execute("SELECT ts, body, output_tokens FROM cache WHERE key=?", (key,)).fetchone()
        if not row or time.time() - row[0] > self.ttl:
            return None
        return row[1], row[2]

    def put(self, key: str, body: bytes, output_tokens: int) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)", (key, time.time(), body, output_tokens))
