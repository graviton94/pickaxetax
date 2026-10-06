> Working memo from cycle B7 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# B7: reading content that is already in the context (a broad W1)

**Exploratory, not pre-registered.** Aggregates only. Lines were hashed in memory (8-byte blake2b), and paths and
command signatures were hashed as SHA-1 prefixes. No text, path or command was printed or stored. The pickles hold
numbers and category labels only. Data: 10 sessions at the dataset-v2 snapshots, 18,706 tool results (16,079 main),
76 sub-agent runs, 34 compactions, and 6.84 B input tokens processed (price 836 M units).

Method notes:
- Per-result records; the replication of the judge's W1 rule matches exactly: 266 cases / 3,414 tokens, and every session agrees. Scripts are kept with the analysis files.

## Method
- **Residency.** Each context has its own resident set: the main session, and each sub-agent run. The set holds every
  tool result, tool input (Write/Edit strings included), assistant text, prompt, harness text and compact summary born
  since the last compaction or since the stream started. Thinking is excluded. The main set is reset at each
  `compact_boundary`.
- **Normalisation.**
  - Harness `<system-reminder>` blocks and Read line-number prefixes are removed.
  - Whitespace is collapsed.
  - Only *non-trivial lines* (≥ 12 characters) are kept.
- **Containment (primary): 3-line shingles.**
  - A line counts as contained if a resident sequence of 3 consecutive non-trivial lines covers it.
  - Results with only 1–2 (long) lines use whole-line matches. These are mostly MCP JSON.
  - Line-level containment is reported as a looser sensitivity check. It is inflated by repeated boilerplate lines,
    such as the Agent launch notice and the Artifact publish notice.
- **Classes.** full ≥ 95%, mostly 50–95%, low < 50%. Results under 200 calibrated tokens are reported separately.
  Tokens are `estimate_tokens` × the session's `bound.calibrate` factor (1.0–2.05). Duplicate tokens = result tokens ×
  the character share of the contained lines.
- **Images** are compared by a hash of their data. Their tokens are estimated from the PNG/JPEG header
  (long edge 1568, w·h/750, capped at 1600).
- **Scope.** *Reading* tools: Read, Bash, Grep/Glob/LS, MCP, WebFetch/WebSearch, ReadNotifications, ToolSearch.
  *Action* tools are reported apart: Edit/Write confirmations, Agent, Artifact and similar. Error results are left to W2.
