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
| **Prices.** Costs use list-price ratios (uncached 1, cache read 0.1, cache write 1.25 for 5 minutes and 2 for 1 hour). Subscriptions are priced differently. | Each call's writes are priced by the split its usage records. A first version priced all writes at 1.25 and understated the cost view (corrected; `self-audit-log.md`). The token views do not depend on prices. |
| **Output is unmeasured.** Output tokens in event pages and in most local records are stream-start placeholders (93–100% of calls with content, all sessions but S01's main one). | Never used in the token views. Cycle C5 estimates output at 9–12% of money by transferring S01's real counts (via visible output and thinking-signature length; held-out error +6%); this rests on S01 being typical and is reported as a band. A disclosure would remove it. |
| **The invisible third.** About 30% of context growth matches no visible piece of the transcript. | Pinned in every counterfactual (the oracle may not drop it), which makes the opportunity numbers conservative. Cycle C2: about half is the model's thinking, about 38% a constant per-call overhead, about 13% images (which `agent.bound` counts as zero tokens). |

## Methods

| Threat | Status |
|---|---|
| **Lexical reuse detection** decides what counts as "used again" (oracle bound, W5, W8). It misses use that leaves no verbatim trace and can see coincidental reuse. | Sensitivity grid (9 settings, calibrated and raw) for every bound number; the rule-tier detectors are pre-registered and will be checked against blind human labels before any of their numbers are called waste. Cycle A5 tested it against behaviour after the 34 real compactions: at the loosest setting it mostly measures shared vocabulary (a placebo window scores 72–99% of the real "demand"), and the agent re-obtained only 3–13% of it. Reuse-based numbers are upper bounds on need. Cycle E5 extended this to every segment: lexical reuse is as frequent before a segment exists as after it (topic, not need); with placebo corrections forgetting rises from 5.6% to 12–45% while the total opportunity stays at 44–56%. |
| **Tokenizer calibration** (about 2× the text estimate) scales segment sizes in the bound. | Raw (uncalibrated) results are reported next to calibrated ones. |
| **Counterfactuals rest on assumptions** the logs cannot test: that a summary would have been enough (restart rules, task-scoped what-ifs), that the oracle knows the future (bound). | Every what-if names its assumption; the oracle is reported as an opportunity, never as waste; simple online policies are backtested under a pre-registered protocol to show what is reachable without foresight. |
| **Code errors.** | Tests for every rule; byte-for-byte reproduction from public files; an independent code review per wave (cycle E2); two errors so far were found by review and corrected before publication (`self-audit-log.md`). |

## The researcher

| Threat | Status |
|---|---|
| **The same party builds the measures, runs them and interprets them**, with a stated position (against waste). Motivated choices are possible: which rule, which threshold, which view leads. | Rules and thresholds are committed before the data they judge (codebook v1, mechanical tier v1, rule tier v0 with sealed hashes); the primary result is always the pre-registered one and later views are labeled sensitivity analyses; corrections that lowered or raised a headline are logged either way; the blind labels come from someone other than the data owner. |
| **An AI agent did most of the analysis.** | Its work is logged per cycle, every number traces to a committed file or a stated private input, and the data owner reviews before anything is published. |
