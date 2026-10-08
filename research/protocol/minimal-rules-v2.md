# Minimal rule set v2: a reflex arc and a mode switch (pre-registration)

Status: **pre-registered 2026-10-08, before any replay of R8 or R9.** It extends v1
(`minimal-rules-v1.md`), whose result is cycle M1: the set is {R3, compact at 150k}. v1's engine, prices,
charges, keep rule and validation are reused unchanged. Only what is new is written here. A change after
results are seen is v3.

## Why

`research/phase2/brain-map.md` sorts the phase 2 inefficiencies by where a rule acts in
input = steps × average context. Two mechanisms were left unmeasured. Both remove or shrink steps that need
no deliberation, so the replay can bound them.

| Rule | Inspired by (analogy only) | Rule shape |
|---|---|---|
| R8 | spinal reflex arc (bypasses the cortex) | a fixed check after an edit runs without a model step |
| R9 | neuromodulation (arousal sets the gain of many circuits) | less thinking in mechanical steps |

## R8: reflex arc (checks after an edit run as a hook)

- **Check commands (fixed list, R8a).** A shell call whose command, after leading `cd …&&` and environment
  assignments, starts with one of:
  - `pytest`, `python -m pytest`, `python3 -m pytest`;
  - `npm test`, `npm run (test|lint|build|typecheck|format)`, `npx (eslint|prettier|tsc|vitest|jest)`;
  - `ruff`, `black`, `isort`, `flake8`, `mypy`, `eslint`, `prettier`, `tsc`;
  - `go (test|vet|build)`, `cargo (test|check|build|clippy)`, `make (test|lint|check|build)`.
- **Eligible call.** A main-session API call that:
  - wrote no text;
  - holds only R8a tool calls;
  - follows, in the same instruction, a call that holds an edit tool (Edit, Write, MultiEdit, NotebookEdit).
- **Effect.** The call disappears: its input, its tool-call text and its unattributed growth. Its results
  stay, because a hook would inject the same output into the next call.
- **Assumption, reported as such.** A hook would have run the same command at the same point. So this is an
  upper bound on what a post-edit hook can remove.
- **Sensitivity.**
  - R8b adds state reads: `git (status|diff|log|show)`, `ls`, `wc`.
  - The edit precondition is dropped.

## R9: mode switch (less thinking in mechanical calls)

- **Mechanical call.** A main-session call that wrote no text and whose tool calls are all reading tools
  (Read, Grep, Glob, LS, NotebookRead) or R8a/R8b commands.
- **Thinking estimate.** Thinking is not reported separately in usage. Cycle C9 put it at about 40% of the
  unattributed growth, so a call's thinking is taken as 0.4 × its positive unattributed growth.
- **Effect.** In mechanical calls, half of that thinking (primary) or all of it (upper bound) is not
  written. The context that carries it shrinks from that call on.
- **Money.** The removed thinking is also removed from output at the output price (5), in the C5 money
  measure only. The B3/B4 price model has no output term and is unchanged.
- **Assumption, reported as such.** Less thinking changes nothing else, including quality. Phase 3 (E2) is
  where that is tested.

## Selection and report (as v1)

- **Selection.**
  - R8 and R9 join the pool; R1 to R7 stay in it.
  - Forward selection is re-run from the empty set, with v1's keep rule (≥ 2 points input and ≥ 1 point
    price) and v1's odd/even session validation.
- **Report.**
  - Each new rule alone, and its marginal contribution on top of {R3}.
  - Steps removed per instruction.
  - The sensitivities above.
  - A session bootstrap of whatever set is chosen.

## Expectation (stated so it can fail)

- **R8.** It removes steps, which is an addend. Each step it removes is cheap once R3 keeps the context small.
  Expected: alone 1–5% of input, and on top of {R3} under 2 points, so it fails the keep rule.
- **R9.** Thinking in mechanical calls is a small share of growth. Expected: alone under 2% of input, and on
  top of {R3} under 1 point.
- **The chosen set stays {R3}.** If R8 or R9 joins it, the expectation is falsified and reported so.

## Also run now: the W8 behaviour check

It was pre-registered in `mechanical-validation-v1.md` and has not been run. Of the exploration results that
the sealed rule tier v0 W8 detector flags, it measures the share whose file is edited later in the same or
the next instruction, or whose path appears in the final answer of the instruction. That share is an upper
bound on the detector's false-flag rate. The detector rate is published with it.

---

## 한국어 요약

v1의 결론({15만에서 압축})에 두 규칙을 더해 다시 고릅니다.
- **R8 반사궁:** 편집 직후의 테스트, 린트, 포맷 실행을 모델 걸음 없이 훅이 처리한다고 보고 그 걸음을 뺍니다.
- **R9 모드 전환:** 글 없이 읽기와 점검만 하는 걸음에서 생각을 절반(상한은 전부) 줄입니다.

엔진, 비용, 남기는 기준(입력 2%p, 비용 1%p), 세션 절반 검증은 v1과 같습니다. 예상은 둘 다 R3 위에서 기준 미달입니다. R8은 덧셈 자리이고, R3이 맥락을 이미 작게 만들기 때문입니다. 둘 중 하나라도 남으면 예상이 틀린 것으로 보고합니다. 등록만 해 두었던 W8(과잉 탐색) 행동 점검도 함께 돌립니다.
