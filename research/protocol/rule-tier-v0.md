# Rule tier v0: candidate detectors, fixed before the blind labels

Codebook: `waste-codebook-v1.md` (§2 T2, §5.5). Code: `pickaxetax/survey/rules.py`, written out
per packet item by `pxt survey machine --tier t2`. Tests: `tests/test_rules.py`.

The codebook's rule tier needs detectors whose accuracy is measured against blind human labels
before any of their numbers are published as waste. For that measurement to mean anything, the
rules and their yes/no thresholds have to be fixed **before** any consensus label exists. This
page and the commit that adds it are that record. A rule changed after the labels are seen is a
new version (v1), reported as such, and checked on a fresh sample.

## Detectors (per instruction)

| Category | Score | "yes" when |
|---|---|---|
| **W5 Stale context** | Tokens carried over from a finished instruction and resident after their last lexical reuse, summed over the instruction's main-session calls (`pickaxetax.agent.bound`, `lexical-v1`, calibrated, `min_shared` = 1, `common_frac` = 0.02) | the score is ≥ 10% of the instruction's main-session input |
| **W8 Over-exploration** | Tokens of exploration results (Read, Grep, Glob, WebFetch, WebSearch, LS, NotebookRead, and shell commands that only read: `cat`, `head`, `tail`, `sed -n`, `grep`, `rg`, `find`, `ls`, `tree`, `wc`, `jq`, `git log/show/diff/status/grep/ls-files/blame`) of which fewer than two distinctive words reappear in any later output of the same context (main session, or one sub-agent run) or, for a sub-agent's result, of the main session (its parent) | the score is ≥ 1,000 tokens and ≥ 50% of the instruction's exploration results |
| **W4 Discarded output** | Tokens of a file written whole (Write) and written whole again later in the session; counted at the instruction that wrote the first version | the score is ≥ 200 tokens |

Distinctive words follow `lexical-v1`: identifiers and paths of six or more characters, Hangul
words of three or more syllables, numbers of four or more digits, without the words that appear
in more than max(3, 2% of the context's outputs) outputs.

Instructions follow the rule every survey module shares (`pickaxetax.survey.events._is_instruction`),
and a piece of context belongs to the instruction of the call it came from: a prompt to the call that
reads it, an output or a tool result to the call before (call *k*'s output is born at *k* + 1). A word keeps trailing punctuation (`loader.` and
`loader` differ), as in every `lexical-v1` result so far.

## Sealed machine labels

The detectors' labels for the main labeling packet were made on 2026-10-07, before any human
label, and are kept away from the labelers until every labels file is in. Their SHA-256
(file bytes, JSON with sorted keys and no spaces):

| File | SHA-256 |
|---|---|
| packet | `8b430b57962582568fdbe1b3c11f50d2583b56c2e2e06e9350f8dd2cac69ea26` (the packet's own digest) |
| T1 (W1, W2, W6), main | `dab850164fd2cf935c710dac1274029d047890c6d8d073ff2dba46e365608ae8` |
| T1, practice | `a0bdffbea8dce7714666e0693b181c016fda0dab9712409c628765bdadfe2a05` |
| T2 (W4, W5, W8), main | `977ed59069ad3fd2b4c240f7149d05eb4be84b26a192dc521b0bb2e19837ae8f` |
| T2, practice | `6b74e9162297954232ebc9d21e37c8cfb40b8e0fd91a4383a83b1cb544e7c0eb` |

If the packet is re-issued (for example after the data owner's redaction review), the sealed
files are made again from the same code and their new hashes are committed here before any
labels are exchanged.

**Re-made 2026-10-06, after the phase 2 code review** (`research/phase2/log.md`, cycle E2), which
fixed the shared instruction rule in the bound, the attribution of outputs to their instruction,
a parent-output check in W8 and the de-duplication of tool results in the judge, before any label
existed. All four sealed files came out byte-identical to the hashes above.

## What the labels then give

For each category, with the consensus labels as reference: precision and recall of the detector,
and from them a corrected estimate with a bootstrap CI over the whole population (codebook §5.5).
A detector with too few positives on either side for a stable estimate is reported as such, not
as zero.

## Secondary analysis, fixed before any label (added 2026-10-06)

Phase 2 found that the reuse link these detectors rest on measures topic more than need: calls
before a piece of context existed share its distinctive words as often as calls after it
(`research/phase2/E5-vocabulary-placebo.md`, `A5-compaction-natural-experiment.md`). The primary
analysis above stays as sealed. Two secondary analyses are added now, before any human label exists,
so that the labels can say which reuse definition tracks need:

1. **W5 under the time-mirror test.** The same W5 detector and threshold (≥ 10% of the
   instruction's input), with reuse links kept only where a segment's later references beat its
   own time-mirrored placebo by two standard deviations (`pickaxetax.agent.bound`, method tag
   `lexical-v1+mirror-2sigma`). Its machine labels for the main packet are made from the same code
   and sealed here (SHA-256) before labels are exchanged; if they cannot be sealed in time, the
   secondary analysis is dropped rather than run after the labels are seen.
2. **Which definition the labels side with.** On the instructions where the two W5 detectors
   disagree, the share that the consensus label marks as W5. The disagreement set and the test (an
   exact binomial test of that share against 50%) are fixed now; no threshold is tuned on the labels.

Neither secondary analysis changes what is published as waste: W5 numbers are published only from
the primary detector, corrected by its measured precision and recall (codebook §5.5). The secondary
result is reported next to it, as evidence on the reuse definition that phase 2's forgetting and
paging ranges depend on (5.6% to 12–45% forgetting).

---

## 한국어 요약

규칙 갈래(W4·W5·W8)의 탐지기와 "있음" 문턱을 사람 판정 전에 고정합니다. 이 문서와 이를 추가한 커밋이 그 증거입니다.
판정을 본 뒤에 규칙을 바꾸면 새 버전이고, 새 표본으로 다시 확인합니다. 본 판정 꾸러미에 대한 기계 판정 파일은 판정이
끝날 때까지 판정자에게 보이지 않게 봉인했고, 그 SHA-256을 위 표에 남겼습니다. 판정이 끝나면 합의 판정과 비교해
탐지기의 정밀도와 재현율을 재고, 그것으로 보정한 추정치를 신뢰구간과 함께 냅니다.

보조 분석(판정 전, 2026-10-06 추가): 2단계에서 재사용 연결이 "필요"보다 "주제"를 잰다는 것이 드러났으므로, W5를 시간
대칭 위약 검정(`lexical-v1+mirror-2sigma`)으로 한 번 더 판정해 봉인하고, 두 탐지기가 갈리는 지시에서 합의 판정이 어느
쪽 편인지를 정확 이항검정으로 봅니다. 낭비로 내는 숫자는 여전히 1차 탐지기에서만 나옵니다.
