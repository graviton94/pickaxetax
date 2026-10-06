# Architecture

```
 share link / export JSON / transcript
                │
        ┌───────▼────────┐   allowlisted hosts only, manual redirects,
        │    ingest/     │   8 MB cap, in-memory
        └───────┬────────┘
                │ RawConversation  (text: memory only, never logged)
        ┌───────▼────────┐
        │   analyze/     │   tokens → keywords → intents → structure → accounting → suggestions
        └───────┬────────┘   raw turns cleared right after
                │ Skeleton  (numbers, labels, salted fingerprints)
        ┌───────▼────────┐
        │    graph/      │   SQLite property graph  ──►  Cypher (Neo4j / Memgraph)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │     web/       │   FastAPI + static SPA
        └────────────────┘
```

## Analysis pipeline (`pickaxetax/analyze`)

| Step | Module | Output |
|---|---|---|
| Token estimate | `tokens.py` | tiktoken `o200k_base` if installed, else a CJK-aware heuristic |
| Keywords | `text.py::rank_keywords` | Topic candidates. User words weigh 2×, assistant words only log-scaled. PII is scrubbed first. Single-mention words that the assistant never echoes are dropped (noise or private detail) |
| Fingerprints | `text.py::simhash` | 64-bit SimHash keyed with the deployment secret. Detects re-asks without keeping text |
| Intents | `intent.py` | user: ask, instruct, clarify, correct, retry, continue, ack, context. assistant: answer, code, followup_question, apology_fix, refusal |
| Structure | `depth.py` | Branch and depth per turn plus typed edges. Thread membership uses transient content cues; depth counts only stored topic labels |
| Accounting | `waste.py` | See below |
| Suggestions | `suggest.py` | A one-shot prompt skeleton built from labels, plus tips ranked by measured waste |

### Token accounting

For each assistant reply *i*, the billed input is everything before it (the history is re-read), and the billed output is the reply itself:

```
billed_input  = Σ_i  context_before(i)
billed_output = Σ_i  tokens(reply_i)
compute_units = billed_input × INPUT_WEIGHT + billed_output      (INPUT_WEIGHT = 0.25)
```

**Optimized replay**: the same useful exchanges, one fresh chat per topic thread, with ack exchanges removed, answers that were later corrected or retried removed, and duplicate prompts removed.
**One-shot bound**: every useful prompt sent once and every useful answer generated once.

Waste attribution:
- `ack`: the full input and output of replies to thank-you or ok turns
- `superseded`: the input and output of answers followed by a correction or retry
- `offtopic_context`: tokens from other threads re-read on each reply

System prompts, tool calls and provider-side caching are not visible in shares, so the figures are **conservative** about absolute cost. Treat the ratios as the meaningful result.

## Graph model (`pickaxetax/graph`)

```
(:Conversation {id, source, language, agenda, metrics…})
   -[:HAS_TURN]->   (:Turn {index, role, tokens, intent, depth, branch, redundant, has_code, fingerprint})
   -[:COVERS {rank}]-> (:Topic {label, conversations, tokens})
(:Turn)-[:ABOUT {rank}]->(:Topic)
(:Turn)-[:NEXT | ANSWERS | DEEPENS | REVISITS | PIVOTS | RETURNS | CORRECTS | RETRIES | CONTINUES]->(:Turn)
(:Topic)-[:CO_OCCURS {count}]->(:Topic)
```

SQLite keeps it dependency-free (`nodes`, `edges` and `meta` tables with JSON props). `skeleton_cypher` and `topics_cypher` emit idempotent `MERGE` statements for a real graph database.

Example query after import: *which intents precede the deepest answers on a topic?*

```cypher
MATCH (p:Topic {label: "kubernetes"})<-[:ABOUT]-(t:Turn {role: "user"})
RETURN t.intent, avg(t.depth) AS depth, count(*) ORDER BY depth DESC
```

## Share-link fetching

- HTTPS only, on an explicit host allowlist (`ingest/share.py::ALLOWED_HOSTS`). Ports other than 443 and credentials in the URL are rejected.
- Redirects are followed manually, and each hop is re-checked against the allowlist (SSRF protection).
- Parsers are layered: the provider JSON API (Claude snapshots), then embedded JSON (`__NEXT_DATA__` and others), then role-attributed DOM.
- Many share pages render client-side and change often. When parsing fails, the user is told to paste the text or upload the export.

## Local proxy (`pickaxetax/proxy`)

