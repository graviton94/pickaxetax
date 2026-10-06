> Working memo from cycle E11 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only.

# E11: session-level uncertainty of the rows added after E4 (A6, C7, C5)

Aggregates only. Scripts and per-session values are kept with the analysis files.

## Method
- **Same procedure as E4.** Each row is a pooled ratio, Σ saved / Σ denominator over sessions.
  - Leave-one-session-out (LOO): "driver" is the session whose removal moves the value most.
  - Session bootstrap: 2,000 reps, `random.Random(20261006)`, 10 draws with replacement in dataset-v2 session order, pooled ratio with multiplicity weights, 5th–95th percentile.
  - Orderings are evaluated inside each rep, and the LOO count is out of 10.
  - The draws are identical to E4's. The uncharged restart row gives E4's 48.7–59.5 interval exactly.
- **Per-session numerators and denominators.** I imported the earlier cycles' functions read-only and copied nothing (run with `-B`). Nothing was written into their folders and the repo is unchanged.
  - **Rows 1–2 (A6).** `A6/stage3.replay` per session with its allow masks: all boundaries, or only boundaries after a gap over 1 h. Charge = B5 median cold start (22.5k, 0.5 calls) plus the boundary's re-obtained tokens (primary window).
    - Denominators: per-session measured input, B5 model price, and expiry-aware price (`stage3.MS`).
    - "% total money" (my addition): the session's model-price saving fraction × its actual main input-side money, divided by its total money (C5's "scaled" convention).
  - **Row 3 (C7).** C7's per-session replay output: observed main money minus policy cost. Policies: (g) 1h + hourly keep-alive to 8 h; (c) per-write oracle under the entry reading. Denominators: main input money, or per-session total money from C5's per-session output (input side of main + sub-agents + 5 × the low or high output estimate).
  - **Row 4 (C5).** Carried re-read = per-session `carried_read`. Lever savings = (1 − lever model price / base model price) × main input-side money, using `money.restart_price` and B4 `curve.replay_one` with R = 0, divided by per-session total money.
- **Input checks.** Every loaded file holds numbers, session ids, 16-hex hashes, tool and category labels, model ids and agent ids only. No text, path or command strings.
- **Self-checks (asserted).**
  - Per-session total money sums to C5's totals.
  - C7's observed main money equals C5's main input-side money per session.
  - A6's base model price equals C5's per session to 2e-5. S03 differs by 4k units in one drop case.
  - Constant weights reproduce every pooled value.

## Reproduction
Every published pooled value reproduces to within 0.1 pt (most to 0.01).
- A6: 55.20, 52.70, 47.62, 49.83, 18.91, 16.04, 14.59, 19.97.
- C7: 4.81, 4.20, 4.07, 6.71, 5.85, 5.67.
- C5: 54.08, 52.40, 51.90, 50.29, 44.60, 43.21, 34.49, 33.42.
- Restart counts: 168 (all boundaries, charged) and 48 (breaks only).

Two notes on the reproduction:
- The break-only rule is published at "about 15% of cost" in synthesis §3. It is 14.6 on the B5 basis.
- The C7 money figures use C7's rounded total (916.5M). Exact per-session totals give the same values to 0.01.

