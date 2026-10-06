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
| **Carry a pointer instead of what the agent wrote** | **about 20%** (10.5% file bodies only) | the agent re-reads when it needs it | no | harness / agent convention | A2 |
| **New session above 200k tokens at an instruction boundary** | **58.5%** | a 10k summary is enough | no | the user, today | B |
| New session every 3 / 10 instructions | 57.9% / 30.8% | same | no | the user, today | B |
| Compact at half the usual ceiling (about 390k instead of 780k) | 39% of input, 29% of cost, re-reads included | the more frequent summaries lose nothing needed | no | harness | D2 |
| Compact before leaving (breaks over 1 h) | up to 29% of cost | a 30k summary is enough | no | the user / harness | C |
| Delegate reading to sub-agents (11–50 calls) | 1.4–5.1× cheaper than reading in the main session | the same reads were needed | no | the agent | D |

(Savings are not additive: several levers act on the same context.)

## 3. What follows

1. **Forgetting is a small lever; carrying is the big one.** Content is mostly used again later, but
   between uses it is re-read on every call. That is why dropping dead content saves little and why
   simple "recently used" rules either miss needed content or save little.
2. **The levers that need no foresight act on context size**: start smaller (restart, delegate),
   or carry pointers to what already exists elsewhere (the agent's own writes). The largest of them
   are available to a user today (restart rules) or to a harness (pointers to written content).
3. **Every large saving rests on an untested assumption** — that a summary, a pointer or a
   sub-agent's answer is enough. Phase 3 has to test exactly that, on real tasks with outcomes
   checked by tests.
4. **Two disclosures would remove the largest unknowns**: thinking tokens reported separately in
   usage, and final output tokens in event logs.

## 4. Open in phase 2

- Blind labels: W4, W5, W8 detectors, and whether the "steps spent only on errors" are waste or
  verification.
- n > 1: other people's transcripts through `pxt survey run`.
