> Working memo from cycle C8 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the per-call numbers of cycles C5 and C7 and the public files.

# C8: how much do the phase-2 cost headlines depend on the price ratios?

This memo uses numbers only. The prices are given relative to uncached input = 1: cache read r, 5-minute write w5, 1-hour write w1, output o.
The default is r 0.1, w5 1.25, w1 2.0, o 5. I could not check a current price list here, so the grid is a sensitivity range, not a claim about today's prices.

## Method
- **Grid.** r ∈ {0.05, 0.08, 0.1, 0.15}, w1 ∈ {1.5, 2.0}, w5 = 1.25 and o ∈ {3, 4, 5}. Output tokens come from C5's low and high estimates (16.06M / 21.94M). That gives 48 settings.
- **Data reuse.** All data is reused read-only and was checked to hold numbers only: no text fields, hashed context keys and model labels.
  - C5's per-call usage (18,543 calls, numbers only).
  - C7's per-call records and cache replay, re-priced.
  - The public `dataset-v2.json` / `floor-t1.json` and `pickaxetax.survey.whatif`.
- **Token quantities are fixed and only the prices change.** The main sessions wrote only 1-hour cache, and the sub-agents wrote only 5-minute cache.
- **Floor.** Floor = (W1 + W2 tokens) × the main-session write price + W6 missed tokens × (write price − r). The denominator is input-side money, which is how judge.py does it.
  - W6 was recomputed with judge.py's rule from the per-call records: 90 events and 39,200,727 tokens, identical to the published values.
  - The variant "without re-writes after >1 h idle" uses the published by-cause split.
- **Money shares and the carried split.** These are C5's prefix-order split [base | carried | current], recomputed in tokens and priced at each setting.
- **Levers.** C5's model is generalised: kept context costs r, new content (summaries, growth) costs w1, and a restart or compaction costs r × base + w1 × the rest.
  - The saving fraction is computed per session ("scaled") and applied to the actual main input-side money at the same prices. Output is unchanged.
  - Restart above 200k mirrors `whatif.restart` (10k summary). Inputs and restart counts are asserted equal.
  - Ceilings use two replays:
    - C5's replay (B4 `curve.replay_one`, base = the session's first context, 22k summary);
    - `whatif.cap` with `COMPACTION_PREFIX` (42k) and `POST_COMPACTION_NEW` (22k), with input asserted equal.
  - The R = D2 re-read is priced per token as (6.6k × w1 + 76.1k × r) / 82.7k, which gives 0.252 at the default prices (C5 used 0.25).
- **TTL.** C7's anchored replay is re-run per policy with unit prices to get read / 5m-write / 1h-write / ping token quantities. Tier choices are price-independent for all policies except oracle + pings, which is re-planned at each setting. Each policy is then priced at each (r, w1, w5).

**Reproduction at the default prices (all exact):**

| quantity | value |
|---|---|
| input-side total | 836,245,393.6 |
| floor | 74,593,081.3 units = 8.92% |
| carried re-read, % of total money (low / high output) | 54.1 / 52.4 |
| carried re-read plus its re-writes, % of total money (low / high output) | 64.4 / 62.4 |
| ceiling 200k / restart / ceiling 390k, % of total money (low output) | 51.9 / 44.6 / 34.5 |
| ceilings with R = D2 | 51.3 / 34.3 |
| all-1h replay | 799.51M |
| all-5m vs all-1h | +19.77% |
| oracle per write (entry / segment) | −6.71 / −1.63% |
| hourly pings to 8 h | −4.81% |

The `whatif.cap` (42k + 22k) ceilings save about 1 point more than C5's replay: 52.8% and 35.5% of total money.

