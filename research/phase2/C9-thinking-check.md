> Working memo from cycle C9 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts and event pages at the dataset-v2 snapshots.

# C9: Does thinking *time* confirm C2's thinking share of the invisible growth? (aggregate numbers only)

Main-session calls of the ten dataset-v2 sessions at the dataset-v2 snapshots. No transcript text, thinking text, paths or commands are reproduced; only counts, sizes, durations and fitted coefficients.

## Findings
1. **Thinking time and signature length measure the same quantity.** In S01, `thinkingDurationMs` predicts the invisible output (real output minus calibrated visible output) as well as signature length does: R² 0.80 against 0.78; Spearman between duration and signature is +0.97. The gap-based duration available in the event pages reproduces the field: Spearman +0.95, sum ratio 1.07. Per-session Spearman of duration against signature is +0.85 to +0.98.
2. **C2's one-for-one transfer holds with an independent measure.** The next call's invisible growth rises by 1.05 tokens per duration-estimated thinking token (pooled event sessions). The slope is 0.94–1.06 in the three opus-5.5 sessions, where the thinking rate transfers directly from S01, and 1.1–1.5 in the opus-5/fable sessions, where the rate had to be scaled.
3. **"About half" is the upper end.** With images in the model, as in C2, duration-based thinking explains **0.39** of the pooled event-session invisible growth. The intercept explains 0.48 and images 0.13. Signature length on the same rows gives 0.49 / 0.38 / 0.13, reproducing C2. Across rate and time-to-first-token (TTFT) variants the pooled share is 0.31–0.50, and it is 0.26–0.79 by session. In S01 it is 0.65–0.71, above C2's 0.50.
4. **The constant per-call overhead is larger by the duration measure.** It is 290 tokens per call, 0.48 of the invisible growth, compared with C2's 231 tokens and 0.38.
5. **Output money sits at C5's low estimate.** Output is **8.3%** of main-session money in the event sessions (8.0–9.0% across variants) and 8.4% across all main sessions. C5 had 8.0% for the event sessions and 8.2% for all main sessions at its low θ = 0.179. The duration-implied tokens per signature character are 0.17–0.26 (S01 0.22). That supports C5's low and middle estimates, not the high θ = 0.39. All money then has an output share of about 9%, the bottom of C5's 9–12% range.

## Method
- **Data.**
  - Per-call records come from C6's per-call records: usage, visible-output estimate, signature length, request start and the C6 trigger classes.
  - New per-line records come from the C6 loader, re-run: every assistant line carries one content block, with its client time, server `created_at`, block type and size (C9/lines.json).
  - C2's residual rows (C2/rows.pkl: r_k = g_k − factor·e_k) are aligned to calls by index. The alignment is asserted on context in every session.
  - Image counts per call follow C2's rule.
- **S01, with real output and `thinkingDurationMs`.**
  - inv = out − 1.96·vis.
  - Fits of out and inv on visible output, signature characters, thinking seconds and generation time. Generation time is last-line latency minus TTFT, with TTFT = 2.12 s: the first thinking line's latency minus `thinkingDurationMs`, median, n = 204.
  - Rates are taken from (a) clean calls without thinking, (b) post-thinking streaming in thinking calls, and (c) inv per thinking second.
- **Thinking duration in the event pages (S02–S10).**
  - The first thinking block lasts from the request start (server `requesting`) to that line's `created_at`, minus TTFT. Each later thinking block lasts from the previous line to its own line.
  - Per-session TTFT is a + b·ctx: Theil–Sen on no-thinking calls, using first-line latency minus the first block's visible tokens divided by the visible rate.
  - Validated on S01 by applying the same gap rule with client time.
  - Calls with C6 class clean, parallel, sub-agent or user-prompt are used. Calls without thinking have a duration of 0. 0.3–3% of thinking calls have no usable time.
- **Duration to tokens.**
  - Rate_think(session) = 84.7 tok/s (S01: median inv per thinking second, real counts) × the session's visible streaming rate ÷ S01's visible streaming rate (152 tok/s, Theil–Sen of the post-thinking stream time on visible tokens).
  - This assumes that the ratio of thinking rate to visible rate (0.56) holds for every model. It is calibrated on S01's real output counts, but it uses neither signature length nor context growth.
- **The C2 test.** OLS of r_k on the previous call's thinking tokens, with and without image counts. The shares are coefficient × sum / Σr. The share at 1:1 is Σ thinking tokens / Σr.
- **Money.** Main session only: inp + 0.1·cache_read + 2.0·cache_write (all main writes are 1-hour) + 5·output. Output = max(recorded, 1.96·vis + thinking tokens). Untimed thinking calls are filled with the session's tokens per signature character. C5-low is recomputed the same way for comparison.
- **Scripts** and their outputs are kept with the analysis files.

