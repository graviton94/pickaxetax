# Chapter 3 — Tokens are the wrong unit

- Date: Thu 2026-10-15
- Purpose: answer the Jevons objection before anyone raises it; connect usage to semiconductors (HBM). This is where the project stops looking like "a token saver".
- Image: none

## Post (English)

#AntiTokenMaxing · Chapter 3/10

"If you make AI cheaper, people will just use more of it."

That's the Jevons paradox, and it's the right objection to any efficiency project. If all we did was lower the price per token, total consumption could go up.

So we changed the unit.

1. Not tokens, but compute per valuable outcome. The same result with less compute is better, however much the total grows.
2. Underneath that, memory residency: how many bytes of accelerator memory a task keeps occupied, and for how long.

Why memory? While a model works on your conversation, it holds a "KV cache" of everything in context. On an open 70B-class model that's about 320 KB per token. The 507,710-token peak context from Chapter 2 would take about 166 GB, more than two 80 GB GPUs just to hold it. (That's an illustration on a public architecture; closed models don't publish these numbers.)

Prompt caching makes re-reading cheaper in compute because it keeps that state in memory between calls. The cost doesn't disappear. It moves from compute to memory capacity, and HBM is the scarcest and most expensive part of an AI chip.

That's the link between your chat window and the semiconductor boom.

Next chapter: the tool. See your own waste, without uploading anything.

## First comment (한국어)

#AntiTokenMaxing · 3/10장

"AI를 싸게 만들면 사람들은 더 많이 쓸 뿐이다."

제번스 역설입니다. 모든 효율화 프로젝트가 들어야 할 정당한 반론입니다. 토큰 단가만 낮춘다면 총사용량은 오히려 늘 수 있습니다.

그래서 단위를 바꿨습니다.
1. 토큰이 아니라 **가치 있는 결과 1건당 연산**. 총량이 늘더라도, 같은 결과를 더 적은 연산으로 내면 더 나은 것입니다.
2. 그 밑에는 **메모리 상주량**. 작업이 가속기 메모리를 몇 바이트, 얼마나 오래 차지하는가입니다.

왜 메모리일까요? 모델은 대화를 처리하는 동안 컨텍스트 전체의 "KV 캐시"를 메모리에 들고 있습니다. 공개된 70B급 모델 기준으로 토큰당 약 320KB입니다. 2장의 최대 컨텍스트 507,710토큰이면 약 166GB, 그것만 담는 데 80GB GPU 두 장 이상이 필요합니다. (공개 구조로 계산한 예시입니다. 비공개 모델은 이 수치를 밝히지 않습니다.)

프롬프트 캐싱은 이 상태를 호출 사이에도 메모리에 붙잡아 두어 다시 읽기의 연산을 줄입니다. 비용이 사라지는 게 아니라 연산에서 **메모리 용량**으로 옮겨 갑니다. 그리고 HBM은 AI 칩에서 가장 비싸고 귀한 부품입니다.

여러분의 채팅창과 반도체 붐은 이렇게 이어져 있습니다.

다음 장: 도구 공개. 아무것도 업로드하지 않고 내 낭비를 직접 확인하기.
