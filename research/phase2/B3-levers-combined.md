> Working memo from cycle B3 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# B3: levers are not additive. What does a realistic bundle save?

All numbers are aggregates over the 10 main sessions (6,579M measured input, dataset v2). No transcript text appears here.

## Method
- One replay engine, copied locally (repo untouched): `read_trace_lines(keep_text)` -> `calibrate` -> `link` (min_shared=1, refs taken over the whole session so a segment kept through a skipped compaction still has refs). Call k's replayed context = base (call-0 context) + live segments (calibrated size; pinned unattributed growth kept by every policy) + re-fetch charges (one-off, not persistent). Segment classes (Write/Edit, shell file-write, inline script, other heredoc) re-derived from command structure; class shares of measured input match A2 exactly (8.0 / 3.8 / 10.2 / 0.9 %).
- Check: with no policy the replay reproduces measured input exactly (0.000% difference, every session; 34 observed compactions applied).
- P1: at an instruction boundary (`_is_instruction`), if the replayed context of the previous call exceeds 200k, drop every segment with `bound.origin` before the boundary and unattributed growth born before it, add a 10k summary segment (dropped again at the next restart).
- P2: Write/Edit/MultiEdit/NotebookEdit inputs and Bash inputs classed as file-write / inline-script / other heredoc (= A2 "(a)+(b)") are 30-token stubs from birth; each later lexical ref (bound refs) while the stub is live adds 1,000 tokens to that call only.
- P3: after adding call k's segments, if replayed context > 390k: charge one read of that full context, then context = base + 22,000 (the call's own new segments fold into the summary).
- Compaction in the replay (this matters, see finding 2). Main regime R2: the harness compacts only at its ceiling. An observed compaction is applied only if the replayed context before it is >= 90% of the observed one (true for the no-policy replay); otherwise it is skipped (its summary and rebuild growth are not added) and the replay compacts by itself when it passes 790k (to base + 22k, uncharged, as observed compactions are in the measured input). Regime R1 (published-style): observed compactions always apply at the observed calls, the replay cannot go above the observed context after one.
- Price-weighted: per call cost = 0.1 x (context kept from the previous call) + 2.0 x (new this call: new segments, summaries, stubs, re-fetches); call 0 and compaction reads use the same rule. Saving is against the same model's no-policy cost (0.715B; the real cache-weighted input is 0.80B per D2, because of cache misses/TTL that this model ignores). Cache-prefix invalidation caused by rewriting old content (stubs, restarts keep the prefix) is NOT modelled.

## Results, % of measured main-session input saved (regime R2)
| session | measured input (M) | P1 | P2 | P3 | P1+P2 | P2+P3 | P1+P3 | P1+P2+P3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S01 | 169 | 62.7 | 7.8 | 46.4 | 65.2 | 45.4 | 62.7 | 65.2 |
| S02 | 575 | 55.7 | -1.5 | 45.6 | 57.2 | 43.2 | 57.9 | 57.2 |
| S03 | 2,055 | 60.9 | 0.3 | 44.7 | 61.2 | 43.5 | 60.9 | 61.2 |
| S04 | 30 | 26.5 | 35.0 | 0.0 | 35.0 | 35.0 | 26.5 | 35.0 |
| S05 | 779 | 37.5 | -5.9 | 42.2 | 41.0 | 42.4 | 51.1 | 52.1 |
| S06 | 166 | 59.3 | -10.1 | 37.4 | 62.7 | 40.1 | 59.3 | 62.7 |
| S07 | 9 | 0.0 | 9.8 | 0.0 | 9.8 | 9.8 | 0.0 | 9.8 |
| S08 | 19 | 32.2 | 3.4 | 0.0 | 34.1 | 3.4 | 32.2 | 34.1 |
| S09 | 1,658 | 57.4 | -4.9 | 44.5 | 59.3 | 44.1 | 60.4 | 59.7 |
| S10 | 1,119 | 50.7 | -13.0 | 41.4 | 52.8 | 38.3 | 52.0 | 53.7 |
| **pooled** | 6,579 | **54.8** | **-4.1** | **43.3** | **56.4** | **42.4** | **57.5** | **58.0** |

Events: P1 146 restarts; P3 85 compactions (82-86 in D2); P2 220k re-fetches (3.3% of input at 1,000 each). Bundle: 103 restarts, 5 P3 compactions, 84k re-fetches.

## Results, price-weighted saving (0.1 kept / 2.0 new; same replay)
| session | measured input (M) | P1 | P2 | P3 | P1+P2 | P2+P3 | P1+P3 | P1+P2+P3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S01 | 169 | 55.3 | -31.2 | 40.7 | 45.7 | 17.3 | 55.3 | 45.7 |
| S02 | 575 | 50.5 | -23.3 | 41.2 | 44.7 | 29.5 | 52.5 | 44.7 |
| S03 | 2,055 | 54.9 | -46.4 | 40.0 | 41.5 | 15.3 | 54.9 | 41.5 |
| S04 | 30 | 20.9 | 12.7 | 0.0 | 12.7 | 12.7 | 20.9 | 12.7 |
| S05 | 779 | 34.8 | -68.0 | 39.0 | 7.2 | 8.8 | 47.4 | 23.5 |
| S06 | 166 | 52.6 | -54.7 | 33.1 | 39.2 | 9.0 | 52.6 | 39.2 |
| S07 | 9 | 0.0 | 1.7 | 0.0 | 1.7 | 1.7 | 0.0 | 1.7 |
| S08 | 19 | 24.0 | -4.6 | 0.0 | 21.3 | -4.6 | 24.0 | 21.3 |
| S09 | 1,658 | 53.6 | -82.6 | 41.3 | 25.2 | -0.5 | 56.3 | 26.2 |
| S10 | 1,119 | 46.8 | -75.4 | 38.0 | 25.0 | 1.8 | 48.0 | 26.3 |
| **pooled** | 6,579 | **50.1** | **-60.0** | **39.4** | **30.7** | **9.4** | **52.6** | **33.1** |

