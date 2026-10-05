# The offline-optimal context bound

How much context did a session need, at least? This document defines the bound, proves it is optimal for its model, describes how it is measured from Claude Code transcripts, and reports the first measurement (n = 1). Code: [`pickaxetax/agent/bound.py`](../pickaxetax/agent/bound.py), CLI `pxt agent bound`.

## 1. Model

A session is a sequence of API calls *k = 0…N−1*. Call *k* processes a context of *c_k* tokens (measured: input + cache read + cache write). The context consists of:

- a **base** *b* that every call carries: system prompt, tool definitions (taken as *c_0*);
- **segments** *s*: user prompts, assistant text, tool inputs, tool results, harness reminders, compaction summaries. Segment *s* has *n_s* tokens, enters the context at call *birth_s* and stays until the next compaction or the end of the session (*end_s*, exclusive).

The agent's actual policy keeps every segment for its whole window:

```
T_actual = N·b + Σ_s n_s · (end_s − birth_s)          (= Σ_k c_k after calibration, §3)
```

Segment *s* is **needed** at a set of calls *R_s ⊆ [birth_s, end_s)*: always at *birth_s* (the next call consumes it) and at every later call that uses it (§3).

A policy chooses, for every segment and call, whether it is present (*x_{s,k} ∈ {0,1}*), with *x_{s,k} = 1* for every *k ∈ R_s*. Its cost is the token-calls it processes, plus *P* tokens every time a segment that was dropped is brought back (re-materialized):

```
cost = N·b + Σ_s Σ_k n_s · x_{s,k} + P · (number of 0 → 1 transitions after birth)
```

*P* stands for whatever a re-fetch costs: a tool call to re-read a file, a lookup by pointer. *P = 0* is an oracle that prefetches for free. *P = ∞* never re-fetches: a segment can only be dropped after its last use.

## 2. The optimum

**Proposition.** With *R_s* sorted as *r_1 < r_2 < … < r_m*, the minimum cost is

```
T*(P) = N·b + Σ_s [ n_s · m  +  Σ_{i<m} min( n_s · (r_{i+1} − r_i − 1),  P ) ]
```

*Proof.* The cost is a sum over segments with no shared constraint (there is no capacity limit), so each segment can be optimized alone. For one segment, *x* is fixed to 1 at every *r_i*, which costs *n_s · m*. Before *r_1 = birth_s* the segment does not exist, and after *r_m* setting *x = 0* is free and never triggers a re-fetch. What remains are the gaps between consecutive uses, which are independent of each other because *x* is pinned at their ends. In a gap of *g = r_{i+1} − r_i − 1* calls, either *x = 1* throughout (cost *n_s · g*), or *x = 0* somewhere, which forces at least one 0 → 1 transition at or before *r_{i+1}* (cost ≥ *P*). The cheapest schedule with a zero is all zeros, at cost exactly *P*. So each gap costs *min(n_s · g, P)*. ∎

The actual policy is one feasible schedule (all ones), so *T\*(P) ≤ T_actual* for every *P*, and *T\*(P)* grows with *P*.

**Relation to Belady.** Belady's MIN (1966) is the offline optimum for a cache of fixed capacity with unit-size pages, minimizing misses: evict the page whose next use is furthest away. Our setting has variable sizes, no capacity, and a cost that combines residency and misses. The shared core is the use of the next-reference time: here it decides, gap by gap, whether keeping or re-fetching is cheaper (the offline rent-or-buy choice). Adding a capacity limit with variable sizes makes the offline problem NP-hard (Chrobak et al., 2012), so the uncapacitated version is the one that yields an exact, computable bound.

## 3. Measurement

**Segments and windows.** Parsed from the transcript JSONL. Usage is counted once per `message.id`. Messages with zero input usage (API errors, interruptions) are not calls. A `compact_boundary` ends every open window, and the compaction summary becomes a new segment. Subagent (sidechain) traffic has its own context and is excluded.

**Calibration.** The text estimator undercounts the provider's tokenizer, and some context never appears in the transcript (thinking, harness framing, attachments). Growth between consecutive calls, *c_k − c_{k−1}*, is measured exactly, so each call's new segments are rescaled to it:

1. Tokenizer factor *f* = median of measured growth ÷ estimated tokens, over calls that added ≥ 2,000 estimated tokens, where invisible overhead is small relative to the content.
2. The segments born at call *k* are scaled by *min(f, growth ÷ estimate)*.
3. Growth that is left over becomes an **unattributed** segment. It is pinned: the oracle must keep it for its whole window. This is the conservative choice, since nothing visible can show when it is used.
4. When context shrinks without a compaction (the harness cleared something), the shrink enters as a negative unattributed segment, applied to the actual and the oracle alike.

After calibration, *N·b + resident tokens* equals the measured *c_k* at every call (checked in `tests/test_bound.py`).

**References.** A segment is used at call *k > birth_s* if call *k*'s output (assistant text and tool inputs) reuses at least `min_shared` of the segment's distinctive tokens: identifiers and paths of six or more characters, Hangul words of three or more syllables, numbers of four or more digits. Tokens that appear in more than `common_frac` of all outputs (and in more than 3) are ignored as too common to signal use.

Lexical detection fails in both directions:

