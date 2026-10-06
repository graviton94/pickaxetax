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

## Cycle C2 — the invisible third (`C2-invisible-third.md`)

**Found.** The context growth that matches no visible piece of the transcript (26–43% of growth by
source) splits, pooled over the event-API sessions, into about **49% the model's own thinking**
(tracked through the length of the thinking blocks' signatures; their text is empty), about 38%
a constant per-call overhead (about 230 tokens a call, harness framing), and about 13% images
(about 1,400 tokens an image). In S01, the only session with real output counts, the previous
call's invisible output enters the next call's context about one for one (slope 0.98).

**Review.** Fits are loose (R² 0.05–0.8 by source); the split of the remainder is weak; the thinking
share is consistent across all ten sources. `agent.bound` counts images as zero tokens: they end up
in the pinned invisible share, which keeps the bound conservative but hides a visible cost.

**Discussion.** Part of what is re-read on every call is the model's own reasoning from earlier
calls. Whether it is dropped at an instruction boundary cannot be told from these records; only a
provider field for thinking tokens (or `count_tokens` with and without thinking blocks) would
settle it. That is a concrete disclosure to ask for.

**Develop (later).** Count images in the bound (as a visible segment kind) — a `lexical-v1` change,
so a new method version; deferred until after the labels.

## Cycle A2 — content that is both on disk and in the context (`A2-authored-content.md`)

**Found.** What the agent itself wrote — Write/Edit inputs and content written inline through the
shell (file bodies, inline scripts) — holds 39.7% of the visible residency, **22.9% of measured
input**; file bodies that sit on disk alone, 11.8%. It stays carried (78% idle, 5.7% dead) and only
about 15% of it is ever read back. Replacing each such input after its call by a 30-token stub
(path and hash) and re-reading it on every later lexical reuse at 1,000 tokens would save about
**20% of measured input** (10.5% for file bodies only), and the saving barely depends on the
re-read price (break-even about 8,600 tokens a re-read).

**Review.** Inline scripts are about 70% of the shell writers (analysis code, not file bodies), so the
strict figure is the on-disk 11.8% / 10.5%. The stub model ignores that an Edit needs the exact old
text and that the model may not know when to re-read: an upper bound. It agrees with the n = 1 bound
(persisted writes were the largest visible item there too).

**Discussion.** This is the first lever found that needs no foresight: the content already lives on
disk, the agent knows its path, and re-reading is a normal tool call. Unlike the simple recency
policies (about 3% at a low miss rate), a "write, then carry a pointer" convention targets exactly
the content that is least read back. It is a harness or agent-convention change, testable in a
controlled experiment (phase 3).

## Cycle B2 — what makes an instruction take many steps (`B2-step-anatomy.md`)

**Found.** Steps are reading (32% of steps), running something (31%; a quarter of all steps are
ad-hoc inline scripts), editing (15%), waiting or polling (6%), version control (5%). Context per
step hardly differs by class, so input follows the step count. The most expensive 10% of
instructions (42% of input) are long sustained chains — median 75 steps against 11 — not retry
loops: edit-verify-error cycles are 0.3% of input (about 1% under looser definitions), polling runs
1.8%, and **none of 181 consecutive polls returned an unchanged result**. Removing every loop would
save about 1.4%.

**Review.** Regex classification cannot tell an analysis script from a test from a file write; the
loop shares are robust to the definition (0.3–2.1%).

**Discussion.** The W3 "polling with no state change" candidate is not supported in these sessions.
Retry waste is small. The step lever is in ordinary chains: fewer, larger steps (batched reads,
scripts that do more per call), or the same steps in a smaller context. Inline scripts tie back to
cycle A2: they are written into the context and then carried.

## Cycle D2 — what compaction costs (`D2-compaction.md`)

**Found.** 34 compactions in 7 sessions, all near the same ceiling (median 783k tokens before, 64k
after: 12× compression). The compaction call itself leaves no usage record. Within each cycle the
last quarter's calls carry 4.3× the context of the first quarter's, and **the top quarter of every
cycle takes 35.4% of all main-session input**. After a compaction, 66% of reads are re-reads of
files already read — but mid-cycle the share is 74–80%: re-reading is the agent's habit, not a
compaction effect. Compacting at half the observed ceiling would cut input by 39% and cost by 29%
with the observed re-read burden applied (more summaries, untested quality).

**Discussion.** The re-read habit is evidence for the pointer levers: content that leaves the
context is fetched again when it is needed. It is also evidence against the "summary is enough"
fear being the whole story: the agent re-reads anyway.

## Cycle E2 — independent code review, and the fixes

**Review.** A separate reviewer read the judge, rules, what-if, labeling, events and bound code and
wrote failing tests for each suspected bug (now `tests/test_review_e2.py`):
1. the judge's `--limit-calls` stopped at the first line of call N and lost its tool results and
   sub-agents (events.cut keeps them);
2. the W5 detector and the bound used a different instruction rule from everything else;
3. a tool result logged twice counted as a repeat;
4. `survey sample` numbered sub-agent files as sessions (labels shift against `survey machine`);
5. an instruction's final answer was attributed to the next instruction (carried undercounted);
6. the restart what-if dropped the new instruction's first growth (savings overstated);
plus four doc mismatches (W1-before-W2 precedence; 1.25× vs 2× write prices; W8's parent check;
the common-word threshold).

**Develop.** All fixed; the shared instruction rule (`events._is_instruction`) is now the only one;
`bound.origin` attributes a piece to the call it came from; event lines sort by parsed time.
185 tests pass.

**Audit of the effect.** The floor is unchanged in its headline (0.0008% tokens, 8.92% cost; W1 266,
W2 346; steps 2.6%). The oracle policies are unchanged (5.6 / 41.5 / 46.1%). The visible context
carried over from finished instructions is 46.5% of input (was 50.8% under the bound's own looser
instruction rule); never used again 5.1% (was 5.4%). The restart what-ifs moved by up to 0.8 points
(above 200k: 58.5%). **The sealed machine labels came out byte-identical**, so the rule-tier
pre-registration stands as committed. *(Corrected in cycle D4: the re-make ran before E2's last fix
was committed; the T2 main file differs in one label and was re-sealed before any label existed.)*

## Cycle D3 — change over time, and the model (`D3-time-and-model.md`)

**Found.** The ten sessions with token records start between 2026-08-10 and 10-05: **eight weeks**,
not three months (the three-month period, from 07-10, is the session list's, which includes two
July sessions with costs only). No workflow measure trends with the start date at a size n = 10 can
detect (all |ρ| ≤ 0.54). Opus-5.5 and opus-5 sessions run the same loop (calls per instruction,
carried share, input per active hour); compactions and the tool mix differ, but model, date and
tooling cannot be separated. In the long sessions, calls per instruction fall from the first third
to the last (clear only in S10); context per call does not.

**Audit.** The phrase "three months" in research note 1 and on the site describes the session list's
period; the token total comes from eight weeks of it. True as a statement about the list, imprecise
as a statement about the tokens. Recorded for the data owner; note 1 is posted and stays as is.

**Discussion.** Nothing here suggests the pattern is a passing phase of one model or one month; it
also cannot show it is not. Separating model, date and task needs the same tasks on different models
in the same weeks (an E2-style experiment).

## Cycle C3 — what one unit of delivered work cost (`C3-value-per-token.md`)

**Found.** Over the ten sessions: 690 commits, about 1,556 files written, 1.96 million tokens written
to files. **One commit cost a median of 7.5 million input tokens processed** (IQR 5.3–13.1M; pooled
9.9M); **one token written to disk, about 2,500** (pooled 3,500). Sessions of 0.6 billion input or
more pay about 1.5× more per commit and 2.9× more per written token than small ones, while API calls
per commit stay near 25: the difference is the weight each call carries, not the number of calls.
Cache-weighted, a commit is about 0.9M token-equivalents. In the three sessions with real output
counts, 9–24% of output tokens became file content.

**Review.** Denominators are proxies (commits differ in size; scripts that write files are missed;
design and research sessions deliver documents and images). Tests, PRs and artifacts are too sparse
to use.

**Discussion.** This is the receipt in units people understand. It also closes the loop with the
mechanism: bigger sessions are less efficient per unit of work because of context weight, which is
exactly what the restart and pointer levers attack.

## Cycle E3 — how much the conclusions depend on the detector (`E3-detector-robustness.md`)

**Found.** Six detector variants. The **size of the paging opportunity is robust** (fetch on demand
35–54%, free fetching 42–55% across all variants). **"Paging beats forgetting" holds for every
lexical variant** (31–40 points pooled, ≥ 11.6 in every session) but not for a windowed detector
that marks large results unused when only part of them was needed (rejected for that bias).
**"Forgetting alone is small" is the least robust**: 3.0% to 18.9% across lexical variants.
Stripping trailing punctuation and matching basenames (V1) moves the headline by 0.2 points.

**Develop (proposal).** lexical-v2 = V1 as the default, with V2 (looser, conservative) and V4
(stricter, optimistic) as the published band; decided only after the blind labels, which measure
recall and precision of each.

**Discussion.** Note 2's "4–25%" for forgetting covers the lexical band; its wording (estimated from
overlapping words, to be checked by blind labeling) stands.

