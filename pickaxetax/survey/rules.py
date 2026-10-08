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
                     (main session, or one sub-agent run) or, for a sub-agent, of the main session
  W4 discarded output a file written whole (Write) and later written whole again before the
                     session ended: the first version's tokens, at the instruction that wrote it

`detect` above is sealed (rule-tier-v0.md): its behaviour and output never change.

Third machine tier (t3, `detect_t3`, version "rule-tier-t3-v0"). Added after human blind labeling
proved infeasible; W3 is judged mechanically, W7 and the outcome by a behavioural PROXY (what the
person did next), checked by the data owner on a 30-item sample. Instructions are counted exactly
as `detect` counts them (events._is_instruction), so the lists align with `labeling.instructions`.
Distinctive words are lexical-v1's (bound.TOKEN_RE), without the words common to the main
session's outputs (in more than max(3, 2% of its calls' outputs)), as in W8.

  W3 coordination loss, per instruction (the one that made the call), any of:
    (a) unused sub-agent result. For each Task/Agent call of the main session, its result is the
        sub-agent run's last non-empty assistant text (sidechain lines whose agentId is the call's
        id), or, when no run is linked, the call's own tool_result text. It arrives at the
        <task-notification> naming the call id, else at the run's last line, else at the
        tool_result. Unused = fewer than 2 (W8_MIN_SHARED) of its distinctive words appear in the
        main session's outputs (text and tool inputs) after the arrival, within the instruction
        current at the arrival or the next one. Not judged when the main session has no output
        after the arrival (snapshot cut). Score += the result's tokens (estimate_tokens).
    (b) failed delegation: the call's tool_result has is_error, or no tool_result ever arrives
        although a later instruction exists (abandoned). Counted, not scored in tokens.
    (c) polling with no state change: in one context (main, or one sub-agent run), >= 3
        consecutive tool calls (no other tool call between them) with the same name and input,
        read-only (Read/Grep/Glob/LS/WebFetch/WebSearch/NotebookRead/BashOutput/TaskOutput/
        ReadNotifications, or a Bash command matching READ_CMD or POLL_CMD, an optional leading
        `sleep N &&` allowed) and byte-identical results (content compared as JSON, so images
        count by their data). Score += tokens of the results after the run's first call.
    Flag "yes" when the score >= W3_MIN_TOKENS (500) or (b) occurred; else "no".

  Next instruction: the following instruction by _is_instruction, skipping interrupt markers
  ("[Request interrupted by user ...]"), which add the signal "interrupt". Its prompt (fenced code
  removed, first SIGNAL_CHARS characters) is matched, case-insensitively, against the phrase lists
  UNDO, CORRECTION, UNREQUESTED and ACCEPT below (Korean "아니" only at a word start and not as
  "아니면"; English on word boundaries). Actions: main-session Bash commands in the next
  instruction (and the skipped markers) that run `git restore` (not `--staged` alone),
  `git checkout ... -- <paths>` on a path this instruction wrote (Write, Edit, MultiEdit,
  NotebookEdit, main or sub-agent; ".", ":/" or a parent directory match all), or `git revert`
  after this instruction ran `git commit`, give "undo_files". "new_topic": the next prompt has
  >= 2 distinctive words and shares fewer than 2 (NEW_TOPIC_MAX_SHARED) with this prompt
  (words in more than max(3, 2% of the session's prompts) prompts are dropped). "last": no next.
  W7 proxy: "yes" if unrequested or undo_files; "no" if accept and none of undo, undo_files,
            unrequested; else "unsure".
  outcome proxy: "not_met" if correction, undo, undo_files or interrupt; else "met" if accept or
            new_topic; else "unknown" (also for the last instruction).
  These are proxies: they read the person's reaction, not the work. Signals are labels only.
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


def detect(lines, placebo: str | None = None) -> dict:
    """Per-instruction scores and flags. `lines`: parsed transcript lines of one session.
    `placebo`: W5's reuse links under a placebo test (`bound.link`); None is the sealed primary rule."""
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
                        explore.append((ins, k2, estimate_tokens(text), frozenset(bound.TOKEN_RE.findall(text)),
                                        len(outputs[k2]), len(outputs["main"])))
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
    def reused(key, terms, at):
        first_seen, common = later.get(key, ({}, set()))
        return sum(1 for t in terms - common if any(i >= at for i in first_seen.get(t, ()))) >= W8_MIN_SHARED

    for ins, key, tok, terms, at, main_at in explore:
        if not ins or not tok:
            continue
        # used if a later output of the same agent, or of its parent (the main session), reuses it
        used = reused(key, terms, at) or (key != "main" and reused("main", terms, main_at))
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
    bound.link(t, placebo=placebo)
    n_calls = len(t.contexts)
    diff = [0.0] * (n_calls + 1)
    starts = t.instruction_starts
    for s in t.segments:
        if s.kind == "unattributed" or s.end <= s.birth:
            continue
        i = bisect.bisect_right(starts, bound.origin(s))
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


# ---------------------------------------------------------------------------------------------
# Third machine tier (t3): W3 coordination loss, W7 unrequested work (proxy), outcome (proxy).
# See the module docstring for the rules. Nothing below is used by `detect`.

T3_VERSION = "rule-tier-t3-v0"
W3_MIN_TOKENS = 500  # unused sub-agent results + redundant polls >= 500 tokens
POLL_MIN_RUN = 3  # >= 3 identical read-only calls in a row
NEW_TOPIC_MAX_SHARED = 2  # a next prompt sharing fewer than 2 distinctive words is a new topic
SIGNAL_CHARS = 400  # reactions are read from the start of the next prompt
DELEGATE = {"Task", "Agent"}
POLL_TOOLS = EXPLORE | {"BashOutput", "TaskOutput", "ReadNotifications"}
POLL_CMD = re.compile(r"^\s*(?:gh\s+(?:run|pr|issue|workflow)\s+(?:view|list|checks|status|watch)\b|"
                      r"gh\s+api\b(?!.*(?:-X|--method)\s*(?:POST|PUT|PATCH|DELETE))|"
                      r"curl\b(?!.*(?:-X\s*(?:POST|PUT|PATCH|DELETE)|\s-d\b|\s--data))|"
                      r"kubectl\s+get\b|docker\s+ps\b|ps\b|sleep\s+\d+\s*$)")
SLEEP_PREFIX = re.compile(r"^\s*(?:sleep\s+\d+(?:\.\d+)?\s*(?:&&|;)\s*)+")
INTERRUPT = re.compile(r"^\s*\[Request interrupted by user")

# Phrase lists of the W7 / outcome proxy (matched case-insensitively on the next prompt).
# They are a proxy for the person's reaction, not a judgment of the work.
UNDO = (r"되돌려", r"되돌리", r"원래대로", r"취소해", r"\bundo\b", r"\brevert\b", r"\broll ?back\b")
CORRECTION = (r"(?<![가-힣])아니(?!면)", r"그게 ?아니라", r"틀렸", r"다시 ?해", r"잘못",
              r"\bnot what i\b", r"\bwrong\b", r"\btry again\b", r"\bstill broken\b",
              r"(?<![가-힣])안 ?돼", r"(?<![가-힣])안 ?됨", r"여전히")
UNREQUESTED = (r"하지 ?말", r"요청 ?안", r"시키지 ?않", r"왜[^.?!\n]{0,30}했",
               r"\bdid(?:n'?t| not) ask\b", r"\bdon'?t change\b", r"\bunnecessary\b")
ACCEPT = (r"좋아(?!하)", r"고마워", r"고맙", r"감사", r"완벽", r"(?<!안 )(?<!안)됐다", r"잘 ?됐",
          r"(?<![가-힣])다음(?![과의])", r"(?<![가-힣])이제 ", r"\bok(?:ay)?\b", r"\bgreat\b",
          r"\bthanks?\b", r"\bthank you\b", r"\bnext\b(?![.\-/])")
_SIG = {name: re.compile("|".join(pats), re.I) for name, pats in
        (("undo", UNDO), ("correction", CORRECTION), ("unrequested", UNREQUESTED), ("accept", ACCEPT))}
_FENCE = re.compile(r"```.*?(?:```|$)", re.S)
_GIT = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?(restore|checkout|revert|commit)\b([^;&|\n]*)")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def prompt_signals(text: str) -> set:
    """The reaction classes a prompt carries: a subset of undo, correction, unrequested, accept."""
    head = _FENCE.sub(" ", str(text or "")).strip()[:SIGNAL_CHARS]
    return {name for name, rx in _SIG.items() if rx.search(head)}


def _instr_text(d) -> str:
    c = (d.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return " ".join(str(b.get("text", "")) for b in c or [] if isinstance(b, dict) and b.get("type") == "text")


def _content_sig(content) -> str:
    return json.dumps(content, ensure_ascii=False, sort_keys=True)


def _read_only(name, inp) -> bool:
    if name in POLL_TOOLS:
        return True
    if name == "Bash":
        cmd = SLEEP_PREFIX.sub("", str(inp.get("command") or ""))
        return bool(READ_CMD.match(cmd) or POLL_CMD.match(cmd))
    return False


def _path_hit(arg: str, written: set) -> bool:
    a = arg.strip("'\"")
    if not a or a.startswith("-"):
        return False
    if a in (".", ":/", "*", "./"):
        return bool(written)
    na = a[2:] if a.startswith("./") else a
    for p in written:
        if p == a or p.endswith("/" + na) or p.startswith(a.rstrip("/") + "/") or ("/" + na.rstrip("/") + "/") in p:
            return True
    return False


def _undo_hits(commands, written: set, committed: bool) -> bool:
    """True if a command restores a path this instruction wrote, or reverts after it committed."""
    for cmd in commands:
        for verb, rest in _GIT.findall(cmd):
            args = rest.split()
            if verb == "revert":
                if committed:
                    return True
            elif verb == "restore":
                if "--staged" in args and "--worktree" not in args and "-W" not in args:
                    continue
                paths = args[args.index("--") + 1:] if "--" in args else [x for x in args if not x.startswith("-")]
                if any(_path_hit(x, written) for x in paths):
                    return True
            elif verb == "checkout" and "--" in args:
                if any(_path_hit(x, written) for x in args[args.index("--") + 1:]):
                    return True
    return False


def detect_t3(lines) -> dict:
    """Per-instruction W3 / W7-proxy / outcome-proxy decisions (rules in the module docstring).
    Returns {version, instructions, scores, flags, signals}; flags[i] = {"W3": yes|no,
    "W7": yes|no|unsure, "outcome": met|not_met|unknown}; signals[i] = sorted labels, no text."""
    lines = list(lines)
    instr, instr_pos, prompts = 0, [], []
    outputs = []  # main session outputs: (line position, instruction, distinctive-word set)
    out_of = {}  # main-session message id -> its index in outputs
    uses = {}  # tool_use_id -> (name, input, context key, instruction, position)
    seq = defaultdict(list)  # context key -> tool_use ids in order
    results = {}  # tool_use_id -> (position, is_error, content)
    side_final, side_last = {}, {}  # agentId -> (position, text) / last position
    notif = {}  # delegation id -> position of the <task-notification> naming it
    written = defaultdict(set)  # instruction -> paths written
    committed = set()  # instructions that ran git commit
    commands = defaultdict(list)  # instruction -> main-session Bash commands
    delegations = []  # tool_use ids of main-session Task/Agent calls
    for pos, d in enumerate(lines):
        m = d.get("message")
        if _is_instruction(d):
            instr += 1
            instr_pos.append(pos)
            prompts.append(_instr_text(d))
            continue
        if not isinstance(m, dict):
            continue
        side = bool(d.get("isSidechain"))
        key = ("side", str(d.get("agentId") or "")) if side else "main"
        content = m.get("content")
        if d.get("type") == "assistant":
            if side:
                txt = _text(content)
                side_last[str(d.get("agentId") or "")] = pos
                if txt.strip():
                    side_final[str(d.get("agentId") or "")] = (pos, txt)
            else:
                mid = str(m.get("id") or d.get("requestId"))
                u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
                ctx = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                if mid not in out_of and ctx:
                    out_of[mid] = len(outputs)
                    outputs.append((pos, instr, set()))
                cur = outputs[out_of[mid]][2] if mid in out_of else None
            for b in content if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                if not side and cur is not None:
                    if b.get("type") == "text":
                        cur.update(bound.TOKEN_RE.findall(str(b.get("text", ""))))
                    elif b.get("type") == "tool_use":
                        inp0 = b.get("input") if isinstance(b.get("input"), dict) else {}
                        cur.update(bound.TOKEN_RE.findall(json.dumps(inp0, ensure_ascii=False)))
                if b.get("type") != "tool_use":
                    continue
                name = str(b.get("name"))
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                tid = b.get("id")
                if tid in uses:
                    continue  # the same block logged twice
                uses[tid] = (name, inp, key, instr, pos)
                seq[key].append(tid)
                if name in WRITE_TOOLS:
                    p = inp.get("file_path") or inp.get("notebook_path")
                    if p:
                        written[instr].add(str(p))
                if name == "Bash" and not side:
                    cmd = str(inp.get("command") or "")
                    commands[instr].append(cmd)
                    if any(v == "commit" for v, _ in _GIT.findall(cmd)):
                        committed.add(instr)
                if name in DELEGATE and not side:
                    delegations.append(tid)
        elif d.get("type") == "user":
            blocks = content if isinstance(content, list) else []
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in uses \
                        and b["tool_use_id"] not in results:
                    results[b["tool_use_id"]] = (pos, bool(b.get("is_error")), b.get("content"))
            if not side and delegations:
                t = content if isinstance(content, str) else _text(content)
                if "<task-notification>" in t:
                    for tid in delegations:
                        if tid and tid not in notif and tid in t:
                            notif[tid] = pos
    n = instr
    score = [{"W3": 0, "W3_unused": 0, "W3_poll": 0, "W3_failed": 0, "W3_delegations": 0} for _ in range(n)]
    sigs = [set() for _ in range(n)]

    def instr_at(pos):
        return bisect.bisect_right(instr_pos, pos)

    # W3 (a) and (b)
    df = Counter(t for _, _, o in outputs for t in o)
    active = sum(1 for _, _, o in outputs if o) or 1
    common = {t for t, c in df.items() if c > max(3, 0.02 * active)}
    out_pos = [p for p, _, _ in outputs]
    for tid in delegations:
        name, inp, key, ins, pos = uses[tid]
        if not ins:
            continue
        score[ins - 1]["W3_delegations"] += 1
        res = results.get(tid)
        if (res and res[1]) or (res is None and n > ins):
            score[ins - 1]["W3_failed"] += 1
            sigs[ins - 1].add("w3_failed_delegation")
            continue
        if tid in side_final:
            text = side_final[tid][1]
            arrival = notif.get(tid, side_last.get(tid, side_final[tid][0]))
        elif res:
            text, arrival = _text(res[2]), res[0]
        else:
            continue
        k = bisect.bisect_right(out_pos, arrival)
        if k >= len(outputs):
            continue  # nothing of the main session after the result: not judged
        at = instr_at(arrival)
        later = set()
        for _, oi, o in outputs[k:]:
            if oi > at + 1:
                break
            later |= o
        terms = set(bound.TOKEN_RE.findall(text)) - common
        if len(terms & later) < W8_MIN_SHARED:
            tok = estimate_tokens(text)
            score[ins - 1]["W3_unused"] += tok
            score[ins - 1]["W3"] += tok
            sigs[ins - 1].add("w3_unused_result")

    # W3 (c): runs of identical read-only calls with identical results
    for key, ids in seq.items():
        run = []
        def close(run):
            if len(run) >= POLL_MIN_RUN:
                for tid in run[1:]:
                    ins = uses[tid][3]
                    if ins:
                        c = results[tid][2]
                        tok = estimate_tokens(c if isinstance(c, str) else _content_sig(c))
                        score[ins - 1]["W3_poll"] += tok
                        score[ins - 1]["W3"] += tok
                        sigs[ins - 1].add("w3_poll")
        prev = None
        for tid in ids:
            name, inp, _, _, _ = uses[tid]
            sig = None
            if tid in results and not results[tid][1] and _read_only(name, inp):
                sig = (name, _content_sig(inp), _content_sig(results[tid][2]))
            if sig is not None and sig == prev:
                run.append(tid)
            else:
                close(run)
                run = [tid] if sig is not None else []
            prev = sig
        close(run)

    # W7 / outcome proxies from the next instruction
    terms_of = [set(bound.TOKEN_RE.findall(p)) for p in prompts]
    pdf = Counter(t for s in terms_of for t in s)
    pcommon = {t for t, c in pdf.items() if c > max(3, 0.02 * (n or 1))}
    terms_of = [s - pcommon for s in terms_of]
    flags = []
    for i in range(n):
        s = sigs[i]
        j, cmds = i + 1, []
        while j < n and INTERRUPT.match(prompts[j]):
            s.add("interrupt")
            cmds += commands[j + 1]
            j += 1
        if j < n:
            s |= prompt_signals(prompts[j])
            cmds += commands[j + 1]
            if _undo_hits(cmds, written[i + 1], (i + 1) in committed):
                s.add("undo_files")
            if len(terms_of[j]) >= NEW_TOPIC_MAX_SHARED and len(terms_of[j] & terms_of[i]) < NEW_TOPIC_MAX_SHARED:
                s.add("new_topic")
        elif "interrupt" not in s:
            s.add("last")
        elif cmds and _undo_hits(cmds, written[i + 1], (i + 1) in committed):
            s.add("undo_files")
        w3 = "yes" if score[i]["W3"] >= W3_MIN_TOKENS or score[i]["W3_failed"] else "no"
        if s & {"unrequested", "undo_files"}:
            w7 = "yes"
        elif "accept" in s and not s & {"undo"}:
            w7 = "no"
        else:
            w7 = "unsure"
        if s & {"correction", "undo", "undo_files", "interrupt"}:
            outcome = "not_met"
        elif s & {"accept", "new_topic"}:
            outcome = "met"
        else:
            outcome = "unknown"
        flags.append({"W3": w3, "W7": w7, "outcome": outcome})
    return {"version": T3_VERSION, "instructions": n, "scores": [{k: round(v) for k, v in sc.items()} for sc in score],
            "flags": flags, "signals": [sorted(s) for s in sigs]}