## Table (% saved; largest session S03 holds 31–32% of every denominator)
| row | published | pooled | LOO min–max (driver → value) | bootstrap 90% | per-session median [min, max] |
|---|---:|---:|---|---|---|
| 1 Restart > 200k, cold start + re-reads charged, % input | 52.7 | 52.70 | 50.3–54.8 (S03 → 50.3) | 47.0–56.2 | 51.3 [0.0, 60.2] |
| 1 same, % B5 price | 47.6 | 47.62 | 46.3–49.4 (S05 → 49.4) | 43.0–50.1 | 46.9 [0.0, 53.4] |
| 1 same, % expiry-aware price | 49.8 | 49.83 | 48.4–51.4 (S05 → 51.4) | 45.3–52.2 | 48.6 [0.0, 53.4] |
| 1 same, % total money (B5-scaled, low output) | — | 41.49 | 40.5–42.7 (S05 → 42.7) | 38.3–43.2 | 40.9 [0.0, 44.8] |
| 2 Restart only after a break > 1 h, charged, % input | 16.0 | 16.04 | 13.1–17.2 (S09 → 13.1) | 10.9–20.1 | **5.2** [0.0, 24.7] |
| 2 same, % B5 price | 14.6 (≈15) | 14.59 | 11.8–15.4 (S09 → 11.8) | 10.0–18.6 | 5.3 [−0.3, 23.2] |
| 2 same, % expiry-aware price | 20.0 | 19.97 | 17.2–21.0 (S09 → 17.2) | 14.8–23.9 | 8.2 [0.0, 28.5] |
| 2 same, % total money (B5-scaled / expiry-scaled, low) | — | 12.76 / 17.36 | 10.5–13.3 / 15.2–18.1 (S09) | 9.1–15.8 / 13.3–20.3 | 4.9 / 7.6 |
| 3 1h + hourly keep-alive to 8 h, % main input money | 4.81 | 4.81 | 4.1–5.0 (S03 → 4.1) | 3.2–5.7 | **1.1** [−13.0, 7.5] |
| 3 same, % total money low / high | 4.20 / 4.07 | 4.20 / 4.07 | 3.6–4.4 / 3.5–4.2 (S03) | 2.9–4.9 / 2.8–4.8 | 1.1 / 1.0 [−11.5, 6.4] |
| 3 Per-write TTL oracle (entry), % main input money | 6.71 | 6.71 | 6.5–7.0 (S03 → 7.0) | 6.4–7.4 | 7.2 [5.7, 20.2] |
| 3 same, % total money low / high | 5.85 / 5.67 | 5.85 / 5.67 | 5.6–6.1 / 5.5–5.9 (S03) | 5.5–6.6 / 5.3–6.4 | 6.5 / 6.2 [4.8, 17.6] |
| 4 Re-reading carried context, % total money low | 54.1 | 54.08 | 53.3–55.1 (S05 → 55.1) | 50.5–55.9 | 51.7 [23.4, 58.3] |
| 4 same, high output | 52.4 | 52.40 | 51.6–53.4 (S05 → 53.4) | 48.9–54.2 | 50.1 [21.5, 56.7] |
| 4 Ceiling 200k, % total money low / high | 51.9 / 50.3 | 51.90 / 50.29 | 51.0–52.7 / 49.4–51.1 (S10) | 50.0–53.9 / 48.4–52.3 | 50.3 / 48.3 [0.0, 56.4] |
| 4 Restart above 200k, % total money low / high | 44.6 / 43.2 | 44.60 / 43.21 | 43.1–46.0 / 41.8–44.5 (S03) | 41.0–46.7 / 39.7–45.3 | 44.4 / 42.6 [0.0, 48.0] |
| 4 Ceiling 390k, % total money low / high | 34.5 / 33.4 | 34.49 / 33.42 | 33.9–34.8 / 32.8–33.7 (S10) | 33.1–35.6 / 32.0–34.5 | 34.2 / 33.0 [0.0, 37.5] |

Per session:
- **Break-only restart.** Restarts happen in 6 sessions: S03 17, S09 13, S10 7, S02 5, S05 5, S06 1. S01, S04, S07 and S08 have none, so the per-session median (5.2) is a third of the pooled value.
- **Hourly keep-alive.** It loses money in 5 sessions: S01 −1.3, S04 −7.6, S06 −1.8, S07 −9.7 and S08 −11.5 (% of total money, low). The pings go to sessions that do not return. It gains 3.4–6.4 in the other five.
- **Per-write oracle.** It saves in every session (4.8–17.6).

