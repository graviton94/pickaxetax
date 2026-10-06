# Blind labeling: how the waste codebook is checked by people

This is §5 of `waste-codebook-v1.md` made operational. Nobody needs an account: the data
owner makes a packet on their own machine, labelers judge it in the public labeling page
(`https://graviton94.github.io/pickaxetax/label.html`), and anyone can recompute the
agreement from the two labels files.

## Roles

- **Data owner:** the person whose AI usage is studied. They make the packet, read it,
  redact it, and hand it to labelers directly (mail, messenger, USB). It is never committed,
  uploaded or posted, because it holds excerpts of their conversations.
- **Labelers (coders):** at least two. The data owner may be one. The other must be someone
  else. Each works alone and does not see the other's labels or any machine judgment.
- **Anyone:** recomputes agreement from the two labels files, which hold item ids and
  choices only.

## Steps

1. **Packet (data owner).**
   `pxt survey sample [transcripts] --n 200 --calibration 20 --seed 20261006 --redact redact.txt --out packet.json`
   Items are drawn per session and per instruction size (tertiles), with a fixed seed. The
   20 practice items are drawn first and never reused. `redact.txt` holds one regular
   expression per line; every match becomes `[가림]`. Read the packet before sharing it.
   Sessions kept as event-API pages are added with `--pages LABEL=LISTFILE`.
2. **Practice round (all labelers).** Open the labeling page, load the packet, enter a coder
   code (A, B …), choose *Practice*, label all 20, download the labels file.
3. **Calibration meeting.** `pxt survey agreement A-practice.json B-practice.json`, then go
   through the disagreements together. What may change: the labeling guide's wording and
   examples. What may not change: the category definitions. If a definition has to change,
   that is codebook v2, published as such, and the practice round is repeated.
4. **Main round.** Each labeler labels the 200 items alone and sends back the labels file.
   The data owner finishes and sends theirs **before** seeing anyone else's.
5. **Agreement.** `pxt survey agreement A-main.json B-main.json --json > agreement.json`.
   A category is usable only if Cohen's κ ≥ 0.70 (yes / no / unsure as three nominal values).
6. **Adjudication.** The labelers settle each disagreement together and record the agreed
   label (coder code `consensus`). Agreed items are copied unchanged. The consensus labels are
   the reference for everything after this.
7. **Use.** The consensus labels give (a) the sample shares for judgment-tier categories (W4
   rejected answers, W7, W8), with bootstrap CIs, and (b) the precision and recall of each
   rule-tier detector (W2 retries, W3, W4 file lifecycle, W5 use detector), which correct the
   machine estimates over the whole population. Categories below the κ bar are reported as
   "not measured".

## What gets published

- The codebook version, the packet's SHA-256, the seed, sample sizes.
- Both labels files and the consensus file (ids and choices; notes only if the labeler
  agrees, since notes are free text).
- The agreement report, every disagreement id and how it was settled.
- Labelers are named as coder A, B … unless they ask to be credited.

Never published: the packet, any conversation text, redaction patterns that would reveal
what was hidden.

---

## 한국어 요약

- **데이터 주인**이 자기 컴퓨터에서 `pxt survey sample`로 판정 꾸러미를 만들고, 읽어 보고 가린 뒤, 라벨러에게 직접 건넵니다. 꾸러미는 커밋하거나 올리지 않습니다.
- **라벨러**는 공개 사이트의 판정 페이지(`label.html`)에서 꾸러미를 불러와 혼자 판정하고, 판정 파일을 돌려줍니다. 계정이 필요 없고, 꾸러미는 그 탭 밖으로 나가지 않습니다.
- 연습 20개 → 해석 맞추기(정의는 못 바꿈, 바꾸면 v2) → 본 판정 200개(데이터 주인이 먼저 제출) → `pxt survey agreement`로 일치도 계산(κ ≥ 0.70인 갈래만 사용) → 엇갈린 항목 합의 → 합의 판정으로 표본 비율과 판정기 정확도를 계산합니다.
- 공개하는 것: 기준 버전, 꾸러미 해시, 시드, 판정 파일(번호와 선택만), 일치도와 엇갈린 항목. 공개하지 않는 것: 꾸러미와 대화 원문.
- 판정자에게 건넬 한 장: [`labeler-guide-ko.md`](labeler-guide-ko.md). 기계 판정 규칙을 검토할 사람에게는 [`review-kit-ko.md`](review-kit-ko.md).
