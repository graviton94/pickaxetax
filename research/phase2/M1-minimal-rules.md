> Result of the pre-registered replay (`research/protocol/minimal-rules-v1.md`), written by an analysis agent and reviewed in `log.md` (cycle M1). Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# M1: minimal rule set v1, the pre-registered replay

Protocol: `research/protocol/minimal-rules-v1.md`, run as written. No threshold was changed after results were seen.
This file holds aggregates only. Ten main sessions, 16,181 calls, 667 instructions, 6,579,410,935 measured
main-session input tokens. Scripts, the run log and the full numbers are kept with the analysis files.

## Method

**Engine.** This is the B3/A4 segment replay.
- Pipeline: `bound.read_trace_lines` → `calibrate` → `link(min_shared=1)` with refs over the whole session (B3).
- Context of call k = base (the call-0 context) + live segments + rule-made segments (summaries and cold-start
  blocks).
- Observed compactions:
  - One applies only if the replay reached 90% of the observed pre-compaction context.
  - Otherwise it is skipped, and the replay compacts by itself at 790k.
  - With no rule, the replay reproduces measured input exactly. This is asserted.
- Prices follow the B3/B4 model:
  - 0.1 per token kept from the previous call and 2.0 per new token;
  - R3's D2 charge at 0.25 per token;
  - extra calls (cold-start calls and fetches) at 0.1 × their context.
- Total money follows C5:
  - Per session, the model's price-saving fraction is applied to that session's actual main input-side money.
  - Summary output is charged at 5: 22k per R3 compaction and 10k per restart.
  - The result is divided by total money with the low and the high output estimate (916.5M and 945.9M units).
- An expiry-aware price is shown for information (A6: a call after an idle gap over 1 h pays 2.0 for kept tokens).
  Selection does not use it.

**Rules as implemented.** Where a choice had to be made, it is listed under deviations.

- **R1: no duplicate reading.** This is B7's W1b rule:
  - a reading tool, not an error, at least 200 calibrated tokens;
  - lines of 12+ characters;
  - at least 95% of lines covered by resident 3-line shingles (whole lines when the result has fewer than 3).

  The candidates are fixed on the observed context, which reproduces B7's 104 results. In the replay, each
  candidate is re-tested against the replay's own live segments: the segments that cover each line are stored
  as indices, and lines were hashed in memory only.
- **R2: no identical repeats.**
  - The judge's W1 with the image-aware result hash: same signature, identical result, same compaction epoch,
    in the main context. There are 49 cases in the main sessions.
  - Plus identical failing retries: same signature as an earlier failing call, and failing again. Outside W1
    there are 0 of these; the one identical failing retry with the same error text is inside W1.
  - In the replay, the earlier copy must still be live.
- **Removed calls (R1, R2).**
  - An API call disappears, input included, when it wrote no text and every one of its tool calls is flagged.
    Its outputs disappear with it, including its positive unattributed growth.
  - Otherwise only the flagged tool call's input and result segments are removed.
  - Assumption: the work succeeds without them.
- **R3: compaction at C.**
  - It fires when the context would pass C (primary 150k).
  - The compaction call reads the full context (as in B3/B4) and is charged D2's 82.7k at 0.25.
  - Afterwards the context is 64k, of which 22k is new and written at 2.0.
- **R4: restart at an instruction boundary when the previous replayed context is above 200k.** It drops
  everything older (B3 P1) and adds:
  - a 10k summary;
  - B5's cold start: 22.5k tokens written fresh, plus 0.5 extra calls on base + summary + T/2;
  - re-obtained content at A5's observed rate, r = 0.026 × R_b. R_b is the dropped tokens with a lexical ref
    inside the next instruction (A4's definition, applied to the replay's live set).
- **R5: the same restart and charges at every instruction boundary after an idle gap over 1 h**, whatever the
  size. There are 63 such boundaries.
- **R6: usage-weighted keep, acting at R3/R4/R5 consolidations.** It keeps the dropped segments with the
  highest A = ln Σ (t − t_j)^−0.5, up to 20k tokens:
  - uses are the birth and the lexical refs before the consolidation call;
  - the lag is floored at 1;
  - the kept segments are rewritten at 2.0.
- **R7: fetch on need, acting on segments dropped by R3/R4/R5.** At its next lexical ref (min_shared 1), a dropped
  segment costs one extra call at the current context, and its tokens are written fresh and carried. With R7,
  the A5 re-obtain charge of R4/R5 is replaced by the fetches.
