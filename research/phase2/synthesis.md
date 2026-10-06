# Phase 2 synthesis: what drives the input, and which levers move it

Status: **draft, 2026-10-06**, from the cycles in `log.md`. Ten Claude Code sessions of one person
(dataset v2, 6.84 billion input tokens). Not a waste judgment: waste is decided only under the
codebook, and the categories that need people wait for the blind labels.

## 1. One mechanism

Every API call re-processes its whole context, so the input of a session is the sum, over its
calls, of the context at each call:

> **input = Σ over calls of context = (number of steps) × (average context)**

Everything measured in phase 2 is a statement about one of the two factors.

- **Steps.** 87% of the variance in an instruction's input is its number of calls (cycle B). The
  costly instructions are long ordinary chains of reading, running and editing (median 75 steps
  against 11), not retry loops: all loops together are about 2% of input and no poll repeated an
  unchanged result (cycle B2). Steps that came back only as duplicates or errors re-read the whole
  context each time (2.6% of input).
- **Context.** It stays near the 780k ceiling because compaction fires only there; a call
  after the third instruction carries about 420k tokens, about 80% of it from instructions already
  finished (cycle B). About 30% of the growth is invisible in the records: mostly the model's own
  thinking, a constant per-call overhead, and images (cycle C2).

Within the context, **the agent's own writing** (file bodies, inline scripts, edits) is the largest
visible item: 22.9% of input, carried long after it was written and read back only about 15% of the
time (cycle A2). Large tool results are not the problem: cost is spread over thousands of mid-size
pieces (cycle A). Compaction fires only near the ceiling (about 783k, down to about 64k): the top
quarter of every cycle takes 35% of all main-session input (cycle D2). The agent re-reads files it
has already read all the time (three reads in four mid-cycle, two in three after a compaction), so content dropped
from the context does come back when needed.

**In money** (cycle C5, list-price ratios, output at 5×): cache reads are 71–74% of all spending,
1-hour cache writes 16%, output an estimated 9–12% (event logs record only placeholders), uncached
input about nothing. **About half of all money (52–54%) re-reads context carried from instructions
already finished**, 62–64% with its re-writes after the cache expired.

**The ceiling sets the average.** Compaction fires only near the ceiling, so a long session's
context runs a sawtooth between about 64k and 783k whatever goes into it. A policy that only slows
the growth (trimming, pointers) mostly delays the next compaction and leaves the average about where
it was: alone, carrying pointers instead of the agent's writes saved nothing (−4%) once compaction
was left to fire at the ceiling (cycle B3). What lowers the average is moving the boundary: a new
session or an earlier compaction. Where the boundary should be has a closed form: in a sawtooth that
grows g tokens a call from P after a compaction, with R tokens of re-reading per compaction, the
input-minimizing ceiling is **C\* = P + √(2g(P + R))**, the economic-order-quantity form; here about
80–90k tokens, 110–160k price-weighted, against 783k today (cycles B4, E6).

## 2. The levers on one scale

Share of main-session input that would not have been processed, with what each lever assumes.
"Foresight" = needs to know what will be needed later.

| Lever | Saving | Assumes | Foresight | Who can pull it | Cycle |
|---|---:|---|---|---|---|
| Drop only content never used again | 5.6% (lexical-v1); about 5.6–13% by the definitions behaviour supports; up to 45% under a time placebo that behaviour does not support | what counts as reuse | yes | — | bound, E3, E5, E8 |
| Fetch content again only when needed (oracle, 1k per fetch) | 41.5% (35–56% across detectors and placebos; 16–28% raw) | perfect foresight | yes | — (upper bound) | bound, E3, E5 |
| Simple recency policy, miss rate < 5% | about 3% | none beyond the replay | no | harness | backtest |
| Cap tool results at 2k / 10k tokens | 4.4% / 0.3% | cut part re-read on reuse | no | harness | A |
| Remove every retry and polling loop | about 1.4% (0.3–2.1%) | loops were avoidable | no | agent | B2 |
| Carry a pointer instead of what the agent wrote | about 20% if compactions stayed where they were; **about 0 (−4%) alone** when compaction fires at the ceiling; negative in cost (re-fetched content is written at 2×) | the agent re-reads when it needs it | no | harness / agent convention | A2, B3 |
| **New session above 200k tokens at an instruction boundary** | **55.2%** if a 10k summary is enough; 52–55% (47–50% of cost) with the re-reads observed after real compactions; 43% (31%) at the worst plausible re-read rate (4–19× the observed); 52–53% (47–48%) with a median real cold start charged to every restart, 41% at the 90th percentile | that each restart loses nothing the re-reads do not restore | no | the user, today | B, B3, A4, A5, B5 |
| New session every 3 / 10 instructions | 55.1% / 23.0% | same | no | the user, today | B |
| Compact at half the usual ceiling (about 390k instead of 780k) | 39–44% of input (29% of cost with the observed re-reads) | the more frequent summaries lose nothing needed | no | harness | D2, B3 |
| **Bundle: new session above 200k + compaction at 390k** | **57.5% of input, 52.6% of cost** | both summary assumptions | no | user + harness | B3 |
| **Compaction ceiling at 150–200k instead of 783k** | **67–73% of input** (about 61–65% of input-side cost) | more frequent summaries lose nothing needed | no | harness (one setting) | B4, E6 |
| Compact before leaving (breaks over 1 h) | up to 29% of cost | a 30k summary is enough | no | the user / harness | C |
| Delegate reading to sub-agents (11–50 calls) | 1.4–5.1× cheaper than reading in the main session | the same reads were needed | no | the agent | D |

