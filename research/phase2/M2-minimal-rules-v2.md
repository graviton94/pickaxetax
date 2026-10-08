> Result of the pre-registered replay (`research/protocol/minimal-rules-v2.md`), written by an analysis agent and reviewed in `log.md` (cycle M2). Numbers only; computed from the private transcripts.

# M2: minimal rule set v2 (R8 reflex arc, R9 mode switch) and the W8 behaviour check

Protocol: `research/protocol/minimal-rules-v2.md`, run as written. It extends v1 (cycle M1). No threshold was
changed after results were seen. This file holds aggregates only. The data are 10 main sessions, 16,181 calls,
667 instructions and 6,579,410,935 measured main-session input tokens.

Files in this folder:
- `stage1b.py` labels each tool call with a category only; no text is stored.
- `replay.py` is M1's engine, copied, with R8 and R9 added.
- `run.py` runs the replay; its log is `run.log` and its numbers are in `results.json`.
- `w8.py` runs the W8 check; its log is `w8.log` and its numbers are in `w8.json`.

M1's numeric trace (`M1/trace.pkl`) is read-only here. Nothing in M1/ or the repository was changed.

## Method

**Engine.** M1's segment replay, prices, charges, keep rule and validation are used unchanged. The new parts are:

- **Tool categories (`stage1b.py`).** Each main-session tool call gets one label, aligned call by call and tool by
  tool with M1's trace (asserted):
  - edit: Edit, Write, MultiEdit or NotebookEdit;
  - read: Read, Grep, Glob, LS or NotebookRead;
  - r8a: a Bash call whose command matches the R8a list. Leading `cd … &&` and `NAME=value` prefixes are
    stripped first, and the listed word must end there;
  - r8b: `git status|diff|log|show`, `ls` or `wc`;
  - shread: another read-only shell command (rule tier `READ_CMD`). It is used only in one R9 sensitivity run;
  - other.
- **R8.** An eligible call:
  - is a main call with no text;
  - has at least one tool call, and all of its tool calls are r8a;
  - comes after an earlier call in the same instruction that has an edit tool. Instructions are bound's
    `instruction_starts`, which gives 667.

  The call does not happen in the replay. Its input, its tool-input segments and its positive unattributed growth
  are removed. Its tool-result segments stay and are born at the next call, as observed.

  Sensitivities: the R8a + R8b list, no edit precondition, and both together.
- **R9.** A mechanical call is a main call with no text, at least one tool call, and every tool call labelled read,
  r8a or r8b.
  - Its thinking is 0.4 × its positive unattributed growth, meaning the unattributed segment born at the next call.
  - That segment is shrunk by 50% of the thinking (primary run) or 100% (upper bound) for its whole life, so the
    context carries less from that call on.
  - Money: the removed thinking is also credited at output price 5 in C5's money measure only.

  Sensitivity: shell reads (`READ_CMD`) also count as mechanical.
- **Selection.** Forward selection over R1–R9 starts from the empty set. It uses v1's keep rule (at least 2 points
  of input and at least 1 point of price) and v1's odd/even validation. R6 and R7 are eligible only after R3, R4 or
  R5. The bootstrap uses E4's method: 2,000 reps, seed 20261006, sessions drawn with replacement.
- **W8 check (`w8.py`).** The detector is the sealed `rules.detect` (rule-tier-v0). Tier-t2 `machine_labels` reads
  exactly its `flags`.
  - The W8 exploration list is re-derived with the same code. Each result also gets its target paths and its
    position in the session.
  - The per-instruction W8 and W8_explore scores are asserted equal to `detect`'s for every instruction of every
    session.
  - Paths are matched in memory only.

## 1. Reproduction checks

| check | target (M1) | here |
|---|---|---|
| no-rule replay, main input | 6,579,410,935 | **6,579,410,935** (asserted for every session) |
| no-rule model price | 0.7147B | 0.7147B |
| R3 alone (compact at 150k) | 72.85 / 64.65, 323 compactions | **72.85 / 64.65**, 323 |
| category alignment with M1 trace | | every call and tool count matches (asserted) |
| W8 scores re-derived vs sealed `detect` | | equal for all 683 instructions (asserted) |

## 2. What the new rules can touch (static counts)

