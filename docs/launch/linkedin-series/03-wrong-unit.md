# 연구 노트 3/10 — 토큰은 잘못된 단위입니다

- 게시일: 목 2026-10-15, 08:00–09:00 KST
- 목적: 제번스 반론에 먼저 답하고, 사용량을 반도체(HBM)와 잇는다.
- 이미지: 없음
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 719자, 게시물 전체 2059자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 3/10] 토큰은 잘못된 단위입니다

"AI를 싸게 만들면 사람들은 더 쓸 뿐이다." 효율을 이야기하면 꼭 돌아오는 반론입니다. 제번스 역설이라고 부르지요. 맞는 말입니다. 토큰 값만 내리면 총사용량은 오히려 늘 수 있습니다.

그래서 측정 단위부터 바꿨습니다. 첫째, 토큰이 아니라 가치 있는 결과 하나당 연산으로 잽니다. 같은 결과를 더 적은 계산으로 냈다면, 총량이 늘어도 더 나은 것입니다.

둘째, 그 밑에 메모리를 둡니다. 모델은 대화를 처리하는 동안 컨텍스트 전체를 KV 캐시라는 형태로 메모리에 올려 둡니다. 공개된 70B급 모델로 계산하면 토큰 하나에 약 320KB입니다. 지난 노트의 최대 컨텍스트라면 약 166GB, 80GB짜리 GPU 두 장으로도 모자랍니다. (공개된 구조로 계산한 예시입니다.)

프롬프트 캐싱은 다시 읽는 연산을 줄여 주지만, 그 대가로 이 상태를 메모리에 붙잡아 둡니다. 비용이 사라지는 것이 아니라 연산에서 메모리로 옮겨 갈 뿐입니다. 계산은 싸졌어도, 책상 위에 펼쳐 둔 책은 그대로인 셈입니다. 그리고 HBM은 AI 칩에서 가장 비싸고 귀한 부품입니다.

그래서 앞으로의 노트는 두 가지를 함께 묻겠습니다. 얼마나 가치 있는 결과를 냈는가, 그리고 그동안 메모리를 얼마나 많이, 얼마나 오래 차지했는가.

채팅창의 "고마워" 한마디와 반도체 붐은 이렇게 이어져 있습니다.

다음 노트: 내 대화의 낭비를 직접 확인하는 도구.

— English —

[Research note 3/10] Tokens are the wrong unit

"Make AI cheaper and people will just use more of it." It's the objection every efficiency effort hears. It's called the Jevons paradox, and it's right: lower only the price per token and total use can go up.

So we changed the unit first. One: we measure compute per valuable outcome, not tokens. The same result with less computation is better, even if the total grows.

Two: underneath that, we put memory. While a model works on a conversation, it keeps the whole context in memory as a "KV cache". On an open 70B-class model that is about 320 KB per token. The peak context from the last note would take about 166 GB, more than two 80 GB GPUs can hold. (An illustration using a public architecture.)

Prompt caching cuts the compute of re-reading, but it does so by holding that state in memory. The cost doesn't disappear. It moves from compute to memory: the reading got cheaper, but the books stay open on the desk. And HBM is the most expensive and scarcest part of an AI chip.

So from here on, every note asks two questions together: how valuable was the result, and how much memory did it occupy, and for how long?

That is how a "thanks" in a chat window connects to the chip boom.

Next: a tool to see the waste in your own conversations.

#AntiTokenMaxing

## 출처

- Facts 표: KV 캐시 약 320KiB/토큰 (공개 70B급 구조), 507,710토큰 ≈ 166GB. `research/framework.md` §1.
