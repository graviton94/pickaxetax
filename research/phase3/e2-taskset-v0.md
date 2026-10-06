# E2 task set v0: restart rule, controlled, on this repository's own history

Status: **candidate set, not yet run; running it is the data owner's decision (it costs API usage).**
Built 2026-10-06 (cycle D6) from the history up to `1632e35` (dev). No model or agent was run. The
machine-readable list is `e2-tasks-v0.json` next to this file.

E2 (`research/phase2/phase3-experiments.md`) needs 20–40 multi-step coding tasks with automated
checks, each long enough to pass 200k tokens of context, run in three arms: (a) one session
throughout, (b) a new session at an instruction boundary above 200k with a summary the agent
writes, (c) the same with a 2k-token summary. This file proposes such a set, SWE-bench style, from
the `pxt` repository itself: **29 usable tasks, in 4 chains of 7 instructions** (plus one task that
fits no chain).

## 1. Selection rule

1. All non-merge commits with a parent on all refs (main, dev and the site branch): **104
   scanned** (the repository has 109 commits in all).
2. A candidate changes both **agent paths** and `tests/`. Agent paths are the files an agent would
   have to write: `pickaxetax/`, `site/`, `worker/`, plus the packaging and plugin manifests
   (`pyproject.toml`, `claude-plugin/`, `.claude-plugin/`), because some tests check versions there.
   **31 candidates.**
3. A candidate is **valid** if at least one test fails with the commit's agent paths reverted and
   passes at the commit (fail-to-pass, below). **30 valid, 1 not** (`e0b6ecb`, a site number
   switch whose test change does not fail on the old code).
4. **Excluded:** `27acb77`, the package rename: all 89 tests fail at the parent because the import
   path changes, not because of behaviour. **29 usable.**
5. No candidate needed a package that is missing here (`tiktoken` is the only missing optional
   dependency and no test needs it). Three tests need Node (≥ 18; v22 here): `test_parity` and two
   `test_contrib` cases.

## 2. Validation method

For every candidate commit C with parent P, in a `git worktree` (removed afterwards), with the
editable install of `pickaxetax` hidden so the worktree imports only its own code:

- **State A** = C with every agent path that C changes reverted to P (files C adds are removed).
  Everything else — tests, research data, protocol documents, docs, binary assets — is as at C.
- **State B** = C, run twice.
- Each state runs the **full suite** (`python -m pytest tests --continue-on-collection-errors`,
  junit XML, 300 s time box; a run took 1–10 s).
- **FAIL_TO_PASS** = tests passing in both B runs and not passing in A (a collection error counts as
  not passing). **PASS_TO_PASS** = tests passing in A and in both B runs.
