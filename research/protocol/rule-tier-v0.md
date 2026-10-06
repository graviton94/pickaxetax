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
| **W8 Over-exploration** | Tokens of exploration results (Read, Grep, Glob, WebFetch, WebSearch, LS, NotebookRead, and shell commands that only read: `cat`, `head`, `tail`, `sed -n`, `grep`, `rg`, `find`, `ls`, `tree`, `wc`, `jq`, `git log/show/diff/status/grep/ls-files/blame`) of which fewer than two distinctive words reappear in any later output of the same context (main session, or one sub-agent run) | the score is ≥ 1,000 tokens and ≥ 50% of the instruction's exploration results |
| **W4 Discarded output** | Tokens of a file written whole (Write) and written whole again later in the session; counted at the instruction that wrote the first version | the score is ≥ 200 tokens |

Distinctive words follow `lexical-v1`: identifiers and paths of six or more characters, Hangul
words of three or more syllables, numbers of four or more digits, without the words that appear
in more than 2% of a context's outputs. A word keeps trailing punctuation (`loader.` and
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

## What the labels then give

For each category, with the consensus labels as reference: precision and recall of the detector,
and from them a corrected estimate with a bootstrap CI over the whole population (codebook §5.5).
A detector with too few positives on either side for a stable estimate is reported as such, not
as zero.

---

## 한국어 요약

규칙 갈래(W4·W5·W8)의 탐지기와 "있음" 문턱을 사람 판정 전에 고정합니다. 이 문서와 이를 추가한 커밋이 그 증거입니다.
판정을 본 뒤에 규칙을 바꾸면 새 버전이고, 새 표본으로 다시 확인합니다. 본 판정 꾸러미에 대한 기계 판정 파일은 판정이
끝날 때까지 판정자에게 보이지 않게 봉인했고, 그 SHA-256을 위 표에 남겼습니다. 판정이 끝나면 합의 판정과 비교해
탐지기의 정밀도와 재현율을 재고, 그것으로 보정한 추정치를 신뢰구간과 함께 냅니다.
