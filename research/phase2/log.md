# Phase 2 research log (autopilot, started 2026-10-06 16:00 UTC)

Phase 2 is the long measurement phase: how the waste and the structure behind it arise, in enough
depth that the solution phase starts from mechanisms, not impressions. Every cycle runs
**do → review → audit → ideation → discussion → develop** and is logged here with what was found,
what was challenged, and what changed. Numbers only; no conversation text.

Constraints: nothing that needs human judgment (blind labels), the data owner's browser, outside
APIs or permissions. Results that rest on unvalidated detection say so.

## Agenda (wave 1)

| # | Question | Data |
|---|---|---|
| A | Context anatomy: what fills the context, and how concentrated is it (largest tool results)? | transcript lines (private), `agent.bound` |
| B | Position in the session: do later instructions cost more, and what would a user-level restart rule save? | `dataset-v2.json` series (public) |
| C | Idle and return: gaps, cache lifetimes, the cost of coming back, and "compact before leaving" | transcript lines (private) |
| D | Sub-agents: does delegating save the main context, or move the cost? | transcript lines (private) |
| E | Audit: reproducibility from a clean checkout, threats to validity, code review | repository |

---

## Cycle E1 — audit (2026-10-06 16:05)

**Do.** Clean clone of `dev` in a fresh virtualenv: 173 tests pass; `report-v2.html`, the what-if
numbers and note 2's figure HTML are reproduced byte for byte from the public files. The T1
floor and the oracle bound need the private transcripts and can only be re-run by the data owner.

**Audit (threats checked on the data).**
1. *Event pages truncating large tool results?* No sign: maximum result lengths vary by session
   (2k–66k characters) with no cluster at a cap.
2. *Instruction split differs between event pages and local transcripts* (S02 49 vs 48, S03 299 vs
   275): the extra ones are ordinary text messages; the dataset keeps the in-session counts.
3. **Cache-write price was wrong.** The main sessions wrote almost only **1-hour** cache
   (`usage.cache_creation.ephemeral_1h_input_tokens`; sub-agents use 5-minute writes). A 1-hour
   write costs 2× uncached input, not 1.25×. The judge now prices each call's writes by the split
   it records. **Removable cost: 5.79% → 8.92%**; sensitivity 0.73–8.92% (within the cache's
   lifetime only: 1.90%). Interpretation changes too: with a 1-hour cache, the 26 re-writes within
   an hour are not expiry but a changed prefix.

**Develop.** `judge.PRICE` has 5-minute and 1-hour write prices; `input_parts` reports both;
W6 carries `price_units` per cause; the sensitivity view sums them. Docs, note 2 (text and
figures), the review kit and the facts table follow.

## Cycle A — context anatomy (`A-context-anatomy.md`)

**Found.** Shell commands hold about two thirds of the visible residency (other shell commands
47%, read-only shell commands 20%); the Read tool only 3.6%. Tool inputs are 32% of residency,
much of it whole files written through the shell. The top 10% of segments hold 56% of
residency. Capping tool results at 2k / 5k / 10k tokens (re-fetching the rest on reuse) would
save only 4.4% / 1.5% / 0.3%. The invisible share (about 30% of growth) is flat across context
sizes.

**Review.** The agent's parsing copy reproduced `bound`'s segment and call counts in every
session. Idle and dead shares inherit the unvalidated lexical detection.

**Discussion.** "Trim big outputs" is a weak lever here: cost is spread over thousands of
mid-size pieces, not a few giant ones. The invisible third behaves like a per-call overhead
proportional to growth (thinking, framing), not a hidden store that grows with the session.
What the agent writes through the shell is carried as input for the rest of the session: the
same content then lives on disk and in the context.

**Ideation.** (i) An agent convention that writes files without echoing their content into the
context (pass a path, not the payload). (ii) Measure how much of tool-input residency is file
content written through the shell (next wave).

## Cycle B — position in the session (`B-session-position.md`)

**Found.** Later instructions cost more per call (about 250–290k context for instructions 1–3,
about 420k from the fourth on) but not more per instruction, because they take fewer calls:
87% of the variance in an instruction's input is its number of calls. A user-level rule
"start a new session with a short summary at an instruction boundary once the context passes
200k tokens" would have cut 58.6% of main-session input (13 restarts per session), if a 10k
summary were enough; every 3 instructions gives the same with more restarts.

**Review — a bug found.** `whatif.task_scoped` pinned the replay at base + summary after an
actual compaction inside an instruction, dropping the growth after it: about 4 points too
optimistic (75.6% → 71.2% at a 2k summary). Fixed: `whatif.restart` replays growth call by
call, and `task_scoped` is `restart(every=1)`. The opportunity page's what-ifs were recomputed.

**Discussion.** Steps, not only context size, drive cost: the same report said so for v1 and
it holds per instruction. The restart rules are the first lever a user can pull today without
any new tool; their weak point is the summary assumption, which only an experiment can test.

**Ideation.** A controlled experiment for phase 3: the same tasks run with and without a
restart-above-200k rule, outcome checked by tests. Needs the data owner (later).

## Cycle C — idle and return (`C-idle-return.md`)

**Found.** 79% of calls come within 30 s of the previous one and the 1-hour cache almost always
survives gaps under an hour; nothing survives gaps over an hour. Returns after more than five
minutes are 3% of calls but 13.2% of input-side cost, because the context at return is large
(median 489k). The 1-hour cache already avoids about 26.5% of cost compared with a 5-minute
cache. "Compact before leaving" (resume from a 30k summary after breaks over an hour) would
save up to about 29% of cost, mostly through the smaller context of the calls that follow, not
the return itself.

**Review.** Consistent with the judge after the price fix (re-writes after the lifetime: 7.3% of
cost; within it: about 1.9–2.0%).

**Discussion.** The idle problem is a context-size problem in disguise: a return is expensive
because what is re-written is huge. The same lever as cycle B (a smaller context) explains most
of the "compact before leaving" gain.

## Cycle D — sub-agents (`D-subagents.md`)

**Found.** 76 sub-agent runs (S01, S02, S03, S09). A run reads about 27k tokens (median) and
returns about 475 to the main session, but processes about 116 times what it reads, because it
re-reads its own growing context. Against the counterfactual "the main session had received the
same reads", delegation was 1.4× cheaper pooled and cheaper in half of the runs; if the main
session also had to take the sub-agent's steps itself (at main-session context size), delegation
was 5.1× cheaper and won in every run. Runs of 11–50 calls paid off most; runs over 50 calls
(14, all in S09) did not, and hold over half of all sub-agent input.

**Review.** 34 of 76 returned results were not visible (background runs whose result arrives as a
notification); they were imputed from the observed median; observed-only runs give 1.49×. The
two counterfactuals bracket the truth: the first undercounts the main session's extra steps.

**Discussion.** The saving comes from the size of the context each step re-reads (about 110k for a
sub-agent call against about 490k for a main call), not from the summary. Delegation is a
"small context" lever, the same mechanism as restarting (cycle B): what costs is steps × context.
Long sub-agent runs re-create the problem inside the sub-agent.

**Ideation.** A single model for every lever: input = Σ over calls of context. Rank the levers
(restart, delegation, earlier compaction, trimming outputs, forgetting, paging, simple online
policies) on that one scale, with the assumption each one rests on (wave 2 synthesis).
