> Working memo from cycle A5 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# A5: does lexical "reuse" measure need? The 34 real compactions as a natural experiment

Aggregates only (no text, paths or commands were printed or stored; paths and commands compared in memory / by hash). 10 main sessions, 16,181 calls; 34 compactions in 7 sessions (S01 1, S02 3, S03 14, S05 3, S06 1, S09 7, S10 5). Scripts are kept with the analysis files.

## Method
- Segments: `bound.read_trace_lines` + `calibrate`. Pre-compaction segments of compaction c = non-"unattributed" segments with birth in [previous compaction, c) (bound's own residency window, so they all end at c). Median 917 segments / 474k calibrated tokens per compaction = 61% of the 783k pre-compaction context; the rest (thinking, images, harness framing) is unattributed and invisible to any lexical measure.
- Lexical demand after: segment is "demanded" if its distinctive tokens (`bound.TOKEN_RE`, minus the session's common tokens, same rule as `link`) reappear in the outputs (assistant text + tool-input JSON) of the next N = 50 / 200 calls. min_shared m = 1, 3, 5: some single call's output shares >= m tokens (link's per-call rule). Coverage rule: union of shared tokens over the window >= 20% of the segment's distinctive tokens. 200-call windows truncated by session end in 2 of 34 compactions (mean window 195).
- Behavioural recovery after: in the same N calls, tool calls whose target was in the pre-compaction cycle: file re-reads (Read tool, or cat/head/tail/sed -n/grep with a file argument; D2's parser) compared by normalised path; command re-runs (Bash without read target, Grep/Glob) compared by SHA-1 of the whitespace-normalised command. Tokens = calibrated size of the re-run's tool result (results without text, i.e. images, count 0: 0.2-0.5 per compaction). "Gross" = every hit; "distinct" = first re-obtaining of each path/command in the window (one re-add per item, the analogue of A4's one-time charge). Primary source set = paths/commands used since the previous compaction (what the pre-compaction segments contained); variant "all history" = anywhere earlier in the session (D2's convention; differs by <10%).
- Harness-restored: first post call's input minus its cache_read (summary + re-injected files; D2's "fresh"). The summary text itself exists for 1 of 34 compactions (S01; about 10k calibrated tokens, of 31.9k fresh).
- Controls: (i) behavioural recovery in windows that do not follow a compaction (mid-cycle and the last N calls of a cycle; sources = cycle so far), same definitions; (ii) a lexical placebo: the real pre-compaction segments scored against the outputs after a different compaction (same session, other cycle: n = 90; other session: n = 102; 3 random partners each); (iii) "unmet" demand: demand left after removing tokens already present in any post-compaction external context (tool results, prompts, harness, summary where present).
- Trouble proxies: is_error rate of tool results issued in 50 / 200 calls before vs after; steps of the instruction spanning the compaction (bound's `instruction_starts`) against the session median, against the length-biased distribution, and against instructions covering calls 75 / 150 calls earlier or later.
- Restart rescale: A4's segment replay (no-policy replay reproduces measured input exactly; r = 1 reproduces A4's 26.7 / 40.9 / 45.7% and 3.7 / 20.2 / 30.4%), with the re-added reused segments replaced by one block of r x R_b tokens priced as fresh (2.0), 10k summary.

## 1. Lexical demand after (mean per compaction)
| setting | N = 50: k tokens (% of visible) | N = 200: k tokens (% of visible) |
|---|---|---|
| min_shared 1 | 394 (82.9%) | 448 (94.2%) |
| min_shared 3 | 208 (43.7%) | 322 (67.7%) |
| min_shared 5 | 137 (28.8%) | 246 (51.8%) |
| coverage >= 20% | 52 (10.8%) | 254 (53.5%) |

At min_shared 1 nearly every kind of segment is "demanded" (71-99% of each kind: tool inputs 83%, tool results 78%, writes 92%, assistant text 84%, harness 99%, prompts 71%), so the measure does not discriminate. Composition of the N=50, m=1 demand: tool inputs 38.9%, tool results 35.5%, own writes 14.5%, assistant text 5.6%, harness 4.3%, prompts 1.3%.

## 2. Behavioural recovery after (mean per compaction)
| | N = 50 | N = 200 |
|---|---|---|
| file re-reads, gross (count / k tokens) | 17.3 / 21.2 | 58.4 / 57.8 |
| file re-reads, distinct paths (count / k tokens) | 7.0 / 10.2 | 16.0 / 20.6 |
| command re-runs (exact signature), count | 0.1 | 0.4 |
| same, all-history sources: gross / distinct k tokens | 22.0 / 11.1 | 61.9 / 23.9 |
| harness-restored (summary + re-injected), k tokens | median 21.6, mean 24.3 | |

Excess over the agent's habit (same definitions, mid-cycle windows): N=50 distinct 10.2k vs 3.4k (excess 6.7k), gross 21.2k vs 7.7k (13.5k); N=200 distinct 20.6k vs 4.6k (16.0k), gross 57.8k vs 32.6k (25.3k). The N=50 excess of 6.7k matches D2's 6.6k per compaction. Of the lexically demanded tool-result tokens, only 30% (N=50) / 46% (N=200) have their source path or command re-obtained in the window, i.e. 10.7% / 16.8% of all demanded tokens.

## 3. Ratio behavioural recovery / lexical demand
Pooled (sum / sum), cycle sources. Per-compaction median in brackets for the distinct N=50 row.
| recovery | N | m = 1 | m = 3 | m = 5 | coverage 20% |
|---|---|---|---|---|---|
| distinct | 50 | 0.026 [0.017] | 0.049 [0.042] | 0.074 [0.063] | 0.197 [0.227] |
| distinct | 200 | 0.046 | 0.064 | 0.084 | 0.081 |
| gross | 50 | 0.054 | 0.102 | 0.155 | 0.411 |
| gross | 200 | 0.129 | 0.180 | 0.235 | 0.227 |
| distinct + harness-restored | 50 | 0.087 | 0.166 | 0.252 | 0.668 |
| distinct + harness-restored | 200 | 0.100 | 0.140 | 0.182 | 0.177 |

Per compaction (distinct, N=50): ratio < 0.25 in 34/34 (m=1), 34/34 (m=3), 32/34 (m=5), 17/34 (coverage). Gross N=200: < 0.25 in 34 / 28 / 16 / 20 of 34. No compaction reaches a ratio of 1 at m = 1. All-history sources change ratios by < 10%. Per session (distinct, N=50, m=1): 0.003 (S01) to 0.056 (S02). Mid-cycle controls give a lower ratio still (distinct N=50 m=1: 0.018), so compaction does raise recovery (about 3x in tokens), but from a very small base.

Placebo (real pre-compaction segments vs outputs after a different compaction), placebo / real demand:
| setting | same session N=50 | N=200 | other session N=50 | N=200 |
|---|---|---|---|---|
| m = 1 | 0.95 | 0.99 | 0.72 | 0.87 |
| m = 3 | 0.81 | 0.94 | 0.39 | 0.49 |
| m = 5 | 0.78 | 0.88 | 0.33 | 0.38 |
| coverage 20% | 0.58 | 0.72 | 0.15 | 0.18 |

Ratio against placebo-adjusted demand (real minus placebo; distinct / gross): other-session placebo, N=50: m1 0.09 / 0.19, m3 0.08 / 0.17, m5 0.11 / 0.23, coverage 0.23 / 0.48; N=200: m1 0.36 / 1.00, m3 0.13 / 0.35, m5 0.14 / 0.38, coverage 0.10 / 0.28. Same-session placebo leaves so little net demand at m=1 (4-18k) that the ratio is unstable (0.56 to > 1); at coverage 20%: 0.45 / 0.97 (N=50), 0.28 / 0.81 (N=200). Unmet demand (tokens not already in post-compaction external context): N=50 m1 313k (79% of lexical), m3 95k (45%), m5 53k (39%); recovery / unmet distinct 0.03 / 0.11 / 0.19. For S01, where the summary text exists, summary vocabulary plus new context explains only 9% of the m=1 demand (429k to 391k).

## 4. Did work go wrong after compaction?
| proxy | before | after | control / note |
|---|---|---|---|
| error-result rate, 50 calls (pooled) | 1.7% (27/1613) | 2.0% (36/1775) | per compaction up 14, down 11, tie 9; mean diff +0.27 pt (se 0.45); pseudo-boundaries inside cycles: mean diff +0.16 pt (n = 115, sd 3.4 pt) |
| error-result rate, 200 calls | 1.8% (117/6620) | 1.8% (123/6660) | up 19, down 15 |
| steps of instruction spanning c (29 of 34 compactions lie inside an instruction) | median 65 vs session median 15 (x5.6) | | length-biased control 1.28x (17/29 above); instructions covering c-150 / c-75: median 41 / 38 vs 42 at c (longer at c in 21/34 and 23/34, shorter in 13 and 11) |

The compaction sits early in its instruction (median 6 steps in, 36 remaining; 15 in at c-75). Proxies show no detectable damage, but they are weak: an omitted decision or constraint shows up as neither an error result nor a longer instruction unless it causes visible failure, and 34 events from 7 sessions of one user give little power (an error-rate rise of about 1 pt would not be detected).

## 5. Implication: A4's restart estimate rescaled
Assumption: at a restart the agent re-obtains a fraction r of the lexically "reused" tokens R_b (same r as after real compactions, windows of 50-200 calls), at the size R_b would have been charged, priced as fresh tokens; 10k summary as in A4; A4's boundary classes (clean / light) still use unscaled R_b. Segment replay, all boundaries above 200k context, % of measured input (price-weighted in brackets):
| rule, detector | r = 1 (A4) | 0.5 | 0.25 | 0.13 | 0.05 | 0.026 | 0 (no charge) |
|---|---|---|---|---|---|---|---|
| every boundary, refs >= 1 | 26.7 (12.1) | 43.0 (31.3) | 49.0 (42.1) | 52.4 (46.8) | 54.1 (49.1) | 54.3 (49.5) | 55.0 (50.3) |
| every boundary, refs >= 3 | 40.9 (30.1) | 49.0 (41.3) | 52.4 (46.5) | 54.0 (48.8) | 54.5 (49.7) | 54.4 (49.6) | 55.0 (50.3) |
| every boundary, refs >= 5 | 45.7 (37.1) | 51.1 (44.5) | 53.5 (48.0) | 53.9 (48.9) | 54.4 (49.6) | 54.6 (49.9) | 55.0 (50.3) |
| clean + light, refs >= 1 | 3.7 (3.2) | 4.6 (4.1) | 5.1 (4.6) | 5.3 (4.8) | 5.4 (4.9) | 5.4 (4.9) | 5.5 (5.0) |
| clean + light, refs >= 3 | 20.2 (17.9) | 21.7 (19.6) | 22.2 (20.2) | 21.0 (19.1) | 21.3 (19.5) | 21.4 (19.6) | 21.5 (19.7) |
| clean + light, refs >= 5 | 30.4 (27.3) | 31.7 (28.8) | 31.5 (28.6) | 31.8 (29.0) | 31.9 (29.2) | 32.0 (29.3) | 32.1 (29.4) |

Observed r, matched detector: refs >= 1 uses r 0.026 (distinct, N=50) to 0.129 (gross, N=200): restarting at every boundary above 200k saves 52.4-54.3% of input (46.8-49.5% price) instead of 26.7% (12.1%); refs >= 3 (r 0.049-0.18): 53.4-54.5% (47.9-49.7%) instead of 40.9% (30.1%); refs >= 5 (r 0.074-0.235): 53.6-54.6% (48.0-49.7%) instead of 45.7% (37.1%). So the charge is no longer what limits the rule: the savings approach A4's unrestricted ceiling (55.0% input, 50.3% price) and the question moves to restart quality. If lexical demand is itself half placebo and recovery were 0.5 of the net (worst plausible r = 0.5 under m = 1), the saving is 43.0% (31.3%). The "clean + light" rules gain little (they restart at only 19-92 boundaries), so most of the gain comes from allowing heavy boundaries.
Absolute-charge cross-check (every boundary, independent of the detector): 10k summary + 10k / 21k / 58k restored (observed distinct N=50 / distinct N=200 / gross N=200): 53.8% (48.8%) / 53.4% (47.9%) / 47.8% (40.3%); with the observed 22k summary-plus-re-injection and +0 / +10k / +21k restored: 53.2% (48.2%) / 53.3% (47.7%) / 51.8% (45.8%).

## Caveats
- The lexical measure is unvalidated against need in both directions; so is the behavioural one. Behavioural recovery is a lower bound on what the agent needed: it misses content carried by the summary itself, content restored by the harness (about 22k, counted separately), re-obtaining by other routes (different command text, python readers, git, Grep tool on directories), content the agent got by reading again under a different path or by inference, and anything it silently went without. Command re-runs need an exact match and so are almost never found (0.1-0.4 per compaction); this understates re-runs of near-identical commands.
- Lexical demand is an upper bound dominated by shared vocabulary: the placebo reaches 95-99% (same session) / 72-87% (other session) of the m = 1 demand, and 58-72% / 15-18% of the coverage demand. Tokens that recur are project vocabulary, not evidence that the specific segment was needed. Same-session placebo also contains legitimate cross-cycle reuse, so it over-corrects; other-session placebo may under-correct (same user, overlapping projects).
- 34 compactions, one user, one auto-compact threshold (783k); S03 contributes 14. Sessions are not independent; bootstrap intervals were not computed.
- Compaction happens at a fixed context, not an instruction boundary, and the agent sees a Claude-written summary of unknown quality (text available for 1 of 34); a restart policy at an instruction boundary has a different summary and a different in-flight state. 144-216 restarts replace 34 compactions, so any per-restart quality loss compounds; not modelled, nor is summary-generation cost.
- Image reads (zero tokens in the text measure) are 0.2-0.5 per compaction; thinking and harness overhead (39% of pre-compaction context) are invisible to both measures.
- Trouble proxies are weak (see section 4); the instruction-length comparison is confounded by length bias and by the compaction's early position within its instruction.
- Token sizes are calibrated estimates (bound's factor), not API values; D2's token numbers were allocated from per-step growth and are larger for ordinary reads (D2 control about 25k per 50 calls vs 7.7k here), but the excess agrees.

## Findings
1. By lexical reuse (m = 1) 83-94% of the 474k visible pre-compaction tokens would have counted as needed after a compaction, yet the agent actually re-obtained only 10-21k distinct tokens (21-58k gross) of it: a ratio of 0.03-0.13 at m = 1, 0.05-0.18 at m = 3, 0.07-0.24 at m = 5, 0.08-0.41 with the 20% coverage rule; 34/34 compactions are below 0.25 at m = 1, 3.
2. Lexical reuse mostly counts shared vocabulary rather than need: the same segments score 95-99% (same session) or 72-87% (other session) of their m = 1 "demand" against the outputs of an unrelated compaction window, and only 11-17% of demanded tokens have their source re-fetched.
3. Behavioural recovery is the more credible measure of "what a summary must carry" (about 22k restored by the harness plus 10-21k distinct re-fetched, total roughly 30-45k per compaction), but as a lower bound; the truth lies between the 0.03-0.13 raw ratio and about 0.1-0.5 after placebo adjustment, and 1.0 is excluded.
4. No detectable damage: error-result rate 1.7% to 2.0% over 50 calls (control drift +0.16 pt), spanning instructions about as long as instructions at the same context 75-150 calls earlier (42 vs 38-41 steps), though the proxies could not see subtler loss.
5. Rescaling A4's restart charge by the observed ratio lifts the every-boundary restart rule from 26.7 / 40.9 / 45.7% input (12.1 / 30.1 / 37.1% price) to 52-55% (47-50% price) for refs >= 1 / 3 / 5, close to the no-charge ceiling of 55.0% / 50.3%; at r = 0.5 it is still 43% (31%). The remaining uncertainty is restart quality, not recovery cost.
