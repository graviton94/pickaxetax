# E2 power and cost: how many replicates the restart experiment needs

Status: **design calculation, cycle D7, 2026-10-06. Nothing was run on a model; running E2 is the data owner's decision.** Scripts and their output tables are in `power/` next to this file. All numbers come from
simulation with stated assumptions. Inputs are public repository files only:
`research/phase3/e2-taskset-v0.md`, `e2-tasks-v0.json`, `research/phase2/phase3-experiments.md`,
`synthesis.md`, and the price ratios of `C5-money.md` and `C3-value-per-token.md`.

## Answer in brief

- **Quality is what drives the size of E2, and the affordable design detects only large losses.**
  One replicate gives 15 post-restart instruction pairs in 4 chain-run units. At a 75% baseline pass
  rate, the loss estimate has an SD of about 15/√R points.
  - With 80% power (one-sided α 0.10), a **20-point loss needs about 4–5 replicates**, a **10-point
    loss about 9–14**, and a **5-point loss about 26–54** (45–94 at two-sided α 0.05).
  - **1–2 replicates can show nothing at two-sided α 0.05.** With 4 units, the smallest possible
    two-sided p is 0.125.
- **Tokens.** The model predicts a 43.4% input saving for arm (b) (45.3% for c).
  - A 90% CI of ±5 points needs about **6–8 replicates if a chain-run varies with CV 0.2**, 15–22 at
    CV 0.35, and 28–44 at CV 0.5. At 6 replicates the CI is about ±5–6, ±8–10 or ±11–14 points.
  - In price units the predicted saving is smaller, **28% (b) / 31% (c)**. Writes and output are
    nearly the same in both arms.
- **Recommended design.**
  - **Two arms, (a) and (b), forked at the first restart boundary.** The boundary is the first
    instruction boundary where the context is above 200k.
  - **Group-sequential with looks at R = 3 and R = 6** (at most 6 replicates).
  - **Non-inferiority margin of 15 points** on the share of post-restart instructions whose
    fail-to-pass tests all pass.
  - **Drop arm (c)** from the confirmatory run.
  - **Cost: at most 1.26–1.66B input tokens (184–244M price units).** When there is no loss, it
    stops on average after about 4.4 replicates (≈0.9–1.2B). That is the budget D6 quoted for
    three replicates of three independent arms.
- **What the recommended design can and cannot tell.**
  - If the restart costs nothing, it concludes "not worse by more than 15 points" with probability
    69–94% (baseline 60–90%).
  - It finds a 20-point loss 84–92% of the time.
  - It **cannot** find a 5-point loss (16–19%), and finds a 10-point loss only 37–49% of the time.
  - Phase 2 expects "a few points" of loss. That is below what E2 at this size can resolve.

## 1. Inputs from the repository

**Token model.** I rebuilt D6's bottom-up model from `e2-tasks-v0.json`: 20k base, 25 calls per
instruction, the instruction's growth spread linearly over them, and a restart above 200k costing
20k + summary + 26.8k cold start. It reproduces every per-chain `est_input` exactly. Two facts follow
from it that the power calculation needs.

| chain | post-restart instructions in (b) | restarts | a (M) | b (M) | c (M) | pre-boundary, all arms (M) | saving b | saving c |
|---|---|---|---|---|---|---|---|---|
| A | 4–7 | 2 | 40.9 | 21.5 | 20.7 | 8.1 | 47.4% | 49.4% |
| B | 4–7 | 1 | 38.4 | 22.2 | 21.4 | 9.4 | 42.1% | 44.2% |
| C | 5–7 | 1 | 33.7 | 22.4 | 21.8 | 11.1 | 33.6% | 35.4% |
| D | 4–7 | 2 | 45.6 | 23.7 | 22.9 | 10.3 | 48.0% | 49.8% |
| **total** | **15 of 28** | | **158.5** | **89.8** | **86.8** | **39.0 (25% of a)** | **43.4%** | **45.3%** |

- Only **15 of the 28 instructions** run after a restart. Instructions before the first boundary are
  identical in every arm by protocol, so they carry no information about the restart.
- D6's figure does not charge the summary-request call (one call at the boundary context). Charging
  it lowers the savings to 42.5% (b) and 44.4% (c).

## 2. Method

### 2.1 Quality model

The outcome is one per instruction: 1 if all of the instruction's fail-to-pass tests pass after it.
For replicate r, chain c, instruction k and arm m:

