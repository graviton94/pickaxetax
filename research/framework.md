# Framework: compute per valuable outcome, measured as memory residency

Status: **working draft** (v0.1, 2026-10-05). Decisions: [ADR-0008](../docs/decisions/0008-research-track.md). Korean summary: [preprint/summary-ko.md](preprint/summary-ko.md).

The project so far has counted *tokens*. Tokens are what vendors bill, but they are not the physical cost, and counting them alone invites the obvious objection: efficiency makes AI cheaper, so people use more of it (Jevons). This document fixes the unit of account before more measurements are published.

## 1. Units

| Level | Unit | What it captures | Measurable today from |
|---|---|---|---|
| U0 | tokens processed (input + output) | the bill | provider usage fields |
| **U1** (base) | **compute per valuable outcome**: tokens or FLOPs ÷ outcomes | waste relative to what was achieved | usage + an outcome signal (§3) |
| **U2** (extension) | **memory residency per valuable outcome**: KV-cache byte-seconds ÷ outcomes | the HBM capacity that the work occupies | usage + model shape + timing (§2) |

U1 is the base because it can be measured now, by anyone, from logs they already have. U2 is where the argument about semiconductors lives, and it is reached from U1 by a conversion that is explicit about its assumptions.

### The common measurable: token-calls

For an agent or chat session with API calls *k = 1…N*, each re-processing a context of *c_k* tokens:

```
token-calls  T = Σ_k c_k
```

*T* is the input that providers report (including cache reads). It is the quantity that both compute and memory scale with:

- **Prefill compute** is roughly `2 · params · c_k` FLOPs per call for the weight multiplications, plus an attention term that grows with `c_k²`. Prompt caching removes most of the prefill compute for the cached prefix, but not the attention reads over it during decoding.
- **KV residency** of call *k* is `β · c_k` bytes, where β is the model's KV-cache bytes per token (`2 · layers · kv_heads · head_dim · bytes_per_value`). It is held for the duration of the call, and **for the cache TTL afterwards** when prompt caching is on.

The last point matters. Prompt caching turns repeated compute into retained memory: re-reading is cheaper in FLOPs because the KV state stays resident in accelerator memory or a nearby tier between calls. Cheap re-reads therefore do not make long contexts free. They shift the cost from compute to memory capacity, which is the scarcest and most expensive part of an accelerator (HBM).

### U2 conversion

```
R = Σ_k β · c_k · τ_k                      (byte-seconds)
```

τ_k is how long call *k*'s KV state is resident: prefill + decode time, plus the retention window if it stays cached. β is public for open-weight models (e.g., a 70B-class model with grouped-query attention, 80 layers, 8 KV heads of dimension 128, fp16 → 2·80·8·128·2 = 327,680 bytes ≈ 320 KiB per token) and must be disclosed or estimated for closed ones. We publish U2 figures only with β, τ and their sources stated, graded like every other number (measured, reported or estimated).

## 2. Efficiency and waste

For a fixed set of valuable outcomes *V*:

```
efficiency   η = V / T                      (or V / R in U2)
waste        W = T − T*(V)
```

T\*(V) is the least token-calls with which the same outcomes could have been produced. T\* is not observable, but it can be **bounded**. The first bound is the offline-optimal context residency: what an oracle that knows which context each call will use would have kept. Method and results: [belady-bound.md](belady-bound.md).

The bound makes waste a property of the session rather than a matter of opinion: *these* segments sat in context for *these* calls while nothing used them.

## 3. Measuring value

A unit "per valuable outcome" needs a definition of outcome that cannot be gamed by producing more output. We use a ladder and always state the rung:

| Rung | Outcome | Example signal | Status |
|---|---|---|---|
| V0 | user accepted | no correction or retry follows the answer | in the conversation analyzer (`superseded` waste) |
| V1 | persisted artifact | tokens written to disk by Write/Edit; commits | in `pxt agent bound` (input per written token) |
| V2 | verified artifact | tests pass, PR merged, artifact still present after N days | needs repository signals |
| V3 | adopted | used by someone other than its author | out of scope for now |

V1 is crude: more written tokens is not more value. It is used only as a denominator for comparisons within one kind of work, never as a target.

## 4. The Jevons question

If efficiency only lowers the price per token, total consumption can rise. Our stance ([ADR-0008](../docs/decisions/0008-research-track.md)) is **efficiency plus value measurement, to move the incentive**:

1. Publish value-normalized figures (T/V, R/V), not just savings. A provider or tool that serves the same outcomes with less residency is visibly better, whatever its total volume.
2. Ask for disclosure of the quantities that only providers can see: invisible context (thinking, harness framing), cache retention time, and β for each served model. See the "unattributed" share in the first measurement: about a third of all input could not be attributed to anything visible in the transcript.
3. Keep the absolute numbers next to the normalized ones in the Compute Bubble Index, so that efficiency gains that are eaten by volume remain visible as such.

## 5. Propositions and their status

| # | Proposition | Status |
|---|---|---|
| P1 | The physical unit of usage-side waste is memory residency × time; token-calls is its measurable proxy. | Definition. U2 conversion stated above. |
| P2 | Most avoidable residency is content that **is** used again later, but not at every call in between. Paging it out and back beats forgetting. | Supported, n = 1: dropping only after last use saves 9.1% of input; an oracle that re-fetches on demand saves 50.1%. [belady-bound.md](belady-bound.md) |
| P3 | Agent state lives in artifacts. Context copies of content already persisted to disk are a cache, not the source of truth. | Supported, n = 1: content the agent itself wrote to disk is 25.1% of resident context, 83.5% of it unneeded at the oracle. Earlier: [hypotheses.md](hypotheses.md) H3. |
| P4 | A large share of context is invisible to the user and to auditing tools. | Measured, n = 1: 32.4% of input is unattributed. |
| P5 | The ratio between the "forget" and "page" bounds is stable across sessions and tools. | Open. Needs contributed bounds from other sessions and agents. |

Borrowed theory, and what each lends:

- **Belady's MIN** (1966): with knowledge of future references, the best eviction is computable offline. This gives a lower bound that no real policy can beat, which turns "waste" into a measurable gap.
- **LSM-tree write amplification** (O'Neil et al., 1996): systems are judged by bytes moved per byte of useful work. Read amplification of an agent session (input processed ÷ output) is the same kind of ratio.
- **Normalization** (Codd, 1970): store a fact once and refer to it ("pointer, not payload"). An agent that keeps file contents in context instead of a path and a version is denormalized.
- **Minimal sufficient statistics**: the least context from which the same next action follows. The oracle bound approximates it from above, at segment granularity.
