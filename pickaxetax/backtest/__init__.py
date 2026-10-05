"""Trace-driven backtests and benchmarks across providers.

The protocol (what is measured, how sessions are split, which statistics are
reported) is pre-registered in ``research/protocol/backtest-v1.md``; the
constants below must match it. Change them only with a new protocol version.
"""

PROTOCOL = "backtest-v1"
MIN_CALLS = 3  # sessions with fewer assistant replies / API calls are excluded
PENALTIES = (0, 1_000, 10_000, float("inf"))
PRIMARY_PENALTY = 1_000  # re-fetch cost for online policies
STUB_TOKENS = 20  # what a pointer to an evicted segment costs per call
GRID = (1, 2, 4, 8, 16, 32)  # policy parameter N, tuned on the dev split only
DEFAULT_N = 8  # used when the dev split has fewer than MIN_DEV sessions
MIN_DEV = 5
MAX_MISS_RATE = 5.0  # %: tuning objective is the lowest cost with median miss rate at or below this
DEV_SHARE = 51  # sessions whose fingerprint's first byte is < 51 (20%) form the dev split
MIN_CELL = 10  # strata with fewer sessions are shown but flagged, never reported as findings
BOOTSTRAP = 10_000
SEED = 20261005
LENGTH_BUCKETS = ((3, 9), (10, 49), (50, 199), (200, None))
SENSITIVITY_MIN_SHARED = (1, 2, 3)
SENSITIVITY_COMMON = (0.01, 0.02, 0.05)
