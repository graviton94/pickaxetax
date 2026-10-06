> Working memo from cycle A3 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots. Paths were compared in memory only and never recorded.

# A3: pointer instead of authored content, replayed with real behaviour

Numbers only; computed in memory from the 10 main sessions (dataset-v2), no text stored. Scripts: `run.py`, `sim.py`, `part1.py`, `part1b_mod.py` in this folder; outputs `replay.json`, `regimes.json`, `part1.json`, `part1b.json`.

## Method
- Parsing loop copied from A2 (asserted identical segment and context counts to `bound.read_trace_lines`), then `bound.calibrate` + `bound.link`. Each tool_use also yields an event (call index, tool, path, shell command kept in memory only).
- Path key: Write/Edit/MultiEdit/NotebookEdit/Read path, or shell redirect target (`cat >`, `tee`, `>`, `>>`, heredoc). Spellings merged by path-suffix. Shell commands that mention a path are typed per command segment (split on `; && || |` and newlines): write target (full or append), `sed -i`/`perl -i` (edit), `cat/head/tail/sed -n/less/nl/bat` (read), `grep/rg/awk` (grep), else mention (run etc.). Matching on full path or basename token (strict variant: last two components).
- Unit = one full file write (Write tool: 458; shell full write with a detectable target: 894). Its life runs until the next full rewrite of the same path. Appends (`>>`) are counted as uses.
- Replay (static, observed compaction windows): authored segments (Write/Edit/MultiEdit/NotebookEdit inputs, shell file writes, inline scripts) are a 30-token stub from birth. Re-fetch only for file writes (unit content = write + appends): at the first Edit/`sed -i` of the path inside the same window that is not preceded by a read (Read, cat-type or grep) after the write in that window. Cost = content tokens x calls carried (from the next call until next rewrite or window end). Reads cost nothing extra. Edit inputs are stubbed without re-fetch (Claude Code forces a Read before editing a file it did not write). Inline scripts: stub, never re-fetched. Net = (carried residency - stub residency - re-fetch residency) / measured input.
- Regimes (coordinator addition, `sim.py`): context replayed call by call as base + sum of present segments (authored = stub, summary and unattributed included at fired compactions). (1) observed: every observed compaction fires. (2) ceiling: an observed compaction fires only if replayed context before it >= 90% of observed pre-compaction context; otherwise it is skipped (the summary and unattributed segments born there are dropped, window continues, so re-fetch triggers can now reach back further) and the replay compacts itself when replayed context >= the session's observed maximum context, resetting to base + 22,000 and charging one read of the full replayed context. The observed-compaction simulation reproduces the static replay within 0.05 pt (20.28 vs 20.33; differences in re-fetch bookkeeping).
- Lexical estimate recomputed on the identical group with bound refs (min_shared=1): stub 30, 1,000 tokens per later ref.

## 1. Behaviour after an authored file write (1,352 units, 3.84 M calibrated tokens)

| | all units | Write tool (458) | shell file write (894) |
|---|---|---|---|
| later edited (Edit/MultiEdit/NotebookEdit/`sed -i`) before next rewrite, % | 16.3 | 28.4 | 10.2 |
| ... edited inside the write's compaction window, % | 9.5 | 21.2 | 3.5 |
| token share of writes later edited, % | 24.7 | 35.4 | 14.6 |
| later read by Read/cat-type, % | 26.0 | 34.1 | 21.9 |
| later read incl. grep, % | 29.1 | 39.3 | 23.8 |
| later mentioned otherwise (run etc.), % | 64.0 | 85.8 | 52.8 |
| any later use, % | 68.3 | 89.7 | 57.4 |
| rewritten later, % | 23.1 | 13.1 | 28.2 |
| never used and never rewritten, % | 19.7 | 7.2 | 26.1 |
| edits per edited unit | 2.2 | 2.5 | 1.7 |

Calls between the write and the first later use (units that have one):

| first later | n | share <= 1 call | share <= 5 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|---|---|
| use of any kind | 924 | 44.5 | 66.2 | 1 | 2 | 12 | 80 |
| edit | 221 | 10.9 | 21.7 | 8 | 57 | 180 | 874 |
| read (incl. grep) | 393 | 8.4 | 16.3 | 17 | 108 | 286 | 784 |
| rewrite (life length) | 312 | 7.4 | 26.3 | 4 | 37 | 382 | 1,585 |

Per session, share of units edited: S01 13.8, S02 22.5, S03 27.8, S04 16.3, S05 2.7, S06 27.9, S07 50.0 (2 units), S08 20.0 (10 units), S09 9.0, S10 5.8. Strict path matching: 10.7% edited (vs 16.3).

