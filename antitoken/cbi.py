"""Compute Bubble Index: validation of the curated capital/utilization dataset.

The dataset lives in git (``cbi/*.csv``) and grows through pull requests.
Every row must cite a primary source and carry a grade; a row counts
toward the index only after a second person has verified it.
"""

from __future__ import annotations

import csv
import re
from datetime import date

COLUMNS = [
    "id", "entity", "metric", "value", "unit", "period_start", "period_end", "grade",
    "source_url", "source_title", "accessed", "curator", "verifier", "notes",
]
REQUIRED = [c for c in COLUMNS if c not in ("verifier", "notes")]
METRICS = {
    "capex_ai",                 # AI-attributed capital expenditure
    "capex_total",              # total capital expenditure (context for capex_ai)
    "revenue_ai",               # revenue the entity attributes to AI products/services
    "circular_deal",            # investment from a supplier into a customer that buys from it
    "depreciation_life_years",  # useful-life assumption for servers / accelerators
    "power_contracted_mw",      # announced or contracted data-center power
    "power_operational_mw",     # power actually in operation
    "utilization_pct",          # reported or estimated accelerator utilization
}
GRADES = {"reported", "estimated", "measured"}
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")


def _iso(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def validate_csv(path: str, require_verified: bool = True) -> list[str]:
    errs: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            return [f"{path}: header must be exactly: {','.join(COLUMNS)}"]
        seen = set()
        for n, row in enumerate(reader, start=2):
            where = f"{path}:{n}"
            for c in REQUIRED:
                if not (row.get(c) or "").strip():
                    errs.append(f"{where}: missing {c}")
            if row["id"] and not _ID.match(row["id"]):
                errs.append(f"{where}: id must be lowercase slug")
            if row["id"] in seen:
                errs.append(f"{where}: duplicate id {row['id']}")
            seen.add(row["id"])
            if row["metric"] and row["metric"] not in METRICS:
                errs.append(f"{where}: unknown metric {row['metric']!r}")
            if row["grade"] and row["grade"] not in GRADES:
                errs.append(f"{where}: grade must be one of {sorted(GRADES)}")
            try:
                float(row["value"])
            except ValueError:
                errs.append(f"{where}: value must be numeric")
            for c in ("period_start", "period_end", "accessed"):
                if row[c] and not _iso(row[c]):
                    errs.append(f"{where}: {c} must be YYYY-MM-DD")
            if row["source_url"] and not row["source_url"].startswith("https://"):
                errs.append(f"{where}: source_url must be https")
            verifier = (row.get("verifier") or "").strip()
            if require_verified and not verifier:
                errs.append(f"{where}: unverified (a second person must fill 'verifier')")
            if verifier and verifier == row["curator"].strip():
                errs.append(f"{where}: verifier must differ from curator")
    return errs
