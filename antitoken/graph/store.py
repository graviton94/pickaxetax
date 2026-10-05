"""Property-graph store on SQLite.

A minimal labeled-property-graph (nodes + typed edges, JSON properties) so
the project runs anywhere with zero infrastructure. ``export.py`` emits
Cypher for loading the same graph into Neo4j/Memgraph when it outgrows
SQLite.

Graph model::

    (:Conversation)-[:HAS_TURN]->(:Turn)-[:ABOUT]->(:Topic)
    (:Turn)-[:NEXT|ANSWERS|DEEPENS|PIVOTS|RETURNS|CORRECTS|RETRIES|...]->(:Turn)
    (:Conversation)-[:COVERS {rank}]->(:Topic)
    (:Topic)-[:CO_OCCURS {count}]->(:Topic)       # global, aggregated

Public (cross-user) reads go through k-anonymity: a topic is only exposed
once it appears in at least ``k`` distinct conversations.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
from itertools import combinations
from typing import Any, Iterable

from ..models import Edge, Skeleton, TurnNode

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    props TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS nodes_label ON nodes(label);
CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    type TEXT NOT NULL,
    props TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (src, dst, type)
);
CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst, type);
CREATE INDEX IF NOT EXISTS edges_type ON edges(type);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

DEFAULT_K = int(os.environ.get("ANTITOKEN_K_ANON", "3"))
SUMMED_METRICS = [
    "visible_tokens", "billed_input_tokens", "billed_output_tokens",
    "compute_units", "optimized_compute_units", "one_shot_compute_units",
]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class GraphStore:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL" if path != ":memory:" else "PRAGMA journal_mode=MEMORY")
        self.db.executescript(SCHEMA)
        self.lock = threading.RLock()
        self.salt = self._salt()

    # --- infra -----------------------------------------------------------------

    def _salt(self) -> bytes:
        env = os.environ.get("ANTITOKEN_SECRET")
        if env:
            return env.encode()
        row = self.db.execute("SELECT value FROM meta WHERE key='salt'").fetchone()
        if row:
            return bytes.fromhex(row[0])
        salt = secrets.token_bytes(32)
        with self.db:
            self.db.execute("INSERT INTO meta(key, value) VALUES ('salt', ?)", (salt.hex(),))
        return salt

    def close(self) -> None:
        self.db.close()

    def _node(self, id_: str) -> dict | None:
        row = self.db.execute("SELECT props FROM nodes WHERE id=?", (id_,)).fetchone()
        return json.loads(row[0]) if row else None

    def _put_node(self, id_: str, label: str, props: dict) -> None:
        self.db.execute(
            "INSERT INTO nodes(id, label, props) VALUES (?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET props=excluded.props",
            (id_, label, json.dumps(props, ensure_ascii=False)),
        )

    def _put_edge(self, src: str, dst: str, type_: str, props: dict | None = None) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO edges(src, dst, type, props) VALUES (?,?,?,?)",
            (src, dst, type_, json.dumps(props or {}, ensure_ascii=False)),
        )

    def _bump_topic(self, label: str, conv_delta: int, tokens: int) -> None:
        tid = f"topic:{label}"
        p = self._node(tid) or {"label": label, "conversations": 0, "tokens": 0}
        p["conversations"] += conv_delta
        p["tokens"] = max(0, p["tokens"] + tokens)
        if p["conversations"] <= 0:
            self.db.execute("DELETE FROM nodes WHERE id=?", (tid,))
            self.db.execute("DELETE FROM edges WHERE src=? OR dst=?", (tid, tid))
        else:
            self._put_node(tid, "Topic", p)

    def _bump_cooccur(self, a: str, b: str, delta: int) -> None:
        a, b = sorted((a, b))
        src, dst = f"topic:{a}", f"topic:{b}"
        row = self.db.execute(
            "SELECT props FROM edges WHERE src=? AND dst=? AND type='CO_OCCURS'", (src, dst)
        ).fetchone()
        count = (json.loads(row[0])["count"] if row else 0) + delta
        if count <= 0:
            self.db.execute("DELETE FROM edges WHERE src=? AND dst=? AND type='CO_OCCURS'", (src, dst))
        else:
            self._put_edge(src, dst, "CO_OCCURS", {"count": count})

    # --- writes ------------------------------------------------------------------

    def save(self, sk: Skeleton, delete_token: str | None = None) -> bool:
        """Persist (= contribute) a skeleton. Returns False if already stored.

        Users who opt out are simply never saved; there is no private tier.
        """
        cid = f"conv:{sk.id}"
        with self.lock, self.db:
            if self._node(cid) is not None:
                return False
            self._put_node(cid, "Conversation", {
                "id": sk.id,
                "source": sk.source,
                "language": sk.language,
                "created_at": sk.created_at,
                "agenda": sk.agenda,
                "metrics": sk.metrics,
                "suggestion": sk.suggestion,
                "delete_token_hash": _hash_token(delete_token) if delete_token else None,
            })
            topic_tokens: dict[str, int] = {}
            for t in sk.turns:
                tid = f"turn:{sk.id}:{t.index}"
                props = {k: v for k, v in t.__dict__.items() if k != "topics"}
                self._put_node(tid, "Turn", props)
                self._put_edge(cid, tid, "HAS_TURN")
                for rank, label in enumerate(t.topics):
                    self._put_edge(tid, f"topic:{label}", "ABOUT", {"rank": rank})
                    topic_tokens[label] = topic_tokens.get(label, 0) + t.tokens
            for e in sk.edges:
                self._put_edge(f"turn:{sk.id}:{e.src}", f"turn:{sk.id}:{e.dst}", e.type)
            for label in topic_tokens:
                self._bump_topic(label, 1, topic_tokens[label])
            for rank, label in enumerate(sk.agenda):
                if label not in topic_tokens:
                    self._bump_topic(label, 1, 0)
                    topic_tokens[label] = 0
                self._put_edge(cid, f"topic:{label}", "COVERS", {"rank": rank})
            for a, b in combinations(sk.agenda, 2):
                self._bump_cooccur(a, b, 1)
            # the topic nodes hold their own conversation count; remember which
            # labels this conversation added so deletion can undo it exactly
            self._put_node(f"conv-topics:{sk.id}", "Bookkeeping", {"labels": sorted(topic_tokens), "tokens": topic_tokens})
        return True

    def delete(self, skeleton_id: str, token: str) -> bool:
        cid = f"conv:{skeleton_id}"
        with self.lock, self.db:
            conv = self._node(cid)
            if conv is None or not conv.get("delete_token_hash"):
                return False
            if not hmac.compare_digest(conv["delete_token_hash"], _hash_token(token)):
                return False
            book = self._node(f"conv-topics:{skeleton_id}") or {"labels": [], "tokens": {}}
            for a, b in combinations(conv["agenda"], 2):
                self._bump_cooccur(a, b, -1)
            for label in book["labels"]:
                self._bump_topic(label, -1, -book["tokens"].get(label, 0))
            turn_ids = [r[0] for r in self.db.execute("SELECT dst FROM edges WHERE src=? AND type='HAS_TURN'", (cid,))]
            for tid in turn_ids:
                self.db.execute("DELETE FROM edges WHERE src=? OR dst=?", (tid, tid))
                self.db.execute("DELETE FROM nodes WHERE id=?", (tid,))
            self.db.execute("DELETE FROM edges WHERE src=?", (cid,))
            self.db.execute("DELETE FROM nodes WHERE id IN (?, ?)", (cid, f"conv-topics:{skeleton_id}"))
        return True

    # --- reads -------------------------------------------------------------------

    def get(self, skeleton_id: str) -> Skeleton | None:
        cid = f"conv:{skeleton_id}"
        with self.lock:
            conv = self._node(cid)
            if conv is None:
                return None
            turns = []
            for (props,) in self.db.execute(
                "SELECT n.props FROM edges e JOIN nodes n ON n.id = e.dst WHERE e.src=? AND e.type='HAS_TURN'", (cid,)
            ):
                p = json.loads(props)
                topics = [
                    r[0][len("topic:"):]
                    for r in self.db.execute(
                        "SELECT dst FROM edges WHERE src=? AND type='ABOUT' ORDER BY json_extract(props, '$.rank')",
                        (f"turn:{skeleton_id}:{p['index']}",),
                    )
                ]
                turns.append(TurnNode(topics=topics, **p))
            turns.sort(key=lambda t: t.index)
            prefix = f"turn:{skeleton_id}:"
            edges = [
                Edge(int(s[len(prefix):]), int(d[len(prefix):]), ty)
                for s, d, ty in self.db.execute(
                    "SELECT src, dst, type FROM edges WHERE src LIKE ? AND dst LIKE ? ESCAPE '\\'",
                    (prefix.replace("_", "\\_") + "%", prefix.replace("_", "\\_") + "%"),
                )
            ]
        edges.sort(key=lambda e: (e.src, e.dst, e.type))
        return Skeleton(
            id=conv["id"], source=conv["source"], language=conv["language"], agenda=conv["agenda"],
            turns=turns, edges=edges, metrics=conv["metrics"], suggestion=conv["suggestion"],
            created_at=conv["created_at"],
        )

    def _conversations(self) -> Iterable[dict]:
        for (props,) in self.db.execute("SELECT props FROM nodes WHERE label='Conversation'"):
            yield json.loads(props)

    def stats(self) -> dict[str, Any]:
        """Aggregate impact numbers across all stored conversations."""
        with self.lock:
            convs = list(self._conversations())
        totals = {k: sum(c["metrics"].get(k, 0) for c in convs) for k in SUMMED_METRICS}
        waste = {}
        intents: dict[str, int] = {}
        sources: dict[str, int] = {}
        languages: dict[str, int] = {}
        for c in convs:
            for k, v in c["metrics"]["waste"].items():
                if not k.endswith("_pct"):
                    waste[k] = waste.get(k, 0) + v
            for k, v in c["metrics"]["intent_counts"].items():
                intents[k] = intents.get(k, 0) + v
            sources[c["source"]] = sources.get(c["source"], 0) + 1
            languages[c["language"]] = languages.get(c["language"], 0) + 1
        cu = totals["compute_units"]
        return {
            "conversations": len(convs),
            **totals,
            "avoidable_units": cu - totals["optimized_compute_units"],
            "avoidable_pct": round(100 * (1 - totals["optimized_compute_units"] / cu), 1) if cu else 0.0,
            "waste": waste,
            "intent_counts": intents,
            "sources": sources,
            "languages": languages,
        }

    def topics(self, k: int = DEFAULT_K, limit: int = 100) -> dict[str, Any]:
        """k-anonymous global topic graph."""
        k = max(k, DEFAULT_K)  # callers may raise the threshold, never lower it
        with self.lock:
            nodes = [
                json.loads(p)
                for (p,) in self.db.execute(
                    "SELECT props FROM nodes WHERE label='Topic' AND json_extract(props, '$.conversations') >= ? "
                    "ORDER BY json_extract(props, '$.conversations') DESC, json_extract(props, '$.tokens') DESC LIMIT ?",
                    (k, limit),
                )
            ]
            keep = {f"topic:{n['label']}" for n in nodes}
            links = []
            for s, d, p in self.db.execute("SELECT src, dst, props FROM edges WHERE type='CO_OCCURS'"):
                c = json.loads(p)["count"]
                if s in keep and d in keep and c >= k:
                    links.append({"source": s[6:], "target": d[6:], "count": c})
        return {"k": k, "nodes": nodes, "links": links}
