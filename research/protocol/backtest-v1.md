# Pre-registered protocol: backtest-v1

- Status: **frozen** on 2026-10-05, before any of the benchmark sessions were seen. The commit that adds this file is its timestamp.
- Code: `pickaxetax/backtest/` (constants in `__init__.py` must equal the values below; `tests/test_backtest_protocol.py` checks it).
- Changes: any change to a definition, threshold or analysis below creates **backtest-v2**. Results under v1 stay reported under v1. Deviations are logged at the end of this file, with the reason, before results are published.

## 1. Questions

- **Q1.** In real AI sessions, how much of the processed context was not needed at each step? Measured by the offline-optimal bound with re-fetch cost *P* ∈ {0, 1,000, 10,000, ∞} ([belady-bound.md](../belady-bound.md)).
- **Q2 (paging vs forgetting).** Is the saving from dropping content between uses and re-fetching it (*P* = 0) larger than the saving from dropping it only after its last use (*P* = ∞)? Per-session difference, median and 95% CI.
- **Q3 (backtest).** How much of that bound do simple online policies, which know only the past, actually achieve, and at what miss rate?
- **Q4 (strata).** Do Q1–Q3 differ by session length and by source (ChatGPT, Claude, Gemini, Grok, coding agents, ...)?

Q2 is the primary hypothesis: **H2: the median per-session paging-minus-forgetting difference is greater than 10 percentage points, with the 95% CI lower bound above 0.** It is decided on the test split.

## 2. Data

- **Units.** One session = one conversation in a chat export, or one agent transcript file. The session is the unit of analysis; tokens are never pooled across sessions for inference.
- **Inclusion.** Every session in the files supplied, any provider, any language.
- **Exclusion (fixed in advance).** Sessions with fewer than **3** assistant replies (chats) or API calls (agents). Nothing else is excluded, and no session is excluded after looking at its result.
- **Contributors.** Every run records who supplied the files, as an opaque label (`--contributor`). The report states the number of distinct contributors. Results from a single person are labeled "one contributor": they describe how one person works, not how people work.
- **Source label.** Detected from the export format, or set by the person supplying the file (`--source`). It labels the product the session came from, not the model version. Model versions inside one product are not separated in v1.
- **Privacy.** Files are processed on the machine they are supplied on and never committed. The report contains numbers only. The manifest (SHA-256 of each file plus the conversation's position) stays private, and its digest is published so the data set can later be proven without being revealed.

## 3. Measurement

| | Chat exports | Agent transcripts |
|---|---|---|
| Call | each assistant reply | each API call with non-zero usage |
| Context per call | all earlier turns (full-history baseline), estimated tokens | provider-measured input, cache included |
| Segments | each turn | prompts, replies, tool inputs and results, reminders, compaction summaries |
| Calibration | none (no usage in exports) | segments scaled to measured growth; remainder pinned as `unattributed` |
| Known bias | providers that trim or summarize long chats process less than the baseline | unattributed context is pinned, so the bound is conservative there |

- **Use detection (method `lexical-v1`).** A segment is used at a later call if the call's output reuses at least **1** of its distinctive tokens. Distinctive means identifiers or paths of 6 or more characters, Hangul words of 3 or more syllables, or numbers of 4 or more digits. Tokens appearing in more than **2%** of outputs (and in more than 3) are ignored. Every segment is also used by the call right after it arrives.
- **Detector validation (required before publication).** A person labels at least **100** (segment, later call) pairs, half drawn from detected uses and half from non-detected pairs, shuffled so the labeler cannot tell the strata apart (`pxt backtest label`). The report states:
  - precision with a Wilson 95% interval;
  - the share of non-detected pairs that were needed;
  - recall estimated by stratum re-weighting.
  
  Results are interpreted in the direction the validation indicates. Low recall means the bound is optimistic.

## 4. Policies (backtest)

Trace-driven simulation against each session's fixed reference string. A policy that dropped a segment a call needs pays **P = 1,000** tokens to fetch it back, and that call counts as a miss.

| Family | Keeps a segment while |
|---|---|
| `full` | always (what actually happened) |
| `window-N` | fewer than N calls have passed since it arrived |
| `recency-N` | it was used within the last N calls |
| `pointer-N` | as recency-N; an evicted segment leaves a **20**-token pointer |

- **Tuning.** N ∈ {1, 2, 4, 8, 16, 32}. Sessions are split by the first byte of SHA-256(fingerprint): below 51 (≈20%) is **dev**, the rest is **test**. Per family, N is chosen on dev as the value with the highest median saving whose median miss rate is at most **5%**. If no N qualifies, the largest N is used. If dev has fewer than **5** sessions, N = **8**. Results are reported on test only.
- **Metrics.** Saving (% of measured input), miss rate (% of uses that found the segment evicted), and gap closed (saving ÷ oracle saving at the same *P*).

## 5. Analysis

- Per stratum: the median, quartiles and a percentile-bootstrap 95% CI of the median (**10,000** resamples over sessions, seed **20261005** plus a fixed offset per statistic).
- **Strata:** all sessions; test split; source; length bucket (3–9, 10–49, 50–199, 200+ calls); source × length.
- **Comparisons between sources** are made only within the same length bucket, because waste grows with length. A stratum with fewer than **10** sessions is shown with its n but is not reported as a finding.
- **Sensitivity (secondary).** Q1 and Q2 are recomputed with `min_shared` ∈ {1, 2, 3} × common-token cut-off ∈ {1%, 2%, 5%}, and for agents also without calibration. A result is called robust only if its direction holds in every cell.
- **What we will not claim.**
  - Differences between sources are differences between sessions as people used those products. They are not differences in model quality.
  - The bound is an opportunity, not an achieved saving.
  - Chat figures are a full-history baseline, not provider costs.

## 6. Reproducibility

The report records:
- the protocol version and method;
- the tool version and git commit;
- the creation time and the manifest digest;
- counts by split;
- the N chosen on dev and why;
- every per-session row: source, length bucket, split, calls, and the metrics.

Anyone with the same files and this commit gets the same numbers: there is no randomness without a fixed seed and no model calls.

## Deviations

None yet.
