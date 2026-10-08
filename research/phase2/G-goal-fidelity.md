> Result of the pre-registered protocol `research/protocol/goal-fidelity-v1.md`, written by an analysis agent and reviewed in `log.md` (cycle G). Numbers only.

# G: goal fidelity across compaction (protocol goal-fidelity-v1)

Aggregates only. No instruction text, summary text, terms, paths or commands were printed or stored; terms existed only in memory. Scripts: `run.py` (analysis), `explore*.py` (summary-carrier search); numbers in `results.json`.

## Method (as run)

- Data: `lines_v2.load()`, 10 sessions, main chain only. Instructions = `events._is_instruction` (683 in all; S01 19, S02 49, S03 299, S04 10, S05 56, S06 36, S07 4, S08 6, S09 129, S10 75).
- Compactions: main-chain `system` lines with subtype `compact_boundary` (same rule as D2/A5): 34 (S01 1, S02 3, S03 14, S05 3, S06 1, S09 7, S10 5). Matches A5/D2.
- Summary identification: walk forward from each boundary on the main chain, skipping attachments, system notices and assistant lines, and stop at the next real instruction or the next boundary. The summary message is the first line flagged `isCompactSummary`. Result: **found for 1 of 34** (S01, 18,337 characters, 1,070 distinct word types). For the other 33 there is no such line anywhere in the data; the whole dataset holds 1 `isCompactSummary` line. For the 33, the line right after the boundary is an assistant line (31) or a system notice (2). The cause is the source: S02-S10 were rebuilt from the remote events API, which does not return the summary. Only S01 comes from a local transcript. This matches D2 and A5, which also found the summary text for 1 of 34.
- Terms: Latin words of 4+ characters (`[A-Za-z][A-Za-z0-9_]{3,}`) or Hangul runs of 2+ syllables, lower-cased. Removed: a fixed stop list (179 English/Korean function words) and the 43 terms that appear in the instructions of more than 5 of the 10 sessions. That leaves 18.8 terms per instruction on average; 675 of 683 instructions keep at least one term.
- G1: for each compaction, take all main-session instructions from the session's start up to the boundary and split them into quintiles by instruction index (`floor(5i/n)`). A term survives if it is in the carrier's word set, built with the same tokenizer. Two weightings: term-weighted (surviving terms / terms) and instruction-weighted (mean per-instruction fraction). Both are pooled over compactions. Bootstrap over compactions: 2,000 reps, seed 20261008, percentile 95%.
- G2: the treated set is the first 3 instructions after each compaction (34 x 3 = 102, all distinct). Controls are instructions from other sessions with no compaction in the 50 previous main calls, the same session-position decile (main calls before / session calls), and a context within ±25%. Context is the ctx of the first main call after the instruction. Up to 3 controls are taken, nearest in ctx, with reuse allowed.
  - (a): `rules.detect_t3(...)["flags"][i]["outcome"] == "not_met"` for that instruction. The instruction count of `detect_t3` equals the `_is_instruction` count in all 10 sessions.
  - (b): at least 30% of the instruction's terms are in the Q1 instructions (first quintile of the instructions before it) and not in the previous 20 instructions.
  - Rate ratio = treated rate / control rate. Bootstrap over compactions; each compaction's controls are resampled with it.

## Checks

- 34 boundaries, and 34 x 3 treated instructions are available. No post-compaction list overlaps another compaction.
- Control pool: 640 instructions. Used: 131 distinct controls from 10 sessions, 213 control slots. Controls per treated instruction: 0 for 18, 1 for 14, 2 for 11, 3 for 59. Instructions with no control have small post-compaction contexts in late deciles. They count in the treated rate.
- Base rates over all 683 instructions: (a) 11.4%, (b) 4.4%.

## G1: survival by quintile

Protocol carrier (compaction summary), n = 1 compaction (S01; 14 instructions before it):

| | Q1 (oldest) | Q2 | Q3 | Q4 | Q5 (newest) |
|---|---|---|---|---|---|
| term-weighted | 0.577 (130 terms) | 0.468 (62) | 1.000 (19) | 1.000 (22) | 1.000 (53) |
| instruction-weighted | 0.700 (3 instr.) | 0.691 (3) | 1.000 (3) | 1.000 (3) | 1.000 (2) |

- First instruction: 100% of its terms survive (n = 1).
- Q1/Q5: term-weighted 0.577, instruction-weighted 0.700. The bootstrap 95% CI is degenerate (0.577-0.577 and 0.700-0.700), because there is only one compaction to resample.
- **Verdict G1: not testable as registered** (33/34 summaries missing). Even on the one available compaction, the criterion fails: Q1 is not below half of Q5 (0.58 > 0.5). Recency bias is therefore **not shown**.

Exploratory, outside the protocol: the carrier is the agent's own continuation output (assistant text + tool inputs, main chain) from the boundary to the next instruction, at most 50 calls. n = 34.

| | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| term-weighted | 0.052 | 0.035 | 0.044 | 0.059 | 0.083 |
| instruction-weighted | 0.064 | 0.045 | 0.048 | 0.064 | 0.076 |

