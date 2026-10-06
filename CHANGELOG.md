# Changelog

## Unreleased
- **Site:** new landing page. A chat window types "Hello" ("안녕하세요"), sends it, and the reply shows what that one line costs, using only measured numbers (427,524 tokens re-read per call in a long session; 5.87 billion tokens and 73.6% carried-over context in the first bill). Then: Did you know? (six measured facts), the analyzer, the first bill with the commands to get your own, and About us. The strict CSP is unchanged: no inline scripts, no external fonts or requests. The first bill is served at `report/user01.html`.
- **Survey:** `pxt survey measure` turns Claude Code transcripts into a numbers-only dataset (per-call context series, instruction boundaries, tools, compactions). `pxt survey report` renders it as a self-contained HTML report that is byte-for-byte reproducible from the dataset: context decomposition (fixed / carried over / current), the context sawtooth, steps × carried context, instruction-level concentration, measured vs displayed usage. The first published case is `research/survey/user01/report.html`.
- **Benchmark:** `pxt backtest run` measures many sessions from any provider (ChatGPT, Claude and Gemini exports, transcripts, Claude Code logs) under the pre-registered protocol `research/protocol/backtest-v1.md`. It reports the offline bound, online policies (window, recency, pointer) tuned on a dev split and reported on a held-out test split, bootstrap confidence intervals, strata by source and length, and a sensitivity grid. `pxt backtest label` validates the use detector by hand.
- **Contributions:** the anonymous `agent` contribution can carry the context bound (`pxt agent bound --export | pxt contribute send -`). Both validators check it, and the public aggregate reports medians over sessions.
- Gemini API (`contents` / `parts`) JSON is accepted as input.
- **Research:** `pxt agent bound` computes the offline-optimal context bound for Claude Code sessions: how much input an oracle that knows which context each call uses would have needed, for any cost of re-fetching dropped content. Segment sizes are calibrated to provider-reported usage, so the model matches measured input at every call.
- `research/`: the unit framework (compute per valuable outcome → memory residency), the bound's proof and first results, the hypothesis log, and the preprint outline with a Korean summary.
- Worker: live smoke test after every deploy; the deploy health check now sends a User-Agent.

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
