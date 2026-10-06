> Working memo from cycle D5 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# D5: do edits fail more often right after a compaction?

Aggregates only. No transcript text, tool output, paths, commands or error messages were printed or stored;
error results were matched against category patterns in memory and only the category counts were kept;
file paths were mapped to per-session integers in memory. Scripts and their outputs are kept with the analysis files.

## Method
- Calls: main-chain calls indexed exactly like `bound.read_trace_lines` (asserted: same count and same
  context per call in all 10 sessions; 16,181 calls, 34 compactions, instruction starts from bound).
  Sub-agents: all sidechain lines, analysed separately (2,362 calls).
- Unit: one Edit / MultiEdit / Write / NotebookEdit tool use and its tool_result. Classes (first match wins,
  matched on the lower-cased result text of is_error results): **stale** (replacement text not found / not
  unique), **state** (harness refusal: file not read yet / modified since read), then reject, no-op, missing,
  exists, input, hook, permission, size (together "other"), else **unclassified**. Check: non-error results
  that match the stale/state patterns are counted too.
- Secondary proxy (the Edit tool carries only part of the file changes): shell edits = Bash commands with
  `sed -i`, or a python command containing a replace (`.replace(`/`re.sub(`) and a file write; failure =
  is_error; split into "stale-like" (assert / not found / no match ...) and other. Over-inclusive (some
  python scripts write analysis outputs, not source edits).
