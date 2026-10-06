# Mechanical tier v1: the waste floor, decided by code

Codebook: `waste-codebook-v1.md`. Code: `pickaxetax/survey/judge.py`, run as
`pxt survey judge`. Tests: `tests/test_judge.py`. This page fixes the operational details
the codebook leaves to implementation, before any result is published. A change to any rule
below is a new version (v2) and every result names the version it used.

## What is counted

Only input-side tokens, i.e. tokens that entered a context. Event-API logs record output
tokens at the start of a stream, before they are final, so output cannot be compared across
sources and is left out of the floor.

| Category | Rule | Tokens counted |
|---|---|---|
| **W1 Duplication** | A tool call with the same tool name and the same input (canonical JSON) as an earlier call in the same context (the main session, or sub-agents), whose result text is byte-identical to that earlier call's result, with no compaction in between | The repeated result's tokens, where it arrives |
| **W2 Failure** | A tool result marked as an error | The error result's tokens |
| **W6 Cache churn** | On the main session only: call *i* had to write to the cache part of the context that call *i−1* already held. Missed = min(cache write of *i*, context of *i−1* − cache read of *i*), counted when it exceeds 2% of the previous context. Skipped when the context shrank (compaction or a cleared session) | The missed tokens |

Token estimates for tool results use `pickaxetax.tokens.estimate_tokens`. Cache figures come
from the provider-recorded usage of each call.

## Views

- **Raw:** floor tokens as a share of all input processed (uncached input + cache reads +
  cache writes, main session and sub-agents).
- **Price-weighted:** the same tokens priced as cache writes (1.25×), as a share of the
  input-side cost (uncached 1×, cache reads 0.1×, cache writes 1.25×). This is closer to the
  compute and money spent, because cache reads are cheap and cache writes are not.

## What it does not count, by design

- W3, W4, W5, W7, W8: they need validated rules or human judgment (codebook §2).
- The carry of a W1 or W2 result into later calls: that is W5.
- Output tokens of failed or duplicated calls (see above).
- Duplicates across contexts (a sub-agent re-reading what the main session read): the
  sub-agent did not have it, so it is not a duplicate by this rule.

So the floor is deliberately low. It is the part nobody can dispute, not an estimate of
total waste.

## Snapshots

A session that kept being used after it was measured is cut at the measurement: by
instruction count (`--limit LABEL=N`) or by main-session call count
(`--limit-calls LABEL=N`).
