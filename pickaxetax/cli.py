"""Command line: analyze locally, serve the web app, export the graph."""

from __future__ import annotations

import argparse
import json
import os
import sys

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
    ah = agsub.add_parser("hook", help="guard hook (called by Claude Code) and its installer")
    ah.add_argument("action", choices=["pre-tool-use", "pre-compact", "install", "uninstall"])
    ah.add_argument("--scope", choices=["user", "project"], default="user")

    c = sub.add_parser("cbi", help="Compute Bubble Index dataset tools")
    csub = c.add_subparsers(dest="cbi_cmd", required=True)
    cv = csub.add_parser("validate", help="validate curated CSV files")
    cv.add_argument("paths", nargs="+")
    cv.add_argument("--drafts", action="store_true", help="allow unverified rows")

    args = ap.parse_args(argv)

    if args.cmd in ("proxy", "ledger", "bench", "cbi", "agent"):
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
    reports = [audit_session(parse(f)) for f in files]
    reports = [r for r in reports if r["api_calls"]]
    m = merge(reports)
    if args.export:
        print(json.dumps(export(m), indent=2))
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


def ledger_path(path):
    from .proxy.ledger import DEFAULT_PATH

    return path or DEFAULT_PATH


if __name__ == "__main__":
    raise SystemExit(main())
