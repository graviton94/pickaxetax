> Working memo from cycle E5 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# E5: the oracle bound when reuse has to beat a vocabulary placebo

Aggregates only; no transcript text, paths, commands or tokens were printed or stored.
10 main sessions (16,181 calls), segments from `bound.read_trace_lines` + `calibrate`
(unchanged). Scripts are kept with the analysis files.

## Method (fixed before any bound result was computed)
- **Baseline V0** = `bound.link(min_shared m, common_frac 0.02)`, re-implemented from per-segment hit counters.
  Reproduces lexical-v1 exactly at m = 1: **5.6 / 41.5 / 46.1** (P = inf / 1000 / 0); m = 3 gives 19.3 / 52.1 / 53.3.
- **Method 1, user-vocabulary filter (U3, U4).** df_other(token) = share of the other nine sessions'
  segments (non-unattributed) that contain the token. A token is distinctive for a session only if
  df_other <= tau, tau = 1e-3 (U3, about 30 segments) or 1e-4 (U4, about 3 segments); the session-common
  rule of `link` is kept. Of each session's output-token occurrences, U3 keeps 49-69%, U4 23-47%.
  Links rebuilt with min_shared 1 and 3.
- **Method 2, placebo correction (on V0, m = 1 and 3).** For segment s with W later calls in its window and
  n_obs ref calls, observed rate r = n_obs / W; placebo rate p:
  - *Cmirror*: time-mirrored calls of the same session before the segment existed (distance d after
    birth <-> call origin(s) - d), so the same distances, the same session, the same vocabulary drift, but
    calls that cannot have used s. No mirror available: session pooled rate of the segment's kind.
  - *Cother*: 1,000 calls sampled uniformly from the other nine sessions (fixed seed).
  - Expected-value correction: genuine rate g = max(0, (r - p)/(1 - p)); each observed ref kept
    independently with probability g / r (birth always needed); bound averaged over 5 draws (spread
    <= 0.3 pt). Secondary deterministic test *T*: keep all refs iff n_obs > pW + 2 sqrt(W p(1-p)), else none.
  - Combined: Cmirror on top of U3 (m = 1).
- Bound policies P = inf, 10000, 1000, 0 via `bound.bound` / `bound.merge` unchanged. "Paging gain" =
  P=1000 minus P=inf. Status flip = segment reused (a ref after birth) under V0 with the same m, never under
  the variant. Reference point: with no reuse at all (every segment needed only at birth) the avoidable
  share is **57.3%**, the ceiling for every column.

## 1. Pooled bound (% of measured main-session input)
| variant | P=inf (forgetting) | P=1000 (paging) | P=10000 | P=0 | paging gain | carried dead | carried idle | segments reused % | segment tokens reused % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **V0 m1 (lexical-v1)** | **5.6** | **41.5** | 22.6 | **46.1** | 35.9 | 5.1 | 37.7 | 80.2 | 96.4 |
| U3 m1 | 12.1 | 48.7 | 36.8 | 51.1 | 36.6 | 10.8 | 41.8 | 62.4 | 91.8 |
| U4 m1 | 26.5 | 53.4 | 47.8 | 54.5 | 26.9 | 22.9 | 44.4 | 42.0 | 77.6 |
| Cother m1 | 13.4 | 47.7 | 33.4 | 51.0 | 34.3 | 11.3 | 41.5 | 66.5 | 85.4 |
| Cmirror m1 | 32.8 | 53.5 | 46.8 | 54.9 | 20.7 | 27.1 | 44.6 | 40.1 | 50.2 |
| U3 + Cmirror m1 | 37.5 | 55.0 | 50.9 | 55.8 | 17.5 | 31.2 | 45.4 | 31.6 | 45.2 |
| Tother m1 | 16.8 | 44.0 | 28.7 | 47.9 | 27.2 | 13.8 | 39.1 | 57.1 | 74.8 |
| Tmirror m1 | 41.3 | 51.6 | 45.6 | 53.3 | 10.3 | 33.8 | 43.3 | 25.8 | 28.6 |
| V0 m3 | 19.3 | 52.1 | 44.4 | 53.3 | 32.8 | 17.0 | 43.5 | 36.9 | 82.6 |
| U3 m3 | 29.8 | 54.8 | 51.0 | 55.4 | 25.0 | 25.7 | 45.1 | 26.5 | 72.7 |
| U4 m3 | 43.4 | 56.2 | 54.6 | 56.5 | 12.8 | 36.3 | 45.9 | 14.4 | 49.9 |
| Cother m3 | 22.8 | 53.4 | 46.9 | 54.4 | 30.5 | 19.8 | 44.3 | 34.9 | 77.9 |
| Cmirror m3 | 39.6 | 55.8 | 53.0 | 56.2 | 16.2 | 33.3 | 45.7 | 19.4 | 42.0 |
| Tother m3 | 24.9 | 52.6 | 45.6 | 53.7 | 27.7 | 21.3 | 43.8 | 32.9 | 71.3 |
| Tmirror m3 | 45.2 | 55.4 | 52.6 | 55.8 | 10.2 | 37.3 | 45.4 | 14.1 | 26.1 |

