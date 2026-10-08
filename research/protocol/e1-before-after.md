# E1: a user-level bundle, before and after (pre-registration)

Status: **approved by the data owner, 2026-10-06**, with one addition (the return rule below).
Committed before any "after" session exists. A change made after an after-session result has been
read is a new version, reported as such.

Design: `research/phase2/phase3-experiments.md` (E1). Code: `pickaxetax/survey/compare.py`, run as
`pxt survey compare`. Tests: `tests/test_compare.py`.

## The bundle (verbatim from phase3-experiments.md)

```
- After writing or editing a file, do not print its content again; refer to it by path and
  read the part you need when you need it.
- Run analyses as scripts that print only the numbers you need.
- Send exploration that reads many files to a sub-agent and ask for a short answer.
- When the context passes about 200k tokens at the end of a task, say so: I will start a new
  session with a short summary.
```

It goes into the project instruction file (for example `CLAUDE.md`) of every project the data owner
works in during the after period, and stays unchanged. Editing it ends the period.

**Return rule (added at approval, from cycle A6).** Beside the file, the data owner follows one habit:
on returning to a session after more than an hour away with a large context, start a new session
with a short summary instead of continuing. It is the data owner's rule, not a line in the file,
because the agent cannot see how long the break was. For each after session the data owner records
whether it began as such a return. Cycle A6 estimates this alone at about 15% of cost on the large
sessions (per-session median about 5%).

The after period starts when the file is in place in the first project and the data owner records
the date in the dataset's notes.

## Before set

`research/survey/user01/dataset-v2.json`: the data owner's ten measured Claude Code sessions
(token records from 2026-08-10 to 2026-10-05; 3 from local transcripts, 7 from event logs). 667 instructions with at
least one call, 16,181 main-session calls, 2,362 sub-agent calls.

| File | SHA-256 |
|---|---|
| `dataset-v2.json`, `pickaxetax.survey.dataset.digest` (sorted keys, no spaces) | `75f10a8309cf8eba76e942bbc798fe550e8a6851ee43c581ca200158d0ce1b69` |
| `dataset-v2.json`, file bytes | `638742a8bbf33522e1064641f09d48d9b23c9e8f4eda8ed7188698c5d52457b1` |
| `floor-t1.json` (the same ten sessions, 6,839,974,268 input in both), file bytes | `ae5f1ebb2336981786fe809c8129218a0200d1a66a61c123cf610ff651aadea2` |

The before side is passed as a folder holding `dataset-v2.json` as `dataset.json` and
`floor-t1.json` as `floor.json`, so that the floor-based measures are compared too.

## After set

Every session the data owner starts with the bundle in place, in order of start, measured with
`pxt survey run` (or the before set's event-log route for cloud sessions; the route is recorded per
session). No session is dropped. A session counts once it has ended.

## Primary measure

