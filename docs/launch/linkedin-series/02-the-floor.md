# 연구 노트 #2 — 반박할 수 없는 바닥부터

- 상태: **초안 v1 (2026-10-06)**, 검토 전. 결정 반영: 본 결과는 v1 규칙(5.79%), 나머지 두 기준은 민감도 분석(범위 0.48~5.79%).
  해석은 "쉰 것이 아니라 구조가 비효율적, 며칠씩 이어 쓰는 사용 방식이 키운다".
- 목적: 판정 기준 v1의 첫 적용. 기계가 정할 수 있는 세 갈래(W1·W2·W6)만. 1편 숫자 정정(S09 완전 측정). 다음 단계(블라인드 판정) 예고.
  조사 자체의 비용도 보고.
- 분량: 한국어 본문 718자(공백 포함). 게시물 전체(한·영) 2330자. 붙여넣기용 `02-post.txt`.
- 이미지: 4장씩, `img/note02/ko/01~04.png`, `img/note02/en/01~04.png` (1080×1350). 원본 `figures/note02-slides.html`,
  `figures/note02-slides.en.html`. 숫자는 데이터 파일에서 바로 뽑는다: `python3 docs/launch/linkedin-series/figures/note02-slides.py`,
  그림은 `node docs/launch/linkedin-series/figures/render-slides.mjs <html> <폴더>`.
- 게시 전 할 일: 공동 검토자의 규칙 검토(`research/protocol/review-kit-ko.md`), 사이트 숫자를 판 2로 전환하는 브랜치 머지.
- 링크: 본문에 넣지 않고 첫 댓글에 단다

## 게시물

[연구 노트 #2] 반박할 수 없는 바닥부터

1편에서 낭비를 여덟 갈래로 정의했습니다. 오늘은 그중 사람의 판단 없이 기록만으로 정할 수 있는 세 갈래를 먼저 셌습니다. 같은 결과를 다시 받은 중복, 오류, 그리고 이미 처리한 맥락을 처음부터 다시 처리한 경우입니다.

먼저 바로잡습니다. 1편의 58억 7천만 토큰은 한 세션을 일부만 받은 하한이었습니다. 빠진 구간까지 다 받아 다시 재니 68억 4천만 토큰입니다.

결과입니다. 중복과 오류로 받은 토큰은 전체의 0.001%도 안 됩니다. 토큰으로는 반박할 수 없는 낭비가 거의 없습니다. 그런데 비용으로는 5.79%입니다. 거의 전부가 캐시에 있던 맥락을 처음부터 다시 처리한 값이고, 그중 79%는 제가 1시간 넘게 쉬었다 돌아온 직후에 생겼습니다.

쉰 것이 낭비는 아닙니다. 돌아올 때마다 평균 44만 토큰의 맥락을 통째로 다시 처리하게 만드는 구조가 비효율적이고, 한 세션을 며칠씩 이어 쓴 제 사용 방식이 그 비용을 키웠습니다. 어디까지 셀지에 따라 결과는 0.48~5.79%의 범위로 냅니다.

바닥이 작다고 낭비가 작은 것은 아닙니다. 매 호출 맥락의 76%는 이미 끝난 지시에서 넘어온 내용이었습니다. 그것이 필요했는지는 사람이 판정해야 합니다. 다음은 두 사람의 블라인드 판정입니다.

이 조사 자체도 쟀습니다. 기록을 받아 오느라 조사 세션 입력의 45%를 하위 에이전트가 썼습니다. 낭비를 재는 일도 낭비를 만듭니다. 더 싼 방법으로 바꿉니다. (계속)


— English —

[Research note #2] Starting from the floor nobody can dispute

Note 1 defined waste in eight categories. Today I counted the three that the records decide on their own, with no human judgment: duplicates (the same result received again), errors, and context that had already been processed but was processed again from scratch.

A correction first. The 5.87 billion tokens in note 1 was a lower bound: one session had been fetched only in part. With the missing part fetched, the total is 6.84 billion.

The result. Tokens received as duplicates or errors are under 0.001% of the total. In tokens, the waste nobody can dispute is close to zero. In cost it is 5.79%. Almost all of that is context the cache already held being processed again from scratch, and 79% of it happened right after I came back from a break of more than an hour.

Taking a break is not waste. The structure is inefficient: every return re-processes the whole context, 440,000 tokens on average. My habit of keeping one session going for days made that cost bigger. Depending on which of these re-writes count, the result is a range: 0.48–5.79%.

A small floor does not mean little waste. 76% of each call's context was carried over from instructions already finished. Whether it was needed is for people to judge. Next: blind labeling by two people.

I measured this research too. Fetching the records took 45% of the research session's input, spent by sub-agents. Measuring waste makes waste. I am switching to a cheaper method. (To be continued)

#AntiTokenMaxing #AI #LLM #TOKENMAXING #GREENAI

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
- 45%: 연구 세션(S01)의 중간 집계, 입력 764,421,492 중 하위 에이전트 340,654,835 (44.6%). 하위 에이전트 입력의 98%가
  이벤트 기록을 쪽 단위로 받아 온 에이전트. `research/survey/self-audit-log.md`.
