> Working memo from cycle D3 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; mostly from the public `dataset-v2.json` and `cloud-sessions.json`.

# D3 - Did the way of working change over the period, and does the model matter?

Numbers only. Scripts: `extract.py` (start time and per-call model from the private lines), `analyze.py` (per-session table), `trend.py` (Spearman), `model_thirds.py` (model groups, thirds). Data: public `dataset-v2.json` series/tools/models/compactions/active_hours and `cloud-sessions.json` (effort, origin); start date and per-call model from the private lines (first main-session timestamp).

## Premise check
- The 10 measured sessions start between **2026-08-10 and 2026-10-05** (56 days, not three months). The list period begins 07-10, but the sessions with tokens only begin 08-10. The two cost-only sessions (S11, S12, sonnet-5) have no token measurement and are left out. No measured session starts between 09-01 and 09-29 (S06 stays open until 09-12 but starts 08-16).
- Models by call: opus-5 dominates 6 sessions (S04, S05, S06, S07, S09, S10), opus-5.5 3 (S01, S02, S03), fable-5 1 (S08). **S04 switches model mid-session**: its first 50 calls (the first 2 instructions) are fable-5, the remaining 115 opus-5 (label "dominant" = by call count). No other session mixes models. Model and date are almost the same variable: all opus-5.5 sessions start 09-30 or later, all opus-5 sessions 08-10 to 08-31, fable-5 08-12 (S08) plus the start of S04 (08-31). Spearman of start date vs "is opus-5.5" = +0.80 (ranks with ties; the three are the three newest).

