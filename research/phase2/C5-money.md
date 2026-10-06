> Working memo from cycle C5 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# C5: where does the money go?

## Method
- Data: per-call usage of the ten sessions at the dataset-v2 snapshots (lines_v2), with usage de-duplicated per message id, main session and sub-agents (sidechain, one context per agent) kept separate. All 18,543 calls are covered. Main-session context sums equal the dataset-v2 series exactly in all ten sessions.
- Prices, relative to uncached input = 1: uncached 1, cache read 0.1, 5-minute cache write 1.25, 1-hour cache write 2.0 (from `ephemeral_1h_input_tokens`), output 5. The main sessions wrote only 1-hour cache and the sub-agents only 5-minute cache.
- Output tokens (per call, the maximum over the message's streamed lines):
  - **Placeholder test.** A call counts as content-bearing if its visible output (text plus tool-call input, estimator × the C2 tokenizer factor) is at least 50 tokens. It is flagged as a placeholder if the recorded output is less than half of that visible output.
  - **Estimates for placeholder sources.**
    - (a) Component, low: factor × visible + θ × thinking-signature characters, with θ = 0.179 tokens per character fitted on S01's real counts. Held out on S01 (fit on odd calls, predict even; fit on the first half, predict the second), it is +5.5% / +5.7% too high, with a per-call Spearman of 0.98.
    - (b) Component, high: the same with θ = 0.39, the largest residual-per-character slope in C2.
    - (c) Growth ratio: S01's output divided by the next call's context growth (ρ = 0.67), applied to positive growth. It is used only for main sessions, because sub-agent growth is mostly tool results.
    - Each call takes the larger of the recorded and the estimated value. Band = minimum and maximum of the applicable estimates. S01's main session keeps its real counts.
- Cache-read split, following the B method: base = context at call 0, and carried from finished instructions = min(context, context at the instruction's first call) − base, which is 0 in the first instruction. The prompt is laid out as [base | carried | current]. Cache read covers the first `cache_read` tokens, the cache write comes next, and uncached input is the tail.
- Levers, main session only, replayed on the public series:
  - **Restart above 200k.** Mirrors `whatif.restart` (10k summary). Input and restart counts match whatif exactly in every session.
  - **Ceiling 200k / 390k.** Uses B4 `curve.replay_one`, with R = 0 and R = D2 (82.7k, priced at 0.25).
  - **Price rule (B4).** 0.1 × kept context + 2.0 × new content. A restart or compaction costs 0.1 × base + 2.0 × (summary + growth). This matches the measured write price: every main session wrote 1-hour cache.
  - **Scaling.** The model's saving fraction, per session, is applied to that session's actual input-side money ("scaled"; this assumes cache misses shrink with the context). Also shown: model units saved over actual money ("unscaled"; misses unchanged).
  - **Floor.** Taken from floor-t1.json and recomputed here.
- Scripts and the per-call numbers they use are kept with the analysis files (numbers only).

## 1. Where the money goes (% of total money)
Pooled shares; output shown three ways. Each row sums to 100.

| scope, output as | uncached | cache read | write 5m | write 1h | output | total units |
|---|---:|---:|---:|---:|---:|---:|
| all, recorded | 0.01 | 80.27 | 1.38 | 17.70 | 0.65 | 841.7M |
| all, estimate low | 0.01 | 73.71 | 1.27 | 16.25 | **8.76** | 916.5M |
| all, estimate high | 0.01 | 71.42 | 1.23 | 15.75 | **11.60** | 945.9M |
| main, low / high | 0.00 | 74.7 / 72.6 | 0 | 17.1 / 16.6 | 8.2 / 10.8 | 871.0 / 896.6M |
| sub-agents, low / high | 0.04 / 0.03 | 55.2 / 51.0 | 25.5 / 23.5 | 0 | 19.3 / 25.5 | 45.5 / 49.3M |

Per session, output share of money with the estimate band (low–high):

| session | main | sub-agents |
|---|---|---|
| S01 | 15.5 (real counts) | 26.0–28.5 |
| S02 | 7.2–11.6 | 12.1–19.2 |
| S03 | 10.2–12.6 | 23.2–31.2 |
| S04 | 12.9–14.6 | — |
| S05 | 6.6–9.1 | — |
| S06 | 9.6–13.1 | — |
| S07 | 21.0–27.2 | — |
| S08 | 11.6–20.7 | — |
| S09 | 6.5–8.8 | 19.2–24.4 |
| S10 | 6.9–9.5 | — |

Across sessions and output scenarios, cache read is 39–82% of main money. The 1-hour write is 13–54%; it is largest in the small sessions S04 and S08, which have many re-writes.

**Placeholders.** Recorded output is a placeholder in 93–100% of content-bearing calls in S02–S10 and in all sub-agents (S01's included). It is 0% in S01's main session. Recorded output is 1.09M tokens against an estimated 16.1–21.9M.

**Sub-agents.** They are 3.8% of input tokens but 5.0–5.2% of money. Output is 19–25% of their money.

## 2. Re-reading carried context (main session)
| part | price units | % of main input-side money | % of total money (low / high output) |
|---|---:|---:|---:|
| cache read: base (system, tools) | 81.6M | 10.2 | 8.9 / 8.6 |
| **cache read: carried from finished instructions** | **495.7M** | **62.0** | **54.1 / 52.4** |
| cache read: current instruction | 73.2M | 9.2 | 8.0 / 7.7 |
| cache write: base | 8.2M | 1.0 | 0.9 / 0.9 |
| cache write: carried (re-written after expiry) | 94.4M | 11.8 | 10.3 / 10.0 |
| cache write: current | 46.4M | 5.8 | 5.1 / 4.9 |

- Carried context is 76.1% of main input tokens and 76.2% of main cache-read money.
- **Re-reading carried context is about 52–54% of all money**, and about 62–64% when its re-writes after cache expiry are added.
- The visible-only definition (`bound`, 46.5% of input) would put the read part at about a third of all money. That is a lower bound, because invisible thinking and overhead are carried too.
- By session, the carried read is 28–30% of main money in the short sessions (S04, S07, S08) and 49–68% in the long ones.

## 3. The levers by money
Savings in % of each base. "All-in" = all input-side money (main and sub-agents). "Total" = all-in plus output (low output estimate / high output estimate).

| lever | % input tokens | model price % (main) | scaled % main-in | % all-in | **% total (lo / hi out)** | unscaled % total (lo / hi) | after summary output* (lo / hi) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ceiling 200k, R=0 | 65.7 | 59.5 | 59.5 | 56.9 | **51.9 / 50.3** | 47.1 / 45.6 | 49.2 / 47.6 |
| Ceiling 200k, R=D2 | 65.4 | 58.9 | 58.9 | 56.3 | 51.3 / 49.7 | 46.5 / 45.1 | 48.6 / 47.1 |
| Restart above 200k (10k summary) | 55.2 | 51.2 | 51.1 | 48.9 | **44.6 / 43.2** | 40.4 / 39.2 | 43.8 / 42.4 |
| Ceiling 390k, R=0 | 42.8 | 39.6 | 39.5 | 37.8 | **34.5 / 33.4** | 31.3 / 30.3 | 33.5 / 32.4 |
| Ceiling 390k, R=D2 | 42.7 | 39.4 | 39.3 | 37.6 | 34.3 / 33.2 | 31.1 / 30.1 | 33.2 / 32.2 |
| Floor (W1+W2+W6 premium) | 0.0008 | — | 9.33 | **8.92** | **8.14 / 7.89** | — | — |

\*The summaries themselves are generated at the output price: 22k tokens per replay compaction (228 at 200k, 86 at 390k) and 10k per restart (146) are charged at 5. This costs 25.1M, 9.5M and 7.3M units.

**How the saving shrinks** (restart above 200k):
- 55.2% of input tokens becomes 51.2% under price weighting, because summaries and new growth are written at 2.0 while kept context costs only 0.1.
- It becomes 48.9% once the untouched sub-agents (4.4% of input-side money) are included.
- Output, which the levers leave unchanged, divides by 1.096–1.131 (×0.91–0.88): 44.6 / 43.2%.
- The summary output costs another 0.8 points.
- The ceiling levers lose about the same share: 14–18 points at 200k, about 9 at 390k.
- The A4 charged-restart range (12–37% of main cost) becomes about 10–32% of total money.

**Ordering.** Ranked by money, the order of the four levers is the same as by input tokens: ceiling 200k > restart above 200k > ceiling 390k > floor. This holds under every variant above: scaled or unscaled, R = 0 or D2, low or high output, with or without the summary output.
- The gap between ceiling 200k and restart narrows from 10.5 points to about 7 points (5–6 after summary output).
- The one change in standing is the floor. In tokens it is about 0 (0.0008%; 2.6% counting the steps spent on duplicates and errors; 1.45% after cycle B7's correction). In money it is about 8%, the size of the token savings of the small levers in synthesis §2 (loops 1.4%, tool-result cap 4.4%, dropping never-used content 5.6%), which were not priced here.

## 4. Sanity checks
- **Shares.** Every price-share row sums to 100.00, per session and pooled.
- **Input-side total.** It is 836,245,393.6 units, equal to floor-t1.json's `price_total_units` to the unit.
- **Floor.**
  - W6 premium recomputed from the per-call records: 74,481,381.3. The published value is identical.
  - Floor = 74,593,081.3 / 836,245,393.6 = **8.92%**, reproduced exactly.
  - Including output it is 8.86% (recorded output), 8.14% (low estimate) or 7.89% (high estimate). The published figure excludes output and sub-agent output: the difference is only the denominator.
- **Replays.** The restart replay reproduces `whatif.restart` input and restart counts exactly in every session. With no policy, the price replay equals B4 `curve.replay_one`.
  - The model's no-policy main cost is 724.3M against 799.5M actual. The 75.2M gap is essentially the W6 cache-miss premium (74.5M), which the replay does not model.
  - That gap is the difference between the scaled and unscaled columns.

## 5. Caveats
- **Output estimates.** All output outside S01's main session is estimated. The estimates transfer S01's relation between output and visible content plus thinking signature, assuming that signature length tracks thinking tokens linearly in every model version. The band (1.5×) covers the θ range and the growth-ratio method, not a model change. S01's own main-session output share (15.5%, real) is above the estimate for most sessions because S01 has the most thinking per call.
- **Output price.** Thinking tokens are billed as output. The ratio of 5 assumes the list price ratio of one model family. A different ratio scales the output share roughly in proportion.
- **Lever savings are modelled.**
  - They use B4's price rule, with no cache-prefix breaks and no idle-expiry misses. The scaled and unscaled columns bracket how misses respond.
  - Summary quality, induced re-reads beyond R, and any output change caused by the levers (for example, re-deriving lost context) are not modelled. Output is held constant apart from the summary cost.
- **Carried split.** It uses the B definition, which includes invisible carried content and treats a post-compaction summary as carried. The prefix-order assignment of reads to base, carried and current assumes the cache hit is always a prefix, which holds for prompt caching.

## Findings
1. Money is re-reading. Cache reads are 71–74% of total money, 1-hour cache writes 16%, output 9–12% (0.65% as recorded), and uncached input about 0.
2. About 52–54% of all money is re-reading context carried from finished instructions (62–64% with its re-writes after cache expiry). Of the main session's cache-read money, 76% is spent on carried context.
3. Ranking by money changes no ordering. Ceiling 200k (50–52% of total money) > restart above 200k (43–45%) > ceiling 390k (33–35%) > floor (7.9–8.1%). Every saving shrinks by about a fifth: price weighting −4 to −6 points, untouched sub-agents −2, output dilution −4 to −6, summary output −1 to −3.
4. The floor is the lever whose standing depends most on the unit: 0.0008% of tokens but about 8% of money. The published 8.92% is reproduced exactly; including output lowers it to 7.9–8.1%.
5. Output is the part the headline unit and every lever miss: 8–11% of main money and 19–25% of sub-agent money. It is unmeasurable from event logs because 93–100% of recorded counts are stream-start placeholders.
