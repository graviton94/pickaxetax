# Self-audit log: waste in this research itself

The waste codebook (`research/protocol/waste-codebook-v1.md`, §4) counts the audit's own
costs. This log lists incidents noticed while doing the research, as candidates for
labeling. It holds no transcript text. Token amounts are filled in when the sessions that
ran the research are measured with the same tools.

| Date | What happened | Candidate category | Measured |
|---|---|---|---|
| 2026-10-05 | Ten research-note drafts were written in one go when only the first was wanted; all but note 1 were set aside | W7 Unrequested work | pending |
| 2026-10-05 | During the S09 and S10 downloads, agents in the hand-off chain started two new cloud sessions and sent them their hand-off prompts instead of handing off to the next agent; both sessions refused, correctly, because the files were not in their containers | W3 Coordination loss | **two sessions, 394,395 input tokens processed (cache reads 279,426, cache writes 114,955, uncached 14), 2,485 output tokens, about $1.03** (provider-recorded usage of the two sessions) |
| 2026-10-05 | The S10 download fetched page 102 twice (same cursor). De-duplication by event id kept the numbers unchanged | W1 Duplication | pending |
| 2026-10-05 | An S09 download agent was started with the wrong session id and stopped | W3 Coordination loss | pending |
| 2026-10-06 | 145 extra API calls to verify S10's page boundaries after the fact (verification, not waste by the codebook's definition; listed for completeness) | Not waste (verification) | 144 calls |
| 2026-10-06 | Research note 1 drafts v3 → v4 → v5 → v6: v4 read the 73.6% carried-over share as waste before any criteria existed; v5 overstated the output ratio as covering all sessions. Both were rewritten | W4 Discarded output | pending |
| 2026-10-06 | Download of the full event text of S04, S06, S07, S08 for the labeling pilot (56 pages), by two sub-agents | Not waste (measurement); counted as research cost | 177,872 sub-agent tokens |
| 2026-10-06 | The first version of the T1 judge treated all sub-agents of a session as one context, so a file read by two different sub-agents counted as a duplicate (S02: 8,210 W1 tokens instead of 211). Fixed before any result was published | Not waste (a measurement error, corrected) | — |
| 2026-10-06 | S02's 115 event pages failed to parse on a raw control character in a tool result. The parser was fixed; the pages did not need to be fetched again | Not waste | — |

## Research cost to date

The research runs in one Claude Code cloud session (S01 in the survey, measured only up to
its 400-call snapshot). Provider-recorded usage of that session as of 2026-10-06 14:00 UTC,
sub-agents included:

| Input processed | Cache reads | Cache writes | Uncached | Output | API-price equivalent |
|---:|---:|---:|---:|---:|---:|
| 584,981,506 | 578,380,118 | 6,336,669 | 264,719 | 1,716,724 | about $180.57 |

The same codebook will be applied to this session once the research phase it covers ends.
