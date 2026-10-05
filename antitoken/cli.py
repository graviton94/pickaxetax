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
    ap = argparse.ArgumentParser(prog="antitoken", description=__doc__)
    ap.add_argument("--db", default=os.environ.get("ANTITOKEN_DB", "data/antitoken.sqlite3"))
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

    args = ap.parse_args(argv)

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


if __name__ == "__main__":
    raise SystemExit(main())
