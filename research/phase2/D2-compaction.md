> Working memo from cycle D2 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots. Paths were compared in memory only and never recorded.

# D2 - What compaction costs and what it makes the agent re-do

Scope: main-session (non-sidechain) calls of the 10 dataset-v2 sessions; usage de-duplicated per message.id; 4 calls with empty usage dropped. 34 compactions in 7 sessions (S01 1, S02 3, S03 14, S05 3, S06 1, S09 7, S10 5); S04, S07, S08 never compact. All numbers are aggregates; no transcript text, paths or commands are reproduced.

Definitions. Context (ctx) of a call = input_tokens + cache_read + cache_creation. Input processed = sum of ctx over calls. Cost-weighted input (cw) = input + 0.1 x cache_read + 1.25/2.0 x cache_creation (5m/1h TTL; all cache writes here are 1h, so 2.0x). Main-session totals: all 10 sessions 6.58B input processed (0.80B cw); the 7 compacting sessions 6.52B (0.79B cw).

## Findings (summary)

1. Compaction fires at a nearly fixed context: pre-compaction ctx median 783k, p90 784k (range 756k-789k) - an auto-compact threshold, not a user choice. Immediately after, ctx is median 64k (p90 75k): compression 12.2x (p90 13.9x). About 42k of the post context is the cached system/tools prefix; the genuinely new part (summary + re-injected material) is median 22k (p90 37k).
2. In the 50 calls after a compaction, 606 of 923 reads (65.7%) hit a path already read before the compaction, carrying 73.9% of the read-result tokens (1.1M tokens, 33k per compaction). BUT the same measure at non-compaction points (calls 100-150 after a compaction, and mid-cycle) is as high or higher (73.7% and 79.5% of reads), so most of this re-reading is the agent's normal habit, not something compaction creates. Excess over that baseline is ~0.7 re-reads and ~7k tokens per compaction.
3. Sawtooth: a compaction-to-compaction cycle is median 370 calls and 165.1M input; mean ctx per call in the last quarter of a cycle is 4.3x the first quarter's. The last quarter of each cycle (by calls) consumes 40.6% of the cycle's input (the first quarter 9.6%); calls at >=75% of the cycle peak (27.1% of calls) consume 44.0%. That is 35.4% of all main-session input of the study.
4. What-if (compaction at half of the observed pre-compaction ctx, same summary size): input processed falls 45.7% without a re-read penalty and 39.4% with the observed post-compaction re-read burden applied per compaction (39.0% of all-10-session main input); cost-weighted saving 41.9% / 29.0%. Compactions rise from 34 to 82-86 (2.4-2.5x). The saving disappears only if each compaction induced ~2x the gross observed re-read tokens (cost-weighted) - well above the measured excess. Answer-quality losses from more frequent summarisation are not modelled.

## 1. Per-compaction size and cost

Pre = ctx of the last main call before the boundary; post = ctx of the first call after. Prefix = cache_read of that first post call (system prompt + tools, survives compaction in cache). Fresh = post - prefix (summary + re-injected files/attachments, written to cache at 2x). Ratio = pre/post.

| session | n | pre med | pre p90 | post med | post p90 | prefix med | fresh med | ratio med |
|---|---|---|---|---|---|---|---|---|
| S01 | 1 | 783k | 783k | 76k | 76k | 44k | 32k | 10.3x |
| S02 | 3 | 783k | 784k | 70k | 76k | 54k | 23k | 11.3x |
| S03 | 14 | 783k | 784k | 70k | 74k | 37k | 35k | 11.2x |
| S05 | 3 | 783k | 784k | 57k | 61k | 46k | 11k | 13.7x |
| S06 | 1 | 784k | 784k | 59k | 59k | 43k | 16k | 13.3x |
| S09 | 7 | 783k | 784k | 63k | 70k | 43k | 20k | 12.4x |
| S10 | 5 | 783k | 787k | 57k | 60k | 42k | 14k | 13.8x |
| **pooled** | 34 | 783k | 784k | 64k | 75k | 42k | 22k | 12.2x |

Pooled spread: post ctx min-max 53k-77k; compression ratio min-max 10.1x-14.9x. Compression of the non-prefix conversation, (pre - prefix)/fresh: median 34x.

Summary size. The summary text itself survives in the dataset for only 1 of 34 compactions (S01: 18,337 characters, about 5k tokens at 3.5 chars/token; range 4.6-6.1k for 4.0-3.0 chars/token). In that compaction the first post call wrote 31.9k fresh tokens, so the summary is only about 1/6 of the fresh content; the rest is re-injected attachments. For the other 33 compactions the summary text is absent, so only the upper bound (fresh, median 22k) is available; a ~5k-token summary is an extrapolation from one case.

