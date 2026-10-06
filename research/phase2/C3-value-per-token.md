> Working memo from cycle C3 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# C3 — The denominator: what was delivered per token processed?

## Method
- Source: `lines_v2.load()`, 10 sessions, main session + sub-agents pooled (sub-agent lines = isSidechain). Input = sum over distinct message.id of input + cache_read + cache_write (6.84e9 total, 18,543 calls, same as README v2). "Cost-equivalent" input = same usage priced 1 / 0.1 / 1.25 / 2.0 (uncached-equivalent tokens).
- Delivered work, from tool_use blocks only (deduplicated by tool_use id; assistant messages are split over several lines, one block per line), results via tool_result.is_error:
  - persisted tokens = estimate_tokens(Write content) + Edit/MultiEdit new_string + NotebookEdit new_source + shell file writes (heredoc bodies whose header is `cat/tee > file`, and `echo/printf > file` commands) + GitHub-MCP file content; distinct files = distinct target paths of those writes (in memory; "created" = Write + shell targets only);
  - commits = Bash commands containing `git commit` (not --dry-run) whose result is not an error (19 erroring ones excluded; 690 counted); pushes = `git push` not error; PRs = `gh pr create` / mcp create_pull_request not error; artifacts = Artifact tool, action publish (default), not asset upload, not error; SendUserFile counted separately;
  - tests = Bash commands matching a test-runner pattern (pytest, unittest, vitest, jest, node --test, cargo/go test, npm test, make test, `python test_*.py` ...) whose result is not an error. Strict variant additionally needs "pass/ok" and no "fail" in the result text.
- Output side: transcript output counts are stream-start values (untrustworthy), except S01. S02 and S03 have provider session-list outputs whose input matches the transcript (ratios 1.02, 0.93), so for S01-S03 only I use session-list output. S04-S10: not trustworthy, not used.
- Script: `run.py` (extraction), `an.py` (ratios); raw numbers `results.json`, `rows.json`.

## 1. Delivered work per session (pooled with sub-agents)
| id | type | input (M) | persisted tok | files (created) | commits | pushes | PRs | artifacts | tests (strict) | SendUserFile |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S01 | research/tool dev | 169.9 | 151,560 | 185 (185) | 21 | 22 | 1 | 0 | 51 (39) | 2 |
| S02 | app dev (feedback) | 611.8 | 106,614 | 51 (48) | 66 | 66 | 1 | 14 | 8 (1) | 6 |
| S03 | app dev (multi-repo, design) | 2,104.9 | 792,134 | 466 (466) | 318 | 300 | 0 | 121 | 4 (0) | 11 |
| S04 | automation pipeline | 29.8 | 51,079 | 41 (41) | 7 | 6 | 0 | 0 | 0 | 3 |
| S05 | game dev (feature) | 778.6 | 85,714 | 75 (66) | 48 | 46 | 0 | 0 | 0 | 11 |
| S06 | media tool | 166.3 | 70,511 | 54 (53) | 24 | 24 | 0 | 0 | 0 | 16 |
| S07 | research/optimisation | 8.6 | 10,386 | 2 (2) | 2 | 4 | 0 | 0 | 0 | 1 |
| S08 | game graphic design | 19.2 | 10,065 | 17 (10) | 4 | 5 | 0 | 0 | 0 | 3 |
| S09 | game dev (feature) | 1,831.9 | 428,084 | 450 (437) | 127 | 120 | 0 | 6 | 4 (0) | 12 |
| S10 | game dev (balance) | 1,119.0 | 252,224 | 215 (207) | 73 | 74 | 0 | 0 | 1 (1) | 15 |
| all | | 6,840 | 1,958,371 | 1,556 | 690 | 667 | 2 | 141 | 68 (41) | 80 |

Sub-agents wrote 197k of the 1.96M persisted tokens (S03 38.5k, S09 159k) and made no commits (all 690 are main-session). Mean persisted size is small: 2.8k tokens per commit overall; Edit new_string tokens are 9% of persisted (S10 35%, S05 25%). Docs-connector payload (S02 only, 7.1k tokens) is not included.

