> Working memo from cycle C of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots (B uses only the public `dataset-v2.json`). Scripts are not published because they read the transcripts.

# Question C: idle and return (aggregate numbers only)

## Method
- Scripts: an2.py (final, TTL-aware; an.py is the superseded first pass priced at 1.25 for all writes). Data: lines_v2 sessions S01-S10, main-session assistant calls only, de-duplicated by message.id, in order. Context of a call = input + cache_read + cache_write.
- Gap = timestamp difference between consecutive main calls (timestamps are assistant-line times, so a gap includes generation and tool time, and is approximate to seconds-to-minutes).
- Prices (relative to uncached input): read 0.1; cache write per call from usage.cache_creation: 1-hour 2.0, 5-minute 1.25. All main-session writes in this data are 1-hour (74.5M tokens 1h, 0 5m, in every session); sub-agents are excluded. "Total input-side cost" = sum over main calls of input + 0.1 read + TTL write price.
- Re-write (W6 convention from judge.py): next call context >= previous, and min(cache_write, prev_ctx - cache_read) > 2% of prev context. Cause: model switch, gap <= 1 h (prefix changed or cache lost within the lifetime), gap > 1 h (expiry). Excess cost = tokens x (write price - read price).
- Returns = calls after a gap > 5 min.
- 3a (replaced after the coordinator correction): share of re-writes within vs after the 1-hour lifetime.
- 3b: re-writes with no model switch and gap < 24 h become reads. Upper bound: a real 24 h tier would charge more per write than 2.0.
- 3c: at each return after > 1 h whose (counterfactual) context exceeds base + 30,000, the previous context is replaced by base (first-call context of the session, median 50k) + 30,000 summary. All later calls carry (context - (prev ctx - base - 30,000)) until the next actual context drop (>2% shrink), at which the offset resets. At the return call the removed tokens come out of the cache-write part (the summary and base are written once at 2.0); at later calls they come out of the cache-read part first. A compaction call that re-reads the pre-leave context warm (0.1) is charged as extra cost ("net"). Output tokens of the summary are not counted (input-side only).

## Results
```
POOLED: 16181 main calls; price-weighted input cost 7.995e+08 units (1h write 2.0, 5m 1.25, read 0.1); 6,579,410,935 tokens processed; cache-write tokens 1h 74,491,609 / 5m 0
| gap bucket | calls | share | mean cache_read share | mean cache_write share | cache survived (non-shrinking) |
|---|---|---|---|---|---|
| <30s | 12741 | 78.8% | 99.4% | 0.6% | 100% |
| 30s-5m | 2941 | 18.2% | 98.7% | 1.3% | 100% |
| 5-60m | 422 | 2.6% | 94.2% | 5.8% | 97% |
| 1-8h | 58 | 0.4% | 3.3% | 96.7% | 0% |
| >8h | 9 | 0.1% | 3.9% | 96.1% | 0% |

Returns (gap>5m): 489; ctx median 488,757, p90 724,523; cache-write tokens 43,228,199; return-call cost 13.2% of input cost, cache-write part 10.8%

Re-writes (next call re-wrote >2% of previous context; not shrinking), by cause:
- model_switch: 0 (0%), 0 tokens (0%), excess-over-read cost 0.00% of input cost
- within_1h: 26 (29%), 8,296,808 tokens (21%), excess-over-read cost 1.97% of input cost
- after_1h: 64 (71%), 30,903,919 tokens (79%), excess-over-read cost 7.34% of input cost
- all re-writes: 90, 39,200,727 tokens, excess cost 9.32% of input cost
3b 24h cache (no model switch, gap<24h): 37,987,886 tokens write->read, saving 9.03% of cost (writes priced at 2.0; a 24h tier would likely cost more per write, so an upper bound)
3c compact-before-leaving (>1h): 65 events; 1,801,486,752 tokens (27.4%) removed; gross saving 29.41% (at return call 6.72%, later calls 22.69%); net of compaction read cost 29.15%

PER SESSION
| id | calls | 1h write tok | 5m write tok | returns>5m | return cost % | return write cost % | rewrites within1h / after1h / switch | 24h wi % | compact net % | span h |
|---|---|---|---|---|---|---|---|---|---|---|
| S01 | 400 | 1,570,869 | 0 | 16 | 8.7 | 6.0 | 2 / 0 / 0 | 0.15 | 0.00 | 7.6 |
| S02 | 1303 | 6,588,396 | 0 | 54 | 14.8 | 11.4 | 0 / 8 / 0 | 10.33 | 41.19 | 48.1 |
| S03 | 4820 | 21,584,289 | 0 | 214 | 12.7 | 9.2 | 2 / 23 / 0 | 8.25 | 27.74 | 136.6 |
| S04 | 166 | 1,644,681 | 0 | 5 | 29.1 | 28.6 | 3 / 0 / 0 | 19.96 | 0.00 | 15.6 |
| S05 | 1923 | 8,507,084 | 0 | 42 | 13.0 | 11.2 | 3 / 7 / 0 | 10.41 | 24.63 | 41.7 |
| S06 | 464 | 2,362,049 | 0 | 16 | 16.0 | 13.7 | 3 / 1 / 0 | 10.53 | 1.55 | 649.3 |
| S07 | 66 | 173,152 | 0 | 1 | 1.0 | 0.0 | 0 / 0 / 0 | 0.00 | 0.00 | 0.6 |
| S08 | 105 | 760,379 | 0 | 5 | 28.6 | 26.8 | 1 / 1 / 0 | 2.20 | 10.61 | 1298.8 |
| S09 | 4056 | 17,535,029 | 0 | 95 | 13.1 | 11.2 | 6 / 18 / 0 | 9.88 | 39.17 | 122.6 |
| S10 | 2878 | 13,765,681 | 0 | 41 | 12.6 | 11.6 | 6 / 6 / 0 | 8.39 | 24.61 | 53.7 |

Spearman rho returns vs span hours (10 sessions): 0.42; pooled returns per span hour 0.21
hour 00-06 UTC: 159 returns / 5090 calls = 3.1%
hour 06-12 UTC: 146 returns / 5588 calls = 2.6%
hour 12-18 UTC: 135 returns / 4117 calls = 3.3%
hour 18-24 UTC: 49 returns / 1376 calls = 3.6%
returns >1h: 67, ctx median 547,380
gap 5-10m: 211 calls, cache survived 99%
gap 10-30m: 149 calls, cache survived 97%
gap 30-60m: 49 calls, cache survived 86%
tokens read on surviving 5-60m returns (would be re-written under a 5m TTL): 184,247,531; avoided cost vs 5m TTL at 1.25 write = 26.5% of input cost
```

