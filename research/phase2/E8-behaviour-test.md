> Working memo from cycle E8 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# E8: which definition of "reused" predicts need, judged by behaviour at the 34 real compactions?

Aggregates only. No transcript text, paths, commands or tokens were printed or stored. Paths and commands were
compared as SHA-1 hashes. 10 main sessions, 16,181 calls, 34 compactions in 7 sessions (S01 1, S02 3, S03 14,
S05 3, S06 1, S09 7, S10 5). Scripts and the full tables are kept with the analysis files.

## Method
- **Segments.** Built with `bound.read_trace_lines` and `calibrate`, unchanged; both functions were untouched by
  the concurrent edit of bound.py, and the run asserts this. A mirror traversal (copied from A5 stage 1) gives
  each segment a source key, and asserts that the per-call outputs it rebuilds equal bound's exactly.
- **Dropped segments.** For compaction c, these are the non-unattributed segments with tokens > 0 born in
  [previous compaction, c). This is A5's set.
- **Behavioural label.** The window is calls [c, c + N), N = 50 / 200, cut at the next compaction or session end
  (mean window 50 / 195). A segment is positive when its source is re-obtained in the window. For a path, that
  means a re-read of the same normalised path: the Read tool, or a shell read parsed by D2's parser (A5's rule).
  For a command, it means an exact re-run with the same hash. Populations:
  - **A**: tool results with a key (10,490 per N).
  - **AP**: A restricted to path keys (5,073). **This is the primary test.** Command results are almost never
    re-run exactly (5 / 18 positives among 5,417), so in A any score that separates file reads from command
    output wins by construction. Size does exactly that in A, with AUC 0.68 / 0.72.
  - **B**: A plus keyed tool inputs and writes, where a write's key is the written path (22,839).
- **Predictions.** Each is E5's rule applied to the same window, with each definition's own linking rule:
  - **V0 / U3 / U4 at m = 1, 3**: some window call's output shares at least m distinctive tokens. The excluded
    tokens are the session-common ones, plus user vocabulary with df_other > 1e-3 (U3) or > 1e-4 (U4).
    The score is the maximum number of shared tokens in any one call. A secondary score, the number of calls
    hit at m, is in the full tables.
  - **C\***: r = n_hit / W, with placebo rate p and g = max(0, (r - p) / (1 - p)). As in E5, each hit is kept
    with probability g / r, so P(predicted) = 1 - (1 - g/r)^n_hit and the score is r - p.
    - Cother uses E5's own sample of 1,000 other-session calls (seed 0).
    - Cmirror uses time-mirrored pre-birth calls at the same distances as the window calls. When none exist, it
      falls back to the session's pooled rate for the segment's kind (8% of AP segments).
    - Cmirror5 uses E5's per-segment in-cycle mirror rate, as a sensitivity check.
  - **T\***: positive when n_hit > pW + 2 sqrt(W p(1 - p)); the score is z.
  - **U3+Cmirror m1**: Cmirror applied on top of U3.
- **Baselines.** Recency (score = -age in calls at c; median age 230) and size (calibrated tokens). There is also
  a matched baseline: in each compaction, the k youngest segments, with k equal to the definition's predicted
  count.
- **Mode "dec".** This repeats the test with the re-fetching call's own tool-input tokens removed from the
  outputs. It removes the mechanical hit that a re-read creates for itself.
- **Metrics.** Pooled metrics are given over all segments, and medians over compactions. Uncertainty comes from
  a compaction-cluster bootstrap (200 reps), leave-one-session-out runs (LOSO), and per-session AUC.

## 1. Primary test: path-keyed tool results (AP)
Prevalence is 45.8% at N = 50 and 65.2% at N = 200. Pooled values; "med" = median over the 33 / 34 compactions
that have both classes.

