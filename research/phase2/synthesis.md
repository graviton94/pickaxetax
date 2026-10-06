# Phase 2 synthesis: what drives the input, and which levers move it

Status: **draft v2, 2026-10-06**, from the cycles in `log.md` (A–A6, B–B6, C–C8, D–D7, E1–E10).
Ten Claude Code sessions of one person (dataset v2, 6.84 billion input tokens). This is not a waste
judgment. Waste is decided only under the codebook, and the categories that need people wait for
the blind labels. Threats to validity: `validity.md`. Experiments that follow: `phase3-experiments.md`.

## 1. One mechanism

Every API call re-processes its whole context. The input of a session is therefore the sum, over
its calls, of the context at each call:

> **input = Σ over calls of context = (number of steps) × (average context)**

Everything measured in phase 2 is a statement about one of the two factors.

- **Steps.** 87% of the variance in an instruction's input is its number of calls (cycle B).
  - The costly instructions are long, ordinary chains of reading, running and editing (median 75
    steps against 11), not retry loops. All loops together are about 2% of input, and no poll
    repeated an unchanged result (cycle B2).
  - Steps that came back only as duplicates or errors re-read the whole context each time (2.6% of
    input).
- **Context.** It stays near the ceiling (about 783k) because compaction fires only there.
  - A call after the third instruction carries about 420k tokens, about 80% of it from instructions
    already finished (cycle B).
  - The agent's own writing (file bodies, inline scripts, edits) is the largest visible item: 22.9%
    of input. It is carried long after it was written and read back only about 15% of the time
    (cycle A2).
  - Large tool results are not the problem: cost is spread over thousands of mid-size pieces
    (cycle A).
  - About 30% of the growth is invisible in the records: mostly the model's own thinking, a constant
    per-call overhead, and images (cycle C2).

**The ceiling sets the average.** A long session's context runs a sawtooth between about 64k and
783k, whatever goes into it. The top quarter of every cycle takes 35% of all main-session input
(cycle D2).
- A policy that only slows the growth (trimming, pointers) mostly delays the next compaction and
  leaves the average where it was. Alone, carrying pointers instead of the agent's writes saved
  nothing (−4%) once compaction was left to fire at the ceiling (cycle B3).
- What lowers the average is moving the boundary: a new session, or an earlier compaction.
- Where the boundary should be has a closed form. In a sawtooth that grows g tokens a call from P
  after a compaction, with R tokens of re-reading per compaction, the input-minimizing ceiling is
  **C\* = P + √(2g(P + R))**, the economic-order-quantity form. Here that is about 80–90k tokens
  (110–160k price-weighted), against 783k today (cycles B4, E6).

## 2. In money and in time

**Money** (list-price ratios, output at 5×; cycle C5):
- Cache reads are 71–74% of all spending, 1-hour cache writes 16%, and output an estimated 9–12%
  (event logs record only placeholders). Uncached input is about nothing.
- **About half of all money (52–54%) re-reads context carried from instructions already finished**,
  62–64% with its re-writes after the cache expired.
- The 1-hour cache lifetime fitted this person's rhythm: all-5-minute caching would have cost 17%
  more (cycle C7).
- These numbers rest on fixed price ratios (cache read 0.1, writes 1.25 / 2.0, output 5). Across
  48 settings (24 ratio sets × 2 output estimates, cycle C8) the order of the levers and the 1-hour choice never change. The
  "half of all money" reading holds only if a cache read costs at least about 0.05–0.09 of an input
  token; counting the re-writes, it is 56–69% in every setting. The floor's cost share moves most
  (4.7–15.4%).

**Time** (cycle C6):
- Model latency grows with context only slowly: about 0.2–0.4 s per 100k tokens, before the first
  token. Context is 6–11% of the 61 h of model time.
- A compaction takes about 130 s.
- So the levers pay in tokens and money, not in model time, except restarts (below).

## 3. The levers on one scale

Share of main-session input that would not have been processed, and what each lever assumes.
"Foresight" means the lever needs to know what will be needed later.

