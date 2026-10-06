# 연구 노트 #2 — 버리는 문제가 아니라, 들고 다니는 문제

- 상태: **초안 v2 (2026-10-07)**, 검토 전. v1(반박할 수 없는 바닥부터)에서 바뀐 것: 조사 자체 비용 단락 삭제(데이터는
  `research/survey/self-audit-log.md`에 유지), 걸음 비용과 오라클 최소치(넘어온 내용이 다시 쓰였나)를 더했다.
  결정 반영: 본 결과는 v1 규칙(5.79%)과 민감도 범위, 해석은 "쉰 것이 아니라 구조가 비효율적".
- 목적: 판정 기준 v1의 첫 적용(기계 판정 세 갈래)과, 기록만으로 잴 수 있는 구조의 몫(오라클 최소치, 낭비 판정 아님).
  1편 숫자 정정(S09 완전 측정). 다음 단계(블라인드 판정) 예고.
- 분량: 한국어 본문 739자(공백 포함). 게시물 전체(한·영) 2444자. 붙여넣기용 `02-post.txt`.
- 이미지: 4장씩, `img/note02/ko/01~04.png`, `img/note02/en/01~04.png` (1080×1350). 원본 `figures/note02-slides.html`,
  `figures/note02-slides.en.html`. 숫자는 데이터 파일에서 바로 뽑는다: `python3 docs/launch/linkedin-series/figures/note02-slides.py`,
  그림은 `node docs/launch/linkedin-series/figures/render-slides.mjs <html> <폴더>`.
- 게시 전 할 일: PR 머지(첫 댓글 링크가 열리도록), 공동 검토자의 규칙 검토(`research/protocol/review-kit-ko.md`),
  사이트 숫자를 판 2로 전환하는 브랜치 머지.
- 링크: 본문에 넣지 않고 첫 댓글에 단다

## 게시물