## Caveats
- Assumes the 30k summary suffices: no re-reading, re-explaining or lost-state cost is counted. Most of the 3c saving (23 of 29 points) is not the return write but shorter contexts on later calls until the next drop, so it is mainly a context-size effect that compaction anywhere would give, not an idle effect. With only 40 actual drops (median context 783k) in 16k calls, the replay carries the reduction for a long stretch. Treat 3c as an upper bound.
- 3b is also an upper bound (24 h write price unknown; priced at 2.0).
- Model switches: 0 in this data, so every re-write is a prefix change or an expiry. "Within 1 h" re-writes are not necessarily prefix changes: the gap is end-to-end between timestamps and can overstate or understate real idle time near the 60-minute edge (30-60 min survival is 86%).
- 10 sessions, one person; S08 spans 1,299 hours (long-lived, few calls). S01 is the live session and was cut at 400 calls. Time of day is UTC (user timezone unknown).
- Sub-agent calls (5-minute writes) are excluded.

## Findings
1. 97% of calls follow a gap under 5 min and read the cache; the 1-hour TTL works: after 5-60 min gaps 97% of calls still read (94% mean read share); after any gap over 1 h, 0% of calls (67 of 67) survive, and 96%+ of the context is written again.
2. Returns (489, 3% of calls) are large: median context 489k, p90 725k tokens; 43.2M write tokens, 13.2% of the main-session input cost (10.8% is the write part at 2.0). Returns over 1 h (67) carry a median 547k context.
3. Of 90 re-writes, 71% (64) came after the 1-hour lifetime (79% of re-written tokens, 7.3% of cost); 29% (26) within it (1.97% of cost), where the prefix changed or timing was at the edge. Caching for 24 h would remove at most about 9.0% of cost.
4. A 1-hour TTL already avoids 184M write tokens on 5-60 min returns, about 26.5% of cost versus a 5-minute TTL.
5. Compacting before leaving would save up to about 29% of cost if the summary suffices, mostly through later calls' smaller context; the return write itself accounts for 6.7 points. No time-of-day pattern; returns per session rise weakly with span (rho 0.42, 10 sessions, 0.21 returns per span hour).