## 1. Headlines over the grid (% ; "a / b" = low / high output estimate)
| headline | default | grid min–max | r .05 w1 1.5 o 3 | r .05 w1 1.5 o 5 | r .05 w1 2 o 3 | r .05 w1 2 o 5 | r .15 w1 1.5 o 3 | r .15 w1 1.5 o 5 | r .15 w1 2 o 3 | r .15 w1 2 o 5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Floor, % input-side money | 8.92 | **4.66–15.4** | 12.3 | 12.3 | 15.4 | 15.4 | 4.66 | 4.66 | 6.19 | 6.19 |
| Floor, % total money | 8.14 / 7.89 | 4.25–14.0 | 11.2 / 10.8 | 10.5 / 9.97 | 14.0 / 13.6 | 13.2 / 12.6 | 4.47 / 4.41 | 4.35 / 4.25 | 5.94 / 5.86 | 5.79 / 5.66 |
| Floor without >1 h re-writes, % input-side | 1.90 | 0.99–3.27 | 2.63 | 2.63 | 3.27 | 3.27 | 0.99 | 0.99 | 1.32 | 1.32 |
| Cache-read share | 73.7 / 71.4 | 55.5–85.5 | 66.3 / 64.1 | 62.4 / 59.2 | 61.8 / 59.9 | 58.4 / 55.5 | 85.5 / 84.3 | 83.3 / 81.3 | 82.9 / 81.7 | 80.8 / 78.9 |
| Cache-write share | 17.5 / 17.0 | 9.9–29.4 | 24.2 / 23.4 | 22.8 / 21.6 | 29.4 / 28.5 | 27.7 / 26.4 | 10.4 / 10.3 | 10.1 / 9.9 | 13.1 / 13.0 | 12.8 / 12.5 |
| Output share | 8.76 / 11.6 | **3.9–19.2** | 9.5 / 12.5 | 14.8 / 19.2 | 8.8 / 11.7 | 13.9 / 18.0 | 4.1 / 5.5 | 6.6 / 8.8 | 3.9 / 5.3 | 6.4 / 8.5 |
| Re-reading carried context, % total | 54.1 / 52.4 | 40.8–62.7 | 48.7 / 47.0 | 45.8 / 43.4 | 45.3 / 43.9 | 42.8 / 40.8 | 62.7 / 61.8 | 61.1 / 59.6 | 60.8 / 60.0 | 59.3 / 57.9 |
| ... plus its re-writes | 64.4 / 62.4 | 55.8–68.7 | 62.6 / 60.5 | 58.8 / 55.8 | 62.6 / 60.7 | 59.1 / 56.3 | 68.7 / 67.7 | 66.9 / 65.3 | 68.6 / 67.6 | 66.8 / 65.3 |
| Ceiling 200k, % total (C5 replay) | 51.9 / 50.3 | 42.2–57.5 | 48.6 / 47.0 | 45.8 / 43.4 | 47.0 / 45.5 | 44.4 / 42.2 | 57.5 / 56.6 | 55.9 / 54.6 | 56.6 / 55.8 | 55.2 / 53.9 |
| Ceiling 200k, % total (whatif.cap) | 52.8 / 51.2 | 43.0–58.4 | 49.5 / 47.9 | 46.6 / 44.2 | 47.8 / 46.4 | 45.2 / 43.0 | 58.4 / 57.6 | 56.9 / 55.5 | 57.6 / 56.8 | 56.1 / 54.8 |
| Restart above 200k, % total | 44.6 / 43.2 | 37.1–48.8 | 42.3 / 40.9 | 39.8 / 37.7 | 41.3 / 40.0 | 39.0 / 37.1 | 48.8 / 48.1 | 47.5 / 46.4 | 48.3 / 47.6 | 47.0 / 46.0 |
| Ceiling 390k, % total (C5 replay) | 34.5 / 33.4 | 28.6–37.8 | 32.6 / 31.6 | 30.7 / 29.1 | 31.8 / 30.8 | 30.1 / 28.6 | 37.8 / 37.2 | 36.8 / 35.9 | 37.4 / 36.8 | 36.4 / 35.6 |
| Ceiling 390k, % total (whatif.cap) | 35.5 / 34.4 | 29.3–39.0 | 33.5 / 32.4 | 31.5 / 29.9 | 32.6 / 31.6 | 30.8 / 29.3 | 39.0 / 38.4 | 38.0 / 37.1 | 38.5 / 38.0 | 37.5 / 36.7 |
| Ceiling 200k, % main input-side | 59.5 | 54.1–62.6 | 56.7 | 56.7 | 54.1 | 54.1 | 62.6 | 62.6 | 61.5 | 61.5 |
| Restart above 200k, % main input-side | 51.1 | 47.6–53.2 | 49.3 | 49.3 | 47.6 | 47.6 | 53.2 | 53.2 | 52.5 | 52.5 |
| Ceiling 390k, % main input-side | 39.5 | 36.7–41.2 | 38.0 | 38.0 | 36.7 | 36.7 | 41.2 | 41.2 | 40.6 | 40.6 |