## Method
- Per-session metrics from the public series. Calls = main-session API calls (de-duplicated). Context per call = input + cache read + cache write. Calls per instruction = segment lengths between `instruction_starts` (equals `per_instruction.calls`; counts differ slightly from `user_instructions` for S01, S03, S08). Carried-over share = `dataset.decompose` (fixed base = first call's context; carried = context present when the instruction began; current = grown during it), share of total input over all calls, for all 10 sessions (the earlier layer-2c file covers six; values agree). Compactions per 1,000 calls from `measurement.compactions`. Tool mix = share of all tool calls: Bash, Read, Edit+Write, other (everything else: MCP, task tools, ToolSearch, AskUserQuestion, Artifact, Agent, Grep ...). Input per active hour = main-session input processed / `active_hours` (including sub-agent input changes it for S01-S03, S09 by <= 10%). Sub-agent share = sub-agent calls / (main + sub-agent calls) and the same for input.
- Spearman with start date as day count; n = 10 (S08/S09 tie). p from 100,000 random permutations; the interval from 4,000 bootstrap resamples of sessions.
- Model groups: group medians (min-max), Cliff's delta (-1..+1, share of pairs larger minus smaller), exact two-sided permutation p of the median difference over all 84 splits of the 9 opus sessions (3 vs 6). fable-5 is a single session, so no test.
- Thirds: the session's calls are split into three equal call-count blocks; an instruction belongs to the block where it starts. Calls per instruction: median/p90 of its instructions in the block; context per call: median over calls. Interval for the change in calls per instruction = bootstrap over instructions; for context per call = block bootstrap in 100-call blocks (calls in a row are strongly dependent). Compaction = a call whose context is below 0.8x the previous call.

## Per-session table (sorted by start)
| id | start | dominant model | effort | calls | instr. | median ctx/call | calls/instr. med / p90 | carried share | compactions /1,000 calls | Bash / Read / Edit+Write / other | active h | input per active h | sub-agent share (calls / input) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S10 | 08-10 | opus-5 | - | 2,878 | 73 | 371k | 15.0 / 99 | 78% | 1.7 | 71 / 5 / 16 / 8% | 22.4 | 50.0M | 0% / 0.0% |
| S08 | 08-12 | fable-5 | - | 105 | 6 | 192k | 14.0 / 35 | 51% | 0.0 | 34 / 20 / 38 / 9% | 1.8 | 10.7M | 0% / 0.0% |
| S09 | 08-12 | opus-5 | medium | 4,056 | 127 | 401k | 19.0 / 58 | 82% | 1.7 | 86 / 3 / 9 / 2% | 42.2 | 39.3M | 29% / 9.5% |
| S07 | 08-15 | opus-5 | - | 66 | 4 | 135k | 8.5 / 36 | 41% | 0.0 | 76 / 7 / 12 / 4% | 0.7 | 12.3M | 0% / 0.0% |
| S06 | 08-16 | opus-5 | - | 464 | 35 | 272k | 10.0 / 30 | 79% | 2.2 | 56 / 16 / 22 / 6% | 5.8 | 28.4M | 0% / 0.0% |
| S05 | 08-17 | opus-5 | - | 1,923 | 55 | 395k | 12.0 / 66 | 60% | 1.6 | 83 / 10 / 6 / 1% | 18.2 | 42.8M | 0% / 0.0% |
| S04 | 08-31 | opus-5 (69%) | medium | 166 | 10 | 171k | 15.5 / 28 | 61% | 0.0 | 56 / 10 / 32 / 2% | 2.4 | 12.2M | 0% / 0.0% |
| S03 | 09-30 | opus-5.5 | high | 4,820 | 292 | 428k | 10.0 / 39 | 78% | 2.9 | 76 / 9 / 2 / 12% | 60.5 | 34.0M | 9% / 2.4% |
| S02 | 10-04 | opus-5.5 | medium | 1,303 | 49 | 439k | 18.0 / 47 | 71% | 2.3 | 69 / 7 / 2 / 22% | 13.7 | 41.9M | 15% / 6.0% |
| S01 | 10-05 | opus-5.5 | high | 400 | 16 | 387k | 18.0 / 66 | 76% | 2.5 | 56 / 4 / 15 / 25% | 4.9 | 34.7M | 2% / 0.3% |
Sub-agent rows: only S01 (8 calls, haiku), S02, S03, S09 have sub-agents; all others 0. Total tool calls per session are the denominator of the tool mix.

## 1. Trends against start date (Spearman, n = 10)
**How weak n = 10 is:** |rho| must exceed about 0.65 for p < 0.05 (two-sided), and the 95% interval for a true rho of 0.5 would still run from about -0.2 to +0.9. A "no trend" result means only that no trend larger than roughly |rho| 0.65 is detectable. Fourteen metrics are tested, so one p < 0.05 would be expected by chance; none reached it. Sessions also differ by two orders of magnitude in length (66 to 4,820 calls), and four of them are very short.

| metric | Spearman rho vs start date | permutation p | bootstrap 95% interval |
|---|---|---|---|
| median context per call | +0.39 | 0.26 | -0.32 to +0.84 |
| calls per instruction, median | +0.15 | 0.68 | -0.63 to +0.86 |
| calls per instruction, p90 | -0.08 | 0.83 | -0.76 to +0.70 |
| carried-over share | -0.02 | 0.97 | -0.61 to +0.74 |
| compactions per 1,000 calls | +0.54 | 0.11 | -0.27 to +0.87 |
| Bash share | -0.16 | 0.66 | -0.76 to +0.54 |
| Read share | -0.07 | 0.85 | -0.97 to +0.62 |
| Edit+Write share | -0.42 | 0.23 | -0.92 to +0.26 |
| other-tool share | +0.42 | 0.23 | -0.50 to +0.92 |
| active hours | -0.01 | 0.98 | -0.66 to +0.71 |
| input per active hour | -0.01 | 0.99 | -0.72 to +0.81 |
| sub-agent call share | +0.37 | 0.29 | -0.36 to +0.83 |
| instructions per active hour | +0.25 | 0.49 | -0.54 to +0.73 |
| calls per active hour | -0.22 | 0.54 | -0.82 to +0.61 |

Reading: nothing is distinguishable from zero. The largest effects are compactions per 1,000 calls (+0.54), median context per call (+0.39), Edit+Write share (-0.42) and other-tool share (+0.42). Two of these are mostly size, not date: **session length (calls) alone predicts median context (rho +0.79), carried share (+0.73), compactions per 1,000 calls (+0.61)**, while date and session length are unrelated (rho -0.01), so date does not hide behind length but the short sessions (S04, S07, S08, S01, S06) pull the context metrics down regardless of date. Stable across sessions: calls per instruction median 8.5-19 (no trend, +0.15), carried share 41-82% (51-82% outside the shortest S07), Bash 56-86% in nine of ten, input per active hour 28-50M in the seven sessions with >= 4.8 active hours (rho -0.01 over all ten; the 10-12M values belong to the three shortest sessions, under 2.5 active hours). Descriptively, the three newest sessions have median context 387-439k, compactions 2.3-2.9 per 1,000 calls (vs 0-2.2 earlier) and a different tool mix: Edit+Write 2% in S02 and S03 against 6-38% in earlier sessions (S01 15%), and 12-25% "other" tools (MCP, task tools, notifications, Artifact) against 1-9% earlier. That points to a changed tool environment (task/MCP tooling available from late September, shell instead of the Edit tool) as much as to a changed habit.

## 2. Differences by model (descriptive; confounded with date, task type, effort, origin)
Group medians (min-max), opus-5.5 (n=3: S01-S03) vs opus-5 (n=6: S04-S07, S09, S10) vs fable-5 (n=1: S08):

| metric | opus-5.5 | opus-5 | fable-5 (S08) | Cliff's delta 5.5 vs 5 | exact perm p |
|---|---|---|---|---|---|
| median context per call | 428k (387-439) | 322k (135-401) | 192k | +0.78 | 0.26 |
| calls/instr., median | 18 (10-18) | 13.5 (8.5-19) | 14 | +0.28 | 0.56 |
| calls/instr., p90 | 47 (39-66) | 47 (28-99) | 35 | +0.11 | 1.00 |
| carried-over share | 76% (71-78) | 69% (41-82) | 51% | +0.11 | 0.49 |
| compactions per 1,000 calls | 2.5 (2.3-2.9) | 1.6 (0-2.2) | 0 | +1.00 | 0.12 |
| Bash share | 69% (56-76) | 74% (56-86) | 34% | -0.22 | 0.75 |
| Edit+Write share | 2.5% (2-15) | 14% (6-32) | 38% | -0.67 | 0.13 |
| other-tool share | 22% (12-25) | 3.5% (1-8) | 9% | +1.00 | 0.04 |
| active hours | 13.7 (4.9-60.5) | 12.0 (0.7-42.2) | 1.8 | +0.22 | 0.95 |
| input per active hour | 34.7M (34.0-41.9) | 33.9M (12.2-50.0) | 10.7M | +0.11 | 0.99 |
| instructions per active hour | 3.6 | 3.7 | 3.3 | +0.11 | 1.00 |

Long sessions only (>= 1,000 calls; opus-5.5 S02, S03 vs opus-5 S05, S09, S10; means): median context 433k vs 389k, calls/instr. median 14 vs 15.3, p90 43 vs 75, carried share 74% vs 73%, compactions 2.6 vs 1.7 per 1,000 calls, input per active hour 37.9M vs 44.0M, Bash 72% vs 80%, Edit+Write 2% vs 10%, other 17% vs 4%.

- **Effect sizes**: the opus-5.5 group has larger context (+106k, but partly session length), more compactions (+0.9 per 1,000 calls; every opus-5.5 session above every opus-5 session, delta +1.00, but p = 0.12 with 3 vs 6), and a far larger "other tools" share (delta +1.00, p = 0.04, the only nominal p < 0.05 of 11 comparisons, so about what chance gives). What the working loop looks like - calls per instruction (median +4.5, delta +0.28), p90, carried share (+7 points, delta +0.11), input per active hour, instructions per hour - barely differs: the differences are inside the spread of opus-5 itself (calls/instr. median 8.5-19 within opus-5).
- **fable-5**: one session (S08, 105 calls, 6 instructions, 1.8 active hours, graphics design task) with Bash 34% (Edit 37%, Read 20%, Grep 7%) against Bash 56-86% elsewhere, and the lowest context (192k) and carried share (51%): a short design session starting from a fresh context looks like this on any model (S07, S04 look similar). Inside S04, the fable segment (first 50 calls, 2 instructions of 32 and 18 calls) vs the opus-5 remainder (8 instructions, median 14.5 calls/instr.) hints that fable-5 ran longer per instruction, but n = 2 instructions and the fable calls come first in the session, so context (median 81k vs 205k) is purely session-position. Not interpretable.
- **Confounds**: model = date (see premise). Task type (session-list labels): the opus-5.5 sessions are research/tool development and two app-development sessions; the opus-5 sessions are game development (three), an automation pipeline, a media tool and research/optimisation; Effort setting differs (opus-5.5: high, medium, high; opus-5: medium for S04, S09, unset elsewhere), origin is Android for all but S09 (desktop, which is also the one with a 29% sub-agent call share). The tooling changed over the same dates (task tools, notifications, Artifact, MCP appear only in the newest sessions). None of these can be separated from the model with these data.

## 3. Within long sessions: first third vs last third (S03, S09, S10; S02 and S05 as supplement)
| session | third | calls | instr. | calls/instr. median (p90) | median ctx/call | p90 ctx | compactions |
|---|---|---|---|---|---|---|---|
| S03 | first | 1,607 | 89 | 13.0 (41) | 421k | 719k | 5 |
| S03 | mid | 1,607 | 110 | 9.0 (29) | 424k | 703k | 5 |
| S03 | last | 1,606 | 93 | 8.0 (37) | 440k | 707k | 4 |
| S09 | first | 1,352 | 56 | 19.0 (44) | 393k | 655k | 2 |
| S09 | mid | 1,352 | 26 | 42.5 (124) | 347k | 714k | 3 |
| S09 | last | 1,352 | 45 | 14.0 (59) | 440k | 710k | 2 |
| S10 | first | 960 | 19 | 37.0 (117) | 255k | 663k | 2 |
| S10 | mid | 959 | 14 | 61.0 (138) | 426k | 705k | 2 |
| S10 | last | 959 | 40 | 10.5 (59) | 414k | 660k | 1 |
| S02 | first | 435 | 15 | 15.0 (70) | 404k | 710k | 1 |
| S02 | mid | 434 | 16 | 20.5 (42) | 479k | 721k | 1 |
| S02 | last | 434 | 18 | 16.5 (46) | 504k | 680k | 1 |
| S05 | first | 641 | 3 | 189.0 (486) | 390k | 668k | 1 |
| S05 | mid | 641 | 14 | 19.5 (77) | 344k | 675k | 1 |
| S05 | last | 641 | 38 | 11.0 (31) | 457k | 670k | 1 |


| session | calls/instr. median first -> last (change, 95% interval over instructions; Cliff's delta; perm p) | context per call median first -> last (change, block-bootstrap interval; Cliff's delta) |
|---|---|---|
| S03 (opus-5.5) | 13.0 -> 8.0 (-5.0; -9 to -1; -0.14; p 0.07) | 421k -> 439k (+18k; -171k to +207k; +0.03) |
| S09 (opus-5) | 19.0 -> 14.0 (-5.0; -14 to +3; -0.13; p 0.30), but middle third 42.5 | 392k -> 440k (+47k; -135k to +250k; +0.14) |
| S10 (opus-5) | 37.0 -> 10.5 (-26.5; -47 to -4.5; -0.45; p 0.003) | 254k -> 413k (+158k; -92k to +334k; +0.29) |
| S02 (opus-5.5, suppl.) | 15.0 -> 16.5 (+1.5; -30 to +14.5; -0.11; p 0.92) | 403k -> 503k (+99k; -198k to +281k; +0.13) |
| S05 (opus-5, suppl.) | 189 -> 11 (first third holds only 3 instructions; p 0.002) | 389k -> 457k (+67k; -216k to +293k; +0.11) |

- **Calls per instruction fall from the first to the last third in all three**: median -5 (S03), -5 (S09), -26.5 (S10); that is 8 vs 13, 14 vs 19, and 10.5 vs 37 calls. But pooled calls-per-instruction (calls / instructions) moves less in S03 (18.1 -> 17.3): the median falls while the long tail stays (p90 41 -> 37), i.e. more short instructions, the occasional long run unchanged. In S09 the middle third is the outlier (median 42.5), so the first-last drop is not a trend. In S10 (and the supplementary S05) the first third consists of few, very long autonomous runs (19 instructions of median 37 and p90 117 calls; S05: 3 instructions, median 189 calls), then many short ones: a shift from delegate-and-wait toward short steering, and also a plausible effect of the work phase (build, then tune); the data cannot say which. Only S10 and S05 have intervals that exclude zero. Counter-case: S02 does not drop.
- **Context per call does not fall**: it is flat in S03 (+18k, 4%) and rises in S09 (+47k) and S10 (+158k), but all intervals include zero (block bootstrap with 100-call blocks; the calls are not independent) and the p90 is the same in first and last thirds (S03 719k vs 707k, S09 654k vs 710k, S10 663k vs 659k). The first third includes the early ramp from ~50k, so the median there is lower by construction; compactions cap the context near 700k, so the ceiling does not move. Compactions: S03 5 vs 4, S09 2 vs 2, S10 2 vs 1 (first vs last third).

## What would be needed to separate model, date and task
- **Model vs date**: sessions on different models at the same time. Here the two are one variable (opus-5.5 only at the end). Needed: parallel or alternating sessions, the same weeks, different model, ideally randomized per task; or the person switching model inside one session at known points (S04 is the only such case, with 2 instructions).
- **Model/date vs task**: same task, same repository, same instruction script, run on each model (or a matched replay of identical instructions); today the sessions are an app, games, a pipeline, media, research, graphics, each once.
- **Harness/tool environment**: record the tool list and effort setting per session; the late sessions have task tools, MCP and Artifact that earlier sessions lack.
- **Size**: with 10 sessions (6 with >= 400 calls), one person, a trend of |rho| < 0.65 is invisible and a group comparison of 3 vs 6 cannot go below a two-sided exact p of 2/84 = 0.024. At least 30-40 sessions, per-instruction rather than per-session analysis with session as random effect, would be the next step; the thirds analysis is already per-instruction but within one session, so it speaks about phases, not about models.

## Findings
1. Over 8 weeks (08-10 to 10-05, ten measured sessions; not three months) no workflow metric trends with start date at n = 10: all |rho| <= 0.54, no p below 0.11, intervals span roughly -0.6 to +0.85; the metrics that look like trends (context, compactions per 1,000 calls) mostly follow session length (rho +0.79 and +0.61).
2. Calls per instruction (median 8.5-19), carried-over share (51-82% in nine of ten sessions), Bash share (56-86%) and input per active hour (28-50M for the longer sessions) are about the same on opus-5 and opus-5.5; the opus-5.5 sessions show more compactions per 1,000 calls (2.3-2.9 vs 0-2.2) and a different tool mix (Edit+Write 2% vs 6-38% in earlier sessions, other tools 12-25% vs 1-9%), but model equals date here, and the tool environment changed with them.
3. fable-5 appears in one short design session (S08, 105 calls: Bash 34% vs 56-86%, Edit 37%) and in the first 50 calls of S04; one session cannot support a model effect.
4. Within the long sessions, calls per instruction fall from the first to the last third (S03 13 -> 8, S09 19 -> 14 with a 42.5 middle, S10 37 -> 10.5), with intervals excluding zero only for S10 (and S05); the very long autonomous runs of early thirds give way to short ones, but S02 does not follow, and the cause (phase of work vs habit) is not identifiable.
5. Context per call in the last third is not lower than in the first (S03 +18k, S09 +47k, S10 +158k, all intervals include zero), and the p90 is unchanged near 650-720k: the working style changed in step length, not in how full the context is.
