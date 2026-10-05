# LinkedIn series: the plan, chapter by chapter

Instead of one launch post, the project's plan is published as a **series of research notes** on LinkedIn. Interest builds over five weeks, and each chapter can take in the comments on the one before it. Decisions: [ADR-0009](../../decisions/0009-linkedin-series.md), [ADR-0010](../../decisions/0010-benchmark-and-backtest.md).

## Format (ADR-0009, ADR-0010)

| | |
|---|---|
| Style | **A research note**: each post reports that note's question, measurement, finding and what's next, as if it were the day's lab result. The author's own motivation appears only in note 1 |
| Language | **Korean is the original, English is the translation**, both in **one post** (Korean first, then `— English —`, then the English) |
| Voice | 합니다체, first person, from the maintainer's account |
| Length | Korean **700–900 characters**; the whole post (both languages) stays under LinkedIn's 3,000-character limit. Each file states its counts |
| Cadence | **Tuesday and Thursday**, 08:00–09:00 KST. Five weeks |
| Title line | `[연구 노트 N/10] 제목` / `[Research note N/10] Title` |
| Ending | "다음 노트: …" / "Next: …", then `#AntiTokenMaxing` once at the very end |
| Drafts | Written together with the maintainer: Korean first, English translated from the final Korean. Status is in each file |

## Arc

The order goes from question → evidence → tool → science → ask. The tool is not shown before the reader cares about the problem, and the request for data comes only after the findings have earned it.

| # | Date | Chapter | Purpose | Link to | Image |
|---|---|---|---|---|---|
| 1 | Thu 10-08 | [The pickaxe tax](01-the-pickaxe-tax.md) | The problem and the promise of the series | — | `docs/img/og.png` |
| 2 | Tue 10-13 | [We measured one session](02-we-measured.md) | First hard number | — | — |
| 3 | Thu 10-15 | [Tokens are the wrong unit](03-wrong-unit.md) | Jevons; memory residency; HBM | — | — |
| 4 | Tue 10-20 | [The tool: see your own waste](04-the-tool.md) | **Launch day**: web app (X thread + Reddit start the same day) | site, repo | `docs/img/result.png` |
| 5 | Thu 10-22 | [Coding agents](05-coding-agents.md) | Audit + guard; the 3× overcount | repo | — |
| 6 | Tue 10-27 | [The hypothesis that failed](06-failed-hypothesis.md) | Credibility through a failure | research | — |
| 7 | Thu 10-29 | [Paging, not forgetting](07-paging-not-forgetting.md) | The headline result | research | `docs/img/series/ch07-paging.png` |
| 8 | Tue 11-03 | [The invisible third](08-invisible-third.md) | Watchdog: ask providers to disclose | research | `docs/img/series/ch08-invisible.png` |
| 9 | Thu 11-05 | [The Compute Bubble Index](09-bubble-index.md) | The public index + one-click contribution | site | — |
| 10 | Tue 11-10 | [n = 1 is not proof](10-call-for-data.md) | Call for data before the preprint | research | — |
| 11 | when data allows | [First results from you](11-first-results.md) | Payoff: aggregate numbers (template) | site | chart from the aggregate |

## Before each post

- [ ] Every number in the draft is in the facts table ([../README.md](../README.md#facts-sources-for-every-number-in-the-drafts)).
- [ ] Any link in the post works (from chapter 4 on, the site and the repo must be live).
- [ ] For chapter 4: the launch checklist in [../README.md](../README.md) is done, including the `main` branch allowed in the `github-pages` environment.

## After each post

- Reply to every comment in the first 3 hours. Good questions become material for the next chapter: say so ("I'll answer this in Chapter N").
- Log impressions, reactions, comments, profile visits and repo stars in the table below. Next chapter's hook gets adjusted if a chapter underperforms.

| # | Impressions | Reactions | Comments | Reposts | Stars (repo) | Note |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## Rules

- No claim beyond the facts table. "Avoidable" is always defined, and n is always stated.
- How the project was built is not part of the story. Posts talk about the problem, the measurements and the tools.
- The business side (organization, funding, acquisition) is not discussed in public posts.
- Never ask for likes or reposts. The ask is "try it", "measure your own" or "send your numbers".