- Results: no flaky test (B1 = B2 everywhere), no test failing or skipped at any C, no failures at
  any P. An earlier variant (P plus C's `tests/` only) gave identical fail-to-pass sets for every
  commit it covered (all but `9930703`, which landed during the scan), so no task's checks depend on the research data or documents in the same commit.

**Chain check.** For consecutive tasks, a second state was run: C_k with agent paths reverted to
C_{k−1} (the state an agent continuing from the reference solution would see). The fail-to-pass set
was the same as the single-task set at every boundary, plus one test at `8371c56 → cdfd09b` that
belongs to an intervening commit (handled by the upstream patch, below).

## 3. Tasks

Columns: files/lines changed in agent paths, in tests, and elsewhere (docs, research, data); size
class from agent-path lines (S < 100, M 100–399, L 400–999, XL ≥ 1000); fail-to-pass and
pass-to-pass counts; the bottom-up context growth estimate (section 5); chain. "thin" = the commit
message is a subject line only, so the statement says little; the visible tests carry the
specification (section 6).

| commit | date | agent f/lines | tests f/lines | other f/lines | size | F2P | P2P | est. growth | chain |
|---|---|---|---|---|---|---|---|---|---|
| `27acb77` | 2026-10-05 | 34/77 | 8/52 | 11/156 | S | 89 | 0 | 47k | excluded |
| `c4c435a` | 2026-10-05 | 6/1287 | 8/274 | 8/76 | XL | 2 | 89 | 61k | A |
| `2af0632` | 2026-10-05 | 10/636 | 1/243 | 6/46 | L | 15 | 91 | 52k | A |
| `21350c5` | 2026-10-05 | 21/1397 | 2/229 | 14/200 | XL | 10 | 106 | 74k | A |
| `931b16c` | 2026-10-05 | 2/340 | 1/97 | 14/694 | M | 7 | 116 | 55k | A |
| `10ce4dd` | 2026-10-05 | 12/691 | 3/213 | 9/167 | L | 15 | 121 | 72k | A |
| `b181c14` | 2026-10-05 | 2/59 | 1/11 | 4/855 | S | 1 | 136 | 44k | A |
| `5a0813a` | 2026-10-06 | 6/795 | 1/37 | 10/370 | L | 2 | 137 | 88k | A |
| `468ac8c` | 2026-10-06 | 8/707 | 2/44 | 2/64 | L | 3 | 139 | 56k | none |
| `327fd50` | 2026-10-06 | 13/156 | 2/36 | 12/214 | M | 4 | 140 | 68k | B |
| `ef5253d` | 2026-10-06 | 7/907 | 2/126 | 23/595 | L | 7 | 144 | 83k | B |
| `8371c56` | 2026-10-06 | 2/215 | 1/52 | 6/59 | M | 5 | 151 | 46k | B |
| `cdfd09b` | 2026-10-06 | 1/4 | 1/44 | 0/0 | S | 1 | 157 | 31k | B |
| `79a61c2` | 2026-10-06 | 3/78 | 1/49 | 1/16 | S | 2 | 158 | 43k | B |
| `800db44` | 2026-10-06 | 1/41 | 1/13 | 0/0 | S | 1 | 160 | 31k | B |
| `8cffe65` | 2026-10-06 | 2/52 | 1/16 | 1/24 | S | 2 | 160 | 44k | B |
| `9121d94` | 2026-10-06 | 1/9 | 1/10 | 3/38 | S | 1 | 162 | 39k | C |
| `c0c297f` | 2026-10-06 | 3/97 | 1/22 | 2/8 | S | 1 | 163 | 50k | C |
| `93b0f19` | 2026-10-06 | 3/256 | 2/55 | 2/1547 | M | 4 | 164 | 56k | C |
| `c8bf634` | 2026-10-06 | 1/37 | 1/13 | 3/373 | S | 1 | 168 | 41k | C |
| `18b551b` | 2026-10-06 | 3/195 | 2/56 | 4/65 | M | 4 | 169 | 52k | C |
| `e81796b` | 2026-10-06 | 2/90 | 2/25 | 21/999 | S | 3 | 172 | 85k | C |
| `d23f1af` | 2026-10-06 | 1/65 | 1/46 | 2/4 | S | 1 | 176 | 45k | C |
| `845b5fc` | 2026-10-06 | 6/98 | 3/148 | 13/744 | S | 10 | 175 | 99k | D |
| `a55c486` | 2026-10-06 | 1/36 | 1/15 | 6/375 | S | 1 | 184 | 54k | D |
| `0891d99` | 2026-10-06 | 1/31 | 1/12 | 6/224 | S | 1 | 185 | 54k | D |
| `a691b86` | 2026-10-06 | 2/48 | 2/64 | 7/252 | S | 8 | 184 | 63k | D (thin) |
| `3bfff85` | 2026-10-06 | 4/120 | 1/178 | 1/16 | M | 9 | 192 | 65k | D (thin) |
| `133d71b` | 2026-10-06 | 2/248 | 1/140 | 2/141 | M | 8 | 201 | 58k | D (thin) |
| `9930703` | 2026-10-06 | 2/9 | 1/124 | 1/18 | S | 5 | 209 | 52k | D (thin) |

Usable tasks by size: 15 S, 7 M, 5 L, 2 XL. Fail-to-pass tests: 1–15 per task, 134 over the 29.
The JSON holds every task's statement (written from the commit message only, as an instruction:
"Add X so that Y"), the test ids, and the per-area counts. Two examples:

- `cdfd09b`: "Make the parser for saved event pages tolerate raw control characters in tool output."
- `0891d99`: "Make `pxt survey whatif` sweep the compaction ceiling (100k–600k) and report the
  sawtooth model's optimum C* = P + sqrt(2g(P + R))."

## 4. Session chains

A chain is a run of consecutive valid tasks in history order. It starts from a fresh checkout of the
first task's parent; instruction k is task k's statement. Chains break where the history between two
tasks changes agent paths by a lot without tests (`5a0813a → 468ac8c`: 584 lines of site;
`468ac8c → 327fd50`: 270 lines), which leaves `468ac8c` alone.

