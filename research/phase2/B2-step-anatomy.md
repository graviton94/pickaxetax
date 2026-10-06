> Working memo from cycle B2 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots. Commands were classified by their structure only and never recorded.

# B2 - What makes an instruction take many steps?

Scope: main session (non-sidechain) API calls of the 10 sessions in the v2 dataset snapshots; usage de-duplicated per message.id (max per field); context of a call = input + cache_read + cache_write; instruction = `_is_instruction`; a step belongs to the latest preceding instruction. 16,181 steps, 667 instructions, 6.58 G input tokens. No transcript text, commands or paths are reproduced here; only counts and category labels.

## Method

- Step = one unique message.id. A step with several tool calls takes the highest-priority class among them: sub-agent > edit > run-verify > vcs > wait-poll > mcp > read > other; no tool_use = text-only.
- Tools: Write/Edit/MultiEdit/NotebookEdit = edit; Read/Grep/Glob = read; Task/Agent/SubagentHandback/ListAgents/SendMessage = sub-agent; Monitor/ScheduleWakeup/ReadNotifications = wait-poll; mcp__* = mcp; TaskCreate/TaskUpdate/Artifact/SendUserFile/ToolSearch/AskUserQuestion/Skill/Web* = other.
- Bash: quoted strings and heredoc bodies are stripped, then regexes in order: vcs (git add/commit/push/checkout/merge/rebase/reset/stash..., gh pr create/merge) > wait-poll (sleep, until, watch, wait, gh run/pr/api/issue, curl/wget) > edit (cat/tee >, heredoc to cat, sed -i, mv/cp/rm/mkdir/touch, printf/echo >) > run-verify (pytest, python script/-m/-c/stdin, npm/npx/node, make, cargo, go, tsc, eslint, playwright, ruff, sh scripts, docker...) > edit by other `>` redirect > read (cat/head/tail/sed -n/grep/rg/find/ls/git log|show|diff|status/jq/wc...) > other.
- Error result of a verify step: `is_error` OR failure markers in the result text (Traceback, N failed, FAILED, Exit code != 0, error:, npm ERR!, etc.) = 'broad'; `is_error` alone = 'strict'.
- Edit-verify loop (cycle): among the edit/run-verify steps of one instruction, edit -> verify(error) [-> more error verifies] -> edit. Loop steps = every step from the starting edit to the failing verify (reads in between included). A chain = consecutive cycles. Polling loop = a run of >= 2 strictly consecutive wait-poll steps in one instruction; 'identical' = result text equal to the previous poll in the run (exact, and with digits masked).
- What-if: polling run of k steps becomes one call, saving (k-1)/k of its input; each edit-verify chain loses one iteration, saving the chain's mean iteration cost (overlaps counted once, per step max). Low bound: cheapest iteration per chain + only identical polls removed.

## 1. Step classes (share of steps % / share of input %)

| session | steps | input M | read | edit | run-verify | vcs | wait-poll | sub-agent | mcp | text-only | other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S01 | 400 | 169 | 11 / 8 | 24 / 21 | 19 / 14 | 6 / 6 | 13 / 17 | 0 / 0 | 13 / 17 | 7 / 9 | 7 / 7 |
| S02 | 1303 | 575 | 29 / 27 | 9 / 9 | 26 / 26 | 5 / 6 | 8 / 9 | 0 / 0 | 7 / 8 | 11 / 12 | 3 / 3 |
| S03 | 4820 | 2055 | 28 / 25 | 12 / 12 | 26 / 27 | 7 / 7 | 9 / 9 | 0 / 1 | 3 / 3 | 11 / 12 | 4 / 4 |
| S04 | 166 | 30 | 10 / 10 | 45 / 36 | 25 / 29 | 2 / 2 | 10 / 14 | 0 / 0 | 0 / 0 | 5 / 7 | 2 / 1 |
| S05 | 1923 | 779 | 43 / 39 | 12 / 11 | 34 / 38 | 4 / 4 | 5 / 5 | 0 / 0 | 0 / 0 | 2 / 3 | 1 / 1 |
| S06 | 464 | 166 | 24 / 21 | 24 / 18 | 31 / 34 | 6 / 8 | 2 / 2 | 0 / 0 | 1 / 2 | 8 / 10 | 5 / 6 |
| S07 | 66 | 9 | 38 / 35 | 15 / 16 | 21 / 23 | 15 / 14 | 2 / 1 | 0 / 0 | 0 / 0 | 6 / 6 | 3 / 4 |
| S08 | 105 | 19 | 38 / 36 | 41 / 40 | 2 / 2 | 6 / 6 | 4 / 4 | 0 / 0 | 0 / 0 | 7 / 8 | 3 / 3 |
| S09 | 4056 | 1658 | 35 / 33 | 14 / 11 | 40 / 44 | 4 / 5 | 2 / 2 | 0 / 0 | 0 / 0 | 3 / 4 | 2 / 1 |
| S10 | 2878 | 1119 | 36 / 32 | 22 / 18 | 28 / 33 | 3 / 4 | 4 / 4 | 0 / 0 | 0 / 0 | 3 / 4 | 3 / 4 |
| POOL | 16181 | 6579 | 32 / 30 | 15 / 13 | 31 / 33 | 5 / 5 | 6 / 6 | 0 / 0 | 2 / 2 | 6 / 7 | 3 / 3 |

