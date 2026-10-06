> Working memo from cycle C2 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# C2 - What is the invisible third? (aggregate numbers only)

## Method
- Per source S01..S10 (main session, sidechains excluded, as in bound.read_trace_lines). Call k kept if k is not 0/compaction restart and g_k = ctx_k - ctx_{k-1} > 0 (S01 n=397, S02 1299, S03 4805, S04 162, S05 1918, S06 462, S07 65, S08 103, S09 4047, S10 2865; pooled event-API n=15726).
- e_k = sum of segment tokens born at k before calibration; factor = calibrate() median (S01 1.96, S02 2.00, S03 2.05, S04 1.72, S05 1.93, S06 1.99, S07 1.82, S08 1.00 (fallback, <5 big calls), S09 1.87, S10 2.02). r_k = g_k - factor*e_k (unclamped).
- Previous-call proxies (k-1, all streamed lines of the message merged): o = max usage.output_tokens; thinking count, summed signature length (chars; redacted_thinking `data` counted too), thinking text length; o_inv = o - factor*(estimated visible assistant tokens in k-1) = output not already counted in e.
- Extra check not in the brief: image blocks and tool_reference blocks inside user tool_results (counted by type only; bound estimates them as 0 tokens).
- Pure-python Spearman / OLS / normal-equation multiple regression. Scripts: meta.py, an.py, an2.py, an3.py in this folder.

## 0. Overall residual
Residual share of growth: S01 0.32, S02 0.26, S03 0.30, S04 0.43, S05 0.33, S06 0.53, S07 0.27, S08 0.74 (factor fallback, ignore), S09 0.36, S10 0.41; pooled event 0.34. No dependence on context size (Spearman r/g vs ctx -0.09..+0.09, S07 +0.28 n=65).

## 1. Trustworthiness of output_tokens
| source | median o | share o<=3 | distinct values | o vs visible-output estimate (Spearman) |
|---|---|---|---|---|
| S01 | 858 | 0% | 351 | +0.89 -> real |
| S02 | 8 | 14% | 115 | -0.23 -> placeholder |
| S03 | 8 | 15% | 281 | -0.15 -> placeholder |
| S04-S10 | 3-16 | 36-59% | 9-25 | negative -> placeholder |
Only S01 has real output counts. S02/S03 look like partly real streaming snapshots but are anticorrelated with content size, so they are not usable. Within a message usage never varies across streamed lines (no later final update).

## 2. Correlation of r_k with o_{k-1} and thinking proxies
Spearman (S) / linear slope (b) / R2 of r on x:
| source | o_{k-1} S, R2 | o_inv S, b, R2 | sig_len S, b, R2 | has_think S |
|---|---|---|---|---|
| S01 (real o) | +0.23, 0.07 | +0.80, 0.98, 0.33 | +0.62, 0.256, 0.27 | +0.37 |
| S02 | -0.31, 0.01 | n/a | +0.47, 0.20, 0.06 | +0.33 |
| S03 | -0.21, 0.00 | n/a | +0.43, 0.26, 0.23 | +0.26 |
| S04 | +0.06, 0.01 | n/a | +0.50, 0.37, 0.05 | +0.43 |
| S05 | -0.46, 0.06 | n/a | +0.69, 0.29, 0.44 | +0.62 |
| S06 | -0.09, 0.01 | n/a | +0.48, 0.25, 0.12 | +0.41 |
| S07 | -0.40, 0.16 | n/a | +0.81, 0.32, 0.73 | +0.56 |
| S08 | -0.46, 0.05 | n/a | +0.61, 0.37, 0.15 | +0.51 |
| S09 | -0.44, 0.00 | n/a | +0.68, 0.28, 0.06 | +0.63 |
| S10 | -0.30, 0.04 | n/a | +0.53, 0.32, 0.14 | +0.49 |
| pooled event | -0.33, 0.00 | n/a | +0.54, 0.27, 0.15 | +0.46 |
(o_inv is meaningless where o is a placeholder.) Raw o_{k-1} correlates weakly in S01 because most of o is visible text/tool input already inside e_k (invisible part o_inv is only 24.5% of o). Thinking text length is empty in most calls (text present in 17-30% of S01-S03 calls, 0 in S04-S10), so it is useless; the signature length survives and is the proxy.