Corrected variants only (all except V0): forgetting 12.1-45.2%, paging (P=1000) 44.0-56.2%, paging gain 10-37 pt.

## 2. Per session (P=inf / P=1000)
| variant | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 m1 | 11.0 / 47.4 | 5.5 / 46.8 | 4.9 / 41.0 | 16.4 / 42.7 | 6.5 / 44.3 | 7.5 / 35.8 | 5.5 / 32.6 | 4.8 / 17.7 | 4.9 / 40.3 | 5.9 / 39.8 |
| U3 m1 | 15.0 / 49.7 | 13.1 / 54.4 | 9.4 / 47.3 | 21.4 / 44.2 | 13.1 / 52.1 | 11.4 / 38.5 | 8.6 / 38.5 | 8.7 / 21.2 | 12.8 / 49.6 | 14.1 / 46.8 |
| U4 m1 | 21.0 / 51.8 | 29.5 / 58.9 | 19.9 / 52.8 | 25.7 / 45.6 | 28.6 / 56.7 | 14.3 / 40.2 | 22.6 / 42.9 | 16.1 / 23.6 | 32.1 / 54.5 | 30.5 / 50.6 |
| Cother m1 | 20.8 / 51.5 | 21.0 / 55.7 | 11.2 / 47.4 | 22.4 / 45.4 | 17.3 / 52.2 | 17.3 / 39.9 | 28.5 / 44.1 | 16.0 / 23.6 | 10.4 / 46.1 | 13.1 / 44.3 |
| Cmirror m1 | 50.2 / 55.8 | 34.2 / 58.4 | 35.1 / 55.5 | 36.3 / 47.2 | 30.5 / 55.0 | 37.9 / 43.6 | 19.7 / 37.9 | 8.7 / 20.4 | 29.7 / 52.6 | 30.8 / 49.2 |
| U3+Cmirror m1 | 50.2 / 56.0 | 37.9 / 59.5 | 38.7 / 56.8 | 39.3 / 47.8 | 35.9 / 57.0 | 37.3 / 43.8 | 18.4 / 40.7 | 10.1 / 21.5 | 36.7 / 54.9 | 35.6 / 50.6 |
| Tother m1 | 24.6 / 50.0 | 28.5 / 52.6 | 13.8 / 43.2 | 33.0 / 45.5 | 22.3 / 48.2 | 19.1 / 37.9 | 45.1 / 46.1 | 23.9 / 24.2 | 12.3 / 41.7 | 16.7 / 41.7 |
| Tmirror m1 | 51.9 / 55.4 | 45.6 / 56.9 | 44.8 / 53.5 | 42.6 / 47.7 | 38.5 / 52.9 | 39.1 / 43.3 | 21.3 / 37.0 | 13.8 / 21.0 | 38.5 / 50.1 | 37.9 / 47.9 |
| V0 m3 | 29.2 / 54.3 | 18.5 / 56.6 | 16.6 / 52.2 | 33.8 / 48.0 | 19.8 / 54.7 | 23.1 / 42.4 | 12.7 / 39.8 | 9.0 / 21.5 | 20.2 / 52.5 | 21.0 / 49.0 |
| U3 m3 | 32.0 / 54.8 | 30.5 / 59.7 | 22.5 / 55.2 | 35.9 / 48.2 | 33.6 / 57.7 | 26.4 / 43.1 | 21.1 / 43.3 | 12.1 / 23.1 | 34.5 / 55.4 | 33.3 / 51.1 |
| U4 m3 | 37.8 / 55.6 | 48.2 / 61.2 | 35.9 / 57.5 | 37.1 / 48.6 | 47.7 / 58.9 | 30.0 / 43.6 | 42.4 / 45.4 | 17.8 / 24.0 | 49.4 / 56.5 | 46.1 / 52.0 |
| Cother m3 | 31.7 / 54.8 | 24.8 / 58.7 | 18.8 / 53.6 | 34.8 / 48.1 | 26.1 / 56.4 | 24.3 / 42.7 | 27.4 / 43.7 | 15.3 / 23.3 | 24.1 / 53.7 | 23.2 / 49.6 |
| Cmirror m3 | 51.3 / 56.8 | 39.7 / 60.3 | 41.5 / 57.8 | 42.9 / 48.9 | 36.1 / 57.6 | 39.5 / 44.4 | 20.0 / 41.3 | 9.6 / 21.6 | 39.2 / 55.5 | 38.3 / 51.2 |
| Tother m3 | 34.2 / 54.8 | 29.9 / 58.0 | 20.5 / 52.7 | 34.8 / 48.0 | 27.9 / 55.3 | 24.0 / 42.5 | 31.5 / 42.8 | 19.9 / 23.2 | 26.5 / 52.9 | 24.5 / 49.2 |
| Tmirror m3 | 52.8 / 56.7 | 49.0 / 60.1 | 48.2 / 57.1 | 44.6 / 49.0 | 42.2 / 57.4 | 40.4 / 44.4 | 21.0 / 40.9 | 9.6 / 21.6 | 43.4 / 55.1 | 42.5 / 51.0 |