## Orderings (share of 2,000 reps; LOO out of 10; all hold in the full sample)
| ordering | bootstrap share | LOO |
|---|---:|---:|
| (a) charged restart > break-only restart, % input | 100% | 10/10 |
| (a) same, % B5 price | 100% | 10/10 |
| (a) same, % expiry-aware price | 100% | 10/10 |
| (a) charged restart > 2 × break-only, expiry-aware price | 99.0% | 10/10 |
| (b) break-only restart > hourly keep-alive, both % total money (B5-scaled) | 100% | 10/10 |
| (b) same, break-only expiry-scaled | 100% | 10/10 |
| (b) as synthesis states it (break-only % B5 price vs keep-alive % total money) | 100% | 10/10 |
| (b′) break-only (B5-scaled) > per-write oracle (entry), % total money | 99.1% | 10/10 |
| (c) ceiling 200k > restart above 200k, % total money low | 100% | 10/10 |
| (c) same, high output | 100% | 10/10 |
| (c′) ceiling 200k > charged restart (B5-scaled), % total money | 100% | 10/10 |
| restart above 200k > ceiling 390k, % total money | 99.9% | 10/10 |
| re-reading carried context > 50% of total money (low) | 96.8% | 10/10 |

Gaps:
- (a) on input: 31.5–41.7 pt (90%).
- (c) on total money (low output): 7.3 pt pooled, 3.6–12.2 pt (90%).
- (b) holds in every individual session too. Where the keep-alive loses, the break-only restart is 0, or −0.3 in S06 against −1.8.

## Caveats
- **Within-person sampling only, n = 10.** Percentile intervals are too narrow, so treat them as lower bounds. As in E4, the resampling does not test the model assumptions: summary sufficiency, the uniform cold-start charge, C7's TTL semantics and ping model, and C5's output estimate. Those move the numbers more than sample composition does. One example: the oracle is 5.9% of total money under the entry reading and 1.4% under the segment reading.
- **"% total money" for the A6 rows is my addition.** It scales A6's model-price saving fraction onto actual main money, as C5 does, which assumes cache misses shrink with the context. Ordering (b) needs this common unit. The published A6 rows are on model-price bases, not on total money.
- **The break-only rule rests on 48 restarts in 6 sessions,** 30 of them in S03 and S09. Its interval (10.9–20.1% of input) is the widest relative to its value of any row, so "16%" describes the large sessions with frequent long breaks.
- **The hourly keep-alive is net negative in half the sessions.** Its pooled 4.2% depends on the large sessions, and its per-session median is about 1%.
- **The A6 charge uses the boundary's observed re-reads.** Those were measured without a restart, which A6 notes double counts and is conservative. The cold start is the same median in every session, so the resampling does not vary it.
- **Shared draws.** The orderings use the same draws and are not independent.

## Findings
1. Every added row reproduces to within 0.1 pt. Bootstrap 90% intervals: charged restart 47.0–56.2% of input (43.0–50.1% B5 price); break-only restart 10.9–20.1% (10.0–18.6% price, 14.8–23.9% expiry-aware); hourly keep-alive 2.9–4.9% of total money; per-write oracle 5.5–6.6%; carried re-reading 50.5–55.9% (low output); ceiling 200k / restart / ceiling 390k in total money 50.0–53.9 / 41.0–46.7 / 33.1–35.6%.
2. All three orderings hold in 100% of reps and 10/10 LOO samples: (a) charged restart > break-only restart (gap 31–42 pt of input); (b) break-only restart > hourly keep-alive on a common total-money basis (also in every single session); (c) ceiling 200k > restart above 200k in total money (gap 3.6–12.2 pt). "Carried re-reading > half of all money" holds in 96.8% of reps.
3. The two break- and idle-dependent levers are pooled statements about the large sessions. The break-only restart's per-session median is 5.2% against 16.0% pooled, with no restarts in 4 sessions. The hourly keep-alive's median is 1.1% against 4.8%, and it loses money in 5 of 10 sessions. The ceiling, restart and carried-share rows move by only about ±1–2 pt.