Pooled mean context per step by class (k tokens): read 370, edit 343, run-verify 440, vcs 440, wait-poll 434, sub-agent 530, mcp 529, text-only 486, other 425.
Of all steps, 22.8% (25.6% of input) are run-verify steps that are only ad-hoc inline python (`python - <<` / `python -c`); these are probably analysis rather than test runs. The rest of run-verify is node/npm/sh/pytest/lint. Per-step context varies only modestly across classes (343-530k), so input share tracks step share.

## 2. Loops (pooled, main definition)

| session | instr | edit-verify cycles | chains | cycle steps | cycle input % | poll runs (>=2) | poll-run steps | poll input % | polls after 1st | identical to prev | single polls | loop input % (union) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| POOL | 667 | 38 | 33 | 92 | 0.3 | 129 | 310 | 1.8 | 181 | 0 | 603 | 2.2 |
| S01 | 16 | 3 | 3 | 6 | 1.3 | 6 | 14 | 4.4 | 8 | 0 | 37 | 5.7 |
| S02 | 49 | 0 | 0 | 0 | 0.0 | 12 | 27 | 1.6 | 15 | 0 | 81 | 1.6 |
| S03 | 292 | 1 | 1 | 2 | 0.1 | 75 | 185 | 3.6 | 110 | 0 | 253 | 3.6 |
| S04 | 10 | 2 | 1 | 4 | 2.7 | 4 | 9 | 7.1 | 5 | 0 | 8 | 9.8 |
| S05 | 55 | 5 | 5 | 12 | 0.5 | 6 | 14 | 0.6 | 8 | 0 | 76 | 1.1 |
| S06 | 35 | 1 | 1 | 2 | 0.3 | 1 | 2 | 0.1 | 1 | 0 | 9 | 0.3 |
| S07 | 4 | 0 | 0 | 0 | 0.0 | 0 | 0 | 0.0 | 0 | 0 | 1 | 0.0 |
| S08 | 6 | 0 | 0 | 0 | 0.0 | 0 | 0 | 0.0 | 0 | 0 | 4 | 0.0 |
| S09 | 127 | 23 | 19 | 60 | 0.8 | 10 | 25 | 0.6 | 15 | 0 | 60 | 1.4 |
| S10 | 73 | 3 | 3 | 6 | 0.1 | 15 | 34 | 1.2 | 19 | 0 | 74 | 1.3 |

Sensitivity of the edit-verify loop (pooled):

| variant | cycles | instr with a cycle | cycle input % | poll runs | poll input % | what-if saving % (central) | low bound % |
|---|---|---|---|---|---|---|---|
| main(broad err) | 38 | 20 | 0.3 | 129 | 1.8 | 1.37 | 0.31 |
| strict is_error | 8 | 5 | 0.1 | 129 | 1.8 | 1.11 | 0.05 |
| broad, inline-python not verify | 49 | 27 | 0.8 | 129 | 1.8 | 1.79 | 0.74 |
| loose fail-then-edit | 81 | 49 | 1.1 | 129 | 1.8 | 2.13 | 1.07 |
| sleep/until polls only | 38 | 20 | 0.3 | 49 | 0.7 | 0.69 | 0.31 |

Verify steps: 4957; 9.0% return an error under the broad rule, 1.8% under is_error alone. Edit -> verify -> edit alternation regardless of result (the looser 'iteration' notion): 6.1% of input (7.8% of steps). Median cost of one edit-verify cycle: 0.4 M input.
Polling: 603 isolated wait-poll steps plus 310 steps in 129 runs. Of the wait-poll Bash steps, most contain sleep or an `until` wait inside the command (already a blocking wait); restricting to sleep/until/watch/gh-run polls leaves 49 runs / 0.7% of input. Consecutive polls were never identical (0 of 181 exact or digit-masked; line-overlap >= 0.9 in 1 of 181 pairs), so the W3 'no state change' candidate is not visible in this data.

## 3. Top 10% of instructions by input (pooled)

Threshold 24.3 M input; 67 instructions hold 42.2% of all input.