**N = 50**
| definition | E5 forgetting % | share pred+ % | precision % | recall % | lift | AUC | med prec / rec % | med AUC (AUC > 0.5) | recency at same share, prec % |
|---|---|---|---|---|---|---|---|---|---|
| V0 m1 | 5.6 | 57.0 | 51.1 | 63.6 | 1.11 | **0.574** | 45.9 / 69.5 | 0.614 (30/33) | 48.2 |
| U3 m1 | 12.1 | 28.9 | 53.5 | 33.8 | 1.17 | 0.547 | 52.4 / 38.5 | 0.588 (31/33) | 47.8 |
| U4 m1 | 26.5 | 9.9 | 53.6 | 11.5 | 1.17 | 0.516 | 54.1 / 15.2 | 0.528 (26/33) | 45.6 |
| Cother m1 | 13.4 | 29.2 | 55.5 | 35.4 | 1.21 | 0.560 | 51.6 / 38.1 | 0.641 (26/33) | 50.2 |
| Tother m1 | 16.8 | 15.8 | 59.8 | 20.6 | 1.31 | 0.560 | 61.2 / 19.7 | 0.639 (26/33) | 49.3 |
| Cmirror m1 | 32.8 | 22.3 | 52.6 | 25.6 | 1.15 | 0.521 | 46.8 / 24.9 | 0.510 (18/33) | 54.7 |
| U3+Cmirror m1 | 37.5 | 14.0 | 57.2 | 17.5 | 1.25 | 0.532 | 47.5 / 18.2 | 0.546 (20/33) | 52.8 |
| Tmirror m1 | 41.3 | 15.9 | 52.8 | 18.4 | 1.15 | 0.525 | 47.1 / 16.2 | 0.512 (19/33) | 56.6 |
| V0 m3 | 19.3 | 14.4 | 54.9 | 17.3 | 1.20 | 0.574 | 56.7 / 20.1 | 0.614 (30/33) | 48.9 |
| U3 m3 | 29.8 | 5.4 | 62.7 | 7.4 | 1.37 | 0.547 | 73.2 / 5.3 | 0.588 (31/33) | 48.2 |
| U4 m3 | 43.4 | 1.8 | 66.7 | 2.6 | 1.46 | 0.516 | 80.0 / 0.0 | 0.528 (26/33) | 44.4 |
| Cother m3 | 22.8 | 10.6 | 58.6 | 13.6 | 1.28 | 0.485 | 59.2 / 15.0 | 0.548 (21/33) | 48.8 |
| Tother m3 | 24.9 | 8.0 | 61.9 | 10.8 | 1.35 | 0.485 | 65.5 / 10.4 | 0.547 (21/33) | 48.4 |
| Cmirror m3 | 39.6 | 7.7 | 56.0 | 9.4 | 1.22 | 0.514 | 61.7 / 9.1 | 0.492 (16/33) | 51.2 |
| Tmirror m3 | 45.2 | 6.3 | 58.6 | 8.0 | 1.28 | 0.514 | 61.1 / 8.3 | 0.494 (15/33) | 55.8 |
| recency | | | | | | 0.488 | | 0.542 (19/33) | |
| size | | | | | | 0.539 | | 0.586 (24/33) | |

