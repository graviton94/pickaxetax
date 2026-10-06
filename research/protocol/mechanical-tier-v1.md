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
| **W1 Duplication** | A tool call with the same tool name and the same input (canonical JSON) as an earlier call in the same context (the main session, or one sub-agent run), whose result text is byte-identical to that earlier call's result, with no compaction in between | The repeated result's tokens, where it arrives |
| **W2 Failure** | A tool result marked as an error | The error result's tokens |
| **W6 Cache churn** | On the main session only: call *i* had to write to the cache part of the context that call *i−1* already held. Missed = min(cache write of *i*, context of *i−1* − cache read of *i*), counted when it exceeds 2% of the previous context. Skipped when the context shrank (compaction or a cleared session) | The missed tokens (see below: a cost, not removable tokens) |

Each sub-agent run is its own context: a local transcript's sub-agent files
(`<session>/subagents/*.jsonl`) are read with it, and event-API lines are keyed by the tool
call that started the sub-agent (`parent_tool_use_id`).

Token estimates for tool results use `pickaxetax.tokens.estimate_tokens`. Cache figures come
from the provider-recorded usage of each call.

## Views

W1 and W2 tokens need not have entered any context: they are **removable tokens**. W6 tokens
are different. They would have been processed anyway, as cache reads; what was wasted is
processing them from scratch (prefill compute) and paying the cache-write price instead of the
cache-read price. So W6 adds no removable tokens, only a **removable cost**.

- **Tokens:** removable tokens (W1 + W2) as a share of all input processed (uncached input +
  cache reads + cache writes, main session and sub-agents).
- **Cost:** W1 + W2 priced as cache writes (1.25×), plus W6 priced at the write premium over a
  read (1.25× − 0.1× = 1.15×), as a share of the input-side cost (uncached 1×, cache reads
  0.1×, cache writes 1.25×). This is closer to the compute and the money spent, because cache
  reads are cheap and cache writes are not.

## W6, broken down by cause

Descriptive only; the floor does not change. Each counted re-write is labelled by what came
before it: a model switch (the cache is per model), or else the idle time since the previous
call, against the cache lifetimes the provider offers (5 minutes by default, 1 hour as an
option): under 5 minutes, 5 minutes to 1 hour, over 1 hour. A re-write after a long idle gap
is waste only in the codebook's sense (the tokens could have been kept by a longer-lived
cache, a smaller context, or a summary); whether that should count the same as a re-write a
minute later is an open question for the joint review, and every result shows the split.

The cost view is also reported under two alternative counts, as a sensitivity analysis added
after the first results were seen: without re-writes after an idle gap of over an hour, and
with re-writes inside five minutes only. The v1 count (all re-writes) stays the primary
result; the alternatives never replace it.

## Carry of W1 and W2, descriptive

A W1 or W2 result stays in the context and is processed again by every later main-chain call
until the next compaction. The judge reports that carry (tokens × later calls) next to the
floor, never in it: whether carrying something is waste is W5's to judge (rule tier).

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