Edits and a preceding read (any Read, cat-type or grep between the path's last full write and the edit):

| edit class | edits | preceded by a read (any window), % | write in same window | of those, read in the same window, % |
|---|---|---|---|---|
| tool edits, path written in session | 179 | 26.8 | 129 | 10.9 |
| `sed -i`, path written in session | 302 | 68.2 | 118 | 28.0 |
| all edits after an in-session write | 481 | 52.8 | 247 | 19.0 (14.2 if grep not a read) |
| tool edits, path not written in session | 691 | 99.9 | n/a | n/a |
| `sed -i`, path not written in session | 37 | 81.1 | n/a | n/a |

So when an edit follows an in-session write inside the same window, 81% of the time the agent edits without having re-read the file (it relies on the text it wrote); edits to files it did not write are read first (the harness requires it).

## 2. Behavioural replay (observed compaction windows), % of main-session measured input

Pooled: carried residency minus stub 21.46, re-fetch cost 1.13 (101 re-fetches = 7.5% of units, mean 3,600 tokens, median 162 calls carried, median 8 calls after the write), net 20.33.

Gross saving by class (pt of measured input): inline scripts 9.91, Write tool 5.56, shell file writes 3.70, Edit-type inputs 2.29.

Per session net (%): S01 33.3, S02 17.2, S03 21.4, S04 29.4, S05 16.9, S06 23.6, S07 9.3, S08 3.7, S09 20.0, S10 20.5.

## 3. Sensitivity and compaction regime (pooled net, % of measured input)

| variant | static replay | observed compactions (sim) | ceiling-triggered (sim) |
|---|---|---|---|
| main (stub 30, 1x, scripts in) | 20.33 | 20.28 | -3.76 |
| re-fetch 2x content | 19.21 | 19.09 | -3.13 |
| stub 100 | 19.06 | 19.00 | -2.55 |
| scripts excluded | 10.43 | 10.37 | -2.28 |
| 2x + stub 100 + grep not a read | n/a | 17.56 | -2.14 |
| grep not a read | 20.08 | | |
| edit segments also re-fetched (pessimistic) | 19.03 | | |
| inline scripts + heredoc-other (git messages) in | 21.20 | | |
| 2x + stub 100 + grep not read + edit re-fetch | 14.45 | | |
| strict path matching | 20.53 | | |

Ceiling regime in detail (main): of 34 observed compactions, 2 fire (replayed context rarely stays >= 90% of the observed pre-compaction context with a ~20% saving), 32 are skipped and 25 replay-triggered compactions occur; charged reads are 0.3% of measured input. Per session (observed compactions / fired / skipped / ceiling-triggered; net %): S01 1/0/1/0, 4.4; S02 3/0/3/3, 0.5; S03 14/1/13/10, 0.6; S05 3/0/3/2, -6.0; S06 1/0/1/1, -17.9; S09 7/1/6/5, -6.5; S10 5/0/5/4, -8.4; S04, S07, S08 never compact: 29.4, 9.3, 3.7 unchanged.

## 4. Versus A2's lexical estimate (same group: Write/Edit + file writes + inline scripts)
- Lexical (1,000 tokens per later lexical ref, 27.0 later refs per segment, min_shared=1): 19.02; A2 reported 19.8 for its (a)+(b) incl. heredoc-other (19.75 recomputed here). Strict subset without scripts: lexical 10.5, behavioural 10.43 (A2: 10.5). Behavioural replay of the same group: 20.33 (21.20 with heredoc-other).
- Gross carried-minus-stub saving is identical in both (21.46); only the cost of re-access differs: lexical 2.44, behavioural 1.13. Lexical charges 27 refs per segment (mostly coincidental identifier overlap, 7.4 at min_shared=3) at a flat 1,000; behaviour charges only a real Edit that needs exact old text (7.5% of units, 101 events) but charges the whole file for the rest of the window (3,600 tokens x ~200 calls). The two roughly offset, so the headline is close (about +1.3 pt behaviourally); the estimate is dominated by the stub residency term, not by the re-fetch model. Per session the two differ by up to 6 pt (S04 35.0 lexical vs 29.4, S06 28.0 vs 23.6, S09 17.6 vs 20.0).
- What neither model captures: the 81% of in-window edits made without a re-read mean the stubbed text is actually used from memory, so the stub only works if the agent can reload it on demand; the replay prices that reload, not the quality risk.

## Caveats
- Shell write detection is regex-based (targets with `$` variables dropped; units without a detectable path, and multi-target commands, use the first target). Basename matching can merge same-named files in different directories (strict variant shown). Inline python that edits a file is not seen as an edit.
- Ceiling = the session's observed maximum context, not a fixed 783k; reset target base + 22,000 as specified. The 90% rule skips almost all observed compactions at a ~20% saving, so the ceiling result is close to "a policy that never compacts early". Skipped compactions also drop the summary and unattributed (thinking/harness) segments that were born at the compaction call.
- Tokens are bound-calibrated; the denominator is measured input (sum of per-call contexts), uncached units, no cache pricing.

## Findings
1. Authored file content is mostly reused soon but rarely edited: 68% of 1,352 file writes get any later use (median 2 calls), only 16% are later edited (28% Write tool, 10% shell), 29% are read back, 23% are rewritten.
2. 81% of edits that follow an in-session write inside the same window are made without re-reading the file; only the harness-enforced read makes edits to non-authored files (99.9%) safe.
3. Behavioural replay gives 20.3% net saving of measured input (gross 21.5, re-fetch 1.1; inline scripts 9.9 pt of it, Write tool 5.6, shell files 3.7, Edit inputs 2.3), within 1.3 pt of A2's lexical 19.0 on the same group; sensitivities range 14.5 to 21.2 (10.4 without inline scripts).
4. The lexical and behavioural re-fetch models disagree on mechanism (27 coincidental refs at 1,000 vs 101 real file reloads at 3,600 tokens x about 200 calls) but cancel to similar totals; the saving is a stub-residency effect.
5. The saving does not survive a ceiling-triggered compaction regime: pooled net -3.8% (-2.1 to -3.1 in the sensitivities), kept only in the three sessions that never compact (S04 29.4, S07 9.3, S08 3.7).