**N = 200**
| definition | E5 forgetting % | share pred+ % | precision % | recall % | lift | AUC | med prec / rec % | med AUC (AUC > 0.5) | recency at same share, prec % |
|---|---|---|---|---|---|---|---|---|---|
| V0 m1 | 5.6 | 80.4 | 69.2 | 85.4 | 1.06 | **0.612** | 66.3 / 86.6 | 0.629 (31/34) | 66.2 |
| U3 m1 | 12.1 | 54.8 | 72.5 | 60.9 | 1.11 | 0.596 | 71.5 / 64.6 | 0.625 (33/34) | 66.2 |
| U4 m1 | 26.5 | 22.5 | 70.3 | 24.2 | 1.08 | 0.527 | 71.0 / 24.9 | 0.551 (27/34) | 63.2 |
| Cother m1 | 13.4 | 47.9 | 70.6 | 51.9 | 1.08 | 0.558 | 71.5 / 59.5 | 0.608 (24/34) | 66.8 |
| Tother m1 | 16.8 | 31.6 | 72.6 | 35.1 | 1.11 | 0.559 | 75.3 / 43.8 | 0.617 (25/34) | 66.6 |
| Cmirror m1 | 32.8 | 29.2 | 69.0 | 30.9 | 1.06 | 0.497 | 64.6 / 30.2 | 0.488 (14/34) | 69.8 |
| U3+Cmirror m1 | 37.5 | 23.0 | 73.6 | 26.0 | 1.13 | 0.513 | 74.0 / 25.9 | 0.496 (16/34) | 70.0 |
| Tmirror m1 | 41.3 | 19.1 | 66.6 | 19.5 | 1.02 | 0.505 | 66.7 / 20.4 | 0.488 (15/34) | 71.0 |
| V0 m3 | 19.3 | 34.3 | 74.3 | 39.1 | 1.14 | 0.612 | 74.2 / 43.1 | 0.629 (31/34) | 67.8 |
| U3 m3 | 29.8 | 17.1 | 76.0 | 20.0 | 1.17 | 0.596 | 80.2 / 24.7 | 0.625 (33/34) | 61.2 |
| U4 m3 | 43.4 | 6.2 | 75.6 | 7.1 | 1.16 | 0.527 | 86.7 / 3.4 | 0.551 (27/34) | 55.4 |
| Cother m3 | 22.8 | 25.1 | 73.8 | 28.4 | 1.13 | 0.491 | 74.5 / 31.6 | 0.554 (22/34) | 65.1 |
| Tother m3 | 24.9 | 19.1 | 73.6 | 21.6 | 1.13 | 0.492 | 75.7 / 18.1 | 0.563 (22/34) | 61.0 |
| Cmirror m3 | 39.6 | 14.6 | 76.7 | 17.2 | 1.18 | 0.498 | 76.7 / 15.0 | 0.485 (15/34) | 69.9 |
| Tmirror m3 | 45.2 | 11.4 | 76.6 | 13.4 | 1.17 | 0.499 | 78.9 / 11.5 | 0.487 (15/34) | 71.4 |
| recency | | | | | | 0.497 | | 0.501 (17/34) | |
| size | | | | | | 0.591 | | 0.571 (28/34) | |