```
 client (OpenAI SDK / Anthropic SDK / any compatible tool)
        │  base_url = http://127.0.0.1:8787[/v1]
 ┌──────▼───────────────────────────────────────────────┐
 │ 1. bare "thanks" (no tools, not answering a question) │──► local reply in the provider's exact format
 │ 2. compact: drop earlier thank-you exchanges           │
 │ 3. cache (opt-in): identical temperature-0 requests     │──► local reply
 │ 4. forward with the client's own credentials            │──► provider
 │ 5. meter usage from JSON or the SSE stream              │
 └──────┬───────────────────────────────────────────────┘
        ▼
 ledger.sqlite3 (counts only: tokens in/out/reasoning, re-sent context, avoided)
```

Usage comes from the provider (`measured`) whenever it is reported, and from estimates otherwise. The ledger records which is which, so the "verified savings" north-star metric only counts what can be verified.

## Over-computation benchmark (`pickaxetax/bench`)

A crowd-run harness for CBI layer M. It runs trivial tasks against any OpenAI-compatible endpoint and records completion and reasoning tokens against the minimal answer length. Results are content-addressed by (model, settings, task set), so the same measurement is never paid for twice. CI validates submitted files and recomputes their summaries.

## Static web app (`site/`)

```
 share page (chatgpt.com / claude.ai / …)      site/ (GitHub Pages, CSP connect-src 'none')
 ┌──────────────────────────────┐   #pxt=…   ┌──────────────────────────────────────────┐
 │ bookmarklet reads the DOM     │──────────► │ engine.js: ingest → skeleton (same as py) │
 └──────────────────────────────┘  fragment  │ app.js: render, JSON download             │
            paste / file ─────────────────────►│ no network after load                     │
                                               └──────────────────────────────────────────┘
```

`site/engine.js` is a line-by-line port of the Python engine. The places where Python and JS semantics differ (Unicode `\w`/`\b`/`\d`, code-point lengths, round-half-even, float formatting) are handled explicitly, and `tests/test_parity.py` enforces identical output.

## Coding agent auditor and guard (`pickaxetax/agent`)

- `transcript.py` parses Claude Code JSONL defensively. Usage is de-duplicated per `message.id`, because one response is split across several lines. Subagent (sidechain) traffic is counted separately.
- `audit.py`: a tool result added at call *k* is re-read on every later call until the next compaction (its "carried" tokens). It detects duplicate reads, large results and repeated failures.
- `guard.py`: a PreToolUse (Read) and PreCompact hook. It denies one re-read of an unchanged file, then allows; it fails open and stores only path/size/mtime. Avoided tokens go to the proxy ledger (`action=agent_dup_read_blocked`).
- `bound.py`: the offline-optimal context bound (`pxt agent bound`). It splits each call's context into segments, rescales them to the measured growth between calls (the remainder is pinned as `unattributed`), finds the later calls whose outputs reuse each segment's distinctive tokens, and computes the least residency per segment and gap. Model and proof: [research/belady-bound.md](../research/belady-bound.md).
- `install.py`: merges hooks into `~/.claude/settings.json` (or the project's), with a backup and idempotent re-runs. The plugin form lives in `claude-plugin/pickaxetax`, with the marketplace at `.claude-plugin/marketplace.json`.

## Backtest and benchmark (`pickaxetax/backtest`)

```
 chat exports / transcripts / agent logs ──► trace.py: one Trace per session (calls, segments, outputs)
                                               │   chats: full-history baseline, estimated tokens
                                               │   agents: measured usage, calibrated
                                               ▼
 agent/bound.py link + bound (oracle, P grid)   policies.py: window / recency / pointer replayed online
                                               ▼
 run.py: dev/test split by hash → tune N on dev → report on test; strata; bootstrap CIs (stats.py); sensitivity grid
                                               ▼
 backtest-report.json (numbers only) + private manifest (its digest is in the report)
```

The constants in `backtest/__init__.py` are the pre-registered protocol (`research/protocol/backtest-v1.md`); `tests/test_backtest_protocol.py` fails if they drift apart. `label.py` samples (segment, call) pairs in two blind strata for hand validation of the use detector; only answers are stored.

## Contributions (`site/contrib.js`, `worker/`, `pickaxetax/contrib*.py`)

```
 web app / pxt contribute ──(allowlisted JSON + proof of work)──► Cloudflare Worker + D1   (anonymous)
 web app / pxt contribute github ──► GitHub issue form ──► Actions: validate → `contributions` branch (verified)
                                                         │
 Pages build (daily) ◄── /export + /labels (k≥3) + contributions branch ──► site/data/aggregate.js
```

There is one validator, mirrored in JS (browser + worker) and Python (CLI + CI). `tests/test_contrib.py` requires identical verdicts on 45 cases. `worker/test/e2e.mjs` runs against the real Workers runtime in CI.