**Median main-session input per instruction**, pooled over all instructions of a side (each
session's `per_instruction.input`), after against before as a ratio, with a **90% percentile
bootstrap CI of the ratio** that resamples **sessions** with replacement on each side
(instructions are clustered in sessions), 2,000 resamples, seed 20261006. This is exactly what
`pxt survey compare BEFORE AFTER` prints and writes with `--out`.

Resolution, stated in advance: comparing the before set with itself gives 0.65–1.54. Drawing 5 or
10 of its own sessions as a mock after set gives a median CI of about 0.61–1.64 (5) and 0.67–1.52
(10). A ratio of about 0.6 or lower is needed before the CI can lie below 1; smaller changes will
read as inconclusive.

**Reading.** The upper end of the CI below 1: input per instruction fell. The lower end above 1:
it rose. Otherwise inconclusive, and the point ratio is not read as an effect.

## When the analysis is run

Not before the after set has **at least 5 sessions and 30 instructions**. No result is read before
then. The analysis is run once at that point and again at **10 sessions**. Both are reported. The
conclusion rests on the 10-session run, and the first run does not stop the experiment.
`pxt survey compare` prints a warning whenever either side is below 5 sessions or 30 instructions.

## Secondary measures (as `pxt survey compare` reports them, before / after / ratio)

- median context per call (pooled per-call series);
- median steps (main-session calls) per instruction;
- share of input carried from finished instructions (the dataset decomposition, `dataset.decompose`);
- compactions per 1,000 main-session calls;
- restarts taken, by proxy: instructions per session (mean and median);
- removable cost % (`floor.json`, codebook v1 T1) and re-reads of unchanged content (W1) per
  1,000 calls, only when both sides have a `floor.json`.

They get no CI and are read only through the rules below. The share of authored content in the
context (cycle A2) is not computed by this tool. If it is measured, it is reported beside the
other measures and not used in the reading.

## Outcome check

At the time, for each instruction in an after session, the data owner records one yes/no:
**accepted without redoing it** (no asking again, no undoing). Where the project has tests, whether
they passed at the end of the instruction is recorded too. Only counts leave the data owner's
machine. The before sessions have no such record, so the share is compared only with sessions
without the bundle that the data owner records the same way in the same period. If there are none,
the share is reported alone.

## What would count against the levers

1. The primary CI lies above 1.
2. More steps eat the saving. The median steps per instruction rises and (steps ratio) × (context-per-call
   ratio) ≥ 1, since input = steps × context (`synthesis.md` §1).
3. More re-reads eat the saving. W1 per 1,000 calls rises while the primary is not below 1.
4. More redone instructions. Proposed for the data owner's approval: the accepted-without-redo
   share is more than 10 points lower than in the same period's sessions without the bundle, with
   at least 30 instructions on each side.

## Confounders (not randomized)

This is a before/after comparison. Anything else that changed between the two periods moves with
the bundle. That includes task mix and projects, model version (`--out` lists the models per side),
Claude Code version and its compaction behaviour, and the measurement route (the before set is
mostly event logs). The data owner also knows the phase 2 results, which may change how they work
regardless of the file. The fourth line and the return rule work only if the data owner restarts. n = 1 person.

---

## 한국어 요약

실험 E1의 사전 등록입니다. 데이터 소유자가 2026-10-06에 승인했습니다. "이후" 세션이 하나도 없을
때 커밋합니다. 번들은 짧은 프로젝트 지시 파일 네 줄이고(위 원문 그대로), 기간 동안 바꾸지 않습니다. 승인 때 사용자 습관 하나를 더했습니다. 1시간 넘게 쉬고 돌아왔는데 맥락이 크면, 이어 가지 말고 짧은 요약과 함께 새 세션을 시작합니다. 에이전트는 쉰 시간을 알 수 없으므로 파일이 아니라 데이터 소유자의 습관이고, 세션마다 그렇게 시작했는지 적습니다. "이전"은
`dataset-v2.json`의 세션 10개입니다(digest `75f10a83…`, 위 표). 1차 지표는 지시당 주 세션 입력의 중앙값입니다. 이후/이전
비율과 그 90% 신뢰구간을 내는데, 신뢰구간은 세션 단위로 다시 뽑는 부트스트랩(2,000번, 시드 20261006)으로 구합니다.
`pxt survey compare`가 내는 값 그대로입니다. 신뢰구간 위끝이 1보다 작으면 줄었다고, 아래끝이 1보다 크면 늘었다고 읽고,
그 밖에는 판단하지 않습니다. 같은 데이터끼리 비교해도 구간이 0.65–1.54이므로, 비율이 0.6 근처보다 작아야 결론이 납니다.

이후 세션이 5개, 지시가 30개가 되기 전에는 결과를 보지 않습니다. 그때 한 번, 세션 10개에서 한 번 분석하고 둘 다 보고합니다.
결론은 10개 분석에서 냅니다. 보조 지표는 호출당 컨텍스트, 지시당 단계 수, 끝난 지시에서 넘어온 입력 비중, 1,000호출당 압축
수, 세션당 지시 수(재시작 대용), 그리고 양쪽에 `floor.json`이 있을 때 제거 가능 비용과 W1 재읽기입니다. 결과 확인으로는
지시마다 "다시 하지 않고 받아들였는가"를 그때그때 예/아니오로 적습니다. 지렛대에 불리한 증거는 네 가지입니다. 입력이
늘거나, 단계나 재읽기가 늘어 절약을 먹거나, 다시 한 지시가 늘어나는 경우입니다. 무작위 배정이 아니므로 작업 구성, 모델
버전, 도구 버전, 측정 경로, 데이터 소유자 자신의 의식 변화가 번들 효과와 섞여 있습니다.
