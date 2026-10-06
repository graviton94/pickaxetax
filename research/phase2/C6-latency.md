> Working memo from cycle C6 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts and event pages at the dataset-v2 snapshots.

# C6: Does a large context also cost time? (aggregate numbers only)

Main-session calls of the 10 dataset-v2 sessions, read at the dataset-v2 snapshots (16,181 calls; the per-call contexts equal the public series exactly in every session). No transcript text, paths or commands are reproduced.

## Findings
1. **Latency grows with context, but slowly.** Each 100k tokens of context adds about **0.37 s** to a call. This is a pooled median regression controlling for output size and uncached tokens, with a 90% block-bootstrap interval of 0.29–0.43 s. Inside the sawtooth itself, where the context falls from 746k to 106k within seconds at a compaction, the drop is **0.19 s per 100k** (interval 0.15–0.36). There, 30 of 33 compactions are faster afterwards (sign test p = 1e-6). The cost sits in the time to first token. Time per output token does not change with context (interaction ≈ 0).
2. **Context is a small part of model time.** Main-session model time is 61 h (13.6 s per call). The context term accounts for about 3.5–6.8 h of it (6–11%), or about 0.8–1.5 s of a call that carries the average 407k.
3. **A compaction takes 130 s** (median; p10–p90 76–192 s, n = 33, measured directly from harness status events). That is about 10 ordinary calls. It is 89 s on opus-5.5 and 177 s on opus-5. D2's 177 s gap included the call that followed.
4. **The token levers do not buy time, except the restart.** A ceiling of 200k saves 4.6 h of call time but adds 178 compactions (+6.5 h): **net +1.9 h slower** (+0.4 s per call; range −0.5 to +4.5 h across slopes). A ceiling of 390k is about neutral (−1.0 h; −2.6 to +0.7). A **restart above 200k** saves **4.9 h (8%; 3.1–6.8 h)** if it costs no summary generation, and about 0 (+0.4 h) if every one of its 146 restarts generates a summary as long as a compaction.
5. **Break-even.** A 200k ceiling saves time only if a compaction at 200k took under 92 s (47 s at the natural-experiment slope), against the 130 s measured at 783k. Time is therefore at best a side benefit of the levers, not a reason for them. The faster model (opus-5.5) has both the smaller context slope (0.16 against 0.46 s/100k) and the shorter compactions.

## 1. What the timestamps are
| source | sessions | line timestamps | extra timing fields |
|---|---|---|---|
| local transcript | S01 | client time of each line (ms). An assistant message is written as 1–3 lines, one per content block, each stamped when that block finishes. Median span from first to last line 3.0 s. | `thinkingDurationMs` on the thinking lines (285 main calls); per-turn totals on 35 system lines |
| event-API pages | S02–S10 | inner line timestamp (client, ms) for all assistant and most user lines, plus `created_at` (server) on every event. `created_at` − inner = 0.1–0.4 s median. Lines per message as in S01. | **harness `status` events**: `requesting` exactly once before each main call (n_req = 1 for 99.9% of calls) and `compacting` every 30 s during a compaction, followed by a null status and the compact boundary |

Latency measures:
- **Last-line latency** (the model time of a call): from the request start to the last streamed line of the message. The request start is the server `created_at` of `requesting` in S02–S10, and the last tool result's client time in S01.
- **First-line latency**: the same start to the first line. This is time to first token plus the streaming of the first block, which is the whole thinking block when thinking comes first.
- **Time to first token**: first-line latency minus `thinkingDurationMs`, in S01 only.
- **Clock check** (S02–S10 clean calls): the client-clock latency (tool result → line) and the server-clock latency (`requesting` → line) differ by 0.03–0.17 s at the median. `requesting` follows the last tool result by 0.02–0.11 s.
- **Compaction calls**: the `requesting` before a compaction belongs to the call after it. Its latency is measured from the compact boundary. The compaction itself runs from the first `compacting` event to the boundary.

## 2. Usable calls
**Clean** means a call triggered by tool results:
- the previous main call's tool calls were all answered;
- it was a single tool call;
- no user prompt, compaction, sub-agent line or interleaved message came in between;
- the latency is between 0 and 1,800 s.

"Loose" also admits parallel tool results and sub-agent interleaving.

