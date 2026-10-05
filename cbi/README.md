# CBI dataset: capital and utilization layer

Curated, sourced data for the Compute Bubble Index ([design](../docs/BUBBLE_INDEX.md)). The data lives in git and grows through pull requests. Data license: [ODbL 1.0](../DATA_LICENSE.md).

## Rules

1. **Primary sources only.** Use filings, earnings releases and transcripts, official company or regulator documents, and peer-reviewed papers. Press articles help you find the primary source; they are not a source themselves.
2. **One number per row**, using the exact figure and unit the source states. Don't convert currencies and don't compute derived values in this file. Derived values belong in the index code.
3. **Grade every row.**
   - `reported`: the source states the number.
   - `estimated`: the number is derived or estimated. Explain how in `notes`.
   - `measured`: a project measurement. Link the run.
4. **Two-person rule.** A row counts only once someone other than the `curator` has checked it against the source and filled in `verifier`. CI rejects unverified rows on the main data file.
5. **Corrections are public.** Fix rows through a PR, and say what changed and why.

## Columns

`id, entity, metric, value, unit, period_start, period_end, grade, source_url, source_title, accessed, curator, verifier, notes`

Metrics: `capex_ai`, `capex_total`, `revenue_ai`, `circular_deal`, `depreciation_life_years`, `power_contracted_mw`, `power_operational_mw`, `utilization_pct`

Check your rows before opening a PR:

```bash
antitoken cbi validate cbi/capital.csv              # main file: rows must be verified
antitoken cbi validate cbi/drafts.csv --drafts      # drafts may be unverified
```
