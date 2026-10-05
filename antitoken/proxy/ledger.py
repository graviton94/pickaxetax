"""Local measurement ledger: counts only, never text, never keys."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

DEFAULT_PATH = os.environ.get("ANTITOKEN_LEDGER", str(Path.home() / ".antitoken" / "ledger.sqlite3"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    action TEXT NOT NULL,           -- forwarded | cache_hit | gratitude_local | error
    streamed INTEGER NOT NULL,
    measured INTEGER NOT NULL,      -- 1 = usage reported by the provider, 0 = estimated
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    reasoning_tokens INTEGER NOT NULL DEFAULT 0,
    cached_input_tokens INTEGER NOT NULL DEFAULT 0,
    history_tokens INTEGER NOT NULL DEFAULT 0,   -- input that was re-sent history
    avoided_input INTEGER NOT NULL DEFAULT 0,
    avoided_output INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS requests_ts ON requests(ts);
"""

FIELDS = [
    "provider", "model", "action", "streamed", "measured", "input_tokens", "output_tokens",
    "reasoning_tokens", "cached_input_tokens", "history_tokens", "avoided_input", "avoided_output",
]


class Ledger:
    def __init__(self, path: str = DEFAULT_PATH):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self.lock = threading.Lock()

    def record(self, **row) -> None:
        values = [row.get(f, 0) for f in FIELDS]
        values[FIELDS.index("streamed")] = int(bool(row.get("streamed")))
        values[FIELDS.index("measured")] = int(bool(row.get("measured")))
        with self.lock, self.db:
            self.db.execute(
                f"INSERT INTO requests(ts, {', '.join(FIELDS)}) VALUES (?{', ?' * len(FIELDS)})",
                [time.time(), *values],
            )

    def summary(self, since: float = 0.0) -> dict:
        with self.lock:
            rows = self.db.execute(
                "SELECT provider, model, action, COUNT(*), SUM(input_tokens), SUM(output_tokens), "
                "SUM(reasoning_tokens), SUM(cached_input_tokens), SUM(history_tokens), "
                "SUM(avoided_input), SUM(avoided_output), SUM(measured) "
                "FROM requests WHERE ts >= ? GROUP BY provider, model, action ORDER BY provider, model, action",
                (since,),
            ).fetchall()
        groups = []
        tot = dict.fromkeys(["requests", "input_tokens", "output_tokens", "reasoning_tokens", "cached_input_tokens",
                             "history_tokens", "avoided_input", "avoided_output", "measured_requests"], 0)
        for p, m, a, n, i, o, r, c, h, ai, ao, meas in rows:
            g = {"provider": p, "model": m, "action": a, "requests": n, "input_tokens": i or 0,
                 "output_tokens": o or 0, "reasoning_tokens": r or 0, "cached_input_tokens": c or 0,
                 "history_tokens": h or 0, "avoided_input": ai or 0, "avoided_output": ao or 0,
                 "measured_requests": meas or 0}
            groups.append(g)
            for k in tot:
                tot[k] += g[k]
        spent = tot["input_tokens"] + tot["output_tokens"]
        avoided = tot["avoided_input"] + tot["avoided_output"]
        tot["history_share_pct"] = round(100 * tot["history_tokens"] / tot["input_tokens"], 1) if tot["input_tokens"] else 0.0
        tot["avoided_pct"] = round(100 * avoided / (spent + avoided), 1) if spent + avoided else 0.0
        return {"totals": tot, "groups": groups}

    def export(self) -> str:
        """Anonymous aggregate for voluntary contribution (no text, no timestamps finer than a day)."""
        with self.lock:
            rows = self.db.execute(
                "SELECT date(ts, 'unixepoch'), provider, model, action, COUNT(*), SUM(input_tokens), "
                "SUM(output_tokens), SUM(reasoning_tokens), SUM(history_tokens), SUM(avoided_input), "
                "SUM(avoided_output), SUM(measured) FROM requests GROUP BY 1, 2, 3, 4 ORDER BY 1"
            ).fetchall()
        keys = ["day", "provider", "model", "action", "requests", "input_tokens", "output_tokens",
                "reasoning_tokens", "history_tokens", "avoided_input", "avoided_output", "measured_requests"]
        return json.dumps({"schema": "antitoken.ledger.v1", "rows": [dict(zip(keys, r)) for r in rows]}, indent=2)

    def close(self) -> None:
        self.db.close()