Key regularity: the slope of residual on signature length is 0.22-0.39 tokens/char in all ten sources (pooled event 0.27, S01 0.26), i.e. about one residual token per 3.5-4 signature characters, in sources with no output information at all.

## 3. Share of residual explained
S01 (real output): r = 423 + 0.98*o_inv, R2 0.33, Spearman 0.80. The slope near 1.0 means that the part of the previous call's output tokens the transcript does not show enters the next call's context one-for-one. Adding signature length to o_inv adds nothing (coef -0.007), i.e. signature is a proxy for the same quantity. Split: tool-loop calls (n=368) slope 1.01, R2 0.41; calls following a new user prompt (n=29) slope 1.3, intercept 1.4k, R2 0.02 (small n). Decomposition of S01 total residual: o_inv term 0.49-0.52, constant ~420 tokens/call about 0.41-0.49 (a constant mixes harness framing with unmodeled blocks), and images explain only ~0.07.
Calls whose previous message held thinking blocks carry 90% (S01), 62% (S02), 66% (S03), 75% (S05), 99% (S07), 54% (S09), 54% (S10) of summed residual (S04 62%, S06 51%, S08 80%), with median r 305-590 vs 55-130 for no-thinking calls (S08 outlier).
Joint model r ~ 1 + sig + n_images (event pooled): intercept 231 tok/call (share 0.38), signature 0.28/char (share 0.49), image ~1381 tok per image (share 0.13), R2 0.22. By source the signature share is 0.30-0.96 (S01 0.78, S03 0.63, S05 0.65, S07 0.96), image share 0.05-0.29.
Images: no-thinking calls whose results include an image have median r 1.2k-2.7k vs 54-130 without (all 9 sources with images). tool_reference blocks add ~300-900 tokens per occurrence (rare).

## 4. Candidate verdicts
(a) thinking blocks: best supported. Previous call had thinking in 30-70% of calls; residual is 1-for-1 with invisible output in S01, scales with signature length everywhere (consistent 0.27 tok/char slope), concentrated in post-thinking calls. Share of the invisible third: roughly 50-65% (S01 ~50%, event pooled ~49% by signature term, up to ~75% in some sources).
(b) output tokens: the same quantity as (a) plus visible output already in e; visible output is not the missing part. Raw o correlation is not interpretable except in S01.
(c) harness framing: constant per-call term, 100-500 tokens/call (S01 ~100-420 depending on model, event pooled 231); no-thinking, no-image calls have median r 54-130 and mean 66-450, no-thinking, no-image residual is heavy-tailed (4-12% of calls r>1000 in S02,S03,S09,S10), so a tail of unmodeled blocks remains. ~0.15-0.55 of residual.
(d) tokenizer mismatch beyond factor: weak. In no-thinking calls with e>=2000 the median r is -24..-480 (factor slightly high); r~e slope -0.06..-0.6 and negative Spearman (-0.12..-0.30), meaning the scalar factor over-corrects large visible chunks and under-corrects small ones (this contributes to the intercept). Not a third.
(e) images/tool_reference (new): 5-29% by source; each image ~1.0-2.4k tokens, which bound treats as 0.

## 5. Conclusion and strength
The invisible third is most likely a mixture: about half encrypted/redacted thinking (strong evidence in S01, where it is 1:1 with output minus visible; consistent signature slope across all sources), plus about a third constant per-call framing/ estimator nonlinearity, plus ~10% unmodeled images/tool references. Strength: moderate-to-strong for thinking as the largest single part, weak for splitting the remainder. R2s are low (0.05-0.8) because per-call framing and tokenizer noise are large and signature is only a proxy.
Caveats: only S01 has real output; factor is itself estimated from the same data (and ~2.0, i.e. the estimator undercounts about half); thinking from earlier calls in the loop is already in earlier context; signature length may be capped/encoded nonlinearly; g<=0 calls excluded; S08 factor=1.0 fallback inflates its residual.
## What would settle it
Provider fields: per-call output_tokens with thinking tokens split out (usage reasoning/thinking token count) and final (not stream-start) output_tokens for event-API sources; or count_tokens on the transcript with and without thinking/image blocks. Event API recording usage at message_delta rather than message_start would make (b) testable for S02-S10.
