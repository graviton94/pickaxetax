> Working memo from cycle B5 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# B5: what does a cold start cost? (the missing term of the restart lever)

Paths and commands were compared in memory as hashes. Scripts are kept with the analysis files.

## Method
- **Streams.** Main session = lines without `isSidechain`, calls de-duplicated per message.id, zero-context calls skipped. The indexing matches `bound.read_trace_lines` exactly (asserted). Each sub-agent (`agentId`) is its own stream: 76 runs (S01 1, S02 7, S03 37, S09 31). There are 34 compactions (`bound` compactions) and 667 instruction starts.
- **Tool uses** are classed in memory. *read*: the Read tool, or a Bash command with a file argument to cat/head/tail/sed -n/grep (D2's parser). *inspect*: Grep/Glob/LS, or Bash made only of listing, search, status and inspection words (ls, find, wc, git status/log/diff/show, ...). *edit*: Write/Edit/MultiEdit/NotebookEdit. *write*: an edit, or a Bash command that writes (redirect to a file, tee, sed -i, mkdir/cp/mv/rm, git commit/add/checkout, ...). *run*: everything else. Orientation = read + inspect. A file is identified by its normalised path. Other commands are identified by the SHA-1 of the whitespace-normalised command, as in A5.
- **Tokens.** A tool result's size is `estimate_tokens` × the session's `bound.calibrate` factor (1.0–2.05; the same factor is used for sub-agents). Image results count 0. Context growth = the sum of positive call-to-call increases of the API-reported context. This covers everything, including thinking and the agent's own text.
- **Events.** For each event, windows cover the first K = 10 / 25 / 50 calls, cut at the next compaction or the end of the stream:
  - (a) the 10 main-session starts (first instruction);
  - (b) the 34 compactions;
  - (c) the 76 sub-agent starts (a run can be shorter than K: median 23 calls).
- **Baselines.**
  - *Warm instruction start*: every later instruction start at least 50 calls after the session start or the last compaction (599 events; 455 with 50 calls available). This is the same boundary a restart would use, without the restart.
  - *Habit window*: a grid of windows every 100 calls, at least 100 calls after the last reset (123 events), as in A5.
- **"Already used before".** A file read, or a command, counts as known if its key had appeared earlier:
  - (a) in an earlier session of the same project. Projects are matched by a hash of the working directory: 9 sessions share one project, and S01 is alone. S10 is the earliest session and S01 has no earlier session, so 8 of the 10 starts can have prior use.
  - (b) earlier in the same session.
  - (c) in the parent session or its other sub-agents before the run's first timestamp.

  Known tokens are gross: every read of a known file in the window counts. For compactions, K = 50 gives 21.5k gross. A5's all-history gross figure for N = 50 is 22.0k, so the two measures agree.
- **Charge per restart.**
  - T = excess tokens. Primary: the excess orientation-result tokens. Broad: the excess context growth.
  - S = excess orientation calls (calls whose every tool use is a read or an inspect).
  - Both are measured in the first 50 calls, minus the warm-start rate per call × the window's calls (warm rate per call: 232 orientation tokens, 1,925 growth, 0.32 orientation calls). Negative excesses are floored at 0 when they are charged.
- **Replay.** `whatif.restart` convention on the dataset-v2 series: restart at an instruction boundary when the replayed context is above 200k, with a 10k summary. The uncharged rule reproduces 55.20%. The charged replay works as follows:
  - The restarted context = base + 10k + **T** + the first call's own growth. T is carried until the next restart like any other content.
  - **S** extra calls are added, each riding on base + 10k + T/2.
  - Price model (A4 convention): 0.1 per token kept from the previous call and 2.0 per new token. After a drop or a restart only the base is kept, so the summary and T are written at 2.0.
  - The measured series costs 0.724B in this model. The comparator `whatif.cap(390k, 22k)` = **42.84% of input, 39.61% of price** in the same model.

## 1. Orientation in the first K calls (median / mean; tokens in k)
| K | group | n | files read | commands (of which inspect, mean) | orientation-result tok | all result tok | context growth | files already used before | orientation share of tool uses |
|---|---|---|---|---|---|---|---|---|---|
| 10 | main start (a) | 10 | 7 / 8.1 | 4 / 4.3 (1.8) | 27.3 / 22.9 | 27.5 / 23.6 | 41.9 / 42.6 | 46% (project) | 61% |
| 10 | compaction (b) | 34 | 5 / 6.0 | 3 / 3.3 (0.8) | 8.9 / 11.2 | 10.7 / 12.8 | 18.2 / 21.8 | 57% (session) | 65% |
| 10 | sub-agent (c) | 76 | 7 / 6.9 | 2 / 2.8 (1.2) | 24.3 / 31.4 | 26.8 / 35.8 | 31.5 / 39.3 | 76% (session) | 78% |
| 10 | warm instr. start | 564 | 3 / 3.6 | 5 / 4.6 (0.2) | 1.5 / 2.9 | 3.2 / 4.7 | 17.4 / 19.8 | 68% (session) | 38% |
| 10 | habit window | 119 | 2 / 2.8 | 5 / 5.3 (0.1) | 1.2 / 2.0 | 2.4 / 3.8 | 12.9 / 15.1 | 69% | 32% |
| 25 | main start | 10 | 9 / 11.0 | 11 / 8.6 (2.1) | 31.8 / 29.6 | 32.7 / 35.2 | 81.6 / 81.1 | 45% | 40% |
| 25 | compaction | 34 | 10 / 10.8 | 10 / 9.2 (1.1) | 17.6 / 18.5 | 22.9 / 24.6 | 47.4 / 50.6 | 54% | 54% |
| 25 | sub-agent | 76 | 10 / 12.6 | 4 / 5.2 (1.7) | 30.9 / 42.2 | 34.1 / 48.0 | 53.7 / 60.6 | 70% | 76% |
| 25 | warm instr. start | 520 | 6 / 7.6 | 12 / 12.1 (0.3) | 4.0 / 6.1 | 8.4 / 10.5 | 44.9 / 48.4 | 61% | 35% |
| 25 | habit window | 110 | 6 / 6.7 | 12 / 12.4 (0.2) | 3.5 / 4.9 | 7.4 / 8.8 | 36.8 / 39.8 | 64% | 34% |
| 50 | main start | 10 | 14 / 17.4 | 20 / 16.4 (2.6) | 34.2 / 38.5 | 42.4 / 49.3 | 123.0 / 135.5 | 33% | 34% |
| 50 | compaction | 34 | 20 / 19.7 | 18 / 18.8 (1.6) | 25.8 / 28.9 | 37.0 / 39.9 | 88.8 / 97.3 | 51% | 50% |
| 50 | sub-agent | 76 | 14 / 15.7 | 4 / 7.9 (2.0) | 36.3 / 48.3 | 48.2 / 55.3 | 76.0 / 75.9 | 68% | 72% |
| 50 | warm instr. start | 455 | 12 / 13.9 | 24 / 24.6 (0.5) | 8.8 / 11.6 | 16.7 / 20.1 | 91.1 / 96.2 | 56% | 35% |
| 50 | habit window | 101 | 10 / 12.0 | 24 / 24.7 (0.3) | 8.0 / 9.6 | 14.6 / 17.2 | 75.9 / 80.6 | 59% | 35% |

- **Known tokens.** Gross result tokens of files or commands already used before, mean per event:
  - K = 10: main 12.2k, compaction 7.8k, sub-agent 20.4k, warm 2.3k.
  - K = 25: 17.8k / 13.7k / 29.5k / 4.7k.
  - K = 50: 19.5k / 21.5k / 34.6k / 8.7k.
- **Commands are almost never re-run exactly** (0–2% known in every group), so command reuse is invisible to the hash, as in A5.
- **Main starts by session.** The share of files in the first 25 calls that were already used in an earlier session ranges from 0% to 100% across the 8 starts with prior sessions. Two starts read no files.

## 2. Time to the first productive action (calls from the start)
| group | n | ever edits | calls to first edit, median / p75 / p90 | context growth until then, median / p90 | orientation tokens until then, median | edit inside the same instruction | first write incl. Bash writes, median / p90 |
|---|---|---|---|---|---|---|---|
| main start | 10 | 10 | 12 / 28 / 31 | 62k / 105k | 29.5k | 6/10 | 10 / 30 |
| compaction | 34 | 31 | 12 / 40 / 76 | 33k / 173k | 16.5k | 17/31 | 5 / 11 |
| sub-agent | 76 | 14 | 10 / 14 / 21 | 30k / 58k | 24.0k | n/a | 6 / 17 |
| warm instr. start | 599 | 431 | 17 / 40 / 87 | 29k / 161k | 2.3k | 180/431 | 2 / 7 |
| habit window | 123 | 91 | 17 / 43 / 91 | 24k / 151k | 2.0k | 44/91 | 1 / 5 |

- **First edit.** A session start does not edit later than a warm instruction start: median 12 against 17 calls. Long warm instructions give the same picture: 17 calls for those of 25 calls or more (n = 157), and 13 for those of 75 or more (n = 32).
- **First write.** Counting Bash writes, the first write does come later at cold starts: median 10 at session starts and 6 in sub-agents, against 2 at warm starts. This measure is noisy, because Bash writes include scratch files and status redirects.
- **What the cold start costs.** It is reading done before the first edit (29.5k against 2.3k), not a delay in calls.

## 3. The charge: excess over the warm-start rate (median / mean / p90)
| window | group | orientation tokens (k) | context growth (k) | orientation calls |
|---|---|---|---|---|
| first 10 | main start | 24.4 / 20.0 / 45.6 | 22.1 / 22.8 / 34.0 | 4.5 / 2.5 / 5.6 |
| first 10 | compaction | 6.0 / 8.4 / 20.1 | -1.6 / 2.0 / 18.3 | 2.5 / 2.4 / 5.2 |
| first 10 | sub-agent | 21.4 / 29.1 / 70.6 | 15.2 / 24.0 / 60.0 | 3.5 / 2.9 / 6.5 |
| first 25 | main start | 25.6 / 23.5 / 49.9 | 33.2 / 32.7 / 58.8 | 0.9 / 1.9 / 15.0 |
| first 25 | compaction | 11.5 / 12.4 / 29.2 | -1.0 / 2.2 / 22.8 | 4.9 / 4.3 / 7.9 |
| first 25 | sub-agent | 27.7 / 38.2 / 98.2 | 15.8 / 29.2 / 80.3 | 5.8 / 6.2 / 15.4 |
| first 50 | main start | 22.5 / 26.9 / 71.6 | 26.8 / 39.3 / 110.3 | 0.5 / 0.8 / 16.0 |
| first 50 | compaction | 14.2 / 17.3 / 42.3 | -7.5 / 1.1 / 41.0 | 9.0 / 7.5 / 13.0 |
| first 50 | sub-agent | 28.3 / 42.7 / 104.6 | 15.9 / 29.3 / 80.8 | 7.3 / 8.5 / 20.0 |

- **Main starts.** The excess comes almost entirely in the first 10 calls (about 20–24k of orientation results and 2.5–4.5 extra orientation calls). It barely grows after that. By 50 calls the extra orientation calls have cancelled out: a new session reads first and then works like any other window.
- **Compactions.** The summary keeps context growth at the warm rate. The agent still makes 2.5–9 extra orientation calls, returning 6–17k tokens.
- **Typical cold start.** It costs about **20–30k tokens and 3–9 extra calls**. The 90th percentile is about **45–110k tokens and 13–20 calls**.

## 4. Restart above 200k with the cold-start charge (series replay; % of measured input, price in brackets)
| charge per restart | T | S | input saved % | price saved % | restarts |
|---|---|---|---|---|---|
| none (`whatif.restart`, 10k summary) | 0 | 0 | **55.20** | 51.06 | 146 |
| main start, median, orientation tokens | 22.5k | 0.5 | 53.03 | 47.97 | 168 |
| main start, median, context growth | 26.8k | 0.5 | 51.90 | 46.74 | 169 |
| main start, mean (floored), orientation / growth | 29.1k / 42.4k | 5.2 | 51.22 / 48.83 | 45.95 / 42.93 | |
| main start, p90, orientation tokens | 71.6k | 16 | **41.24** | 33.21 | 244 |
| main start, p90, context growth | 110.3k | 16 | 30.14 | 15.66 | 387 |
| compaction, median / p90 (orientation tokens) | 14.2k / 42.3k | 9 / 13 | 52.13 / 46.99 | 47.61 / 41.26 | 159 / 188 |
| sub-agent, median / p90 (orientation tokens) | 28.3k / 104.6k | 7.3 / 20 | 50.33 / 29.67 | 45.22 / 16.95 | 171 / 353 |
| one real cold start drawn per restart, main (50 draws, median [5-95%]) | | | 51.2 [50.3-52.1] | 46.0 | |
| same, compaction | | | 51.8 [51.3-52.8] | 47.1 | |
| same, sub-agent | | | 49.3 [48.2-50.4] | 43.7 | |
| *comparator: compaction ceiling 390k (`whatif.cap`, 22k)* | | | *42.84* | *39.61* | |

The drawn rows use orientation tokens. With context growth instead, they give main 50.6, compaction 52.6 and sub-agent 50.7.

**Break-even** (the charged restart rule falls to the 390k ceiling lever, uniform charge per restart):
| extra calls S | T at break-even, input (42.84%) | T at break-even, price (39.61%) |
|---|---|---|
| 0 | 100k | 67k |
| 5 | 86k | 59k |
| 10 | 75k | 51k |
| 20 | 52k | 42k |
| 40 | 34k | 27k |

- **Calls alone.** With no extra tokens, the restart rule needs 89 extra calls per restart to fall to 42.8%.
- **Why the restart count rises with T.** A larger T makes the fixed 200k rule restart more often (146 restarts at T = 0, 169 at 27k, 387 at 110k), because the restarted context reaches 200k sooner. Most of the drop in the p90 rows comes from this cascade, not from the charge itself. Raising the threshold to 200k + T avoids the cascade but saves less: 48.8% instead of 51.8% at T = 27k, and 35.5% instead of 41.3% at 72k + 16 calls.
- **Raw upper bound.** Charging the raw first-50-call growth of a session start (median 123k, 16.5 calls) as pure overhead gives 24.2% input (5.4% price). That treats the first task's whole work as orientation, so it is not a credible cold-start cost.

## Caveats
- **The confound: a first instruction is a different kind of task.** It usually opens a new piece of work ("look at X and do Y"). A mid-session instruction is more often a follow-up whose material is already in context. Part of the session-start excess is that difference, not the cost of being cold. Three checks:
  - The excess persists against long warm instructions. In the first 25 calls, warm instructions of 25+ calls show a mean of 8.0k orientation tokens and those of 75+ calls 13.3k, against 29.6k at session starts. This still leaves 16–21k excess.
  - Compactions, which restart mid-task with a summary, show a smaller excess of 6–17k.
  - Sub-agents, which start cold with only a task prompt, show 21–28k. But their task is usually reading, which overstates the excess.

  A restart at an instruction boundary with a 10k summary lies between a compaction (22k summary, same task) and a session start (no summary, new task). So the main-start excess is an upper estimate for a typical restart, and the compaction excess a lower one.
- **Starts are few and correlated.** There are 10 session starts from one user, 9 of them in one project, and S03/S09 dominate the sub-agents and compactions. Percentiles of 10 events are rough: p90 is about the second-largest start.
- **Orientation is identified by tool and command word.** Inline scripts that read files, and git or python readers, are classed as *run*. Command identity uses an exact hash, so reuse of near-identical commands is not seen. Image reads count 0 tokens, and thinking is visible only in the context-growth measure.
- **The replay simplifies.** The charge is uniform per restart, or drawn independently. T is carried until the next restart, and the extra calls ride on half of T. The summary-writing call itself, cache expiry across the restart, and any quality loss are not modelled. The price model is a series approximation: it gives the 390k ceiling 39.6% of price, where C5's money model with re-reads gave 29%. Compare price rows only within this table.
- **Prior use is a hashed working directory.** Paths under session-specific scratch directories never match across sessions, so the cross-session known share is a lower bound.

## Findings
1. A real cold start costs about **20–30k tokens of extra orientation and 3–9 extra read/search calls** beyond a warm instruction start (session starts: 20–27k, almost all in the first 10 calls; sub-agents: 21–28k; compactions: 6–17k). The 90th percentile is 45–110k tokens and 13–20 calls.
2. A cold start is largely **re-obtaining**. 45% of the files a new session reads in its first 25 calls had been used in an earlier session of the same project, and 70–76% of a sub-agent's reads were already used by its parent session. Exact command re-runs are invisible (0–2%).
3. Cold starts **do not delay the first edit**: median 12 calls at session start and 10 in sub-agents, against 17 at warm instruction starts. The cost is reading before the edit (about 30k against 2k tokens), not lost steps.
4. Charging every restart with the median observed cold start leaves the restart-above-200k lever at **51.9–53.0% of input (46.7–48.0% price)** instead of 55.2% (51.1%). With charges drawn from the real starts it saves 49–53%. The p90 charges give 41.2% (72k + 16 calls) down to 29.7–30.1%.
5. The lever falls below the 390k ceiling lever (42.8%) only if every restart costs about **100k fresh tokens** (75k with 10 extra calls, 52k with 20). In price the thresholds are 67k / 51k / 42k against 39.6%. That is 3–4× the median observed cold start, at or above its 90th percentile, so the cold start narrows the restart lever but does not overturn its lead.
