# LinkedIn series: the plan, chapter by chapter

The project is published on LinkedIn as **research notes, one at a time**. There is no fixed list of notes: each note reports what the research reached that day, and the maintainer and Claude write it together. The comments on one note can shape the next research step. Decisions: [ADR-0009](../../decisions/0009-linkedin-series.md), [ADR-0010](../../decisions/0010-benchmark-and-backtest.md).

## Format (ADR-0009, ADR-0010)

| | |
|---|---|
| Style | **A research note**: each post reports that note's question, measurement, finding and what's next, as if it were the day's lab result. The author's own motivation appears only in note 1 |
| Language | **Korean is the original, English is the translation**, both in **one post** (Korean first, then `— English —`, then the English) |
| Voice | 합니다체, first person, from the maintainer's account |
| Length | Korean **700–900 characters**; the whole post (both languages) stays under LinkedIn's 3,000-character limit. Each file states its counts |
| Cadence | When there is a result worth reporting; the date is set together for each note |
| Title line | `[연구 노트 #N] 제목` / `[Research note #N] Title` |
| Ending | `#AntiTokenMaxing` once at the very end. A "next note" line only when the next step is already known |
| Drafts | Written together with the maintainer: Korean first, English translated from the final Korean. Status is in each file |

## Notes

| # | Note | Status | Posted |
|---|---|---|---|
| 1 | [곡괭이세](01-the-pickaxe-tax.md) | draft, being refined together | — |

## How a note is made

1. A research step is done (a measurement, an experiment, a tool, a failure).
2. Together we decide what that step showed and what is worth telling.
3. The Korean is drafted and refined together; the English is translated from the final Korean.
4. Every number is added to the facts table ([../README.md](../README.md#facts-sources-for-every-number-in-the-drafts)) before posting.

## After each post

- Reply to every comment in the first 3 hours. Questions worth researching become candidates for the next step.
- Log the response below.

| # | Impressions | Reactions | Comments | Reposts | Stars (repo) | Note |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## Rules

- No claim beyond the facts table. "Avoidable" is always defined, and n is always stated.
- How the project was built is not part of the story. Posts talk about the problem, the measurements and the tools.
- The business side (organization, funding, acquisition) is not discussed in public posts.
- Never ask for likes or reposts. The ask is "try it", "measure your own" or "send your numbers".