Per-session paging gain, min / median / max: V0 m1 12.9 / 34.6 / 41.3; U3 m1 12.5 / 33.7 / 41.3; Cother m1
7.7 / 31.0 / 36.2; U4 m1 7.5 / 24.1 / 32.9; Cmirror m1 5.6 / 18.3 / 24.5; Tmirror m1 3.5 / 9.4 / 15.7.
Forgetting (P=inf) above 10% in 2 of 10 sessions under V0 m1, 7/10 under U3 m1, 10/10 under U4, Cother, T*.
In S08 (P=1000 at 18-24% under every variant) and S07 the mirror correction changes little; there the
other-session placebo is the stricter one.

## 3. Status flips: % of V0-reused segments that become never-reused (count; token-weighted)
Same m as V0. Expected value over draws for C variants.
| variant | tool_result | tool_input | persisted_write | assistant_text | user_prompt | harness | ALL |
|---|---:|---:|---:|---:|---:|---:|---:|
| U3 m1 | 29 (8) | 16 (3) | 5 (1) | 25 (5) | 28 (11) | 35 (1) | 22 (5) |
| U4 m1 | 57 (32) | 37 (13) | 27 (7) | 56 (15) | 49 (24) | 42 (10) | 48 (20) |
| Cother m1 | 25 (15) | 10 (5) | 9 (14) | 14 (9) | 29 (17) | 27 (28) | 17 (11) |
| Cmirror m1 | 50 (46) | 50 (50) | 53 (47) | 48 (49) | 44 (42) | 65 (51) | 50 (48) |
| U3+Cmirror m1 | 64 (52) | 59 (54) | 55 (47) | 58 (56) | 55 (51) | 73 (71) | 61 (53) |
| Tother m1 | 39 (29) | 20 (14) | 18 (24) | 26 (21) | 41 (33) | 47 (44) | 29 (22) |
| Tmirror m1 | 68 (68) | 68 (73) | 70 (68) | 65 (70) | 60 (54) | 84 (80) | 68 (70) |
| *V0 m1 reused share* | 77 (95) | 81 (97) | 97 (100) | 87 (96) | 69 (90) | 78 (100) | 80 (96) |
| U3 m3 | 34 (19) | 24 (10) | 16 (4) | 35 (12) | 32 (8) | 2 (1) | 28 (12) |
| U4 m3 | 72 (56) | 53 (34) | 47 (18) | 66 (41) | 58 (20) | 22 (38) | 61 (40) |
| Cother m3 | 9 (9) | 3 (3) | 5 (4) | 2 (3) | 4 (10) | 8 (13) | 5 (6) |
| Cmirror m3 | 47 (45) | 50 (52) | 50 (44) | 39 (54) | 17 (33) | 67 (72) | 47 (49) |
| Tother m3 | 16 (17) | 7 (8) | 12 (16) | 5 (10) | 7 (20) | 19 (35) | 11 (14) |
| Tmirror m3 | 60 (63) | 66 (73) | 67 (64) | 51 (71) | 24 (55) | 87 (89) | 62 (68) |
| *V0 m3 reused share* | 34 (76) | 39 (84) | 80 (97) | 29 (81) | 19 (61) | 48 (99) | 37 (83) |

n segments (V0): tool_result 15,083, tool_input 14,749, assistant_text 4,659, persisted_write 1,328,
user_prompt 1,030, harness 186 (one compact summary, not shown). The vocabulary filters flip mostly small
segments (count >> tokens); the mirror correction flips large and small alike (count ~ tokens), and no kind
is spared: tool results, tool inputs and the agent's own writes lose half their links. Writes are the most
robust kind only under the vocabulary filters.

## 4. Diagnostic (post hoc): reuse is as likely before a segment exists as after
Hit rate per (segment, call), pooled over all segments; real window vs time-mirrored calls before origin vs
other-session sample:
| distance (calls) | m=1 real / mirror / other | m=3 real / mirror / other |
|---|---|---|
| 1-10 | 14.6 / 15.3 / 2.6% | 4.4 / 4.4 / 0.26% |
| 11-100 | 7.1 / 6.7 / 2.6% | 1.6 / 1.5 / 0.26% |
| 101-1000 | 5.3 / 5.0 / 2.7% | 0.93 / 0.92 / 0.28% |

