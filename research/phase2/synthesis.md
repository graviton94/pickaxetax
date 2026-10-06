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
has already read all the time (about three reads in four, compaction or not), so content dropped
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
90–100k tokens, 120–170k price-weighted, against 783k today (cycle B4).

## 2. The levers on one scale

Share of main-session input that would not have been processed, with what each lever assumes.
"Foresight" = needs to know what will be needed later.

| Lever | Saving | Assumes | Foresight | Who can pull it | Cycle |
|---|---:|---|---|---|---|
| Drop only content never used again | 5.6% (3.5–24.7%) | lexical reuse detection | yes | — | bound |
| Fetch content again only when needed (oracle, 1k per fetch) | 41.5% (35–54%; 16–28% raw) | lexical detection, perfect foresight | yes | — (upper bound) | bound |
| Simple recency policy, miss rate < 5% | about 3% | none beyond the replay | no | harness | backtest |
| Cap tool results at 2k / 10k tokens | 4.4% / 0.3% | cut part re-read on reuse | no | harness | A |
| Remove every retry and polling loop | about 1.4% (0.3–2.1%) | loops were avoidable | no | agent | B2 |
| Carry a pointer instead of what the agent wrote | about 20% if compactions stayed where they were; **about 0 (−4%) alone** when compaction fires at the ceiling; negative in cost (re-fetched content is written at 2×) | the agent re-reads when it needs it | no | harness / agent convention | A2, B3 |
| **New session above 200k tokens at an instruction boundary** | **55.2%** if a 10k summary is enough; 27–46% (12–37% of cost) if every lexically reused earlier token had to be re-read | how much of the old context the next task needs | no | the user, today | B, B3, A4 |
| New session every 3 / 10 instructions | 55.1% / 22.3% | same | no | the user, today | B |
| Compact at half the usual ceiling (about 390k instead of 780k) | 39–43% of input (29% of cost with the observed re-reads) | the more frequent summaries lose nothing needed | no | harness | D2, B3 |
| **Bundle: new session above 200k + compaction at 390k** | **57.5% of input, 52.6% of cost** | both summary assumptions | no | user + harness | B3 |
| **Compaction ceiling at 150–200k instead of 783k** | **66–72% of input** (about 56–64% of cost) | more frequent summaries lose nothing needed | no | harness (one setting) | B4 |
| Compact before leaving (breaks over 1 h) | up to 29% of cost | a 30k summary is enough | no | the user / harness | C |
| Delegate reading to sub-agents (11–50 calls) | 1.4–5.1× cheaper than reading in the main session | the same reads were needed | no | the agent | D |

In money (output included, cycle C5) every saving shrinks by about a fifth and the order stays the
same: ceiling 200k 50–52%, restart above 200k 43–45%, ceiling 390k 33–35%. Only the floor changes
standing: about 0 in tokens, about 8% of money.

(Savings are not additive: several levers act on the same context. In the full bundle the restart
rule does almost all the work; an earlier compaction adds 1.6 points and pointers 0.5, cycle B3.)

Resampling the ten sessions (cycle E4) moves the ceiling and paging rows by about ±1–2 points
and the restart rows by 3–5 (90% intervals: restart above 200k 49–60%, ceiling 200k 64–67%, oracle
40–43%). Every ordering in this table holds in at least 97% of resamples, except two: restart above
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

1. **Carrying is the big lever; forgetting is smaller and less certain.** Content is mostly used again
   later, but between uses it is re-read on every call. The paging opportunity is robust to how
   reuse is detected (35–54% across six detectors, cycle E3); how little forgetting alone saves is
   not (3–19% across lexical detectors), which the blind labels have to settle. Simple "recently
   used" rules either miss needed content or save little.
2. **The levers that need no foresight move the boundary**: start a new session, compact earlier,
   or delegate to a sub-agent with its own small context. Trimming what goes in helps only once the
   boundary has moved; under today's ceiling it mostly postpones the next compaction. The largest
   lever is available to a user today (a restart rule).
3. **Every large saving rests on an untested assumption** — that a summary, a pointer or a
   sub-agent's answer is enough. Phase 3 has to test exactly that, on real tasks with outcomes
   checked by tests.
4. **Two disclosures would remove the largest unknowns**: thinking tokens reported separately in
   usage, and final output tokens in event logs.

## 5. Open in phase 2

- Blind labels: W4, W5, W8 detectors, and whether the "steps spent only on errors" are waste or
  verification.
- n > 1: other people's transcripts through `pxt survey run`.