Compaction call itself. Not identifiable as a separate usage record: no assistant line with ctx near the pre-compaction value and summary-sized output sits between the last pre call and the boundary, and the next call already has the reduced ctx. What is observable: the wall-clock gap between the last pre call and the first post call is median 177 s (p90 300 s, max 3008 s; includes any user idle time). Estimate of the hidden call: input ~ pre ctx (783k) + ~5k output, i.e. 26.6M input tokens over 34 compactions = 0.4% of compacting-session input at face value, ~0.3% cost-weighted if it reads the existing cache (0.1x), ~6.7% if it missed the cache entirely (2x). The observed cache-rebuild cost on the first post call is the fresh tokens written at 2x: 1.7M cw over 34 compactions (0.2% of compacting-session cw).

<details><summary>Per-compaction rows (tokens, k)</summary>

| session | # | pre | post | fresh | ratio | gap s |
|---|---|---|---|---|---|---|
| S01 | 1 | 783 | 76 | 31.9 | 10.3 | 3008 |
| S02 | 1 | 781 | 68 | 23.9 | 11.4 | 84 |
| S02 | 2 | 784 | 70 | 15.2 | 11.3 | 94 |
| S02 | 3 | 783 | 77 | 23.0 | 10.1 | 80 |
| S03 | 1 | 756 | 63 | 13.9 | 12.0 | 307 |
| S03 | 2 | 784 | 70 | 20.8 | 11.2 | 123 |
| S03 | 3 | 779 | 56 | 30.1 | 14.0 | 411 |
| S03 | 4 | 781 | 64 | 38.1 | 12.3 | 173 |
| S03 | 5 | 783 | 70 | 34.8 | 11.2 | 127 |
| S03 | 6 | 778 | 63 | 28.2 | 12.3 | 153 |
| S03 | 7 | 783 | 75 | 47.3 | 10.5 | 103 |
| S03 | 8 | 783 | 65 | 27.7 | 12.1 | 95 |
| S03 | 9 | 782 | 72 | 35.4 | 10.8 | 93 |
| S03 | 10 | 778 | 68 | 40.3 | 11.4 | 138 |
| S03 | 11 | 782 | 71 | 34.2 | 10.9 | 114 |
| S03 | 12 | 783 | 74 | 37.2 | 10.5 | 89 |
| S03 | 13 | 784 | 73 | 35.6 | 10.8 | 106 |
| S03 | 14 | 783 | 70 | 32.7 | 11.2 | 87 |
| S05 | 1 | 783 | 56 | 10.4 | 14.0 | 177 |
| S05 | 2 | 784 | 61 | 15.8 | 12.8 | 282 |
| S05 | 3 | 780 | 57 | 11.4 | 13.7 | 178 |
| S06 | 1 | 784 | 59 | 15.7 | 13.3 | 182 |
| S09 | 1 | 773 | 61 | 18.7 | 12.7 | 266 |
| S09 | 2 | 784 | 64 | 21.5 | 12.2 | 227 |
| S09 | 3 | 784 | 77 | 34.7 | 10.1 | 252 |
| S09 | 4 | 781 | 58 | 15.1 | 13.5 | 340 |
| S09 | 5 | 784 | 62 | 19.0 | 12.7 | 187 |
| S09 | 6 | 782 | 64 | 21.7 | 12.1 | 190 |
| S09 | 7 | 783 | 63 | 20.3 | 12.4 | 181 |
| S10 | 1 | 782 | 53 | 11.6 | 14.7 | 218 |
| S10 | 2 | 789 | 53 | 11.1 | 14.9 | 201 |
| S10 | 3 | 783 | 61 | 19.2 | 12.8 | 161 |
| S10 | 4 | 784 | 58 | 16.0 | 13.5 | 191 |
| S10 | 5 | 783 | 57 | 14.3 | 13.8 | 195 |

</details>

## 2. Re-reads after compaction

Method. A read = Read tool call, or a shell command segment using cat, head, tail, sed -n (not -i) or grep/rg with at least one file/dir argument (cd prefixes tracked; arguments with shell variables skipped). Paths normalised and compared in memory only. Re-read = a read in the next 50 main calls after a boundary whose target path (any of them, for multi-path commands) was read earlier in the same session before that boundary (all earlier history, including previous cycles). Result tokens per read = ctx increase to the next call, split among that step's tool results by character share (0.6 tok/char fallback). Issuing-call input = ctx of each distinct call that issued >=1 re-read.

