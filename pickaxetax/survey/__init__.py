"""Phenomenon survey: what a person's Claude Code use consists of, from recorded usage only.

measure.py   one transcript (local JSONL) -> numbers
events.py    saved remote-session events-API pages -> the same numbers
dataset.py   per-session measurements + session-list values -> one dataset file
report.py    dataset -> a self-contained HTML report (deterministic)
"""