```
logit P(pass) = mu + u[c,k] + w[c] + v[c,r,m] + delta * post[c,k] * [m = b] - carry * fail[c,r,m,k-1]
```

- `u` is the instruction effect, with SD **s_u = 0.5, 1.0, 1.5** (the heterogeneity asked for). It
  is drawn once per simulated experiment, so power is averaged over task sets like this one.
- `w` is the chain effect (SD 0.5), shared by arms and replicates.
- `v` is the **chain-run effect** (SD 0.5; sensitivity 0 and 1.0), one per run. It makes
  instructions in the same run correlated, which is the clustering a test must respect.
- `post` marks the post-restart instructions from the table above (A, B, D: 4–7; C: 5–7).
- `carry` lowers the next instruction's chance after a failure (0 in the main runs, 1.0 as a
  sensitivity). It models the task set's dependence of later tasks on earlier ones.
- Two designs are simulated:
  - **Independent runs**: arms (a) and (b) are separate runs with independent `v`.
  - **Forked**: one run up to the boundary, then two branches from the same session and working
    tree. Pre-boundary outcomes are shared, and the post-boundary run effects correlate at ρ = 0.5.
- **Calibration.**
  - `mu` is set so that arm (a)'s pass rate on post-restart instructions equals the baseline (60%,
    75%, 90%).
  - `delta` is set so that arm (b)'s rate is lower by the loss (5, 10, 15, 20, 30 points).
  - Without carry-over this uses a numerical integral; with carry-over, an exact Markov recursion
    over 3,000 draws.
  - Simulated pass rates match the targets within 0.3 points (T9 in `power_quality.out`).
- 5,000 simulated experiments per scenario, each with 10 replicates analysed as nested prefixes
  R = 1…10. The Monte Carlo SE is at most 0.7 points.

### 2.2 Tests

The unit is the chain-run pair: 4 per replicate. For each unit, D = Σ over post-restart instructions
of (pass_a − pass_b).

- **Primary: an exact sign-flip (randomization) test on D**, one-sided (b worse) at 0.10 and
  two-sided at 0.05. It is valid whatever the within-run correlation, because it uses the
  independent unit.
- **Secondary: exact McNemar** on the pooled discordant instruction pairs. It ignores clustering.
- **Non-inferiority (NI): "restart is not worse by more than M."**
  - The loss estimate is ΣD / Σn.
  - Its SE is a cluster (ratio-estimator) SE over units.
  - NI is concluded if the estimate + t(0.90, units − 1) × SE < M.

### 2.3 Tokens

- **Variation.** Run-to-run variation of a chain-run's input is lognormal with **CV 0.2 / 0.35 /
  0.5**. These CVs are **assumptions**: no repeated run of the same chain exists, and phase 2 has no
  replicate runs.
- **Independent runs.** The two arms are independent.
- **Forked runs.** The pre-boundary part is shared. The segment CV is set so that a whole arm-(a)
  run still has the stated CV.
- **Estimand.** The pooled saving is 1 − Σb / Σa.
- **Two interval widths are reported:**
  - *ideal*: delta method with the CV known (confirmed by the simulated 5–95% spread);
  - *practical*: the mean half-width of the interval an analyst would compute. That is a
    chain-stratified t interval on per-run log ratios, with df = 4(R − 1); at R = 1 it is
    across 4 units with df = 3.

### 2.4 Cost conversion (price units)

The project's ratios (C5) are used, with uncached input = 1:

- **Rule (B4).** In each call, the content added since the previous call is a 1-hour cache write
  (2.0) and the rest of the context is a cache read (0.1). A variant uses 5-minute writes (1.25).
- **Output** is 20k per instruction (C3) plus each summary, at 5. Uncached input is ≈ 0 (C5: 0.01%).
- **Check.** Arm (a) comes to 0.119 input-side units per input token, against phase 2's 0.92M /
  7.5M = 0.123 per commit (C3).
- **Dollars** = units × the model's price per uncached input token. No price is assumed here.
- **High scenario.** Arm (a) is scaled to phase 2's median of 7.5M input per instruction (×1.32),
  with the same saving. D6's "≤ 630M" is a looser bound that assumes no saving at all.

## 3. Tokens and cost

**Predicted saving in money.** Price units per replicate:

| | a | b | c |
|---|---|---|---|
| 1-hour writes (2.0) | 21.7M | 15.7M | 15.1M |
| 5-minute writes (1.25) | 20.5M | 14.3M | 13.7M |

- The saving is **27.7% (b) / 30.6% (c)** with 1-hour writes, and 30.2% / 33.1% with 5-minute
  writes. Both are well below the 43–45% saving in input tokens.
