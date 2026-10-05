"""Data models.

Two families live here and they must never be mixed up:

* ``Raw*`` objects hold the original conversation text. They exist only in
  memory for the duration of one analysis call and are never persisted,
  logged, or returned by the API.
* ``Skeleton`` and friends hold the derived structure (agenda, intents,
  depth, token counts, topic labels). This is the only thing that is stored.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

USER = "user"
ASSISTANT = "assistant"


@dataclass
class RawTurn:
    role: str  # USER | ASSISTANT
    text: str


@dataclass
class RawConversation:
    turns: list[RawTurn]
    source: str = "text"  # chatgpt | claude | gemini | openai-messages | text | html

    def __repr__(self) -> str:  # keep raw text out of logs and tracebacks
        return f"RawConversation(source={self.source!r}, turns={len(self.turns)})"


@dataclass
class TurnNode:
    index: int
    role: str
    tokens: int
    intent: str
    topics: list[str]
    depth: int = 0
    branch: int = 0
    redundant: bool = False
    has_code: bool = False
    fingerprint: str = ""  # 64-bit simhash, lets us detect re-asks without text


@dataclass
class Edge:
    src: int
    dst: int
    type: str


@dataclass
class Skeleton:
    id: str
    source: str
    language: str
    agenda: list[str]
    turns: list[TurnNode]
    edges: list[Edge]
    metrics: dict[str, Any] = field(default_factory=dict)
    suggestion: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Skeleton":
        return cls(
            id=d["id"],
            source=d["source"],
            language=d["language"],
            agenda=list(d["agenda"]),
            turns=[TurnNode(**t) for t in d["turns"]],
            edges=[Edge(**e) for e in d["edges"]],
            metrics=dict(d.get("metrics", {})),
            suggestion=dict(d.get("suggestion", {})),
            created_at=d.get("created_at", ""),
        )