| session | windows | reads | re-reads | re-read share | re-read result tok | issuing calls | issuing-call input |
|---|---|---|---|---|---|---|---|
| S01 | 1 | 17 | 1 | 5.9% | 4k | 1 | 0.2M |
| S02 | 3 | 85 | 36 | 42.4% | 125k | 36 | 4.5M |
| S03 | 14 | 402 | 228 | 56.7% | 512k | 226 | 28.2M |
| S05 | 3 | 79 | 71 | 89.9% | 129k | 70 | 7.6M |
| S06 | 1 | 27 | 4 | 14.8% | 10k | 4 | 0.4M |
| S09 | 7 | 177 | 151 | 85.3% | 183k | 143 | 13.4M |
| S10 | 5 | 136 | 115 | 84.6% | 159k | 106 | 9.5M |
| **pooled** | 34 | 923 | 606 | 65.7% | 1.1M | 586 | 63.7M |

- Post-compaction windows: 1700 calls, 196.7M input. Reads per call 0.54; re-reads per call 0.356. Re-read tokens are 73.9% of all read-result tokens in the windows (1.5M).
- Distinct re-read paths: 352 (about 10 per compaction); per compaction 17.2 issuing calls and 33k result tokens.
- Input of the issuing calls: 63.7M = 32.4% of window input, 1.0% of compacting-session input (cw: 9.1M). These are upper bounds on the added cost (a call may also have done other work).
- Carry cost: the 1.1M re-read result tokens stay in context until the next compaction (no non-compaction ctx drops exist in the data); tokens x remaining calls in the cycle = 436.9M input = 6.7% of compacting-session input. Gross, not excess (see control).
- Sensitivity: of the 606 re-reads, 599 target files the agent had not Edit/Write-n since the last read, so file changes by the Edit/Write tools do not explain them (changes made through shell commands are invisible).

Control (same definition, windows of 50 calls that start 100 calls after a compaction, or at mid-cycle; prior-read set = all earlier history of the session):

| window | n windows | reads/call | re-reads/call | re-read share | re-read tok/call |
|---|---|---|---|---|---|
| first 50 after compaction | 34 | 0.54 | 0.356 | 65.7% | 660 |
| calls 100-150 after compaction | 32 | 0.47 | 0.349 | 73.7% | 545 |
| mid-cycle | 29 | 0.42 | 0.335 | 79.5% | 508 |

Excess attributable to compaction = (post rate - control rate) x 50 calls = 0.7 re-reads and 6.6k tokens per compaction, against gross 17.8 re-reads and 33k tokens. Reads per call are higher just after compaction (0.54 vs 0.45), but the re-read share is lower: the agent re-reads files constantly (a mid-cycle read is ~80% likely to repeat an earlier path), so compaction mostly adds new-file orientation reads rather than re-reads. Caveat: the control history set is larger, which biases control shares upward.

## 3. Sawtooth economics

A cycle = calls from one boundary (or session start) to the next. 34 cycles end in a compaction: 27 strictly compaction-to-compaction plus 7 from session start. Open tails after the last compaction (7 sessions) are excluded from cycle statistics but are in the totals. Quarters are by call count; 'top' = calls at >=75% of the cycle's peak ctx.

| session | cycles | calls/cycle med | input/cycle med | mean ctx/call first Q | last Q | last/first | last-Q input share | top-ctx input share |
|---|---|---|---|---|---|---|---|---|
| S01 | 1 | 295 | 146.3M | 185k | 732k | 4.0x | 36.5% | 62.3% |
| S02 | 3 | 345 | 167.5M | 189k | 707k | 3.7x | 38.2% | 49.0% |
| S03 | 14 | 328 | 136.8M | 165k | 694k | 4.2x | 40.0% | 45.6% |
| S05 | 3 | 448 | 188.2M | 180k | 676k | 3.8x | 40.3% | 38.5% |
| S06 | 1 | 338 | 146.0M | 157k | 706k | 4.5x | 40.6% | 51.3% |
| S09 | 7 | 522 | 210.0M | 154k | 688k | 4.5x | 41.4% | 43.7% |
| S10 | 5 | 500 | 207.9M | 145k | 672k | 4.6x | 42.5% | 38.6% |
| **pooled (34)** | 34 | 370 | 165.1M | 162k | 688k | 4.2x | 40.6% | 44.0% |
| pooled, 27 strict cycles | 27 | 389 | 167.5M | 161k | 690k | 4.3x | 40.8% | 44.0% |

