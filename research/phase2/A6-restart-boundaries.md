> Working memo from cycle A6 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# A6: can a no-foresight rule pick safer restart boundaries, and what does it cost?

## 0. Pre-specified design (written after building the features, before any outcome was looked at)

**Boundaries.** Instruction boundaries b (first call of instruction j+1; unique `bound` instruction
starts, identical to the dataset-v2 series starts) whose observed context at call b-1 is > 200k: 582
(A4's set). All 657 boundaries carry features and outcomes so that any boundary the replay restarts
can be scored.

**Outcome (hindsight, used only to evaluate).** Sources = files read or written (Read / Edit / Write
/ shell reads, D2's parser, normalised path) and commands (exact whitespace-normalised hash, plus
Grep/Glob signatures) used since the last compaction before b (A5's primary set; variant: all
history). Re-obtaining = a Read of a source path, or an exact re-run of a source command, counted
once per item (A5's "distinct").
- **Y (primary)**: at least one re-obtaining in instruction j+1, the window cut at the next
  compaction.
- Y50: the same in the next 50 calls (cut at the next compaction or session end).
- Yall: primary window, all-history sources.
- Token-weighted: re-obtained tokens (calibrated result size of the first re-obtaining of each
  item; images 0). "Heavy" = at least 10k re-obtained tokens in the primary window.

**Signals at b (no foresight), each with a direction fixed in advance (score oriented so that a
higher score = more expected need = do not restart):**
- (a) overlap: share of the prompt's distinctive tokens (`bound.TOKEN_RE` minus the session's
  common tokens by `link`'s rule) that occur in the outputs (assistant text + tool inputs) of the
  last K = 50 / 200 calls (ov50, ov200), in the outputs since the last compaction (ovcyc), or in any
  segment born since the last compaction (tool results, prompts, writes; ovctx). Direction +.
  A prompt with no distinctive token gets overlap 1 (a bare follow-up such as "go on"); sensitivity:
  0, and excluded. Variant: common tokens from the calls before b only (no whole-session vocabulary).
- (b) prompt length (estimated tokens). Direction − (short prompts are follow-ups).
- (c) the prompt names a file seen before b (a path-like prompt token equal to the basename or a
  path suffix of a file read or written earlier; compared in memory). Direction +.
- (d) idle gap: time between call b-1 and call b. Direction − (a long break ends a thread).
- (e) steps of the instruction just finished. Direction +.
- (f) context size at b-1. Direction +.
Metric: AUC (Mann-Whitney, ties 1/2) for Y, Y50, Yall and heavy, pooled over the 582; session
cluster bootstrap 95% interval (1,000 reps) for Y; per-session AUC.

**Combined rule, leave-sessions-out.** Folds by session, balanced on boundaries: F1 = S03, S04, S08
(265 boundaries), F2 = S01, S02, S05, S06, S09, S10 (317). On the training fold: choose the overlap
variant with the highest AUC for Y, then the threshold θ (from the training fold's quantiles) that
maximises Youden's J for "safe" (Y = 0) boundaries; rule = restart iff overlap < θ OR gap > 1 h.
Apply the frozen rule to the other fold. Also: idle-only rule (restart only after a gap > 1 h), and
the full θ frontier in-sample (descriptive only).

**Saving.** `whatif.restart` convention on the dataset-v2 series (restart at an instruction boundary
when the replayed context > 200k, 10k summary, the replay compacts at the session's ceiling), first
reproducing 55.2%, with restarts allowed only where the rule allows. Charges per restart: none;
B5's median cold start (T = 22.5k tokens joining the context, 0.5 extra calls); cold start plus the
boundary's behavioural re-obtained tokens (primary window; variant 50 calls). Price: B5's model
(0.1 per token kept, 2.0 per new token) and an expiry-aware variant in which a call after a gap
> 1 h pays 2.0 for the kept tokens too (cycle C: all writes are 1-hour). Harm: of the boundaries the
replay restarts, the share with Y = 1; restarted Y = 1 boundaries and re-obtained tokens as a share
of the unrestricted rule's. Idle (> 1 h) boundaries reported as their own subset.

Deviations from the spec: none in the pre-specified parts. Everything marked **post-hoc** below was
added after seeing the outcomes (length-stratified AUC, stricter outcomes, random-allow control,
hindsight oracle, in-sample frontier on the steps signal).

## 1. Method (as run)
- Features and outcomes: 657 boundaries, 582 above 200k,
  asserts the call indexing equals `bound.read_trace_lines`, B5's hashed tool keys and the dataset-v2
  series. Prompts, outputs and paths were compared in memory; scripts are kept with the analysis files.
- Replay: `whatif.restart` logic re-implemented with an allow mask and charges; with everything
  allowed and no charge it equals `whatif.restart` exactly (**55.20%**; asserted). With nothing
  allowed it equals the measured input (6.579B). Price totals: B5 model 0.724B, expiry-aware 0.785B.
- A boundary the rule refuses is not skipped for good: the replay restarts at the next allowed
  boundary while the replayed context stays above 200k, so refusing boundaries moves restarts
  rather than removing them one for one.

## 2. Base rates (582 boundaries above 200k)
| outcome | base rate |
|---|---|
| Y: any re-read / exact re-run of a current-cycle item in instruction j+1 | 64.8% |
| Y50: same in the next 50 calls | 88.7% |
| Yall: all-history sources | 66.8% |
| heavy: >= 10k re-obtained tokens | 0.9% (5 boundaries) |
| post-hoc: >= 3 items / tokens >= p90 (2.7k) | 33.0% / 10.3% |

- Re-obtained per boundary (primary window, median 12 calls): 2.2 items, **mean 0.9k tokens**
  (median 0.2k, p90 2.7k; 0.7k median among Y = 1); 50-call window mean 2.1k. These boundaries had no
  restart, so this is the agent's habit with the old context still present (A5's mid-cycle habit:
  3.4k distinct per 50 calls; after a real compaction 10.2k).
- Y is mostly the length of the next instruction (hindsight): 20.5% when it has 1-4 calls (n 117),
  66.0% for 5-19 (268), 88.1% for 20-74 (168), 96.6% for 75+ (29).
- By idle gap before the boundary: < 5 min n 331, Y 64.0%; 5-60 min n 192, 65.6%; > 1 h n 59,
  66.1%. A break does not mark a safer boundary.
- Per session Y: S01 33%, S02 70%, S03 53%, S04 60%, S05 72%, S06 48%, S08 67%, S09 77%, S10 91%.
- Prompts: 4.1% have no distinctive token (Y 58%); 4.3% contain a path-like token; only 0.3% name a
  file seen before, so signal (c) is nearly constant.

## 3. Signal AUCs (oriented: > 0.5 = the pre-specified direction)
| signal | Y | Y50 | Yall | heavy (n=5) | Y, session bootstrap 95% | within-session | post-hoc: length-stratified | post-hoc: tokens >= p90 | post-hoc: >= 3 items |
|---|---|---|---|---|---|---|---|---|---|
| (a) overlap, last 50 calls | 0.516 | 0.480 | 0.516 | 0.559 | 0.48-0.58 | 0.501 | 0.485 | 0.502 | 0.496 |
| (a) overlap, last 200 calls | 0.520 | 0.502 | 0.521 | 0.547 | 0.47-0.61 | 0.493 | 0.469 | 0.528 | 0.510 |
| (a) overlap, outputs since compaction | 0.533 | 0.510 | 0.532 | 0.530 | 0.48-0.63 | 0.488 | 0.463 | 0.516 | 0.526 |
| (a) overlap, whole context since compaction | 0.531 | 0.541 | 0.526 | 0.401 | 0.49-0.63 | 0.503 | 0.468 | 0.471 | 0.508 |
| (a) same, empty prompt = 0 | 0.544 | 0.593 | 0.543 | 0.438 | 0.50-0.66 | 0.524 | 0.484 | 0.498 | 0.517 |
| (a) last 50, prefix-only common | 0.527 | 0.499 | 0.527 | 0.563 | 0.47-0.58 | 0.515 | 0.510 | 0.490 | 0.495 |
| (a) context, prefix-only common | 0.538 | 0.558 | 0.533 | 0.407 | 0.50-0.61 | 0.505 | 0.482 | 0.462 | 0.509 |
| (b) short prompt | **0.431** | 0.465 | 0.425 | 0.354 | 0.36-0.54 | 0.410 | 0.441 | **0.336** | 0.412 |
| (c) names a file seen before | 0.503 | 0.502 | 0.503 | 0.498 | 0.50-0.50 | 0.504 | 0.501 | 0.507 | 0.501 |
| (d) short idle gap | 0.496 | 0.480 | 0.506 | 0.567 | 0.47-0.57 | 0.501 | 0.512 | **0.402** | 0.467 |
| (e) steps of the finished instruction | **0.622** | 0.646 | 0.617 | 0.572 | 0.50-0.65 | 0.620 | **0.592** | 0.513 | 0.603 |
| (f) context size | 0.490 | 0.490 | 0.485 | 0.320 | 0.42-0.53 | 0.470 | 0.426 | 0.428 | 0.484 |
| calls since compaction | 0.584 | 0.596 | 0.573 | 0.309 | 0.49-0.66 | 0.478 | 0.464 | 0.368 | 0.533 |

Excluding the 24 empty prompts, overlap AUCs are 0.524-0.542. Per session (Y, sessions with >= 5
of each class) the overlap AUCs range 0.38-0.75 and change sign across sessions (S02 0.65-0.75,
S10 0.36-0.42). The pooled 0.53-0.54 is between-session (within-session 0.49-0.52). Longer prompts and
longer breaks predict *more* re-obtaining (0.66 and 0.60 for the top-decile token outcome, reversed).
Only (e) carries a consistent signal (0.59-0.62, also within session and within next-length strata),
and it points to "do not restart after a long instruction", which is when context is largest.

## 4. Pre-specified leave-sessions-out rule: restart iff overlap < θ OR idle > 1 h
| train -> test | overlap variant chosen (training AUC) | θ | test AUC | test Youden J | test boundaries allowed (Y=0 / Y=1) |
|---|---|---|---|---|---|
| F1 -> F2 | last 50, prefix-only common (0.507) | 0.062 | 0.526 | 0.040 | 57% (60% / 56%) |
| F2 -> F1 | whole context since compaction (0.583) | 0.240 | 0.482 | -0.017 | 51% (50% / 52%) |

Replay on the test fold's sessions (cold start 22.5k / 0.5 calls + the boundary's re-obtained tokens
charged; input %, price B5 / expiry-aware in brackets):
| test fold | rule | no charge | charged | restarts | Y=1 restarts (share) | re-obtained tokens at restarts |
|---|---|---|---|---|---|---|
| F2 | unrestricted | 52.7 | 50.7 (46.7 / 48.9) | 96 | 74 (77%) | 109k |
| F2 | **rule** | 47.5 | 45.5 (42.0 / 44.8) | 83 | 62 (75%) | 86k |
| F2 | random allow at 57% (20 seeds) | | 42.9 (39.7 / 41.8) | 77.9 | 59.2 (76%) | 89k |
| F2 | idle > 1 h only | 19.9 | 16.2 (15.0 / 20.2) | 31 | 21 (68%) | 28k |
| F1 | unrestricted | 60.7 | 57.1 (49.9 / 52.0) | 72 | 43 (60%) | 84k |
| F1 | **rule** | 54.9 | 50.8 (44.6 / 47.6) | 57 | 35 (61%) | 62k |
| F1 | random allow at 51% | | 50.6 (44.3 / 46.2) | 58.0 | 34.5 (59%) | 78k |
| F1 | idle > 1 h only | 16.9 | 15.8 (13.7 / 19.5) | 17 | 12 (71%) | 24k |

Out of sample the rule keeps 89-90% of the charged saving and removes 16-19% of the harmful
restarts, which is what refusing a random half of the boundaries does too (the replay re-restarts at
the next boundary). The share of restarts that land on a Y = 1 boundary is unchanged (75% vs 77%;
61% vs 60%).

## 5. All sessions: rules, controls and the hindsight bound (input %, price B5 / expiry-aware)
| rule | no charge | cold start | cold + re-obtained (instr.) | cold + re-obtained (50 calls) | restarts | Y=1 (share) | Y50=1 | re-obtained tok | after > 1 h |
|---|---|---|---|---|---|---|---|---|---|
| unrestricted | **55.2** (51.1 / 53.3) | 53.0 (48.0 / 50.2) | **52.7** (47.6 / 49.8) | 52.3 (47.2 / 49.4) | 168 | 117 (70%) | 152 | 193k | 22 |
| not after idle > 1 h | 52.5 (48.5 / 49.2) | 49.8 (45.0 / 45.9) | 49.4 (44.6 / 45.5) | 49.1 (44.3 / 45.2) | 156 | 106 (68%) | 142 | 200k | 0 |
| idle > 5 min only | 46.0 (42.8 / 45.7) | 41.7 (38.1 / 41.3) | 41.4 (37.8 / 41.0) | 40.9 (37.3 / 40.5) | 122 | 84 (69%) | 112 | 154k | 31 |
| **idle > 1 h only** | 18.9 (17.5 / 22.6) | 16.2 (14.8 / 20.1) | **16.0** (14.6 / 20.0) | 16.0 (14.5 / 19.9) | 48 | 33 (69%) | 45 | 52k | 48 |
| overlap (context) < median, in-sample | 47.5 (44.2 / 46.1) | 43.7 (39.9 / 42.0) | 43.4 (39.6 / 41.7) | 43.2 (39.3 / 41.5) | 129 | 87 (67%) | 119 | 154k | 16 |
| same OR idle > 1 h | 50.8 (47.1 / 49.7) | 46.9 (42.7 / 45.7) | 46.7 (42.4 / 45.4) | 46.4 (42.1 / 45.1) | 138 | 92 (67%) | 127 | 155k | 34 |
| overlap (context) < q75 OR idle > 1 h | 54.7 (50.6 / 52.8) | 51.3 (46.5 / 49.0) | 51.1 (46.2 / 48.7) | 50.8 (45.9 / 48.4) | 161 | 109 (68%) | 146 | 175k | 26 |
| post-hoc: steps of finished instr. < 6 (q25) | 23.3 (21.5 / 23.0) | 20.0 (18.1 / 19.6) | 20.0 (18.2 / 19.6) | 20.1 (18.2 / 19.7) | 64 | 34 (53%) | 54 | 41k | 6 |
| post-hoc: steps < 13 (median) | 35.4 (32.8 / 33.9) | 32.7 (29.7 / 30.8) | 32.5 (29.5 / 30.6) | 32.4 (29.4 / 30.6) | 100 | 61 (61%) | 91 | 147k | 10 |
| post-hoc: steps < 25 (q75) OR idle > 1 h | 47.7 (44.1 / 47.0) | 44.0 (39.8 / 42.9) | 43.7 (39.5 / 42.6) | 43.4 (39.1 / 42.3) | 138 | 92 (67%) | 123 | 178k | 36 |
| post-hoc: random allow 25% / 50% / 75% (20 seeds) | | | 30.6 / 43.8 / 49.7 | | 89 / 131 / 154 | 60 / 90 / 106 (67-69%) | | 103k / 161k / 184k | |
| post-hoc ORACLE: only Y = 0 boundaries | 24.1 (22.3 / 24.3) | 21.7 | 21.7 (19.6 / 21.7) | 21.5 | 85 | 0 | 64 | 0 | 8 |
| post-hoc ORACLE: only re-obtained < 1k | 45.5 (42.2 / 44.3) | 42.0 | 42.1 (38.2 / 40.4) | 41.7 | 134 | 76 (57%) | 115 | 30k | 18 |

- Every no-foresight rule sits on the random-allow line: about 67-70% of its restarts land on a
  Y = 1 boundary, as for the unrestricted rule (70%) and for random refusal (67-69%). Only the
  hindsight oracle and the post-hoc "short finished instruction" rule (53% at q25) are below it,
  and the latter keeps only 20% of input.
- Even perfect foresight of Y would keep only 24% (22% charged): restarting only where the next
  instruction re-reads nothing forgoes more than half the lever, because two in three boundaries
  are followed by some re-reading.
- The behavioural charge itself is small: cold start + re-obtained tokens cost 2.5 points of input
  (55.2 -> 52.7) for all 168 restarts; the re-obtained part is 0.3 points (193k tokens in all).

## 6. The idle subset (breaks over 1 h)
- 59 of 582 boundaries above 200k follow a break of over 1 h (mean context 523k); Y 66% against 65%
  elsewhere: no safer.
- Restarting only there: 48 restarts, **16.0% of input, 14.6% of B5 price, 20.0% of expiry-aware
  price** (charged; 18.9% / 22.6% uncharged), i.e. about 30% of the unrestricted rule's input saving
  and 40% of its expiry-aware price saving with 29% of its restarts.
- Per restart this is the cheapest subset in money: 0.42 points of expiry-aware price per restart
  against 0.30 for the unrestricted rule and 0.29 for "never after a break" (input: 0.33 vs 0.31).
  The measured context at these 59 returns is re-written at 2.0 anyway: 59M price units, 7.5% of the
  expiry-aware total, which a restart replaces by base + summary + cold start.
- Excluding them ("not after idle") costs 3.3 points of input and 4.3 of expiry-aware price
  against the unrestricted rule, and removes only 11 of 117 harmful restarts.

## Caveats
- **The outcome is not harm.** Y is observed in sessions that did not restart, so it measures
  whether the next instruction touches files of the current cycle, mostly the agent's re-reading
  habit and the length of the next instruction (20% for 1-4 calls, 97% for 75+). It cannot see a
  wrong decision, a lost constraint or a re-derivation by another route (A5's caveats apply). A
  restart would raise re-reading (about 3x after real compactions, A5), and re-reads of images count
  0 tokens. No rule can be shown to be "safe" with it; only that the signals do not rank it.
- The heavy outcome (>= 10k) has 5 positives and is not interpretable; the post-hoc top decile
  (>= 2.7k) has 60.
- Charging the re-obtained tokens double counts them (the re-reads are already in the series growth
  the replay keeps): conservative, and small here.
- Features use the observed session; after a replayed restart the "since last compaction" window
  would start at the restart. The common-token set uses the whole session (bound's rule); the
  prefix-only variant changes AUC by <= 0.02.
- Prompt path matching is lexical (basename or suffix); 0.3% of prompts name a known file, so (c) is
  untested rather than null.
- One user, 9 sessions with boundaries above 200k, S03 has 44% of them; two folds only. The
  expiry-aware price charges 2.0 for kept tokens after a > 1 h gap but ignores the cache lifetime
  of the restarted context itself (the summary is written fresh anyway).

## Findings
1. No no-foresight signal ranks the boundaries the agent re-reads after: prompt overlap with the
   current context scores AUC 0.52-0.54 pooled, 0.49-0.52 within sessions, 0.46-0.51 once the next
   instruction's length is held fixed, and it flips sign between sessions; naming a known file occurs
   at 0.3% of prompts.
2. The pre-specified rule (overlap < θ OR idle > 1 h, chosen on half the sessions) keeps 89-90% of the
   charged saving out of sample (45.5% vs 50.7%; 50.8% vs 57.1%) but leaves 75% / 61% of its
   restarts on boundaries followed by re-reading, the same as the unrestricted rule and as refusing a
   random half of the boundaries.
3. Breaks are not safer boundaries (Y 66% after > 1 h vs 65%; longer breaks and longer prompts
   predict more re-reading), but they are the cheapest place to restart: restarting only after
   breaks over 1 h saves 16% of input and 20% of expiry-aware price with 48 restarts, 0.42 price points
   per restart against 0.30 for the full rule.
4. Avoiding "harm" as measured costs most of the lever: even perfect hindsight of Y keeps only 22-24%
   of input, because two in three boundaries are followed by some re-reading; the only consistent
   signal (a long finished instruction, AUC 0.59-0.62) says not to restart exactly where context is
   largest.
5. The behavioural charge is not what limits the lever: cold start plus re-obtained tokens take
   55.2% to 52.7% (47.6% B5 price, 49.8% expiry-aware); the open risk remains quality, which neither
   the outcome nor any boundary signal measured here can see.