## 1. S01: real output against visible output, signature and thinking time (n = 400 calls, 285 with thinking)
| fit | coefficients | R² |
|---|---|---|
| out ~ visible (calibrated) | 459 + 0.99·vis (Spearman +0.89) | 0.78 |
| out ~ signature chars | 788 + 0.41·sig (Spearman +0.68) | 0.44 |
| out ~ thinking s | 971 + 139·s (Spearman +0.70) | 0.45 |
| out ~ generation time (clean, n = 368) | 14 + 110 tok/s × s (Spearman +0.98) | 0.94 |
| out ~ 1 + vis + sig | −58 + 0.85·vis + 0.284·sig | 0.974 |
| out ~ 1 + vis + thinking s | 69 + 0.85·vis + 95.5·s | 0.973 |
| out ~ 1 + vis + s + sig | 0 + 0.85·vis + 46·s + 0.149·sig | 0.975 |
| inv ~ sig (origin, i.e. out = vis + θ·sig) | θ = 0.238 tok/char | 0.78 |
| inv ~ thinking s (origin) | 84.7 tok/s | 0.80 |

**Thinking share of S01 output.**
- 0.245 by out − vis.
- 0.28 by 84.7 tok/s × duration.
- 0.32 by the free fit on duration.
- 0.33–0.39 by the signature fits.

The visible coefficient falls to 0.85 when thinking enters the model. In no-thinking calls, out / (1.96·vis) is 0.97.

**Rates (tok/s).**

| source of the rate | rate |
|---|---|
| no-thinking clean calls (n = 95): median vis / (latency − TTFT) | 84.9 |
| no-thinking clean calls: Theil–Sen marginal rate | 153 (134 with real out) |
| post-thinking stream (n = 279) | 152 |
| invisible output per thinking second, thinking ≥ 2 s (n = 196) | 84.7 (Theil–Sen 86.8) |

Thinking therefore yields about 0.56× the visible streaming rate per second.

**How well duration × rate predicts the invisible output.**

| rate used | predicted / actual inv | inv ~ prediction | R² |
|---|---|---|---|
| 85 tok/s (median ratio) | 1.16 | slope 1.03 | 0.80 |
| 153 tok/s (marginal visible rate) | 2.09 | slope 0.57 | 0.80 (0.19 against identity) |

The "little-thinking" rate only works in its median-ratio form, which carries a per-call overhead. The marginal visible rate overstates thinking about two-fold.

## 2–3. Duration-based thinking tokens by session
| session | model | visible rate tok/s (n) | TTFT s, a + b per 100k | thinking rate used | timed / thinking calls | median thinking s | Spearman dur~sig | Σ dur-tok / Σ 0.179·sig (C5) | / 0.27·sig (C2) | tok per sig char |
|---|---|---|---|---|---|---|---|---|---|---|
| S01 | opus-5.5 | 153 (264) | 2.12 (fixed) | 85 | 270/285 | 4.1 | +0.86 | 1.24 | 0.82 | 0.221 |
| S02 | opus-5.5 | 143 (695) | 1.78 + 0.07 | 80 | 722/736 | 2.5 | +0.85 | 0.94 | 0.62 | 0.168 |
| S03 | opus-5.5 | 143 (2764) | 1.46 + 0.19 | 80 | 2854/2944 | 2.9 | +0.85 | 1.15 | 0.76 | 0.206 |
| S04 | opus-5/fable | 98 (56) | 3.48 + 0.07 | 55 | 56/57 | 2.8 | +0.93 | 1.19 | 0.79 | 0.212 |
| S05 | opus-5 | 84 (744) | 2.16 + 0.49 | 47 | 844/847 | 6.1 | +0.90 | 1.22 | 0.81 | 0.218 |
| S06 | opus-5 | 98 (169) | 2.32 + 0.76 | 55 | 188/191 | 5.4 | +0.95 | 1.23 | 0.82 | 0.220 |
| S07 | opus-5 | 77 (41) | 1.44 + 0.26 | 43 | 43/43 | 6.2 | +0.98 | 1.07 | 0.71 | 0.191 |
| S08 | fable-5 | 105 (56) | 8.27 − 0.99 | 59 | 60/61 | 6.4 | +0.93 | 1.47 | 0.98 | 0.264 |
| S09 | opus-5 | 81 (1308) | 1.73 + 0.42 | 45 | 1471/1495 | 5.7 | +0.92 | 1.09 | 0.72 | 0.195 |
| S10 | opus-5 | 94 (836) | 2.04 + 0.43 | 52 | 894/905 | 5.8 | +0.94 | 1.25 | 0.83 | 0.223 |