- **Cost.**
  - *Tokens added*: the duplicate tokens, priced at the main cache-write rate (2.0) as the judge prices them.
  - *Carried* (descriptive, W5's territory): the duplicate tokens × the later main calls before the next compaction,
    priced at the read rate (0.1).
  - *Steps*: API calls that wrote no text and whose every tool result only re-obtained resident content. Each costs its
    whole context, as in the judge's steps-only measure.

## 1. How much of what is read is already resident? (≥ 200 tokens, non-error)
| context | class | results | tokens | duplicate tokens |
|---|---|---:|---:|---:|
| main reading | full ≥ 95% | 104 | 78,508 | 77,614 |
| | mostly 50–95% | 509 | 318,812 | 207,242 |
| | low < 50% | 5,738 | 5,847,408 | 160,183 |
| | short < 200 (full / mostly / low / unmeasurable) | 7,263 (1,178 / 651 / 3,864 / 1,570) | 488,716 | 71,093 |
| sub-agent reading, own context | full / mostly / low | 5 / 19 / 1,674 | 3,908 / 17,078 / 4,312,483 | 3,738 / 12,937 / 67,024 |
| main action tools (not reads) | full / mostly | 2 / 111 | 7,201 / 73,948 | 6,355 / 57,301 |

- **Main share.** In the main session, **9.7% of reading results ≥ 200 tokens (613 of 6,354) were at least half
  resident**. They hold 4.6% of reading tokens.
- **Line-level comparison.** Line-level containment would say 159 full and 797 mostly results, instead of 104 and 509.
- **Images.** There were 1,081 image results (≈ 1.25 M tokens, outside the calibrated text). Only **5** were identical
  to a resident image (5.9k tokens).

By route (main, ≥ 200 tokens):

| route | results | ≥ 50% resident | share of tokens resident |
|---|---:|---:|---:|
| Read tool | 147 | 40 (27%) | 11% |
| shell file reads (cat/sed/head/grep of a file) | 3,423 | 160 (4.7%) | 3.3% |
| shell runs (tests, scripts) | 967 | 229 (24%) | 10% |
| shell writes that print | 1,397 | 169 (12%) | 6.2% |
| MCP | 217 | 8 | 1.1% |

## 2. Categories of duplicate reading (≥ 50% resident; W1 at any size)
| | category | results (full + mostly) | tokens | duplicate tokens | short (< 200) also flagged |
|---|---|---:|---:|---:|---:|
| main | (a) W1 exact (judge rule) | 256 (245 short) | 6,716 | 6,716 | — |
| | (b) Read, full re-read, previous read resident, not written since | 0 + 2 | 2,463 | 1,440 | 2 |
| | (b2) Read after own Edit/Write (read-back) | 19 + 9 | 32,617 | 30,762 | 2 |
| | (c) Read, partial re-read (offset/limit) of resident content | 3 + 2 | 12,063 | 11,512 | 1 |
| | (c′) Read, first read of the path in residency, content resident from another route | 2 + 3 | 4,970 | 3,991 | 5 |
| | (d1) shell file read of resident content | 37 + 123 | 161,751 | 125,318 | 210 |
| | (d2) same command re-run, output resident (unchanged status, tests) | 1 + 20 | 9,600 | 5,957 | 3 |
| | (d3) other command/tool whose output is resident | 31 + 350 | 169,497 | 101,516 | 1,578 |
| sub | W1 / (c) / (d1) / (d3) | 10 / 1 / 14 / 9 | 26 / 5,537 / 9,697 / 5,751 | 26 / 5,026 / 7,883 / 3,766 | 46 |

**Path view of (b) and (c).** These are Read calls of a text file whose previous Read is still resident. Image results
are excluded.

| | re-reads | median calls since the previous read | containment of the result |
|---|---:|---:|---|
| main, full re-read, unchanged | 15 | 3 | 2 mostly, 7 low, 6 short |
| main, partial re-read, unchanged | 24 | 4 | 3 full, 2 mostly, 16 low |
| main, partial re-read, written since | 30 | 25 | 11 full, 4 mostly, 14 low |
| sub-agents, partial re-read, unchanged | 35 | 1 | 34 low (paging through a file) |

- **Content shows changes the path rule misses.** A "same path, unchanged" re-read whose content is mostly new means the
  file changed by a route the path rule cannot see, such as a shell write or a regenerated file, or the read took a
  different slice.
- **The 212 unchanged full re-reads of image paths returned new screenshots.** See §3.

## 3. W1 reproduced, and a false-positive class in it
- **Reproduced exactly.** The judge rule (same context, same signature, same result hash, same epoch) gives 266 cases /
  3,414 estimated tokens, the same as `floor-t1.md`. Calibrated, that is 6,742 tokens.
- **Most cases are image re-reads with different data.** **221 of the 266 are Read calls of an image path. Only 5 of
  them returned the same image data, and only 4 of 174 PNGs had the same pixels.** The judge hashes only the text
  blocks of a result, so every image result hashes as empty: a screenshot re-taken at the same path looks like an
  identical result.
  - Corrected W1 (image data must match): **50 cases**. Tokens are unchanged, because images count 0 tokens.
  - The judge's W1 step cost ("steps spent only on duplicates") falls from **223 steps / 1.36% of input (1.20% of price)
    to 36 steps / 0.22% (0.20%)**. The 187 removed steps are all image re-reads.
  - The other 45 W1 cases are tiny or empty: 19 Bash, 25 other/MCP, 1 text Read. Only 11 W1 results are ≥ 200 tokens.
    The W1 token floor is therefore tiny partly because re-reads of unchanged *text* with identical arguments
    hardly occur.
- **Why the broad measure is larger than W1.**
  - It does not need the same signature. Shell reads with a different command, and different tools reaching the same
    lines, make up 80% of the broad duplicate tokens.
  - It does not need an identical result: "mostly" duplicates are 73% of the ≥ 200-token duplicate tokens.
  - It counts content the agent wrote itself, through Edit/Write strings.

## 4. Cost
Shares of all input processed (6.84 B) and of the input-side price (836 M units).

| measure | tokens or steps | % of input | % of input price |
|---|---:|---:|---:|
| W1 (judge), tokens | 3,414 (est) | 0.00005% | 0.0008% |
| broad duplicate tokens added (full + mostly, all sizes, images included) | 379,100 | **0.0055%** | **0.091%** |
| … of which full ≥ 95%, ≥ 200 tokens | 81,352 | 0.0012% | 0.019% |
| carried by later main calls until compaction (descriptive) | 71.97 M | 1.05% | 0.86% |
| **steps: all results ≥ 200 tokens and ≥ 95% resident (or corrected W1)** | **105 steps** | **0.59%** | **0.52%** |
| steps: the same with ≥ 50% | 472 steps | 2.85% | 2.65% |
| steps: also multi-line short results, ≥ 95% | 176 steps | 1.10% | 0.95% |
| steps: any measurable result ≥ 95% (upper bound) | 964 steps | 6.20% | 5.55% |
| W1 steps, judge / corrected | 223 / 36 | 1.36 / 0.22% | 1.20 / 0.20% |

- **The upper bound is not reading.** It is dominated by short Bash outputs of write/run commands that repeat an
  earlier line: 444 shell-write and 285 shell-run results. That is mostly confirmation output, not reading.
- **Composition of the primary 105 steps.** Bash 68 (shell file reads 41, runs 16, printing writes 11), Read 23, MCP 13
  (identical polls, W1). Main session 99, sub-agents 6.

Per session (duplicate tokens: full + mostly, reading):

| session | input | duplicate tokens | % of input | % of reading tokens | steps ≥ 95% (% input) | steps ≥ 50% (% input) | W1 judge → corrected |
|---|---:|---:|---:|---:|---:|---:|---:|
| S01 | 0.17 B | 13,671 | 0.008% | 4.8% | 5 (1.93%) | 11 (3.08%) | 13 → 9 |
| S02 | 0.61 B | 37,744 | 0.006% | 1.8% | 3 (0.26%) | 16 (1.19%) | 12 → 4 |
| S03 | 2.10 B | 114,599 | 0.005% | 2.9% | 17 (0.26%) | 143 (3.04%) | 77 → 17 |
| S04 | 0.03 B | 3,958 | 0.013% | 22.8% | 0 | 0 | 0 → 0 |
| S05 | 0.78 B | 61,851 | 0.008% | 7.2% | 19 (1.13%) | 73 (4.18%) | 45 → 2 |
| S06 | 0.17 B | 4,302 | 0.003% | 5.4% | 3 (0.47%) | 5 (1.14%) | 12 → 0 |
| S07 | 0.01 B | 5,193 | 0.060% | 9.8% | 2 (3.33%) | 2 (3.33%) | 0 → 0 |
| S08 | 0.02 B | 28 | 0.000% | 0.1% | 0 | 0 | 0 → 0 |
| S09 | 1.83 B | 81,815 | 0.005% | 2.9% | 32 (0.60%) | 138 (2.72%) | 58 → 12 |
| S10 | 1.12 B | 50,049 | 0.004% | 6.2% | 24 (0.84%) | 84 (3.05%) | 49 → 6 |

## 5. Habit or need? Distance to the resident copy
This covers main reading results ≥ 200 tokens that were ≥ 50% resident (n = 613). The "latest copy" is the most recent
resident item that holds most of the matched shingles.

| calls since the latest resident copy | 0 | 1 | 2–5 | 6–20 | 21–50 | 51–200 | > 200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| results | 16 | 55 | 105 | 163 | 104 | 120 | 50 |
| share | 2.6% | 9.0% | 17.1% | 26.6% | 17.0% | 19.6% | 8.2% |

- **Distance.** The median is 16 calls (mean 53). For the *first* resident copy the median is 67.
  - For full duplicates only: median 21 calls.
  - Same command re-run (d2): 9 calls. Shell file reads (d1): 41. Read-back after own write (b2): 38.
  - Path-based unchanged Read re-reads: median 3 (mostly images).
- **58% happen within the same instruction** (63% of full duplicates).
- **Where the resident copy came from.** An earlier tool result for 84%, a tool input (command or Write/Edit text) for
  8%, and a write for 7%.
- **Reading.** The re-obtaining is spread across the window, not concentrated right after the copy arrived.
  - Under a third (29%) happens within 5 calls. That part is a plain repeat, with the copy still near the end of the
    context.
  - 28% happens more than 50 calls later, where the copy sits deep in the context. That part may be an attention
    refresh, or a habit of checking state by reading again.
  - This matches A7's mid-cycle control: re-reading happens just as much while the content is still resident. The data
    cannot say whether a far-back copy was still usable to the model.

## 6. Sub-agents: content already resident in the parent at delegation (e)
The parent snapshot is the main context since its last compaction, up to the sub-agent run's first timestamp. A
sub-agent cannot see it, so this is a hand-off measure, not duplication inside one context.

The population is 1,698 sub-agent reading results ≥ 200 tokens (4.33 M tokens).

| containment against | full ≥ 95% (results / tokens) | mostly 50–95% | line-weighted resident tokens |
|---|---|---|---:|
| own context | 5 / 3,908 | 19 / 17,078 | 97k (2.2%) |
| parent's context at delegation | 40 / 115,926 (2.7%) | 168 / 601,428 (13.9%) | **836k (19.3%)** |
| either | 46 / 125,371 | 183 / 609,076 | 896k (20.7%) |

- **Read results.** Of the 162 Read results ≥ 200 tokens, 9 were fully resident in the parent and 25 (15%) were at least
  half resident.
- **Why this is far below B5.** B5 found that 70–76% of the files a sub-agent read had already been read by its parent.
  B5 counted by path, over the whole session history (including before compactions and other sub-agents). Here the
  parent's *resident* content is matched by content, and most sub-agent tokens are Bash output. The parent knew the
  file; it seldom held the same text at the moment of delegation.

## Caveats
- **Verbatim measure.** Paraphrased or reformatted content does not count (for example `grep -n` output against a
  plain read), so the measure is a floor. Lines under 12 characters are ignored: a result made only of short lines is
  "unmeasurable" (1,570 main short results, mostly images).
- **Residency is modelled, not observed.** Tool results that the harness cleared without a compaction (bound's negative
  rests) are treated as resident, which overstates residency. The compact summary counts as resident after a
  compaction.
- **"Not written since" sees only Edit/Write.** Shell writes and regenerated files are invisible to the path rule. The
  content test catches them.
- **Duplicate output is not the same as useless output.** A re-run with unchanged output (d2, and part of d3) can be
  verification: the fact that it is unchanged is new information. Read-back after an edit (b2) checks the edit. Both
  are counted here but labelled.
- **Shingle choice.** Shingles are stricter than lines. Line-level containment gives about 1.5× more flagged results.
  Boilerplate in action tools, such as Artifact publish notices (113 results, 81k tokens ≥ 50% resident), is excluded
  as "not reading".
- **Sub-agent timing.** The parent snapshot uses timestamps, so ordering errors of a few seconds are possible.

## Findings
1. **Verbatim re-reading of resident content is small in tokens.**
   - 379k calibrated tokens, which is 0.0055% of input and 0.09% of input price. That is about 56× the calibrated W1,
     and still negligible.
   - Carried until compaction it is 1.05% of input (0.86% of price).
2. **Its cost is the steps.** 105 calls that only re-obtained resident content (≥ 95%, ≥ 200 tokens) re-read 0.59% of
   input (0.52% of price). At ≥ 50% it is 472 calls, 2.85% (2.65%).
3. **The judge's W1 has a false-positive class.** 216 of its 266 cases are re-reads of a screenshot path whose image had
   changed (the judge hashes text only). Corrected W1 is 50 cases, and its step cost falls from 1.36% to 0.22% of input.
   The token floor is unchanged.
4. **A path re-read is rarely a content duplicate.**
   - Only 9.7% of main reading results (4.6% of tokens) were at least half resident.
   - Same-path unchanged Read re-reads with the previous read still resident: 15 full and 24 partial in the whole
     dataset.
   - Sub-agents found 2.7% of their reading tokens fully (19% line-weighted) in the parent's context, against B5's
     70–76% by path.
5. **Duplicates are not immediate.** The median is 16 calls since the latest resident copy. 29% happen within 5 calls,
   28% after more than 50, and 58% within the same instruction. That is consistent with A7's habit reading, and cannot
   separate a refresh from waste.

## Proposed rule: W1b "resident duplicate" (thresholds fixed now; not applied to any repository file)
- **Unit.** A tool result of a *reading* tool, meaning Read, a shell command, Grep/Glob/LS, MCP, or Web fetch/search.
  It must not be an error (W2 takes errors first) and must not already be W1.
- **Context.** The same context (the main session, or one sub-agent run), since its last compaction.
- **Text.**
  1. Drop `<system-reminder>` blocks and Read line-number prefixes.
  2. Collapse whitespace.
  3. Keep lines ≥ 12 characters.
- **Test.** At least 95% of the result's kept lines are covered by a 3-line shingle that is already resident in the
  context. A result with fewer than 3 kept lines needs whole-line matches. The result must be ≥ 200 tokens (calibrated).
- **Images.** An image result is a duplicate only if its data hash is resident. **The same fix applies to W1**: hash
  image data, not just text.
- **Counted.**
  - Result tokens × the contained character share, at the write price.
  - Step cost, descriptive: a no-text API call whose every result is W1 or W1b.
- **Labels, not discounts.**
  - `read-back` (b2): the resident copy is the agent's own Edit/Write.
  - `re-run` (d2): the same command signature, which may be verification. It is reported separately, and only the read
    routes go into the floor.
- **Expected size on this dataset.** 109 results across all reading tools (1 of them a d2 re-run), 81k tokens, 0.0012% of input. Step cost 105 calls, 0.59% of input.
  The rule moves the token floor only negligibly. Its value is in the step cost and in the W1 image fix.
