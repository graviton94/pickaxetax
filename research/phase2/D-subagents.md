> Working memo from cycle D of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# Question D - does delegating to sub-agents save the main context, or move the cost?

Scripts: `run.py` (extract, writes `data.json` with per-run aggregates), `summ.py` (tables). Data: S01, S02, S03, S09 (the four sessions with sub-agents), at the dataset-v2 cuts. Only aggregate numbers appear here.

## Method
- Input processed per call = input_tokens + cache_read + cache_creation, one value per message.id (max over duplicate lines); main and each sub-agent de-duplicated separately. "Cache-weighted" variant = input + 0.1*read + 1.25*write.
- Run = one agentId (76 runs: S01 1, S02 7, S03 37, S09 31). Event-API sessions: agentId == tool_use id of the main Agent call, 75/75 linked. S01: one sub-agent and one Agent call, so linked 1:1 by assumption; the local agent id does not appear as a task-id in any notification, so no id-level link exists.
- What the main session gets back: (a) the Agent tool_result, a launch acknowledgement of a constant ~261 tokens in every run (agents run async), and (b) a later `<task-notification>` user message carrying `<result>`. (b) is observable for only 42 of 76 runs (S01 0/1, S02 2/7, S03 21/37, S09 19/31); the other 34 have a "completed" system notification but no result-bearing user message in the data. For those, the result is imputed as the sub-agent's final assistant message + 210 tokens of wrapper (the median wrapper measured on the 42 observed runs, range 172-369). "returned" = ack + notification. Tokens via `pickaxetax.tokens.estimate_tokens`.
- Sub-agent reads = estimate_tokens of every tool_result in its own sidechain.
- Main context series per session = per-call input processed; a "drop" = a call whose context is < 0.8x the previous call (matches compact_boundary markers: S02 3, S03 15 vs 14, S09 7, S01 3 vs 1). Residency of X tokens arriving before main call k = X * (index of next drop after k, else end of session, minus k) = extra main input processed (same unit as sub-agent input processed).
- Delegation cost = sub-agent input processed + residency of ack (from the call after launch) + residency of the result (from its delivery time).
- Counterfactual = each sub-agent tool result placed in the main context at the main call index current at that result's timestamp (not earlier than the call after launch), resident until the next drop. Assumption: the main session would have needed the same reads, and nothing else changes (same compaction points, no extra main calls, no sub-agent prompt/system overhead). Sensitivities: all reads at launch (cf_start) or all at delivery (cf_end).

## 1. Per-run distribution (median / p90)
| scope | runs | API calls | input processed | max ctx | sub-agent reads (tok) | returned to main (tok) | compression ratio (input / returned) |
|---|---|---|---|---|---|---|---|
| S01 | 1 | 8 | 444,284 | 90,549 | 59,667 | 473 (imputed) | 939 |
| S02 | 7 | 27 / 47 | 3.21M / 9.36M | 197k / 291k | 77k / 109k | 2,447 / 2,695 | 3,491 / 5,829 |
| S03 | 37 | 5 / 33 | 263k / 3.50M | 66k / 174k | 9.0k / 52k | 470 / 474 | 554 / 7,447 |
| S09 | 31 | 47 / 81 | 4.37M / 8.07M | 127k / 178k | 29k / 42k | 4,721 / 7,044 | 902 / 2,158 |
| pooled | 76 | 23 / 70 | 2.25M / 7.75M | 111k / 188k | 27.6k / 58.4k | 475 / 5,532 | 904 / 6,107 |

Pooled ratio (sum input / sum returned) = 1,489 (observed-result runs only: 1,735). Returned tokens in S03 are mostly the 261-token ack plus a short summary. Sub-agent input per call averages 110k tokens; main context at launch is median 492k / p90 736k. Sub-agents read ~1/116 of what they process (pooled reads / input = 0.9%).

## 2. Delegation cost vs counterfactual (units: input tokens processed, imputed result)
| scope | delegation | counterfactual (reads resident in main) | cf / deleg | share of runs where delegation cheaper | result-summary share of delegation |
|---|---|---|---|---|---|
| S01 (1) | 0.52M | 9.37M | 18.1 | 1/1 | 14% |
| S02 (7) | 39.7M | 106.2M | 2.68 | 7/7 | 7% |
| S03 (37) | 51.0M | 78.1M | 1.53 | 32% | 3% |
| S09 (31) | 213.9M | 230.4M | 1.08 | 58% | 19% |
| pooled (76) | 305.1M | 424.1M | 1.39 | 50% (38/76) | 15% |