| Lever | Saving | Assumes | Foresight | Who can pull it | Cycle |
|---|---:|---|---|---|---|
| Fetch content again only when needed (oracle, 1k per fetch) | 41.5% (35–56% across detectors and placebos; 16–28% raw) | perfect foresight | yes | — (upper bound) | bound, E3, E5 |
| Drop only content never used again | 5.6% by lexical-v1; **about 5.6–13%** by the definitions behaviour supports | what counts as reuse | yes | — | bound, E5, E8 |
| Simple recency policy, miss rate < 5% | about 3% | none beyond the replay | no | harness | backtest |
| Mechanical floor (duplicates, errors, cache churn) | 0.0008% of tokens; **8.92% of input-side cost** | codebook v1 | no | user / harness | floor |
| Cap tool results at 2k / 10k tokens | 4.4% / 0.3% | the cut part is re-read on reuse | no | harness | A |
| Remove every retry and polling loop | about 1.4% (0.3–2.1%) | the loops were avoidable | no | agent | B2 |
| Carry a pointer instead of what the agent wrote | about 20% if compactions stayed where they were; **about 0 (−4%) alone** under today's ceiling; negative in cost | the agent re-reads when it needs to | no | harness / agent convention | A2, B3 |
| **New session above 200k tokens at an instruction boundary** | **55.2%** if a 10k summary is enough; **52–53%** (47–48% of cost) with the observed re-reads and a median cold start charged to every restart; 41–43% at pessimistic charges | each restart loses nothing the re-reads do not restore | no | the user, today | B, A4, A5, B5, A6 |
| New session every 3 / 10 instructions | 55.1% / 23.0% | same | no | the user, today | B |
| New session only on returning from a break over 1 h (context above 200k) | 16% of input, 15% of cost on the same basis as the row above (20% counting cache expiry), 48 restarts | same; the return re-writes the whole context anyway | no | the user, today | A6, C |
| Compact before leaving (breaks over 1 h) | up to 29% of cost | a 30k summary is enough | no | the user / harness | C |
| Compact at about 390k instead of 783k | 39–44% of input (34–36% of total money; 29% with D2's gross re-read burden) | the more frequent summaries lose nothing needed | no | harness | D2, B3, E6 |
| **Compaction ceiling at 150–200k** | **67–73% of input** (about 61–65% of input-side cost) | same | no | harness (one setting) | B4, E6 |
| Bundle: new session above 200k + compaction at 390k | 57.5% of input, 52.6% of cost | both summary assumptions | no | user + harness | B3 |
| Cache lifetime chosen per write, with keep-alive requests while idle | 4.1–4.2% of total money for an hourly keep-alive; up to 5–6% (9% with foresight) under the unverified "entry" billing reading; 1.5–11% across price ratios | the harness can choose per write | no | harness | C7 |
| Delegate reading to sub-agents (11–50 calls) | 1.4–5.1× cheaper than reading in the main session | the same reads were needed | no | the agent | D |

**How to read the table.**
- **Savings are not additive.** Several levers act on the same context. In the full bundle the
  restart rule does almost all the work; an earlier compaction adds 1.6 points and pointers 0.5
  (cycle B3).
- **In money** (output included; cycle C5) every saving shrinks by about a fifth and the order stays
  the same: ceiling 200k about 51–53%, restart above 200k 43–45%, ceiling 390k about 34–36%. Only the
  floor changes standing: about 0 in tokens, about 8% of money.
- **In time** (cycle C6), a 200k ceiling would make the sessions slightly slower (+1.9 h): its 178
  extra compactions cost more than the faster calls save, unless a smaller compaction is also faster.
  390k is about neutral. The restart rule saves about 8% of model time if no summary is generated,
  and about none if each restart generates a compaction-length summary.
- **Resampling the ten sessions** (cycle E4) moves the ceiling and paging rows by about ±1–2 points
  and the restart rows by 3–5. The 90% intervals are: restart above 200k 49–60%, ceiling 200k 65–68%,
  oracle 40–43%. Every ordering E4 tested holds in at least 97% of resamples (rows added later, from
  cycles A6, C and C7, were not resampled), with two exceptions:
  restart above 200k and a new session every 3 instructions are tied, and "compaction adds under 5
  points on top of restart" holds in 89%.

## 4. In units of work

- One commit cost a median of 7.5 million input tokens processed (pooled 9.9M; about 0.9M
  cache-weighted), and one token written to disk about 2,500.
- Large sessions pay 1.5× more per commit and 2.9× more per written token than small ones at the
  same number of calls per commit. The difference is context weight (cycle C3).
- The pattern shows no trend over the eight weeks measured and is the same on the two main model
  versions, though model, date and tooling cannot be separated at n = 10 (cycle D3).

## 5. What follows

1. **The total opportunity is robust; how it splits needed checking.** With perfect foresight,
   35–56% of input need not have been processed, whatever counts as reuse (six detectors, cycle E3;
   four placebo corrections, cycle E5).
   - Lexical reuse is symmetric in time: calls before a segment existed share its words as often as
     calls after it. A raw link therefore measures topic as well as need.
   - Corrected against that time placebo, forgetting ("never used again") rises to 33–45%. Corrected
     only against other sessions' vocabulary, it rises to 12–13% (cycle E5).
   - Behaviour decides between them. At the 34 real compactions, plain lexical reuse and the
     cross-session corrections predict which files the agent went back for (AUC 0.57–0.61 and
     0.55–0.60). The
     time-placebo corrections do no better than chance (cycle E8).
   - So forgetting is most likely 5.6–13%, and **carrying, not forgetting, is the larger lever**. The
     blind labels check this once more; a secondary analysis is pre-registered.
2. **The levers that need no foresight move the boundary**: start a new session, compact earlier, or
   delegate to a sub-agent with its own small context.
   - Trimming what goes in helps only once the boundary has moved. Under today's ceiling it mostly
     postpones the next compaction.
   - The largest lever is available to a user today: a restart rule.
3. **What a summary must carry is small, judged by behaviour.**
   - Lexical reuse makes the next instruction look as if it needed most of the old context (cycle
     A4), but an unrelated window scores 72–99% of the same "demand".
   - After the 34 real compactions, the agent re-obtained only 10–21k distinct tokens, beside about
     22k restored by the harness (cycle A5).
   - A new session's cold start costs 20–30k tokens of orientation (cycle B5).
   - No damage was visible in error rates, step counts or failed edits (cycles A5, D5). These proxies
     are blunt: edits fail too rarely (0.75%) to show anything below a threefold rise.
   - The cost of a restart is therefore a few points, not tens.
   - No signal known at the boundary picks safer restart points (cycle A6): not the new prompt's
     overlap with the context, its length, or the break before it. Refusing a boundary only moves the
     restart to the next one.
   - The restart rule cannot be made safer by being selective. It can only be tested.
4. **Every large saving rests on one untested assumption:** that a summary, a pointer or a
   sub-agent's answer is enough. Only quality can still overturn the restart and ceiling levers, and
   the logs cannot measure quality. Phase 3 tests it on tasks with outcome checks.
   - `research/phase3/e2-taskset-v0.md` has a candidate task set for E2: 29 validated tasks from
     this repository's history, in 4 chains of 7 instructions (cycle D6).
   - `research/protocol/e1-before-after.md` pre-registers the user-level before/after experiment.
     One person's before/after can detect only a change to about 0.6× or less (cycle B6).
5. **Three disclosures would remove the largest unknowns**: thinking tokens reported separately in
   usage, final output tokens in event logs, and a usage record for the compaction call.

## 6. Open in phase 2

- Blind labels: the W4, W5 and W8 detectors (with W5's pre-registered secondary analysis), and
  whether "steps spent only on errors" are waste or verification.
- n > 1: other people's transcripts through `pxt survey run`.
