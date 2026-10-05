"""Parse pasted plain-text transcripts with role markers."""

from __future__ import annotations

import re

from ..models import ASSISTANT, USER, RawConversation, RawTurn

_USER_MARKERS = [
    "you said", "user", "you", "me", "human", "q", "question", "prompt",
    "나", "사용자", "질문", "유저", "저",
]
_ASSISTANT_MARKERS = [
    "chatgpt said", "claude said", "gemini said", "copilot said",
    "assistant", "chatgpt", "gpt", "claude", "gemini", "copilot", "grok", "perplexity",
    "ai", "bot", "a", "answer", "model", "답변", "답", "어시스턴트", "챗봇",
]


def _marker_regex(names: list[str]) -> str:
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    # "User:", "**User**:", "[User]:" or a markdown heading "## User" at line start
    return rf"(?:#+[ \t]*(?:{alts})[ \t]*\n|(?:\*\*|\[)?(?:{alts})(?:\*\*|\])?[ \t]*(?::|：))"


_LINE = re.compile(
    rf"^\s*(?:(?P<u>{_marker_regex(_USER_MARKERS)})|(?P<a>{_marker_regex(_ASSISTANT_MARKERS)}))",
    re.I | re.M,
)


def parse_transcript(text: str) -> RawConversation:
    text = text.replace("\r\n", "\n")
    matches = list(_LINE.finditer(text))
    if not matches:
        raise ValueError("no role markers found (expected lines like 'User:' / 'Assistant:')")
    turns: list[RawTurn] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        if not body:
            continue
        role = USER if m.group("u") else ASSISTANT
        if turns and turns[-1].role == role:
            turns[-1].text += "\n\n" + body
        else:
            turns.append(RawTurn(role, body))
    if not any(t.role == USER for t in turns):
        raise ValueError("transcript has no user turns")
    return RawConversation(turns=turns, source="text")
