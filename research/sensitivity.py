"""Sensitivity grid for the offline-optimal context bound.

    python research/sensitivity.py ~/.claude/projects/<project>/<session>.jsonl > result.json

Prints aggregates only (no text, paths or identifiers), so the output can be
published. The model and its caveats are in research/belady-bound.md.
"""

import json
import sys

from pickaxetax.agent.bound import analyze


def main(path: str) -> dict:
    main_run = analyze(path)
    grid = []
    for calibrated in (True, False):
        for min_shared in (1, 2, 3):
            for common_frac in (0.01, 0.02, 0.05):
                r = analyze(path, min_shared=min_shared, common_frac=common_frac, calibrated=calibrated)
                grid.append({"calibrated": calibrated, "min_shared": min_shared, "common_frac": common_frac,
                             **{k: v["avoidable_pct"] for k, v in r["policies"].items()}})
    return {"main": main_run, "sensitivity_avoidable_pct": grid}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=1))
