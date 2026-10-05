"""Token estimation.

Uses ``tiktoken`` (o200k_base) when installed; otherwise a dependency-free
heuristic calibrated against it: ~1 token per CJK/Hangul character and
~4 characters per token for everything else.
"""

from __future__ import annotations

import math
import re

try:  # optional, exact counts
    import tiktoken

    _ENC = tiktoken.get_encoding("o200k_base")
except Exception:  # pragma: no cover - depends on environment
    _ENC = None

_CJK = re.compile(r"[ᄀ-ᇿ぀-ヿ㄰-㆏㐀-鿿가-힯豈-﫿]")
_SPACE = re.compile(r"\s+")


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    if _ENC is not None:
        return len(_ENC.encode(text, disallowed_special=()))
    cjk = len(_CJK.findall(text))
    rest = len(_SPACE.sub(" ", _CJK.sub("", text)).strip())
    return max(1, math.ceil(cjk * 1.0 + rest / 4.0))
