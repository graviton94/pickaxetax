"""Find where a coding agent's tokens went.

Every tool result stays in the context and is re-read on each later API call
until the history is compacted. So a 5,000-token log dumped at call 10 of a
60-call session costs its 5,000 tokens once, plus ~250,000 tokens of re-reads
(mostly served from the prompt cache, which is cheaper but not free).
"""

from __future__ import annotations

from collections import Counter, defaultdict

from .transcript import Session

LARGE_RESULT_TOKENS = 2000
FILE_WRITERS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _carry(s: Session, call_index: int) -> int:
    """Number of later API calls that re-read something added after ``call_index``."""
    end = len(s.calls)
    for c in s.compactions:
        if c > call_index:
            end = c
            break
    return max(0, end - call_index - 1)


def _read_key(t) -> tuple:
    i = t.input
    return (i.get("file_path") or i.get("path") or i.get("notebook_path"), i.get("offset"), i.get("limit"), i.get("pages"))


def audit_session(s: Session) -> dict:
    calls = s.calls
    tot_in = sum(c.input for c in calls)
    tot_cr = sum(c.cache_read for c in calls)
    tot_cw = sum(c.cache_write for c in calls)
    tot_out = sum(c.output for c in calls)
    processed = tot_in + tot_cr + tot_cw

    # duplicate reads of unchanged files (no write to it, no compaction in between)
    dup = []
    last_read: dict[tuple, object] = {}
    for t in s.tools:
        if t.name in FILE_WRITERS:
            path = t.input.get("file_path") or t.input.get("notebook_path")
            for k in [k for k in last_read if k[0] == path]:
                del last_read[k]
            continue
        if t.name != "Read" or not t.has_result or t.is_error:
            continue
        key = _read_key(t)
        prev = last_read.get(key)
        if prev is not None and not any(prev.call_index < c <= t.call_index for c in s.compactions):
            dup.append(t)
        last_read[key] = t

    large = [t for t in s.tools if t.has_result and t.result_tokens >= LARGE_RESULT_TOKENS]

    # identical tool call that failed right after the same call failed
    failed_repeats = []
    prev_fail: dict[tuple, bool] = {}
    for t in s.tools:
        if not t.has_result:
            continue
        sig = (t.name, repr(sorted(t.input.items())))
        if t.is_error and prev_fail.get(sig):
            failed_repeats.append(t)
        prev_fail[sig] = t.is_error

    by_tool: dict[str, dict] = defaultdict(lambda: {"calls": 0, "result_tokens": 0, "carried_tokens": 0, "errors": 0, "images": 0})
    for t in s.tools:
        b = by_tool[t.name]
        b["calls"] += 1
        b["result_tokens"] += t.result_tokens
        b["carried_tokens"] += t.result_tokens * _carry(s, t.call_index)
        b["errors"] += int(t.is_error)
        b["images"] += t.images

    def cost(items):
        return {
            "count": len(items),
            "tokens": sum(t.result_tokens for t in items),
            "carried_tokens": sum(t.result_tokens * _carry(s, t.call_index) for t in items),
        }

    return {
        "session_id": s.session_id,
        "api_calls": len(calls),
        "subagent_calls": s.sidechain_calls,
        "compactions": len(s.compactions),
        "tokens": {"input": tot_in, "cache_read": tot_cr, "cache_write": tot_cw, "output": tot_out, "processed_input": processed},
        "cache_hit_pct": round(100 * tot_cr / processed, 1) if processed else 0.0,
        "peak_context": max((c.context for c in calls), default=0),
        "avg_context": round(processed / len(calls)) if calls else 0,
        "tool_calls": len(s.tools),
        "duplicate_reads": cost(dup),
        "large_results": cost(large),
        "failed_repeats": cost(failed_repeats),
        "by_tool": dict(sorted(by_tool.items(), key=lambda kv: -kv[1]["carried_tokens"])),
        "_detail": {  # local-only, never exported
            "duplicate_reads": Counter(str(_read_key(t)[0]) for t in dup).most_common(10),
            "large_results": sorted(((t.result_tokens, t.name, _label(t)) for t in large), reverse=True)[:10],
        },
    }


def _label(t) -> str:
    i = t.input
    if t.name == "Bash":
        return str(i.get("command", ""))[:80]
    return str(i.get("file_path") or i.get("path") or i.get("pattern") or i.get("url") or "")[:80]


