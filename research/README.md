# Research

Theory and measurements behind Pickaxe Tax. The goal is to replace "AI wastes compute" with numbers that can be checked: a unit of account, provable bounds and reproducible measurements.

| Document | What it is |
|---|---|
| [framework.md](framework.md) | Units (compute per valuable outcome → memory residency), efficiency and waste, value measurement, the Jevons stance, propositions |
| [belady-bound.md](belady-bound.md) | The offline-optimal context bound: model, proof, measurement and first results |
| [hypotheses.md](hypotheses.md) | Every hypothesis with its result, failures included |
| [protocol/waste-codebook-v1.md](protocol/waste-codebook-v1.md) | What counts as waste: eight categories, evidence tiers (mechanical / rule / judgment), blind double labeling with κ ≥ 0.70, results as ranges. Frozen 2026-10-06, not yet applied to data |
| [protocol/mechanical-tier-v1.md](protocol/mechanical-tier-v1.md) | The waste floor decided by code (`pxt survey judge`): W1 duplication, W2 failures, W6 cache churn, exact rules and views |
| [protocol/rule-tier-v0.md](protocol/rule-tier-v0.md) | Rule-tier candidate detectors (W4, W5, W8) and their thresholds, fixed before the blind labels; hashes of the sealed machine labels |
| [protocol/review-kit-ko.md](protocol/review-kit-ko.md) | 공동 검토자용 한 장: 기계 판정 규칙 요약과 봐 줄 질문 (Korean) |
| [protocol/labeler-guide-ko.md](protocol/labeler-guide-ko.md) | 판정자 안내 한 장: 판정 페이지 쓰는 법과 여덟 갈래 요약 (Korean) |
| [protocol/labeling.md](protocol/labeling.md) | Blind labeling in practice: packet (`pxt survey sample`), the public labeling page, agreement (`pxt survey agreement`), adjudication. No account needed |
| [survey/self-audit-log.md](survey/self-audit-log.md) | Waste incidents in the research itself, as candidates for labeling |
| [survey/user01/floor-t1.md](survey/user01/floor-t1.md) | First result of codebook v1: the mechanical floor (T1) over user01's 10 sessions. Preliminary; judgment-tier categories wait for blind labeling |
| [survey/user01/opportunity-v1.md](survey/user01/opportunity-v1.md) | Opportunity, not waste: the oracle bound over the 10 sessions (drop only what is never used again vs fetch on demand) and what-ifs |
| [survey/user01/dataset-v2.json](survey/user01/dataset-v2.json) | user01 data, revision 2: all 10 sessions complete (S09 was partial), per-call series for every session. v1 stays as published |
| [protocol/backtest-v1.md](protocol/backtest-v1.md) | The benchmark and backtest protocol, committed (10ce4dd) before any benchmark data was collected; the commit is its timestamp, and a test keeps the code constants identical to it |
| [protocol/data-intake.md](protocol/data-intake.md) | How to supply sessions from each product, and what happens to them |
| [preprint/outline.md](preprint/outline.md) | Outline of the English preprint (draft for approval) |
| [preprint/summary-ko.md](preprint/summary-ko.md) | 한글 요약 |
| [results/](results/) | Published aggregates (no text, paths or identifiers) |

## Reproduce on your own sessions

```bash
pip install pickaxetax
pxt agent bound                      # all Claude Code sessions in ~/.claude/projects
pxt agent bound path/to/session.jsonl --json
python research/sensitivity.py path/to/session.jsonl   # the full sensitivity grid, aggregates only
pxt backtest run exports/*.json --source chatgpt     # the pre-registered benchmark over many sessions
```

## Rules

- **Local only.** Transcripts never leave the machine they were recorded on. Only aggregates are published.
- **Failures stay in the log.** A falsified hypothesis is a result.
- **Every number carries its snapshot,** its method and its known biases.
- **n is stated.** A single session is a case study, not evidence of a general pattern.
