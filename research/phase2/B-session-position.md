> Working memo from cycle B of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots (B uses only the public `dataset-v2.json`). Scripts are not published because they read the transcripts.

# Question B: position in the session, and user-level restart rules

Data: research/survey/user01/dataset-v2.json, 10 sessions with series, 16,181 main-session calls, 667 instructions,
6.579e9 input tokens measured. No repo file modified. Code: restart.py (replay + self-test), analyze.py (tables; raw output in analyze_output.txt).

## Method
- Conventions as in pickaxetax.survey: base = context[0]; an instruction is the call segment between consecutive unique
  `instruction_starts` (plus 0), so the instruction index = segment number; carried-over = context at the instruction's first call minus base
  (the decompose definition, per call min(x, start) - base).
- Replay (restart.py, mode "delta"): state s <= actual always. At a restart s = min(actual, base+S); otherwise s grows by the same call-to-call
  growth as the actual series; if actual drops (a real compaction/clear) s = min(s, actual). Instruction N+1, 2N+1, ... starts the new session
  (the first instruction is never restarted). Rule (b) restarts at an instruction boundary when the *replayed* context at the end of the previous
  instruction exceeds X. "with cost" variant adds one read of the replayed context at each restart (writing the summary).
- "% saved" = 1 - replay input / measured main-session input, pooled over the 10 sessions (not the mean of per-session %).

## 1. Does an instruction cost more the later it comes?
Pooled by index bucket (all sessions; n = instructions):

| index | n | sessions | calls/instr | mean ctx/call | input/instr | carried at start | carried share of input | session-normalised mean ctx |
|---|---|---|---|---|---|---|---|---|
| 1 | 10 | 10 | 93.6 | 293k | 27.4M | 0 | 0% | 0.43 |
| 2-3 | 20 | 10 | 35.9 | 249k | 8.9M | 184k | 62% | 0.74 |
| 4-7 | 36 | 10 | 18.0 | 396k | 7.1M | 296k | 80% | 1.07 |
| 8-15 | 59 | 8 | 29.6 | 438k | 13.0M | 463k | 75% | 1.33 |
| 16-31 | 97 | 7 | 24.1 | 425k | 10.2M | 435k | 80% | 1.18 |
| 32+ | 445 | 6 | 22.0 | 420k | 9.2M | 425k | 81% | 1.13 |

Spearman (index vs ...): 

| | mean ctx/call | input | calls | carried at start |
|---|---|---|---|---|
| pooled (667) | +0.11 | -0.09 | -0.17 | +0.11 |
| median of per-session | +0.16 | -0.04 | -0.20 | +0.17 |
| per session (n>=35): S02 / S03 / S05 / S06 / S09 / S10 | +.14/+.14/-.06/-.28/+.12/+.18 | +.03/-.05/-.29/-.78/+.04/-.38 | -.07/-.12/-.21/-.61/-.05/-.45 | |

(S01 n=16: +0.47 mean ctx, +0.09 input; S04/S07/S08 n<=10: mean-ctx rho = +1.0 but trivial n.)

Separating the two effects: context per call rises with position only up to roughly instruction 4-8, then it is flat (420-440k, a plateau
bounded by compaction near ~780k). Calls per instruction fall with position (instruction 1 is the long set-up: 94 calls, 4% of input from 10 of 667
instructions), so input per instruction does NOT rise. Log-linear slope on log(index): mean ctx +0.10, calls -0.16, input -0.06. Variance of
log(input) is explained about 87% by calls per instruction and 13% by context per call: what an instruction costs is mostly how long it runs,
not where it sits. What position does decide is the carried part: from instruction 4 on, ~80% of every call's context is carried over from
earlier instructions (62% at index 2-3), and 62% of all input sits in instructions 32+ simply because that is where most instructions are.
Answer: a later instruction costs more *per call* (about 1.5x the early ones, ~420k vs ~250-290k), but not more per instruction, and the
effect saturates after about the 8th instruction; it is a weak, session-dependent trend, not a law.

## 2. Restart rules (replay, "delta" mode; measured main-session input = 6.579e9)

### 2a. New session every N instructions (pooled % of input saved; in brackets, with the summary-writing read)
| N | S = 2,000 | S = 10,000 | restarts (all 10 sessions) | per-session range (S=10k) |
|---|---|---|---|---|
| 1 | 71.2 (70.2) | 69.6 (68.5) | 657 | 34-76% |
| 2 | 64.6 (63.9) | 63.1 (62.4) | 326 | 30-71% |
| 3 | 60.1 (59.5) | 58.6 (58.0) | 218 | 3-67% |
| 5 | 51.3 (50.8) | 50.1 (49.6) | 127 | 0-60% |
| 10 | 32.1 (31.7) | 31.2 (30.8) | 61 | 0-44% |
| 20 | 18.2 (18.0) | 17.6 (17.3) | 28 | 0-30% |

### 2b. Restart at a boundary when the context exceeds X (S = 10,000; S=2k / 30k in the sensitivity below)
| X | saved % | with cost | restarts per session (S01..S10) | mean/session |
|---|---|---|---|---|
| 100k | 67.5 | 66.8 | 10, 32, 140, 3, 25, 14, 2, 2, 57, 37 | 32.2 |
| 200k | 58.6 | 58.1 | 5, 13, 54, 1, 10, 5, 0, 1, 25, 19 | 13.3 |
| 300k | 50.2 | 49.8 | 3, 7, 30, 1, 7, 2, 0, 0, 15, 12 | 7.7 |
| 400k | 39.7 | 39.3 | 1, 5, 21, 0, 5, 2, 0, 0, 9, 7 | 5.0 |