def merge(reports: list[dict]) -> dict:
    out = {"sessions": len(reports), "api_calls": 0, "subagent_calls": 0, "compactions": 0, "tool_calls": 0,
           "tokens": Counter(), "duplicate_reads": Counter(), "large_results": Counter(), "failed_repeats": Counter(),
           "by_tool": defaultdict(Counter), "peak_context": 0}
    for r in reports:
        for k in ("api_calls", "subagent_calls", "compactions", "tool_calls"):
            out[k] += r[k]
        out["peak_context"] = max(out["peak_context"], r["peak_context"])
        out["tokens"].update(r["tokens"])
        for k in ("duplicate_reads", "large_results", "failed_repeats"):
            out[k].update(r[k])
        for name, b in r["by_tool"].items():
            out["by_tool"][name].update(b)
    p = out["tokens"]["processed_input"]
    out["cache_hit_pct"] = round(100 * out["tokens"]["cache_read"] / p, 1) if p else 0.0
    out["tokens"] = dict(out["tokens"])
    for k in ("duplicate_reads", "large_results", "failed_repeats"):
        out[k] = {kk: out[k].get(kk, 0) for kk in ("count", "tokens", "carried_tokens")}
    out["by_tool"] = {k: dict(v) for k, v in sorted(out["by_tool"].items(), key=lambda kv: -kv[1]["carried_tokens"])}
    out["carried_share_pct"] = round(100 * sum(b["carried_tokens"] for b in out["by_tool"].values()) / p, 1) if p else 0.0
    return out


def tips(m: dict) -> list[dict]:
    t = []
    dr, lr, fr = m["duplicate_reads"], m["large_results"], m["failed_repeats"]
    if dr["count"]:
        t.append({"code": "dup_read", "weight": dr["carried_tokens"],
                  "en": f"{dr['count']} re-read(s) of unchanged files added {dr['tokens']:,} tokens, re-read {dr['carried_tokens']:,} more times afterwards. `pxt agent hook install` blocks these automatically.",
                  "ko": f"바뀌지 않은 파일을 {dr['count']}번 다시 읽어 {dr['tokens']:,} 토큰이 추가됐고, 이후 {dr['carried_tokens']:,} 토큰만큼 재전송됐습니다. `pxt agent hook install`로 자동 차단할 수 있습니다."})
    if lr["count"]:
        t.append({"code": "large_output", "weight": lr["carried_tokens"],
                  "en": f"{lr['count']} tool result(s) over {LARGE_RESULT_TOKENS:,} tokens ({lr['tokens']:,} tokens, carried {lr['carried_tokens']:,}). Ask the agent to read files with offset/limit and to pipe long command output through tail/grep.",
                  "ko": f"{LARGE_RESULT_TOKENS:,} 토큰이 넘는 도구 결과 {lr['count']}개 ({lr['tokens']:,} 토큰, 재전송 {lr['carried_tokens']:,}). 파일은 범위를 지정해 읽고, 긴 명령 출력은 tail/grep으로 거르도록 지시하세요."})
    if fr["count"]:
        t.append({"code": "failed_repeat", "weight": fr["carried_tokens"] + fr["tokens"],
                  "en": f"{fr['count']} identical tool call(s) failed again right after failing. Tell the agent to change approach after one failure.",
                  "ko": f"같은 도구 호출이 실패 직후 똑같이 다시 실패한 경우가 {fr['count']}번 있습니다. 한 번 실패하면 방법을 바꾸라고 지시하세요."})
    if m.get("peak_context", 0) > 120_000:
        t.append({"code": "long_session", "weight": m["peak_context"],
                  "en": f"Context peaked at {m['peak_context']:,} tokens. Start a fresh session (/clear) when the task changes.",
                  "ko": f"컨텍스트가 최대 {m['peak_context']:,} 토큰까지 커졌습니다. 작업이 바뀌면 새 세션(/clear)을 여세요."})
    return sorted(t, key=lambda x: -x["weight"])


def export(m: dict) -> dict:
    """Anonymous aggregate for contribution: counts only, no paths, commands or ids."""
    keep = ("sessions", "api_calls", "subagent_calls", "compactions", "tool_calls", "tokens", "cache_hit_pct",
            "peak_context", "duplicate_reads", "large_results", "failed_repeats", "carried_share_pct")
    out = {k: m[k] for k in keep if k in m}
    by_tool: dict[str, Counter] = defaultdict(Counter)
    for name, b in m["by_tool"].items():
        by_tool["mcp" if name.startswith("mcp__") else name].update(b)  # MCP tool names can reveal private services
    out["by_tool"] = {k: dict(v) for k, v in by_tool.items()}
    out["schema"] = "pickaxetax.agent.v1"
    out["agent"] = "claude-code"
    return out
