> Working memo from cycle A4 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# A4: how safe is "start a new session at an instruction boundary"?

Aggregates only; 10 main sessions, 16,181 calls, 667 instructions, 657 instruction boundaries (582 with context > 200k), 6.579e9 input tokens.

## Method
- Segments: `read_trace_lines` -> `calibrate` -> `link` (min_shared=1; windows end at observed compactions, so a reused segment was really in context at b). `bound.origin` gives the call of origin. Instruction boundary b = first call of instruction j+1 (unique `instruction_starts`, `_is_instruction`).
- Reuse R_b = calibrated tokens of segments with origin < b that have >= 1 lexical ref (excluding the birth ref) inside instruction j+1's calls. Unattributed segments (thinking, images, harness overhead) are not counted (not reusable lexically). Age = instructions back from j+1 to the segment's instruction. Also re-run with min_shared 3 and 5 (sensitivity).
- Classes: clean R <= 10k, light 10-50k, heavy > 50k. "Later input" = input tokens of instruction j+1's calls. ">200k" = observed context of the call before b.
- Re-reads by path (memory only): Read calls of instruction j+1 whose file path was read or written (Read/Write/Edit/MultiEdit/NotebookEdit) at any earlier call.
- Restart saving: segment replay of B3 (regime R2): context = base + live segments; observed compaction applies only if the replay reached 90% of the observed context, else skipped and the replay self-compacts at 790k to base+22k; no-policy replay reproduces measured input exactly (6,579,410,935). Restart at a boundary when the replayed context of the previous call > 200k and the boundary's class is allowed: drop segments with origin < b, add a 10k summary, plus (charged variants) re-add the segments of R_b (written once at 2.0 price, then carried and dropped at the next restart unless reused again). A restart is skipped if it would not shrink the context. All boundaries allowed with no charge reproduces B3 P1 (55.0% vs 54.8%; 144 restarts vs 146). The series replay of `whatif.restart` (current repo: 55.2% for the same rule) is run as a cross-check with the restart context = base + 10k + charge + new growth.
- Price = 0.1 per token kept from the previous call, 2.0 per new token (no-policy model total 0.715B).

## 1. How much of the past does the next instruction use (min_shared=1)
| | all boundaries (657) | context > 200k (582) |
|---|---|---|
| R_b median / quartiles | 171k (93k - 262k) | 187k (114k - 272k) |
| R_b share of prior context | | mean 38% (quartiles 28-50%) |
| segments reused, median | | 169 (quartiles 92 - 274) |
| boundaries with R_b = 0 | 1 | 1 |

Age of reused tokens (context > 200k), instructions back: 1: 10.5%, 2: 10.6%, 3: 9.2%, 4: 8.8%, 5: 8.1%, 6: 7.4%, 7: 6.4%, 8: 6.4%, 9: 5.3%, 10+: 27.2%. The previous instruction is no more reused than older ones; a quarter of what is quoted is 10+ instructions old (token-weighted mean age: clean 4.3, light 8.0, heavy 7.2).

## 2. Clean / light / heavy (min_shared=1)
Share of boundaries (b) and of the next instruction's input (i):
| set | n | clean | light | heavy |
|---|---|---|---|---|
| pooled | 657 | 2% b / 0% i | 11% / 5% | 87% / 95% |
| context > 200k | 582 | 1% / 0% | 5% / 2% | 93% / 98% |
| context <= 200k | 75 | 4% / 2% | 57% / 40% | 39% / 58% |

Per session, context > 200k (clean / light / heavy boundary counts; heavy share of next input):
S01 12 (0/0/12; 100%), S02 43 (0/0/43; 100%), S03 257 (2/18/237; 99%), S04 5 (0/1/4; 93%), S05 50 (1/1/48; 99%), S06 27 (0/7/20; 95%), S07 0, S08 3 (0/3/0; 0%), S09 118 (4/1/113; 98%), S10 67 (0/1/66; 94%). Only the small S08 (3 boundaries, 105 calls) and S04/S06 have any light share.

Sensitivity to the ref threshold (context > 200k; boundaries b / next input i):
| refs | clean | light | heavy | median R_b | mean R_b share of context |
|---|---|---|---|---|---|
| >= 1 shared term | 1% / 0% | 5% / 2% | 93% / 98% | 187k | 38% |
| >= 3 shared terms | 4% / 2% | 23% / 9% | 72% / 89% | 96k | 22% |
| >= 5 shared terms | 11% / 6% | 32% / 17% | 57% / 77% | 59k | 16% |
(Refs counted over the whole session instead of the observed windows give R_b above the context size: not usable as a class measure.)

