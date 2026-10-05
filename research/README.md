# Research

Theory and measurements behind Pickaxe Tax. The goal is to replace "AI wastes compute" with numbers that can be checked: a unit of account, provable bounds and reproducible measurements.

| Document | What it is |
|---|---|
| [framework.md](framework.md) | Units (compute per valuable outcome → memory residency), efficiency and waste, value measurement, the Jevons stance, propositions |
| [belady-bound.md](belady-bound.md) | The offline-optimal context bound: model, proof, measurement and first results |
| [hypotheses.md](hypotheses.md) | Every hypothesis with its result, failures included |
| [preprint/outline.md](preprint/outline.md) | Outline of the English preprint (draft for approval) |
| [preprint/summary-ko.md](preprint/summary-ko.md) | 한글 요약 |
| [results/](results/) | Published aggregates (no text, paths or identifiers) |

## Reproduce on your own sessions

```bash
pip install pickaxetax
pxt agent bound                      # all Claude Code sessions in ~/.claude/projects
pxt agent bound path/to/session.jsonl --json
python research/sensitivity.py path/to/session.jsonl   # the full sensitivity grid, aggregates only
```

## Rules

- **Local only.** Transcripts never leave the machine they were recorded on. Only aggregates are published.
- **Failures stay in the log.** A falsified hypothesis is a result.
- **Every number carries its snapshot,** its method and its known biases.
- **n is stated.** A single session is a case study, not evidence of a general pattern.
