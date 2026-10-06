> Working memo from cycle C7 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# C7: was the 1-hour cache the right choice, and what would an ideal TTL policy save?

Numbers only; computed from the private transcripts at the dataset-v2 snapshots (lines_v2).
Scripts and their outputs are kept with the analysis files.

## Method
- **Calls.** Usage is de-duplicated per message id. The main session (16,181 calls) and each sub-agent (2,362 calls in
  their own contexts) are kept separate. For each call: uncached input i, cache read r, cache write w
  (1h/5m split from `usage.cache_creation`), context = i + r + w, start time t (first line of the
  message), and gap g = time since the previous call of the same context.
  - The main sessions wrote only 1-hour cache (74.5M tokens) and the sub-agents only 5-minute cache.
- **Prices.** Read 0.1, 5-minute write 1.25, 1-hour write 2.0, uncached 1 (RULES). Total money is from C5:
  916.5M units with the low output estimate and 945.9M with the high one.
- **TTL semantics.** I used the provider's semantics as understood (not re-checked against current documentation; the read-refresh part is confirmed by the data): a read refreshes the entry's timer on either TTL, and the
  lifetime runs from the start of the request. The data agrees:
  - **Reads refresh the timer.** 11,388 main-session reads (of 16,119) read tokens last written more than 1 h earlier and still hit, all but 29 with the
    previous use under 1 h ago. Among sub-agents, 1,109 reads hit tokens written more than 5 min earlier.
    Without refresh, the lifetime would run from the write.
  - **Survival by gap.** The cache survived (re-write ≤ 2%) in:

    | context | gap < 5 min | gap 5–60 min | gap > 1 h |
    |---|---:|---:|---:|
    | main (1-hour TTL) | 15,638 of 15,650 | 395 of 409 | 0 of 64 |
    | sub-agents (5-minute TTL) | 2,266 of 2,271 | 2 of 15 | — |

    Both tiers expire as labelled.
- **Replay (anchored).** The call sequence, contexts, uncached input and every prefix change are held fixed.
  - For each call, U = the prefix it could read if the cache were alive:
    - the observed read when the gap is within the observed TTL;
    - the observed read plus the W6 miss when the gap is longer, because that re-write was an expiry;
    - the observed read when the context shrank.
  - A call reads the longest live entry, clipped to U. If no entry is live, it reads nothing, or the observed read when the observed chain had also expired (an external read). It writes the rest at the price of the tier the policy chooses for that call.
- **Two semantics for mixed TTLs.** These matter only for policies that mix 5-minute and 1-hour writes.
  - **"entry"** follows the mixed-TTL billing as understood (not re-checked). An entry at a breakpoint covers its whole prefix, and a 1h write is
    charged only on the tokens after the longest hit. A small 1h write at the tail therefore protects the
    whole context.
  - **"segment"** is a pessimistic bound. Each written span keeps the TTL it was written with, and reads refresh it but
    never upgrade it.
  - The data cannot separate the two, because no call mixes tiers.
- **Pings (keep-alive).** A ping is a `max_tokens: 0` request that re-sends the previous prompt. It costs a read of the whole
  previous context at 0.1, has no output, and refreshes the timer. An "upgrade" ping also carries the
  previous response under a 1h breakpoint, which gives the entry a 1-hour life (entry semantics only).
  - Ping intervals are 4.5 min on 5-minute entries and 55 min on 1-hour entries.
  - Pings after the last call of a context, up to the horizon, are charged as wasted.

## 1. Reproduction of the observed price
| replay | main input-side units | vs observed |
|---|---:|---:|
| observed (usage) | 799.51M | — |
| anchored all-1h replay | 799.51M | **0.0000%** |
| anchored, without letting entries cover reads beyond the previous logged prompt | 800.42M | +0.11% |
| structural (read = previous prompt if gap ≤ 1 h; nothing after > 1 h) | 786.5M | −1.63% |

