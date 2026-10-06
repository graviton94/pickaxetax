> Working memo from cycle A of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots (B uses only the public `dataset-v2.json`). Scripts are not published because they read the transcripts.

# Phase 2 / A: context anatomy (10 sessions, dataset-v2 cut)

## Method
- Main session only (sidechains skipped), as `bound` does. `bound.read_trace_lines` parsing loop copied locally (verified identical segment/context counts) so each tool_result/tool_input/persisted_write segment carries a tool label (tool_use_id -> name; Bash split into Bash-read (cat/head/tail/sed -n/grep/rg/find/ls/git log|show|diff at start of command) vs Bash-other; mcp__* -> mcp). Then `calibrate` + `link`.
- Residency = calibrated tokens x (end - birth) token-calls. Shares use the sum over non-unattributed segments (call it visible residency) as denominator unless stated. Visible residency is 57.6% of measured input; unattributed residency is 29.9%; the remainder is the fixed base.
- Idle = share of a segment's residency spent at calls that are not a ref call (birth counts as a ref). Dead = after the last ref (dead is a subset of idle).
- Size thresholds and B are in calibrated tokens (factor ~2 x the text estimate).
- Pooled = all segments / all calls of the 10 sessions together (dominated by S03, S09, S10 which hold ~65% of calls).
- Spearman is pure python (average ranks); p-values are approximate.

## 1. Concentration of residency (non-unattributed segments)

| session | segments | top 1% | top 5% | top 10% | >2k | >5k | >10k | >20k | n>2k |
|---|---|---|---|---|---|---|---|---|---|
| S01 | 1069 | 14.3 | 38.7 | 57.6 | 55.5 | 19.6 | 10.9 | 0.0 | 102 |
| S02 | 3011 | 25.1 | 51.6 | 66.1 | 58.9 | 34.7 | 17.5 | 6.6 | 216 |
| S03 | 11198 | 20.4 | 47.3 | 63.0 | 57.3 | 30.1 | 15.4 | 2.5 | 877 |
| S04 | 422 | 18.6 | 47.5 | 61.1 | 42.8 | 8.8 | 0.0 | 0.0 | 18 |
| S05 | 4096 | 16.4 | 37.1 | 53.7 | 33.6 | 11.5 | 1.8 | 0.5 | 167 |
| S06 | 1081 | 20.9 | 48.6 | 64.5 | 46.5 | 11.6 | 0.0 | 0.0 | 49 |
| S07 | 151 | 29.5 | 59.0 | 70.0 | 60.5 | 41.0 | 29.5 | 0.0 | 10 |
| S08 | 260 | 52.7 | 66.9 | 73.7 | 57.3 | 52.7 | 21.9 | 0.0 | 4 |
| S09 | 9081 | 17.3 | 35.5 | 51.4 | 26.9 | 10.9 | 5.0 | 0.0 | 243 |
| S10 | 6667 | 12.8 | 31.3 | 47.9 | 23.2 | 6.2 | 0.0 | 0.0 | 208 |
| POOLED | 37036 | 19.0 | 40.9 | 56.3 | 41.3 | 19.0 | 8.5 | 1.5 | 1894 |

Values are %% of visible residency held by the largest x%% of segments (by size) or by segments larger than the threshold. Pooled token share (not residency) of the top 1%% / 10%% segments: 18.3%% / 57.3%%.

Residency and token share by segment kind (pooled):

| kind | residency % | token % | idle % of own residency | dead % |
|---|---|---|---|---|
| user_prompt | 1.4 | 1.5 | 77.0 | 16.6 |
| tool_input | 32.3 | 38.8 | 81.6 | 11.9 |
| tool_result | 43.9 | 37.9 | 83.5 | 10.4 |
| persisted_write | 13.9 | 12.6 | 76.8 | 4.8 |
| assistant_text | 4.3 | 5.9 | 80.4 | 8.6 |
| harness | 4.1 | 3.3 | 43.4 | 0.5 |
| compact_summary | 0.0 | 0.1 | 44.8 | 1.0 |

## 2. Which tools produce the residency (pooled; result + input + write segments attributed to the tool)

| tool | residency % | token % | idle % | dead % | segments |
|---|---|---|---|---|---|
| Bash-other | 47.3 | 52.5 | 82.6 | 10.9 | 17584 |
| Bash-read | 20.3 | 15.2 | 84.4 | 10.9 | 6955 |
| Write | 9.9 | 10.1 | 73.3 | 4.7 | 916 |
| Edit | 4.8 | 3.0 | 87.5 | 10.8 | 1740 |
| Read | 3.6 | 2.6 | 76.7 | 9.1 | 1347 |
| mcp | 1.5 | 2.6 | 81.4 | 9.6 | 662 |
| Artifact | 1.4 | 1.4 | 64.9 | 5.8 | 318 |
| Agent | 0.5 | 0.7 | 79.2 | 5.9 | 152 |
| AskUserQuestion | 0.2 | 0.3 | 86.6 | 7.2 | 78 |
| ReadNotifications | 0.2 | 0.3 | 81.2 | 0.8 | 136 |
| TaskCreate | 0.2 | 0.2 | 92.5 | 16.1 | 366 |
| SendUserFile | 0.1 | 0.1 | 95.8 | 57.7 | 160 |

Tool-result segments only:

