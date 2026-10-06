"""Rule-tier candidates (T2) of the waste codebook, per instruction, fixed before the blind labels.

research/protocol/rule-tier-v0.md states the rules and thresholds. They are committed before any
consensus label exists, so the labels can measure their precision and recall honestly; until
then their outputs are not published as waste. Everything here is computed from the records:

  W5 stale context   carried over from a finished instruction and resident after its last
                     lexical reuse (pickaxetax.agent.bound, lexical-v1, default settings),
                     summed over the instruction's main-session calls
  W8 over-exploration exploration results (Read, Grep, Glob, WebFetch, WebSearch, LS, and shell
                     commands that only read: cat, grep, sed -n, git log ...) of which fewer than
                     two distinctive words reappear in any later output of the same context
                     (main session, or one sub-agent run)
  W4 discarded output a file written whole (Write) and later written whole again before the
                     session ended: the first version's tokens, at the instruction that wrote it
"""

from __future__ import annotations

import bisect
import json
import re
from collections import Counter, defaultdict

from ..agent import bound
from ..tokens import estimate_tokens

VERSION = "rule-tier-v0"
EXPLORE = {"Read", "Grep", "Glob", "WebFetch", "WebSearch", "LS", "NotebookRead"}
# shell commands that only read: the first command of the line (agents often explore with the shell)
READ_CMD = re.compile(r"^\s*(?:cd\s+\S+\s*(?:&&|;)\s*)?(?:cat|head|tail|less|sed\s+-n|grep|egrep|rg|ag|find|ls|tree|wc|jq|"
                      r"git\s+(?:log|show|diff|status|grep|ls-files|blame))\b")
W8_MIN_SHARED = 2  # a result counts as used when >= 2 of its distinctive words reappear in a later output
# yes/no thresholds, fixed before labeling (rule-tier-v0.md)
W5_MIN_SHARE = 0.10  # stale tokens >= 10% of the instruction's main-session input
W8_MIN_TOKENS = 1_000  # unreferenced exploration >= 1,000 tokens ...
W8_MIN_SHARE = 0.50  # ... and >= half of the instruction's exploration results
W4_MIN_TOKENS = 200  # a discarded whole-file version of >= 200 tokens


def _is_instruction(d) -> bool:
    from .events import _is_instruction as rule  # the rule `measure`, `judge` and `labeling` share
    return rule(d)


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def detect(lines) -> dict:
    """Per-instruction scores and flags. `lines`: parsed transcript lines of one session."""
    lines = list(lines)
    # main-session API calls in order, and the instruction each belongs to (1-based; 0 = before any)
    instr, call_instr, call_ctx, seen = 0, [], [], set()
    explore = []  # (instruction, context key, tokens, terms, arrival index in that context)
    outputs = defaultdict(list)  # context key -> list of output term sets, one per API call
    uses = {}  # tool_use_id -> (name, context key, instruction)
    writes = []  # (instruction, path, tokens) in order
    ctx_calls = defaultdict(set)
    for d in lines:
        m = d.get("message")
        if _is_instruction(d):
            instr += 1
            continue
        if not isinstance(m, dict):
            continue
        key = ("side", str(d.get("agentId") or "")) if d.get("isSidechain") else "main"
        content = m.get("content")
        if d.get("type") == "assistant":
            mid = str(m.get("id") or d.get("requestId"))
            u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
            ctx = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if mid not in ctx_calls[key]:
                if not ctx:
                    continue
                ctx_calls[key].add(mid)
                outputs[key].append(set())
                if key == "main" and mid not in seen:
                    seen.add(mid)
                    call_instr.append(instr)
                    call_ctx.append(ctx)
            out = outputs[key][-1]
            for b in content if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    out.update(bound.TOKEN_RE.findall(str(b.get("text", ""))))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    out.update(bound.TOKEN_RE.findall(json.dumps(inp, ensure_ascii=False)))
                    name = str(b.get("name"))
                    if name == "Bash" and READ_CMD.match(str(inp.get("command") or "")):
                        name = "Read"  # a read-only shell command explores like Read
                    uses[b.get("id")] = (name, key, instr)
                    if b.get("name") == "Write" and inp.get("file_path"):
                        writes.append((instr, str(inp["file_path"]), estimate_tokens(str(inp.get("content") or ""))))
        elif d.get("type") == "user":
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in uses:
                    name, k2, ins = uses[b["tool_use_id"]]
                    if name in EXPLORE and not b.get("is_error"):
                        text = _text(b.get("content"))
                        explore.append((ins, k2, estimate_tokens(text), frozenset(bound.TOKEN_RE.findall(text)), len(outputs[k2])))
    n = instr
    score = [{"W4": 0, "W5": 0, "W5_input": 0, "W8": 0, "W8_explore": 0} for _ in range(n)]

    # W8: per context, words that later outputs used (common words, as in the bound, do not count)
    later = {}
    for key, outs in outputs.items():
        df = Counter(t for o in outs for t in o)
        active = sum(1 for o in outs if o) or 1
        common = {t for t, c in df.items() if c > max(3, 0.02 * active)}
        first_seen = {}
        for i, o in enumerate(outs):
            for t in o - common:
                first_seen.setdefault(t, []).append(i)
        later[key] = (first_seen, common)
    for ins, key, tok, terms, at in explore:
        if not ins or not tok:
            continue
        first_seen, common = later.get(key, ({}, set()))
        used = sum(1 for t in terms - common if any(i >= at for i in first_seen.get(t, ()))) >= W8_MIN_SHARED
        score[ins - 1]["W8_explore"] += tok
        if not used:
            score[ins - 1]["W8"] += tok

    # W4: a whole-file write later replaced by another whole-file write of the same path
    last_write = {}
    for ins, path, tok in writes:
        prev = last_write.get(path)
        if prev and prev[0] and prev[1] >= 1:
            score[prev[0] - 1]["W4"] += prev[1]
        last_write[path] = (ins, tok)

    # W5: the bound's carried-and-dead residency, attributed to the call where it is carried
    t = bound.read_trace_lines(lines)
    bound.calibrate(t)
    bound.link(t)
    n_calls = len(t.contexts)
    diff = [0.0] * (n_calls + 1)
    starts = t.instruction_starts
    for s in t.segments:
        if s.kind == "unattributed" or s.end <= s.birth:
            continue
        i = bisect.bisect_right(starts, s.birth)
        a = max(starts[i] if i < len(starts) else s.end, s.birth)
        last = s.refs[-1] if s.refs else s.birth - 1
        lo = max(a, last + 1)
        if lo < s.end:
            diff[lo] += s.tokens
            diff[s.end] -= s.tokens
    run = 0.0
    for k in range(min(n_calls, len(call_instr))):
        run += diff[k]
        ins = call_instr[k]
        if ins:
            score[ins - 1]["W5"] += run
            score[ins - 1]["W5_input"] += call_ctx[k]

    flags = []
    for sc in score:
        f = set()
        if sc["W5_input"] and sc["W5"] >= W5_MIN_SHARE * sc["W5_input"]:
            f.add("W5")
        if sc["W8"] >= W8_MIN_TOKENS and sc["W8"] >= W8_MIN_SHARE * sc["W8_explore"]:
            f.add("W8")
        if sc["W4"] >= W4_MIN_TOKENS:
            f.add("W4")
        flags.append(sorted(f))
    return {"version": VERSION, "instructions": n, "scores": [{k: round(v) for k, v in s.items()} for s in score],
            "flags": flags,
            "totals": {k: round(sum(s[k] for s in score)) for k in ("W4", "W5", "W5_input", "W8", "W8_explore")}}
