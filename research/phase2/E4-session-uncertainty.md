> Working memo from cycle E4 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Public numbers only; the script and its output stay with the analysis files.

# E4: how much do the phase-2 headlines depend on which sessions are in the sample?

Data: public numbers only: the dataset-v2 per-call context series, per-session results in floor-t1.json and opportunity-v1.json, and the per-session percentages published in the B3 (R2 table) and D2 (scenario B) memos. Replays use `pickaxetax.survey.whatif` (restart, cap) and B4's `curve.replay_one` (C* grid). No private lines loaded; aggregates only. Script and full output (per-session values) are kept with the analysis files.

## Method
- Each headline is a pooled ratio: Σ saved / Σ denominator over sessions. Denominators: main-session input (6,579M; replays, oracle bound, B3, D2), all input including sub-agents (6,840M; floor tokens, steps-only), price units (836M; floor cost).
- Reproduce first: every pooled value must match the published number to within 0.1 pt before resampling.
- Leave-one-session-out (LOO): pooled over the other 9 sessions. "Driver" = the session whose removal moves the value most.
- Session bootstrap: 2,000 reps, `random.Random(20261006)`, draw 10 session ids with replacement, pooled ratio with multiplicity weights; 5th–95th percentile. The same draws are used for every headline, so orderings are evaluated inside each rep.
- Per-session median of the per-session ratios; share of the denominator from the largest session (S03 in every case).
- C\*: argmin of pooled replayed input over B4's fine grid (90k–800k, 10k steps, plus 783k), summary 22k, R per replay compaction = 0 / D2's 82.7k / 10× D2.
- B3 and D2 rows: saved = published per-session % × that session's series input (rounded memo percentages; reproduces pooled values to 0.05 pt).
- Self-checks (asserted): constant weights reproduce every pooled value; every rep holds 10 sessions; C\*(R = D2) = 100k as in B4.

## Reproduction
All headlines reproduce to within 0.1 pt except one. **Compaction at 390k on the public series gives 42.8%, not the 46.1% that B3 quotes for "whatif on series".** That B3 number came from series rebuilt from the traces. The public series with whatif.cap semantics (22k summary, compaction read charged) gives 42.8. Only a 2k summary gets close (46.3), so the gap is a difference in inputs, not in the code. The synthesis states this lever as 39–43%. Both ends reproduce from published per-session values: D2 scenario B 39.0 and B3 P3 43.3. Our 42.8 falls inside that range, so the synthesis figure stands.

## Headlines
| headline | published | pooled | LOO min–max (driver → value) | bootstrap 90% | per-session median [min, max] | largest-session share |
|---|---:|---:|---|---|---|---:|
| Removable cost (floor, price-weighted) | 8.92 | 8.92 | 8.7–9.3 (S03 → 9.3) | 8.1–9.8 | 9.6 [0.0, 20.0] | 31% |
| Removable tokens (floor) | 0.0008 | 0.0008 | 0.00075–0.00086 (S03 → 0.00075) | 0.0007–0.0009 | 0.0008 [0.0, 0.0024] | 31% |
| Steps only on W1/W2, % of input | 2.6 | 2.59 | 2.3–2.9 (S03 → 2.9) | 2.0–3.4 | 3.7 [0.0, 4.4] | 31% |
| Oracle paging P = 1000 | 41.5 | 41.47 | 41.0–41.9 (S02 → 41.0) | 40.4–43.2 | 40.6 [17.7, 47.4] | 31% |
| Forgetting only P = inf | 5.6 | 5.59 | 5.5–5.9 (S03 → 5.9) | 5.2–6.5 | 5.7 [4.8, 16.4] | 31% |
| Restart above 200k, 10k summary | 55.2 | 55.20 | 52.3–57.5 (S03 → 52.3) | 48.7–59.5 | 53.4 [0.0, 61.5] | 31% |
| New session every 3 instructions | 55.1 | 55.08 | 51.2–57.3 (S03 → 51.2) | 46.4–60.8 | 48.7 [2.8, 63.6] | 31% |
| New session every 10 instructions | 22.3 | 22.32 | 17.5–24.0 (S03 → 17.5) | 15.4–28.2 | 15.4 [0.0, 34.4] | 31% |
| Compaction at 390k, series cap 22k | 46.1 (B3) | **42.84 (does not reproduce)** | 42.1–43.3 (S03 → 42.1) | 40.9–43.8 | 41.3 [0.0, 47.4] | 31% |
| Compaction at 390k, B3 P3 (segment replay) | 43.3 | 43.34 | 42.7–43.7 (S03 → 42.7) | 41.5–44.3 | 41.8 [0.0, 46.4] | 31% |
| Compaction at half trigger + re-reads (D2 B) | 39.0 | 39.03 | 38.5–39.4 (S03 → 38.5) | 37.6–40.0 | 38.1 [0.0, 42.7] | 31% |
| Ceiling 200k | 65.7 | 65.70 | 65.0–66.0 (S09 → 65.0) | 64.2–66.6 | 64.9 [0.0, 68.3] | 31% |
| Ceiling 150k | 71.6 | 71.60 | 71.1–71.8 (S09 → 71.1) | 70.4–72.4 | 71.2 [19.8, 73.3] | 31% |
| B3 P1 restart > 200k (segment replay) | 54.8 | 54.75 | 52.0–57.1 (S03 → 52.0) | 48.4–59.0 | 53.2 [0.0, 62.7] | 31% |
| B3 P2 pointers alone (ceiling kept) | −4.1 | −4.06 | −6.0 to −2.2 (S03 → −6.0) | −7.9 to −0.6 | −0.6 [−13.0, 35.0] | 31% |
| B3 bundle P1 + P3 | 57.5 | 57.53 | 56.0–58.7 (S03 → 56.0) | 53.5–60.0 | 55.0 [0.0, 62.7] | 31% |

