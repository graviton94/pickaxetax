# Proposal: a "survey" contribution kind (n > 1)

Status: **proposal, not implemented** — a contribution schema change is the maintainer's decision
(both validators, `pickaxetax/contrib.py` and `site/contrib.js`, must change together and stay in
parity, and the public aggregate gains a new block).

## Why

Every phase 2 result is one person. `pxt survey run` already produces the same measurements on
anyone's transcripts, locally, numbers only. What is missing is a way to pool them anonymously.

## What would be sent

One object per contributor, built by `pxt survey run --export` and sent through the existing
`pxt contribute send -` path (issue or worker), as `kind: "survey"`:

| Field | Per session (at most 200) | Rounding |
|---|---|---|
| calls, instructions, compactions | integers | none (small counts) |
| input processed | integer | 2 significant digits |
| median context per call, peak context | integers | nearest 10k |
| carried-over share (decomposition) | % | 1 decimal |
| floor: removable tokens %, removable cost %, steps-only-on-W1/W2 % | % | 2 decimals |
| oracle bound: P=∞, P=1000, P=0 | % | 1 decimal |
| what-if: restart above 200k (10k summary) | % | 1 decimal |
| 1-hour share of cache writes | % | whole number |

Plus: tool version, `lexical-v1` method tag, agent (`claude-code`), and the number of sessions.

## What would never be sent

Text of any kind, paths, ids, timestamps, model names beyond the family, session titles, the
per-call series. Rounding keeps a contribution from acting as a fingerprint of a session that
someone else could match against a known transcript.

## Validation (both validators)

Exact key set; integer and range checks (percentages 0–100, counts ≥ 0, sessions ≤ 200); method
tag known; rejected otherwise with the existing error format.

## Public aggregate

Medians and IQRs across contributors (not sessions) for each field, with the contributor count;
nothing shown until at least five contributors, as for the other kinds.
