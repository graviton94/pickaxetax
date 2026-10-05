# Changelog

## Unreleased
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
