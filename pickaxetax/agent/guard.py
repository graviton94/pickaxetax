"""Claude Code hook: stop re-reads of files that have not changed.

Wired as a PreToolUse hook on ``Read`` and a PreCompact hook. Rules, in order:

1. The file (same path + offset/limit) was read before in this session, its
   size and mtime are unchanged, and no compaction happened since  -> deny
   once, telling the model the content is already in its context.
2. The model asks for the same read again right after a denial -> allow
   (it may genuinely need it, e.g. inside a subagent with its own context).
3. Anything unexpected (missing file, bad input, I/O error) -> allow.

The hook must never break the agent: every failure path exits 0 silently.
Per-session state lives in ~/.pickaxetax/agent/<session>.json and holds only
paths, sizes and mtimes -- never file contents.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from ..tokens import estimate_tokens

STATE_DIR = Path(os.environ.get("PICKAXETAX_HOME", str(Path.home() / ".pickaxetax"))) / "agent"
MAX_ESTIMATE_BYTES = 2_000_000


def _state_path(session_id: str) -> Path:
    safe = hashlib.sha256(session_id.encode()).hexdigest()[:24]
    return STATE_DIR / f"{safe}.json"


def _load(session_id: str) -> dict:
    try:
        return json.loads(_state_path(session_id).read_text())
    except (OSError, ValueError):
        return {"reads": {}, "denied": {}}


def _save(session_id: str, state: dict) -> None:
    p = _state_path(session_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    os.replace(tmp, p)


def _estimate_read_tokens(path: str, offset, limit) -> int:
    try:
        if os.path.getsize(path) > MAX_ESTIMATE_BYTES:
            return int(os.path.getsize(path) / 4)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        start = max(0, int(offset or 1) - 1)
        end = start + int(limit) if limit else min(len(lines), start + 2000)  # Read's default window
        return estimate_tokens("".join(lines[start:end]))
    except (OSError, ValueError, TypeError):
        return 0


def pre_tool_use(event: dict) -> dict | None:
    """Return the hook output to print, or None to allow silently."""
    if event.get("tool_name") != "Read":
        return None
    ti = event.get("tool_input") or {}
    path = ti.get("file_path")
    session = str(event.get("session_id") or "")
    if not path or not session or not os.path.isfile(path):
        return None
    st = os.stat(path)
    sig = [st.st_size, st.st_mtime_ns]
    key = json.dumps([event.get("agent_id") or "", os.path.abspath(path), ti.get("offset"), ti.get("limit"), ti.get("pages")])
    state = _load(session)
    prev = state["reads"].get(key)
    if prev == sig and not state["denied"].get(key):
        state["denied"][key] = True
        _save(session, state)
        tokens = _estimate_read_tokens(path, ti.get("offset"), ti.get("limit"))
        _record_avoided(tokens)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"pickaxetax: {os.path.basename(path)} is unchanged since you last read it in this session "
                    f"(~{tokens:,} tokens). Use the content already in your context. "
                    "If you truly need it again (e.g. it was compacted away), request the same Read once more and it will be allowed."
                ),
            }
        }
    state["reads"][key] = sig
    state["denied"].pop(key, None)
    _save(session, state)
    return None


def pre_compact(event: dict) -> None:
    """History is about to be summarized: earlier reads leave the context."""
    session = str(event.get("session_id") or "")
    if session:
        _save(session, {"reads": {}, "denied": {}})


def _record_avoided(tokens: int) -> None:
    try:
        from ..proxy.ledger import Ledger, DEFAULT_PATH

        led = Ledger(os.environ.get("PICKAXETAX_LEDGER", DEFAULT_PATH))
        led.record(provider="claude-code", model="", action="agent_dup_read_blocked", streamed=False,
                   measured=False, avoided_input=tokens)
        led.close()
    except Exception:  # the ledger is best effort; never break the agent
        pass


def run_hook(kind: str, stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    try:
        event = json.load(stdin)
        if not isinstance(event, dict):
            return 0
        if kind == "pre-tool-use":
            out = pre_tool_use(event)
            if out:
                stdout.write(json.dumps(out))
        elif kind == "pre-compact":
            pre_compact(event)
    except Exception:  # fail open
        return 0
    return 0