| quantity | count |
|---|---:|
| main calls / with no text / with no text and no tool call | 16,181 / 11,514 / 1 |
| main calls with an edit tool | 1,249 |
| Bash tool calls matching R8a (pytest 8, npm family 15) | 23 |
| Bash calls with an R8a check word elsewhere in the command (wrapped, chained: diagnostic only) | 92 |
| Bash calls matching R8b | 324 |
| **R8 eligible calls: R8a, edit precondition (primary)** | **10** |
| R8a, no precondition / R8a+R8b with precondition / R8a+R8b, no precondition | 14 / 98 / 238 |
| R9 mechanical calls (primary definition) | 1,095 (1,037 with positive unattributed growth) |
| their positive unattributed growth / all positive unattributed growth | 1.61M / 10.58M tokens (15.2%) |
| mechanical calls incl. shell reads (sensitivity) | 4,838 (3.15M tokens of growth) |

## 3. R8 and R9: alone and on top of {R3}

Values are % saved. The money column is C5 money with the low / high output estimate. "Removed" counts calls
removed, per instruction in brackets. Marginal is in points on top of {R3}, where R3 alone gives 72.85 / 64.65 /
52.42 money (lo).

| rule (variant) | input alone | price alone | money alone (lo/hi) | removed (per instr.) | marginal on R3: input / price | money marginal (lo/hi) | passes keep rule |
|---|---:|---:|---:|---:|---|---:|---|
| **R8 primary** (R8a, edit precondition) | 0.044 | 0.041 | 0.039 / 0.038 | 10 (0.015) | **+0.022 / +0.021** | +0.02 / +0.02 | no |
| R8 sens: R8a+R8b | 0.614 | 0.577 | 0.51 / 0.49 | 98 (0.147) | +0.136 / +0.144 | +0.14 / +0.14 | no |
| R8 sens: no edit precondition | 0.068 | 0.064 | 0.06 / 0.06 | 14 (0.021) | +0.028 / +0.027 | +0.03 / +0.03 | no |
| R8 sens: R8a+R8b, no precondition | 1.656 | 1.620 | 1.41 / 1.37 | 238 (0.357) | +0.346 / +0.445 | +0.45 / +0.43 | no |
| **R9 primary** (cut 50%) | 0.860 | 0.877 | 0.94 / 0.91 (output part 0.18) | 0 | **−0.096 / +0.019** | +0.23 / +0.22 | no |
| R9 upper (cut 100%) | 1.720 | 1.754 | 1.88 / 1.83 (output 0.35) | 0 | −0.114 / +0.119 | +0.54 / +0.53 | no |
| R9 sens: + shell reads, 50% | 1.994 | 2.003 | 2.10 / 2.03 (output 0.34) | 0 | +0.006 / +0.218 | +0.61 / +0.59 | no |
| R9 sens: + shell reads, 100% | 3.989 | 4.006 | 4.19 / 4.06 (output 0.69) | 0 | −0.009 / +0.418 | +1.20 / +1.16 | no |
| R8 + R9 primary together | 0.903 | 0.917 | 0.98 / 0.95 | 10 | −0.079 / +0.036 | +0.25 / +0.24 | — |

Removed thinking: R9 primary 0.32M tokens, upper 0.64M, + shell reads 0.63M / 1.26M.

**Why R9's input marginal on {R3} is negative.** A smaller context reaches 150k later, so R3 compacts less often
(320 instead of 323 compactions; 311 in the widest variant).
- Calls between compactions then sit higher above the 64k post-compaction floor, which offsets the thinking
  removed. So input on {R3} falls slightly.
- Price still rises a little, because each compaction avoided saves its D2 re-read and its 22k rewrite.
- Per session, the R9 input marginal on R3 ranges from −1.78 (S08) to +0.98 (S04). The bootstrap's 90% range is
  −0.20 to −0.03.

**Per session, R8 on R3.** Only three sessions have any eligible call: S04 +1.98, S06 +0.46, S01 +0.08 points of
input; the other seven have 0. The bootstrap's 90% range is +0.002 to +0.074.

## 4. Forward selection (R1–R9, from the empty set)

`*` marks a rule that passes the keep rule. Values are marginal input / price, in points.

