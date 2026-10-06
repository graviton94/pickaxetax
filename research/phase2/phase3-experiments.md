# From phase 2 to phase 3: experiments the levers need

Status: **design draft, 2026-10-06** (ideation from `synthesis.md`). Nothing here has been run.
Each experiment tests the assumption a phase 2 lever rests on, with outcomes checked by tests,
and is meant to be pre-registered (committed before it runs) like the codebook and the backtest.

## Why experiments

Every large saving in phase 2 rests on an assumption the logs cannot check: that a summary is
enough to continue (restart rules, earlier compaction), that a pointer is enough until the content
is needed (authored content), that a sub-agent's answer is enough (delegation). Only running the
same work under the changed structure, and checking the result, can test that.

## E1 — A user-level bundle, before and after (the data owner, from the next sessions)

The levers a user can pull today, as a short project instruction file (for example `CLAUDE.md`):

```
- After writing or editing a file, do not print its content again; refer to it by path and
  read the part you need when you need it.
- Run analyses as scripts that print only the numbers you need.
- Send exploration that reads many files to a sub-agent and ask for a short answer.
- When the context passes about 200k tokens at the end of a task, say so: I will start a new
  session with a short summary.
```

- **Design:** the data owner's next N sessions with the file, against the ten measured sessions
  (and any sessions without it in the same period). Not randomized: a before/after with stated
  confounders (task mix, model version).
- **Primary measure:** main-session input per instruction (median), from `pxt survey run`.
- **Secondary:** context per call, steps per instruction, share of authored content in residency
  (cycle A2's measure), restarts taken.
- **Outcome check:** the share of instructions whose result the data owner accepted without
  redoing it (one yes/no per instruction, recorded at the time), and test pass rates where the
  project has tests.
- **What would count against the levers:** more steps or more re-reads per instruction that eat
  the saving, or more redone instructions.

## E2 — Restart rule, controlled (needs a task set and a harness)

- **Tasks:** 20–40 multi-step coding tasks with automated checks (a public benchmark or a frozen
  set from the data owner's repositories), each long enough to pass 200k tokens of context. A
  candidate set is in `research/phase3/e2-taskset-v0.md`: 29 tasks from this repository's history,
  validated fail-to-pass, in 4 chains of 7 instructions (cycle D6).
- **Arms:** (a) one session throughout; (b) restart at an instruction boundary above 200k with a
  summary the agent writes; (c) the same with a 2k-token summary.
- **Measures:** input processed, cost, checks passed, steps; paired by task.
- **Pre-registered expectation from phase 2:** (b) saves about 55% of input if the summary suffices,
  52–55% with the re-reads seen after real compactions (cycle A5), 43% at the worst plausible re-read
  rate (4–19× the observed); 52–53% with a median real cold start (20–30k tokens of orientation, cycle B5). The experiment measures what the logs cannot: whether checks pass as often with about 150
  restarts as with 34 compactions.

## E3 — Pointer for authored content (needs a harness change or a convention)

- **Mechanism:** after a Write/Edit or a shell file write, the harness keeps only the path and a
  hash in the context; the agent reads the file again when it needs it. As a convention (no
  harness change), E1's first line approximates it.
- **Measures:** as E2; plus re-reads of written files and Edit failures (wrong old text).
- **Expectation from phase 2:** small. With compactions left where they were it would save 10–20%
  (cycle A2), but under today's ceiling alone about nothing (−4%), on top of a restart rule
  +1.6 points (+0.5 on top of restart and earlier compaction), and in cost it loses, because
  re-fetched content is written at 2× (cycle B3).
  Test it as an add-on arm to E2, not on its own.

## E4 — Compaction ceiling (needs a harness setting)

- **Arms:** compaction at about 780k (today) against about 390k and about 200k (the model's
  price-weighted optimum is 110–160k, cycles B4, E6).
- **Expectation:** about 39–44% less input at 390k and about 67% at 200k, after the observed re-reads
  (cycles D2, B3, B4); the experiment measures the one unknown, the quality cost of more frequent
  summaries (R in C\* = P + √(2g(P + R))),
  if the more frequent summaries lose nothing needed.

## Disclosures to ask for (no experiment needed)

1. Thinking tokens reported separately in usage (cycle C2: about half of the invisible third).
2. Final output tokens in remote-session event logs (they are stream-start placeholders today).
3. A usage record for the compaction call itself (cycle D2: none appears).

## What phase 2 still owes these experiments

- The blind labels (W4, W5, W8 detectors; whether error-only steps are verification).
- n > 1: other people's measurements with `pxt survey run`, so E1's baseline is not one person.