**One factor at a time from the default** (low output):

| headline | default | r 0.05 / 0.08 / 0.15 | w1 1.5 | o 3 / 4 | output high |
|---|---:|---:|---:|---:|---:|
| Floor, % input-side | 8.92 | 15.4 / 10.8 / 6.19 | 6.88 | — | — |
| Floor, % total | 8.14 | 13.2 / 9.65 / 5.79 | 6.25 | 8.43 / 8.28 | 7.89 |
| Cache-read share | 73.7 | 58.4 / 69.2 / 80.8 | 76.8 | 76.4 / 75.0 | 71.4 |
| Output share | 8.76 | 13.9 / 10.3 / 6.40 | 9.13 | 5.45 / 7.13 | 11.6 |
| Carried re-read, % total | 54.1 | 42.8 / 50.7 / 59.3 | 56.4 | 56.0 / 55.0 | 52.4 |
| Ceiling 200k, % total | 51.9 | 44.4 / 49.7 / 55.2 | 52.9 | 53.8 / 52.8 | 50.3 |
| Restart above 200k, % total | 44.6 | 39.0 / 43.0 / 47.0 | 45.2 | 46.2 / 45.4 | 43.2 |
| Ceiling 390k, % total | 34.5 | 30.1 / 33.2 / 36.4 | 35.0 | 35.7 / 35.1 | 33.4 |

How each headline moves with the prices:
- **The read price r drives almost everything.**
- **The floor goes against r.** W6 is priced at w1 − r and the denominator is mostly reads, so halving r raises the floor by 1.7×.
- **The levers go with r.** They remove reads of kept context, but their summaries and growth are still written at w1.
- **w1 1.5 → 2.0** moves the levers by about 1 point and the floor by 2 points.
- **o** changes only the denominator, by 1–2 points.

## 2. Robustness checks
- **Lever ordering.** Ceiling 200k > restart above 200k > ceiling 390k > floor holds in all **48 / 48** settings. It also holds with the summary output charged, with `whatif.cap` instead of C5's replay, and with R = D2.
  - The gap between ceiling 200k and restart is 5.1–8.7 points.
  - The floor also stays above every TTL lever (oracle per write, hourly pings, upgrade ping) in 48 / 48.
- **"Half of the money re-reads finished work"** is only partly price-robust.
  - Carried context is 76.2% of main cache-read tokens, which does not depend on price.
  - Its share of total money is 41–63%, and at least 50% in 35 / 48 settings.
  - Solving for 50% gives r* = 0.054–0.086 depending on w1, o and output. Below that read price, the read part alone is under half.
  - With its re-writes after cache expiry it stays at 56–69% in every setting. As a share of input-side money (no output) it is 50–65%.
- **The 1-hour vs 5-minute TTL conclusion is fully price-robust** (table below).

| r | w1 | all-5m vs all-1h (main input money) | same, % of total money (o 3–5) | sub-agents: all-1h vs observed 5m | oracle per write, entry / segment | 1h + hourly pings to 8 h | 5m + upgrade ping (to 4 h) | oracle + pings |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 1.5 | +46.8% | 35.8–40.2 | +4.5% | −4.1 / −0.8 | −7.6 | −6.9 | −11.4 |
| 0.05 | 2.0 | +35.3% | 27.5–30.6 | +22.0% | −11.3 / −2.7 | −9.9 | −14.2 | −18.3 |
| 0.08 | 1.5 | +31.5% | 25.7–27.9 | +3.5% | −2.8 / −0.6 | −4.4 | −3.1 | −7.3 |
| 0.08 | 2.0 | +24.2% | 19.9–21.6 | +16.8% | −8.0 / −1.9 | −6.2 | −8.5 | −12.4 |
| 0.1 | 1.5 | +25.6% | 21.5–23.1 | +3.1% | −2.3 / −0.5 | −3.2 | −1.6 | −5.8 |
| **0.1** | **2.0** | **+19.8%** | 16.7–17.9 | +14.6% | −6.7 / −1.6 | −4.8 | −6.2 | −10.1 |
| 0.15 | 1.5 | +17.1% | 14.9–15.7 | +2.4% | −1.6 / −0.3 | −1.5 | +0.5 | −3.6 |
| 0.15 | 2.0 | +13.2% | 11.6–12.2 | +11.0% | −4.8 / −1.2 | −2.7 | −2.8 | −6.8 |

