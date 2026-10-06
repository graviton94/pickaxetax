# Threats to validity (phase 2, as of 2026-10-06)

What could make the phase 2 numbers wrong or misleading, what was done about each, and what is
still open. Kept up to date as cycles find new ones (`log.md`).

## Sample

| Threat | Status |
|---|---|
| **One person, one agent, one kind of work.** Ten Claude Code sessions of one user, mostly software and game development, July–October 2026. Nothing generalizes to people, agents or tasks. | Open. `pxt survey run` lets others produce the same measurements on their own transcripts; the anonymous contribution path does not yet carry them (a schema change, for the maintainer to decide). |
| **Long, heavy sessions dominate.** S03, S09 and S10 hold most of the input; pooled numbers follow them. | Reported: per-session tables everywhere, and session medians in the backtest. Cycle E4: S03 alone is 31% of input; leave-one-out and a session bootstrap move the ceiling and paging numbers by about ±1–2 points and the restart rules by 3–5; every directional conclusion holds in at least 97% of resamples (within this person only; n = 10 intervals are too narrow). |
| **Period.** The ten sessions with token records span eight weeks (2026-08-10 to 10-05); "three months" (from 07-10) is the session list's period, which includes two July sessions with costs only. | Stated in the phase 2 documents; note 1 and the site say "three months" (recorded for the data owner). No trend with date is detectable at n = 10 (cycle D3). |
| **Snapshots.** S01, S02, S03 and S08 kept being used after they were measured; they are cut at the measurement. | Cuts are by call or instruction count and verified against the dataset (usage identical to the token). |

## Data