- **All ten.**
  - From the empty set: R3 +72.85/+64.65\*; R4 +52.05/+46.40\*; R5 +15.70/+13.83\*; R1 +0.92/+0.88;
    **R9 +0.86/+0.88**; R2 +0.26/+0.24; **R8 +0.04/+0.04**. R3 is added.
  - From {R3}: R2 +0.037/+0.038; R1 +0.008/+0.032; **R8 +0.022/+0.021**; **R9 −0.096/+0.019**; R4 0/0;
    R5 −0.15/−0.58; R6 −2.79/−5.48; R7 −22,383/−21,868. **Stop: {R3}.**
- **Odd half.** From {R3}: R9 −0.034/+0.068; R8 +0.003/+0.003. Stop: {R3}.
- **Even half.** From {R3}: R8 +0.071/+0.067; R9 −0.250/−0.099. Stop: {R3}.
- **Validation.** Both halves choose {R3}, the same set as all ten. The held-out loss is 0, so the result stands.
- **Under each sensitivity, all ten sessions:** {R3} in every case. The cases are R8a+R8b; no precondition; both;
  R9 at 100%; R9 with shell reads at 100%; and all the widest variants at once.

**Chosen set: {R3}, unchanged from v1.**
- Input 72.85%, price 64.65%, money 52.42 / 50.80%. That is 175.5% of the 41.5% oracle reference.
- Extra steps: 549, which is 0.82 per instruction and 3.39% of calls.
- Marginal on the final set: R8 +0.022/+0.021; R9 −0.096/+0.019.

**Session bootstrap of {R3}** (E4: 2,000 reps, seed 20261006):
- input 90% interval 71.70–73.45 (median 72.86);
- price 63.17–65.55;
- 100% of reps reach at least half of the oracle.

## 5. W8 behaviour check (mechanical-validation-v1)

**Detector rate (sealed rule tier v0).**
- 2 of 683 instructions are flagged W8 (0.3%), which is also 2 of 667 instructions with main calls (0.3%), in two
  sessions.
- Exploration results total 4.22M estimated tokens, of which 1.0% (40.5k) are unused.
- The unused results inside flagged instructions are 3.0k tokens, or 0.07% of exploration tokens.

**Behaviour.** The table gives the share of results whose file is edited later in the same or next instruction,
or whose path appears in that instruction's final main-session text.

| population | results (tokens) | with a file target | exact path: edit / answer / either | + dir prefix | + basename in answer |
|---|---|---:|---|---:|---:|
| **flagged** (unused, in W8-flagged instructions) | **3** (3.0k) | 2 | **0 / 0 / 0 of 3 (0%; Wilson 95% 0–56%)** | 0 | 0 |
| unused, unflagged instruction | 806 (37.5k) | 423 | 7 / 0 / 7 (0.9%) | 30 (3.7%) | 39 (4.8%) |
| all unused (flagged + unflagged) | 809 | 425 | 7 / 0 / 7 (0.9%; 0.4–1.8%) | 30 (3.7%) | 39 (4.8%; 3.5–6.5%) |
| used (reference) | 6,164 (4.18M) | 2,075 | 203 / 2 / 205 (3.3%; 2.9–3.8%) | 262 (4.3%) | 315 (5.1%; 4.6–5.7%) |

- **Upper bound on the false-flag rate of the flagged results: 0 of 3.** The sample is far too small to bound
  anything; the Wilson interval is 0–56%.
- On the wider set of all results judged unused, the bound is 0.9% (exact path) to 4.8% (basename).
- **The test discriminates weakly.** Results the detector calls *used* meet the same behavioural criterion only
  3.3–5.1% of the time, barely more than unused ones. Most exploration is shell reads with no single file target
  (66% of used results have none), and final answers rarely carry full or cwd-relative paths.

## 6. Verdicts against the stated expectations

| expectation (pre-registered) | result | verdict |
|---|---|---|
| R8 alone 1–5% of input | 0.044% (most generous variant 1.66%) | **falsified (below the range)**: few check commands exist (23 R8a calls, 10 eligible) |
| R8 on {R3} < 2 points, fails keep rule | +0.022 / +0.021 (max variant +0.35 / +0.45) | holds |
| R9 alone < 2% of input | 0.86% (upper 1.72%; with shell reads at 100%, 3.99%) | holds (primary and upper); exceeded only in the extra sensitivity |
| R9 on {R3} < 1 point | −0.096 / +0.019 (max +0.42 price) | holds |
| chosen set stays {R3} | {R3} on all ten, both halves, all sensitivities | holds |