V0, U3 and U4 share one score (maximum shared tokens per call), so their AUC does not depend on m. The secondary
score, the number of calls hit, gives V0 m1 an AUC of 0.583 / 0.624. In the sensitivity check, Cmirror5 and
Tmirror5 (E5's in-cycle mirror rate) score 0.46-0.52 at both N.

## 2. Confirmed need that each rule calls "unused" (AP)
| definition | E5 forgetting % | N=50: confirmed need predicted unused % | re-read among predicted-unused % (base 45.8) | N=200: confirmed need predicted unused % | re-read among predicted-unused % (base 65.2) |
|---|---|---|---|---|---|
| V0 m1 | 5.6 | 36.4 | 38.8 | 14.6 | 48.6 |
| U3 m1 | 12.1 | 66.2 | 42.7 | 39.1 | 56.4 |
| Cother m1 | 13.4 | 64.6 | 41.8 | 48.1 | 60.3 |
| Tother m1 | 16.8 | 79.4 | 43.2 | 64.9 | 61.8 |
| V0 m3 | 19.3 | 82.7 | 44.3 | 60.9 | 60.5 |
| U4 m1 | 26.5 | 88.5 | 44.9 | 75.8 | 63.7 |
| Cmirror m1 | 32.8 | 74.4 | 43.8 | 69.1 | 63.6 |
| U3+Cmirror m1 | 37.5 | 82.5 | 43.9 | 74.0 | 62.7 |
| Tmirror m1 | 41.3 | 81.6 | 44.5 | 80.5 | 64.9 |
| Tmirror m3 | 45.2 | 92.0 | 44.9 | 86.6 | 63.7 |

Under the mirror and strict rules, segments predicted "unused" are re-read at almost the base rate (63-65% vs
65.2% at N = 200). Their extra "unused" segments therefore look like a random sample of the confirmed-need
segments.

## 3. Robustness (AP)
| check | V0 m1 | U3 m1 | Cother m1 | Tother m1 | Cmirror m1 | Tmirror m1 | U4 m1 | recency | size |
|---|---|---|---|---|---|---|---|---|---|
| AUC, N=50, bootstrap 95% | 0.574 (0.549-0.604) | 0.547 (0.522-0.577) | 0.560 (0.519-0.609) | 0.560 (0.519-0.610) | 0.521 (0.486-0.554) | 0.525 (0.488-0.557) | 0.516 (0.502-0.541) | 0.488 (0.441-0.535) | 0.539 (0.506-0.569) |
| AUC, N=200, bootstrap 95% | 0.612 (0.578-0.650) | 0.596 (0.562-0.634) | 0.558 (0.516-0.604) | 0.559 (0.514-0.602) | 0.497 (0.462-0.534) | 0.505 (0.472-0.544) | 0.527 (0.506-0.551) | 0.497 (0.440-0.553) | 0.591 (0.557-0.628) |
| LOSO min-max, N=200 (drop S03 etc.) | 0.582-0.637 | 0.564-0.633 | 0.525-0.611 | 0.530-0.611 | 0.482-0.520 | 0.491-0.526 | 0.508-0.551 | 0.471-0.527 | 0.565-0.611 |
| one youngest segment per compaction x path, AUC N=50 / 200 | 0.604 / 0.660 | 0.588 / 0.654 | 0.596 / 0.613 | 0.595 / 0.612 | 0.510 / 0.509 | 0.514 / 0.517 | 0.554 / 0.578 | 0.521 / 0.541 | 0.571 / 0.606 |
| size-stratified AUC (quintiles), N=50 / 200 | 0.561 / 0.564 | 0.542 / 0.558 | 0.556 / 0.545 | 0.558 / 0.546 | 0.532 / 0.519 | 0.533 / 0.523 | 0.515 / 0.511 | 0.488 / 0.506 | 0.500 / 0.518 |
| decoupled (re-fetch inputs removed), AUC N=50 / 200 | 0.558 / 0.606 | 0.528 / 0.583 | 0.528 / 0.530 | 0.528 / 0.534 | 0.495 / 0.465 | 0.500 / 0.475 | 0.505 / 0.515 | same | same |

Bootstrap AUC differences:
| comparison | N = 50 | N = 200 |
|---|---|---|
| V0 m1 minus Cmirror m1 | +0.055 (0.022-0.091) | +0.119 (0.064-0.176) |
| V0 m1 minus size | +0.035 (0.001-0.070) | +0.020 (-0.009-0.047) |
| V0 m1 minus U3 m1 | +0.026 (0.007-0.046) | +0.016 (-0.003-0.035) |
| V0 m1 minus Tother m1 | +0.015 (-0.017-0.043) | +0.054 (0.024-0.087) |

**Per session (AP, AUC N = 50 / 200).** Positives per session: S01 2 / 3, S02 79 / 174, S03 589 / 1003,
S05 247 / 406, S06 4 / 4, S09 825 / 1063, S10 577 / 655.

| definition | S01 | S02 | S03 | S05 | S06 | S09 | S10 |
|---|---|---|---|---|---|---|---|
| V0 m1 | 0.87 / 0.65 | 0.63 / 0.57 | 0.64 / 0.69 | 0.59 / 0.63 | 0.54 / 0.48 | 0.52 / 0.54 | 0.60 / 0.64 |
| Cmirror m1 | 0.73 / 0.67 | 0.59 / 0.58 | 0.49 / 0.50 | 0.53 / 0.51 | 0.44 / 0.45 | 0.55 / 0.53 | 0.45 / 0.38 |

V0 m1 has the higher AUC in 6/7 sessions at N = 50 and 5/7 at N = 200. S01 and S06 have 2-4 positives each.

**Other populations.**
- **A** (with command results). This population is dominated by the split between path and command results:
  - Size: AUC 0.683 / 0.719.
  - V0: 0.643 / 0.707. U3: 0.579 / 0.654. Cother m1: 0.539 / 0.570.
  - Cmirror m1: 0.493 / 0.472. Tmirror m1: 0.496 / 0.479.
  - Recency: 0.441 / 0.440. Older segments are slightly *more* likely to be re-obtained.
  - V0 m1 precision / recall: 31.3 / 63.6% (N = 50, prevalence 22.2%) and 39.7 / 85.4% (N = 200, prevalence 31.7%).
  - Excluding S03 (pooled, N = 50 / 200): V0 0.633 / 0.690 and Cmirror m1 0.507 / 0.485, the same ordering.
- **B** (adds tool inputs and writes). All rules are close to chance:
  - V0: 0.521 / 0.530. Cother m1: 0.533 / 0.520.
  - Cmirror m1: 0.554 / 0.528. Tmirror m1: 0.556 / 0.531. Cmirror5 m1: 0.580 / 0.570.
  - Recency: 0.452 / 0.447. Size: 0.477 / 0.494.
  - In B the mirror rules are slightly *above* V0. Tool inputs carry their own path, and a re-read call's input
    names that path again, so V0's link saturates on them: V0 m1 predicts 47 / 69% positive at a precision of
    22 / 32% against prevalences of 20.8 / 30.1%. B is a poor test of need. AP is the clean one.

## Bias of the behavioural label (read before using any number above)
- **What a positive misses.** A positive means "re-read the same path within N calls". It misses need that was met
  in other ways:
  - by the compaction summary;
  - by the files the harness re-injects after compaction (about 22k tokens per compaction, A5);
  - by inference or memory;
  - by another route (a different command, a different path spelling, a script reading the file).

  It also misses all need for command output, because exact re-runs are rare.
- **What a positive wrongly includes.** Some re-reads are habit, not need for the dropped content. A5's mid-cycle
  control re-reads about a third as much without any compaction. Some re-reads fetch a newer version of a file
  the agent edited, so the old segment was stale, not needed.
- **Precision.** "False positives" are partly real need (met by the summary or re-injection), so precision is a
  lower bound in that respect. Habitual and stale re-reads inflate it a little.
- **Recall.** Recall, and its complement "confirmed need predicted unused", is measured only on confirmed need. As
  a measure of how much need a rule catches it is a lower bound on need (need met by the summary is unobserved).
  For the confirmed subset, though, it is a direct count of need that a rule would have dropped. Summarised need
  is probably mentioned more often, so every rule's recall on all need is likely higher. That does not rescue the
  mirror rules, which are at chance on the confirmed part.
- **Share predicted positive** does not depend on the label.
- **AUC.** If the label noise is unrelated to the score, it pulls every AUC toward 0.5 by a similar amount. The
  levels (0.50-0.66) are then lower bounds on discriminative power, and the ranking across definitions is more
  reliable than the levels.
- **Mechanical coupling.** A re-read's own tool input can create the lexical hit. Removing it ("dec") lowers V0's
  AUC by only 0.006-0.016, so V0's signal is not mainly self-generated.
- **Sample and transfer.** The data are one user, 34 events, and 7 sessions, with S03 holding 14 of 34
  compactions and 34% of AP segments. Compactions are not independent. The cluster bootstrap and LOSO cover part
  of this; the per-session pattern holds in 5-6 of 7 sessions. This test checks each rule's prediction across a
  compaction; E5's forgetting share uses the same rule over the segment's whole in-cycle window. Carrying a rule's
  validity from one to the other is an assumption.

## Which definition does behaviour favour?
- **Rankers.** The lexical count with only cross-session vocabulary removed carries a weak but real signal about
  what the agent re-fetches: V0, U3, Cother and Tother at m1 score AUC 0.55-0.61 (0.59-0.66 per unique source).
  V0's raw count is the best ranker at both N, though not significantly better than U3 at N = 200 or Tother at
  N = 50. V0 beats size by 0.02-0.035 (significant only at N = 50), and recency has no signal (0.49-0.50).
- **The same-session time placebo.** Cmirror, Tmirror and U3+Cmirror all sit at AUC 0.50-0.53 with intervals that
  include 0.5. Cmirror and Tmirror are also below recency at the same share (precision 52.6-52.8 vs 54.7-56.6
  at N = 50; 66.6-69.0 vs 69.8-71.0 at N = 200). At N = 200, Cmirror m1's AUC is 0.12 below V0's
  (0.06-0.18). U4 (0.52-0.53) is close to chance too. These corrections remove the predictive part along with the
  vocabulary: the topical locality that E5 found to be time-symmetric is also what predicts re-reading.
- **Binary rules.** Precision barely rises as a rule gets stricter: lift is 1.06-1.46, and AP precision is
  51 → 54-67% at N = 50. Recall collapses: 64 → 3-26%.
- **As a keep/drop rule, V0 m1 is the only one that keeps most confirmed need:** 85% at N = 200, against 61% for
  U3 m1, 52% for Cother, 35% for Tother and 31% for Cmirror.
- **Implied forgetting share.** The behavioural evidence supports the V0 / U3 / Cother band, that is, **about
  5.6% (V0 m1) to 12-13% (U3 m1, Cother m1)** of input saved by forgetting alone. Tother (16.8%) is the edge of
  what the evidence allows. It does not support the 27-45% figures from U4 and the mirror corrections.
- **Caution on V0's own forgetting share.** Even the V0 m1 "unused" set is leaky: 49% of the segments it predicts
  unused at N = 200 are re-read within 200 calls (base rate 65%). Lexical "never reused" is therefore not "never
  needed", even at 5.6%.

## Findings
1. Behaviour favours the permissive definitions. V0 and U3, Cother and Tother at m1 rank the path segments the
   agent re-reads after compaction better than chance (AUC 0.55-0.61; V0 is best at 0.574 / 0.612). The
   same-session mirror corrections (Cmirror, Tmirror, U3+Cmirror) and U4 do no better than chance
   (AUC 0.50-0.53; V0 minus Cmirror is +0.12, 95% interval 0.06-0.18, at N = 200).
2. Stricter rules buy almost no precision: lift over prevalence is 1.06-1.46, and AP precision is 51-67% against a
   base of 46%. Recall falls instead: 64 → 3-26% at N = 50. Mirror and strict rules call 69-93% of the
   confirmed-need segments "unused" at N = 200, against 15% for V0 m1.
3. The forgetting share this supports is about **5.6-13%** (V0 m1 to U3 / Cother m1; Tother's 16.8% at most), not
   E5's 33-45%. Even V0's "unused" set is leaky: 49% of it is re-read within 200 calls (base 65%).
4. The lexical signal is weak in absolute terms. It is not made up of the re-read call's own tokens (removing them
   costs 0.006-0.016 AUC), and it beats segment size only narrowly (+0.02-0.035). Recency carries no information
   (AUC 0.49-0.50).
5. The label misses need met by the summary, re-injection or inference, so recall-type numbers are lower bounds on
   need and some "false positives" are real need. Habitual and stale re-reads push the other way. S03 holds 14 of
   34 compactions, but the ordering holds with any single session left out and in 5-6 of 7 sessions.