The structural gap decomposes as follows:
- **−1.97%:** 30 calls that re-wrote within 1 h because the prefix changed (W6 gap ≤ 1 h).
- **+0.11%:** 657 calls that read more than the previous logged prompt. Some unlogged request on the same prefix extended the cache within the gap.
- **+0.23%:** 29 calls after a gap of more than 1 h that still read part of the prefix from elsewhere.
- **Model switches: 0. Compactions** are anchored, so they leave no gap.

Sub-agents: the anchored 5-minute replay equals the observed 36.74M exactly.

## 2. Gap distribution (gap before a call, since the previous call of the same context)
| context | gap | calls | share of calls | share weighted by context | after a user instruction |
|---|---|---:|---:|---:|---:|
| main | < 5 min | 15,682 | 97.0% | 96.5% | 2% |
| main | 5–60 min | 422 | 2.6% | 3.0% | 52% |
| main | > 60 min | 67 | 0.4% | 0.5% | 94% |
| sub-agents | < 5 min | 2,271 | 99.3% | 99.4% | — |
| sub-agents | 5–60 min | 15 | 0.7% | 0.6% | — |

- Per session, the context-weighted share of 5–60 min gaps is 1.3–4.2%, and of gaps over 60 min 0–1.4%.
- About half of the 5–60 min gaps are inside an agent turn: a long tool run, not the user.