| session | main calls | clean (strict) | clean (loose) | user prompt | compaction | parallel | sub-agent | other excluded | first-line s p50 | last-line s p50 / p90 |
|---|---|---|---|---|---|---|---|---|---|---|
| S01 | 400 | 314 | 368 | 31 | 1 | 52 | 2 | 0 | 5.5 | 9.9 / 39.8 |
| S02 | 1303 | 1052 | 1147 | 59 | 3 | 76 | 19 | 94 | 3.7 | 5.8 / 18.6 |
| S03 | 4820 | 3810 | 4134 | 398 | 14 | 266 | 58 | 274 | 4.4 | 6.7 / 25.4 |
| S04 | 166 | 143 | 153 | 12 | 0 | 10 | 0 | 1 | 5.0 | 10.7 / 34.7 |
| S05 | 1923 | 1788 | 1804 | 113 | 3 | 16 | 0 | 3 | 7.4 | 9.4 / 32.6 |
| S06 | 464 | 393 | 421 | 38 | 1 | 28 | 0 | 4 | 8.1 | 10.7 / 31.7 |
| S07 | 66 | 57 | 62 | 4 | 0 | 5 | 0 | 0 | 5.8 | 10.9 / 37.5 |
| S08 | 105 | 77 | 98 | 6 | 0 | 21 | 0 | 1 | 10.0 | 12.9 / 33.3 |
| S09 | 4056 | 3644 | 3859 | 159 | 7 | 38 | 177 | 31 | 6.5 | 8.8 / 28.5 |
| S10 | 2878 | 2608 | 2719 | 126 | 5 | 111 | 0 | 28 | 6.4 | 8.4 / 27.8 |
| **all** | 16181 | **13886** | 14765 | 946 | 34 | 623 | 256 | 436 | | |

"Other excluded" is mostly calls whose previous tool call had no recorded result before the call (S02/S03), plus 13 without a usable time.

## 3. Latency by context (pooled clean calls, medians)
- **Output** is estimated as in C5: the larger of the recorded output and 1.96–2.05 × the visible output plus 0.179 × thinking-signature characters. S01 uses its real counts.
- **New** = uncached input plus cache write.
- Every row of the four right-hand columns has new < 20k.

| ctx bin | all calls: n / last-line s / out est | output < 150 tok: n / last-line s | output 150–600: last-line s / first-line s | output ≥ 600: last-line s / s per 1k out |
|---|---|---|---|---|
| 50–100k | 652 / 5.1 / 285 | 198 / 2.8 | 5.1 / 4.1 | 18.1 / 14.3 |
| 150–200k | 1125 / 6.5 / 340 | 337 / 3.4 | 6.0 / 4.9 | 17.2 / 13.9 |
| 250–300k | 1094 / 7.1 / 384 | 309 / 3.8 | 6.3 / 5.3 | 18.0 / 12.9 |
| 350–400k | 927 / 7.9 / 436 | 271 / 4.3 | 6.4 / 5.5 | 19.3 / 13.9 |
| 450–500k | 954 / 8.4 / 446 | 290 / 4.6 | 6.5 / 5.8 | 20.3 / 14.7 |
| 550–600k | 851 / 9.9 / 528 | 213 / 4.9 | 7.3 / 6.3 | 19.7 / 15.1 |
| 650–700k | 893 / 10.7 / 573 | 225 / 5.2 | 6.9 / 6.1 | 21.7 / 15.5 |
| 750–800k | 500 / 10.7 / 576 | 140 / 5.3 | 8.1 / 7.1 | 19.3 / 14.9 |

(Calls at large contexts also write more: the median estimated output rises from 285 to 576 tokens, which is the confound the output control removes.)

## 4. Fits (last-line latency in s; ctx per 100k, out per 1k, new per 10k)
- **TS** = Theil–Sen on context, no controls.
- **TS small** = Theil–Sen on calls with output < 150 and new < 20k.
- **LAD** = median regression (IRLS). LAD1: T ~ 1 + ctx + out + new. LAD2 adds an out × ctx term.

| session | n | TS | TS small (n) | LAD1 ctx | LAD1 out | LAD1 new | LAD2 ctx | LAD2 out×ctx |
|---|---|---|---|---|---|---|---|---|
| S01 | 314 | −0.67 | 0.14 (27) | 0.27 | 8.8 | 1.00 | 0.35 | −0.11 |
| S02 | 1052 | 0.07 | 0.06 (240) | 0.04 | 7.3 | 0.02 | 0.09 | −0.10 |
| S03 | 3810 | 0.42 | 0.18 (628) | 0.19 | 7.6 | 1.69 | 0.19 | −0.01 |
| S04 | 143 | 0.77 | −0.18 (24) | 0.18 | 10.4 | 0.28 | 0.02 | 0.08 |
| S05 | 1788 | 0.97 | 0.50 (627) | 0.45 | 13.8 | 1.83 | 0.54 | −0.25 |
| S06 | 393 | 0.92 | 0.97 (106) | 0.89 | 11.6 | 1.47 | 0.81 | 0.21 |
| S07 | 57 | 2.49 | – (12) | 1.03 | 15.6 | 0.45 | 0.47 | 1.65 |
| S08 | 77 | −0.63 | – (16) | −1.28 | 15.8 | 0.28 | 1.06 | −5.47 |
| S09 | 3644 | 0.74 | 0.41 (1287) | 0.41 | 14.0 | 0.24 | 0.38 | 0.11 |
| S10 | 2608 | 0.93 | 0.44 (869) | 0.46 | 12.2 | 0.27 | 0.52 | −0.13 |
| **pooled** | 13886 | 0.56 | 0.35 (3836) | **0.36** | 10.0 | 0.21 | **0.37** | −0.04 |