## 7. Deviations and interpretation choices (most literal reading taken)

1. **R8a matching is a strict prefix match.** The command must start with a listed check after `cd X &&` and
   `NAME=value` prefixes are stripped.
   - Not counted: wrappers such as `timeout`, `uv run`, a venv path or `source … &&`; checks after `;`; and checks
     later in a chain. There are 92 such commands.
   - A `:` suffix such as `npm run test:x` is counted as a match.
   - *Could not change the selection.* Even R8a+R8b with no precondition (238 calls) adds only +0.35 on {R3}, and
     the 92 extra commands are fewer than that.
2. **"Follows a call that holds an edit tool" means any earlier main call in the same instruction,** not only the
   one just before. *Could not change the selection.* Dropping the precondition entirely adds +0.006.
3. **An R8 or R9 call needs at least one tool call.** A no-text call with no tool call would satisfy "all its tool
   calls are …" vacuously. Only 1 such call exists, so this is immaterial.
4. **R8 removal follows M1's R1/R2 convention.** Positive unattributed growth is removed, and a negative one
   (context the harness removed) is kept. The tool results are kept at their observed birth. R8-removed calls get no
   output credit in money, because the protocol credits output for R9 only. *Selection is unaffected*, since money
   is not a selection measure.
5. **R9's thinking is taken from the call's own unattributed segment** (born at the next call). It is skipped when
   the next call is an observed compaction call, whose growth is the post-compaction rebuild. The cut applies to
   the segment for its whole life. Mechanical calls follow the protocol's explicit tool list, so shell reads (cat,
   grep, sed -n, find…) are not mechanical. That reading leaves out 3,743 calls. The shell-read sensitivity covers
   them and *does not change the selection* (best case +0.42 price, −0.01 input on {R3}).
6. **W8 "flagged exploration results" means results judged unused (fewer than 2 distinctive words reused) inside a
   W8-flagged instruction.** All unused results are also reported.
   - "Edited later" means an Edit/Write/MultiEdit/NotebookEdit call in any context (main or sub-agent) that comes
     after the result, in the same or next instruction, on the same normalized absolute path.
   - "Final answer" means the instruction's last non-empty main-session text, counted with `detect`'s instruction
     numbering (683 instructions, versus bound's 667).
   - A path "appears" when its absolute or cwd-relative form is a substring. The directory-prefix and basename
     variants are sensitivities.
   - File targets come from Read and NotebookRead, from Grep with a file-like path, and from file arguments of
     cat/head/tail/sed/wc/grep/rg/jq.
   - The detector was called directly. `machine_labels(tier="t2")` needs a packet and only re-indexes the same
     `detect` flags.

## Findings

1. **The chosen set stays {R3}, and v2's main expectation holds.** Forward selection over R1–R9 stops after R3 on
   all ten sessions, on both halves and under every sensitivity. Input saved is 72.85% (bootstrap 90%:
   71.70–73.45), price 64.65%.
2. **R8 is almost empty in this data.** Only 23 Bash calls start with an R8a check and 10 calls are eligible
   (0.015 per instruction). Alone it saves 0.04% of input, which falsifies the pre-registered 1–5% on the low side.
   On {R3} it adds +0.02 points.
3. **R9 saves 0.86% alone** (upper 1.72%; 3.99% with shell reads at 100%). On {R3} its input marginal is negative
   (−0.10), because a smaller context delays R3's compactions. Its money marginal is +0.23 points (up to +1.2), half
   of it from output not written.
4. **The W8 detector almost never fires.** It flags 2 of 683 instructions (0.3%) and 0.07% of exploration tokens.
   None of the 3 flagged results has its file edited later or named in the final answer (0/3, Wilson 0–56%).
5. **The W8 behaviour test barely separates used from unused results.** It hits 0.9–4.8% of all unused results and
   3.3–5.1% of used ones. As an upper bound on the false-flag rate it is valid but weak.