| group | instr | median steps | mean steps | median input M | mean ctx/step k | loop input % | cycle % | poll % | instr with any loop % |
|---|---|---|---|---|---|---|---|---|---|
| top 10% | 67 | 75 | 102 | 34.9 | 408 | 1.8 | 0.5 | 1.3 | 34 |
| rest | 600 | 11 | 16 | 4.6 | 406 | 2.5 | 0.2 | 2.3 | 12 |
| all | 667 | 13 | 24 | 5.5 | 407 | 2.2 | 0.3 | 1.8 | 14 |

Class mix, steps % / input %:

| group | read | edit | run-verify | vcs | wait-poll | sub-agent | mcp | text-only | other |
|---|---|---|---|---|---|---|---|---|---|
| top 10% | 36.7 / 33.6 | 16.0 / 13.8 | 31.4 / 34.2 | 4.0 / 4.5 | 5.1 / 5.5 | 0.3 / 0.4 | 1.6 / 2.4 | 2.9 / 3.7 | 2.0 / 2.1 |
| rest | 29.4 / 26.6 | 14.5 / 12.1 | 30.1 / 32.4 | 5.7 / 6.1 | 6.0 / 6.4 | 0.2 / 0.3 | 1.8 / 2.1 | 8.6 / 10.0 | 3.7 / 3.8 |

Other contrasts, top vs rest: steps before the first edit 11.5% vs 37.5% of steps; steps per edit 6.2 vs 6.9; instructions with at least one edit 100% vs 65.8%; steps in read streaks of >= 5: 8.6% vs 4.9%; edit-verify-edit alternation input share 8.9% vs 4.1%. 30.7% of all instructions contain no edit (they hold 11.0% of input). Per-session top-decile median steps range 14-135 vs 7-17 for the rest (S04 has a single top instruction).
Instructions that contain any loop: median 28 steps (n=93, 28% of input) vs 11 steps (n=574) without; log(steps) vs log(input) R2 = 0.825.

## 4. What-if (pooled input saved)

| scenario | saved % of main-session input |
|---|---|
| polling runs collapsed to one call | 1.1 (sleep/until-only runs: 0.4-0.7) |
| one fewer iteration per edit-verify chain (central / cheapest-iteration) | 0.31 / 0.31 (loose fail-then-edit definition: 1.1) |
| both, overlap-safe | 1.4 central; 0.3 low; about 2.1 under the loosest edit definition |

Per session (central %): S01 3.9, S02 0.9, S03 2.1, S04 5.4, S05 0.8, S06 0.3, S07 0.0, S08 0.0, S09 1.1, S10 0.8, POOL 1.4.

## Caveats

- Classification is regex-based on the command skeleton: a step with a heredoc python script cannot be told apart as analysis vs. file write vs. test; 22.8% of steps fall in that inline-python bucket and sit in run-verify by the spec's rule.
- Mixed-tool steps (642 of 16,181) take a single class by priority, which slightly over-weights edit and run-verify.
- Error detection is heuristic: text markers like 'error' in passing output can inflate failures, `is_error` alone undercounts (only 1.8% of verifies); the loop numbers bracket the truth between those two and both are small.
- Polling is strictly adjacent steps; a poll separated by a text-only or read step starts a new run. Many sleep polls already block inside one command (until-loops), so the one-call what-if is partly already realised.
- What-if ignores that removing steps also shrinks the context carried by later steps and that waits can lapse the prompt cache; it counts only the dropped steps' input, so it is a rough lower-order estimate. Sessions S01-S03 and S08 are truncated snapshots; S01 sub-agent lines are excluded (main chain only).
- Instruction boundaries follow `_is_instruction`; tool-result-only user turns and system-reminder prompts do not start a new instruction, so scheduled wake-ups may be folded into the previous instruction.

## Findings

- Steps, not step type, make instructions big: the top 10% of instructions (42% of input) have median 75 steps vs 11, at the same ~407k context per step.
- Step mix is read 32% / run-verify 31% / edit 15% of steps (30/33/13% of input); long instructions are slightly more read- and edit-heavy and have far fewer text-only steps (3% vs 9%), i.e. they are sustained tool-chains.
- Edit-verify-error-edit loops are rare (38 cycles, 0.3% of input; at most ~1% under looser definitions): verifies mostly pass, so rework loops do not explain long instructions.
- Polling loops are 129 runs holding 1.8% of input, concentrated in S03/S04/S01; none returned a result identical to the previous poll, so W3 'no state change' is not supported here.
- Collapsing polling loops and shaving one iteration per edit loop saves only ~1.4% of input (range 0.3-2.1%); big savings must come from fewer or cheaper steps in ordinary read/run/edit chains, not from loop elimination.
