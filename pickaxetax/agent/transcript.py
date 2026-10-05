"""Read Claude Code session transcripts (~/.claude/projects/<project>/<session>.jsonl).

The JSONL schema is internal to Claude Code and may change, so parsing is
defensive: unknown lines are skipped. Facts verified on real transcripts:

* one API response is written as several ``assistant`` lines (one per content
  block) that share ``message.id`` and repeat the same ``usage`` -- usage must
  be counted once per message id, or totals come out ~3x too high;
* tool results arrive in ``user`` lines as ``tool_result`` blocks whose
  ``content`` is a string or a list of text/image/reference blocks.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from ..tokens import estimate_tokens

DEFAULT_GLOB = str(Path.home() / ".claude" / "projects" / "*" / "*.jsonl")


@dataclass
class Call:
    """One API request/response."""
    input: int
    cache_read: int
    cache_write: int
    output: int

    @property
    def context(self) -> int:
        return self.input + self.cache_read + self.cache_write


@dataclass
class ToolUse:
    id: str
    name: str
    input: dict
    call_index: int  # index of the API call that requested it
    result_tokens: int = 0
    images: int = 0
    is_error: bool = False
    has_result: bool = False


@dataclass
class Session:
    path: str
    session_id: str = ""
    calls: list[Call] = field(default_factory=list)
    tools: list[ToolUse] = field(default_factory=list)
    compactions: list[int] = field(default_factory=list)  # call index at which history was compacted
    sidechain_calls: int = 0


def _result_size(content) -> tuple[int, int]:
    """(estimated text tokens, image count) of a tool_result content."""
    if isinstance(content, str):
        return estimate_tokens(content), 0
    tokens = images = 0
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                tokens += estimate_tokens(str(b.get("text", "")))
            elif b.get("type") == "image":
                images += 1
    return tokens, images


def parse(path: str) -> Session:
    s = Session(path=path)
    seen_msgs: set[str] = set()
    by_id: dict[str, ToolUse] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            s.session_id = s.session_id or str(d.get("sessionId") or "")
            if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                s.compactions.append(len(s.calls))
                continue
            if d.get("isCompactSummary"):
                if not s.compactions or s.compactions[-1] != len(s.calls):
                    s.compactions.append(len(s.calls))
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if d.get("type") == "assistant":
                mid = msg.get("id") or d.get("requestId") or d.get("uuid")
                if d.get("isSidechain"):
                    # subagent traffic has its own context; counted, not mixed into the main thread
                    if mid not in seen_msgs and isinstance(msg.get("usage"), dict):
                        s.sidechain_calls += 1
                    seen_msgs.add(mid)
                    continue
                if mid not in seen_msgs and isinstance(msg.get("usage"), dict):
                    u = msg["usage"]
                    s.calls.append(Call(int(u.get("input_tokens") or 0), int(u.get("cache_read_input_tokens") or 0),
                                        int(u.get("cache_creation_input_tokens") or 0), int(u.get("output_tokens") or 0)))
                    seen_msgs.add(mid)
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in by_id:
                            t = ToolUse(str(b.get("id")), str(b.get("name") or "?"),
                                        b.get("input") if isinstance(b.get("input"), dict) else {},
                                        max(0, len(s.calls) - 1))
                            by_id[t.id] = t
                            s.tools.append(t)
            elif d.get("type") == "user" and isinstance(content, list) and not d.get("isSidechain"):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        t = by_id.get(str(b.get("tool_use_id")))
                        if t is None or t.has_result:
                            continue
                        t.result_tokens, t.images = _result_size(b.get("content"))
                        t.is_error = bool(b.get("is_error"))
                        t.has_result = True
    return s


def find_transcripts(paths: list[str] | None = None, since_days: float | None = None) -> list[str]:
    import time

    patterns = paths or [DEFAULT_GLOB]
    files: set[str] = set()
    for p in patterns:
        if os.path.isdir(p):
            files.update(glob.glob(os.path.join(p, "**", "*.jsonl"), recursive=True))
        else:
            files.update(glob.glob(os.path.expanduser(p)) or ([p] if os.path.isfile(p) else []))
    if since_days is not None:
        cutoff = time.time() - since_days * 86400
        files = {f for f in files if os.path.getmtime(f) >= cutoff}
    return sorted(files)
