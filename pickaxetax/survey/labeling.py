"""Blind human labeling under the waste codebook (research/protocol/waste-codebook-v1.md, §5).

    packet = build_packet(sessions, n=200, calibration=20, seed=...)   # the data owner, locally
    -> labelers open site/label.html, load the packet, export a labels file
    agreement(labels_a, labels_b)                                       # anyone, from the two labels files

The packet holds excerpts of the owner's own conversations. It is handed to labelers
directly and never committed or uploaded. A labels file holds item ids and choices only
(plus optional notes), so it can be published.
"""

from __future__ import annotations

import hashlib
import json
import random
import re

from .events import lines_from

PACKET_SCHEMA = "pickaxetax.labelpacket.v1"
LABELS_SCHEMA = "pickaxetax.labels.v1"
CODEBOOK = "v1"
CATEGORIES = ("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8")
CHOICES = ("yes", "no", "unsure")
OUTCOMES = ("met", "partial", "not_met", "unsure")
KAPPA_MIN = 0.70

MAX_INSTRUCTION = 2000
MAX_FINAL = 1500
MAX_STEPS = 60
REDACTED = "[가림]"


def _short(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _target(name, inp):
    """What a tool call acted on, in one short line."""
    if not isinstance(inp, dict):
        return ""
    for k in ("file_path", "path", "notebook_path", "command", "pattern", "url", "query", "description", "prompt", "skill"):
        if inp.get(k):
            return _short(inp[k], 120)
    for v in inp.values():
        if isinstance(v, str) and v.strip():
            return _short(v, 120)
    return ""


def _text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(str(b.get("text", "")) for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def _jsonl(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                yield d


def instructions(lines) -> list[dict]:
    """Split a session into instructions: one per real user message (the same rule as
    `measure`), each with what the agent did until the next one."""
    out, cur, seen, results = [], None, set(), {}
    for d in lines:
        m = d.get("message")
        if not isinstance(m, dict) or d.get("isSidechain"):
            continue
        content = m.get("content")
        if d.get("type") == "user":
            if d.get("isCompactSummary") or d.get("isMeta"):
                continue
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
            if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in results:
                        step = results[b["tool_use_id"]]
                        c = b.get("content")
                        size = len(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
                        step["result_chars"] = size
                        step["error"] = bool(b.get("is_error"))
                continue
            text = _text_of(blocks)
            if not text.strip() or "<system-reminder>" in text[:200] or text.lstrip().startswith("<"):
                continue
            cur = {"instruction": _short_keep_lines(text, MAX_INSTRUCTION), "steps": [], "final": "",
                   "stats": {"calls": 0, "input": 0, "output": 0, "errors": 0, "subagents": 0}}
            out.append(cur)
        elif d.get("type") == "assistant" and cur is not None:
            mid = str(m.get("id") or d.get("requestId") or d.get("uuid"))
            u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
            if mid not in seen and u:
                seen.add(mid)
                ctx = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                if ctx:
                    cur["stats"]["calls"] += 1
                    cur["stats"]["input"] += ctx
                    cur["stats"]["output"] += int(u.get("output_tokens") or 0)
            for b in content if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    name = str(b.get("name") or "?")
                    step = {"tool": "mcp" if name.startswith("mcp__") else name, "target": _target(name, b.get("input"))}
                    cur["steps"].append(step)
                    if b.get("id"):
                        results[b["id"]] = step
                    if name in ("Task", "Agent"):
                        cur["stats"]["subagents"] += 1
                elif b.get("type") == "text" and str(b.get("text", "")).strip():
                    cur["final"] = _short_keep_lines(b["text"], MAX_FINAL)
    for it in out:
        it["stats"]["errors"] = sum(1 for s in it["steps"] if s.get("error"))
        if len(it["steps"]) > MAX_STEPS:
            extra = len(it["steps"]) - MAX_STEPS
            it["steps"] = it["steps"][:MAX_STEPS] + [{"tool": "…", "target": f"그 외 {extra}개 / {extra} more"}]
    return out


def _short_keep_lines(s, n):
    s = str(s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def session_instructions(path_or_pages) -> list[dict]:
    """A transcript file (.jsonl), or a list of saved event-API pages for one session."""
    if isinstance(path_or_pages, (list, tuple)):
        return instructions(lines_from(list(path_or_pages)))
    return instructions(_jsonl(path_or_pages))


def _alloc(sizes: dict, n: int) -> dict:
    """Proportional allocation with largest remainders; never more than a stratum holds."""
    total = sum(sizes.values())
    if total <= n:
        return dict(sizes)
    raw = {k: n * v / total for k, v in sizes.items()}
    got = {k: min(sizes[k], int(r)) for k, r in raw.items()}
    for k in sorted(raw, key=lambda k: (raw[k] - int(raw[k]), k), reverse=True):
        if sum(got.values()) >= n:
            break
        if got[k] < sizes[k]:
            got[k] += 1
    return got


def build_packet(sessions: dict, n: int = 200, calibration: int = 20, seed: int = 20261006,
                 redact: list[str] | None = None, exclude: set | None = None) -> dict:
    """sessions: {label: [instruction, ...]}. Stratified by session and by instruction size
    (tertiles of input within the session); calibration items are drawn first and never
    reused in the main sample."""
    pool = []
    for label in sorted(sessions):
        items = [it for it in sessions[label] if it["stats"]["calls"]]
        if not items:
            continue
        cuts = sorted(it["stats"]["input"] for it in items)
        t1, t2 = cuts[len(cuts) // 3], cuts[(2 * len(cuts)) // 3]
        for idx, it in enumerate(items):
            if exclude and (label, idx) in exclude:
                continue  # already shown to labelers in an earlier packet (e.g. a pilot)
            size = "s" if it["stats"]["input"] < t1 else "m" if it["stats"]["input"] < t2 else "l"
            pool.append((f"{label}|{size}", label, idx, it))
    rng = random.Random(seed)
    strata = {}
    for row in pool:
        strata.setdefault(row[0], []).append(row)
    for k in strata:
        rng.shuffle(strata[k])

    def draw(k_total):
        got = _alloc({k: len(v) for k, v in strata.items()}, k_total)
        picked = []
        for k, m in got.items():
            picked += strata[k][:m]
            strata[k] = strata[k][m:]
        return picked

    cal, main = draw(calibration), None
    main = draw(n)

    def item(row):
        _, label, idx, it = row
        iid = "i" + hashlib.sha256(f"{seed}|{label}|{idx}".encode()).hexdigest()[:10]
        return {"id": iid, "session": label, "index": idx, **it}

    packet = {"schema": PACKET_SCHEMA, "codebook": CODEBOOK, "seed": seed,
              "population": {"sessions": len(sessions), "instructions": len(pool), "excluded": len(exclude or ())},
              "calibration": [item(r) for r in cal], "items": [item(r) for r in main]}
    if redact:
        packet = apply_redaction(packet, redact)
    packet["sha256"] = packet_digest(packet)
    return packet


def shown_items(packet: dict) -> set:
    """(session, index) of every item a packet showed to labelers, to exclude them later."""
    return {(x["session"], x["index"]) for x in packet.get("calibration", []) + packet.get("items", [])}


def apply_redaction(packet: dict, patterns: list[str]) -> dict:
    rx = [re.compile(p) for p in patterns if p.strip()]

    def fix(v):
        if isinstance(v, str):
            for r in rx:
                v = r.sub(REDACTED, v)
            return v
        if isinstance(v, list):
            return [fix(x) for x in v]
        if isinstance(v, dict):
            return {k: fix(x) for k, x in v.items()}
        return v

    out = fix(packet)
    out["redacted_patterns"] = len(rx)
    return out


def packet_digest(packet: dict) -> str:
    body = {k: v for k, v in packet.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_labels(lab: dict) -> list[str]:
    errs = []
    if lab.get("schema") != LABELS_SCHEMA:
        errs.append("schema")
    if not isinstance(lab.get("labels"), dict):
        return errs + ["labels"]
    for iid, v in lab["labels"].items():
        for c in CATEGORIES:
            if v.get(c) not in CHOICES + (None,):
                errs.append(f"{iid}.{c}")
        if v.get("outcome") not in OUTCOMES + (None,):
            errs.append(f"{iid}.outcome")
    return errs


MACHINE_CATEGORIES = ("W1", "W2", "W6")  # the mechanical tier (T1) of codebook v1


def machine_labels(packet: dict, lines_by_session: dict, phase: str = "main", coder: str = "machine-t1") -> dict:
    """The T1 judge's decisions on a packet's items, as a labels file.

    For the mechanical categories only (W1, W2, W6): "yes" when the judge counted that category
    while the instruction was current, else "no"; the others are left unanswered. Compare it
    with the consensus labels (`agreement`) only after the human labeling is closed, so no
    labeler ever sees it. lines_by_session: {label: transcript lines cut at the same snapshot
    as the packet}."""
    from .judge import judge_lines

    maps = {}
    for label, lines in lines_by_session.items():
        lines = list(lines)
        instr = instructions(lines)
        flags = judge_lines(lines, per_instruction=True)["per_instruction"]
        if len(flags) != len(instr):
            raise ValueError(f"{label}: {len(instr)} instructions but the judge saw {len(flags)}")
        with_calls = [i for i, it in enumerate(instr) if it["stats"]["calls"]]  # packet indexes count these only
        maps[label] = [set(flags[i]) for i in with_calls]
    labels = {}
    for item in packet["items" if phase == "main" else "calibration"]:
        cats = maps.get(item["session"])
        if cats is None or item["index"] >= len(cats):
            raise ValueError(f"no transcript for item {item['id']} ({item['session']} #{item['index']})")
        labels[item["id"]] = {c: ("yes" if c in cats[item["index"]] else "no") for c in MACHINE_CATEGORIES}
    return {"schema": LABELS_SCHEMA, "codebook": packet.get("codebook"), "packet": packet["sha256"], "phase": phase,
            "coder": coder, "machine": {"tier": "T1", "categories": list(MACHINE_CATEGORIES)}, "labels": labels}


def cohen_kappa(a: list, b: list) -> float | None:
    """Nominal Cohen's kappa. None when undefined (both coders used one same value only)."""
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe >= 1:
        return None
    return (po - pe) / (1 - pe)


def agreement(a: dict, b: dict) -> dict:
    """Per category: items both coders answered, raw agreement, kappa over yes/no/unsure,
    whether it clears the codebook's bar, and the ids they disagree on."""
    if a.get("packet") != b.get("packet"):
        raise ValueError("the two labels files are for different packets")
    if a.get("phase") != b.get("phase"):
        raise ValueError("the two labels files are for different phases")
    la, lb = a["labels"], b["labels"]
    common = sorted(set(la) & set(lb))
    rows = {}
    for c in CATEGORIES + ("outcome",):
        pairs = [(i, la[i].get(c), lb[i].get(c)) for i in common if la[i].get(c) and lb[i].get(c)]
        xa, xb = [p[1] for p in pairs], [p[2] for p in pairs]
        k = cohen_kappa(xa, xb)
        rows[c] = {"n": len(pairs), "agree_pct": round(100 * sum(x == y for x, y in zip(xa, xb)) / len(pairs), 1) if pairs else None,
                   "kappa": None if k is None else round(k, 3),
                   "passes": None if c == "outcome" else (k is not None and k >= KAPPA_MIN),
                   "disagree": [p[0] for p in pairs if p[1] != p[2]]}
    return {"schema": "pickaxetax.agreement.v1", "codebook": a.get("codebook"), "packet": a.get("packet"),
            "phase": a.get("phase"), "coders": [a.get("coder"), b.get("coder")], "items_both": len(common),
            "kappa_min": KAPPA_MIN, "categories": rows}


def render_agreement(r: dict) -> str:
    lines = [f"agreement · codebook {r['codebook']} · phase {r['phase']} · coders {r['coders'][0]} vs {r['coders'][1]} · items {r['items_both']}",
             f"{'category':9} {'n':>4} {'agree%':>7} {'kappa':>7}  result"]
    for c, v in r["categories"].items():
        k = "—" if v["kappa"] is None else f"{v['kappa']:.3f}"
        res = "" if v["passes"] is None else ("pass" if v["passes"] else f"below {r['kappa_min']:.2f}")
        a = "—" if v["agree_pct"] is None else f"{v['agree_pct']:.1f}"
        lines.append(f"{c:9} {v['n']:>4} {a:>7} {k:>7}  {res}  {len(v['disagree'])} disagreements")
    return "\n".join(lines)
