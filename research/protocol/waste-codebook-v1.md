# Waste codebook v1 — what counts as waste, and how it is decided

Status: **frozen, 2026-10-06.** v1 is v0 with the two open questions decided (see the
changelog at the end). It was committed before any data was judged with it, and that commit
is its timestamp. Changes after this are new versions (v2 …) with a changelog, and every
result names the version it used.

Why this exists: the first survey measured *volume* (how much was read, written, carried
over). Volume is not waste. 73.6% of each call's context was carried over from finished
instructions, but some of that context was genuinely needed. To call anything waste we need
criteria that are written down before looking, applied mechanically where possible, and
checked by people who cannot see what the machine decided.

## 1. Definition

**Waste** is tokens (input or output) that the outcome did not need: removing them, under a
stated counterfactual, would not have changed what was delivered. Every category below
names its counterfactual.

**Not waste, by definition** (reported separately, never added to waste):
- **Operating overhead:** the fixed base every call needs (system prompt, tool
  definitions). It is reported as overhead, because removing it would stop the agent from working.
- **Exploration that informed the result:** reading a file and then acting on what was read.
  Exploration beyond that is W8 (over-exploration) and does count.
- **Verification:** tests and checks, even when they pass.
- **The user's own thinking time.** Only tokens are counted.

## 2. Evidence tiers

Each category is assigned the strongest tier it can support. Results are reported per tier
and never blended silently.

| Tier | How it is decided | How it is reported |
|---|---|---|
| **T1 Mechanical** | From the logs by deterministic code; no judgment | Exact count, a **lower bound** of waste |
| **T2 Rule** | A written rule applied by code, validated against blind human labels | Corrected estimate with a confidence interval, published only if agreement passes (§5) |
| **T3 Judgment** | Needs to know what the person wanted | Hand-labeled sample proportion with a CI; never extrapolated beyond the sample frame |

## 3. Categories

Each token is assigned to **at most one** category. When several apply, the earliest in
this list wins, so nothing is counted twice.

| # | Category | Definition | Counterfactual | Tier | Detection |
|---|---|---|---|---|---|
| W1 | **Duplication** | The same work done again with the same result: the same tool call with the same arguments on unchanged input (re-reading an unchanged file), the same page fetched twice, identical retries | Done once | T1 | Equal call signature + unchanged size/mtime or identical result hash; duplicate event ids |
| W2 | **Failure and retry** | Calls that errored or were aborted, identical failing calls repeated, and the context re-read to recover from them | The successful path only | T1 (errors), T2 ("retry of") | Error results, aborted turns, rate-limit retries; a retry is a call that repeats a failed call's intent |
| W3 | **Coordination loss** | Work lost between agents or sessions: a hand-off sent to the wrong place, a delegated task refused or abandoned, a sub-agent whose output nobody read, a polling loop with no state change | The work routed correctly the first time | T1/T2 | Messages to sessions outside the plan, refusals, sub-agent outputs never referenced later, polls whose responses did not change |
| W4 | **Discarded output** | Output thrown away before use: files written then deleted or replaced wholesale, drafts superseded unread, answers the user rejected ("no, not that") | Only the kept output | T2 (git history + transcript), T3 (rejection) | File lifecycle in version control; rejection turns labeled by people |
| W5 | **Stale context** | Context carried into a call from a finished instruction that is never used again later in the session | A fresh context holding only what is used later | T2 | Use detector (`lexical-v1`, `research/protocol/backtest-v1.md`), validated by blind labels. Upper bound: all carried context; lower bound: carried and never used |
| W6 | **Cache churn** | Cache writes beyond the first for the same prefix: caused by resuming a session, switching models, or the cache expiring | One cache write per prefix | T1 | `cache_creation` tokens on a prefix already written in the same session |
| W7 | **Unrequested work** | Work the person did not ask for and did not use (e.g. ten drafts produced when one was asked for) | Only the requested work | T3 | Hand labels on instruction/response pairs |
| W8 | **Over-exploration** | Reads and searches by an agent or sub-agent whose results did not inform what was delivered: files opened and never acted on, searches whose hits were never used, a sub-agent reading 30 files to return a summary built from three | Only the exploration the result drew on | T3 (T2 proxy under validation) | Hand labels; proxy: tool results never referenced in any later output of that agent or its parent |

## 4. Units and counting

- Usage is de-duplicated per message id (one response is often logged as several lines).
- W8 takes the tokens of the exploring call's tool result where it arrives; carrying that
  result into later calls is W5. The two never take the same tokens.
- Input is split per call into overhead / carried / current (the survey's decomposition).
  Each category takes its tokens from the call it happened in.
- Two views of every number: **raw tokens**, and **price-weighted** (cache reads at 0.1×,
  cache writes at 1.25×, output at the model's output price). The second is closer to compute.
- The audit's own costs count too. Measurement runs, including the chain of agents that
  downloaded the survey pages, are logged as sessions and go through the same codebook.
  A study of waste that hides its own waste is not credible.

## 5. Validation (before any T2/T3 number is published)

1. **Sample:** 200 instructions, stratified by session and by instruction size, drawn with
   a fixed seed from a hash of the session fingerprints (as in `backtest-v1`).
2. **Coders:** two people label each item blind: they cannot see the detector's decision or
   each other's labels. The subject of the data may be one coder; the other must be someone
   else. An LLM may be a third coder, reported separately, never treated as ground truth.
3. **Agreement:** Cohen's κ per category. A category is published only if κ ≥ 0.70.
   Otherwise its definition is revised in a new codebook version and re-labeled.
4. **Disagreements:** every disagreement is published (ids and labels, no text), with how
   it was resolved.
5. **Detector accuracy:** for T2 rules, precision and recall against the agreed labels. The
   published estimate is corrected by them, with a bootstrap CI (seed 20261005).

## 6. What will be reported

For each category: T1 exact tokens, T2 corrected estimate with CI, T3 sample proportion with
CI. The total is a **range**, never one number: from the T1 sum (what nobody can dispute) to
T1 + T2 + T3 upper bounds. Categories that failed validation are listed as "not measured",
not as zero.

## 7. Known limits

- One person's logs describe how one person works, not how people work.
- Some waste is invisible in logs (a good answer the user never read). It is not estimated.
- "Needed" is judged against what was delivered, not against what would have been ideal.
  The codebook measures avoidable cost under the outcome that actually happened.

## Decisions on v0's open questions (2026-10-06)

1. **Context that was obeyed but never quoted** (a constraint like "don't touch the tests"
   that the agent followed without repeating it). The use detector still counts only reuse
   it can see. In the blind labels, a constraint the agent demonstrably followed counts as
   **used**. The detector's miss rate on such context is measured against those labels and
   the W5 estimate is corrected by it, so the detector's blind spot widens the confidence
   interval instead of inflating waste.
2. **A sub-agent's exploration when only its summary was used.** Exploration that the
   summary and the result drew on is not waste. Exploration beyond that is waste, as the
   new category **W8 Over-exploration**, judged on the labeled sample (T3). A mechanical
   proxy (tool results never referenced again by the agent or its parent) is reported only
   after it is validated against those labels.

## Changelog

- **v1 (2026-10-06):** frozen. Adds W8 Over-exploration. Decides the two open questions above.
- **v0 (2026-10-06):** first draft, seven categories, two open questions.
