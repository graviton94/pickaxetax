> Working memo from cycle A2 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots. Commands were classified by their structure only and never recorded.

# Phase 2 / A2: content that is both on disk and in the context

## Method
- Same 10 main sessions (dataset-v2 cut), main session only. `bound.read_trace_lines` loop copied locally (asserted identical segment and context counts), each tool_input / persisted_write segment labeled by regexes on the command structure (nothing printed or stored as text), then `bound.calibrate` + `bound.link` (min_shared=1; sensitivity min_shared=3).
- Classes. (a) Write/Edit/MultiEdit/NotebookEdit (bound's `persisted_write`). Shell (Bash) commands are split by priority: (b-file) `cat >`/`cat >>`, `tee`, `printf ... >`, or a heredoc with a redirect to a file; (b-script) `python - <<`, `python -c` over 500 chars, `node -e` (inline code, not necessarily saved to disk); (b-heredoc-other) any other `<<` (mostly git commit messages); (c) other shell; (d) all other tools (Read, Grep, Agent, mcp, ...). "(b)" = b-file + b-script + b-heredoc-other. `echo ... >` is not in (b) (it falls in c).
- Residency = calibrated tokens x (end - birth). "Share of visible" uses the sum over non-unattributed segments (all kinds) as denominator; visible = 57.6% of measured input pooled. Idle / dead as in bound refs (idle = calls that are not a ref call, birth counts as a ref; dead = after the last ref).
- A segment is born the call after the one that wrote it, so all its residency is "after the call that wrote it"; "after birth call" excludes the first call that consumes it (differs by <0.2 pt).
- What-if (Q2): from birth, the segment costs min(30, n) tokens per call instead of n; each later ref (refs[1:], lexical) costs +1,000 once. Net saved = n*(end-birth) - stub residency - 1000*later refs. The "selective" variant (only stub where net > 0) is identical to "all" at the 2 d.p. shown, since net > 0 for 99.3% of segments.
- Read-back (Q3): write W has distinctive terms (bound's TOKEN_RE, minus the session's common terms); testable if >= 8 terms. W is "read back" if (i) a later tool_result (same window, before any compaction) from a Read or a Bash read command (cat/head/tail/sed -n/less/nl/bat) shares >= 30% of W's terms, or (ii) path match: a later Read of the same file_path, or a later read command containing the write's path (a: file_path; b: the redirect target). "Either" = (i) or (ii), over all writes (untestable ones can only count by path).

## 1. Classes of tool_input (pooled, 10 sessions)

| class | segments | tokens (M) | % visible resid. | % measured input | idle % | dead % |
|---|---|---|---|---|---|---|
| (a) Write/Edit/MultiEdit/NotebookEdit | 1,328 | 2.37 | 13.9 | 8.0 | 76.8 | 4.8 |
| (b-file) cat >/tee/printf >/heredoc > file | 857 | 1.68 | 6.5 | 3.8 | 75.1 | 5.5 |
| (b-script) python - <<, python -c >500, node -e | 3,757 | 4.07 | 17.7 | 10.2 | 80.4 | 6.9 |
| (b-heredoc-other) other `<<` | 223 | 0.30 | 1.5 | 0.9 | 74.3 | 1.4 |
| (c) other shell | 7,433 | 0.92 | 5.1 | 2.9 | 94.6 | 36.0 |
| (d) other tools | 2,479 | 0.32 | 1.4 | 0.8 | 87.4 | 29.8 |
| all tool inputs incl. (a) | 16,077 | 9.67 | 46.1 | 26.6 | | |
| (b) total | 4,837 | 6.05 | 25.7 | 14.9 | | |
| (a)+(b) total | 6,165 | 8.42 | 39.7 | 22.9 | 78.0 | 5.7 |
| (a)+(b-file) ("surely on disk") | 2,185 | 4.05 | 20.5 | 11.8 | 76.2 | 5.0 |

(The earlier A "tool_input 32.3%" excluded persisted_write; with it, inputs are 46% of visible residency.) Shell content writers (b) are the larger part; (b-script) alone is the largest single class. Inline scripts mostly drive analysis and are not files, so (b-file) is the clean on-disk subset; (b-script) is on disk only in the sense that it is code the agent authored.

Per session: share of visible residency (a / b-file / b-script / b-hd-other / c / d), then (a)+(b) as % of measured input and its idle/dead.

| session | a | b-file | b-script | b-hd | c | d | (a)+(b) % meas | idle % | dead % |
|---|---|---|---|---|---|---|---|---|---|
| S01 | 36.0 | 18.5 | 9.3 | 0.5 | 2.4 | 5.6 | 37.3 | 84.6 | 17.1 |
| S02 | 8.1 | 5.7 | 15.2 | 0.1 | 4.2 | 2.2 | 18.1 | 81.1 | 7.1 |
| S03 | 11.7 | 8.9 | 18.0 | 0.1 | 5.5 | 1.3 | 23.2 | 72.3 | 4.2 |
| S04 | 62.3 | 6.0 | 6.0 | 0.0 | 4.4 | 0.7 | 37.3 | 88.6 | 28.8 |
| S05 | 6.1 | 4.8 | 19.6 | 1.9 | 4.9 | 0.6 | 19.3 | 79.9 | 4.5 |
| S06 | 48.6 | 1.4 | 18.5 | 1.0 | 3.0 | 0.9 | 31.4 | 84.0 | 10.0 |
| S07 | 18.4 | 0.0 | 1.2 | 2.2 | 5.1 | 0.5 | 10.4 | 71.1 | 10.2 |
| S08 | 13.4 | 4.1 | 0.3 | 0.0 | 3.9 | 1.4 | 4.4 | 92.5 | 45.0 |
| S09 | 14.7 | 3.2 | 19.8 | 4.1 | 5.0 | 1.4 | 23.9 | 78.3 | 4.3 |
| S10 | 17.8 | 7.6 | 15.7 | 1.3 | 5.7 | 1.1 | 22.3 | 82.8 | 6.1 |
| pooled | 13.9 | 6.5 | 17.7 | 1.5 | 5.1 | 1.4 | 22.9 | 78.0 | 5.7 |

## 2. Already persisted, still carried; stub what-if

| group | % of measured input carried after the writing call | stub resid. | re-fetch cost (1,000 x later refs) | net saved, % of measured input | later refs / segment |
|---|---|---|---|---|---|
| (a)+(b) | 22.9 | 0.56 | 2.58 | 19.8 | 27.6 |
| (a)+(b-file) | 11.8 | 0.24 | 1.05 | 10.5 | 31.6 |
| (a) only | 8.0 | 0.18 | 0.68 | 7.2 | 33.8 |
| (b) only | 14.9 | 0.39 | 1.90 | 12.6 | 25.9 |
| (b-file) only | 3.8 | 0.06 | 0.37 | 3.3 | 28.3 |
| (b-script) only | 10.2 | 0.30 | 1.39 | 8.5 | 24.3 |

Per-session net saved for (a)+(b), % of measured input: S01 35.0, S02 16.6, S03 20.7, S04 35.0, S05 16.1, S06 28.4, S07 9.6, S08 3.4, S09 19.6, S10 18.7.

Sensitivity: with min_shared=3 (fewer coincidental refs) later refs drop to 7.7 per segment, re-fetch cost to 0.72%, net saved (a)+(b) = 21.6%, (a)+(b-file) = 11.2%. Break-even per-ref re-fetch cost (net = 0) is about 8,600 tokens at min_shared=1 and about 30,000 at min_shared=3, i.e. the result is insensitive to the 1,000 assumption.

## 3. Read-back of writes (path match or >= 30% shared terms, with a read-type result)

| group | writes | terms-based (>=30%), % of testable | looser (>=10%) | path-based, % of writes | either, % of writes | token share read back | residency share read back |
|---|---|---|---|---|---|---|---|
| (a)+(b) | 6,165 | 3.3 | 16.0 | 13.0 | 15.2 | 12.0 | 15.0 |
| (a)+(b-file) | 2,185 | 4.3 | 19.9 | 21.1 | 23.1 | 14.2 | 17.6 |
| (a) | 1,328 | 6.7 | 28.3 | 17.6 | 20.7 | 10.7 | 14.9 |
| (b-file) | 857 | 1.3 | 8.9 | 26.5 | 26.7 | 19.1 | 23.2 |
| (b-script) | 3,757 | 2.9 | 14.4 | 8.9 | 11.3 | 10.5 | 12.9 |

Per session, share of (a)+(b) writes read back (either test): S01 20.3, S02 9.9, S03 9.2, S04 7.1, S05 29.2, S06 21.1, S07 22.2, S08 21.1, S09 17.6, S10 11.7.
Allowing any tool_result (not only reads) at >= 30% terms raises the terms figure from 3.3% to 9.9% (the content is echoed by test runs, diffs, greps).

## Caveats
- Residency of (a)/(b) is mechanically "carried after write": whether a stub is safe depends on the agent not needing the text, and lexical refs (any single shared rare term in a later output) are a crude proxy. A ref count of ~28 per segment is dominated by common-ish identifiers; min_shared=3 gives ~8.
- The stub what-if ignores that Edit needs exact old text, that the model loses its memory of what it wrote (re-derivation/quality risk), prompt-cache effects, and the cost of the stub mechanism. It is an upper bound on pure token saving.
- Read-back is approximate: reading code to understand it leaves terms but a partial `sed -n` range or `grep` hit (grep is not counted as a read) may fall under the threshold; Write results echo nothing. Path matching uses substring on the command so relative vs absolute spellings may miss. Read-back figures are therefore lower bounds on later use; they ignore the writes' own re-use via lexical refs (Q2).
- (b-script) is code, not necessarily a file; do not read it as "duplicated on disk". The strict on-disk number is (a)+(b-file) = 11.8% of measured input.
- Residency is token-calls under the calibrated segment sizes (factor ~2 over the text estimate); the denominators are pooled sums, so S03/S09/S10 dominate pooled figures.

## Findings
1. Content authored into files (Write/Edit plus shell-inline file writes and scripts) holds 39.7% of visible residency, 22.9% of measured input; the strict on-disk subset (Write/Edit + cat>/tee/printf>/heredoc>) is 20.5% / 11.8%.
2. Shell inline writers are larger than the Write tool: (b) is 14.9% of measured input vs 8.0% for (a); the whole-file-through-shell suspicion holds, but 70% of (b) is inline python/node scripts rather than file bodies.
3. Content stays carried: 78% of it is idle and only 5.7% dead, i.e. it is referenced lexically along the way, yet only about 15% of such writes are ever read back by a Read/cat (13% by path; 3% by >=30% term overlap).
4. A 30-token stub with 1,000-token re-fetch per lexical ref would save 19.8% of measured input for (a)+(b) (10.5% for the strict subset); results are insensitive to the re-fetch price (break-even above 8,600 tokens per ref).
5. The saving is very uneven by session: 35% (S01, S04) down to 3-10% (S07, S08); S04/S06 are Write-heavy (a = 62%/49% of visible residency).
