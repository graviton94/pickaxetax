# Mechanical judging with behavioural checks (replaces the human blind labels)

Status: **adopted by the data owner, 2026-10-06, before any main-round label existed.** This page
changes how the codebook's categories are judged and checked. Its rules and pass criteria are fixed
here, before the one human check it keeps (below) is made.

## Why the human blind labels were withdrawn

The practice round of the blind labeling (`labeling.md`, `labeler-guide-ko.md`) showed that people
could not do it. The labelers reported three problems:
- the categories were hard to tell apart;
- the items were long and many (median 12 steps, 41 of 200 items above 30);
- the user's intent was unknown (the median instruction is 72 characters).

A check of the packet found a fourth, decisive one: for six of the eight categories the screen held no
evidence. The page shows each tool call's name, target and result length, not its result. So W1, W3,
W4, W5, W6 and W8 could at best be answered "unsure". The main round was not run. Practice labels are
not used for any estimate.

## How each category is judged now

| Category | Rule (all mechanical) | What checks the rule | Reported as |
|---|---|---|---|
| W1, W2, W6 | mechanical tier v1 (`mechanical-tier-v1.md`, amended for images) | the rules are operational definitions | the floor, as published |
| W4 discarded output | rule tier v0 detector (sealed) | an operational definition (file events) | detector rate |
| W3 coordination loss | `rules.detect_t3` (W3): a sub-agent result its parent never quotes (fewer than 2 distinctive words in later output), an errored delegation, or polling with identical results | the parent's later output | detector rate |
| W5 stale context | rule tier v0 detector (sealed) | **behaviour**: files actually re-read after the 34 real compactions (phase 2 cycles E8, A7: lexical reuse predicts re-reads, AUC 0.57–0.61) | the behaviour-calibrated range (forgetting about 6–13%) |
| W8 over-exploration | rule tier v0 detector (sealed) | **behaviour** (pre-registered here, not yet run): of the exploration results the detector flags, the share whose file is edited later in the same or the next instruction, or whose path appears in the final answer. That share is an upper bound on its false-flag rate | detector rate with that share |
| W7 unrequested work | `rules.detect_t3` (W7 proxy): the next instruction carries an "unrequested" or "undo" signal (yes), or acceptance/progress without one (no); otherwise unsure | **the data owner's check** (below) | see the decision rule |
| Outcome met | `rules.detect_t3` (outcome proxy): correction/redo/undo/interrupt in the next instruction → not met; acceptance or a new topic without one → met; otherwise unknown | **the data owner's check** (below) | see the decision rule |

The proxies' exact phrase lists and rules are in `pickaxetax/survey/rules.py` (`detect_t3`), with
tests in `tests/test_rules_t3.py`. Over the ten sessions the proxies' rates are:
- W3 yes 0.1%;
- W7 yes / no / unsure 1.5% / 14.9% / 83.6%;
- outcome met / not met / unknown 73.1% / 11.4% / 15.5%. Most "met" calls come from the new-topic
  rule (407 of 499), the weakest signal.

## The data owner's check (30 items)

Only the data owner knows what they asked for, so the intent categories are checked by them on a small
sample. Owner bias is a known limit.

- **Packet:** 30 instructions from the ten sessions with at most 15 steps and an instruction of at
  least 10 characters (354 eligible), drawn by `build_packet` (seed 20261008, stratified by session
  and size). They are selected by length only, never by any detector's answer. It asks W7 and the
  outcome only. Digest `3cc9a24ce8f92e5b…` (the file stays private).
- **Sealed machine labels** (tier t3, made before the owner's labels; SHA-256 of the file, JSON with
  sorted keys and no spaces): `1889437c53679f7e908602e6aa37890b06b03a403fc7561b237c59917a3a7c16`.
- **Method:** the data owner labels on the labeling page, without seeing the next instruction or any
  machine label. The comparison is `pxt survey agreement owner.json machine-t3.json`.

**Decision rules, fixed now.** Owner "partial" counts as "not met". "Decided" means the proxy said
met / not met (outcome) or yes / no (W7).
- **Outcome proxy usable** if it decides at least 70% of the 30 items and agrees with the owner on at
  least 80% of the items it decides. Then the ten-session outcome rates are published with the
  agreement attached. Otherwise only the owner's own rate on the 30 items is published, with a Wilson
  95% interval.
- **W7 proxy usable** on the same two thresholds (50% decided, 80% agreement). Phase 2 expects it to
  fail, because it decides only about one instruction in six. Otherwise W7 is published as the
  owner's yes rate on the 30 items, with a Wilson 95% interval, and the proxy rate is labelled
  unvalidated.
- No threshold is changed after the owner's labels are seen. Any later rule is a new version, checked
  on a new sample.

## What this changes elsewhere

- `rule-tier-v0.md`: the W4, W5 and W8 detectors and their sealed labels stand. The comparison with
  human consensus labels, including W5's pre-registered secondary analysis against the time-mirror
  placebo, cannot run and is withdrawn. Phase 2's behaviour test (E8) answered that secondary
  question instead: behaviour favoured lexical reuse over the time-mirror correction.
- Public wording: numbers are "judged by pre-registered rules and checked against behaviour" (W5,
  W8), or "against the data owner's 30-item check" (W7, outcome). They are not "human-validated".

---

## 한국어 요약

블라인드 판정은 연습 단계에서 중단했습니다. 판정자들이 곤란했던 이유는 세 가지였습니다. 갈래 구분이 어렵고, 항목이 길고 많고, 의도를 알 수 없었습니다. 더 근본적으로는 화면에 근거가 없었습니다. 여덟 갈래 중 여섯은 화면만으로 판단할 수 없었습니다.

대신 모든 갈래를 규칙으로 판정하고, 규칙은 사람 대신 행동으로 점검합니다.
- W5(묵은 맥락)는 실제 압축 뒤 다시 읽은 파일로 점검합니다.
- W8(과잉 탐색)은 읽은 파일이 나중에 고쳐지거나 답에 나왔는지로 점검합니다.
- W1·W2·W6·W4·W3은 정의 자체가 규칙입니다.

의도가 필요한 W7(요청 밖 작업)과 결과 충족만 데이터 주인이 짧은 항목 30개로 직접 확인합니다. 기계 판정은 그 전에 봉인했습니다. 통과 기준은 미리 고정했습니다. 기계가 판정한 항목이 충분하고(결과 70%, W7 50% 이상), 그 항목에서 주인과 80% 이상 일치하면 그 대리 지표를 씁니다. 아니면 주인의 30개 표본 비율만 신뢰구간과 함께 냅니다.
