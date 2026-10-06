"""Command line: analyze locally, serve the web app, export the graph."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .graph import GraphStore, skeleton_cypher, topics_cypher
from .models import Skeleton
from .service import process_bytes, process_text


def _summary(sk: dict) -> str:
    m = sk["metrics"]
    lines = [
        f"id            {sk['id']}  ({sk['source']}, {sk['language']})",
        f"agenda        {', '.join(sk['agenda'])}",
        f"turns         {m['user_turns']} user / {m['assistant_turns']} assistant, "
        f"{m['branches']} thread(s), max depth {m['max_depth']}",
        f"tokens        visible {m['visible_tokens']:,} | billed input {m['billed_input_tokens']:,} | output {m['billed_output_tokens']:,}",
        f"compute       {m['compute_units']:,} -> {m['optimized_compute_units']:,} units  "
        f"(avoidable {m['savings_pct']}%, one-shot {m['one_shot_savings_pct']}%)",
        "",
        sk["suggestion"]["prompt_template"],
        "",
    ]
    lang = "ko" if sk["language"] == "ko" else "en"
    lines += [f"- {tip[lang]}" for tip in sk["suggestion"]["tips"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pickaxetax", description=__doc__)
    ap.add_argument("--version", action="version", version=f"pickaxetax {__version__}")
    ap.add_argument("--db", default=os.environ.get("PICKAXETAX_DB", "data/pickaxetax.sqlite3"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="analyze a file, share URL, or '-' for stdin")
    a.add_argument("source")
    a.add_argument("--save", action="store_true", help="store the skeleton in the graph db")
    a.add_argument("--json", action="store_true", help="print skeleton JSON")
    a.add_argument("--cypher", action="store_true", help="print Cypher statements")

    s = sub.add_parser("serve", help="run the web app")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)

    e = sub.add_parser("export", help="export the k-anonymous public topic graph as Cypher")
    e.add_argument("--k", type=int, default=0)

    p = sub.add_parser("proxy", help="run the local measuring/optimizing LLM proxy")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--openai-base", default=os.environ.get("PICKAXETAX_OPENAI_BASE", "https://api.openai.com"),
                   help="upstream for /v1/chat/completions (any OpenAI-compatible server)")
    p.add_argument("--anthropic-base", default=os.environ.get("PICKAXETAX_ANTHROPIC_BASE", "https://api.anthropic.com"))
    p.add_argument("--no-compact", action="store_true", help="do not drop old thank-you exchanges")
    p.add_argument("--no-gratitude", action="store_true", help="always forward bare 'thanks' messages")
    p.add_argument("--cache", action="store_true", help="cache identical temperature-0 requests locally")
    p.add_argument("--cache-all", action="store_true", help="cache all identical requests (disables regeneration)")
    p.add_argument("--ledger", default=None, help="ledger path (default ~/.pickaxetax/ledger.sqlite3)")

    lg = sub.add_parser("ledger", help="show what the proxy measured and avoided")
    lg.add_argument("--ledger", default=None)
    lg.add_argument("--export", action="store_true", help="print an anonymous aggregate for contribution")

    b = sub.add_parser("bench", help="over-computation benchmark (crowd-run)")
    bsub = b.add_subparsers(dest="bench_cmd", required=True)
    br = bsub.add_parser("run", help="run once against an OpenAI-compatible endpoint")
    br.add_argument("--base-url", required=True, help="e.g. http://localhost:11434 (Ollama)")
    br.add_argument("--model", required=True)
    br.add_argument("--api-key-env", default=None, help="name of the env var holding the API key")
    br.add_argument("--max-tokens", type=int, default=1024)
    br.add_argument("--reasoning-effort", default=None, help="passed through if the model supports it")
    br.add_argument("--out", default="bench/results")
    br.add_argument("--force", action="store_true", help="re-run even if a result already exists")
    bv = bsub.add_parser("validate", help="validate result files (used by CI)")
    bv.add_argument("paths", nargs="+")
    bsub.add_parser("tasks", help="list the task set")

    ag = sub.add_parser("agent", help="coding agents: audit transcripts, guard hook")
    agsub = ag.add_subparsers(dest="agent_cmd", required=True)
    aa = agsub.add_parser("audit", help="where did the coding agent's tokens go? (Claude Code transcripts)")
    aa.add_argument("paths", nargs="*", help="transcript files or directories (default: ~/.claude/projects)")
    aa.add_argument("--since", type=float, default=None, help="only sessions modified in the last N days")
    aa.add_argument("--json", action="store_true", help="print the full report as JSON (local, includes paths)")
    aa.add_argument("--export", action="store_true", help="print an anonymous aggregate for contribution")
    ab = agsub.add_parser("bound", help="how far from the least context it needed was each session? (offline-optimal bound)")
    ab.add_argument("paths", nargs="*", help="transcript files or directories (default: ~/.claude/projects)")
    ab.add_argument("--since", type=float, default=None, help="only sessions modified in the last N days")
    ab.add_argument("--min-shared", type=int, default=1, help="distinctive tokens a later output must reuse to count as a use")
    ab.add_argument("--raw", action="store_true", help="skip calibration against measured context growth")
    ab.add_argument("--json", action="store_true", help="print the aggregate as JSON")
    ab.add_argument("--export", action="store_true", help="print an anonymous aggregate (audit + bound) for contribution")
    ah = agsub.add_parser("hook", help="guard hook (called by Claude Code) and its installer")
    ah.add_argument("action", choices=["pre-tool-use", "pre-compact", "install", "uninstall"])
    ah.add_argument("--scope", choices=["user", "project"], default="user")

    bt = sub.add_parser("backtest", help="pre-registered backtest and benchmark over many sessions (any provider)")
    btsub = bt.add_subparsers(dest="backtest_cmd", required=True)
    br = btsub.add_parser("run", help="measure sessions and write the report (aggregates only)")
    br.add_argument("paths", nargs="+", help="chat exports (ChatGPT, Claude, Gemini, ...), transcripts or agent logs")
    br.add_argument("--source", default=None, help="provider label for every session in these files (overrides detection)")
    br.add_argument("--contributor", default="1", help="opaque label of who supplied the files (stored as a short hash)")
    br.add_argument("--out", default="backtest-report.json", help="publishable report (no text, paths or ids)")
    br.add_argument("--manifest", default="backtest-manifest.txt", help="private list of session fingerprints (keep it)")
    bl = btsub.add_parser("label", help="validate the use detector by hand (text shown locally, only answers saved)")
    bl.add_argument("paths", nargs="+")
    bl.add_argument("--source", default=None)
    bl.add_argument("--n", type=int, default=100, help="pairs to label (half detected, half not)")
    bl.add_argument("--labels", default="backtest-labels.json")
    bl.add_argument("--sheet", default=None, help="write a sheet to answer later instead of asking in the terminal")
    bl.add_argument("--key", default="backtest-label-key.json", help="with --sheet: item numbers -> pair ids (no text)")
    ba = btsub.add_parser("answer", help="apply answers to a label sheet, e.g. '1y 2n 3s'")
    ba.add_argument("key")
    ba.add_argument("answers")
    ba.add_argument("--labels", default="backtest-labels.json")
    bv = btsub.add_parser("validation", help="summarize detector validation labels")
    bv.add_argument("labels")

    sv = sub.add_parser("survey", help="phenomenon survey of Claude Code use: measure sessions, render a report")
    svsub = sv.add_subparsers(dest="survey_cmd", required=True)
    sm = svsub.add_parser("measure", help="measure transcripts into a dataset (numbers only)")
    sm.add_argument("paths", nargs="*", help="transcript files or directories (default: ~/.claude/projects)")
    sm.add_argument("--label", default="me", help="how the subject is named in the report")
    sm.add_argument("--out", default="survey-dataset.json")
    sr = svsub.add_parser("report", help="render a dataset as a self-contained HTML report")
    sr.add_argument("dataset")
    sr.add_argument("--out", default="survey-report.html")
    ss = svsub.add_parser("sample", help="draw a blind-labeling packet from your own transcripts (keep it private)")
    ss.add_argument("paths", nargs="*", help="transcript files or directories (default: ~/.claude/projects)")
    ss.add_argument("--pages", action="append", default=[], metavar="LABEL=LISTFILE",
                    help="a session saved as event-API pages: a file listing the page files, one per line")
    ss.add_argument("--n", type=int, default=200, help="main sample size (default 200)")
    ss.add_argument("--calibration", type=int, default=20, help="practice items, drawn first (default 20)")
    ss.add_argument("--seed", type=int, default=20261006)
    ss.add_argument("--redact", help="a file of regular expressions, one per line; matches become [가림]")
    ss.add_argument("--exclude", action="append", default=[], metavar="PACKET",
                    help="an earlier packet whose items must not be drawn again (e.g. a pilot)")
    ss.add_argument("--limit", action="append", default=[], metavar="LABEL=N",
                    help="keep only a session's first N instructions (cut at a measurement snapshot)")
    ss.add_argument("--out", default="label-packet.json")
    sj = svsub.add_parser("judge", help="mechanical waste floor (codebook v1, tier T1): duplication, failures, cache churn")
    sj.add_argument("paths", nargs="*", help="transcript files or directories (default: ~/.claude/projects)")
    sj.add_argument("--pages", action="append", default=[], metavar="LABEL=LISTFILE",
                    help="a session saved as event-API pages: a file listing the page files, one per line")
    sj.add_argument("--limit", action="append", default=[], metavar="LABEL=N",
                    help="stop a session after its first N instructions (cut at a measurement snapshot)")
    sj.add_argument("--limit-calls", action="append", default=[], metavar="LABEL=N",
                    help="stop a session after its first N main-session API calls")
    sj.add_argument("--out", help="write the numbers-only report as JSON")
    sa = svsub.add_parser("agreement", help="inter-rater agreement of two labels files (kappa per category)")
    sa.add_argument("labels", nargs=2)
    sa.add_argument("--json", action="store_true")

    co = sub.add_parser("contribute", help="contribute anonymous numbers to the public index")
    cosub = co.add_subparsers(dest="contrib_cmd", required=True)
    for name, hlp in (("send", "send anonymously (one click, no account)"), ("github", "open a prefilled GitHub issue (verified)"),
                      ("validate", "check a payload without sending")):
        cp = cosub.add_parser(name, help=hlp)
        cp.add_argument("file", help="export JSON (skeleton / ledger / agent) or '-' for stdin")
        cp.add_argument("--labels", action="store_true", help="include up to 3 topic labels (they become public)")
        if name == "send":
            cp.add_argument("--url", default=None, help="worker URL (default: discovered from the website)")
    cb = cosub.add_parser("build-site", help=argparse.SUPPRESS)
    cb.add_argument("--site", default="site")
    cb.add_argument("--data-dir", default=None)
    cosub.add_parser("ingest-issue", help=argparse.SUPPRESS)

    c = sub.add_parser("cbi", help="Compute Bubble Index dataset tools")
    csub = c.add_subparsers(dest="cbi_cmd", required=True)
    cv = csub.add_parser("validate", help="validate curated CSV files")
    cv.add_argument("paths", nargs="+")
    cv.add_argument("--drafts", action="store_true", help="allow unverified rows")

    args = ap.parse_args(argv)

    if args.cmd in ("proxy", "ledger", "bench", "cbi", "agent", "contribute", "backtest", "survey"):
        return _tools(args)

    if args.cmd == "serve":
        import uvicorn

        from .web import create_app

        uvicorn.run(create_app(GraphStore(args.db)), host=args.host, port=args.port)
        return 0

    if args.cmd == "export":
        sys.stdout.write(topics_cypher(GraphStore(args.db).topics(k=args.k, limit=100_000)))
        return 0

    store = GraphStore(args.db) if args.save else None
    try:
        if args.source == "-":
            results = process_text(sys.stdin.read(), store, args.save)
        elif args.source.startswith("https://"):
            results = process_text(args.source, store, args.save)
        else:
            with open(args.source, "rb") as f:
                results = process_bytes(f.read(), store, args.save)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    for r in results:
        if args.json:
            print(json.dumps(r["skeleton"], ensure_ascii=False, indent=2))
        elif args.cypher:
            sys.stdout.write(skeleton_cypher(Skeleton.from_dict(r["skeleton"])))
        else:
            print(_summary(r["skeleton"]))
            if r.get("delete_token"):
                print(f"\ndelete token: {r['delete_token']}")
            print()
    return 0


def _ledger(path):
    from .proxy import Ledger

    return Ledger(ledger_path(path))


def _tools(args) -> int:
    if args.cmd == "proxy":
        import uvicorn

        from .proxy import ProxyOptions, ResponseCache, create_proxy_app

        opts = ProxyOptions(openai_base=args.openai_base, anthropic_base=args.anthropic_base,
                            compact=not args.no_compact, gratitude=not args.no_gratitude,
                            cache=args.cache, cache_all=args.cache_all)
        ledger = _ledger(args.ledger)
        cache = None
        if args.cache or args.cache_all:
            cache = ResponseCache(os.path.join(os.path.dirname(os.path.abspath(ledger_path(args.ledger))), "cache.sqlite3"))
        print(f"pickaxetax proxy on http://{args.host}:{args.port}  "
              f"(OpenAI-compatible: /v1  ·  Anthropic: base URL as-is)", file=sys.stderr)
        uvicorn.run(create_proxy_app(opts, ledger=ledger, cache=cache), host=args.host, port=args.port, log_level="warning")
        return 0

    if args.cmd == "ledger":
        ledger = _ledger(args.ledger)
        if args.export:
            print(ledger.export())
            return 0
        s = ledger.summary()
        t = s["totals"]
        print(f"requests        {t['requests']:,}  ({t['measured_requests']:,} measured by provider, rest estimated)")
        print(f"spent           input {t['input_tokens']:,} | output {t['output_tokens']:,} | reasoning {t['reasoning_tokens']:,}")
        print(f"re-sent context {t['history_tokens']:,} tokens = {t['history_share_pct']}% of input")
        print(f"avoided         input {t['avoided_input']:,} | output {t['avoided_output']:,}  ({t['avoided_pct']}%)")
        for g in s["groups"]:
            print(f"  {g['provider']:<9} {g['model'][:32]:<32} {g['action']:<20} {g['requests']:>6}")
        return 0

    if args.cmd == "bench":
        from .bench import TASKS, TASKSET_VERSION, existing_result, run, settings_key, validate_files

        if args.bench_cmd == "tasks":
            print(f"task set {TASKSET_VERSION}: {len(TASKS)} tasks")
            for t in TASKS:
                print(f"  {t['id']:<14} {t['prompt']}")
            return 0
        if args.bench_cmd == "validate":
            bad = {p: e for p, e in validate_files(args.paths).items() if e}
            for p, errs in bad.items():
                for e in errs:
                    print(f"{p}: {e}", file=sys.stderr)
            return 1 if bad else 0
        settings = {"temperature": 0}
        if args.reasoning_effort:
            settings["reasoning_effort"] = args.reasoning_effort
        key = settings_key(args.model, settings)
        prior = existing_result(args.out, key)
        if prior and not args.force:
            print(f"already measured: {prior}\nNo need to spend compute again (use --force to override).", file=sys.stderr)
            return 3
        api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
        res = run(args.base_url, args.model, api_key=api_key, settings=settings, max_tokens=args.max_tokens,
                  progress=lambda t, r: print(f"  {t['id']:<14} {'ok ' if r['correct'] else 'BAD'} {r['completion_tokens']:>6} tok",
                                              file=sys.stderr))
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps(res["summary"], indent=2))
        print(f"\nwrote {path} -- open a pull request to contribute it.", file=sys.stderr)
        return 0

    if args.cmd == "agent":
        return _agent(args)
    if args.cmd == "backtest":
        return _backtest(args)
    if args.cmd == "survey":
        return _survey(args)

    if args.cmd == "contribute":
        return _contribute(args)

    if args.cmd == "cbi":
        from .cbi import validate_csv

        errs = [e for p in args.paths for e in validate_csv(p, require_verified=not args.drafts)]
        for e in errs:
            print(e, file=sys.stderr)
        return 1 if errs else 0
    return 2


def _agent(args) -> int:
    if args.agent_cmd == "hook":
        if args.action in ("pre-tool-use", "pre-compact"):
            from .agent.guard import run_hook

            return run_hook(args.action)
        from .agent.install import install, settings_path, uninstall

        path = settings_path(args.scope)
        if args.action == "install":
            print(f"installed pickaxetax guard hook in {install(path)}")
            print("Re-reads of unchanged files are now blocked once per file; see savings with `pxt ledger`.")
        else:
            print("removed" if uninstall(path) else "nothing to remove", f"({path})")
        return 0

    from .agent import audit_session, export, find_transcripts, merge, parse, tips

    files = find_transcripts(args.paths or None, args.since)
    if not files:
        print("no Claude Code transcripts found (looked in ~/.claude/projects)", file=sys.stderr)
        return 1
    if args.agent_cmd == "bound" and not args.export:
        return _agent_bound(files, args)
    reports = [audit_session(parse(f)) for f in files]
    reports = [r for r in reports if r["api_calls"]]
    m = merge(reports)
    if args.export:
        from .agent import bound

        bounds = [r for r in (bound.analyze(f) for f in files) if r["api_calls"]]
        print(json.dumps(export(m, bound.export(bounds) if bounds else None), indent=2))
        return 0
    if args.json:
        print(json.dumps({"summary": m, "sessions": reports}, indent=2, default=list))
        return 0
    t = m["tokens"]
    print(f"sessions        {m['sessions']}  ·  API calls {m['api_calls']:,} (+{m['subagent_calls']:,} subagent)  ·  tool calls {m['tool_calls']:,}")
    print(f"input processed {t.get('processed_input', 0):,} tokens  (cache hits {m['cache_hit_pct']}%)  ·  output {t.get('output', 0):,}")
    print(f"peak context    {m['peak_context']:,} tokens  ·  tool results re-read later: {m['carried_share_pct']}% of all input")
    for k, label in (("duplicate_reads", "re-read unchanged files"), ("large_results", "large tool results"), ("failed_repeats", "repeated failures")):
        v = m[k]
        print(f"{label:<24}{v['count']:>5}  ·  {v['tokens']:>10,} tokens  ·  carried {v['carried_tokens']:>12,}")
    print("\ntop tools by carried tokens:")
    for name, b in list(m["by_tool"].items())[:6]:
        print(f"  {name[:28]:<28} {b['calls']:>5} calls  {b['result_tokens']:>10,} tok  carried {b['carried_tokens']:>12,}")
    details = [d for r in reports for d in r["_detail"]["large_results"]]
    if details:
        print("\nlargest tool results (local only):")
        for tok, name, label in sorted(details, reverse=True)[:5]:
            print(f"  {tok:>8,} tok  {name:<6} {label}")
    lang = "ko" if os.environ.get("LANG", "").startswith("ko") else "en"
    for tip in tips(m):
        print(f"- {tip[lang]}")
    return 0


def _agent_bound(files: list[str], args) -> int:
    from .agent import bound

    reports = [r for r in (bound.analyze(f, min_shared=args.min_shared, calibrated=not args.raw) for f in files)
               if r["api_calls"]]
    if not reports:
        print("no API calls found in the transcripts", file=sys.stderr)
        return 1
    m = bound.merge(reports)
    if args.json:
        print(json.dumps(m, indent=2))
        return 0
    measured = m["measured_input"]
    print(f"sessions {m['sessions']}  ·  API calls {m['api_calls']:,}  ·  input processed {measured:,} tokens")
    print(f"pinned (fixed base + context the transcript does not show): {100 * m['pinned_input'] / measured:.1f}%")
    names = {"P=inf": "drop after last use, never re-fetch", "P=0": "oracle, free re-fetch"}
    print(f"\n{'policy':<40}{'bound input':>16}{'avoidable':>11}")
    for label, p in sorted(m["policies"].items(), key=lambda kv: -kv[1]["bound_input"]):
        name = names[label] if label in names else f"oracle, re-fetch costs {int(label[2:]):,} tokens"
        print(f"{name:<40}{p['bound_input']:>16,}{p['avoidable_pct']:>10.1f}%")
    print(f"\n{'segment kind':<18}{'share of resident':>18}{'dead after last use':>21}{'unneeded':>10}")
    for name, k in m["by_kind"].items():
        print(f"{name:<18}{k['share_of_resident_pct']:>17.1f}%{k['dead_after_last_use_pct']:>20.1f}%{k['unneeded_pct']:>9.1f}%")
    if m["written_tokens"]:
        best = m["policies"].get("P=0", {}).get("bound_input", measured)
        print(f"\ninput per token written to disk: {measured / m['written_tokens']:,.0f} (oracle: {best / m['written_tokens']:,.0f})")
    print("References are detected lexically; see research/belady-bound.md for what that means for these numbers.")
    return 0


def _survey(args) -> int:
    from .survey import dataset, report

    if args.survey_cmd in ("sample", "agreement"):
        return _survey_labeling(args)
    if args.survey_cmd == "judge":
        return _survey_judge(args)
    if args.survey_cmd == "report":
        with open(args.dataset, encoding="utf-8") as f:
            ds = json.load(f)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report.render(ds))
        print(f"wrote {args.out} (dataset sha256 {dataset.digest(ds)[:16]}…)")
        return 0
    from datetime import datetime, timezone

    from .agent import find_transcripts
    from .survey.measure import with_subagents

    files = find_transcripts(args.paths or None)
    sessions = []
    for i, path in enumerate(files, 1):
        m = with_subagents(path, include_series=True)
        if not m["api_calls"]:
            continue
        models = m.get("models") or {}
        sessions.append({"id": f"S{i:02d}", "type": "", "model": max(models, key=models.get) if models else "",
                         "origin": "", "span_hours": m["span_hours"], "session_list": None, "measurement": m,
                         "source": "local", "partial": False, "base_override": None})
    if not sessions:
        print("no Claude Code transcripts with API calls found", file=sys.stderr)
        return 1
    stamps = datetime.now(timezone.utc).date().isoformat()
    ds = dataset.build({"label": args.label, "who": args.label, "scope": "Claude Code (local transcripts)",
                        "period": f"measured {stamps}", "sources": "provider-recorded usage in local transcripts",
                        "dataset_path": args.out, "notes": []}, sessions)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(ds, f, ensure_ascii=False, separators=(",", ":"))
    print(f"measured {len(sessions)} sessions -> {args.out} (numbers only; no text, paths or ids)")
    return 0


def _survey_judge(args) -> int:
    from .agent import find_transcripts
    from .survey import judge

    limits = {k: int(v) for k, _, v in (x.partition("=") for x in args.limit)}
    call_limits = {k: int(v) for k, _, v in (x.partition("=") for x in args.limit_calls)}
    sources = {}
    for i, path in enumerate(find_transcripts(args.paths or None) if (args.paths or not args.pages) else [], 1):
        sources[f"S{i:02d}"] = path
    for spec in args.pages:
        label, _, listfile = spec.partition("=")
        with open(listfile, encoding="utf-8") as f:
            sources[label] = [l.strip() for l in f if l.strip()]
    per = {}
    for label, src in sources.items():
        r = judge.judge_source(src, limits.get(label), call_limits.get(label))
        if r["calls"]:
            per[label] = r
    if not per:
        print("no sessions with API calls found", file=sys.stderr)
        return 1
    rep = judge.combine(per)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    print(f"{'session':8} {'calls':>7} {'input':>15} {'W1 dup':>10} {'W2 fail':>10} {'W6 churn':>12} {'floor %':>8} {'price %':>8}")
    for label, r in sorted(per.items()):
        print(f"{label:8} {r['calls']:>7,} {r['input_processed']:>15,} {r['W1']['tokens']:>10,} {r['W2']['tokens']:>10,} "
              f"{r['W6']['tokens']:>12,} {r['floor_pct_of_input']:>8.3f} {r['floor_pct_price_weighted']:>8.2f}")
    t = rep["total"]
    print(f"{'total':8} {t['calls']:>7,} {t['input_processed']:>15,} {t['W1']['tokens']:>10,} {t['W2']['tokens']:>10,} "
          f"{t['W6']['tokens']:>12,} {t['floor_pct_of_input']:>8.3f} {t['floor_pct_price_weighted']:>8.2f}")
    print("Floor only: the mechanical tier of codebook v1. W3, W4, W5, W7, W8 need validated rules or human judgment.")
    return 0


def _survey_labeling(args) -> int:
    from .survey import labeling

    if args.survey_cmd == "agreement":
        files = []
        for path in args.labels:
            with open(path, encoding="utf-8") as f:
                lab = json.load(f)
            errs = labeling.validate_labels(lab)
            if errs:
                print(f"{path}: not a valid labels file ({', '.join(errs[:5])})", file=sys.stderr)
                return 1
            files.append(lab)
        try:
            r = labeling.agreement(*files)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1
        print(json.dumps(r, ensure_ascii=False, indent=1) if args.json else labeling.render_agreement(r))
        return 0
    from .agent import find_transcripts

    sessions = {}
    for i, path in enumerate(find_transcripts(args.paths or None) if (args.paths or not args.pages) else [], 1):
        items = labeling.session_instructions(path)
        if items:
            sessions[f"S{i:02d}"] = items
    for spec in args.pages:
        label, _, listfile = spec.partition("=")
        with open(listfile, encoding="utf-8") as f:
            pages = [l.strip() for l in f if l.strip()]
        items = labeling.session_instructions(pages)
        if items:
            sessions[label] = items
    for spec in args.limit:
        label, _, n = spec.partition("=")
        if label in sessions:
            sessions[label] = sessions[label][: int(n)]
    if not sessions:
        print("no transcripts with instructions found", file=sys.stderr)
        return 1
    exclude = set()
    for path in args.exclude:
        with open(path, encoding="utf-8") as f:
            exclude |= labeling.shown_items(json.load(f))
    patterns = []
    if args.redact:
        with open(args.redact, encoding="utf-8") as f:
            patterns = [l.rstrip("\n") for l in f if l.strip() and not l.startswith("#")]
    packet = labeling.build_packet(sessions, n=args.n, calibration=args.calibration, seed=args.seed, redact=patterns,
                                   exclude=exclude)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(packet, f, ensure_ascii=False, indent=1)
    print(f"wrote {args.out}: {len(packet['calibration'])} practice + {len(packet['items'])} items from "
          f"{packet['population']['instructions']} instructions in {len(sessions)} sessions (sha256 {packet['sha256'][:12]}…)")
    print("It holds excerpts of your conversations. Read it, redact what must not be shared, and hand it to labelers "
          "directly. Do not commit or upload it.")
    return 0


def _backtest(args) -> int:
    from .backtest import label, run

    if args.backtest_cmd == "label":
        if args.sheet:
            n = label.write_sheet(args.paths, args.n, args.sheet, args.key, args.source)
            print(f"wrote {n} items to {args.sheet} (contains text: keep it local) and the key to {args.key}")
            return 0
        print(json.dumps(label.interactive(args.paths, args.n, args.labels, args.source), indent=2))
        return 0
    if args.backtest_cmd == "answer":
        print(json.dumps(label.apply_answers(args.key, args.answers, args.labels), indent=2))
        return 0
    if args.backtest_cmd == "validation":
        with open(args.labels, encoding="utf-8") as f:
            print(json.dumps(label.summarize(json.load(f)), indent=2))
        return 0
    report, manifest = run.run(args.paths, args.source, args.contributor)
    report = run.nan_to_none(report)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(args.manifest, "w", encoding="utf-8") as f:
        f.write("\n".join(manifest) + "\n")
    s = report["sessions"]
    print(f"{report['protocol']} · sessions kept {s['kept']} (dev {s['dev']}, test {s['test']}), excluded short {s['excluded_short']}"
          " · one contributor")
    if not report["aggregate"]:
        return 1

    def fmt(x):
        return f"{x['median']}% [{x['ci95'][0]}, {x['ci95'][1]}] n={x['n']}" if x["n"] else "-"
    rows = [("all sessions", report["aggregate"]["all_sessions"]), ("test split", report["aggregate"]["test_split"])]
    rows += [(f"source: {k}", v) for k, v in report["aggregate"]["by_source"].items()]
    rows += [(f"length: {k} calls", v) for k, v in report["aggregate"]["by_length"].items()]
    print(f"\n{'stratum':<26}{'forget (P=inf)':<30}{'page (P=0)':<30}{'best online (test N)'}")
    for name, b in rows:
        from .backtest import MAX_MISS_RATE

        ok = [f for f in ("window", "recency", "pointer") if (b[f"online_{f}"]["miss_rate"]["median"] or 0) <= MAX_MISS_RATE]
        best = max(ok, key=lambda f: b[f"online_{f}"]["saved_pct"]["median"] or -1) if ok else None
        flag = "  (n < 10: not a finding)" if b["insufficient"] else ""
        online = (f"{best}-{b[f'online_{best}']['n']}: {b[f'online_{best}']['saved_pct']['median']}%, "
                  f"miss {b[f'online_{best}']['miss_rate']['median']}%") if best else f"none within {MAX_MISS_RATE}% misses"
        print(f"{name:<26}{fmt(b['oracle_Pinf']):<30}{fmt(b['oracle_P0']):<30}{online}{flag}")
    print(f"\nreport: {args.out} (publishable) · manifest: {args.manifest} (private; its digest is in the report)")
    return 0


def _contribute(args) -> int:
    from pathlib import Path

    from . import contrib

    if args.contrib_cmd == "build-site":
        from .contrib_ops import build_site

        print(json.dumps(build_site(Path(args.site), Path(args.data_dir) if args.data_dir else None)))
        return 0
    if args.contrib_cmd == "ingest-issue":
        from .contrib_ops import ingest_issue

        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            print(ingest_issue(json.load(f), Path.cwd()))
        return 0

    raw = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    try:
        payload = contrib.from_export(json.loads(raw), labels=args.labels)
    except (ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    errs = contrib.validate(payload)
    if errs:
        for e in errs:
            print(f"invalid: {e}", file=sys.stderr)
        return 1
    if args.contrib_cmd == "validate":
        print(f"valid {payload['kind']} contribution ({len(json.dumps(payload))} bytes)")
        return 0
    if args.contrib_cmd == "github":
        url = contrib.github_issue_url(payload)
        print(url)
        try:
            import webbrowser

            webbrowser.open(url)
        except Exception:
            pass
        return 0
    print("sending (solving a small proof-of-work, a few seconds)...", file=sys.stderr)
    try:
        res = contrib.send(payload, args.url)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"thank you! contribution {res['id']}")
    print(f"delete it any time: curl -X DELETE -H 'X-Delete-Token: {res['delete_token']}' <worker>/contribute/{res['id']}")
    return 0


def ledger_path(path):
    from .proxy.ledger import DEFAULT_PATH

    return path or DEFAULT_PATH


if __name__ == "__main__":
    raise SystemExit(main())
