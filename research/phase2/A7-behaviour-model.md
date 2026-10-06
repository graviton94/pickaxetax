> Working memo from cycle A7 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# A7: a behaviour-fitted need model, and the forgetting share it implies

**Exploratory, not pre-registered.** I chose the models, variants and thresholds after seeing E8. This memo
holds aggregates only. No transcript text, paths, commands or tokens were printed or stored. Paths were
SHA-1 hashed in memory only, and the stored pickles hold numbers and category labels. No token-set trace
was written to disk. 10 main sessions (16,181 calls); 34 compactions in 7 sessions. Scripts and the full tables are kept with the analysis files.


## Method
1. **Training data: E8's population AP, rebuilt and checked.**
   - The rows are path-keyed tool results dropped at each compaction: 5,073 per N.
   - Label: the same path is re-read in [c, c+N), N = 50 / 200, with the window cut at the next compaction.
   - The rebuild reproduces E8: prevalence 45.8 / 65.2%, V0 AUC 0.574 / 0.612, size AUC 0.539 / 0.591.
   - Features with no information from after the compaction:
     - log size and log age (calls since birth);
     - instruction distance (instructions started between origin and c);
     - prior reads of the same path before the segment's own read (**prior**);
     - reads of the same path between the segment and c (**newer**, which means a newer copy exists);
     - whether the agent edited the file, before and since the segment's birth;
     - read route (Read tool or shell);
     - number of paths in the key.
   - **Lexical features use information from after the compaction**, as the bound itself does:
     - V0 and U3 maximum shared tokens per call, and calls hit;
     - the Cother-adjusted hit rate (r − p_other, using E5's 1,000-call sample, seed 0);
     - log W;
     - "dec" variants, which drop the re-reading call's own input.
2. **Models.** Ridge-logistic regression (Newton/IRLS, standard library only) on standardised features:
   - *no-foresight*: path history, size, age, instruction distance, edits.
   - *lexical*.
   - *all*: both of the above.
   - *transfer*: V0 max / hits, Cother-adjusted rate, size, age, instruction distance, W. Every segment of the
     bound has these features.
   - *size+age*.

   Evaluation:
   - out-of-fold AUC by leave-one-session-out (LOSO, 7 folds) and leave-one-compaction-out (LOCO, 34 folds);
   - per-session and per-compaction AUC;
   - Brier score, log loss, and LOSO decile calibration;
   - a compaction-cluster bootstrap (200 reps) of the out-of-fold AUC and of its difference from V0.
3. **Habit control (added).** I placed mid-cycle pseudo-boundaries every 150 calls inside every cycle: 68
   boundaries, 6,673 rows per N. Population and label follow the same rule, but the content is still in
   context, so any re-read there is habit or a refresh. I then:
   - applied the models fitted at compactions to these rows;
   - fitted a pooled compaction + mid-cycle model with a "dropped" indicator, with and without interactions
     with V0 and prior reads;
   - ran a session bootstrap of that pooled fit (30 reps).
4. **Bound translation.**
   - **Blocks.** Each segment's lexical-v1 refs after birth are cut into blocks of N calls, starting at
     birth + 1. A block is the bound-side analogue of one training row: "dropped at the block start, needed
     in the next N calls?". Its age is the block start minus the origin.
   - **Rule.** A block's refs are kept if its score clears the threshold at which the share predicted
     positive in training equals the behavioural base rate; otherwise they are removed. Refs are only ever
     removed, never added.
   - **Primary rule: "V0 hits, calibrated".** The score is the number of window calls that share at least one
     distinctive token: E8's best lexical ranker, which no fitted lexical model beat out of session (§1).
     - N = 50: keep blocks with ≥ 2 hits, and blocks with exactly 1 hit with probability 0.35.
     - N = 200: keep blocks with ≥ 4 hits, and blocks with 3 hits with probability 0.65.
     - Monte Carlo over 10 draws.
   - **Other variants:**
     - the transfer model (base-rate threshold, p ≥ 0.5, or an expected-need weight of P(keep) = p);
     - the path model (no-foresight + V0 features) on path-keyed tool results only;
     - thinning restricted to tool results.
   - **Need computation.** Need is recomputed with `bound.needed`'s formula.
     - The deterministic variants were validated: running `bound.bound` / `merge` unchanged on a freshly
       parsed trace with the refs thinned in the same way gives identical results to 0.1 pt.
     - With nothing thinned, the result is 5.6 / 41.5 / 46.1, which reproduces lexical-v1.
   - **Intervals: session bootstrap, 200 reps.** The 10 sessions are resampled with replacement and the pooled
     share recomputed, (i) with the model fixed, and (ii) with the model and threshold refitted on the drawn
     sessions' compactions, row-weighted.

## 1. Can a fitted model predict re-reads better than V0? (AP, out of fold)
| score | AUC LOSO N=50 / 200 | AUC LOCO | median per-session AUC | 95% interval (comp. bootstrap) | minus V0 (95%) |
|---|---|---|---|---|---|
| V0 max shared (E8, no fit) | 0.574 / 0.612 | same | 0.60 / 0.63 | (E8) 0.55-0.60 / 0.58-0.65 | — |
| prior reads alone (no fit) | **0.838 / 0.867** | same | 0.75 / 0.80 | | |
| no-foresight model | 0.851 / 0.883 | 0.856 / 0.879 | 0.76 / 0.81 | 0.81-0.89 / 0.85-0.92 | +0.28 (+0.22 to +0.34) / +0.27 (+0.22 to +0.32) |
| **all (no-foresight + lexical)** | **0.873 / 0.892** | 0.875 / 0.890 | 0.80 / 0.84 | 0.84-0.90 / 0.86-0.92 | +0.30 (+0.25 to +0.35) / +0.28 (+0.23 to +0.33) |
| lexical only (fitted) | 0.467 / 0.542 | 0.539 / 0.608 | 0.61 / 0.60 | 0.43-0.53 / 0.50-0.60 | −0.10 / −0.07 (both below 0) |
| transfer (lexical + size/age/instr) | 0.561 / 0.483 | 0.634 / 0.573 | 0.61 / 0.58 | 0.48-0.64 / 0.44-0.54 | −0.01 (−0.08 to +0.07) / −0.12 (−0.18 to −0.07) |
| size+age | 0.376 / 0.494 | 0.480 / 0.570 | 0.56 / 0.56 | | |

- **Path history dominates.** In the "all" model (per SD), prior reads carry +1.19 / +1.48, newer copies
  +0.88 / +0.91, and instruction distance −0.71 (N = 50). The lexical terms are +0.1 to +0.4.
- **Lexical features add little.** Over no-foresight they add +0.02 / +0.01 AUC.
- **The "all" model is the best ranker:**
  - per session, 0.74-0.95 in 6 of 7 sessions; S01, with 2-4 positives, is unstable;
  - on the latest copy of each path (newer = 0, n = 1,181), 0.82 / 0.84, against V0's 0.63 / 0.67.
- **Calibration.** LOSO deciles are well calibrated for "all": predicted 0.02 → 0.97 against observed
  0.04 → 0.96 at N = 50, and 0.08 → 0.99 against 0.07 → 0.99 at N = 200. The transfer model is flat, and
  inverted at N = 200 (top decile: predicted 0.85, observed 0.59).
- **Fitted lexical weights do not transfer across sessions.** Pooled LOSO AUC falls below V0's unfitted count.
  Within sessions the fitted models rank about as well as V0 (median 0.58-0.61), but their scales differ
  between sessions.

## 2. Is what the model predicts "need"? Mid-cycle control
| | N = 50 | N = 200 |
|---|---|---|
| re-read prevalence, after compaction vs mid-cycle (content still in context) | 45.8 vs 48.5% | 65.2 vs 62.6% |
| "all" model fitted at compactions, AUC on mid-cycle rows | 0.870 | 0.862 |
| prior reads alone, AUC mid-cycle | 0.836 | 0.855 |
| drop effect net of features, log-odds (session bootstrap) | +0.79 (+0.32 to +1.45) | +0.54 (+0.19 to +1.08) |
| excess re-read probability from the drop, mean over dropped segments | **10.2 pt** (3.5-18.4) of 45.8% | **6.7 pt** (1.9-13.4) of 65.2% |
| excess with V0 hit / without (interaction model) | 12.4 / 6.2 pt | 7.8 / 2.5 pt |
| drop × log V0 max / hits / prior (log-odds; intervals include 0) | +0.34 / +0.03 / −0.07 | −0.00 / +0.19 / +0.04 |

The behavioural label is mostly the agent's re-reading habit for frequently used files, and that habit does not
depend on whether the content was dropped:
- The compaction-fitted model predicts mid-cycle re-reads just as well, and the raw rates are the same.
- Net of the features, dropping adds only about 7-10 points of re-read probability, about 10-22% of the
  positives.
- That added part leans towards segments with a lexical hit (12 vs 6 pt at N = 50), but the interaction
  intervals include 0.

The 0.87-0.89 AUC is therefore a much better predictor of **re-reading**, not demonstrably of **need for
the dropped content**.

## 3. Forgetting share (P = inf) implied for the whole bound (% of measured main-session input)
| variant | N=50: P=inf (95%, fixed / refit) | P=1000 | N=200: P=inf (95%, fixed / refit) | P=1000 | V0-reused segments that lose all later refs, count / tokens % (N=50; N=200) |
|---|---|---|---|---|---|
| lexical-v1 (keep all) | 5.6 (5.1-6.8) | 41.5 | 5.6 (5.1-6.8) | 41.5 | 0 |
| **V0 hits, calibrated to base rate (primary)** | **7.1** (6.5-8.5 / 5.4-10.9) | 41.7 | **7.7** (7.1-9.4 / 6.0-10.5) | 41.7 | 8 / 2; 24 / 7 |
| same, tool results only | 6.3 (5.9-7.5 / 5.4-8.5) | 41.6 | 6.7 (6.2-8.0 / 5.7-8.5) | 41.6 | 4 / 1; 10 / 3 |
| V0 hits ≥ k (k = 2 / 4, no tie-break) | 8.1 (7.5-9.9 / 5.5-11.8) | 41.9 | 8.4 (7.6-10.1 / 6.4-11.1) | 41.8 | 15 / 4; 29 / 9 |
| path model on path tool results, V0 elsewhere | 8.5 (7.3-10.3 / 7.8-11.1) | 42.3 | 9.5 (7.7-12.8 / 6.7-12.3) | 42.4 | 3 / 2; 5 / 5 |
| transfer model, base-rate threshold* | 8.4 (7.2-10.0 / 7.3-10.7) | 42.2 | 23.4 (20.4-26.6 / 6.8-29.8) | 46.9 | 12 / 3; 49 / 45 |
| transfer, tool results only* | 6.9 | 41.7 | 12.5 | 43.2 | |
| transfer, p ≥ 0.5* | 9.9 | 42.6 | 20.5 | 46.0 | |
| transfer, expected-need weight* | 11.7 (10.5-13.4) | 45.7 | 24.7 (22.2-27.9) | 47.6 | |
| path model + transfer elsewhere* | 10.5 | 42.8 | 22.7 | 46.7 | |
| sensitivity: V0 hits calibrated to half the base rate | 13.1 (12.1-15.5) | 43.0 | 15.8 (14.7-18.2) | 43.4 | |
| sensitivity: V0 hits calibrated to the drop-attributable rate (10.2 / 6.7%) | 19.1 (17.7-22.0) | 44.6 | 31.8 (30.1-35.5) | 47.8 | |

\* The transfer model does not beat V0 out of session and is miscalibrated (§1). Its N = 200 numbers depend on
the threshold and are unstable under refit (6.8-29.8), so they are shown as sensitivity only.

Further results:
- **Per session** (primary rule, N = 50): P = inf is 5.3-20.3%. S04 has the highest share (20.3), then S01
  (14.3); the other eight are 5.3-9.3.
- **Other policies.** P = 10000 moves from 22.6 to 23.8%, and P = 0 from 46.1 to 46.2%.
- **Status flips.** Under the primary rule, a V0-reused segment loses all its later refs mostly when it is
  small: 8 / 24% by count, but only 2 / 7% by tokens. Writes are flipped least (2.5 / 6.9% by count).

## Caveats
- **The label is a lower bound on need.** It misses need met by the summary, by the files the harness
  re-injects (about 22k tokens per compaction, A5), by inference, or by another route. Command output is not in
  the AP population at all. File re-reads are only one route of need.
- **Habit inflates the positives, and §2 shows it dominates them.** The rates match those in mid-cycle
  windows, path history predicts both, and the drop adds only 7-10 points. Calibrating the bound to the raw
  base rate therefore treats habitual re-reads as need, so the forgetting share is understated. The
  habit-net calibration (19-32%) goes the other way: it treats only re-reads caused by the drop as need, and
  ignores need met by the summary or re-injection. It also equates a probability difference with a base rate.
  Read the two as brackets, not estimates.
- **Transfer is assumed.**
  - The model is fitted at compactions on file-read tool results, after their content was dropped. It is
    applied to every segment kind while the segment is still in context, with blocks of N calls standing in
    for a drop at each block start.
  - Lexical hits in context and hits after a drop are different populations. The block scores of small
    segments (tool inputs, text) fall outside the training range.
  - The tool-results-only variants (6.3-6.9% under the hits rule) limit this extrapolation.
  - Thinning can only raise forgetting. Need with no lexical trace is never added: 36% of N = 50 positives
    have no V0 hit at all (E8).
- **Sample.** One user, 7 sessions with compactions, and 34 compactions. S03 holds 14 compactions and 34% of
  rows, and S04, S07 and S08 have no AP rows. In the refit bootstrap, the S01 / S06 folds have 2-4 positives.
  The threshold choice (base rate), the block length (N) and the mid-cycle spacing (150 calls) were all chosen
  post hoc.
- **Intervals.** The session bootstrap with the model fixed ignores model uncertainty; the refit bootstrap
  includes it, which is why its intervals are wider.

## Findings
1. Behaviour can be predicted far better than by lexical reuse: a logistic model with path history (prior reads,
   newer copies) reaches out-of-session AUC 0.87 / 0.89 (N = 50 / 200), against V0's 0.57 / 0.61 (+0.28-0.30, 95% interval
   +0.23 to +0.35), and is well calibrated. Lexical features add only about 0.01-0.02. Fitted lexical-only models do not beat
   V0's raw count out of session (pooled LOSO AUC 0.47-0.56).