Pooled 90% intervals, from 40 bootstrap resamples of 100-call blocks:
- LAD1 ctx 0.17–0.46, out 9.0–10.7, new −0.02–0.26;
- LAD2 ctx 0.29–0.43, out × ctx −0.40–0.19;
- TS small 0.29–0.40.

The context coefficient is positive in every session with more than 300 clean calls (0.04–0.89). S04, S07 and S08 are too small to read.

**Time to first token.**
- S01 (first line minus thinking duration, n = 225): median 2.25 s, Theil–Sen 1.24 + 0.22 s per 100k. By bin: 1.4 s below 150k and 2.6 s above 450k.
- S02–S10 calls whose first block is a tool call, with no thinking and output < 150 (n = 3,350): first line 2.7 s at 0–100k and 5.3 s at 700–800k, Theil–Sen 0.38 s per 100k.

So the context cost is a prefill and attention cost at the start of the response. It does not slow token generation.

**Confound checks.**
- **Natural experiment.** Take the 33 compactions with at least 10 clean calls in the 40 calls before and the 40 calls after. Same task, model, hour and server conditions; the median context goes from 746k to 106k. The output-adjusted latency is 1.15 s lower after (raw 3.86 s, first line 2.65 s). It is lower in 30 of 33 compactions, sign test p = 1.4e-6. The implied slope is 0.19 s per 100k (IQR 0.09–0.51; bootstrap 90% interval 0.15–0.36).
- **Time of day.** The LAD1 context slope by UTC 6-hour bin is 0.43, 0.22, 0.48 and 0.36. It is positive in every bin.
- **Model.** opus-5: 0.46 s/100k and 13.3 s per 1k output. opus-5.5: 0.16 s/100k and 7.7 s per 1k output. fable-5: n = 119, unstable.

## 5. Compaction duration (first `compacting` status → compact boundary)
| session | n | median s (min–max) |
|---|---|---|
| S02 | 3 | 77 (76–89) |
| S03 | 14 | 95 (73–130) |
| S05 | 3 | 153 (141–257) |
| S06 | 1 | 162 |
| S09 | 7 | 178 (159–228) |
| S10 | 5 | 182 (143–194) |
| **pooled** | 33 | **130** (p10 76, p90 192; mean 135; total 1.23 h) |

- The compaction starts at the same instant as the `requesting` of the call that triggered it. That call then answers 4.8 s (median) after the boundary.
- S01 has no status events.
- Duration hardly tracks the size of the restored content: Spearman −0.37 (opus-5.5) and +0.27 (opus-5).
- All 33 compactions happen at about 783k, so how the duration would change at a 200k ceiling cannot be observed.

## 6. Model time under the levers
**Method.**
- Replayed per-call contexts come from line-by-line copies of `whatif.cap` (ceilings 200k / 390k, `COMPACTION_PREFIX` 42k + `POST_COMPACTION_NEW` 22k) and `whatif.restart` (above 200k, 10k summary). Their input totals and restart and compaction counts are asserted equal to whatif's.
- Δ time is the sum of four parts:
  - slope × Σ(replayed − observed context);
  - prefill of the new content: β_new = 0.21 s per 10k, applied to 22k per compaction and to base + 10k per restart;
  - compaction time: each replay compaction costs the session's measured median duration, minus slope × (783k − ceiling); each removed observed compaction is credited at the observed duration;
  - for the restart only, optionally one compaction-length summary generation per restart.
- Observed model time is 61.1 h of calls plus 1.23 h of compactions. It is measured for every S02–S10 call and imputed at the median for S01's non-clean calls.