(S=2k: 68.7 / 59.6 / 50.9 / 40.4; S=30k: 65.0 / 57.1 / 48.3 / 37.9.) Compared with "every 3 instructions" (58.6%, 218 restarts),
"restart above 200k" gets the same saving (58.6%) with 133 restarts, i.e. the threshold rule is about 1.6x more restart-efficient;
"restart above 100k" (322 restarts) reaches 67.5%, close to every-instruction restarts (657 restarts, 69.6%) with half the restarts.
Sessions that actually are tall (max ctx 783k in 7 of 10 sessions) dominate: S03 alone needs 54 restarts at 200k.

### 2c. Agreement with whatif.task_scoped (N = 1)
My default replay does NOT match task_scoped: 71.2% vs 75.6% (S=2k) and 69.6% vs 73.7% (S=10k), a gap of ~4.2-4.4 pp; sessions differ
only where an instruction contains an actual drop of context (any decrease, even small: 8 of 10 sessions; the largest gaps are S10 +38%, S09 +24%, S05 +20% in their own input; S07/S08 have no drops and are identical).
Cause: task_scoped computes `current = x - base - carried` with carried = min(x, start) - base, so after an actual in-instruction compaction
(x < start) current = 0 and the replay stays pinned at base + S until the real context climbs back above its value at the instruction start;
the growth that really happens after the compaction is dropped. My replay keeps that growth (sum of deltas). With mode="anchor"
(s = base + S + max(0, x - actual_at_restart)) restart.py reproduces task_scoped exactly: 1,605,956,876 (S=2k) and 1,727,424,196 (S=10k)
tokens, equal for every session (asserted in the self-test). So the two agree on the rule; the 4 pp is a modelling choice about
post-compaction growth, and task_scoped is the optimistic one (it is also not defensible for N > 1: with anchor mode the pinned
stretch gets very long, e.g. N=20 gives 49% instead of 18%, X=100k gives 80%, so I use delta as primary).

## 3. Caveats and sensitivity
Saved % vs S (delta mode, no cost): 

| S | N=1 | N=3 | N=10 | X=100k | X=200k | X=400k |
|---|---|---|---|---|---|---|
| 0 | 71.6 | 60.4 | 32.3 | 69.0 | 59.7 | 40.6 |
| 2k | 71.2 | 60.1 | 32.1 | 68.7 | 59.6 | 40.4 |
| 10k | 69.6 | 58.6 | 31.2 | 67.5 | 58.6 | 39.7 |
| 30k | 65.6 | 55.1 | 29.0 | 65.0 | 57.1 | 37.9 |
| 50k | 61.8 | 51.9 | 27.2 | 61.8 | 54.9 | 36.8 |
| 100k | 52.9 | 44.1 | - | 50.4 | - | 34.1 |
| 200k | 37.1 | 30.5 | - | 37.1 | - | 28.0 |
| 300k | 24.0 | 19.2 | - | 24.0 | - | 22.0 |

- Sensitivity to S is small: S 2k -> 10k costs ~1.6 pp (N=1); S 2k -> 50k costs ~9 pp. Treat any "re-read" as extra S: re-reading 100k of files
  per restart leaves 53% (N=1) / 50% (X=100k); the saving only reaches zero if the restart context is near the actual context (S well above 300k).
- The assumption the numbers depend on most is not S but that a restart can happen at every boundary at all, i.e. that the instruction
  after the restart needs no more than base + S + what it itself adds ("nothing has to be re-read" and "summary is enough"). That is untestable
  from numbers. Next, the baseline: contexts are huge (mean 420k) because actual compaction only fires near ~780k, so any early restart
  looks large; against a baseline that compacted at 200k the saving would be much smaller (see whatif.cap).
- Metric is input tokens, not money: restarting forfeits cache hits on the old prefix and writes a new prefix (higher price per token for the first
  call); cached reads are cheap, so the saving in cost is smaller than in tokens. Summary generation (+~1 pp) and its quality are not modelled.
- Instruction boundaries here are the user's instruction_starts; the replay assumes every instruction is separable from the earlier ones; for
  follow-up edits ("also change X") it is not, and the true carry-over need is higher than S.
- Small sample (10 sessions, 3 with <=10 instructions; two sessions with 0 compactions). The 32+ bucket comes from 6 sessions; S03 alone has 292 instructions.
- Part 1 trend is ecological: index is confounded with session and with compactions (sawtooth); the pooled Spearman is weak (+0.11 / -0.09).

## Findings
1. Later instructions cost slightly more per call (420k vs 250-290k mean context) but not more per instruction (Spearman index vs input -0.09 pooled; calls per instruction fall with index); 87% of the variance in an instruction's input is its call count.
2. From instruction 4 on ~80% of every call's context is carried over, which is what a restart removes.
3. "New session every instruction" saves 70% of input (S=10k), every 3rd 59%, every 5th 50%, every 10th 31%, every 20th 18%.
4. A size trigger beats a fixed count: restarting at a boundary above 200k saves 59% with ~13 restarts per session (above 100k: 67%, 32 restarts; above 400k: 40%, 5 restarts).
5. The numbers barely move with S (2k to 10k: -1.6 pp; to 50k: -9 pp); the replay agrees with task_scoped only in "anchor" mode (75.6%/73.7%); task_scoped overstates by ~4 pp by freezing post-compaction growth.