Per-cycle distributions (n=34): calls 370 median (p90 579, range 210-606); input 165.1M median (p90 230.1M); last/first-quarter mean ctx ratio 4.3x (range 3.3-5.5); last-quarter input share 40.4% (p90 43.2%); top-ctx share 44.7%.
Cost-weighted: last quarter of cycles = 40.2% of cycle cw (first quarter 10.1%), a bit lower than the raw share because early calls pay for cache writes. The 34 cycles hold 87.1% of all main-session input; the last quarters alone hold 35.4% (2.33B).

## 4. What-if: compaction at half the observed pre-compaction ctx

Method. For each of the 7 compacting sessions, replay the observed per-call context growth (ctx_i - ctx_{i-1}); keep the same call sequence. Trigger = 0.5 x the pre-compaction ctx of the observed cycle (session median for the open tail), at least 1.25 x post; on trigger ctx resets to the observed post-compaction ctx of the preceding compaction (same summary size). Observed boundary jumps are removed from the growth series. Scenario A: no re-read penalty. Scenario B: remove the observed post-compaction re-read growth from the series (no double counting) and add, per what-if compaction, the pooled gross re-read burden of section 2 (17.2 extra calls and 33k carried result tokens). Cost-weighted uses 0.1x reads, 2.0x cache writes with the post-compaction fresh part rewritten; the model reproduces observed cw within 5-13% per session (it ignores TTL misses). Baseline = same model on observed ctx. Compaction-call input (hidden) is shown separately.

| scenario | compactions (obs 34) | input processed | vs baseline | cw | vs baseline | % of all-10 main input |
|---|---|---|---|---|---|---|
| baseline (observed, 7 sessions) | 34 | 6.52B | - | 707.8M | - | - |
| A: half trigger, no re-read penalty | 82 | 3.54B | -45.7% | 410.9M | -41.9% | -45.3% |
| B: half trigger + observed gross re-read burden | 86 | 3.95B | -39.4% | 502.3M | -29.0% | -39.0% |
| extra: quarter trigger, no penalty | 206 | 2.04B | -68.7% | 265.2M | -62.5% | -68.1% |

Including the hidden compaction calls (input = ctx at trigger, in both baseline and what-if):

| scenario | raw saving | cw saving, cached compaction (0.1x) | cw saving, uncached compaction (2x) |
|---|---|---|---|
| A | -45.5% | -41.7% | -37.6% |
| B | -39.1% | -28.8% | -25.2% |

Per session, scenario A / B raw saving: S01 46.7%/42.4%; S02 49.3%/42.7%; S03 47.6%/40.3%; S05 45.1%/39.4%; S06 42.3%/32.3%; S09 44.1%/38.8%; S10 43.7%/37.4%.

Penalty scan (no subtraction, penalty = m x gross burden): m=0.0: raw -45.7%, cw -41.9%; m=1.0: raw -39.6%, cw -28.6%; m=1.5: raw -36.2%, cw -15.3%; m=2.0: raw -32.3%, cw +3.5%; m=3.0: raw -23.7%, cw +61.4%; m=4.0: raw -11.8%, cw +158.1%. Break-even is near m=2 for cost-weighted input (about 66k re-read tokens and 34 extra calls per compaction) and m~5 for raw tokens; the measured excess is only ~0.2x the gross burden.

## Caveats

- Compaction fires at ~783k ctx, so the pre/post statistics describe one threshold; 'median vs p90' differ by <0.2%. The result transfers only to this auto-compact setting (1M-class window).
- The summary text is present for 1 of 34 compactions; the summary size elsewhere is bounded by the fresh part of the first post call, which includes re-injected attachments. Token counts of text are estimates (3.5 chars/token); all other token figures are API usage values.
- The compaction call is not in the transcripts as a usage record; its cost is estimated, and could be ~10x larger in cost-weighted terms if it does not hit the prompt cache. Output token values in the usage records are streaming snapshots and unusable.
- Re-read detection is syntactic (cat/head/tail/sed -n/grep/Read with resolvable paths; exact-path match; python or other readers are missed; directory greps count as targets). Per-read tokens are an allocation of step-level ctx growth, not a direct measure.
- Gross post-compaction re-reads are not evidence of compaction-induced loss: the control shows the agent re-reads at the same or higher rate at other times. The what-if charges the gross burden (conservative); the excess-only variant is close to scenario A.
- The what-if keeps the call sequence and growth fixed, ignores cache-TTL misses, quality loss from more frequent/lossy summaries (82-86 vs 34 summaries, each generation ~3 minutes of wall clock), and the extra wall time. Sessions without compaction (S04, S07, S08; peak ctx <=343k) are unaffected by the 50% rule only because their pre-compaction ctx is not observed; a half-of-783k trigger (392k) would not have fired in them.
- Cycles are counted per main-session call; sub-agent (sidechain) calls are excluded throughout, so their input is not in any denominator.