- Windows: first N = 10 / 50 calls after (a) each of the 34 compactions, (b) every instruction start
  (A6's boundaries, all contexts), (c) instruction starts after an idle gap > 1 h (63). Control (A5): calls
  at least 100 calls after the last compaction or session start. Also a gradient by calls since compaction.
- Noise: (i) placebo: the same number of pseudo-compactions per session at uniform random calls, 5,000
  draws, one-sided p = share of draws with a pooled window rate >= observed; (ii) session cluster bootstrap
  (7 compacting sessions, 5,000) of post-window rate minus control rate; (iii) leave S03 out; (iv) power:
  failures needed in the post window for a one-sided binomial p < 0.05 at the control rate.
- Knowledge age: for each edit, the last earlier touch of the same file (successful Read / Write / Edit
  tool; variants: + shell reads by D2's parser; Read tool only). "Pre" = that touch lies before the last
  compaction preceding the edit; "same cycle" = after it; "never" = no earlier touch. Fisher exact, one-sided.
- Cost: failing call to the next successful edit (same file, within 30 calls; variant any edit within 10);
  steps x context = sum of the context of those calls (input processed) and cost-weighted (0.1 cache read,
  2.0 / 1.25 writes). Per compaction: gross = cost of failures in the post window / 34; excess = (post rate
  - control rate) x post-window edits x mean cost; upper = same with the Clopper-Pearson 95% upper post rate.

## 1. Classes
| | attempts | success | stale (not found / not unique) | state (not read yet / modified since read) | other | unclassified |
|---|---|---|---|---|---|---|
| main, Edit | 870 | 866 | 3 (3 / 0) | 1 (0 / 1) | 0 | 0 |
| main, Write | 458 | 452 | 0 | 6 (3 / 3) | 0 | 0 |
| main, MultiEdit / NotebookEdit | 0 | | | | | |
| **main, all** | **1,328** | 1,318 | **3 (0.23%)** | **7 (0.53%)** | 0 | **0 (0%)** |
| sub-agents (47 Edit, 119 Write) | 166 | 166 | 0 | 0 | 0 | 0 |
| shell edits (471 sed -i, 3,139 python) | 3,610 | 3,560 | 3 stale-like | | 47 | |

Non-error results matching stale/state patterns: 0. Every edit-tool error was classified (target < 5% met).
Per session (main attempts / failures): S01 65/1, S02 27/0, S03 116/3, S04 55/0, S05 108/1, S06 101/0,
S07 8/0, S08 46/0, S09 339/3, S10 463/2. Edit-tool calls are 8.2% of main calls; shell edits are 2.7x as many.

## 2. Failure rate by window (pooled; failures / attempts)
| window | Edit+Write tool | Edit only | shell edits | both |
|---|---|---|---|---|
| all main calls | 0.75% (10/1328) | 0.46% (4/870) | 1.39% (50/3610) | 1.22% (60/4938) |
| control: >= 100 calls after compaction/start | 1.05% (7/667) | 0.71% (3/424) | 1.37% (40/2923) | 1.31% (47/3590) |
| first 10 after compaction | **0.00% (0/25)** | 0.00% (0/18) | 7.14% (2/28) | 3.77% (2/53) |
| first 50 after compaction | **0.56% (1/179)** | 0.00% (0/130) | 1.74% (4/230) | 1.22% (5/409) |
| first 10 after instruction start | 1.39% (4/287) | 0.89% (1/112) | 1.73% (19/1098) | 1.66% (23/1385) |
| first 50 after instruction start | 0.97% (7/719) | 0.49% (2/407) | 1.37% (39/2849) | 1.29% (46/3568) |
| first 10 after idle > 1 h | 0.00% (0/13) | | 2.16% (3/139) | 1.97% (3/152) |
| first 50 after idle > 1 h | 0.88% (1/114) | | 1.52% (9/593) | 1.41% (10/707) |

Gradient, Edit+Write tool, by calls since compaction: [0,10) 0/25, [10,50) 1/154, [50,100) 2/150,
[100,200) 2/228, [200,400) 2/182, 400+ 0/53. Shell: 2/28, 2/202, 6/368, 10/726, 18/1329, 4/472.
Per compacting session, edit tool, post-50 vs control: S01 0/8 vs 1/12; S02 0/4 vs 0/15; S03 0/19 vs 2/73;
S05 0/0 vs 1/80; S06 0/1 vs 0/34; S09 1/82 vs 1/162; S10 0/65 vs 2/290. Edit attempts per compaction:
0.74 in the first 10 calls, 5.3 in the first 50.

Noise:
| proxy, N | observed | placebo null median [5-95%] | placebo p | bootstrap post - control, 95% |
|---|---|---|---|---|
| edit tool, 10 | 0.00% | 0.00% [0-5.9%] | 1.00 | -2.2 .. -0.6 pt |
| edit tool, 50 | 0.56% | 0.90% [0-2.8%] | 0.66 | -2.2 .. +0.3 pt |
| shell, 10 | 7.14% | 1.22% [0-3.8%] | 0.001 | -1.5 .. +31.9 pt |
| shell, 50 | 1.74% | 1.21% [0.3-2.3%] | 0.20 | -1.1 .. +3.9 pt |
| both, 10 | 3.77% | 1.01% [0-3.2%] | 0.024 | -1.4 .. +10.5 pt |
| both, 50 | 1.22% | 1.15% [0.4-2.1%] | 0.44 | -1.2 .. +1.7 pt |

Without S03: edit tool 0/23 (N=10), 1/160 (N=50) vs control 5/594 (0.84%). Power: with 25 / 179 post-window
edits at the 1.05% control rate, only >= 2 failures (8%) / >= 5 failures (2.8%) would reach p < 0.05; the
95% upper bound of the post-50 edit-tool rate is 3.1% (N=10: 13.7%).
The shell signal at N=10 is two failures, in two sessions (S02, S09), both exactly 9 calls after their
compaction (on the window edge), both class "other" (not stale-like); at N=50 it is 4 failures, all "other".

## 3. Knowledge age (Edit + Write, failures / attempts)
| last touch of the file | tool touches | + shell reads | Read tool only |
|---|---|---|---|
| before the last compaction (pre-compaction knowledge) | 1/64 (1.6%; 95% upper 8.4%) | 0/58 (0%; upper 6.2%) | 1/95 (1.1%) |
| same cycle | 7/816 (0.86%) | 10/830 (1.20%) | 0/204 (0%) |
| never touched before | 2/448 (0.45%) | 0/440 | 9/1029 (0.87%) |
| Fisher p (pre > same) | 0.45 | 1.00 | 0.32 |

Same cycle, by distance (tool touches): Edit < 10 calls 2/530, 10-49 1/180, >= 50 1/70; Write 0/9, 1/21, 2/6.
Once shell reads count as touches, every failure has its file seen in the current cycle; the harness
refusals follow files changed or seen through the shell, not compaction (4 of 7 are "modified since read").

## 4. Cost of a failure (steps x context)
| | failures | steps to the successful retry | input per failure | cost-weighted | total |
|---|---|---|---|---|---|
| edit tool (same file, 30 calls) | 10 (9 resolved) | median 2, mean 2.9, max 11 | mean 1.2M, median 0.78M (fractional 1.17M) | ~0.13M | 12.1M (0.18% of main input) |
| edit tool (any edit, 10 calls) | 10 (10) | median 2, mean 2.2 | mean 0.91M | 0.10M | 9.1M |
| shell edits (any edit, 10 calls) | 50 (47) | median 2, mean 2.5 | mean 0.95M, median 0.60M | 0.10M | 47.4M |
| all | 60 | | | | 56.5M = 0.86% of main input (0.77% of cw) |

Context at the failing edit-tool call: median 376k (119k-646k). The single edit-tool failure inside a post-50
window came 30 calls after its compaction.

Per compaction (34):
| proxy, N | gross cost in window | excess, point | excess, 95% upper |
|---|---|---|---|
| edit tool, 10 | 0 | -7k (none) | 85k input (9.6k cw) |
| edit tool, 50 | 7.5k input (1.7k cw) | -24k (none) | 97k input (11.0k cw) |
| shell, 10 | 27k (3.8k cw) | +45k | 173k (18.6k cw) |
| shell, 50 | 39k (5.3k cw) | +24k | 194k (20.9k cw) |

For scale, D2's re-read excess (0.7 extra re-read calls and 6.6k tokens per compaction; A5 6.7k) is about
76k input processed for the extra calls (0.7 x 109k mean context of an issuing call), before carry.

## Caveats
- Rare events: 10 edit-tool failures in the whole dataset, 1 in a post-compaction window. The test can only
  exclude large effects (post-50 rate above about 3%, i.e. 3x the control).
- The Edit tool is a minority route for file changes here (1,328 vs about 3,600 shell edits); shell edits do
  not quote text, so their failures are mostly syntax/runtime errors, not stale quotes, and the shell proxy
  is over-inclusive. A `sed -i` or python replace whose pattern no longer matches usually exits 0 and is
  invisible as an error.
- An edit that quotes text that is still present but acts on stale understanding succeeds; neither proxy sees
  wrong edits, only refused ones. After a compaction the harness re-attaches recently read files, which can
  suppress both stale quotes and "not read yet" refusals by design.
- Windows overlap (most edits are within 50 calls of some instruction start; compaction windows lie inside
  instruction windows). Idle windows are few (63 boundaries, 13 edits in the first 10 calls).
- Cost charges the whole failing call even when it carried other tool uses (fractional variant within 3%);
  carry of the error text and retry reads in later context is not counted (small next to steps x context).
- One user, 7 compacting sessions; S03 holds 14 of 34 compactions (leaving it out changes nothing). Placebo
  draws ignore cycle structure; the shell p = 0.001 rests on two failures on the window edge and the session
  bootstrap interval includes zero.

## Findings
1. Edit refusals are too rare to be a sharp quality proxy here: 10 of 1,328 main edit-tool calls (0.75%; 3
   stale quotes, 7 harness refusals, 0 unclassified) and 0 of 166 in sub-agents.
2. No rise after compaction: 0/25 edit-tool failures in the first 10 calls and 1/179 (0.56%) in the first 50,
   against 1.05% mid-cycle, 0.97% after instruction starts and 0.88% after idle breaks (placebo p 1.0 / 0.66);
   the data exclude only a rise above about 3%.
3. Edits that rely on pre-compaction knowledge do not fail more: 1/64 (1.6%) vs 0.86% same-cycle (p 0.45),
   0/58 once shell reads count as touches; harness refusals follow shell-side reads and changes, not compaction.
4. Shell edits show 2/28 failures in the first 10 calls (7.1% vs 1.4%, placebo p 0.001), but both sit 9
   calls after the compaction, are ordinary errors rather than stale-pattern failures, and vanish at 50 calls
   (1.7%, p 0.20; bootstrap interval includes 0): not evidence of loss.
5. A failed edit costs about 2 extra steps, about 0.9-1.2M input (0.1M cost-weighted); all edit failures
   together are 0.86% of input. Per compaction the attributable charge is about 0 (point), at most about
   100-190k input (10-21k cost-weighted) at the 95% bound, the same order as D2's re-read excess (about 76k
   input-equivalent), so it does not change the restart arithmetic.