[연구 노트 #2] 버리는 문제가 아니라, 들고 다니는 문제

1편에서 낭비를 여덟 갈래로 정의했습니다. 오늘은 그중 기록만으로 정할 수 있는 세 갈래를 먼저 셌습니다. 같은 결과를 다시 받은 중복, 오류, 이미 처리한 맥락을 처음부터 다시 처리한 경우입니다. 먼저 바로잡습니다. 1편의 58억 7천만 토큰은 한 세션을 일부만 받은 하한이었고, 다 받아 다시 재니 68억 4천만 토큰입니다.

중복과 오류로 받은 토큰 자체는 0.001%도 안 됩니다. 하지만 그 한 걸음을 내딛느라 AI는 매번 맥락 전체를 다시 읽었고, 그렇게 쓰인 입력이 2.6%입니다. 비용으로 보면 5.79%입니다. 거의 전부가 이미 처리한 맥락(평균 44만 토큰)을 처음부터 다시 처리한 값이고, 그 79%는 제가 1시간 넘게 쉬었다 돌아온 직후였습니다. 쉰 것이 낭비가 아니라, 그렇게 만드는 구조가 비효율적입니다.

진짜 질문은 따로 있습니다. 매 호출 맥락의 76%는 이미 끝난 지시에서 넘어온 내용이었습니다. 그 내용이 뒤에서 다시 쓰였는지 기록을 추적했습니다. 끝까지 다시 쓰이지 않을 내용만 버렸다면 줄었을 입력은 생각보다 적었습니다(4~25%). 대부분은 언젠가 다시 쓰였지만, 그때까지 쓰이지 않은 채 매 호출마다 다시 읽혔습니다. 필요할 때 정확히 불러오는 이상적인 구조였다면 입력의 35~54%가 필요 없었습니다.

버릴 것이 많은 게 아니라, 전부를 늘 들고 다니는 방식이 문제입니다. 다시 쓰였는지는 글자 겹침으로 추정한 값이라, 다음은 두 사람의 블라인드 판정으로 검증합니다. (계속)


— English —

[Research note #2] Not what to throw away, but what we carry

Note 1 defined waste in eight categories. Today I counted the three that the records decide on their own: duplicates (the same result received again), errors, and context already processed but processed again from scratch. A correction first: the 5.87 billion tokens in note 1 was a lower bound, because one session had been fetched only in part. Fetched in full, it is 6.84 billion.

The duplicate and error results themselves are under 0.001% of the tokens. But to take each of those steps the AI re-read its whole context, and those steps took 2.6% of the input. In cost it is 5.79%. Almost all of that is context already processed being processed again from scratch (440,000 tokens on average), and 79% of it came right after I returned from more than an hour away. The break is not the waste; the structure that makes it so expensive is inefficient.

The real question is elsewhere. 76% of each call's context was carried over from instructions already finished. I traced whether that content was used again later. Dropping only what was never used again would have saved less than I expected (4–25% of the input). Most of it was used again at some point, but until then it was re-read, unused, on every call. With an ideal structure that fetches content exactly when it is needed, 35–54% of the input would not have been needed.

The problem is not that much should be thrown away. It is carrying everything, all the time. Reuse was estimated from overlapping words, so next, two people will check it by blind labeling. (To be continued)

#AntiTokenMaxing #AI #LLM #TOKENMAXING #GREENAI

## 첫 댓글 (링크)

기계 판정 결과와 규칙: https://github.com/graviton94/pickaxetax/blob/main/research/survey/user01/floor-t1.md
넘어온 내용은 다시 쓰였나 (오라클 최소치): https://github.com/graviton94/pickaxetax/blob/main/research/survey/user01/opportunity-v1.md
판정 기준 v1: https://github.com/graviton94/pickaxetax/blob/main/research/protocol/waste-codebook-v1.md
영수증 판 2: https://graviton94.github.io/pickaxetax/report/user01.html
1편: https://lnkd.in/p/esfBHm8W

Data, rules and results: the links above (in English and Korean).

(게시 전 확인: 이 문서들이 main에 머지돼 링크가 열리는지, 사이트 판 2 브랜치가 머지돼 영수증이 판 2인지.)

## 출처

- 기준: `research/survey/user01/dataset-v2.json` → `report-v2.html`, 기계 판정 결과 `research/survey/user01/floor-t1.json`
  (`pxt survey judge`, 규칙 `research/protocol/mechanical-tier-v1.md`). 판 1 `dataset.json`은 1편이 인용하므로 그대로 둔다.
- 68억 4천만: 판 2 처리한 입력 6,839,974,268 (하위 에이전트 포함). 58억 7천만(판 1, 5,871,292,005)과의 차이 968,682,263은
  S09의 앞부분(2026-08-12~15)과 그 하위 에이전트, S01 하위 에이전트 444,284.
- 0.001% 미만: 지울 수 있던 토큰 (W1 3,410 + W2 52,440) ÷ 6,839,974,268 = 0.0008%.
- 5.79%: 지울 수 있던 비용 (W1·W2 × 1.25 + W6 39,200,727 × 1.15) ÷ 입력 쪽 비용. 가격 비율은 제공사 정가.
- 79%: W6 토큰 중 직전 주 세션 호출과의 간격이 1시간을 넘은 재작성 30,903,919 ÷ 39,200,727 = 78.8% (90건 중 64건).
- 평균 44만 토큰: W6 39,200,727 ÷ 90건 = 435,564.
- 0.48~5.79%: 민감도. 5분 안의 재작성만 0.48%, 1시간 넘게 쉰 뒤 제외 1.23%, 모두 5.79%(본 결과).
- 76%: 판 2 컨텍스트 분해, 이전 지시에서 넘어온 몫 76.1% (10개 세션 모두). 1편의 73.6%는 시계열이 있던 8개 세션 기준.
- 2.6%: 걸음 비용(하한 밖). 도구 호출이 모두 중복이었던 걸음 222번 92,455,835 + 모두 오류였던 걸음 256번 84,431,767
  = 176,887,602 ÷ 6,839,974,268 = 2.59%. `floor-t1.md`의 "걸음 비용".
- 4~25%, 35~54%: 오라클 최소치(`opportunity-v1.md`), 주 세션 6,579,410,935토큰. 다시는 안 쓰인 것만 버리기(P = ∞) 5.6%,
  9가지 탐지 기준(보정) 3.5~24.7%. 필요할 때 다시 불러오기(P = 1,000) 41.5%, 같은 9가지 35.2~53.9%(보정 없이 16.2~28.1%).
  미래를 아는 오라클의 값(기회의 크기)이고, 재사용은 글자 겹침(`lexical-v1`)으로 추정해 아직 블라인드 판정으로 검증하지 않았다.