## 3. Re-reads by path
Distinct files Read in instruction j+1: 843 over all boundaries (669 at > 200k); 14-15% had been read or written earlier (117 / 98); 73 of 582 boundaries above 200k contain at least one re-read. Re-read share by class (> 200k): clean 4/8, light 4/21, heavy 90/640. Re-read tokens are not reliable: 95% of the Read calls in the largest session return images (no text segment, counted as unattributed), so only text Reads have a measured size; of the text Read-result tokens 39% (> 200k) were re-reads. Path re-reads cover about 0% of lexically reused tokens (0.1M of 114.5M): the lexically reused content is almost never a file that is simply re-read. So a restart would mostly cost not a re-read of a known file but loss of derived content (Bash output, earlier assistant text, prompts).

## 4. Restart saving (% of measured input; price-weighted in brackets), segment replay
Context-triggered (> 200k) restarts, summary 10k:
| allowed boundaries | refs >= 1 | refs >= 3 | refs >= 5 |
|---|---|---|---|
| all (B3 P1; no charge, no class limit) | 55.0 (50.3) | 55.0 (50.3) | 55.0 (50.3) |
| clean only | 0.7 (0.6) [2 restarts] | 3.6 (3.2) [19] | 10.3 (9.4) [33] |
| clean + light, reuse charged as re-read | 3.7 (3.2) [19] | 20.2 (17.9) [70] | 30.4 (27.3) [92] |
| clean + light, only light charged | 3.9 (3.3) | 20.3 (18.0) | 30.6 (27.5) |
| clean + light, nothing charged (a summary carries <= 50k) | 5.5 (5.0) | 21.5 (19.7) | 32.1 (29.4) |
| every boundary, reuse charged | 26.7 (12.1) [272] | 40.9 (30.1) [247] | 45.7 (37.1) [216] |
Of the 144 restarts the unrestricted rule makes, 2 are clean, 12 light, 130 heavy (refs >= 1); 4/38/102 (>= 3); 12/54/78 (>= 5).

Series replay (`whatif.restart` convention, restart context = base + 10k + charge + new growth): unrestricted 55.2%; clean only -0.0 / -0.5 / 6.4; clean+light charged -0.5 / 20.1 / 28.7; every boundary charged 26.3 / 41.0 / 45.7 (refs >= 1 / 3 / 5). Segment and series replay agree within 2 points.

Threshold on R_b instead of the fixed classes (refs >= 1, charge as re-read, segment replay): R <= 50k 3.7%, <= 100k 12.5%, <= 150k 19.0%, <= 200k 24.2%, <= 300k 27.4%, all 26.7% (price: 3.2 / 10.3 / 14.2 / 16.5 / 15.0 / 12.1). The price-weighted saving peaks at R <= 200k (16.5%) and falls when heavier reuse is charged.

## Caveats
- Lexical reuse is unvalidated in both directions. min_shared=1 over identifier-like words is pessimistic (any single shared term makes a segment "reused"; a 100-segment tool output is credited for one repeated word); content obeyed but never quoted (instructions, decisions, style) is invisible, which makes every clean/light count optimistic. The truth for "how clean" lies between the min_shared=1 and >= 5 columns at best.
- Charging R_b as a re-read assumes the agent can fetch exactly those segments, at their original size, with no derivation cost; heavy reuse is mostly large tool outputs (Bash) that cannot be re-read by path.
- Images (most Reads in the largest session) have no text segment and are unattributed, so they never count as reused.
- Classification uses the original context; the restart context differs after earlier restarts. Summary writing, summary quality, cache-prefix breaks not modelled. Same-session boundaries are correlated (S03 has 44% of boundaries).
- Segments dead through an observed compaction are not counted as reusable (windows), so R_b is a lower bound relative to a no-compaction session.

## Findings
1. At 93% of the boundaries above 200k (98% of the next instruction's input) the next instruction quotes more than 50k of earlier content (median 187k, 38% of the context, ~170 segments); only 1% of boundaries are clean (R <= 10k).
2. Reuse is not recent: only 10% of reused tokens come from the instruction just before; 27% are 10+ instructions old, so a short summary of the last instruction would not carry it.
3. Even with looser refs (>= 5 terms) only 11% of boundaries are clean, and "restart only at clean points above 200k" saves 0.7% (3.6% / 10.3% for >= 3 / >= 5 terms) instead of 55%.
4. Allowing light boundaries with the reused tokens charged as a re-read gives 3.7% (price 3.2%); charging reuse at every boundary leaves 26.7% of input but only 12.1% of price, because re-read tokens cost 2.0 and the context stays large.
5. Re-reads by path are rare (14% of files read after a boundary) and cover ~0% of the lexically reused tokens, so the reuse is not cheap file re-reads; the 55% from the restart rule depends on the summary replacing content the next instruction quotes, which the records contradict for >= 1-term reuse.
