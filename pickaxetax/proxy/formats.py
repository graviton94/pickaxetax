"""Provider wire formats: usage extraction (JSON and SSE) and locally
synthesized replies that look exactly like the real API's."""

from __future__ import annotations

import json
import time
import uuid

from ..tokens import estimate_tokens
from .messages import ANTHROPIC, OPENAI


def usage_from_json(provider: str, body: dict) -> dict | None:
    u = body.get("usage") if isinstance(body, dict) else None
    if not isinstance(u, dict):
        return None
    if provider == OPENAI:
        return {
            "input_tokens": int(u.get("prompt_tokens") or 0),
            "output_tokens": int(u.get("completion_tokens") or 0),
            "reasoning_tokens": int((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0),
            "cached_input_tokens": int((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0),
        }
    cache_read = int(u.get("cache_read_input_tokens") or 0)
    return {
        "input_tokens": int(u.get("input_tokens") or 0) + cache_read + int(u.get("cache_creation_input_tokens") or 0),
        "output_tokens": int(u.get("output_tokens") or 0),
        "reasoning_tokens": 0,
        "cached_input_tokens": cache_read,
    }


class StreamMeter:
    """Watches an SSE stream as it passes through and extracts usage, or
    falls back to estimating output from the text deltas."""

    def __init__(self, provider: str):
        self.provider = provider
        self.buf = b""
        self.usage: dict = {}
        self.text: list[str] = []

    def feed(self, chunk: bytes) -> None:
        self.buf += chunk
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            line = line.strip()
            if not line.startswith(b"data:"):
                continue
            data = line[5:].strip()
            if not data or data == b"[DONE]":
                continue
            try:
                ev = json.loads(data)
            except ValueError:
                continue
            self._event(ev)

    def _event(self, ev: dict) -> None:
        if self.provider == OPENAI:
            if ev.get("usage"):
                self.usage.update(usage_from_json(OPENAI, ev) or {})
            for ch in ev.get("choices") or []:
                d = (ch or {}).get("delta") or {}
                if isinstance(d.get("content"), str):
                    self.text.append(d["content"])
            return
        t = ev.get("type")
        if t == "message_start":
            u = usage_from_json(ANTHROPIC, ev.get("message") or {}) or {}
            self.usage["input_tokens"] = u.get("input_tokens", 0)
            self.usage["cached_input_tokens"] = u.get("cached_input_tokens", 0)
        elif t == "message_delta" and isinstance(ev.get("usage"), dict):
            self.usage["output_tokens"] = int(ev["usage"].get("output_tokens") or 0)
        elif t == "content_block_delta":
            d = ev.get("delta") or {}
            if isinstance(d.get("text"), str):
                self.text.append(d["text"])

    def result(self, input_estimate: int) -> tuple[dict, bool]:
        """(usage, measured)"""
        measured = "output_tokens" in self.usage and "input_tokens" in self.usage
        u = {"input_tokens": input_estimate, "output_tokens": estimate_tokens("".join(self.text)),
             "reasoning_tokens": 0, "cached_input_tokens": 0}
        u.update({k: v for k, v in self.usage.items() if v is not None})
        return u, measured


def local_reply(provider: str, model: str, text: str, stream: bool) -> tuple[bytes, str]:
    """(body, content_type) of a reply generated without calling any model."""
    now = int(time.time())
    if provider == OPENAI:
        rid = f"chatcmpl-pickaxetax-{uuid.uuid4().hex[:12]}"
        if not stream:
            return json.dumps({
                "id": rid, "object": "chat.completion", "created": now, "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }).encode(), "application/json"
        chunks = [
            {"id": rid, "object": "chat.completion.chunk", "created": now, "model": model,
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}]},
            {"id": rid, "object": "chat.completion.chunk", "created": now, "model": model,
             "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        ]
        out = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return out.encode(), "text/event-stream"

    mid = f"msg_pickaxetax_{uuid.uuid4().hex[:12]}"
    message = {"id": mid, "type": "message", "role": "assistant", "model": model,
               "content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
               "stop_sequence": None, "usage": {"input_tokens": 0, "output_tokens": 0}}
    if not stream:
        return json.dumps(message).encode(), "application/json"
    start = dict(message, content=[], stop_reason=None)
    events = [
        ("message_start", {"type": "message_start", "message": start}),
        ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                           "usage": {"output_tokens": 0}}),
        ("message_stop", {"type": "message_stop"}),
    ]
    out = "".join(f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events)
    return out.encode(), "text/event-stream"