**C2 test, single regressor:** r_k ~ a + b·(thinking tokens of call k−1).

| session | n | b | a (tok/call) | R² | Spearman | thinking share fitted (1:1) | intercept share | signature model, same rows: b, a, R² |
|---|---|---|---|---|---|---|---|---|
| S01 (field) | 383 | 1.06 | 228 | 0.38 | +0.59 | 0.69 (0.65) | 0.31 | 0.255, 140, 0.34 |
| S02 | 1285 | 1.02 | 353 | 0.10 | +0.46 | 0.36 (0.35) | 0.64 | 0.202, 317, 0.07 |
| S03 | 4716 | 0.94 | 364 | 0.26 | +0.41 | 0.44 (0.47) | 0.56 | 0.262, 264, 0.24 |
| S04 | 161 | 1.46 | 437 | 0.14 | +0.47 | 0.30 (0.21) | 0.70 | 0.334, 413, 0.13 |
| S05 | 1915 | 1.12 | 227 | 0.41 | +0.69 | 0.53 (0.47) | 0.47 | 0.286, 183, 0.44 |
| S06 | 459 | 1.07 | 798 | 0.12 | +0.48 | 0.26 (0.25) | 0.74 | 0.250, 780, 0.12 |
| S07 | 65 | 1.34 | 114 | 0.69 | +0.81 | 0.79 (0.59) | 0.21 | 0.318, 7, 0.73 |
| S08 | 103 | 1.30 | 1248 | 0.17 | +0.60 | 0.33 (0.26) | 0.67 | 0.370, 1196, 0.15 |
| S09 | 4023 | 1.33 | 327 | 0.06 | +0.67 | 0.35 (0.27) | 0.65 | 0.284, 310, 0.06 |
| S10 | 2854 | 1.30 | 416 | 0.14 | +0.52 | 0.32 (0.25) | 0.68 | 0.325, 392, 0.14 |
| **event pooled** | 15581 | **1.05** | **376** | 0.16 | +0.54 | **0.37 (0.36)** | **0.63** | 0.270, 318, 0.15 |

The S01 rows use the field. With the gap-based duration instead, b = 1.01, a = 217, R² 0.38. Tool-loop calls only: b = 1.05, a = 199, R² 0.46.

**Pooled joint model:** r ~ 1 + dur-tok + sig gives coefficients 359 + 0.83·dur-tok + 0.06·sig, R² 0.161. Duration absorbs almost all of the signature's information.

**With images,** as C2's joint model (shares of Σr: intercept / thinking / images):

| session | duration model: a, b, tok per image, R², shares | signature model: a, b, tok per image, R², shares |
|---|---|---|
| S01 | 141, 1.09, 1572, 0.45, 0.19 / 0.71 / 0.09 | 42, 0.266, 1619, 0.42, 0.06 / 0.85 / 0.10 |
| S02 | 269, 1.09, 1273, 0.21, 0.49 / 0.39 / 0.13 | 223, 0.221, 1283, 0.18, 0.40 / 0.47 / 0.13 |
| S03 | 222, 0.99, 1446, 0.44, 0.34 / 0.46 / 0.20 | 104, 0.281, 1484, 0.43, 0.16 / 0.64 / 0.20 |
| S04 | 368, 1.51, 598, 0.18, 0.58 / 0.31 / 0.10 | 341, 0.346, 605, 0.17, 0.54 / 0.36 / 0.10 |
| S05 | 153, 1.16, 1256, 0.51, 0.32 / 0.55 / 0.14 | 101, 0.299, 1323, 0.55, 0.21 / 0.65 / 0.14 |
| S06 | 449, 1.21, 2386, 0.27, 0.41 / 0.30 / 0.29 | 418, 0.288, 2418, 0.27, 0.39 / 0.32 / 0.29 |
| S07 | 97, 1.30, 1010, 0.73, 0.17 / 0.77 / 0.06 | −2, 0.307, 876, 0.76, 0.00 / 0.95 / 0.05 |
| S08 | 1057, 1.36, 1025, 0.19, 0.56 / 0.35 / 0.08 | 1000, 0.390, 1019, 0.17, 0.53 / 0.38 / 0.08 |
| S09 | 297, 1.36, 1063, 0.07, 0.59 / 0.36 / 0.05 | 279, 0.292, 1077, 0.07, 0.55 / 0.40 / 0.05 |
| S10 | 370, 1.34, 1045, 0.16, 0.60 / 0.33 / 0.07 | 345, 0.334, 1049, 0.16, 0.56 / 0.37 / 0.07 |
| **event pooled** | **290, 1.08, 1358, 0.24, 0.48 / 0.39 / 0.13** | **225, 0.283, 1384, 0.24, 0.38 / 0.49 / 0.13** (= C2) |

