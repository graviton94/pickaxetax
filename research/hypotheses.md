# Hypothesis log

Every hypothesis is recorded with its result, including the ones that failed. All experiments run locally on transcripts and publish aggregates only.

The first experiments used the session that built this repository as their subject (the "dogfood" session). They were run at different points of that session, so the call counts differ between entries.

## H0 — Read amplification (descriptive)

*Question:* how much input does a coding agent process per token it writes?
*Snapshot:* 226 calls, 94,880,088 input tokens, 485,860 output tokens.
*Result:* **195×** read amplification. The base context (system prompt and tools) was 46,707 tokens, so 11.1% of all input was a floor that every call re-sends.

## H1 — Dead context

*Claim:* most carried context is never used again.

- **H1, naive metric: falsified.** Counting a segment as "used" if any later output shares any of its tokens marked nearly everything as used. Only 1% looked dead. Common tokens (paths, keywords) make the test meaningless.
- **H1′, refined:** ignore tokens that appear in more than 2% of outputs and measure, per segment, the share of distinctive tokens that no later output echoes. **54%** of carried information was never echoed. This is an **upper bound** on dead context, because lexical echo misses use that leaves no verbatim trace.
- **Superseded by** the offline-optimal bound ([belady-bound.md](belady-bound.md)), which asks a sharper question: not "is it ever used again" but "is it needed at each call in between". The answer changed the picture: little is dead (9.1% avoidable by forgetting), much is idle (50.1% avoidable by paging).

## H2 — Task-scoped context

*Claim:* if every genuine user instruction started a fresh context that carried only a fixed-size summary of earlier work, input would drop by more than half.
*Method:* replay the measured per-call context, removing what had accumulated before each task and adding a summary of 2,000 / 8,000 / 20,000 tokens.
*Result:* **66–70%** less input (supported). *Caveat:* it assumes a summary is sufficient, which the experiment cannot check. It also drops the unattributed context that the oracle bound conservatively pins, which is why it exceeds the bound's 57.5% ceiling.

## H3 — State lives in artifacts

*Claim:* a large part of carried context duplicates content the agent already persisted to disk.
*Result:* Write/Edit content was **43%** of carried segment tokens, and about **78%** when all tool inputs are included (supported). The oracle bound confirms it with calibrated tokens: persisted writes are 25.1% of resident context (36% of it is unattributed), and 83.5% of their residency is unneeded.

## Open

- **H4 — Paging/forgetting ratio is stable** (framework P5): needs bounds from other sessions, other agents and other kinds of work.
- **H5 — A pointer policy approaches the oracle:** keep a pointer (path, version, range) plus a recency window, re-fetch on use, and measure the gap to *T\*(P)* on the same transcripts.
- **H6 — Invisible share by provider:** the unattributed 32.4% needs explanation. Compare sessions with thinking on and off, and across harnesses.
