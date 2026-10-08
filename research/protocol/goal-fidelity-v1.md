# Goal fidelity across compaction (pre-registration)

Status: **pre-registered 2026-10-08, before any of these measures was computed.** A change after results are
seen is v2.

## Question

Phase 2 found that the cost-optimal rule is to compact more often (cycle M1: compact at 150k, about ten times
as many compactions). The data owner's experience points to the side effect: after compaction, the agent
loses what was agreed early in the session and drifts. If compaction keeps what is recent and drops what is
old, then the cheap rule makes that worse. Two measures test this on the 34 real compactions in the ten
sessions.

## G1: what survives a compaction (recency bias)

- **Terms.** For each compaction, take the user instructions before it (the session's instructions, main
  session). From each instruction take its distinctive terms:
  - words of 4+ characters, or Hangul words of 2+ syllables, lower-cased;
  - not in a stop list;
  - not in more than 50% of the ten sessions' instructions.
- **Survival.** A term survives if it appears in the compaction's summary (the first message after the
  compaction that carries the summary).
- **Age.** Instructions are split into quintiles by position, from the session's start to the compaction.
  - Q1 is the oldest; it holds the initial goals and agreements.
  - Q5 is the newest.
- **Report.**
  - Survival rate by quintile, pooled over compactions (term-weighted and instruction-weighted).
  - The ratio Q1 / Q5, with a bootstrap over compactions (2,000 reps, seed 20261008).
  - The first instruction of the session on its own.
- **Recency bias is supported** if Q1 survival is less than half of Q5 survival, and the bootstrap 95%
  interval of the ratio stays below 1.

## G2: drift signals after a compaction

- **Instructions after a compaction.** These are the first three user instructions after each compaction.
- **Controls.** For each one, take up to three instructions from other sessions with no compaction in the 50
  previous calls, at the same session-position decile and with a context within ±25%.
- **Signals (fixed).**
  - (a) **Correction.** The `rules.detect_t3` outcome proxy says "not met" (correction, redo, undo or
    interrupt phrases).
  - (b) **Restatement.** At least 30% of the instruction's distinctive terms appeared in the session's Q1
    instructions and not in the previous 20 instructions. This is the user saying again something agreed
    early.
- **Report.**
  - The rate of (a), (b) and (a or b) after compactions against the controls.
  - The rate ratio, with a bootstrap over compactions.
- **A drift signal is supported** if the ratio for (a or b) is at least 1.5 and its 95% interval excludes 1.
  With n = 34 the test has little power, so a null is reported as "not shown", never as "no drift".

## Limits stated now

- Survival is lexical. A summary can keep a goal in other words, so G1 is an upper bound on loss. A summary
  can also name a term without keeping its constraint, so G1 is also a lower bound on loss. The two do not
  cancel, and both are reported.
- G2 sees only what the user typed. Drift the user did not notice, or fixed without words, is invisible.
- These are one person's ten sessions and one harness's summaries.

## What it decides

If both measures are supported, phase 2 states that recency-ordered compaction trades goal fidelity for cost.
It then proposes role-ordered memory (`research/phase2/brain-map.md`, §goal layer) as the hypothesis for phase
3. If neither is, the claim is reported as not shown, and the proposal stays a hypothesis without this
support.

---

## 한국어 요약

압축을 자주 할수록 싸지만, 압축이 최근 것만 남기고 초기의 목적과 합의를 잃는다면 싼 규칙이 그 부작용을 키웁니다. 실제 압축 34번으로 두 가지를 잽니다.
- **G1. 요약에 무엇이 살아남나.** 지시를 오래된 순으로 다섯 묶음으로 나누고, 각 묶음의 핵심 단어가 압축 요약에 남은 비율을 봅니다. 가장 오래된 묶음의 생존율이 가장 최근 묶음의 절반 미만이면 최신 편향이 있다고 봅니다.
- **G2. 압축 뒤 표류 신호.** 압축 직후 지시에서 사용자가 바로잡거나 초기에 했던 말을 다시 하는 비율을, 압축이 없던 비슷한 지시와 비교합니다. 1.5배 이상이고 신뢰구간이 1을 넘으면 신호가 있다고 봅니다. 표본이 작아서, 차이가 안 보이면 "보이지 않음"으로만 씁니다.