| tool | residency % | token % | idle % | dead % | segments |
|---|---|---|---|---|---|
| Bash-other | 19.6 | 18.6 | 85.8 | 13.8 | 8792 |
| Bash-read | 17.1 | 12.1 | 83.5 | 7.2 | 3477 |
| Read | 3.3 | 2.3 | 74.7 | 1.8 | 217 |
| mcp | 1.3 | 2.3 | 81.1 | 8.1 | 331 |
| Artifact | 1.3 | 1.3 | 61.8 | 2.5 | 159 |
| Edit | 0.6 | 0.3 | 98.4 | 40.1 | 870 |
| ReadNotifications | 0.2 | 0.3 | 81.2 | 0.6 | 68 |
| Write | 0.2 | 0.2 | 98.1 | 36.6 | 458 |

Tool-input (the call's own arguments) and persisted_write segments are counted under the tool name in the first table; Bash-other input (heredocs, scripts) is the single biggest source.

## 3. Output-budget what-if (tool results only)

Tool results: 15083; >2k: 637, >5k: 132, >10k: 33; with at least one later lexical ref: 11562.

Rule: result seen in full at birth call; at every later call resident size is B instead of n; each later ref (any ref after birth) costs P=1000 re-fetch tokens. 'all' truncates every result >B; 'selective' only those where the saving exceeds the re-fetch cost (an oracle choice). Percent of pooled measured input.

| B | policy | segments cut | gross saved % | re-fetch cost % | net saved % | re-fetches |
|---|---|---|---|---|---|---|
| 2000 | all | 637 | 4.92 | 0.54 | 4.38 | 35686 |
| 2000 | selective | 547 | 4.89 | 0.47 | 4.41 | 31136 |
| 5000 | all | 132 | 1.69 | 0.15 | 1.54 | 9588 |
| 5000 | selective | 125 | 1.68 | 0.14 | 1.54 | 9190 |
| 10000 | all | 33 | 0.34 | 0.04 | 0.29 | 2858 |
| 10000 | selective | 27 | 0.33 | 0.03 | 0.29 | 2235 |

## 4. Unattributed share

| session | calls | calibration factor | unattributed % of input | visible % | base % | compactions |
|---|---|---|---|---|---|---|
| S01 | 400 | 1.96 | 31.0 | 58.0 | 11.0 | 1 |
| S02 | 1303 | 2.00 | 23.2 | 62.2 | 14.7 | 3 |
| S03 | 4820 | 2.05 | 26.4 | 60.0 | 13.6 | 14 |
| S04 | 166 | 1.72 | 19.7 | 50.2 | 30.1 | 0 |
| S05 | 1923 | 1.93 | 27.6 | 59.9 | 12.5 | 3 |
| S06 | 464 | 1.99 | 40.7 | 45.2 | 14.1 | 1 |
| S07 | 66 | 1.82 | 13.9 | 47.9 | 38.2 | 0 |
| S08 | 105 | 1.00 | 53.8 | 24.9 | 21.3 | 0 |
| S09 | 4056 | 1.87 | 33.0 | 57.2 | 9.8 | 7 |
| S10 | 2878 | 2.02 | 35.0 | 52.5 | 12.4 | 5 |

Pooled unattributed: 29.9% of measured input.

Does it grow with context size? Pooled Spearman (n=16137), per-call unattributed growth (tokens, can be negative, 0 when none) vs previous-call context size: rho = 0.003 (p~0.71). Unattributed fraction of the call's measured growth (calls with growth>0) vs context size: rho = -0.015 (p~0.06, n=16123). Per-session rho of growth vs context size ranges -0.09 to 0.14. Mean unattributed fraction of growth by context-size quartile: 33%, 31%, 32%, 31%.

## Caveats
- Lexical reuse detection is unvalidated: refs are a mix of misses (understanding without verbatim trace; makes idle and dead shares too high and re-fetch counts too low) and coincidental hits (re-fetch counts and 'needed' too high). Idle/dead shares inherit this directly.
- Calibration scales visible text by a median factor ~2 (S08 fell back to 1.0 because it had fewer than 5 usable calls); size thresholds and B are in calibrated tokens, so a 2k calibrated threshold is roughly 1k text-estimate tokens. Segments are scaled uniformly, so large tool results may be mis-scaled relative to thinking/harness overhead that is really in the unattributed bucket.
- Unattributed is the residual after the visible growth: thinking blocks, tokenizer error beyond the median factor, harness framing. It is not evidence about any one content type.
- Re-fetch what-if: re-fetch counts count every later lexical ref, not distinct needs; the cut part is assumed to cost exactly P per ref and never to stay resident after a re-fetch. A smarter policy (keep what was just re-fetched) would reduce cost; a policy without an oracle for relevance would also cut things the model needed.
- Residency denominators exclude unattributed and the base; shares of measured input are about 0.58x the shares quoted.
- Sessions are cut at snapshots and S03/S09/S10 dominate pooled numbers.

## Findings
- Residency is concentrated but not extreme: the largest 10% of segments hold 56% of visible residency (top 1%: 19%); segments over 2k tokens (5% of segments) hold 41%, over 10k hold 8%.
- Bash dominates: Bash-other (47% of residency, mostly its own large scripts/heredocs as tool_input plus outputs) and Bash-read (20%) together are two thirds; Read is only 3.6%, Write/Edit 15%.
- About 83% of every tool-result's residency is idle (not a lexical ref call) and ~10% dead after the last ref; the pattern is nearly identical across tools.
- Truncating tool results to a budget saves little: B=2k nets 4.4% of measured input (35.7k re-fetches), B=5k 1.5%, B=10k 0.3%; most residency comes from many mid-size segments, not a few giants.
- Unattributed is ~30% of measured input (14%-54% per session) and does not grow with context: pooled Spearman ~0.00 for growth vs context size, and its share of per-call growth is flat (~31-33%) across context quartiles; it behaves like a constant proportional overhead (thinking/tokenizer), not an accumulating hidden store.