2. What it predicts is mostly habit, not need. The same model predicts re-reads equally well when nothing was dropped
   (mid-cycle AUC 0.86-0.87; prevalence 48.5 / 62.6% vs 45.8 / 65.2%). The drop itself adds about 10 / 7 points of re-read
   probability (95% 3.5-18 / 2-13), roughly 10-22% of the positives.
3. Calibrating V0's hit count to the behavioural base rate gives a forgetting share of **7.1% (N = 50) and 7.7% (N = 200)**.
   Session bootstrap: 6.5-8.5 and 7.1-9.4 with the model fixed, 5.4-10.9 and 6.0-10.5 refitted. Paging (P = 1000) stays at
   41.7%.
4. Credible variants span 6.3-10.5% (tool-results-only, path model, strict k). This sits inside E8's 5.6-13% and close to
   lexical-v1's 5.6%. Only the unvalidated transfer model at N = 200 (20-25%) and the habit-net calibration (19-32%) go
   higher.
5. Behaviour calibrated to raw re-reads therefore supports "forgetting is small, about 6-11%, and carrying is the larger
   lever". That rests on counting habitual re-reads as need. If only drop-attributable re-reads count, the share rises
   towards 13-32%. The behavioural data cannot separate the two, because of habit and the unobserved summary channel.