**Sensitivity,** pooled event, single regressor:

| variant | b | a | share fitted | share 1:1 | output % of event main money |
|---|---|---|---|---|---|
| model-scaled rate (primary) | 1.05 | 376 | 0.37 | 0.36 | 8.3 |
| S01 rate (85 tok/s) for all sessions | 0.79 | 364 | 0.39 | 0.50 | 9.0 |
| TTFT + 1 s | 1.08 | 397 | 0.34 | 0.31 | 8.0 |
| TTFT − 1 s | 1.01 | 355 | 0.41 | 0.40 | 8.5 |

## 4. Output share of main-session money (%)
| session | recorded | C5 low (1.96·vis + 0.179·sig) | duration-based |
|---|---|---|---|
| S01 | 15.5 (real) | 16.6 | 16.7 |
| S02 | 0.3 | 7.2 | 7.1 |
| S03 | 0.4 | 10.2 | 10.5 |
| S04 | 0.1 | 12.9 | 13.2 |
| S05 | 0.1 | 6.6 | 6.9 |
| S06 | 0.1 | 9.6 | 10.1 |
| S07 | 0.2 | 21.0 | 21.3 |
| S08 | 0.1 | 11.6 | 13.4 |
| S09 | 0.1 | 6.5 | 6.6 |
| S10 | 0.1 | 6.9 | 7.2 |
| **event pooled** | 0.2 | **8.0** | **8.3** (8.0–9.0) |
| all main (S01 real) | – | 8.2 | 8.4 |

In S01 both estimators overshoot the real 15.5% by about 1 point, through the max(recorded, estimate) rule and the visible coefficient of 0.85.

## Conclusion
- **The 1:1 mechanism.** An estimate of thinking that uses neither signature length nor output counts outside S01 confirms that the previous call's thinking enters the next context about one for one (pooled slope 1.05; 0.94–1.06 on opus-5.5).
- **The size of the thinking part.** Thinking is the largest single component in S01 (0.65–0.71) and in S03, S05 and S07. Pooled over the event sessions it explains **about 0.36–0.39 of the invisible growth**, range 0.31–0.50, rather than C2's 0.49. The constant per-call term is correspondingly larger: about 0.48 instead of 0.38.
- **Revised summary of the invisible third.** It is about 40% thinking, about 45–50% per-call constant and unmodeled blocks, and about 13% images. "About half thinking" holds in S01 and the opus-5.5 session S03, and at the top of the sensitivity range.
- **Output money.** C5's output estimate is confirmed at its low end: about 8–9% of main money, about 9% of all money. The θ = 0.39 high scenario (10.8% of main, 11.6% of all) is not supported.

## Caveats
- **Rate transfer.**
  - The duration-to-token rate is calibrated on S01, the only session with real output counts. That makes it independent of signature length and context growth, but not of S01's output counts.
  - For opus-5 and fable it is scaled by the ratio of visible streaming rates. Slopes of 1.1–1.5 in those sessions suggest the scaled rate understates their thinking by about 25%. The "S01 rate for all" variant brackets this: 1:1 share 0.50, money 9.0%.
- **TTFT is modelled, not observed, in S02–S10.** A ±1 s change moves the pooled share between 0.31 and 0.41. Lines are stamped when a block completes, and server `created_at` adds a 0.1–0.4 s ingestion delay. In S01 the gap rule matched the field: sum ratio 1.07, R² 0.97.
- **Noise.** Measurement noise in duration (TTFT error, clamping at 0) attenuates the slope and inflates the intercept. That pushes the fitted thinking share down, so 0.39 is a lower-leaning estimate and the signature-based 0.49 an upper-leaning one.
- **Fit quality.** R² values are low (0.06–0.73), as in C2. The intercept mixes harness framing, tokenizer nonlinearity and unmodeled blocks, and cannot be split further with these data.
- **Coverage.** Money is main session only. Sub-agent output was not re-estimated, so the "about 9% of all money" figure extrapolates C5's sub-agent share.
