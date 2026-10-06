> Working memo from cycle B4 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the public `dataset-v2.json` alone. The sweep and the model are reproduced by `pxt survey whatif`.

# B4 - If the ceiling sets the average context, where should it be?

Data: only the public per-call context series (research/survey/user01/dataset-v2.json, 10 sessions, 16,181 calls, 6.58B input) plus the published D2 and B3 memos. No private lines loaded; aggregates only.
Files: curve.py (function `ceiling_curve(series_list, ceilings, R)`, model helpers, self-test; the test also checks equality with `whatif.cap`), curve.csv (ceiling x R, fine grid 90k-800k step 10k), curves.json, run.py.

## Method
- Replay = `whatif.cap` semantics: when the replayed context passes C it is compacted to base + 22,000 (base = call-0 context), the compaction call is charged one read of the full context, an observed drop applies only if the replay reached 90% of its size (so observed compactions are free where they still occur, as in whatif). Pooled over all 10 sessions; saving is against actual measured input (6,579M). Self-test: replay equals `whatif.cap` input and compaction count on real series.
- R = flat extra input per replay-triggered compaction. R_D2 = 6.6k excess re-read result tokens + 0.7 excess re-reads x 108.7k mean input of an issuing call (63.7M / 586, D2 table 2) = 82.7k. Also 5x = 413k and 10x = 827k. (Carry of the re-read tokens through the cycle is not in flat R; sensitivity below.)
- Price-weighted (same replay): per call 0.1 x kept context + 2.0 x new content; a compaction costs a read of the context plus 2.0 x the (base + 22k) rebuild; R priced at 0.25 per token (D2's composition: 6.6k written at 2.0, 76k read at 0.1). Baseline = same model with the observed compactions only.
- Analytic model: context saw-tooths P..C at growth g per call. input(C) = N(P+C)/2 + (G/(C-P)) x (C+R), G = N g. Setting the derivative to zero gives (C-P)^2 = 2 g (P+R), so **C* = P + sqrt(2 g (P+R))**. With a read price w and fixed per-compaction cost K (summary written at 2.0): C* = P + sqrt(2 g (P + K/w)). Inputs from the data: g = 1,787 tokens per call (pooled positive growth / calls), P = 72.7k (call-weighted base + 22k; D2 observed 64k median post).

## Replay curve (saving vs actual, %, raw input / price-weighted)
| C | compactions (replay) | R=0 | R=D2 (83k) | R=5x | R=10x |
|---|---:|---|---|---|---|
| 100k | 1,329 | 76.5 / 61.8 | 74.8 / 58.0 | 68.2 / 42.8 | 59.8 / 23.8 |
| 150k | 388 | 71.6 / 63.8 | 71.1 / 62.7 | 69.2 / 58.2 | 66.7 / 52.7 |
| 200k | 228 | 65.7 / 59.5 | 65.4 / 58.9 | 64.3 / 56.3 | 62.8 / 53.0 |
| 250k | 160 | 59.8 / 54.5 | 59.6 / 54.1 | 58.8 / 52.2 | 57.8 / 50.0 |
| 300k | 123 | 53.6 / 49.2 | 53.4 / 48.8 | 52.8 / 47.4 | 52.0 / 45.7 |
| 400k | 83 | 41.9 / 38.7 | 41.8 / 38.5 | 41.4 / 37.6 | 40.9 / 36.4 |
| 500k | 63 | 30.3 / 28.2 | 30.2 / 28.0 | 29.9 / 27.3 | 29.5 / 26.4 |
| 600k | 49 | 18.7 / 17.4 | 18.7 / 17.3 | 18.4 / 16.7 | 18.1 / 16.0 |
| 783k (today) | 26 | -1.5 / -1.5 | -1.6 / -1.6 | -1.7 / -1.8 | -1.8 / -2.2 |
(783k: the replay compacts at its own ceiling a hair earlier than some observed ones and charges the compaction read, hence -1.5%; the rest of the table is relative to the measured baseline, so subtract about 1.5 for savings "vs today".)

## Optimum and flatness (fine grid, 10k steps)
| R | analytic C* (raw) | const-growth replay | real replay opt (saving) | within 2 pts | within 5 pts | within 10 pts | price-weighted opt (saving), within 2 pts | analytic price C* |
|---|---|---|---|---|---|---|---|---|
| 0 | 89k | 100k | 100k (76.5%) | 90-120k | 90-150k | 90-190k | 120k (64.8%), 110-160k | 116k |
| D2 | 96k | 100k | 100k (74.8%) | 100-130k | 90-160k | 90-200k | 130k (63.1%), 110-170k | 123k |
| 5x | 114k | 120k | 120k (70.7%) | 110-150k | 100-180k | 100-230k | 150k (58.2%), 130-200k | 147k |
| 10x | 129k | 130k | 140k (67.1%) | 120-170k | 110-200k | 100-250k | 170k (53.4%), 140-220k | 169k |
Per-session optima (R=D2) sit at 90-110k raw and 110-150k price-weighted in all 10 sessions.

## Model vs replay
Saving relative to each curve's own 783k point, R=D2: C=100k model 77.1 / constant-growth replay 75.8 / real 75.2; 200k 67.4 / 66.5 / 65.9; 300k 56.0 / 55.0 / 54.1; 400k 44.4 / 43.6 / 42.7; 600k 21.2 / 21.4 / 19.9. The closed form tracks the real replay within about 1 point from 150k up, and the optimum within 5-15k; lumpy growth and per-session base differences make the real curve slightly lower and its optimum slightly higher. The model gets worse only where compactions are every ~10 calls (C near P).

## Findings
1. In raw input the optimum is not a mid-range ceiling: it is as low as the post-compaction size allows (100k with R=0 or D2's R; 120-140k with 5-10x R), i.e. P + sqrt(2g(P+R)), which is only 17-56k above P. The pure token curve falls roughly 11 points per 100k of ceiling (783k -> 400k +43 pts, 400k -> 200k +24, 200k -> 100k +11 pts).
2. Flatness: within 2 points of the optimum spans only about 30-60k (e.g. 100-130k at D2's R); within 10 points it is 90-200k. At 150k the replay already keeps 71% (D2's R) and at 200k 65%, so 150-200k loses 4-11 points against the bare optimum but needs 388/228 compactions instead of 1,329.
3. Dependence on R is weak in the C* location and strong at the very low end: R from 0 to 10x moves the optimum 100k -> 140k and the best saving 76.5 -> 67.1%; at C >= 200k R barely matters (65.7 -> 62.8%). Break-even (saving = 0 at fixed C) needs R of 3.8M tokens per compaction at 100k and 19M at 200k, i.e. 46x-230x D2's R for flat R. Carrying the re-read tokens through the cycle (6.6k carry: opt 100k, 74.7%; 33k carry, D2's gross: opt 130k, 67.8%) shifts the optimum up 30k at most.
4. Price-weighted (summary rewrite at 2.0 dominates short cycles) the optimum moves up to 120-170k (63-53% saving) and 100k becomes poor with R (23.8% at 10x); a sensible reading is a ceiling around 150-200k: 63.8 / 59.5% at R=0 and 58.2 / 56.3% at 5x.
5. The 1,329 compactions at 100k (one per ~12 calls; D2 puts ~177 s of wall clock on each) and the quality cost of 40x as many summaries are exactly what the token arithmetic ignores: R above is only re-read burden. Where the real optimum lies between 150k and 400k is decided by the quality cost per summary, which only the phase-3 experiment can measure.

## Caveats
- Fixed call sequence and growth (growth is independent of context size); summary 22k always enough; the compaction call reads the cached context (charged as one read); no wall-time or cache-TTL effects; observed compactions are free where the replay reaches them (as in whatif), so counts include only the replay-triggered ones.
- R is flat per compaction and a D2 extrapolation: 0.7 excess re-reads came from compactions at 783k; at short cycles the habitual re-read rate may not hold. R_D2 includes the issuing calls as extra calls (an upper reading, D2 measured them as mixed with other work).
- For C below about 90-100k the post size (base + 22k, up to 87k in S02) approaches C, so the replay compacts nearly every call; those points are shown only to locate the optimum.
- Price weighting prices R at 0.25 and does not model the cache-prefix break of a changed context.