| chain | start (checkout) | instructions | F2P | est. context after each instruction (k) | first boundary above 200k | upstream patches |
|---|---|---|---|---|---|---|
| A | parent of `c4c435a` | c4c435a, 2af0632, 21350c5, 931b16c, 10ce4dd, b181c14, 5a0813a | 52 | 81, 133, 207, 263, 335, 379, 468 | after 3 | before 2af0632: `9543886` (pyproject, 19 lines); before 931b16c: `259b565`, `f2cf1a4`, `fcd193e` (versions, worker deploy; 53 lines) |
| B | parent of `327fd50` | 327fd50, ef5253d, 8371c56, cdfd09b, 79a61c2, 800db44, 8cffe65 | 22 | 88, 172, 218, 249, 293, 325, 369 | after 3 | before cdfd09b: `05951a7` (events.py, 17 lines); before 8cffe65: `953109d` (report.py, 8 lines) |
| C | parent of `9121d94` | 9121d94, c0c297f, 93b0f19, c8bf634, 18b551b, e81796b, d23f1af | 15 | 59, 109, 165, 207, 260, 345, 391 | after 4 | none |
| D | parent of `845b5fc` | 845b5fc, a55c486, 0891d99, a691b86, 3bfff85, 133d71b, 9930703 | 42 | 119, 174, 229, 292, 357, 415, 468 | after 3 | none |

Every chain crosses 200k at a boundary with three or four instructions still to come, so arms (b)
and (c) restart at least once (by the estimate, A and D twice), and arm (a) peaks at 370–470k. That
is below the ~780k compaction point measured in phase 2, so arm (a) runs without a compaction —
**provided the harness uses a 1M-token context window**. With a 200k window, arm (a) would be
auto-compacted near 160k and would no longer be "one session throughout".

**Estimate basis.** Bottom-up, per instruction: the tokens of every file the commit touches as it
was at the parent (all read once) and of new test files, plus the added lines (written once), at
4 characters per token; plus 20k of output and reasoning (phase 2, C3: about 20k output per commit),
3 test runs at 1.5k each, and 5k of orientation (listing, grep); a 20k base for the system prompt and
tools. Per instruction this gives 31–99k, median 54k. The phase 2 measurements give a cross-check of
the same size: 25 API calls per commit (C3) × 1,925 tokens of warm context growth per call (B5) =
48k per commit. The estimate does not count re-reads, failed attempts or exploration beyond the
touched files, so real sessions probably grow faster and cross 200k earlier.

## 5. What the harness needs

1. **Checkout.** A fresh clone of the repository at the chain's start commit, with the
   dependencies of `pyproject.toml` and Node ≥ 18. A clean `HOME`; no transcript of an earlier run.
2. **Before each instruction k** the harness, not the agent:
   - syncs every non-agent path to C_k (`git checkout C_k -- <paths>` over the files that differ):
     the task's **tests** (visible to the agent), research data, protocol documents, docs, and
     binary assets (fonts, images) even when they sit under `site/`;
   - applies the listed upstream patches (agent-path changes made between two tasks in the real
     history, without tests) with `git apply --3way`; on a conflict it takes the reference version
     of those files and records the event.
3. **Instruction k** = the statement from the JSON, plus one fixed line: "The tests in
   `<task's test files>` describe the expected behaviour; make them pass without breaking the rest
   of the suite." Visible tests are the primary design because the commit messages do not name the
   functions the tests call (four statements are subject lines only). A hidden-test variant (tests
   copied in only for scoring) is a secondary option; it would mostly measure guessing interfaces.
4. **Arms**, paired by chain and replicate (same model, same harness version, same settings):
   - (a) one session for all seven instructions;
   - (b) at the first instruction boundary where the context of the last call is above 200k, the
     agent is asked, in the old session, to "write a summary for a new session that will continue
     this work: what was done, where, what is left, open problems" (no length limit; phase 2
     assumed about 10k); a new session starts with that summary followed by the next instruction.
     The rule applies again at later boundaries;
   - (c) the same as (b) with "in at most 2,000 tokens"; the harness truncates at 2k tokens if the
     agent exceeds it. The summary request and the summary count toward the arm's input.