## 2. Input processed per unit of delivered work
| id | input / persisted token | input / commit (M) | input / file (M) | input / push (M) | cost-eq / persisted token | cost-eq / commit (M) | persisted tok / commit |
|---|---:|---:|---:|---:|---:|---:|---:|
| S01 | 1,121 | 8.09 | 0.92 | 7.72 | 133 | 0.96 | 7,217 |
| S02 | 5,738 | 9.27 | 12.00 | 9.27 | 707 | 1.14 | 1,615 |
| S03 | 2,657 | 6.62 | 4.52 | 7.02 | 322 | 0.80 | 2,491 |
| S04 | 583 | 4.25 | 0.73 | 4.96 | 119 | 0.87 | 7,297 |
| S05 | 9,083 | 16.22 | 10.38 | 16.93 | 1,097 | 1.96 | 1,786 |
| S06 | 2,359 | 6.93 | 3.08 | 6.93 | 300 | 0.88 | 2,938 |
| S07 | 830 | 4.31 | 4.31 | 2.16 | 115 | 0.60 | 5,193 |
| S08 | 1,911 | 4.81 | 1.13 | 3.85 | 335 | 0.84 | 2,516 |
| S09 | 4,279 | 14.42 | 4.07 | 15.27 | 518 | 1.74 | 3,371 |
| S10 | 4,436 | 15.33 | 5.20 | 15.12 | 547 | 1.89 | 3,455 |

Across the 10 sessions (median; IQR; min-max):
| unit | median | q25-q75 | min-max | pooled (sum/sum) | pooled excl. S03, S09 |
|---|---:|---|---|---:|---:|
| input per persisted token | 2,508 | 1,319-4,397 | 583-9,083 | 3,493 | 3,933 |
| input per commit | 7.5M | 5.3M-13.1M | 4.3M-16.2M | 9.9M | 11.8M |
| input per distinct file written | 4.2M | 1.6M-5.0M | 0.73M-12.0M | 4.4M | 4.5M |
| input per push | 7.4M | - | 2.2M-16.9M | 10.3M | 11.8M |
| input per artifact (S03: 121; S02: 14; S09: 6) | - | - | S03 17.4M, S02 43.7M, S09 305M | 48.5M | - |
| cost-eq per persisted token | 329 | - | 115-1,097 | 427 | 487 |
| cost-eq per commit | 0.92M | - | 0.60M-1.96M | 1.21M | 1.47M |
| API calls per commit | 25 | - | 17-45 | 27 | - |

In plain terms: one commit cost about 10M input tokens processed (0.9-1.2M if priced at the cache-weighted rate), one distinct file about 4M, one persisted token about 3,500 input tokens (about 430 at price-equivalent).

## 3. Variation with session type and size
- By type (pooled, input per persisted token / per commit / per file): code, app and game dev (S02, S03, S05, S09, S10) 3,872 / 10.2M / 5.1M; tool and pipeline (S01, S04) 986 / 7.1M / 0.88M; media tool (S06) 2,359 / 6.9M / 3.1M; research (S07) 830 / 4.3M / 4.3M (one file, n=1); design (S08) 1,911 / 4.8M / 1.1M. Tool-building and research sessions deliver more characters per file and per commit (5-7k persisted tokens per commit vs 1.6-3.5k), so they are cheaper per token; game and app sessions are 3-4x more expensive per persisted token. Feature game sessions S05, S09, S10 are the most expensive per commit (14-16M); S03 (app, many small commits) is cheapest of the large ones (6.6M).
- By size (Spearman over 10 sessions, no p-values, n small): input size vs input per persisted token rho 0.68; vs input per commit 0.66; vs input per file 0.49; vs persisted tokens per commit -0.38; vs API calls per commit 0.07. Large sessions (>=0.6B: S02, S03, S05, S09, S10): 3,872 per persisted token, 10.2M per commit, 5.1M per file; small (S01, S04, S06, S07, S08): 1,342, 6.8M, 1.3M. So larger sessions pay about 1.5x more input per commit and 2.9x more per persisted token; the commit effect comes from heavier context per call (calls per commit is flat), not from more calls.
- Spread across sessions: 16x per persisted token, 3.8x per commit, 16x per file. Commit is the steadiest unit; the token and file units mostly measure how big a commit's content is.