Median per-run cf/deleg 1.02. Sensitivity of pooled cf/deleg to read arrival: all reads at launch 1.33, all at delivery 1.53; with the unimputed (observed-result-only) delegation cost: 284M vs 424M = 1.49, 53% of runs cheaper. By run size (pooled, imputed): <=10 calls (29 runs) cf/deleg 1.97 but delegation cheaper in only 31% of runs (median per-run cf/deleg 0.52: little is read, but every call re-processes the sub-agent's context); 11-50 calls (33 runs) 2.00, cheaper in 73%; >50 calls (14 runs) 0.87, cheaper in 36%. 5 of 76 runs overlapped a main-context drop.
Average residency of a read in the counterfactual = 189 further main calls; of the returned summary = 254 calls (it arrives later, and early-session tails are long).

Sensitivity - the counterfactual main session would also have to make the sub-agent's calls itself, each at main-context size (median 492k vs 110k per sub-agent call): adding calls x main context at launch to the counterfactual gives 1,561M vs 305M = 5.1x, delegation cheaper in 76/76 runs (per session 4.4x to 25.5x; the call term is 73% of the counterfactual in S03 and S09). This is outside the stated "nothing else changes" assumption but is the larger effect.

## 3. Sub-agent share of input
| session | main calls | sub-agent runs | sub-agent calls | main input | sub-agent input | sub share (raw) | sub share (cache-weighted) | share of sub input in runs with >50 calls |
|---|---|---|---|---|---|---|---|---|
| S01 | 402 | 1 | 8 | 169.5M | 0.44M | 0.3% | 0.8% | 0% (0 runs) |
| S02 | 1,303 | 7 | 221 | 574.7M | 37.0M | 6.0% | 7.6% | 0% (0) |
| S03 | 4,821 | 37 | 460 | 2,055.4M | 49.5M | 2.4% | 3.7% | 0% (0) |
| S09 | 4,056 | 31 | 1,673 | 1,658.3M | 173.6M | 9.5% | 10.8% | 80.5% (14 runs) |
| pooled | 10,582 | 76 | 2,362 | 4,457.9M | 260.6M | 5.5% | 6.8% | 53.6% (14 runs) |

## Caveats
- Result tokens for 34/76 runs are imputed (final sub-agent message + 210); results of S03/S02 runs are often a short summary. Notification content is only visible as user text; system task events carry no result.
- Notification delivery time = the user line's timestamp; imputed delivery = the sub-agent's last line. Background agents run in parallel with the main loop, so residency is counted from timestamps.
- Main context drops are inferred from a 20% fall; a drop that the counterfactual itself would have triggered earlier is ignored. Raw input-processed is not cost: most of both sides is cache read (cache-weighted shares are only 1-2 points higher).
- S01 is a single run and S02 has 7, so session-level medians there are not stable. S02/S03 cut at the measured API-call limit; sub-agent lines after the cut are not present.
- Output tokens are not used (per-message usage output counts are streaming placeholders).

## Findings
1. Sub-agents are not context-free: delegation costs a pooled 305M input-processed vs 424M for reading the same material in the main session (1.4x cheaper), and it is cheaper in only half of the runs (50%).
2. The saving is mostly "cheap context vs expensive context", not compression: a sub-agent call processes ~110k tokens vs ~492k for a main call; once the main session also pays for its own extra calls, delegation is 5.1x cheaper and wins in 76/76 runs.
3. The compression ratio is huge (median 904, p90 6,107; sub-agents read ~27k tokens and return ~475), so the returned summary is only ~15% of delegation cost; the cost moves into the sub-agent's own repeated re-reads (input/reads = 116x).
4. Delegation does not pay when the run is long or tiny: runs with >50 calls (14, all in S09) cost 0.87x of the counterfactual and are cheaper in 36% of runs; runs with <=10 calls are cheaper in only 31%; the sweet spot is 11-50 calls (cheaper in 73%).
5. Sub-agents are 5.5% of total input overall (0.3% in S01 to 9.5% in S09), but 54% of that spend sits in the 14 runs over 50 calls.