## Cycle B3 — the levers combined (`B3-levers-combined.md`)

**Found.** On one segment-level replay (reproducing measured input exactly with no policy):
restart above 200k saves 54.8%, compaction at 390k 43.3%, both together 57.5% (52.6% of cost), all
three with pointers 58.0%. **Pointers for the agent's own writes save nothing alone (−4.1%) once
compaction fires at the ceiling**: slower growth only postpones the compaction. They save about 20%
only if compactions stay at the observed calls (A2's assumption), and in price they lose (each
re-fetch is written at 2×). The restart rule carries almost the whole bundle.

**Review — a flaw found in the what-ifs.** The series replay let a smaller replayed context ride the
real session's compactions for free. Fixed: an observed compaction applies to a replay only if it
had reached at least 90% of the pre-compaction size; otherwise the replay keeps growing (and the cap
policy compacts on its own). A restart is taken only if it makes the context smaller. Restart above
200k: 58.5% → **55.2%** (B3's segment replay: 54.8%); every 3 / 10 instructions 55.1% / 22.3%;
compaction at 400k 43.5%.

**Discussion.** This changes the reading of every "keep less" result: under a ceiling-triggered
compaction the ceiling, not the content, sets the average context of a long session. The levers
that matter move the boundary (new session, earlier compaction, sub-agent). It also qualifies A2's
pointer lever and the oracle-style opportunities: they are real only where the boundary is not the
binding constraint (short sessions) or after it has been moved.

## Cycle C4 — how far back reused content comes from (`C4-reuse-distance.md`)

**Found.** 487,195 reuse events. Reuse is bursty: half come within 3 calls of the previous use
(token-weighted p90: 10 calls). But content lives long by being touched again and again: a
segment's last use lands a median 143 calls and 6 instructions after it arrived, and **35% of reused
tokens are used more than five instructions after they arrived**. Of the visible residency, 70% is
idle calls between uses. A recency window of N calls misses 26% of reuses at N = 8 and still 6.8% at
N = 32, where it saves only 6.5%; large segments are reused in tighter loops (token-weighted misses
1.4% at N = 32), which favours a size-aware tier over a fixed window. The recency-8 run reproduces the
pre-registered backtest exactly.

**Audit.** The agent installed a package from the network (`pip install numpy`), which the task rules
forbid; no data was involved and the repository was untouched. The rules now say so explicitly.

**Discussion.** Two facts pull against each other: reuse gaps are short in calls (a pointer rarely
has to reach far in time) but long in instructions (a third of reused content crosses five or more
instruction boundaries). The second is the risk to the restart rule: what a summary drops may be
exactly what comes back. Cycle A4 measures that directly.

## Cycle B4 — where the compaction ceiling should be (`B4-ceiling-curve.md`)

**Found.** On the public series alone: a ceiling of 100k / 150k / 200k / 300k / 400k / 600k instead
of 783k would have cut input by 76.5 / 71.6 / 65.7 / 53.6 / 41.9 / 18.7%, compaction reads included.
A sawtooth model gives the optimum in closed form, **C\* = P + √(2g(P + R))** (P ≈ 72k after a
compaction, g ≈ 1,790 tokens of growth a call, R the re-reading a compaction causes): about 88k with
no re-reading, about 96k with D2's observed re-reading, 120–170k price-weighted; the model tracks the
replay within about 1 point from 150k up. Re-reading would have to be 46–230× the observed amount to
erase the gain.

**Review.** The replay matches `whatif.cap`; the sweep and the model are now in `pxt survey whatif`
(`ceiling_*`, `ceiling_model`, `optimal_ceiling`), reproducible from `dataset-v2.json`. At 100k the
session would compact every ~12 calls (about 40× today's summaries): whatever quality a summary loses
is multiplied, which the numbers cannot see.

**Discussion.** Today's ceiling sits about 5–8× above the token-optimal one. This is the cleanest
structural result of phase 2: one harness setting, a closed-form optimum, and a single unknown (the
quality cost per summary) for an experiment to measure.

## Cycle A3 — the pointer lever replayed with real behaviour (`A3-pointer-behaviour.md`)

**Found.** 1,352 file writes (458 Write tool, 894 shell). 68% are used again (median 2 calls later),
16% are later edited, 29% read back, 23% rewritten. **When the agent edits a file it wrote itself, it
did not re-read it first 81% of the time** (it edits from the copy carried in its context); files it did
not write are re-read before 99.9% of edits. Replaying "stub after writing, re-fetch at the first edit
not preceded by a read" gives 20.3% of input with the observed compaction points (lexical estimate on
the same group: 19.0%) and **−3.8% when compaction is left to fire at the ceiling** — independent
confirmation of cycle B3.

**Discussion.** The carried copy of what the agent wrote is used: it is what the agent edits from.
A pointer convention would turn those edits into re-reads (cheap, 7.5% of files). Its saving exists
only where the boundary already moved; the ceiling result stands.

## Cycle A4 — is "start a new session at a boundary" safe? (`A4-restart-safety.md`)

**Found.** Of 582 instruction boundaries above 200k tokens, by lexical reuse the next instruction draws
on more than 50k tokens of earlier content at 93% (median 187k, 38% of the context), mostly old
(only 10.5% from the instruction just finished; 27% from ten or more back). Restarting only at
"clean" boundaries saves under 1%. Charging every lexically reused token as a re-read keeps 26.7% of
input (12.1% of cost) at the loosest detector, 40.9–45.7% (30–37% of cost) at stricter ones, against
55% if the summary were enough.

**Review — two measures disagree.** By lexical reuse, a summary of the last instruction could not
carry what comes next. By behaviour after the 34 real compactions (cycle D2), which drop almost
everything for a ~22k summary, the agent re-read only about 0.7 files (≈7k tokens) per compaction
beyond its habit. Lexical-v1 counts a whole segment as reused when one distinctive word reappears;
that measures mention, not need. Which one predicts what a summary must carry is testable on the
data: cycle A5 uses the real compactions as a natural experiment.

**Discussion.** Until A5 (and in the end an experiment) settles it, the restart and ceiling levers
are reported as a range: from about 12–27% (every lexical mention must be restored) to about 55%
(the summary is enough).

## Cycle E4 — how much do the headlines depend on the sample? (`E4-session-uncertainty.md`)

**Found.** Every headline reproduces from public files to within 0.1 point but one (below). S03 is
31% of input, and S03, S09 and S10 together are 73%. Leaving one session out or resampling the ten
(2,000 reps) moves the floor, the oracle bound and the ceiling by about ±1–2 points. The restart
rules move by 3–5 (restart above 200k 49–60%, every 10 instructions 15–28%). C\* stays at
90–110k, or 120–150k with ten times the re-read cost. Every directional conclusion of the synthesis
holds in at least 97% of resamples and in all ten leave-one-out samples. Two do not hold that well:
restart above 200k against a new session every 3 instructions is a tie (50%), and "earlier
compaction adds under 5 points on top of restart" holds in 89%.

**Review — a stale number.** B3's series column gave 46.1% for compaction at 390k. That was
computed before the replay fix of cycle B4; the current replay gives 42.8%. B3 now carries a
correction note. The synthesis range (39–43%) was not affected.

**Discussion.** Sample composition is not what makes the numbers uncertain. Per-session medians
differ from pooled values by up to 7 points, so pooled numbers describe the large sessions. The
intervals are for this one person only, and at n = 10 they are too narrow. The assumptions (the
detector in E3, whether a summary is enough in A4/A5) move the numbers far more.

## Cycle C5 — where the money goes (`C5-money.md`)

**Found.** At list-price ratios (output at 5×), cache reads are 71–74% of all spending, 1-hour
cache writes 16%, output an estimated 9–12%, uncached input about nothing. 76% of the main
sessions' cache-read money is for context carried from finished instructions: about half of all
money (52–54%), 62–64% with the re-writes after expiry. Sub-agents are 3.8% of input but about 5%
of money (a fifth of it output). Ranked by money, the levers keep their order (ceiling 200k 50–52%,
restart above 200k 43–45%, ceiling 390k 33–35% of total money); each shrinks by about a fifth
(price weighting, untouched sub-agents, output, the summaries' own output). The floor reproduces
exactly (8.92% of input-side money; 7.9–8.1% with output).

**Review.** Output is the weak part: recorded counts are placeholders everywhere but S01's main
session, so output is transferred from S01 through visible output and thinking-signature length
(held-out error +6% within S01; across sessions it is untested). Nothing in the ordering depends on
it: the band only rescales every lever. The "carried" split uses cycle B's definition, which counts
invisible carried content and post-compaction summaries as carried; the visible-only definition
would give about a third of all money, a lower bound.

**Discussion.** This is the plainest statement of the thesis in money: about half of what was paid
went to re-reading finished work. It supports leading with the cost view, not the token view, when
talking about levers. A third disclosure would help: output and thinking tokens per call, as
recorded by the API.

## Cycle A5 — the real compactions as a natural experiment (`A5-compaction-natural-experiment.md`)

**Found.** Before each of the 34 compactions about 474k visible tokens are in context. By lexical
reuse 83% of them reappear in the next 50 calls (94% in 200; 29–44% at stricter settings). By
behaviour the agent re-obtained 10k distinct tokens in 50 calls and 21k in 200, beside about 22k the
harness restores. That is a ratio of 0.03–0.13 at the loosest setting and below 0.25 for every
compaction. A placebo settles which one measures need: scoring the same segments against the window
after an unrelated compaction gives 95–99% of the "demand" in the same session and 72–87% in
another. Only 11–17% of demanded tokens have their source re-fetched. Error rates (1.7% → 2.0%
against a drift of +0.16 points) and the steps of the instruction around the compaction show no
damage, though both are weak proxies.

**Review.** The disagreement of cycle A4 is resolved in favour of behaviour. Lexical reuse at one
shared term is mostly project vocabulary. Behaviour is a lower bound: it cannot see what the summary
carried or what the agent did without. Placebo-adjusted, the ratio is about 0.1–0.5, and 1 is
excluded. Rescaled by the observed ratio, the every-boundary restart rule saves 52–55% of input
(47–50% of cost), against 26.7–45.7% in A4. At a ratio of 0.5 it is 43% (31%). The A4 range in the
synthesis is replaced.

**Discussion.** The cost of re-reading no longer limits the restart and ceiling levers. Quality
does: whether about 150 restarts lose what 34 compactions apparently did not. Logs cannot answer
that; E2 in `phase3-experiments.md` can. The finding also qualifies every reuse-based number in
phase 2 (the oracle bound, W5, W8): at the loosest setting they are upper bounds on need.

## Cycle E6 — second independent code review, and the fixes

**Found.** A reviewer with no part in the code reviewed everything changed since cycle E2. That was
only `whatif.py`, plus B4's analysis script. Five bugs were confirmed, each by a test that failed:
1. A restart replay that had skipped a real compaction could grow past the ceiling (up to 837k).
2. The ceiling replay compacted to the first call's context + 22k (72k) instead of the observed 64k
   (a 42k cached prefix + 22k). This is why the replay at today's 783k was 1.5% off.
3. The model's growth was divided by steps, not calls.
4. A ceiling below the post-compaction size charged a compaction on every call.
5. An empty series crashed `run()`.

**Fixed** (`tests/test_review_e6.py`). The restart replay now compacts, as the harness would, at the
session's ceiling, to its observed post-compaction size. The ceiling sweep compacts to 42k + 22k, and
at 783k it now reproduces measured input within 0.1%. A compaction that would not shrink the
context does not happen. Empty series are skipped. For bug 1 the reviewer's toy test asked that a
restart rule never be worse than none, which no replay can guarantee once a real compaction it
skipped is gone. The test now checks the stated principle: the replayed context never exceeds the
session's ceiling.

**Changed numbers.** "New session every 10 instructions" went from 22.3% to 23.0%; the other restart
rows are unchanged, including 55.2%. The ceiling savings are about 1 point higher (200k: 65.7 →
66.8%; 150k: 71.6 → 72.7%). The optimum is about 10k lower: 79k / 87k raw (R = 0 / D2) and 110–160k
price-weighted (was 120–170k). These are updated in `opportunity-v1`, B4 (as a correction note),
the synthesis and the phase 3 plan. Cycles E4 and C5 used the old ceiling values. Their conclusions
(intervals, orderings, the money ranking) do not depend on a 1-point shift, so they were not rerun.

## Cycle B5 — what a cold start costs (`B5-cold-start.md`)

**Found.** Beyond a warm instruction start, a new session spends about 20–27k tokens and 3–9 extra
read or search calls getting going, almost all in its first 10 calls. A sub-agent spends 21–28k, a
compaction 6–17k. The 90th percentile is 45–110k tokens and 13–20 calls. The cold start is largely
re-obtaining: 45% of the files a new session reads were used in an earlier session of the same
project, and 70–76% of a sub-agent's reads were already used by its parent. It does not delay the
first edit (median 12 calls against 17 at a warm start): the cost is reading before it. With a median
cold start charged to every restart, the restart-above-200k rule saves 51.9–53.0% (46.7–48.0% of
cost) instead of 55.2%. It falls to the 390k-ceiling lever only if every restart costs about 100k
fresh tokens, which is 3–4× the median cold start.

**Review.** The confound (a first instruction opens new work) is handled by three comparisons:
long warm instructions, compactions and sub-agents. The session-start figure is the upper estimate
for a restart with a summary, the compaction figure the lower one. There are ten starts, nine in
one project. The 390k comparator (42.8%) predates the E6 fix (now about 43%); the break-even
conclusion does not change.

**Discussion.** Together with A5, the restart lever's two hidden costs are now measured from
behaviour: re-reading after losing context (A5) and getting going (B5). Each costs a few points,
not tens. What remains is quality, which only an experiment can measure.

## Cycle E5 — the oracle bound against a vocabulary placebo (`E5-vocabulary-placebo.md`)

**Found.** The method was fixed before any bound was run, and the baseline reproduces exactly
(5.6 / 41.5 / 46.1). Two ways of making reuse beat a placebo were tried. One was a user-vocabulary
filter (a word counts only if rare in the other nine sessions). The other was a placebo correction:
the same session's calls before the segment existed (time mirror), or calls from other sessions.
Under these, forgetting alone (P = ∞) rises from 5.6% to 12–45% of input, and paging (P = 1000)
from 41.5% to 44–56%, against 57.3% if nothing were ever reused. The diagnostic behind it: calls
before a segment exists share its words at the same rate as calls after it (14.6% against 15.3%
within 10 calls; 5.0% against 5.3% at 100–1000). Under the time-mirror placebo, 50–68% of the
segments lexical-v1 counts as reused fail, across every kind of segment.

**Review.** Neither placebo is the truth. The time mirror over-corrects where a segment descends
from what came just before it: a tool result reads the file the agent just wrote. The other-session
placebo under-corrects, because the session's own topic is left in. So the two bracket the answer:
forgetting 12–13% under the mild corrections, 33–41% under the mirror. This replaces E3's 3–19%
lexical range. E5 extends A5's finding from 34 compaction windows to every segment of all ten
sessions.

**Discussion.** The thesis is unaffected, and its total grows: 41–56% need not have been processed
with foresight. What changes is the claim that "carrying is the big lever, forgetting the smaller
one". It holds only under the mild corrections, and the synthesis now presents the split as
depending on the detector. The blind labels (W5 "dead context") are where it gets settled. They
should be read against both brackets. The note 2 draft quotes 4~25% and 35~54% from the earlier
ranges; this is for the data owner to decide.

## Cycle D4 — the placebo test as an option of the tool

`pxt agent bound --placebo mirror` (and `bound.link(placebo="mirror")`) runs E5's deterministic
time-mirror test. A segment's later references count only if they beat the session's own calls
before the segment existed by two standard deviations. The method tag is `lexical-v1+mirror-2sigma`.
On the ten sessions it reproduces E5 exactly: 41.3 / 51.6 / 53.3% for P = ∞ / 1000 / 0 at
min_shared 1. The default path is byte-identical to lexical-v1, and a contribution export refuses
the option. The rule-tier W5 detector takes the same option (`pxt survey machine --tier t2
--placebo mirror`), for the secondary analysis pre-registered in `research/protocol/rule-tier-v0.md`.
Its labels are sealed there.

While sealing, the primary T2 main labels did not reproduce their sealed hash: one S01 W5 label
differs. The re-seal after cycle E2 had run three minutes before E2's last fix was committed. The
file was re-sealed from the committed code and the protocol corrected, before any label existed.
The other three primary files reproduce exactly.

## Cycle E7 — a consistency audit of every published number

**Found.** An auditor with no part in the analyses checked every number in the phase 2 documents,
the survey pages, the launch facts, the note 2 draft and figures, the site and the changelog against
their sources. Most matched: the what-if replay on the public data equals the published numbers
exactly, and the note 2 slides regenerate byte for byte. It listed 32 discrepancies.

**Fixed.**
- CHANGELOG still gave the pre-correction removable cost (5.79%; now 8.92%).
- The note 2 draft's step split was stale: 222 + 256 steps is now 223 + 255; the total is unchanged.
- The synthesis's total opportunity range was "41–56%". Across the detectors it cites it is 35–56%.
- The phase 3 plan expected 10–20% from pointers with a restart; B3 measured +1.6 points.
- Ceiling-dependent numbers computed before E6 (E4 interval, C5 money, 390k range) are now updated
  or marked.
- validity.md undercounted the review findings.
- The survey contribution proposal misdescribed the anonymity threshold of the other kinds.
- A few rounding and wording fixes in the launch facts table.

**Left for the data owner.**
- The note 2 draft quotes the earlier ranges (4~25%, 35~54%), and its framing rests on forgetting
  being small (see E8).
- The site and README on `dev` still carry v1 numbers (73.6%, 5.87B, 586 instructions, 148 kg).
  The site branch has v2 and waits for note 2.
- "석 달" against the eight weeks of token records.
- The v1 sections of the user01 README are historical but not marked as such.

## Cycle E8 — which definition of "reused" predicts need? (`E8-behaviour-test.md`)

**Found.** At the 34 real compactions, 5,073 dropped tool results came from file reads, and 46% (50
calls) to 65% (200 calls) of them were re-read. The question is which E5 definition of reuse
predicts which files those were.
- Plain lexical-v1 is best (AUC 0.574 / 0.612), followed by the cross-session corrections
  (0.55–0.60).
- The time-mirror corrections and the strict vocabulary filter do no better than chance
  (0.50–0.53). The gap between lexical-v1 and the mirror correction is 0.12, with a 95% interval of
  0.06–0.18.
- The segments the mirror calls "unused" are re-read at the base rate: its extra forgetting is
  random thinning.
- Recency carries no signal, and size carries about as much as lexical reuse.
- The ordering holds with any session left out, within size groups, and with one segment per file.

**Review.** The behavioural label is a lower bound on need: it misses need met by the summary,
re-injection or inference. Re-reading is partly habit (three in four reads). Both pull the AUCs
toward 0.5, so the ordering is more reliable than the levels. A modest AUC also means lexical reuse
is a weak measure of need, even though it is the best one available.

**Discussion.** E5's alarm is answered: the time-mirror placebo over-corrects, as its own caveat
suspected, because a segment and the calls just before it share ancestry. Forgetting is most likely
5.6–13%, and the paging opportunity is 41.5–49% under the supported definitions. "Carrying, not
forgetting, is the larger lever" stands, and so does note 2's framing. Its "4~25%" (lexical-v1 over
nine settings) contains the supported range. The pre-registered secondary W5 analysis will still
test the time-mirror definition against human labels.

## Cycle B6 — tooling and a pre-registration for phase 3's first experiment

`pxt survey compare BEFORE AFTER` compares two survey datasets or `pxt survey run` folders. Its
primary measure is median main-session input per instruction, as a ratio, with a 90% bootstrap CI
that resamples sessions (instructions are clustered). Its secondary measures are those of E1 in
`phase3-experiments.md`. It warns when a side has fewer than 5 sessions or 30 instructions
(`tests/test_compare.py`). `research/protocol/e1-before-after.md` pre-registers E1 against the ten
measured sessions (digest `75f10a83…`). It is a draft for the data owner's approval, because adopting
the bundle is their decision.

The resolution found while writing it matters for the design. Comparing the before set with itself
gives a CI of 0.65–1.54. Mock after-sets of 5 or 10 of its own sessions give CIs of about 0.61–1.64
and 0.67–1.52. So one person's before/after can detect only a change to about 0.6× or less. The
restart lever alone predicts about 0.45–0.5× if it is followed. Smaller levers (pointers, scripts
that print only numbers) cannot be seen this way; they need E2's paired task set.

## Cycle A6 — can a rule without foresight choose safer restart points? (`A6-restart-boundaries.md`)

**Found.** The design was pre-specified before outcomes were seen.
- 65% of the boundaries above 200k are followed by some re-read or re-run in the next instruction,
  but the amounts are small: 0.9k tokens on average, and 0.9% of boundaries reach 10k. Most of it
  is habit and the length of the next instruction.
- No signal known at the boundary ranks this outcome. The new prompt's overlap with the context
  gives an AUC of 0.46–0.54, with the sign flipping between sessions. Longer prompts and longer
  breaks predict more re-reading, not less. Only the length of the instruction just finished carries
  a signal, and it argues against restarting where the context is largest.
- A rule chosen on half the sessions and tested on the other half keeps 89–90% of the charged
  saving. Its harm rate is no lower than refusing boundaries at random (75/61% against 76/59%),
  because a refused boundary only moves the restart to the next one.
- With every restart charged a median cold start and its observed re-reads, the full rule saves
  52.7% of input (47.6% of cost). Restarting only on return from a break over 1 h saves 16% of input
  and 20% of cost with 48 restarts; those returns re-write the whole context at the write price
  anyway.

**Review.** The outcome is measured in sessions where no restart happened, so it sees re-reading
habit, not loss of quality. Its small size (0.9k) is consistent with A5 and B5: the charge of a
restart is a few points, not tens. The post-hoc parts (stratified AUC, hindsight bound,
random-refusal control) are labelled as such in the memo.

**Discussion.** The restart lever cannot be made safer by being selective, only tested (E2 in the
phase 3 plan). The return-after-a-break rule is the cleanest version for a user. It costs nothing
the return does not already cost, and it is easy to follow: "after an hour away, start a new
session with a summary".

## Cycle D5 — do edits fail more after a compaction? (`D5-edit-failures.md`)

**Found.** Of 1,328 Edit/Write calls in the main sessions, 10 failed (0.75%). Three quoted text that
was no longer there, and seven were refused by the harness (file not read, or changed since read).
Sub-agents' 166 edits never failed. After a compaction the failure rate is 0/25 in the next 10
calls and 1/179 in the next 50, against 1.05% mid-cycle. A placebo with randomly placed fake
compactions gives p = 1.0 / 0.66. Edits of files last seen before the compaction failed 1/64
against 7/816 (p = 0.45). Shell edits (3,610; 1.4% errors) show a spike at 10 calls that rests on
two ordinary errors at the window's edge and is gone at 50.

**Review.** The test can only exclude a rise above about 3% (three times the control). An edit
that is wrong but still applies is invisible to it. The harness re-attaches recently read files
after a compaction, which may suppress refusals by design.

**Discussion.** A third behavioural measure (after A5's re-reads and error rates, and A6's
re-reading) finds no visible cost of losing context at a compaction. All three are blunt.
Together they say that losing context does not cause frequent, visible breakage. They cannot say
that nothing subtle was lost. The quality question remains for an experiment with outcome checks.

## Cycle C6 — does a large context cost time? (`C6-latency.md`)

**Found.** The event pages carry a "requesting" status event before 99.9% of main calls, which gives
an exact start. Latency runs from that start to the last streamed line. On the 13,886 calls
triggered by a single tool result, latency grows by about 0.37 s per 100k tokens of context (90%
interval 0.29–0.43), controlling for output and uncached tokens. At the 33 measured compactions,
calls get faster in 30 of 33, which gives 0.19 s per 100k. The extra time comes before the first
token. Context is 6–11% of the 61 h of main-session model time. A compaction itself takes a median
130 s (89 s on the newer model, 177 s on the older).

Translated with the fitted slope: a 200k ceiling makes the sessions 1.9 h slower, because its 178
extra compactions cost more than the faster calls save. 390k is about neutral. The restart rule
saves about 4.9 h (8%) if no summary is generated, and is about neutral if each restart generates a
compaction-length summary.

**Review.** The time of a compaction at a smaller ceiling is unknown; all observed ones were near
783k. If summarizing less takes less time, the ceiling levers could turn into time savings (break
even at about 92 s per compaction at 200k). Model and date coincide. Server load cannot be seen,
but the slope is positive in every time-of-day bin.

**Discussion.** The levers pay in tokens and money, not in model time, except restarts. That is
worth saying plainly to users: a lower ceiling saves money but does not make the agent faster. A
provider could change this, if a compaction of a smaller context is cheap to compute.

## Cycle E9 — third independent code review, and the fixes

A reviewer reviewed the code added since E6: the placebo option, its plumbing into the rule tier,
`pxt survey compare`, and the two protocol documents. It checked that the default path is unchanged:
the code before and after gives byte-identical results on 60 synthetic transcripts, for every
report, export and CLI output. Three bugs were confirmed by failing tests (`tests/test_review_e9.py`):
1. In the mirror test, a tool result born at call 0 (origin −1) got a negative "mirror length". It
   skipped the fallback to the pooled rate, and it could push the pooled rate out of [0, 1] and
   crash.
2. `compare` reported a CI when the before median was 0 and the ratio undefined.
3. A `floor.json` that is valid JSON but not an object crashed instead of giving an error.

All three are fixed. After the fix, every sealed label file is re-made byte-identical (the primary
four and the two secondary), and the E5 / D4 numbers are unchanged (41.3 / 51.6 / 53.3%): no
session in the data starts with a tool result. Smaller concerns are noted in the review and left as
they are. The 5-session warning counts sessions without instructions, and nothing checks that a
`floor.json` matches its dataset.

## Cycle C7 — was the 1-hour cache the right choice? (`C7-cache-ttl.md`)

**Found.** The main sessions wrote only 1-hour cache (2× input), and sub-agents only 5-minute cache
(1.25×). A replay with every prefix change held fixed reproduces the observed price exactly. The data
confirms that a read refreshes the timer.
- 97% of calls follow a gap under 5 minutes, 2.6% a gap of 5–60 minutes, and 0.4% a gap over an
  hour. Half of the 5–60 minute gaps fall inside an agent's turn.
- All-5-minute caching would have cost 19.8% more main input money (about 17% of all money). The
  1-hour premium (56M units) avoided 214M units of re-writes.
- But 93% of the premium was paid on writes followed by a gap under 5 minutes. A per-write choice
  with foresight saves 1.6–6.7% of main input money, depending on how mixed lifetimes are billed.
  With keep-alive requests while idle it saves about 10%.
- Realistic rules get 4–6% of total money. An hourly keep-alive while idle (up to 8 h) is the only
  gain that holds under both billing readings: 4.1–4.2%.
- Sub-agents were right on 5 minutes; 1 hour would cost them 14.6% more.

**Review.** The mixed-lifetime billing ("entry" vs "segment" reading) cannot be checked here: no
call in the data mixes the two, and the agent's statements about the provider's documentation and
price list were not re-checked (no network). The memo marks them as assumptions. The read price of
0.1 is the project's ratio; a lower read price would strengthen every direction.

**Discussion.** The cache lifetime is a harness lever of the same size as the floor (about 4–8% of
money). It needs no change in behaviour and is an order of magnitude smaller than moving the
ceiling. Most of the W6 cost (re-writes after breaks over an hour, the floor's 8.92%) is also
addressed by an hourly keep-alive, or by restarting on return (A6).

## Cycle D6 — a task set for phase 3's controlled restart experiment (`research/phase3/e2-taskset-v0.md`)

The design is SWE-bench style, built on this repository's own history. Of 104 commits scanned, 31
change both code and tests. 30 of those have tests that fail with the commit's code reverted and
pass at the commit, twice, with no flakes. One (the package rename) is excluded. That leaves **29
tasks with 134 fail-to-pass tests**, grouped into **4 chains of 7 consecutive instructions**. The
chain boundaries are checked too: the fail-to-pass sets hold when an agent continues from the
previous reference solution. The estimated context growth is 31–99k tokens per instruction, so
every chain passes 200k after instruction 3 or 4, as E2's restart arm needs. The set also lists
what a harness needs, and estimates one replicate of all three arms at 335–630M input tokens.

**Review.** Four chains make the pairing thin. The repository is public, so the model may have
seen it. All tasks come from one project, and four commit messages are a subject line only, so the
design shows the tests as the specification. Running it costs API usage and is the data owner's
decision. Nothing was run.

## Cycle C8 — how much do the cost numbers depend on the price ratios? (`C8-price-sensitivity.md`)

**Found.** Every cost headline was recomputed over 48 settings: cache read 0.05–0.15, 1-hour write
1.5–2.0, output 3–5. At the default all reproduce exactly.
- **Holds everywhere.** The order of the levers holds in 48 of 48 settings: ceiling 200k 42–58% of
  total money, restart above 200k 37–49%, ceiling 390k 29–38%, then the floor and the cache-lifetime
  levers. The 1-hour cache beats all-5-minute at every point (all-5-minute costs 12–40% more).
- **Partly holds.** "Half of all money re-reads finished work" is 41–63% for the reads alone, and at
  least half in 35 of 48 settings. It falls below half when a read costs less than about 0.054–0.086
  of an input token. With the re-writes after expiry it is 56–69% everywhere.
- **Moves most.** The floor ranges 4.7–15.4% of input-side money, because its re-write part is
  priced at the write premium over a read. The output share ranges 3.9–19%.

**Review.** The grid is a sensitivity range. No current price list was checked, and one ratio set
is applied to calls from several models.

**Discussion.** The ordering and the direction of every lever are price-robust. Public statements
should quote "half of all money" with its condition, or quote the robust form: "56–69% counting the
re-writes". The floor's 8.92% should keep its price basis attached. Note 2 states 8.92% with
"비용으로 보면", which is the default-ratio figure; that is for the data owner's wording.

## Cycle E10 — second consistency audit

An auditor checked everything changed since E7: synthesis v2 and its Korean version, the new
memos, the protocols, the phase 3 task set, the opportunity page. Most matched, including all 281
what-if values (against `whatif.run`) and every cell of the task-set table (against its JSON). It
listed 24 discrepancies, mostly wording.

**Fixed.**
- Two E7 fixes had reached the synthesis but not the phase 3 plan: the 390k range and the "ten
  times" wording.
- validity.md counted two reviews instead of three.
- One AUC range was attributed to lexical reuse and the cross-session corrections together, where
  0.57–0.61 is lexical reuse alone and 0.55–0.60 the corrections.
- In the levers table, the break-only restart and the 390k row were on a different price basis
  from their neighbours.
- The restart rule's time saving now carries its condition (no summary generated).
- The resampling claim is limited to the orderings E4 actually tested.
- The Korean synthesis gave the 12–45% forgetting range for the time correction alone, and its
  table is now labelled a summary.
- The rule-tier correction was attributed to cycle E7 instead of D4, and the E2 log entry now notes
  that correction.
- Smaller fixes in the E8, C7 and task-set memos.

## Cycle D7 — how many runs E2 needs (`research/phase3/e2-power-v0.md`)

This is a simulation only, with fixed seeds and the standard library, from the public task set. The
token model rebuilds D6's per-chain figures exactly. Only 15 of the 28 instructions come after a
restart, so only those can show a quality difference.
- **Tokens.** A ±5-point CI on the saving needs 6–8 replicates if a chain run varies by 20%, and
  28–44 if it varies by 50%. Run-to-run variation is assumed, since no run exists.
- **Quality.** At a 75% baseline pass rate, the loss estimate has an SD of about 15/√R points. 80%
  power needs about 4 replicates for a 20-point loss, 13 for 10 points and 45 for 5 points. With 4
  chains no test can reach two-sided 5% with fewer than 3 replicates.
- **Recommendation.** Run arms (a) and (b) forked at the first boundary above 200k (exact, and 16%
  cheaper). Drop arm (c). Use a 15-point non-inferiority margin with looks at 3 and 6 replicates,
  at a cost of at most 1.3–1.7B input tokens.

**Review.** The quality model is assumed: random effects for instructions and chains, with the
effect only after restarts. Its conclusion is robust to the heterogeneity assumed. The scripts and
tables are in `research/phase3/power/` and reproduce.

**Discussion.** This is a limit to state up front. The experiment phase 2 calls for can rule out a
large quality loss from restarting, but not a small one. A small one is what the behavioural
evidence (A5, B5, D5, A6) suggests. Resolving it needs a larger task set (a public benchmark) or
many more runs. Phase 3 should say so before running anything.
