# 연구 노트 #1 — 21세기 골드러시의 영수증

- 게시일: 원고 확정 후 바로
- 목적: 왜 시작했는지(계기), 그리고 무엇을 낭비로 볼지 판정 기준을 먼저 고정해 보여 준다. 판정은 다음 노트부터 한 갈래씩. 계기는 이 노트에만 넣는다.
- 상태: **확정 v6** (2026-10-06, 한국어 확정 후 영어 번역). 결정 페이지의 결정 8개를 반영했다. 기계적 사실을 바로잡았다(매 호출 전체 재입력, 컴팩션 예외). 소탐대실 어조를 넣었다. 출력 비율 범위를 세션 3개로 한정했다. 갈래 정의를 이미지로 옮기고, 실제 오배송 사례를 넣고, "(계속)"으로 맺었다.
- 분량: 한국어 본문 804자(공백 포함). 게시물 전체(한·영) 2,604자, 링크드인 3,000자 이내. 붙여넣기용 `01-post.txt`.
- 이미지: 4장씩, 한국어 `img/note01/ko/01~04.png`, 영어 `img/note01/en/01~04.png` (1080×1350). 한 게시물에 한국어 4장 + 영어 4장을 순서대로 올린다. 원본 `figures/note01-slides.template.html`, `figures/note01-slides.en.template.html`
- 링크: 본문에 넣지 않고 첫 댓글에 단다

## 게시물 (한국어 원문 + 영어 번역, 한 게시물)

[연구 노트 #1] 21세기 골드러시의 영수증

AI는 답할 때마다 지금까지의 대화를 통째로 다시 입력받습니다. 대화가 너무 길어져 요약되기 전까지는 처음부터 전부입니다. 캐시가 다시 계산하는 수고는 덜어 주지만, 읽는 양은 줄지 않습니다. 대화가 길어지고 에이전트가 오래 돌수록, 답 한 번에 드는 연산은 계속 커집니다.

지금 AI 산업은 더 큰 모델과 더 많은 데이터센터로 속도 경쟁을 하고 있습니다. 쓰는 자원이 만들어 내는 가치보다 빠르게 늘고 있는 건 아닌지, 아무도 재지 않은 채로요. 저는 AI를 반대하지 않습니다. 하지만 재지 않고 달리는 속도 경쟁은 소탐대실입니다. 그래서 재는 것부터 시작합니다.

첫 조사 대상은 저 자신입니다. 석 달 동안 Claude 코딩 에이전트가 처리한 입력은 58억 7천만 토큰이었습니다. 출력이 정확히 기록된 세션 3개를 보면, 입력의 98.9%는 이미 읽은 내용을 캐시에서 다시 읽은 것이었고, 써낸 출력은 읽은 양의 0.19~0.43%였습니다.

많이 읽었다고 다 낭비는 아닙니다. 그래서 숫자를 해석하기 전에 낭비부터 정의했습니다. 결과를 바꾸지 않고 뺄 수 있었던 토큰입니다. 이를 여덟 갈래로 나누고, 갈래마다 무엇과 비교해 낭비로 볼지, 기계가 셀지 사람이 판정할지를 정했습니다(이미지). 사람이 판정하는 갈래는 두 사람이 서로의 판정을 모른 채 같은 표본을 보고, 충분히 일치할 때만 결과를 냅니다.

이 조사 자체의 낭비도 셉니다. 조사 도중 제 에이전트가 작업 지시를 엉뚱한 세션에 보내 헛돈 일도 그 대상입니다.

기준은 오늘 고정했습니다. 다음 노트부터 이 기준으로 제 기록을 한 갈래씩 판정해 나가겠습니다. (계속)


— English —

[Research note #1] The receipt of the 21st-century gold rush

Every time an AI answers, it takes in the whole conversation so far as input again. Until the conversation grows long enough to be summarized, that means everything from the start. Caching saves recomputing it, but not reading it. The longer a conversation runs and the longer an agent works, the more compute each single answer takes.

The AI industry is racing for bigger models and more data centers, and nobody is measuring whether the resources it burns are growing faster than the value they create. I am not against AI. But a race that runs without measuring is penny-wise and pound-foolish. So I am starting with measurement.

The first subject is me. Over three months, the Claude coding agent I worked with processed 5.87 billion input tokens. In the 3 sessions whose output was recorded exactly, 98.9% of the input was content it had already read, read again from the cache, and what it wrote was 0.19–0.43% of what it read.

Reading a lot is not the same as wasting. So before interpreting any number, I defined waste first: tokens that could have been removed without changing the result. I split it into eight categories and fixed, for each one, what it is compared against and whether a machine counts it or people judge it (see the images). For the categories people judge, two people label the same sample without seeing each other's labels, and a result is published only when they agree closely enough.

The waste of this research counts too, including the time one of my agents sent its task to the wrong session.

The criteria are fixed as of today. From the next note on, I will judge my own records against them, one category at a time. (To be continued)

#AntiTokenMaxing

## 출처



- 기준: `research/survey/user01/dataset.json` (SHA-256 ba8c2161…) → `pxt survey report`로 만든 `report.html`
- 58억 7천만: 총입력 5,871,292,005 (S09 부분 측정이라 하한), 세션 목록 합계의 1.49배.
- 586번: 10개 세션의 사용자 지시 합, 평균 10,019,270 토큰/지시.
- 0.19~0.43%, 98.9%: 출력이 정확히 기록된(로컬 트랜스크립트) S01·S02·S03의 출력/입력 비율과 캐시 읽기 비중. 나머지 7개는 이벤트 API라 출력 수치가 자리표시값이다.
- 93%: 상위 5개 세션(S03, S10, S09, S05, S02)의 비중 93.3%.
- 73.6%: 레포트의 컨텍스트 분해(고정 12.7% / 이전 지시에서 넘어온 것 73.6% / 지금 지시 13.7%), `report.html`. 해석은 `INSIGHTS.md`(중간 집계 기준 74.1%).
- 148 kg, 나무 25년: `research/carbon-factors.md` (추정. Jegham 외 2025, 캐시 읽기 요금 비율 0.1, IEA 445 g/kWh, EPA 나무 1그루 10년 60 kg).
- 2억 토큰: 지시 하나의 최대 입력 219,620,777 (S05).
- 판정 기준: `research/protocol/waste-codebook-v1.md` (2026-10-06 고정, 아직 적용 전)
- 매 호출 전체 대화 재입력: 측정한 호출별 입력이 그 시점 컨텍스트 전체와 같다(컴팩션 뒤에는 요약부터). 캐시 읽기도 입력으로 과금·처리된다.