- **Missed use** (the model read code to understand it and wrote nothing from it verbatim) makes the bound **optimistic**: it drops content that was in fact needed.
- **Coincidental reuse** (a common identifier) makes the bound **pessimistic**: it keeps content that was not needed.

The pinned unattributed share pulls the other way and makes the bound conservative. All of this is why we report a sensitivity grid rather than a single number.

## 4. First measurement (n = 1)

One long, real Claude Code session (anonymized; which work it was is not disclosed, as for every published session). Aggregates only; the snapshot is [`results/belady-session-01.json`](results/belady-session-01.json) and is reproduced with `python research/sensitivity.py <transcript>`.

| | |
|---|---|
| API calls | 322 (1 compaction) |
| Input processed | 149,273,256 tokens |
| Base (call 0) | 46,707 tokens → 10.1% of all input |
| Unattributed (pinned) | 32.4% of all input |
| Ceiling for any context policy in this model | 57.5% |
| Tokenizer factor | 1.93 |

**Bound** (calibrated, `min_shared` = 1, `common_frac` = 0.02):

| Policy | Bound input | Avoidable |
|---|---:|---:|
| Drop after last use, never re-fetch (*P* = ∞) | 135,655,306 | **9.1%** |
| Oracle, re-fetch costs 10,000 tokens | 97,503,874 | 34.7% |
| Oracle, re-fetch costs 1,000 tokens | 78,314,352 | 47.5% |
| Oracle, free re-fetch (*P* = 0) | 74,552,319 | **50.1%** |

**Where the residency was** (share of resident segment tokens, excluding the base):

| Segment kind | Share | Dead after last use | Unneeded at *P* = 0 |
|---|---:|---:|---:|
| unattributed (pinned) | 36.0% | — | — |
| persisted writes (Write/Edit inputs) | 25.1% | 11.1% | 83.5% |
| other tool inputs | 22.9% | 19.7% | 88.9% |
| tool results | 10.6% | 21.9% | 90.9% |
| assistant text | 4.8% | 8.3% | 89.2% |
| user prompts | 0.3% | 33.2% | 95.3% |

**Sensitivity** (avoidable share over `min_shared` ∈ {1, 2, 3} × `common_frac` ∈ {0.01, 0.02, 0.05}):

| Policy | Calibrated | Uncalibrated (estimates only, rest pinned) |
|---|---|---|
| *P* = 0 | 42.7 – 56.5% | 22.7 – 30.0% |
| *P* = 1,000 | 37.9 – 56.3% | 18.4 – 29.9% |
| *P* = 10,000 | 21.0 – 54.9% | 7.9 – 28.6% |
| *P* = ∞ | 3.6 – 38.5% | 1.9 – 20.4% |

Value proxy (rung V1): 1,889 input tokens processed per token written to disk; 943 at the *P* = 0 oracle.

## 5. What this says

1. **Paging, not forgetting.** Dropping content once it is dead is worth little (9.1%, at most 38.5% under the most permissive detection). An oracle that drops content between uses and brings it back on demand is worth 50.1%. In every cell of the sensitivity grid, paging beats forgetting by at least 18 points (at least 9.6 points without calibration). Most context is used again, just not at every call in between. The design implication is an agent that holds **pointers** (path, version, line range, result id) and dereferences them when needed, instead of carrying payloads. A pointer dereference costs on the order of the *P* = 1,000 row: the saving barely drops (47.5%).
2. **The agent's own writes are the largest visible item.** A quarter of resident context is content the agent wrote to disk itself, which is already the source of truth there. 83.5% of that residency was unneeded.
3. **A third of the input is invisible.** 32.4% of all input processed could not be attributed to anything in the transcript. Whether it is thinking, harness framing or something else, neither users nor auditing tools can see it, and only providers can disclose it.
4. **The ceiling is set by what cannot be seen.** With the base and the unattributed share pinned, no context policy can save more than 57.5% in this model. Disclosure would move that ceiling, in one direction or the other.

## 6. Limitations

- **n = 1**, a single agent (Claude Code), a single kind of work (software development). Nothing here generalizes until other sessions are measured. `pxt agent bound` exists so that they can be.
- Segment granularity: a segment is all-or-nothing. Keeping only the used lines of a large tool result would lower the bound further, so at this level it is conservative.
- Token-calls is a proxy. It weights a cached and an uncached token equally. That is right for memory residency (P1), but overstates compute when caching is on.
- *P* is a parameter, not a measurement. A real re-fetch also costs an extra call in some designs; the *P* = 10,000 row shows the effect of an expensive re-fetch.
- The oracle knows the future. The bound measures the size of the opportunity, not the result of any implementable policy. A practical policy (e.g., keeping a pointer plus a recency window) is the next experiment, and should be judged against this bound.

## References

- L. A. Belady. A study of replacement algorithms for a virtual-storage computer. *IBM Systems Journal* 5(2), 1966.
- M. Chrobak, G. J. Woeginger, K. Makino, H. Xu. Caching is hard — even in the fault model. *Algorithmica* 63, 2012.
- P. O'Neil, E. Cheng, D. Gawlick, E. O'Neil. The log-structured merge-tree (LSM-tree). *Acta Informatica* 33, 1996.
- E. F. Codd. A relational model of data for large shared data banks. *Communications of the ACM* 13(6), 1970.
