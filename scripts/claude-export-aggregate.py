#!/usr/bin/env python3
"""Aggregate a claude.ai data export locally. Prints numbers and schema key names only, never content.

Usage (on your own computer, Python 3.8+, no packages needed):
    python3 claude-export-aggregate.py conversations-000.zip projects-000.zip frames-000.zip > export-aggregate.json
Then share export-aggregate.json (a few KB). Nothing else leaves your machine.

What it reports:
- schema: for each JSON file in the zips, key paths and value types (key names only; keys that do not look like
  schema names are masked as <k>);
- conversations: per-conversation turn counts and character sizes, the estimated input if every reply re-read the
  whole conversation (sum of the context before each reply), and the share of that input which belongs to earlier
  turns; idle gaps between messages;
- sizes only for everything else (project documents, memories, frames).
Characters, not tokens: the export has no token counts. Hidden system prompts, tool results and attachments that
the export omits are not counted, so input estimates are lower bounds.
"""
import io, json, re, sys, zipfile
from datetime import datetime, timezone

KEY_OK = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,40}$")
SKIP_KEYS = {"uuid", "id", "created_at", "updated_at", "sender", "role", "type", "account", "parent_message_uuid",
             "index", "start_timestamp", "stop_timestamp", "file_name", "file_type", "file_size", "model"}
TIME_KEYS = ("created_at", "updated_at", "timestamp", "create_time")


def schema(obj, path="$", out=None, depth=0):
    out = {} if out is None else out
    t = type(obj).__name__
    rec = out.setdefault(path, {})
    rec[t] = rec.get(t, 0) + 1
    if depth > 8:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            schema(v, f"{path}.{k if KEY_OK.match(str(k)) else '<k>'}", out, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:200]:
            schema(v, path + "[]", out, depth + 1)
    return out


def text_chars(obj, key=None):
    if isinstance(obj, str):
        return 0 if key in SKIP_KEYS else len(obj)
    if isinstance(obj, dict):
        return sum(text_chars(v, k) for k, v in obj.items() if k not in SKIP_KEYS)
    if isinstance(obj, list):
        return sum(text_chars(v, key) for v in obj)
    return 0


def msg_time(m):
    for k in TIME_KEYS:
        v = m.get(k)
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass
        if isinstance(v, (int, float)):
            return float(v)
    return None


def is_message(d):
    return isinstance(d, dict) and (d.get("sender") in ("human", "assistant") or d.get("role") in ("user", "assistant"))


def find_conversations(obj, found):
    """Any list whose items are mostly messages is a conversation."""
    if isinstance(obj, list):
        if obj and sum(is_message(x) for x in obj) >= max(1, len(obj) // 2):
            found.append([x for x in obj if is_message(x)])
            return
        for v in obj:
            find_conversations(v, found)
    elif isinstance(obj, dict):
        for v in obj.values():
            find_conversations(v, found)


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))]


def conv_stats(convs):
    per, gaps = [], {"lt5m": 0, "5m_1h": 0, "gt1h": 0}
    tot_input = tot_earlier = tot_chars = 0
    months = {}
    for msgs in convs:
        times = [msg_time(m) for m in msgs]
        if all(t is not None for t in times):
            order = sorted(range(len(msgs)), key=lambda i: times[i])
            msgs = [msgs[i] for i in order]
            times = [times[i] for i in order]
        # the export can carry a message's text twice (a plain `text` and a `content` block list); count it once
        sizes = [text_chars({k: v for k, v in m.items() if not (k == "text" and isinstance(m.get("content"), list))})
                 for m in msgs]
        user = [(m.get("sender") == "human" or m.get("role") == "user") for m in msgs]
        ctx = 0
        turn_start = 0
        inp = earlier = 0
        for i, (s, u) in enumerate(zip(sizes, user)):
            if u:
                turn_start = ctx
            else:
                inp += ctx
                earlier += turn_start
            ctx += s
        for a, b in zip(times, times[1:]):
            if a is not None and b is not None:
                d = b - a
                gaps["lt5m" if d < 300 else "5m_1h" if d < 3600 else "gt1h"] += 1
        if times and times[0] is not None:
            mo = datetime.fromtimestamp(times[0], tz=timezone.utc).strftime("%Y-%m")
            months[mo] = months.get(mo, 0) + 1
        per.append({"turns": sum(user), "messages": len(msgs), "chars": sum(sizes), "input_est_chars": inp})
        tot_input += inp
        tot_earlier += earlier
        tot_chars += sum(sizes)
    turns = [c["turns"] for c in per]
    inputs = [c["input_est_chars"] for c in per]
    top = sorted(inputs, reverse=True)
    return {
        "conversations": len(per),
        "messages": sum(c["messages"] for c in per),
        "user_turns": sum(turns),
        "chars_total": tot_chars,
        "input_est_chars_total": tot_input,
        "input_share_earlier_turns": round(tot_earlier / tot_input, 4) if tot_input else None,
        "input_over_chars": round(tot_input / tot_chars, 2) if tot_chars else None,
        "turns_p50_p90_max": [pct(turns, 50), pct(turns, 90), max(turns) if turns else None],
        "input_share_top10pct_convs": round(sum(top[: max(1, len(top) // 10)]) / tot_input, 4) if tot_input else None,
        "turn_buckets": {b: sum(1 for t in turns if lo <= t < hi) for b, lo, hi in
                         [("1", 1, 2), ("2-5", 2, 6), ("6-20", 6, 21), ("21-50", 21, 51), ("51+", 51, 10**9)]},
        "gaps_between_messages": gaps,
        "conversations_by_month": dict(sorted(months.items())),
    }


def main(paths):
    out = {"files": {}, "schema": {}, "conversations": None}
    convs = []
    for p in paths:
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                ext = name.rsplit(".", 1)[-1].lower() if "." in name.rsplit("/", 1)[-1] else "noext"
                label = f"{p.replace(chr(92), '/').rsplit('/', 1)[-1]}:depth{name.count('/')}.{ext}"  # names masked
                f = out["files"].setdefault(label, {"count": 0, "bytes": 0})
                f["count"] += 1
                f["bytes"] += info.file_size
                if not name.endswith((".json", ".jsonl")):
                    continue
                raw = z.read(info)
                try:
                    if name.endswith(".jsonl"):
                        data = [json.loads(l) for l in io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8") if l.strip()]
                    else:
                        data = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    f["unparsed"] = f.get("unparsed", 0) + 1
                    continue
                sch = schema(data)
                dst = out["schema"].setdefault(label, {})
                for k, v in sch.items():
                    d = dst.setdefault(k, {})
                    for t, n in v.items():
                        d[t] = d.get(t, 0) + n
                find_conversations(data, convs)
    out["conversations"] = conv_stats(convs) if convs else None
    for lab in out["schema"]:  # keep the schema readable
        out["schema"][lab] = dict(list(out["schema"][lab].items())[:300])
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
