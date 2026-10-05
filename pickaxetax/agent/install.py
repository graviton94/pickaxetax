"""Install / uninstall the guard hook into Claude Code settings.

Merges into existing settings without touching anything else, keeps a backup,
and identifies its own entries by the ``pickaxetax`` marker in the command.
"""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path

MARKER = "pickaxetax.cli agent hook"


def settings_path(scope: str, cwd: str | None = None) -> Path:
    if scope == "project":
        return Path(cwd or ".") / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def _command(kind: str) -> str:
    # absolute interpreter path: works even when pxt is not on the agent's PATH
    return f"{shlex.quote(sys.executable)} -m {MARKER} {kind}"


def _ours(entry: dict) -> bool:
    return any(MARKER in str(h.get("command", "")) for h in entry.get("hooks", []) if isinstance(h, dict))


def install(path: Path) -> str:
    data = {}
    if path.exists():
        data = json.loads(path.read_text() or "{}")
        shutil.copy2(path, path.with_suffix(".json.bak-pickaxetax"))
    hooks = data.setdefault("hooks", {})
    for event, matcher, kind in (("PreToolUse", "Read", "pre-tool-use"), ("PreCompact", "", "pre-compact")):
        entries = [e for e in hooks.get(event, []) if not _ours(e)]
        entries.append({"matcher": matcher, "hooks": [{"type": "command", "command": _command(kind), "timeout": 10}]})
        hooks[event] = entries
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return str(path)


def uninstall(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text() or "{}")
    hooks = data.get("hooks", {})
    changed = False
    for event in list(hooks):
        kept = [e for e in hooks[event] if not _ours(e)]
        if len(kept) != len(hooks[event]):
            changed = True
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not hooks:
        data.pop("hooks", None)
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n")
    return changed