## Do singles reproduce the published numbers?
| lever | published | here, R1 (observed compaction schedule kept) | here, R2 (compaction at the ceiling) | whatif on series, same traces |
|---|---:|---:|---:|---:|
| P1 | 58.5 | 58.6 | 54.8 | 58.5 |
| P2 (a)+(b) | 19.8 | 19.8 | -4.1 | not expressible |
| P2 (a)+(b-file) | 10.5 | 10.5 | -3.4 | |
| P3 | 39-46 | not applicable | 43.3 (43.8 without the compaction-read charge) | 46.1 (cap 390k, 22k) |

Under R1 the P1 and P2 singles reproduce to a tenth of a point (P2 matches A2 session by session: 35.0, 16.6, 20.7, 35.0, 16.2, 28.4, 9.8, 3.4, 19.6, 18.7). The gaps:
- P1, R2 vs series 3.8 points. whatif replays "min(s, x)": when the observed context drops (an observed compaction), the replay drops with it even if it is only 300k. That is a free compaction inside long instructions. The segment replay compacts only at the ceiling, so long instructions (S05, S10) keep more context. With observed compactions forced (R1) the segment replay gives 58.6.
- P3, 43.3 vs 46.1: the series version keeps the same free observed-compaction resets after its own earlier compaction and keeps the call's delta; the segment version also pays the 22k rebuild at 2.0 in price terms. Both sit inside the published 39-46.
- P2 cannot be done on the series at all; it needs segment identity.
- *Correction (cycle E4):* the series column predates the replay fix of cycle B4 (an observed compaction applies only if the replay reached 90% of its size). With the current `whatif.cap` on the public series, P3 gives 42.8%, not 46.1%; the 39–43% range used in the synthesis is unaffected.

## Findings
1. The bundle does not stack: singles of 58.5 + 20 + 43 sum to over 120%, the bundle saves 58.0% of input (price-weighted 33%); P1 alone gives 54.8%, P1+P3 57.5%.
2. P2 (pointers) saves 19.8% only if the compaction schedule stays as observed; with compaction at the ceiling it is -4.1% (-0.7% even with free re-fetches), because slower growth just lets the context sit near the ceiling for more calls. Its real gain appears only in sessions that never reach the ceiling (S04 35%, S07 9.8%, S08 3.4%) or after P1/P3 cap the context: marginal +1.6 points on top of P1, +0.5 on top of P1+P3.
3. Marginal contributions in the full bundle: P1 +15.6 points (58.0 vs 42.4 for P2+P3), P3 +1.6 (vs P1+P2), P2 +0.5 (vs P1+P3). P1 is nearly the whole bundle; P3 mostly helps sessions with long instructions that P1 cannot cut (S05: 37.5 -> 51.1).
4. Price-weighted, pointers are a net loss in this model: each re-fetch is 1,000 new tokens at 2.0 (2,000 units) against 0.1 per stubbed token-call; P1+P2 saves 30.7% vs 50.1% for P1 alone. Coincidental refs drive it: restricting refs to >=3 shared terms gives P1+P2 47.5%, P2+P3 32.7%, bundle 49.1% (P1+P3 52.6%).
5. Realistic bundle (P1+P3, no pointers): 57.5% of input, 52.6% price-weighted; adding pointers adds 0.5 input points and subtracts about 19 price points (about 3 with the >=3 term refs).

## Assumptions the bundle stacks
- P1: a 10k summary is enough at every restart; the user restarts at every boundary above 200k (146 restarts); restart lets the replay's later growth continue unchanged.
- P3: a 22k summary (observed median new part) is enough; harness compacts at 390k (about 85 compactions instead of 34); the compaction call reads the whole context once; later compactions lose nothing needed.
- P2: every stubbed segment is re-fetchable at 1,000 tokens when lexically reused, no re-derivation cost, Edit still works; lexical refs (min_shared=1) are real needs (they are not; 3 terms halves the count).
- Common: no re-reads induced by lost context except P2's charges (P1/P3 induced re-reads are not charged; D2 estimated them at about 6 points for P3); re-injected content after restart equals the observed prompt and harness segments; the observed growth per call (including invisible thinking and overhead, 30% of context growth) is unchanged by the policy; the model's work is the same call sequence; prices assume perfect prefix caching.
- In bundles the replay re-times events: P2 makes P1 fire less often (106 vs 146 restarts), P1 removes the ceiling compactions, so each lever's saving is measured against a context that the others already shrank.

## Caveats
- Sensitivities (R2): P1 summary 30k 53.4%; P1 dropping growth born at the boundary call 54.8% (no change); P2 re-fetch 10k -34%; P3 keeping the call's new segments 43.4%; P3 without compaction-read charge 43.8%.
- Rule-based no-policy baseline (ignoring observed compactions, ceiling 790k, 22k) is +2.2% above measured; measuring against it instead gives P1 56.1, P2 -2.8, P3 44.8, P1+P2 57.9, P2+P3 43.3, P1+P3 58.5, bundle 59.4.
- Summary quality, lost-context errors and the cache-prefix break of rewriting old content are not modelled; all savings are upper bounds on pure token arithmetic.