- **Where all-5-minute would win.** All-5m is cheaper than all-1h only if w1 > 3.50 × w5 − 2.50 × r, because it writes 260.5M tokens against 74.5M.
  - At w5 = 1.25 this means **w1 > 4.0–4.25** (r 0.15 → 0.05).
  - At w5 = 1.0 it means w1 > 3.1–3.4, and at w5 = 1.5 it means w1 > 4.9–5.1.
  - The ratio w1 / w5 would have to exceed about 3.1–3.4, against 1.2–1.6 in the grid.
  - Lower read prices make 1h more valuable, because the survival it buys is a read instead of a re-write.
- **Per session** (r 0.1, w5 1.25), the break-even w1 is:

  | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 |
  |---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | 5.2 | 5.3 | 5.8 | **1.46** | 3.5 | 3.7 | **2.0** | 2.15 | 3.6 | 2.4 |

  S04 prefers 5m at every grid point, and S07 at w1 = 2.0.
- **Sub-agents.** 5m stays the better choice everywhere, but at w1 = 1.5 the margin shrinks to +2–5%.
- **TTL lever sizes are not price-robust.**
  - The oracle per write (entry) ranges from −1.6% to −11.3%, and hourly keep-alive from −1.5% to −9.9%.
  - The upgrade ping turns slightly costly at r 0.15, w1 1.5 (+0.5%).
  - They all scale with (w1 − w5) and with 1 / r.

## Caveats
- **Price ratios.** The grid is the brief's assumption, not a checked price list. Ratios may also differ between the models mixed in these sessions; a single ratio set is applied to all calls.
- **Replay behaviour.** Token quantities and replays are held fixed under every price. Real users and harnesses might behave differently under other prices, for example choosing different TTLs. Only the oracle + pings plan re-optimises.
- **Output.** Output tokens are C5's estimates (placeholders are recorded for 93–100% of calls). Output only enters denominators, because no lever changes it apart from the summary output.
- **Scaled savings.** Lever savings use C5's "scaled" convention: model saving fraction × actual money. The unscaled variant is not re-gridded; at the default it is 3–5 points lower for every lever.
- **TTL semantics.** The entry / segment caveats of C7 carry over unchanged.

## Findings
1. **The lever ordering is price-robust.** Ceiling 200k > restart above 200k > ceiling 390k > floor > TTL levers holds in 48 / 48 price settings. Ceiling 200k saves 42–58% of total money, restart 37–49% and ceiling 390k 29–38%; each moves by about ±7 points around C5's values, mostly with the read price.
2. **The floor is the most price-sensitive headline.** It is 8.92% at the default, 4.7–15.4% of input-side money across the grid, and 4.3–14.0% of total money. It moves inversely with r because W6 is priced at w1 − r.
3. **"Half of all money re-reads finished work" holds only for a read price ratio of about 0.06–0.09 or more.** Over the grid the read part alone is 41–63% (at least 50% in 35 / 48 settings). With its re-writes it is 56–69% everywhere. In tokens, carried context is 76% of main cache reads whatever the price.
4. **1-hour beats all-5-minute at every grid point.** The extra cost of all-5m is +13% to +47% of main input money, or 12–40% of total money. All-5m wins only if the 1-hour write costs more than about 3.1–3.4 times the 5-minute write (w1 > 4.0 at w5 = 1.25). Only S04, and S07 at w1 = 2, would prefer 5m.
5. **Shares and TTL lever sizes move most.**
   - Output share ranges 3.9–19% and cache-read share 56–86%.
   - The ideal-TTL savings range 1.5–11% (keep-alive / oracle), roughly proportional to (w1 − w5) / r.

Scripts and their outputs are kept with the analysis files.