Notes:
- S03, S09 and S10 together hold 73% of main input. The three small sessions (S04, S07, S08) hold under 1%. They barely move any pooled value, but they hold the zeros and extremes of the per-session ranges.
- Several per-session medians differ from the pooled values: every 10 instructions (15.4 vs 22.3), every 3 (48.7 vs 55.1), steps-only (3.7 vs 2.6) and pointers (−0.6 vs −4.1). In each case the pooled number is a statement about the large sessions.

### Input-optimal ceiling C\* (B4 grid)
| R per compaction | pooled C\* | LOO range | bootstrap 90% | per-session C\* median [min, max] | reps with C\* ≤ 150k |
|---|---:|---|---|---|---:|
| 0 | 100k | 90–100k | 90–100k | 90k [90k, 110k] | 100% |
| D2 (82.7k) | 100k | 100–110k | 90–110k | 100k [90k, 110k] | 100% |
| 10× D2 | 140k | 130–140k | 120–150k | 130k [120k, 180k] | 100% |

## Do the synthesis conclusions survive resampling?
Each row gives the share of the 2,000 bootstrap reps in which the ordering holds, and the number of the 10 LOO samples in which it holds. All rows hold in the full sample.

| conclusion (synthesis wording) | ordering tested | bootstrap share | LOO |
|---|---|---:|---:|
| Restart beats trimming / forgetting | restart > 200k (series) > forgetting-only P = inf | 100% | 10/10 |
| | restart (B3 P1) > pointers alone (B3 P2) | 100% | 10/10 |
| | restart > cap on tool results at 2k (4.4%, held constant: no per-session data) | 100% | 10/10 |
| The ceiling sets the average (slowing growth alone saves ~nothing) | pointers alone ≤ 0 | 97.6% | 10/10 |
| | pointers alone < 5% | 99.9% | 10/10 |
| | ceiling 200k > pointers alone + 50 pt | 100% | 10/10 |
| | ceiling 200k > restart above 200k | 100% | 10/10 |
| | ceiling 150k > ceiling 200k (a lower ceiling saves more) | 100% | 10/10 |
| Carrying is the big lever, forgetting the smaller one | oracle P = 1000 > forgetting P = inf | 100% | 10/10 |
| | oracle P = 1000 > 4 × forgetting P = inf | 100% | 10/10 |
| The largest lever is available to the user today | restart > 200k > oracle P = 1000 | 99.5% | 10/10 |
| Restart does almost all the work in the bundle | P1 > P3 (B3) | 99.9% | 10/10 |
| | restart > 200k > cap 390k (series) | 99.9% | 10/10 |
| | P1 + P3 − P1 < 5 pt | **88.7%** | 10/10 |
| Restart above 200k vs fixed counts | restart > 200k > every 10 instructions | 100% | 10/10 |
| | restart > 200k > every 3 instructions | **50.1%** | 7/10 |
| The floor is small | floor tokens < 0.01% of input | 100% | 10/10 |
| | floor cost < 10% | 97.0% | 10/10 |
| | steps-only W1/W2 < 5% of input | 100% | 10/10 |
| | floor cost < restart saving | 100% | 10/10 |
| C\* is far below today's 783k | C\* (R = D2) ≤ 150k | 100% | 10/10 |
| | C\* (10× D2) ≤ 200k | 100% | 10/10 |

## Caveats
- This is within-person sampling only. The bootstrap treats these 10 sessions as a sample of this person's sessions. It says nothing about other users, other harness versions, or other models.
- A percentile bootstrap with n = 10 tends to give intervals that are too narrow. The 90% intervals are lower bounds on the real uncertainty.
- Resampling sessions does not test the assumptions that the replays and bounds rest on: lexical reuse detection, summaries being enough, flat R. Those (cycle E3 and phase 3) move the numbers much more than sample composition does. One example: the oracle ranges 16–54% across detectors (E3) but only 40–43% across resamples.
- The B3 and D2 rows are rebuilt from per-session percentages rounded to 0.1 pt, so their intervals carry up to ±0.05 pt of rounding.
- The orderings are not independent, because they share the same draws. The "cap tool results 2k" comparison holds its side fixed at 4.4% because no per-session values are published.
- The floor and steps-only numbers come from published per-session results, which were computed on private data. Only their pooling is redone here.
- C\* is limited to the 10k grid steps. The lower end (90k) sits near the post-compaction size, which B4 already flags as an edge effect.

## Findings
1. All headlines reproduce to within 0.1 pt except compaction at 390k on the public series (42.8, not 46.1). The synthesis range of 39–43% still holds.
2. Sample composition matters little for the ceiling and paging bounds: bootstrap 90% intervals are about ±1–2 pt (ceiling 200k 64–67%, oracle 40–43%, forgetting 5–6.5%). The user restart rules are less stable: restart above 200k 49–60%, every 10 instructions 15–28%. Removing S03 lowers each of them by 3–5 pt.
3. Every directional conclusion survives in at least 97% of reps and in all 10 LOO samples. These are: restart beats trimming and forgetting; pointers alone save at most about 0; carrying beats forgetting; restart beats the oracle and the 390k compaction; the floor is small (cost < 10% in 97% of reps); C\* ≤ 150k in every rep.
4. Two comparisons are weaker. Restart above 200k vs every 3 instructions is a coin toss (50%), so the 55.2 vs 55.1 tie should not be read as a ranking. "The earlier compaction adds under 5 pt on top of restart" holds in only 89% of reps.
5. S03 is 31% of input and drives most of the LOO extremes. Per-session medians for the fixed-count restarts and for steps-only differ from the pooled values by 1–7 pt, so pooled headlines describe mainly the three large sessions.
