"""The pre-registered protocol and the code must say the same thing."""

import re
from pathlib import Path

from pickaxetax import backtest as b
from pickaxetax.agent import bound

DOC = (Path(__file__).resolve().parent.parent / "research/protocol/backtest-v1.md").read_text()


def test_constants_match_protocol():
    assert b.PROTOCOL == "backtest-v1" and bound.METHOD == "lexical-v1" and "`lexical-v1`" in DOC
    assert f"fewer than **{b.MIN_CALLS}** assistant replies" in DOC
    assert f"**P = {b.PRIMARY_PENALTY:,}** tokens" in DOC
    assert f"leaves a **{b.STUB_TOKENS}**-token pointer" in DOC
    assert "N ∈ {" + ", ".join(map(str, b.GRID)) + "}" in DOC
    assert f"below {b.DEV_SHARE} (≈20%)" in DOC
    assert f"at most **{b.MAX_MISS_RATE:g}%**" in DOC
    assert f"fewer than **{b.MIN_DEV}** sessions, N = **{b.DEFAULT_N}**" in DOC
    assert f"fewer than **{b.MIN_CELL}** sessions" in DOC
    assert f"**{b.BOOTSTRAP:,}** resamples" in DOC and f"seed **{b.SEED}**" in DOC
    buckets = ", ".join(f"{lo}–{hi}" if hi else f"{lo}+" for lo, hi in b.LENGTH_BUCKETS)
    assert f"({buckets} calls)" in DOC


def test_detection_constants_match():
    import inspect

    src = inspect.getsource(bound.link)
    assert "min_shared: int = 1" in src and "common_frac: float = 0.02" in src and "max(3," in src
    assert re.search(r"at least \*\*1\*\* of its distinctive tokens", DOC) and "more than **2%** of outputs" in DOC
