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

## Analysis pipeline (`antitoken/analyze`)

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

## Graph model (`antitoken/graph`)

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