5. **Scoring after each instruction**: copy C_k's test files over the agent's (the agent may have
   edited them), run the full suite, and record task k's FAIL_TO_PASS passed (of n), PASS_TO_PASS
   passed (of n), and also every earlier task's fail-to-pass tests in the chain (regressions). The
   agent's tree is not reset to the reference between instructions: a wrong earlier step is part of
   the outcome, the same in every arm.
6. **Logs**: the full transcript of every session (main and sub-agents) in Claude Code's JSONL format,
   kept per arm and chain, so `pxt survey run` can measure it.

## 6. Measures

Paired by chain and replicate, arms (b) and (c) against (a):

- **Input processed** (primary token measure): `pxt survey run <transcripts of one arm>` gives
  the dataset (per-call context, input per instruction); `pxt survey compare <arm a> <arm b>` gives
  the ratio with a bootstrap interval over sessions. Arms (b) and (c) include their summary calls and
  every new session.
- **Cost**: the same run's price-weighted input (`floor.json`, `total.price_total_units`: cache
  reads, writes and uncached input at their relative prices), times the model's price for dollars.
- **Checks passed** (primary quality measure): share of fail-to-pass tests passing after their
  instruction, share of instructions with all fail-to-pass passing, and pass-to-pass breaks;
  separately for instructions before and after the first restart.
- **Steps**: API calls and tool calls per instruction; re-reads of files already read before the
  restart; wall time.
- **Pre-registered expectation** (phase 2): (b) saves about 52–55% of input if the summary
  suffices. On these shorter sessions the bottom-up model gives less: about 43% for (b) and 45% for
  (c) (section 7). What would count against the rule: fewer checks passing after a restart than in
  (a) at the same instruction.

## 7. Cost of a run (tokens)

| | arm (a) | arm (b) | arm (c) | one replicate (3 arms) |
|---|---|---|---|---|
| bottom-up model, 4 chains (28 instructions) | 159M | 90M | 87M | **335M input tokens** |
| phase 2 rate, 7.5M input per commit (median, C3) | 210M | ≤ 210M | ≤ 210M | **≤ 630M** |

The bottom-up model spreads each instruction's growth over 25 calls and charges every restart a 20k
base, the summary (10k or 2k) and a 26.8k cold start (B5 median). Per chain, arm (a): A 40.9M,
B 38.4M, C 33.7M, D 45.6M. The phase 2 rate comes from sessions whose average context was about
300k, so it is an upper figure for these. In cache-weighted terms, phase 2's 0.92M cost-equivalent
per commit gives about 77M cost-equivalent tokens per replicate. Three replicates (to see run-to-run
spread at n = 4 chains) cost about 1.0–1.9B input tokens. A pilot of one chain in arms (a) and (b)
costs about 60–105M.

## 8. Caveats

- **Contamination.** The repository is public. The model may have seen these commits, their code and
  their tests; it can then recall rather than solve, which raises pass rates in every arm. It does
  not favour one arm by design, but recall may survive a restart better than reasoning does. Check
  by asking the model, before the run, to reproduce a few of the test files from their names; report
  the result.
- **One project, one author, one domain.** All tasks are from this repository (Python survey and
  analysis code, a static site, a worker), written over two days. Results
  do not carry to other code bases without another set.
- **Small n.** The unit of pairing is the chain: 4 chains. Instructions (28) are nested in chains,
  so per-instruction tests need clustering. Replicates measure run-to-run spread, not new tasks.
- **Estimates are not measurements.** Context growth is estimated from file sizes; real sessions
  read more. If a chain does not cross 200k in arm (a), its pair adds nothing to E2 and is reported
  as such.
- **Statements are short and some are thin.** They come from commit messages only. The visible tests
  carry the specification; this makes the tasks easier than an issue-only benchmark and makes "checks
  passed" partly a measure of reading tests.
- **Later tasks depend on earlier ones.** A divergent earlier solution can fail later tests that
  assume the reference interface. The scoring records this; analysis should also report each
  instruction conditional on the previous ones passing.
- **Harness-supplied files.** Syncing research data, documents and upstream patches between
  instructions changes files under the agent; an agent holding the old content in context (arm a)
  sees stale text. This mirrors working in a team repository, but it is a difference from a clean
  task.
- **History moved during the build.** Three commits landed on dev while the scan ran; the set is
  frozen at `1632e35`.

## Reproduction

The mining, chain check, size estimate and assembly scripts were run from a scratch folder (not in
the repository): they create a worktree, run the suite in the states above and write the JSON. The
JSON records the selection and validation rules and the estimate constants.