## 3. Policies (main session, input-side money relative to observed all-1h; − = cheaper)
| policy | entry semantics | segment semantics | pings (cost) |
|---|---:|---:|---|
| (a) all 1h (observed) | 0 | 0 | — |
| **(b) all 5m** | **+19.77%** | +19.77% | — |
| **(c) oracle per write (1h iff the next gap is 5–60 min)** | **−6.71%** | **−1.63%** | — |
| (c+) oracle per gap: let it expire / 1h tail / 5m pings / upgrade ping / hourly pings | −10.12% | — | 173 (8.7M) |
| (d) 1h only when the context is > 50k / 100k / 200k / 300k / 500k | −0.02 / −0.24 / +0.15 / +1.16 / +5.73% | +0.19 / +1.38 / +2.22 / +3.76 / +8.71% | — |
| (d) 1h unless this call writes > 20k (cold start, re-write after expiry or compaction: 5m) | −4.00% | +21.92% | — |
| (d') the same + hourly pings while idle ≤ 8 h | −6.66% | — | — |
| (e) 5m + keep-alive pings every 4.5 min, idle ≤ 15 / 30 / 60 / 120 min | +4.65 / +4.67 / +5.76 / +7.75% | — | 1,031–2,862 |
| (f) 5m + one 1h-upgrade ping at 4.5 min idle | −4.53% | n/a | 520 (24.6M) |
| (f) the same + hourly pings while idle ≤ 2 / 4 / 8 h | −5.98 / −6.19 / −6.16% | n/a | 639–803 |
| **(g) 1h + hourly keep-alive pings while idle ≤ 2 / 4 / 8 / 24 h** | **−3.88 / −4.49 / −4.81 / −3.84%** | same (no mixing) | 122–539 (6–26M) |

**Per session** (% vs all-1h): b = all 5m, c = oracle (entry), c' = oracle (segment), d = write rule (entry), f = upgrade ping with idle ≤ 4 h, g = 1h with hourly pings to 8 h.

| session | b | c | c' | d | f | g |
|---|---:|---:|---:|---:|---:|---:|
| S01 | +25.5 | −5.7 | −0.5 | −2.0 | −1.5 | +1.5 |
| S02 | +30.7 | −7.0 | −0.9 | −4.4 | −5.3 | −7.5 |
| S03 | +33.2 | −6.1 | −1.0 | −3.0 | −6.0 | −6.4 |
| S04 | **−14.5** | −20.2 | −12.5 | −17.1 | −13.4 | +8.7 |
| S05 | +13.5 | −6.1 | −2.0 | −3.7 | −6.1 | −4.4 |
| S06 | +18.5 | −8.4 | −1.1 | −5.3 | −4.2 | +2.0 |
| S07 | −0.1 | −10.9 | −4.3 | −3.1 | −2.3 | +12.3 |
| S08 | +3.3 | −16.8 | −8.5 | −13.2 | −6.5 | +13.0 |
| S09 | +14.5 | −6.4 | −1.4 | −4.0 | −6.3 | −5.0 |
| S10 | +3.6 | −7.5 | −2.8 | −5.2 | −7.5 | −3.7 |
| pooled | +19.77 | −6.71 | −1.63 | −4.00 | −6.19 | −4.81 |

**Sub-agents** (observed 5m = 36.74M):
- All 1h: +14.6%.
- Oracle: −2.5% (0.93M units, 0.10% of total money).
- Keep-alive pings: +12.7%.

5 minutes was the right choice for them.

## 4. The 1-hour premium: what it bought
The premium is 0.75 × the 1h-written tokens = 55.87M units: 7.0% of main input-side money, 5.9–6.1% of total money.

| premium paid on writes whose next gap is | units | share |
|---|---:|---:|
| < 5 min | 52.17M | 93.4% |
| 5–60 min (the writes that protected a surviving gap) | 2.26M | **4.0%** |
| > 60 min (expired anyway) | 0.80M | 1.4% |
| last call | 0.65M | 1.2% |

- 61.5% of the premium was paid on writes over 50k tokens: cold starts, re-writes after expiry, and the first writes after compaction.
- Survival across 5–60 min gaps saved 213.9M units of re-writes (U × 1.15). That is 3.8× the whole premium, so the blanket 1h policy
  pays for itself several times over.
- **Share of the premium that bought that survival:**
  - entry semantics: 4% (only the tail write before the gap needs 1h);
  - segment semantics: about 77% (the oracle can drop only 13.0M of the 55.9M).

## 5. Break-evens
- **1h tail on a call** (entry semantics). It pays when p(next gap 5–60 min) × 1.15 × context > 0.75 × write. At the pooled
  p = 2.6%, that means context / write > 25.
  - 97.4% of calls pass, but they carry only 33.6% of the premium.
  - The remaining 2.6% are the large writes, where 1h does not pay in expectation. They should be written at 5m, and the next small write re-establishes 1h cover.
- **5-minute keep-alive.** A ping costs 0.1 × context every 4.5 min, against 1.15 × context to re-write. It breaks even
  up to about 54 min of idle, but it never beats a 1h tail while the write is under 1/7.5 of the context. Empirically it is worse than all-1h at every horizon.
- **Upgrade ping** (5m writes, one ping at 4.5 min idle that turns the entry to 1h). It costs 0.1 × context once per
  idle period over 4.5 min. Measured, it beats all-1h by 4.5%.
- **Hourly keep-alive on 1h.** A ping at 0.1 × context against a re-write at 1.9 × context allows up to 19 pings, about 18 h, if the return is
  certain. Pings on sessions that never return put the measured optimum at an idle horizon of 4–8 h
  (−4.5 to −4.8%); at 24 h the saving falls back to −3.8%.
- **Context threshold.** It does not help (best −0.24% at 100k). The premium scales with the written tokens,
  not with the context, so the right cut is on write size, not context size.

## 6. In total-money terms and next to the other levers
| lever (synthesis §2 / C5) | % of total money (low / high output) |
|---|---:|
| Switching to all-5m (what 1h avoided) | **−17.2 / −16.7** (cost increase) |
| Oracle TTL per write (entry / segment) | 5.9 / 5.7 · 1.4 / 1.4 |
| Oracle TTL + pings | 8.8 / 8.6 |
| **1h + hourly keep-alive to 8 h (robust to semantics)** | **4.2 / 4.1** |
| 5m + 1h-upgrade ping (+hourly to 4 h) (entry only) | 5.4 / 5.2 |
| 1h except large writes, + hourly pings (entry only) | 5.8 / 5.6 |
| Ceiling 200k / restart above 200k / ceiling 390k (C5) | 50–52 / 43–45 / 33–35 |
| Floor W1+W2+W6 premium (C5) | 7.9–8.1 |
| Token levers (not priced): drop never-used 5.6%, cap tool results 4.4%, loops 1.4% (of input) | — |

- The TTL lever is of the same size as the small behaviour levers and the floor, and needs no change in behaviour.
  It is about an order of magnitude smaller than moving the compaction boundary.
- **Overlap.**
  - The keep-alive part removes the W6 "after 1 h" re-writes that make up most of the floor's W6 premium.
  - C's 24-hour-cache upper bound (9.0%) is the same mechanism without the ping cost.
  - Under a 200k ceiling, contexts shrink, and both the re-write cost and the ping cost shrink with them roughly in proportion.

## Caveats
- **Mixed-TTL semantics decide the gap between "ideal" and "observed".** Under segment semantics, the only clear gain left is the
  hourly keep-alive (−4.8%); the oracle gains only 1.6%, and the write-size rule becomes worse than all-5m (+21.9%). The entry semantics follow
  the mixed-TTL billing as understood, but no call in this data mixes tiers, so it is untested here.
- **Timestamps.** The time is the first line of each message, which approximates the request start; generation time counts against
  the lifetime.
  - With an effective 5-minute lifetime of 4 / 6 min: all-5m is +23.7 / +15.5%, the oracle −5.7 / −6.7%, the upgrade ping −5.6 / −6.6%.
  - The 1h results do not move.
- **Read price.** The project prices cache reads at 0.1 of input. As a sensitivity (not checked against a current price list), at 0.05:
  - all-5m: +35.3%;
  - oracle: −11.3% (entry) / −2.7% (segment);
  - upgrade ping: −14.3%;
  - hourly keep-alive: −9.9%.

  The direction holds and the lever doubles.
- **Prefix-change misses** (30 calls within 1 h) are held fixed: no TTL fixes them.
- **Under shorter TTLs**, a policy-induced miss is assumed to read nothing from elsewhere. This slightly overstates the 5m costs; after real expiries, 3–4% of the context was still read from elsewhere.
- **Pings** assume `max_tokens: 0` requests with the same thinking/effort settings, so they hit. No output is billed.
  Pings during idle after the snapshot end are charged, which is conservative. Ping traffic and its rate-limit effect are not modelled.
- **Data.** Ten sessions of one person. S01 was cut at 400 calls, and S04, S07 and S08 are small and dominated by a few events (S04 is
  cheaper under all-5m). Output is unchanged by every policy.

## Findings
1. The 1-hour TTL was the right blanket choice for this work rhythm. All-5-minute writes would have cost 19.8% more main input
   money (about 17% of total money): survival across 5–60 min gaps (3% of context-weighted calls, half of them inside agent
   turns) avoided 214M units of re-writes for a 56M premium.
2. The premium is mostly paid where it buys nothing. 93% of it went on writes followed by a gap under 5 min, and 62% on large
   writes (cold starts, re-writes after expiry, post-compaction). Under the entry reading of mixed-TTL billing (assumed; no call in the data mixes tiers), only the tail write before a gap needs 1h. An oracle per write
   then saves 6.7% of main input money (5.7–5.9% of total); under the pessimistic per-span semantics, 1.6%.
3. Adding keep-alive pings, the ideal policy saves 10.1% of main input money (8.6–8.8% of total money). Realistic rules get most of it:
   - hourly keep-alive on 1h up to 8 h idle: 4.8% (4.1–4.2% of total, the only gain robust to TTL semantics);
   - 5m plus a 1h-upgrade ping at 4.5 min idle: 6.2%;
   - 1h except large writes, plus hourly pings: 6.7%.
4. A context-size threshold does not help (best −0.2%), and 5-minute keep-alive pings are worse than 1h (+4.7% or more). Sub-agents
   were right on 5 minutes: 1h would cost them +14.6%.
5. As a lever, an ideal TTL policy is worth about 4–6% of total money (up to 9% with oracle pings). That is the size of the small
   levers and the floor, and needs no change in behaviour, but it is an order of magnitude below moving the compaction ceiling.
