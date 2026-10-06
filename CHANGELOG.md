# Changelog

## Unreleased
- **Judging:** `pxt survey judge` computes the mechanical waste floor of codebook v1 (W1 duplication, W2 failures, W6 cache churn) per session: removable tokens (W1 + W2) and removable cost (W6 counts only its cache-write premium over a read, since those tokens are processed either way), with main session and sub-agents shown apart, each sub-agent as its own context. W6 is broken down by what preceded it (model switch, idle gap); the carry of W1/W2 results into later calls is reported outside the floor. Rules: `research/protocol/mechanical-tier-v1.md`.
- **Survey data v2:** `research/survey/user01/dataset-v2.json` and `report-v2.html`. S09 is measured in full (it was partial), S02 and S03 gain per-call series from event pages cut at the snapshot, S01 gains its sub-agents up to the snapshot. Input processed: 6.84 billion tokens (v1: 5.87 billion, a lower bound); carried-over share 76.1% (v1: 73.6%, over 8 of 10 sessions). `dataset.json` (v1) is unchanged, since research note 1 cites its digest.
- **First T1 floor:** `research/survey/user01/floor-t1.md`: removable tokens 0.0008% of input, removable cost 5.79%, almost all of it cache re-writes, 79% of those after an idle gap of over an hour.
- Event pages: raw control characters in tool output are accepted; sub-agent usage is measured; `measure_pages` can cut a session at a snapshot (calls or instructions). Local transcripts are judged with their `subagents/` files.
- Report: no partial-measurement sentences when no session is partial.
- `pxt survey sample --exclude` and `--limit`; the labeling page in five languages.
- **Rule tier v0** (`research/protocol/rule-tier-v0.md`, `pickaxetax/survey/rules.py`): per-instruction candidate detectors for W5 stale context, W8 over-exploration (read-only shell commands included) and W4 discarded output, with thresholds fixed before the blind labels and the sealed machine labels' hashes committed. `pxt survey machine --tier t2`.
- **Opportunity** (`research/survey/user01/opportunity-v1.md`): the oracle bound over the 10 sessions and `pxt survey whatif`; the bound accepts parsed lines and reports context carried over from finished instructions.
- Judge: steps spent only on W1 or W2 results (descriptive).
- `pxt survey machine`: the T1 judge's decisions on a packet's items as a labels file, to check the mechanical tier against the consensus labels with the same agreement report. `pxt survey judge` can return per-instruction categories.
- **Labeling:** `pxt survey sample` draws a blind-labeling packet from your own transcripts (stratified, seeded, optional redaction); `site/label.html` lets anyone label it in the browser with no account and nothing uploaded; `pxt survey agreement` computes Cohen's kappa per category from two labels files. Procedure: `research/protocol/labeling.md`.
- **Research:** waste codebook v1 (eight categories, frozen before any judgment).

## 0.4.0 — 2026-10-06
- **Site:** #AntiTokenMaxing. The bill is now "the receipt of the 21st-century gold rush". "The weight of a line" turns re-read tokens into energy, CO₂ and trees with every factor sourced (`research/carbon-factors.md`, `pxt`'s `pickaxetax.survey.carbon` and `site/carbon.js`, parity-tested), labelled as estimate and metaphor. "The cost" shows the world's receipt (Big Tech capex, data-centre power and CO₂ from the IEA, generative-AI e-waste) next to the measured digital waste, with sources and a scope caveat. The personal result gains a carbon estimate. Dark cinematic sections, scroll reveals off under reduced motion; the strict CSP is unchanged.
- **Site:** landing page. A chat window types "Hello" ("안녕하세요"), sends it, and the reply shows what that one line costs, using only measured numbers (427,524 tokens re-read per call in a long session; 5.87 billion tokens and 73.6% carried-over context in the first bill). Then: Did you know? (six measured facts), the analyzer, the first bill with the commands to get your own, and About us. The strict CSP is unchanged: no inline scripts, no external fonts or requests. The first bill is served at `report/user01.html`.
- **Survey:** `pxt survey measure` turns Claude Code transcripts into a numbers-only dataset (per-call context series, instruction boundaries, tools, compactions). `pxt survey report` renders it as a self-contained HTML report that is byte-for-byte reproducible from the dataset: context decomposition (fixed / carried over / current), the context sawtooth, steps × carried context, instruction-level concentration, measured vs displayed usage. The first published case is `research/survey/user01/report.html`.
- **Benchmark:** `pxt backtest run` measures many sessions from any provider (ChatGPT, Claude and Gemini exports, transcripts, Claude Code logs) under the pre-registered protocol `research/protocol/backtest-v1.md`. It reports the offline bound, online policies (window, recency, pointer) tuned on a dev split and reported on a held-out test split, bootstrap confidence intervals, strata by source and length, and a sensitivity grid. `pxt backtest label` validates the use detector by hand.
- **Contributions:** the anonymous `agent` contribution can carry the context bound (`pxt agent bound --export | pxt contribute send -`). Both validators check it, and the public aggregate reports medians over sessions.
- Gemini API (`contents` / `parts`) JSON is accepted as input.
- **Research:** `pxt agent bound` computes the offline-optimal context bound for Claude Code sessions: how much input an oracle that knows which context each call uses would have needed, for any cost of re-fetching dropped content. Segment sizes are calibrated to provider-reported usage, so the model matches measured input at every call.
- `research/`: the unit framework (compute per valuable outcome → memory residency), the bound's proof and first results, the hypothesis log, and the preprint outline with a Korean summary.
- Worker: live smoke test after every deploy; the deploy health check now sends a User-Agent.
- Tests: store fixtures use distinct conversations (skeleton ids are locality-sensitive, so near-identical fixtures could collide).

## 0.3.1 — 2026-10-05
- Launch-ready README (screenshot, quick start, privacy guarantees), `pxt --version`, OG card and social meta tags.
- SECURITY, CODE_OF_CONDUCT, issue and PR templates, and the launch kit in `docs/launch/`.

## 0.3.0 — 2026-10-05
- **Contributions:** one-click anonymous contributions from the web app and `pxt contribute send` to a Cloudflare Worker (proof of work, no stored IPs, delete tokens). Verified contributions through a GitHub issue form with automated validation and `/withdraw`.
- One allowlist validator, mirrored in JS and Python, with identical verdicts on 45 cases.
- The public aggregate (k-anonymous topics) is baked into the static site daily.

## 0.2.0 — 2026-10-05
- **Coding agents:** `pxt agent audit` for Claude Code transcripts (de-duplicates usage per message; detects re-reads, large outputs and repeated failures; tracks carried tokens).
- Guard hook against re-reading unchanged files; `pxt agent hook install`; the repository doubles as a Claude Code plugin marketplace.

## 0.1.0 — 2026-10-05
- Conversation skeleton analyzer (agenda, intents, topic threads, depth, token accounting) with a graph store and Cypher export.
- Local-first static web app (browser engine, bookmarklet for share links, CSP-enforced no-upload).
- Local proxy with a counts-only ledger, local gratitude replies and history compaction.
- Crowd-run over-computation benchmark; CBI dataset schema and validator.