| slope used (s/100k) | ceiling 200k: Δ ctx h / Δ comp. h / **net h** | ceiling 390k: net h | restart >200k: net h, no summary time / with |
|---|---|---|---|
| natural experiment (0.19) | −2.33 / +6.52 / **+4.21** | +0.50 | **−3.07** / +2.21 |
| per model group (0.16 / 0.46) | −4.02 / +6.48 / **+2.48** | −0.60 | **−4.37** / +0.91 |
| pooled LAD2 (0.37), primary | −4.56 / +6.46 / **+1.92** | −1.00 | **−4.89** / +0.39 |
| per-session LAD1 | −4.01 / +6.48 / **+2.49** | −0.58 | **−4.38** / +0.90 |
| LAD1 low bound (0.17) | −2.08 / +6.53 / **+4.47** | +0.67 | **−2.86** / +2.42 |
| raw Theil–Sen, no output control (0.56) | −6.93 / +6.39 / **−0.52** | −2.59 | **−6.83** / −1.55 |

- **Counts:** +178 compactions at ceiling 200k, +55 at 390k; at the restart, 146 restarts and 33 fewer compactions.
- **Primary, per call:** ceiling 200k +0.43 s, 390k −0.22 s, restart −1.09 s (no summary time) or +0.09 s (with).
- **As a share of observed model time:** +3.1%, −1.6%, and −7.9% / +0.6%.
- **Context share of the change:** the ceiling-200k replay removes 4.44B tokens of context (−67%), which is worth only 2.1–6.9 h of model time.

Per session, primary slope (net h):

| session | observed model h | ceiling 200k | ceiling 390k | restart >200k (no summary / with) |
|---|---|---|---|---|
| S01 | 1.85 | +0.09 | −0.01 | −0.14 / +0.04 |
| S02 | 3.34 | −0.06 | −0.19 | −0.39 / −0.09 |
| S03 | 17.13 | +0.22 | −0.53 | −1.65 / −0.06 |
| S04 | 0.78 | +0.10 | +0.11 | +0.03 / +0.06 |
| S05 | 8.34 | +0.18 | −0.14 | −0.43 / +0.04 |
| S06 | 2.31 | +0.15 | −0.02 | −0.15 / +0.08 |
| S07 | 0.34 | 0.00 | 0.00 | 0.00 / 0.00 |
| S08 | 0.59 | +0.03 | +0.04 | −0.01 / +0.03 |
| S09 | 15.59 | +0.62 | −0.27 | −1.33 / +0.05 |
| S10 | 10.80 | +0.59 | +0.02 | −0.83 / +0.23 |

**Break-even compaction duration** (primary slope): about 92 s for ceiling 200k and 198 s for 390k, against 130 s measured at 783k (89 s on opus-5.5). At the natural-experiment slope the 200k break-even is about 47 s.

## Caveats
- **Observational.**
  - Large-context calls come late in a compaction cycle and do different work: more output, more thinking. The output control rests on estimated output (placeholders in S02–S10) and does not capture difficulty.
  - The natural experiment removes time of day, model and task. It still compares the end of one stretch of work with the start of the next, and its slope (0.19) is about half the cross-sectional one (0.37).
- **Server load and time of day.**
  - Not observable. The slope is positive in all four UTC bins (0.22–0.48), but the median latency differs by about 1 s between bins.
  - The sessions span 8 weeks and three models. Model and date coincide (D3). opus-5.5's slope is a third of opus-5's, so the time benefit depends on the model and may change with the next one.
- **Streaming artifacts.**
  - Lines are stamped when a content block completes, not at the first token. TTFT is directly observable only in S01, through `thinkingDurationMs`, or approximately for tool-call-first messages without thinking.
  - The last line marks the end of the last block, not the end of the HTTP stream.
  - Server `created_at` carries a 0.1–0.4 s ingestion delay, the same for both ends of the interval.
- **Compaction duration at smaller ceilings is extrapolated.**
  - The replay charges the 783k duration, less the prefill term.
  - If summary generation scales with the amount of conversation summarized, compactions at 200k could be much shorter, and the ceiling levers would turn into time savings. The break-even values show how much shorter they would need to be.
  - Restart summary time is bracketed: 0 if the user starts fresh, or one compaction if a summary is generated.
- **Only model time is counted.** Tool execution time, user idle time and re-reads after a compaction or restart (D2, A5) are not counted, and neither are quality effects. The 17 extra calls per compaction that D2 scenario B charges, at about 13 s each, would add about 3.7 min per compaction and make the ceiling levers slower still.
- **Calls excluded from the fit.** These are user-prompt, parallel, sub-agent-interleaved and compaction calls, 14% of calls. The time totals include all of them except S01's 86 untimed calls, which are imputed at the median.

Scripts and their numeric outputs are kept with the analysis files.