- Cache reads are about 72% of arm (a)'s price. Writes and output (13%) are nearly the same in both
  arms, and each restart adds a summary and a cold start written at 2.0.
- Phase 2's 47–48% saving of cost included re-writes after idle breaks, which a harness run without
  breaks does not have.
- This is a pre-registrable expectation for the cost measure.

**Cost of one replicate (4 chains).** Input tokens and price units, model / high:

| design | input tokens | price units |
|---|---|---|
| 3 arms, independent runs (D6's design) | 335M / 444M | 52.5M / 69.5M |
| 2 arms (a, b), independent runs | 248M / 329M | 37.4M / 49.6M |
| 3 arms, forked at the boundary | 257M / 341M | 39.1M / 51.8M |
| **2 arms, forked at the boundary** | **209M / 277M** | **30.7M / 40.7M** |

R replicates cost R times these. For example, 6 forked two-arm replicates cost 1.26–1.66B tokens
(184–244M units), and 10 cost 2.09–2.77B. The full table by R is in `tokens_cost.out`.

**Precision of the input saving (b vs a).** Practical 90% CI half-width, in points:

| design | CV | R=1 | R=3 | R=6 | R=10 | R for ±5 (ideal / practical) |
|---|---|---|---|---|---|---|
| independent | 0.2 | 19.5 | 8.4 | 5.6 | 4.2 | 7 / 8 |
| independent | 0.35 | 34.0 | 14.5 | 9.6 | 7.3 | 22 / 21 |
| independent | 0.5 | 50.0 | 20.7 | 13.5 | 10.2 | 44 / 40 |
| forked | 0.2 | 16.8 | 7.1 | 4.7 | 3.6 | 6 / 6 |
| forked | 0.35 | 27.5 | 12.1 | 8.0 | 6.2 | 16 / 15 |
| forked | 0.5 | 39.8 | 16.9 | 11.1 | 8.5 | 33 / 28 |

±5 points is affordable only if chain-runs vary by about 20% or less. A first estimate of the CV will
come from the R = 3 look. Even at CV 0.5, six replicates separate 43% from 0% or from 20%.

## 4. Quality: power

**T1. Power to detect a loss.** Exact sign-flip test on chain-run units, s_u = 1.0, independent
runs. Each cell is one-sided α 0.10 / two-sided α 0.05, in %.

| baseline | loss | R=1 | R=2 | R=3 | R=4 | R=5 | R=6 | R=7 | R=8 | R=9 | R=10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 60% | 5 | 3 / 0 | 11 / 2 | 15 / 4 | 18 / 6 | 20 / 7 | 23 / 7 | 25 / 8 | 27 / 9 | 30 / 11 | 32 / 12 |
| 60% | 10 | 4 / 0 | 21 / 4 | 29 / 10 | 36 / 14 | 43 / 17 | 48 / 22 | 53 / 25 | 58 / 30 | 62 / 34 | 67 / 38 |
| 60% | 20 | 12 / 0 | 47 / 16 | 65 / 35 | 77 / 48 | 85 / 60 | 91 / 71 | 94 / 79 | 96 / 85 | 98 / 90 | 99 / 93 |
| 75% | 5 | 2 / 0 | 11 / 2 | 16 / 4 | 20 / 6 | 23 / 8 | 26 / 9 | 29 / 10 | 30 / 11 | 32 / 12 | 35 / 14 |
| 75% | 10 | 3 / 0 | 21 / 3 | 32 / 10 | 39 / 15 | 46 / 20 | 52 / 26 | 57 / 31 | 62 / 35 | 67 / 39 | 71 / 44 |
| 75% | 20 | 10 / 0 | 49 / 15 | 69 / 36 | 80 / 52 | 88 / 64 | 92 / 75 | 96 / 83 | 97 / 88 | 98 / 92 | 99 / 95 |
| 90% | 5 | 1 / 0 | 10 / 1 | 18 / 4 | 23 / 6 | 28 / 9 | 32 / 11 | 36 / 14 | 39 / 16 | 42 / 18 | 46 / 20 |
| 90% | 10 | 3 / 0 | 22 / 4 | 37 / 12 | 49 / 21 | 57 / 29 | 65 / 37 | 72 / 45 | 77 / 51 | 81 / 57 | 85 / 63 |
| 90% | 20 | 10 / 0 | 57 / 17 | 77 / 47 | 88 / 66 | 94 / 79 | 97 / 87 | 98 / 93 | 99 / 96 | 100 / 98 | 100 / 99 |

**Smallest loss found with 80% power** (one-sided 0.10), in points:

| design | baseline | R=3 | R=4 | R=5 | R=6 | R=8 | R=10 |
|---|---|---|---|---|---|---|---|
| independent | 60% | 26 | 21 | 19 | 17 | 14 | 13 |
| independent | 75% | 25 | 20 | 18 | 16 | 14 | 12 |
| independent | 90% | 21 | 17 | 14 | 13 | 11 | 9 |
| forked | 75% | 24 | 19 | 17 | 15 | 13 | 12 |

**Replicates for 80% power beyond 10.** Normal approximation from the simulated SD at R = 10; each
cell is one-sided 0.10 / two-sided 0.05.

| baseline | SD of the loss estimate at R=10 | loss 5 | loss 10 | loss 20 |
|---|---|---|---|---|
| 60% | 5.4 points | 54 / 94 | 14 / 23 | 4 / 6 |
| 75% | 4.8 points | 45 / 78 | 13 / 22 | 4 / 6 |
| 90% | 3.4 points | 28 / 48 | 9 / 15 | 4 / 6 |

A 10-point loss at a 75% baseline needs about 13 replicates: 2.7–3.6B tokens in the forked two-arm
design. A 5-point loss needs about 45: 9–13B tokens.

**Heterogeneity barely matters.** Power at R = 3 / 5 / 10, one-sided 0.10:

| baseline, loss | s_u 0.5 | s_u 1.0 | s_u 1.5 |
|---|---|---|---|
| 75%, 10 | 28 / 42 / 67 | 32 / 46 / 71 | 33 / 49 / 75 |
| 75%, 20 | 65 / 85 / 98 | 69 / 88 / 99 | 73 / 91 / 99 |
| 90%, 10 | 37 / 56 / 82 | 37 / 57 / 85 | 40 / 60 / 86 |

More heterogeneity helps a little: instructions near 0% or 100% rarely disagree, so fewer pairs are
discordant by chance. Pairing removes the instruction effect itself. The full grid is in
`power_quality.out` (T2).

**Clustering and design.** Baseline 75%, s_u 1.0, R = 3 / 5 / 10:

| model | power, loss 10 | power, loss 20 | NI power, M = 15 | SD of the estimate at R=5 |
|---|---|---|---|---|
| main (chain-run SD 0.5, independent) | 32 / 46 / 71 | 69 / 88 / 99 | 65 / 82 / 96 | 6.8 |
| chain-run SD 1.0 | 28 / 39 / 62 | 61 / 81 / 97 | 58 / 75 / 93 | 7.6 |
| carry-over 1.0 | 27 / 40 / 63 | 60 / 81 / 97 | 58 / 75 / 93 | 7.8 |
| forked at the boundary | 32 / 47 / 73 | 71 / 90 / 99 | 67 / 83 / 97 | 6.7 |
| forked + carry-over | 28 / 42 / 66 | 64 / 84 / 98 | 60 / 77 / 94 | 7.2 |

- **Forking gains little power.** Post-restart outcomes are dominated by per-instruction chance.
- **Its gains are cost (−16% against independent two-arm runs) and comparability.** Both arms are
  scored on the same post-boundary instructions, starting from the same code.
- **False positives with no true loss** (full table: T3):
  - McNemar is at 2–8% against a nominal 5% (two-sided) and 5–11% against 10% (one-sided). It runs
    above nominal once runs are correlated (chain-run SD 1.0, or carry-over).
  - The sign-flip test stays at or below nominal everywhere (1–4% / 4–9%). Its slight loss of power
    against McNemar (T4) is the price of validity.

**Non-inferiority.** Probability of concluding "not worse by more than M" when the true loss is 0,
one-sided 0.10, independent runs, s_u 1.0:

| baseline | M | R=1 | R=2 | R=3 | R=4 | R=5 | R=6 | R=8 | R=10 |
|---|---|---|---|---|---|---|---|---|---|
| 60% | 10 | 22 | 30 | 38 | 44 | 49 | 54 | 63 | 70 |
| 60% | 15 | 30 | 45 | 56 | 67 | 73 | 79 | 88 | 93 |
| 60% | 20 | 41 | 59 | 74 | 84 | 90 | 94 | 98 | 99 |
| 75% | 10 | 24 | 34 | 42 | 50 | 56 | 62 | 72 | 79 |
| 75% | 15 | 32 | 52 | 65 | 75 | 82 | 87 | 93 | 96 |
| 75% | 20 | 48 | 67 | 82 | 90 | 94 | 97 | 99 | 100 |
| 90% | 10 | 40 | 51 | 60 | 72 | 78 | 84 | 90 | 94 |
| 90% | 15 | 45 | 73 | 85 | 92 | 95 | 97 | 99 | 100 |

- **M = 5 is out of reach:** 35–57% at R = 10.
- **Size** (NI concluded when the true loss equals M): 9–12% at the 60% and 75% baselines for
  R ≥ 2, but **12–17% at 90%**. With few units and pass rates near 1, the t bound is too
  optimistic. R = 1 is unreliable at every baseline: 9–21%.

## 5. Recommended design

1. **Arms: (a) and (b), forked at the boundary.**
   - Run each chain once up to the first instruction boundary where the last call's context is
     above 200k.
   - Save the session and a copy of the working tree. Claude Code can resume a saved session into a
     new one (`--resume … --fork-session`); check this on the harness version used.
   - Then run two branches:
     - **(a)** continues the same session;
     - **(b)** asks that session for the summary and continues in a new session. Later restarts
       happen inside the (b) branch.
   - This is exact, not an approximation: the protocol makes the arms identical up to that
     boundary.
   - It saves 39M tokens per replicate and puts both arms on the same post-boundary instructions.
2. **Drop arm (c)** from the confirmatory run.
   - Its token difference from (b) is about 2–3 points. That is below any affordable token CI
     (±5–13 at R = 6).
   - Its quality comparison would need the same replicates again, plus a multiplicity correction.
   - If budget allows, add it as a third branch at **+48M tokens (+8.4M units) per replicate**, and
     report it as exploratory.
3. **Pilot (not analysed):** one chain, forked (a)+(b), to check the harness. Chain C is the
   cheapest, about 45M tokens. The pilot checks:
   - that arm (a) does not auto-compact (1M window);
   - that the 200k boundary is reached;
   - that scoring and logs work;
   - that the (b) branch's first call reads a warm cache.
4. **Order of runs.**
   - Run replicate by replicate. Within a replicate, run the 4 chains in a random order.
   - Within a chain, run the prefix, then the two branches back to back in a random order.
     Start the (b) branch's summary request within the cache lifetime. Otherwise that one call
     re-writes the whole ≥200k context at 2.0. If that happens, price the call as a cache read in
     the cost analysis and say so.
   - Pin the model version, harness version and settings. Record them. Change nothing between looks.
   - Score automatically. Do not analyse outcomes before a planned look.
5. **Primary quality measure and test.**
   - The measure is the share of post-restart instructions whose fail-to-pass tests all pass,
     paired by chain-run.
   - Tests: an exact sign-flip test for harm; a cluster-t bound for non-inferiority.
   - Secondary measures: McNemar, the share of individual fail-to-pass tests (finer than all-pass),
     the first instruction after each restart alone, and regressions of earlier tasks.
6. **Non-inferiority margin: M = 15 points.**
   - It is the smallest margin with about 80% power at an affordable maximum of 6 replicates (75%
     baseline).
   - M = 10 would need about 10 or more replicates to reach 70–80%.
7. **Stopping rule (two looks, at R = 3 and R = 6).** At each look, compute the upper one-sided 95%
   bound of the loss (cluster t, 4R − 1 df) and the sign-flip one-sided p for harm.
   - **Stop for non-inferiority** if the bound is below 15 points.
   - **Stop for harm** if p < 0.05.
   - Otherwise continue to R = 6. At R = 6, the same tests decide, or the result is
     **inconclusive**: a loss between the estimate's bounds cannot be excluded.
   - Using α 0.05 per look keeps the overall error at about 10%: the NI claim is wrong 8–9% of the
     time at a true loss of 15, at 60–75% baselines.
   - **If arm (a)'s observed pass rate is above 85%, use α 0.04 per look.** At a 90% baseline the
     t bound is optimistic (11–12% at α 0.05).
   - Token savings and cost are reported with their CIs at the stopping point. They do not drive
     stopping.

**Operating characteristics of the stopping rule** (M = 15, forked, s_u 1.0). Each cell gives
P(non-inferior) / P(harm found) / P(inconclusive), and the mean number of replicates:

| true loss | baseline 75% | baseline 60% (independent runs) | baseline 90% (independent runs) |
|---|---|---|---|
| 0 | 80 / 5 / 15, R̄ 4.3 | 69 / 6 / 25, R̄ 4.7 | 94 / 3 / 3, R̄ 3.7 |
| 5 | 53 / 17 / 30, R̄ 4.8 | 45 / 16 / 40, R̄ 5.0 | 67 / 19 / 14, R̄ 4.5 |
| 10 | 25 / 42 / 33, R̄ 5.0 | 21 / 37 / 42, R̄ 5.1 | 34 / 49 / 17, R̄ 4.7 |
| 15 | 9 / 69 / 23, R̄ 4.8 | 8 / 63 / 29, R̄ 4.9 | 11 / 79 / 10, R̄ 4.5 |
| 20 | 3 / 89 / 9, R̄ 4.3 | 2 / 84 / 14, R̄ 4.5 | 4 / 92 / 4, R̄ 4.0 |
| 30 | 0 / 100 / 0, R̄ 3.4 | — | — |

**Variant: looks at R = 4 and R = 8.** At most 1.67–2.22B tokens.
- At a 75% baseline it concludes NI 88% of the time with no loss, and finds a 20-point loss 95% of
  the time.
- The mean number of replicates is 5.4 with no loss.
- It still finds a 10-point loss only about half the time.

## 6. What the design can and cannot detect

With at most 6 forked two-arm replicates (45 post-restart instruction pairs at R = 3, 90 at R = 6):

- **Can.**
  - Find a loss of 20 points or more (84–92%) and of 30 points (≈100%), usually at the first look.
  - With no loss, conclude that the restart costs at most 15 points (69–94%).
  - Measure the input saving to about ±5 (CV 0.2) to ±11 points (CV 0.5).
- **Cannot.**
  - Find a 5-point loss (16–19%). A 10-point loss is a coin flip (37–49%).
  - With no loss, conclude "not worse by more than 10 points" more than about half the time.
  - Test phase 2's "a few points" (synthesis §5.3). That needs about 30–50 replicates of this task
    set (6–14B tokens), or a task set about ten times larger.
  - Reach ±5 points on the saving if a chain-run varies by more than about 20%.
- **Generalization is limited by the task set, not the replicates.** Replicates repeat the same 15
  post-restart instructions. Doubling the chains would buy the same power per token, and would also
  widen what the result covers.

## 7. Caveats

- **Every quality number depends on the assumed model.** That covers the logit random effects, a
  restart effect that is constant over post-restart instructions, the carry-over form, and ρ = 0.5
  for forked branches. A loss concentrated in the first instruction after a restart is diluted
  about 4×. Hence the secondary analysis of that instruction alone.
- **The token CVs are assumptions.** No repeated run of a chain exists. The R = 3 look gives the
  first estimate. Phase 2 found that 87% of an instruction's input variance is its number of calls.
  - A secondary, pre-registered decomposition could split the saving into a steps ratio and an
    average-context ratio: input = steps × average context.
  - The context ratio is mostly mechanical and should be much tighter. If the steps ratio is near 1,
    it narrows the saving's CI.
- **The token model is D6's estimate.** Real sessions read more and may cross 200k earlier. That
  would put more instructions after the restart, which helps power, and change the saving. A chain
  that does not cross 200k in arm (a) adds nothing (D6 rule).
- **Discrete tests at few units.**
  - The sign-flip test is conservative.
  - The NI t bound is slightly optimistic at a 90% baseline (12–17% at nominal 10%) and at R = 1.
  - The stopping rule's per-look α accounts for this at 60–75% baselines only.
- **Contamination, one repository, thin statements, harness-synced files.** D6's caveats apply
  unchanged. Contamination raises the baseline, and power rises with the baseline (T1). It cannot
  be counted on.
- **Price units** use C5's list-price ratios and D6's growth model. Without idle breaks there are no
  cache-expiry re-writes. Dollar figures need the model's input price, which is not assumed here.

## Reproduction

The scripts are in the D7 scratch folder: standard library only, no network, no model calls, fixed
seeds.

- `stats_util.py`: t distribution, exact McNemar, exact sign-flip test by dynamic programming.
- `tokens_cost.py <repo>`: rebuilds D6's token model from `e2-tasks-v0.json` (asserting exact
  agreement), then the price units, cost by design and R, and the token-CI simulation.
  Writes `tokens_cost.out` and `tokens_cost.json`. Takes about 5 min.
- `power_quality.py [nsim]`: the quality simulation (5,000 per scenario, 4 processes, about 2 min).
  Writes `power_quality.json`.
- `make_tables.py` and `extrapolate.py`: the tables (`power_quality.out`, `extrapolate.out`).