- Q1/Q5: term-weighted 0.62 (CI 0.51-0.78), instruction-weighted 0.85 (CI 0.74-1.04).
- First instruction: 10% of its terms; at least one term in 79% of compactions.
- Q1 is never below half of Q5, so even this proxy would not meet the "supported" rule. The term-weighted ratio is below 1 throughout its CI.
- This proxy measures what the agent mentions, not what the summary keeps.

Information only (requested): G1 survival of Q1 terms by summary length.

- With the protocol carrier this cannot be computed (one summary).
- Substitute: the proxy carrier, split at the median "fresh" tokens of the first post-compaction call (summary + re-injected material; median 21.6k). Fresh at or below the median (n = 17): Q1 0.066 term-weighted (Q5 0.078), 0.057 instruction-weighted. Above the median (n = 17): Q1 0.048 (Q5 0.085), 0.066 instruction-weighted. The two halves give opposite signs under the two weightings, so there is no consistent length effect.

## G2: drift signals after compaction

| signal | after compaction (n = 102) | controls (n = 213 slots) | rate ratio | bootstrap 95% CI |
|---|---|---|---|---|
| (a) correction | 11.8% (12) | 13.1% (28) | 0.90 | 0.46-1.70 |
| (b) restatement | 2.9% (3) | 4.2% (9) | 0.70 | 0.00-2.50 (3 reps undefined) |
| (a or b) | 14.7% (15) | 17.4% (37) | 0.85 | 0.48-1.41 |

**Verdict G2: not shown.** The (a or b) ratio is 0.85, below the 1.5 threshold, and its CI includes 1. With n = 34 the test has little power, so this is not evidence of "no drift".

Sensitivity of (a or b): RR / CI.

| variant | RR | 95% CI |
|---|---|---|
| decile by instruction index | 0.84 | 0.41-1.60 |
| ctx tolerance ±50% (8 treated without controls) | 0.84 | 0.48-1.36 |
| (a) read as "this prompt is itself a correction" (previous instruction's flag) | 1.08 | 0.54-1.97 |
| (b) with Q1 taken before the compaction | 0.85 | identical |

No variant reaches 1.5.

## Deviations and interpretation choices

1. **Summary missing for 33/34 compactions** (a data limit; nothing carries it in the events-API sessions). G1 is run on n = 1 and its bootstrap is degenerate. *Could change the verdict:* yes. With all 34 summaries G1 could come out supported or not; as run, it can only be "not testable / not shown".
2. Quintiles are equal-count bins by instruction index, `floor(5i/n)` (n = 14 gives bins of 3, 3, 3, 3, 2). The pre-compaction instructions start at the session start, not at the previous compaction, and include interrupt markers, because `_is_instruction` counts them. *Could change the verdict:* not at n = 1; Q3-Q5 are all 1.0.
3. Tokenizer and matching are not specified in the protocol. Survival is exact word-type membership. Hangul runs keep attached particles, which makes matching stricter; substring matching would raise survival. *Could change the verdict:* unlikely for G1 at n = 1. Survival levels and the (b) rate would shift.
4. The stop list is not given in the protocol, so I used my own fixed list of 179 words. The ">50%" filter is read as "in the instructions of more than 5 of the 10 sessions" (removes 43). *Could change the verdict:* unlikely.
5. G2 operational choices:
   - context = ctx of the first call after the instruction;
   - decile = by calls;
   - controls = nearest in ctx, reused across treated, other sessions only;
   - treated instructions without controls kept in the treated rate.
   *Could change the verdict:* no, per the sensitivity table.
6. (a) is read literally as the `detect_t3` outcome flag of the post-compaction instruction, which is decided by the person's next prompt. The alternative reading gives RR 1.08 and does not change the verdict.
7. (b) Q1 = the first quintile of the instructions before the instruction (symmetric for controls). The alternative "before the compaction" gives the same result.
8. Bootstrap: percentile method; replicates with a control rate of 0 are dropped (3 of 2,000, (b) only).

## Findings

1. The compaction summary survives for 1 of 34 compactions (S01 only), so G1's recency test cannot be run as registered.
2. On that one summary, Q1 survival is 0.58 term-weighted (0.70 instruction-weighted), against 1.00 for Q5: ratio 0.58 / 0.70, above the 0.5 threshold. The first instruction survives in full.
3. A proxy on all 34 compactions (the agent's continuation output) shows mild recency: Q1/Q5 0.62 (CI 0.51-0.78) term-weighted and 0.85 (0.74-1.04) instruction-weighted. It still does not meet the "less than half" criterion.
4. Drift signals after compaction are not raised. (a or b) is 14.7% after compaction vs 17.4% in matched controls: RR 0.85 (CI 0.48-1.41). Correction alone has RR 0.90; restatement is rare (3 of 102). The result is the same under every sensitivity variant.
5. Neither measure is supported. Per the protocol, the claim that recency-ordered compaction trades goal fidelity for cost is "not shown", and role-ordered memory stays a hypothesis without this support.
