# 연구 노트 #1 — 21세기 골드러시의 영수증

- 게시일: 미정
- 목적: 왜 시작했는지(계기)와 첫 현상조사 결과를 함께 보여 준다. 계기는 이 노트에만 넣는다.
- 상태: 초안 v4 (브랜드를 #AntiTokenMaxing과 "21세기 골드러시의 영수증"으로 바꾸고, 73.6% 발견과 탄소 추정을 넣음). 한국어 확정 전이며, 영어는 한국어가 바뀌면 다시 번역한다.
- 분량: 한국어 본문 733자(공백 포함), 게시물 전체(한·영) 약 2,300자
- 이미지: [img/01-receipt.png](img/01-receipt.png) (1080×1350)
- 링크: 본문에 넣지 않고 첫 댓글에 단다 (`https://graviton94.github.io/pickaxetax/`)

## 게시물

[연구 노트 #1] 21세기 골드러시의 영수증

AI에게 말을 걸 때마다, AI는 그동안의 대화를 처음부터 다시 읽습니다. 여기에 수억 명의 사용자와 쉬지 않고 도는 에이전트를 곱하면, 전 세계의 반도체와 전력을 끌어다 쓰는 낭비가 됩니다. 지금의 AI 붐은 제2의 골드러시이고, 사람을 돕던 연산이 오히려 산업 전체를 끌고 다니는 주종 역전이 일어나고 있습니다. 이 구조를 근본부터 고칠 방법을 찾으려고 이 연구를 시작했습니다.

첫 단계는 현상조사이고, 첫 조사 대상은 저 자신입니다. 지난 석 달 동안 Claude 코딩 에이전트에 맡긴 일 전부를, 제공사가 호출마다 기록한 사용량으로 다시 쟀습니다.

• AI가 처리한 입력: 58억 7천만 토큰. 세션 목록에 표시된 합계의 1.5배였습니다.
• 제가 내린 지시는 586번, 지시 한 번에 평균 1,000만 토큰을 읽었습니다.
• AI가 써낸 양은 읽은 양의 0.2~0.4%였습니다.
• 며칠씩 이어 쓴 세션 5개가 전체 입력의 93%를 차지했습니다.
• 매 호출이 들고 다닌 컨텍스트의 73.6%는 이미 끝난 지시들이 남긴 내용이었습니다.

가장 큰 발견은 마지막 줄입니다. 비용 대부분이 지금 하는 일이 아니라, 이미 끝난 일을 다시 읽는 데 들어갔습니다. 탄소로 환산하면 약 148 kg, 나무 한 그루가 25년 동안 흡수할 양입니다(추정).

누구나 같은 방법으로 자기 영수증을 뽑을 수 있게 도구와 데이터를 공개했습니다. 다음 노트에서는 지시 하나가 2억 토큰까지 불어나는 과정을 들여다봅니다.

— English —

[Research note #1] The receipt of the 21st-century gold rush

Every time you talk to an AI, it re-reads the whole conversation from the beginning. Multiply that by hundreds of millions of users and agents that never stop, and you get waste that pulls on the world's chips and power. Today's AI boom is a second gold rush, and the compute that was meant to serve people now drags a whole industry behind it: master and servant have swapped places. I started this research to find a way to fix that structure at its root.

The first step is a survey of what actually happens, and the first subject is me. I re-measured everything I gave a Claude coding agent over the last three months, using the usage the provider recorded for every call.

• Input the AI processed: 5.87 billion tokens, 1.5× the total the session list showed.
• I gave 586 instructions; each one read 10 million tokens on average.
• What the AI wrote was 0.2–0.4% of what it read.
• Five sessions, each continued over days, made up 93% of all input.
• 73.6% of the context carried on every call was left over from instructions that were already finished.

The last line is the biggest finding. Most of the cost went not to the work at hand but to re-reading work that was already done. In carbon that is about 148 kg, what one tree absorbs in 25 years (estimate).

I published the tool and the data so anyone can print their own receipt the same way. Next, I look at how a single instruction grows to 200 million tokens.

#AntiTokenMaxing

## 출처

- 기준: `research/survey/user01/dataset.json` (SHA-256 ba8c2161…) → `pxt survey report`로 만든 `report.html`
- 58억 7천만: 총입력 5,871,292,005 (S09 부분 측정이라 하한), 세션 목록 합계의 1.49배.
- 586번: 10개 세션의 사용자 지시 합, 평균 10,019,270 토큰/지시.
- 0.2~0.4%: 세션 안 기록이 있는 S01·S02·S03의 출력/입력 비율 0.19~0.43%.
- 93%: 상위 5개 세션(S03, S10, S09, S05, S02)의 비중 93.3%.
- 73.6%: 레포트의 컨텍스트 분해(고정 12.7% / 이전 지시에서 넘어온 것 73.6% / 지금 지시 13.7%), `report.html`. 해석은 `INSIGHTS.md`(중간 집계 기준 74.1%).
- 148 kg, 나무 25년: `research/carbon-factors.md` (추정. Jegham 외 2025, 캐시 읽기 요금 비율 0.1, IEA 445 g/kWh, EPA 나무 1그루 10년 60 kg).
- 2억 토큰: 지시 하나의 최대 입력 219,620,777 (S05).