## 4. Output side (S01-S03 only, session-list output)
S01 622,625 output; S02 1,215,393; S03 6,312,669. Output per persisted token: 4.1 / 11.4 / 8.0 (pooled 7.8); output per commit 29.6k / 18.4k / 19.9k (pooled 20.1k); output per file 3.4k / 23.8k / 13.5k; input per output 354 pooled. About 11-24% of output tokens (persisted / output 0.24, 0.09, 0.125) end up as file content; the rest is text, reasoning and tool-call text that is not persisted.

## 5. Tests, PRs, artifacts
- Test commands not erroring: 68 total (S01 51, S02 8, S03 4, S09 4, S10 1); strict "passed" 41 (S01 39). 5 of 10 sessions have zero narrow-pattern tests; a looser pattern (any command mentioning test/spec/assert) gives about 2,400 hits but mostly paths and file names, so is an upper bound. Build/lint/typecheck-type commands (tsc, eslint, npm run build...) not tabulated per session beyond `results.json` (verify field, broad pattern). So tests per input is not a reliable denominator; indicative: S01 about 3.3M input per test run, others one test run per 76M (S02) to 1.1B (S10) input.
- PRs: 2 created in the whole data (S01, S02). Artifacts: 141 successful publish calls (S03 121 over 79 distinct file/URL targets, S02 14, S09 6); S03's 5 days of artifact work cost about 17M input per publish.
- 80 SendUserFile deliveries (S06 16, S10 15, S09 12, S03 11, S05 11); not valued.

## Caveats
- Edit new_string counts only replacements; it omits deleted/moved text, so refactoring-heavy sessions look under-delivered. Writes by python -c/ node -e scripts and other generators are not counted. Heredoc/echo writes depend on regex, so file counts may include repeated spellings of a path (relative vs absolute) and miss unknown ones (rough +/- 10%).
- Commits differ greatly in size (persisted tokens per commit span 1.6k-7.3k). `git commit` that was chained after failing steps may count once; commit count may include commits containing only deletions or docs. Commit count per session is 690 with 19 erroring commits excluded (S10 11).
- Sessions of research/design type (S07, S08) deliver documents/images; their "persisted tokens" omit image content, so their ratio is an upper bound. S07 has n=2 commits and 2 files.
- Input is dominated by cache reads (99%), so "input processed per unit" mostly reflects context length x calls; the cost-equivalent figures are the better price proxy.
- Output counts exist only for S01-S03 (see above). Session-list output of S01 (622,625) differs from the transcript sum (729,469) by 17% due to snapshot timing; session-list output was used.
- Per-session n=10 and heavy-tailed sizes: medians and pooled values differ by 1.3x; pooled values are dominated by S03, S09, S10 (73% of input).

## Findings
1. One commit cost a median 7.5M input tokens processed (IQR 5.3-13.1M, range 4.3-16.2M; pooled 9.9M), or about 0.9-1.2M price-equivalent tokens; 690 commits in 6.84B input.
2. One persisted token (file content written) cost a median 2,500 input tokens (IQR 1.3k-4.4k; pooled 3,500, range 580-9,100); one distinct file written about 4.2M (pooled 4.4M).
3. Cost per unit grows with session size (rho 0.66-0.68 for per commit / per persisted token); feature game sessions are most expensive per commit (14-16M), tool-building and research sessions cheapest per persisted token (about 1,000).
4. Output per commit is about 20k tokens (S01-S03 only); only 9-24% of output tokens become file content, so input processed per output token (354 pooled) dwarfs any delivery ratio.
5. Test runs, PRs and artifacts are too sparse to serve as a denominator (68 test commands, 2 PRs, 141 artifact publishes concentrated in S03).