| Threat | Status |
|---|---|
| **Two sources** (local transcripts, event-API pages) may differ. | Usage matches the in-session measurement exactly where both exist (S02, S03). No sign of truncated tool results in event pages. Instruction splitting differs slightly (S02 49 vs 48, S03 299 vs 275); dataset counts keep the in-session values. Output tokens from event pages are stream-start placeholders and are never used. |
| **Prices.** Costs use list-price ratios (uncached 1, cache read 0.1, cache write 1.25 for 5 minutes and 2 for 1 hour). Subscriptions are priced differently. | Cycle C8 re-ran every cost headline over 48 alternative ratio settings (read 0.05–0.15, 1-hour write 1.5–2.0, output 3–5): the order of the levers and the 1-hour cache choice hold in all; "half of all money re-reads finished work" needs a read price of at least about 0.05–0.09 (56–69% everywhere with re-writes); the floor moves most (4.7–15.4%). Each call's writes are priced by the split its usage records. A first version priced all writes at 1.25 and understated the cost view (corrected; `self-audit-log.md`). The token views do not depend on prices. |
| **Output is unmeasured.** Output tokens in event pages and in most local records are stream-start placeholders (93–100% of calls with content, all sessions but S01's main one). | Never used in the token views. Cycle C5 estimates output at 9–12% of money by transferring S01's real counts (via visible output and thinking-signature length; held-out error +6%); this rests on S01 being typical and is reported as a band. A disclosure would remove it. |
| **The invisible third.** About 30% of context growth matches no visible piece of the transcript. | Pinned in every counterfactual (the oracle may not drop it), which makes the opportunity numbers conservative. Cycle C2: about half is the model's thinking, about 38% a constant per-call overhead, about 13% images (which `agent.bound` counts as zero tokens). |

## Methods

| Threat | Status |
|---|---|
| **Lexical reuse detection** decides what counts as "used again" (oracle bound, W5, W8). It misses use that leaves no verbatim trace and can see coincidental reuse. | Sensitivity grid (9 settings, calibrated and raw) for every bound number; the rule-tier detectors are pre-registered and will be checked against blind human labels before any of their numbers are called waste. Cycle A5 tested it against behaviour after the 34 real compactions: at the loosest setting it mostly measures shared vocabulary (a placebo window scores 72–99% of the real "demand"), and the agent re-obtained only 3–13% of it. Reuse-based numbers are upper bounds on need. Cycle E5 extended this to every segment: lexical reuse is as frequent before a segment exists as after it (topic, not need); with placebo corrections forgetting rises from 5.6% to 12–45% while the total opportunity grows from 41.5% to 44–56%. Cycle E8 checked the corrections against behaviour (the files re-read after the 34 real compactions): lexical-v1 and the cross-session corrections predict re-reads better than chance (AUC 0.55–0.61), and the time-placebo corrections do not, so forgetting is most likely 5.6–13%. The test is weak (modest AUC; re-reading is partly habit). |
| **Tokenizer calibration** (about 2× the text estimate) scales segment sizes in the bound. | Raw (uncalibrated) results are reported next to calibrated ones. |
| **Counterfactuals rest on assumptions** the logs cannot test: that a summary would have been enough (restart rules, task-scoped what-ifs), that the oracle knows the future (bound). | Every what-if names its assumption; the oracle is reported as an opportunity, never as waste; simple online policies are backtested under a pre-registered protocol to show what is reachable without foresight. |
| **Code errors.** | Tests for every rule; byte-for-byte reproduction from public files; three independent code reviews (cycles E2, E6 and E9: 14 confirmed bugs, each fixed with a regression test); replay errors found in cycles B, B3 and E4; two consistency audits of every published number (cycles E7 and E10), corrected and logged, except the items left for the data owner (`log.md`, `self-audit-log.md`). |

## The researcher

| Threat | Status |
|---|---|
| **The same party builds the measures, runs them and interprets them**, with a stated position (against waste). Motivated choices are possible: which rule, which threshold, which view leads. | Rules and thresholds are committed before the data they judge (codebook v1, mechanical tier v1, rule tier v0 with sealed hashes); the primary result is always the pre-registered one and later views are labeled sensitivity analyses; corrections that lowered or raised a headline are logged either way; the blind labels come from someone other than the data owner. |
| **An AI agent did most of the analysis.** | Its work is logged per cycle, every number traces to a committed file or a stated private input, and the data owner reviews before anything is published. |

## What moves each headline, and by how much

Each headline was stress-tested separately against each source of uncertainty. The widest range
shows what the number depends on most.

| Headline (point value) | Sample: resampling sessions (E4) | Detector: what counts as reuse (E3, E5, E8) | Prices: 48 ratio settings (C8) | Assumption: re-reads, cold start (A5, B5, A6) | Depends most on |
|---|---|---|---|---|---|
| Mechanical floor, cost (8.92%) | 8.1–9.8% | — (mechanical) | 4.7–15.4% | — | prices |
| Steps spent only on duplicates/errors (2.6% of input) | 2.0–3.4% | — | — (tokens) | — | sample |
| Oracle paging, P = 1000 (41.5%) | 40.4–43.2% | 35–56% | — (tokens) | — (foresight assumed) | detector |
| Forgetting only, P = ∞ (5.6%) | 5.2–6.5% | 7–8% calibrated to behaviour (6–11% credible; 13–32% if only compaction-caused re-reads count as need); 3–45% across all definitions | — | — | detector |
| Restart above 200k (55.2% of input) | 48.7–59.5% | 26.7–45.7% if lexical reuse were need (A4); behaviour says it is not | 37–49% of total money | 52–53% with observed charges; 41% at the 90th-percentile cold start | sample, then the charge |
| Ceiling 200k (66.8% of input) | 65–68% | — | 42–58% of total money | +R per compaction: 64–67% | prices (in money) |
| Ceiling 390k (44% of input) | about ±1 | — | 29–38% of total money | 39% with D2's gross re-reads | prices |
| "Half of all money re-reads finished work" (52–54%) | — | B definition vs visible-only: about a third at the lower bound | 41–63% (56–69% with re-writes) | — | prices, definition |
| Optimal ceiling C\* (80–90k; 110–160k price-weighted) | 90–110k (pre-E6 grid) | — | — | 10× re-read cost: 120k (price 160k) | re-read cost per compaction |

None of these ranges reverses an ordering between levers (E4: ≥ 97% of resamples for the orderings
it tested; C8: 48 of 48 price settings). Every range is within this person's data. None says
anything about other people, agents or tasks, and none tests quality. Those are phase 3's job.
