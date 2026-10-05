"""Parse JSON exports and embedded share-page payloads.

Supported shapes:
* ChatGPT data export / share payload: ``{"mapping": {...}, "current_node": ...}``
  or ``{"linear_conversation": [...]}`` (single object or a list of them)
* Claude data export / share snapshot: ``{"chat_messages": [...]}``
* OpenAI-style message list: ``{"messages": [{"role", "content"}]}`` or a bare list
"""

from __future__ import annotations

from typing import Any

from ..models import ASSISTANT, USER, RawConversation, RawTurn

_ROLE = {
    "user": USER, "human": USER,
    "assistant": ASSISTANT, "model": ASSISTANT, "bot": ASSISTANT, "ai": ASSISTANT,
}


def _content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(filter(None, (_content_text(c) for c in content)))
    if isinstance(content, dict):
        if "parts" in content:
            return _content_text(content["parts"])
        if content.get("type") in (None, "text", "output_text", "input_text") and "text" in content:
            return _content_text(content["text"])
        if "content" in content:
            return _content_text(content["content"])
    return ""


def _finish(turns: list[RawTurn], source: str) -> RawConversation | None:
    merged: list[RawTurn] = []
    for t in turns:
        if not t.text.strip():
            continue
        if merged and merged[-1].role == t.role:
            merged[-1].text += "\n\n" + t.text
        else:
            merged.append(RawTurn(t.role, t.text))
    if not any(t.role == USER for t in merged):
        return None
    return RawConversation(turns=merged, source=source)


def _from_chatgpt_mapping(obj: dict) -> RawConversation | None:
    mapping = obj["mapping"]
    node_id = obj.get("current_node")
    if node_id not in mapping:  # pick the deepest leaf
        leaves = [k for k, v in mapping.items() if not v.get("children")]
        node_id = leaves[-1] if leaves else None
    chain = []
    seen = set()
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        chain.append(mapping[node_id])
        node_id = mapping[node_id].get("parent")
    turns = []
    for node in reversed(chain):
        msg = node.get("message") or {}
        role = _ROLE.get(((msg.get("author") or {}).get("role") or "").lower())
        if role and not (msg.get("metadata") or {}).get("is_visually_hidden_from_conversation"):
            turns.append(RawTurn(role, _content_text(msg.get("content"))))
    return _finish(turns, "chatgpt")


def _from_message_list(items: list, source: str) -> RawConversation | None:
    turns = []
    for m in items:
        if not isinstance(m, dict):
            continue
        if "message" in m and isinstance(m["message"], dict):  # linear_conversation nodes
            m = m["message"]
        role_raw = m.get("role") or m.get("sender") or (m.get("author") or {}).get("role") or ""
        role = _ROLE.get(str(role_raw).lower())
        if not role:
            continue
        text = m.get("text") if isinstance(m.get("text"), str) and m.get("text") else None
        turns.append(RawTurn(role, text or _content_text(m.get("content"))))
    return _finish(turns, source)


def parse_json(obj: Any) -> list[RawConversation]:
    """Return every conversation found in a parsed JSON document."""
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) and ("role" in x or "sender" in x) for x in obj):
            conv = _from_message_list(obj, "openai-messages")
            return [conv] if conv else []
        out: list[RawConversation] = []
        for x in obj:
            out.extend(parse_json(x))
        return out
    if not isinstance(obj, dict):
        return []
    conv = None
    if isinstance(obj.get("mapping"), dict):
        conv = _from_chatgpt_mapping(obj)
    elif isinstance(obj.get("linear_conversation"), list):
        conv = _from_message_list(obj["linear_conversation"], "chatgpt")
    elif isinstance(obj.get("chat_messages"), list):
        conv = _from_message_list(obj["chat_messages"], "claude")
    elif isinstance(obj.get("messages"), list):
        conv = _from_message_list(obj["messages"], "openai-messages")
    else:  # look one level down (e.g. Next.js page props wrappers)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                found = parse_json(v)
                if found:
                    return found
    return [conv] if conv else []