At every distance, the calls after a segment share its tokens at about the rate of the calls before it.
That symmetry is why the mirror placebo removes so much: the lexical link does not distinguish "needed
later" from "the session was talking about this topic around then". Both decay with distance, so the
"reuse" signal is topical locality. The other-session placebo is flat and 2-15x lower, so it removes only
cross-project vocabulary. The pooled symmetry would remove nearly all reuse. The per-segment correction
keeps half of the reused segments (Cmirror) or a third (Tmirror) because some segments do beat their own
mirror, partly by chance (the expected-value thinning keeps positive noise, which the 2-sigma test removes).

## 5. What changes in the synthesis
- **"Carrying is the big lever, forgetting is smaller"** holds only for the mild corrections. Under the
  vocabulary filter U3 and the other-session placebo, forgetting roughly doubles (5.6 to 12-13%, m=1) and
  paging still gains 34-37 points. Under the strict filter (U4) the two are equal (26.5 vs 26.9). Under the
  same-session time placebo, forgetting is the larger part: 33-41% vs a paging gain of 10-21 (m=1), and
  40-45% vs 10-16 (m=3). Across all 14 corrected variants forgetting is **12-45%** (V0 5.6%) and the
  paging gain is **10-37 points** (V0 36). The statement should become: "the split between forgetting and
  paging depends on what counts as reuse; with reuse that has to beat its own topic, forgetting is the
  bigger part."
- **Paging range**: the oracle P=1000 figure *rises* under every correction: **44-56%** (V0 41.5%; synthesis
  range 35-54%). P=0 is 48-57% against a no-reuse ceiling of 57.3%. The total opportunity is robust and,
  if anything, larger. What is not robust is how much of it needs foresight. With the placebo the
  "drop never-used content" row (5.6%, 3.5-24.7%) widens to 12-45%.
- Synthesis section 4.3 ("lexical reuse measures shared vocabulary") extends from A5's 34 compaction
  windows to every segment of all ten sessions, and from cross-session vocabulary to within-session topic.

## Caveats
- No ground truth. The time-mirror placebo over-corrects if pre-birth outputs are the segment's causal
  ancestors (a tool result reads a file the agent just wrote; a tool input names what the text just
  discussed): shared ancestry is not the same as non-use. The other-session placebo under-corrects
  (same user, overlapping projects, but no within-session topic). Treat Cother/U3 (12-13% forgetting)
  and Cmirror/Tmirror (33-41%) as the bracket, not either as the answer.
- The correction is statistical. It removes the expected share of links per segment and does not identify
  which use was genuine. The independent-thinning assumption ignores clustering of real uses. Long windows
  with short pre-birth history fall back to a kind-level mirror rate.
- The thresholds (1e-3, 1e-4) were fixed from a descriptive vocabulary table before the bound was run, but
  are arbitrary. The df uses segments of nine other sessions of the same user, so vocabulary shared by all
  of this user's projects is the target, not the English or programming lexicon at large.
- Reuse in thinking and by reading without quoting stays invisible to every variant (the bound stays
  optimistic in that direction). Unattributed context (pinned) is untouched, which is why every column
  stays below the 57.3% ceiling. One user, ten sessions; MC spread <= 0.3 pt; no session bootstrap.

## Findings
1. lexical-v1 reproduces exactly (5.6 / 41.5 / 46.1). When reuse must beat a vocabulary placebo, forgetting
   alone saves **12-45%** of input instead of 5.6%: 12-13% against cross-session vocabulary (U3, Cother), 27% with
   a strict vocabulary filter, and 33-41% against the session's own pre-birth outputs (m=1).
2. Lexical reuse is time-symmetric: calls *before* a segment exists share its tokens at the same rate as calls
   after it (14.6 vs 15.3% within 10 calls, 5.3 vs 5.0% at 100-1000, m=1). The link measures topical locality,
   not need. 50-68% of V0-reused segments (about half to 70% of tokens) fail their own time placebo, across all kinds.
3. The oracle paging figure is robust and grows: P=1000 is **44-56%** under every correction (P=0 48-57%, ceiling
   57.3%). The paging *gain* over forgetting shrinks from 36 to **10-21 points** under the time placebo.
4. "Carrying is the big lever, forgetting is smaller" survives only cross-session corrections (forgetting 12-13 vs
   paging gain 34-37). Under the strict filter they tie (27 vs 27), and under the same-session placebo forgetting
   is the bigger lever (33-45 vs 10-21). The synthesis should present the split as detector-dependent, and widen the
   "drop never-used content" range to 12-45%.
