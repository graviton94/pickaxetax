# Preprint outline (draft for approval)

**Working title:** *Paging, Not Forgetting: An Offline-Optimal Bound on Context Residency in LLM Agents*

**Format:** English preprint (arXiv, cs.LG or cs.DC with a cs.SE cross-list), with a Korean summary ([summary-ko.md](summary-ko.md)). Code and data: this repository (Apache-2.0 / ODbL).

**Gate before submission:** results from more than one session and more than one agent (H4). The n = 1 case study alone is a blog post, not a paper.

## Abstract (draft)

LLM agents re-process their whole context on every call, so the input they process grows with the square of session length. We ask how much of that context a session needed. We model an agent's context as segments with measured residency windows. Using the calls whose outputs reuse each segment, we compute the offline-optimal residency: what a policy that knows the future would have kept, for any cost of re-fetching dropped content. The optimum decomposes per segment and per gap between uses, which makes the bound exact for the model and computable in linear time from ordinary transcripts. We calibrate segment sizes to provider-reported usage, so that the model reconciles exactly with measured input at every call. On a 322-call coding-agent session, dropping content after its last use avoids 9.1% of input, while an oracle that drops content between uses and re-fetches on demand avoids 50.1%. A third of all input cannot be attributed to anything visible in the transcript. We argue that usage-side efficiency should be measured as memory residency per valuable outcome, and that agents should carry pointers, not payloads.

## Sections

1. **Introduction.** Quadratic re-reading in chat and agents. Why tokens are the wrong unit (Jevons) and memory residency the physical one (HBM, prompt caching as compute→memory conversion). Contributions:
   - an exact, computable offline bound on context residency;
   - a calibration method that reconciles transcript-level models with provider usage;
   - an open tool and the first measurements;
   - the "paging, not forgetting" result and its design implication.
2. **Units.** Token-calls; U1 compute per valuable outcome; U2 KV byte-seconds; the value ladder V0–V3. ([framework.md](../framework.md) §1–3)
3. **Model and optimum.** Segments, windows, references, cost with re-fetch penalty *P*; the per-gap proposition and proof; relation to Belady's MIN and to NP-hard capacitated variable-size caching. ([belady-bound.md](../belady-bound.md) §1–2)
4. **Measurement.** Transcript parsing, de-duplication, compaction, calibration and the unattributed remainder, lexical reference detection and its two failure directions. (§3)
5. **Results.**
   - Case study (n = 1).
   - Contributed sessions (target: ≥ 30 sessions, ≥ 2 agents).
   - Sensitivity grids.
   - Breakdown by segment kind.
   - Value proxy.
6. **Implications.**
   - Pointer-not-payload agent design: evaluate a practical pointer + recency policy against the bound (H5).
   - What providers should disclose: invisible context, cache retention, KV bytes per token.
   - How the Compute Bubble Index uses the bound.
7. **Limitations.** n, lexical detection, segment granularity, token-calls vs. FLOPs, the oracle assumption.
8. **Related work.**
   - Caching theory: Belady 1966; Chrobak et al. 2012.
   - Storage amplification: O'Neil et al. 1996.
   - Context management for LLMs: virtual-context paging (MemGPT, Packer et al. 2023); prompt compression (LLMLingua, Jiang et al. 2023).
   - KV-cache eviction: H2O, Zhang et al. 2023; StreamingLLM, Xiao et al. 2023.
   - How we differ: those methods change what a model keeps. We measure how far real sessions are from the least they needed, independently of any method, and we provide the yardstick to evaluate such methods on real agent traces.
9. **Reproducibility.** `pxt agent bound`, `research/sensitivity.py`, published aggregates, and the contribution path for bounds.

## Before submission

- [ ] Add the bound to the anonymous `agent` contribution kind, in both validators, so others can contribute bounds (aggregates only).
- [ ] Collect ≥ 30 sessions from ≥ 2 agents (H4).
- [ ] Implement and measure a practical pointer policy (H5).
- [ ] Verify every related-work citation against the primary source.
- [ ] Choose the arXiv category and find an endorser.