- **Selection (fixed).** Forward selection over the pooled sessions of each sample. At each step the eligible
  rule with the largest marginal price saving is added, among those that add at least 2 points of input and
  at least 1 point of price. R6 and R7 are eligible only once R3, R4 or R5 is in the set. The run is repeated on
  S01/03/05/07/09 and on S02/04/06/08/10, and each half's set is evaluated on the other half.

## 1. Reproduction checks

| check | target | here |
|---|---|---|
| no-rule replay, main input | 6,579,410,935 | **6,579,410,935** (asserted; every session exact; 34 observed compactions applied) |
| no-rule model price (B3) | 0.715B | 0.7147B (expiry-aware 0.7777B) |
| B3 P1 (restart > 200k, 10k summary, no charge, B3 self-compaction base + 22k) | 54.8% / 50.1%, 146 restarts | 54.77% / 50.06%, 146 |
| B3 P3 (compaction at 390k, read charged) | 43.3% / 39.4%, 85 | 43.31% / 39.40%, 85 |
| B7 W1b, main reading results ≥ 95% resident, ≥ 200 tokens | 104 | 104 (R1 candidates; 0 have images) |
| B7 steps: no-text calls whose every result is W1 (corrected) or W1b | 99 main | 99 (35 W1-only, as B7) |
| judge W1, image-aware (corrected) | 50 incl. sub-agents | 49 main |
| A6 combined charge, restart > 200k (series replay, imported read-only) | 52.7% / 47.6% | **52.70% / 47.62%**, 168 restarts |
| same charge in this segment replay (cross-check for R4) | | 52.37% / 46.74%, 168 restarts |
| R4 as pre-registered (A5 rate instead of A6's per-boundary tokens) | | 52.05% / 46.40%, 168 restarts |

Segment vs. series replay accounts for the 0.3-point input gap; B3 P1 shows the same gap (54.8 vs 55.2). The A6
price model also adds a read of base + summary + T on every restart, which this engine does not.

## 2. Single rules (all ten sessions)

| rule | input saved % | price saved % | expiry-aware % | money % (lo / hi out) | extra steps (per instr.) | events |
|---|---:|---:|---:|---:|---:|---|
| R1 no duplicate reading | 0.92 | 0.88 | 0.84 | 0.77 / 0.75 | 0 (−72 calls removed) | 100 tool calls removed, 72 calls |
| R2 no identical repeats | 0.26 | 0.24 | 0.23 | 0.21 / 0.20 | 0 (−31 calls) | 42 tool calls, 31 calls |
| **R3 compact at 150k** | **72.85** | **64.65** | 65.89 | **52.42 / 50.80** | 549 (0.82) | 323 compactions |
| R4 restart > 200k | 52.05 | 46.40 | 48.85 | 39.43 / 38.21 | 84 (0.13) | 168 restarts |
| R5 restart after idle > 1 h | 15.70 | 13.83 | 19.76 | 11.67 / 11.31 | 32 (0.05) | 63 restarts |
| R6 alone / R7 alone | 0 | 0 | 0 | 0 | 0 | they need R3, R4 or R5 to act |

R6 and R7 on top of each base rule (marginal input / price, in points):

| | on R3 | on R4 | on R5 |
|---|---|---|---|
| R6 keep top activation ≤ 20k | −2.79 / −5.48 (416 compactions instead of 323) | −2.54 / −3.57 | −2.60 / −2.73 |
| R7 fetch on need | −22,383 / −21,868 (2.41M fetches; replay input 224× measured) | −797 / −778 (150k fetches) | −130 / −123 (21k fetches) |

- **R1 and R2.** Each removes under 1 point. In the large sessions they save 0.2–1.8% of input, and 2.5% (R1) in
  S01 and 5.0% (R1) in S07.
- **R5.** Its saving sits mostly in S02, S03, S05 and S09 (14–25%). Its money case is the expiry-aware column
  (19.8%), which the selection price does not use.
- **R7.** It cannot be made affordable. With lexical need at min_shared 1, nearly every dropped segment is
  "needed" again soon, as in A5, where 83–94% was demanded. Each fetch is an extra call at the full context,
  and the fetched content restarts growth, so compactions cascade (9,093 instead of 323).

## 3. Forward selection

Marginal input / price in points; `*` = passes the keep rule (≥ 2 input and ≥ 1 price).

**All ten sessions**
- Start (input 0, price 0): R3 +72.85/+64.65\*; R4 +52.05/+46.40\*; R5 +15.70/+13.83\*; R1 +0.92/+0.88;
  R2 +0.26/+0.24. **R3 is added.**
- From {R3} (72.85 / 64.65): R2 +0.04/+0.04; R1 +0.01/+0.03; R4 +0.00/+0.00; R5 −0.15/−0.58; R6 −2.79/−5.48;
  R7 −22,383/−21,868. **Stop.**

**Odd half (S01, S03, S05, S07, S09)**
- Start: R3 +73.30/+65.14\*; R4 +52.65/+47.00\*; R5 +18.40/+16.31\*; R1 +0.90/+0.86; R2 +0.29/+0.27. **R3 is
  added.**
- From {R3}: R2 +0.04/+0.05; R1 −0.01/+0.01; R4 0/0; R5 −0.12/−0.55; R6 −2.71/−5.43; R7 −29,195/−28,429.
  **Stop.**

**Even half (S02, S04, S06, S08, S10)**
- Start: R3 +71.75/+63.44\*; R4 +50.57/+44.93\*; R5 +9.08/+7.77\*; R1 +0.98/+0.94; R2 +0.19/+0.17. **R3 is
  added.**
- From {R3}: R1 +0.04/+0.08; R2 +0.02/+0.02; R4 0/0; R5 −0.22/−0.65; R6 −2.98/−5.61; R7 −5,718/−5,871.
  **Stop.**

R4 adds exactly 0 to R3, because a 150k ceiling never lets the context pass R4's 200k trigger.

## 4. The chosen set: n = 1, {R3: compact when the context would pass 150k}

| measure | value |
|---|---|
| input saved (pooled) | **72.85%** |
| price saved (B3/B4 model) | **64.65%** (expiry-aware 65.89%) |
| total money saved (C5; low / high output) | **52.4% / 50.8%** |
| share of the oracle (41.5%) | **175.5%** (see deviations 14) |
| extra steps | 549 = 323 compaction calls + 0.7 × 323 D2 re-reads; **0.82 per instruction, 3.39% of all calls** |
| per session input / price | S01 73.7/62.4, S02 75.0/66.0, S03 73.8/64.3, S04 38.7/26.9, S05 72.8/66.0, S06 70.1/59.9, S07 21.3/10.7, S08 39.4/26.0, S09 73.1/66.5, S10 71.8/64.6 |

The table below gives every rule's marginal contribution against the chosen set, in points of input / price /
expiry-aware price. R3 is measured by removing it; the others are measured by adding them.

| rule | marginal |
|---|---|
| R3 (in the set) | +72.85 / +64.65 / +65.89 |
| R1 | +0.01 / +0.03 / −0.06 |
| R2 | +0.04 / +0.04 / +0.05 |
| R4 | 0 / 0 / 0 |
| R5 | −0.15 / −0.58 / +0.20 |
| R6 | −2.79 / −5.48 / −5.07 |
| R7 | −22,383 / −21,868 |

For reference only, outside the protocol: a boundaries-only set without R3 would stop at R4 alone. On top of R4,
R5 adds +1.11 / +0.77 and R1 adds +0.36 / +0.35. R4 + R5 + R1 + R2 gives 53.6% / 47.6%.

## 5. Held-out validation

| selected on | set | held-out half: chosen set (input / price) | held-out half: all-ten set | loss |
|---|---|---|---|---|
| odd → evaluated on even | {R3} | 71.75 / 63.44 | 71.75 / 63.44 | 0.00 / 0.00 |
| even → evaluated on odd | {R3} | 73.30 / 65.14 | 73.30 / 65.14 | 0.00 / 0.00 |

Both halves choose the same set as all ten sessions, so **the result stands** by both criteria.

## 6. Sensitivity

**R3 threshold.** The selection is re-run in full at each threshold.

| C | R3 alone: input / price | compactions | extra steps (per instr., % of calls) | selection result |
|---|---|---|---|---|
| 100k | 77.98 / 66.10 | 754 | 1,282 (1.92, 7.9%) | {R3}; R6 −4.76 / −18.86 |
| **150k (primary)** | **72.85 / 64.65** | 323 | 549 (0.82, 3.4%) | {R3} |
| 200k | 67.12 / 60.27 | 204 | 347 (0.52, 2.1%) | {R3}; R5 +0.07 / −0.33 |

**R7 need.** The A7 primary rule thins need: V0 hits calibrated, N = 50, keep a block with ≥ 2 hits, or with
1 hit with probability 0.35; 10 draws.
- R7 stays catastrophic: marginal −21,238 / −20,803 on R3 (2.30M fetches), −807 / −790 on R4 and −114 / −109 on
  R5. It fails the keep rule in every draw.
- Two further variants do not rescue R7 either:
  - one extra call per fetching call instead of one per fetch: −98.9 / −1,355 on R3, −84.8 / −122.2 on R4,
    −34.3 / −35.3 on R5;
  - R3 without its D2 charge: −22,372 / −21,843.

**Interpretation checks (none changes the selection).**
- R3 with the B3 post size (base + 22k instead of 64k): 71.63 / 63.18.
- R3 without the compaction-read charge: 73.60 / 65.76.
- R4 with A5's re-obtained rate at r = 0.129 / 0.5: 50.71 / 44.71 and 47.82 / 40.44.
- R5 at the same rates: 14.17 / 12.21 and 9.82 / 7.48.

## 7. Session bootstrap of the final set

The method is E4's: 2,000 reps, `random.Random(20261006)`, 10 session ids drawn with replacement, pooled ratio
with multiplicity weights.

| | pooled | bootstrap 5–95% (median) | leave-one-session-out |
|---|---|---|---|
| input saved | 72.85 | 71.70–73.45 (72.86) | 72.40–73.07 |
| price saved | 64.65 | 63.17–65.55 | 64.02–64.84 |

All 2,000 reps stay above half the oracle (20.75%).

## 8. Pre-registered falsifiers

| falsifier | result | verdict |
|---|---|---|
| the chosen set captures less than half of the oracle in input | 72.85% vs 20.75% (bootstrap minimum is far above) | **passed** (not falsified) |
| its extra steps exceed 10% of all steps | 3.39% of calls (7.9% at C = 100k; 3.39% even if each restart cost a summary call, since there are no restarts) | **passed** |
| the two session halves choose different sets | both {R3} | **passed** |

**The expectation is partly wrong in its content.** Phase 2 expected a small boundary-based set of R4 or R3,
perhaps with R5, and with R1/R2 adding a point or two. The set is the smallest possible, R3 alone:
- R4 and R5 add nothing on top of it;
- R1 and R2 add under 0.1 point, not "a point or two";
- R6 and R7 subtract, as expected.

## Deviations and interpretations

Each item gives the reading taken and whether it could change the selection.

1. **Post-compaction size.**
   - R3 compacts to a 64k context in every session: 42k prefix, plus 22k written at 2.0.
   - S02's call-0 context is 64.6k, so there "64k" means slightly less than the base. The literal 64k is kept.
   - The replay's own 790k compaction also goes to 64k; B3 used base + 22k.
   - Effect: with base + 22k, R3 gives 71.63 / 63.18. **No change.**
2. **R3 also pays the compaction call's full read** (B3/B4), on top of D2's 82.7k. It also counts 1 + 0.7 extra
   steps per compaction. Without the read: 73.60 / 65.76. **No change.**
3. **R1 candidates.**
   - The candidates are fixed on the observed residency (B7) and re-tested against the replay's live segments.
     Results that only become resident because an observed compaction was skipped are not added.
   - R1 may remove a W1 result that is also ≥ 95% resident (10 steps overlap) when R2 is absent.
   - Image-only duplicates are left out of R1; there are none ≥ 200 tokens.
   - **No change:** R1 is below 1 point.
4. **R2.** "Repeats an identical failing call" is read as same signature, failing again, same epoch, earlier copy
   live. No such case exists outside W1. **No change.**
5. **Removing a call.**
   - The whole API call is removed only when it wrote no text and every tool call in it is flagged. Its thinking
     growth goes with it.
   - Otherwise only the flagged tool call's segments are removed.
   - **No change.**
6. **R4/R5 re-obtained charge.**
   - "The re-reads observed after real compactions" is read as A5's distinct N = 50 rate (r = 0.026) × R_b.
   - A6's per-boundary behavioural tokens are used only as the cross-check.
   - Effect: r = 0.129 or 0.5 lowers R4 by 1.3 to 4.2 points. **No change**, because R4 adds 0 to R3.
7. **Extra calls.** They are priced at 0.1 × context. Cold-start calls ride on base + summary + kept + T/2 (B5).
   The summary-writing call of a restart is not charged, as in B3, B5 and A6. **No change**, because the chosen
   set has no restarts.
8. **R5 restarts at every idle boundary, even when this does not shrink the context** (literal "whatever the
   context size"). **No change:** R5 is negative on R3.
9. **R6.**
   - Only attributed segments compete. Unattributed growth (thinking, images, overhead) has no lexical uses.
   - The lag is floored at 1 call. A segment that does not fit the budget is skipped.
   - Kept segments are rewritten at 2.0.
   - R6 does not act at harness or ceiling compactions.
   - **No change:** R6 is −2.5 to −2.8 points on every base, mostly because the larger post-compaction context
     makes R3 compact more often (416 vs 323).
10. **R7.**
    - Each fetched segment is its own extra call (literal).
    - R3's D2 charge is kept when R7 is present.
    - Only rule-dropped segments are fetchable, and a harness or ceiling compaction ends that.
    - Need is whole-session lexical refs, as in B3.
    - All alternatives (batched calls, D2 off, A7 thinning) stay below −34 points. **No change.**
11. **Stop rule.**
    - Read as: add the largest-price rule among those passing both thresholds, and stop when none passes.
    - The other reading is to stop as soon as the top-price rule fails.
    - Both give the same traces here. **No change.**
12. **Validation loss** is checked in both input and price. Both are 0.
13. **Extra steps** = added calls (compaction calls, D2's 0.7 re-read calls, 0.5 cold-start calls, fetches) ÷
    16,181 measured calls. Calls removed by R1/R2 are reported separately and not netted.
14. **Share of the oracle is 176%.**
    - The 41.5% oracle keeps every lexically needed segment and pays 1,000 tokens per re-fetch.
    - R3 drops needed content and pays only D2's behavioural re-read charge.
    - The protocol's ratio is reported literally. It compares two different need definitions, so above 100% it
      means only that the rule's charges are lighter than the oracle's need, not that the rule beats an
      optimum.

## Caveats

- **Quality is not measured.**
  - Every saving assumes that compaction at 150k (323 compactions instead of 34, about one every 50
    calls) loses nothing beyond D2's re-read charge. That charge comes from compactions at 783k
    (B4/E6 caveat).
  - R1/R2 assume the work succeeds without the removed calls.
- **Need definitions disagree by orders of magnitude.** Under lexical need (min_shared 1), dropping content is
  ruinous if it is re-fetched (R7). Under behavioural re-reading (A5/D2), dropping is nearly free. The selection
  of R3 rests on the behavioural charge.
- **The price model assumes perfect prefix caching** and no cache breaks from rewriting. Money uses C5's scaling
  (misses shrink with context), and the summary-generation output is the only output change. The output of
  removed or added calls is not modelled.
- **Samples.**
  - One user and ten sessions. S03, S09 and S10 hold 73% of input.
  - The halves are fixed by the protocol, not balanced. The odd half holds 71% of input.
  - The bootstrap covers session sampling only, not model uncertainty in the charges.
- **Lexical refs.** R6's activation and R4's R_b use lexical refs, which A5/E5 show to be mostly shared
  vocabulary.

## Findings

1. **The minimal rule set is one rule.** Compacting whenever the context would pass 150k saves 72.9% of input,
   64.7% of model price and 51–52% of total money, with 0.82 extra steps per instruction (3.4% of calls). All
   ten sessions, both halves, the bootstrap (71.7–73.5%) and C = 100k / 200k choose the same set.
2. **Boundary rules are dominated.** Restarting above 200k (52.1% / 46.4%) and after idle hours (15.7% / 13.8%)
   each pass the keep rule alone, but add 0 and −0.15 points once R3 caps the context below 200k.
3. **The reflex and habituation rules are real but tiny.** R1 removes 72 calls (0.92% input) and R2 removes 31
   (0.26%). On top of R3 they add 0.01–0.04 points, far below the 2-point keep threshold.
4. **Usage-weighted keeping and fetch-on-cue cost more than they save** under the pre-registered charges. R6
   costs 2.5–2.8 input points on every base. With lexical need, R7 multiplies input by 2× to 224×, and stays
   catastrophic under A7's behaviour-calibrated thinning and with batched fetches.
5. **No pre-registered falsifier fires.** The set reaches 72.9% (more than half the 41.5% oracle), its extra
   steps are 3.4% of calls, and the halves agree. Contrary to the stated expectation, the set is not built
   around boundaries, and R1/R2 do not add "a point or two".