In money (output included, cycle C5) every saving shrinks by about a fifth and the order stays the
same: ceiling 200k 50–52%, restart above 200k 43–45%, ceiling 390k 33–35% (computed before the E6
correction, which raises the ceiling rows by about a point). Only the floor changes standing: about
0 in tokens, about 8% of money.

(Savings are not additive: several levers act on the same context. In the full bundle the restart
rule does almost all the work; an earlier compaction adds 1.6 points and pointers 0.5, cycle B3.)

Resampling the ten sessions (cycle E4) moves the ceiling and paging rows by about ±1–2 points
and the restart rows by 3–5 (90% intervals: restart above 200k 49–60%, ceiling 200k 65–68% after the E6
correction, oracle 40–43%). Every ordering in this table holds in at least 97% of resamples, except two: restart above
200k and a new session every 3 instructions are tied (50%), and "compaction adds under 5 points on
top of restart" holds in 89%.

## 3. In units of work

One commit cost a median of 7.5 million input tokens processed (pooled 9.9M; about 0.9M
cache-weighted), and one token written to disk about 2,500. Large sessions pay 1.5× more per commit
and 2.9× more per written token than small ones at the same number of calls per commit: the
difference is context weight (cycle C3). The pattern shows no trend over the eight weeks measured
and is the same on the two main model versions, though model, date and tooling cannot be separated
at n = 10 (cycle D3).

## 4. What follows

1. **The total opportunity is robust; how it splits is not.** With perfect foresight about 35–56%
   of input need not have been processed, whatever counts as reuse (six detectors, cycle E3; 41.5%
   by lexical-v1 and 44–56% under the placebo corrections of cycle E5). How much of that is content never needed again (forgetting) and
   how much content needed later but carried in between (paging) depends on the detector. By
   lexical-v1, forgetting is 5.6% and paging adds 36 points. Lexical reuse turns out to be symmetric
   in time: calls before a segment existed share its words as often as calls after it, so a raw link
   measures topic as well as need. Corrected against that placebo, forgetting rises to 33–45%; corrected
   only against other sessions' vocabulary, to 12–13% (cycle E5). Behaviour decides between them: at the
   34 real compactions, the files the agent went back for are predicted by plain lexical reuse
   (AUC 0.57–0.61) and the cross-session corrections, while the time-placebo corrections do no better
   than chance (cycle E8). So forgetting is most likely 5.6–13%, and **carrying, not forgetting, is the
   larger lever**. The blind labels check this once more (a secondary analysis is pre-registered). Simple "recently used" rules either miss needed content or
   save little.
2. **The levers that need no foresight move the boundary**: start a new session, compact earlier,
   or delegate to a sub-agent with its own small context. Trimming what goes in helps only once the
   boundary has moved; under today's ceiling it mostly postpones the next compaction. The largest
   lever is available to a user today (a restart rule).
3. **What a summary must carry is small by behaviour.** Lexical reuse makes the next instruction
   look as if it needed most of the old context (cycle A4), but an unrelated window scores 72–99% of
   the same "demand": it measures shared vocabulary. After the 34 real compactions the agent
   re-obtained 10–21k distinct tokens, beside about 22k restored by the harness, and no damage was
   visible in error rates or step counts (cycle A5). The cost of re-reading therefore does not limit
   the restart lever; whether quality survives 150 restarts instead of 34 compactions is the open part.
4. **Every large saving rests on an untested assumption** — that a summary, a pointer or a
   sub-agent's answer is enough. Phase 3 has to test exactly that, on real tasks with outcomes
   checked by tests.
5. **Two disclosures would remove the largest unknowns**: thinking tokens reported separately in
   usage, and final output tokens in event logs.

## 5. Open in phase 2

- Blind labels: W4, W5, W8 detectors, and whether the "steps spent only on errors" are waste or
  verification.
- n > 1: other people's transcripts through `pxt survey run`.
