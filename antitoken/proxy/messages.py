"""Provider-neutral views of chat requests, and the safe rewrites we apply.

Rewrites are deliberately conservative: we only touch exchanges that carry
no information (pure gratitude), never tool calls, never multimodal parts.
"ok" / "yes" / "네" are *not* gratitude -- in agent workflows they usually
mean "go ahead", and short-circuiting them would break the task.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..tokens import estimate_tokens

OPENAI = "openai"
ANTHROPIC = "anthropic"

_GRATITUDE = re.compile(
    r"^\W*(thanks?( a lot| so much| you( so much| very much)?)?|thx|ty|many thanks|cheers|much appreciated|"
    r"감사(합니다|해요|드립니다)?|고마워(요)?|고맙습니다|ㄳ|ㄱㅅ|"
    r"ありがとう(ございます)?|谢谢|多谢|merci( beaucoup)?|gracias|danke( schön)?|obrigad[oa])"
    r"[\s!.~♡❤️😊🙏👍]*$",
    re.I,
)
MAX_GRATITUDE_REPLY_TOKENS = 120


def text_of(content: Any) -> str | None:
    """Plain text of a message content, or None if it holds anything else
    (images, tool calls/results) -- those messages are never rewritten."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if not isinstance(p, dict) or p.get("type") not in ("text", "input_text", "output_text"):
                return None
            parts.append(str(p.get("text", "")))
        return "\n".join(parts)
    return None


def is_gratitude(text: str | None) -> bool:
    return bool(text) and estimate_tokens(text) <= 12 and bool(_GRATITUDE.match(text.strip()))


@dataclass
class View:
    provider: str
    body: dict

    @property
    def messages(self) -> list[dict]:
        return self.body.get("messages") or []

    @property
    def has_tools(self) -> bool:
        return bool(self.body.get("tools") or self.body.get("functions") or self.body.get("tool_choice"))

    @property
    def stream(self) -> bool:
        return bool(self.body.get("stream"))

    @property
    def model(self) -> str:
        return str(self.body.get("model") or "")

    def _plain(self, m: dict) -> bool:
        if self.provider == OPENAI and (m.get("tool_calls") or m.get("function_call") or m.get("role") == "tool"):
            return False
        return text_of(m.get("content")) is not None

    def input_estimate(self) -> int:
        total = 0
        system = self.body.get("system")
        if system is not None:
            total += estimate_tokens(text_of(system) or str(system))
        for m in self.messages:
            t = text_of(m.get("content"))
            total += 4 + estimate_tokens(t if t is not None else str(m.get("content")))
        return total

    def last_user_tokens(self) -> int:
        for m in reversed(self.messages):
            if m.get("role") == "user":
                t = text_of(m.get("content"))
                return estimate_tokens(t if t is not None else str(m.get("content")))
        return 0

    def gratitude_only(self) -> bool:
        """The latest turn is a bare thank-you that needs no model call."""
        msgs = self.messages
        if self.has_tools or len(msgs) < 2:
            return False
        last, prev = msgs[-1], msgs[-2]
        if last.get("role") != "user" or not self._plain(last) or not is_gratitude(text_of(last.get("content"))):
            return False
        # if the assistant just asked something, "thanks" may be an answer to it
        prev_text = text_of(prev.get("content")) if prev.get("role") == "assistant" else None
        return prev_text is not None and not prev_text.rstrip().endswith(("?", "？"))

    def compact(self) -> int:
        """Drop earlier (thank-you, short reply) exchanges from the history.

        Returns the estimated number of input tokens removed. The latest user
        message is never touched.
        """
        msgs = self.messages
        if self.has_tools or len(msgs) < 3:
            return 0
        keep: list[dict] = []
        removed = 0
        i = 0
        while i < len(msgs):
            m = msgs[i]
            nxt = msgs[i + 1] if i + 1 < len(msgs) else None
            is_last_user = i == len(msgs) - 1
            if (
                not is_last_user
                and nxt is not None
                and i + 1 < len(msgs) - 1  # the reply is not the final message either
                and m.get("role") == "user"
                and nxt.get("role") == "assistant"
                and self._plain(m) and self._plain(nxt)
                and is_gratitude(text_of(m.get("content")))
                and estimate_tokens(text_of(nxt.get("content")) or "") <= MAX_GRATITUDE_REPLY_TOKENS
            ):
                removed += 8 + estimate_tokens(text_of(m["content"])) + estimate_tokens(text_of(nxt["content"]))
                i += 2
                continue
            keep.append(m)
            i += 1
        if removed:
            self.body["messages"] = keep
        return removed
