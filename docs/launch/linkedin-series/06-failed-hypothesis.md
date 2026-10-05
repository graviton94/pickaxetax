# Chapter 6 — The hypothesis that failed

- Date: Tue 2026-10-27
- Purpose: credibility. Show the method (hypothesis → test → falsify → refine) and set up chapter 7.
- Image: none

## Post (English)

#AntiTokenMaxing · Chapter 6/10

Our first theory was wrong, and I want to show it.

The hypothesis was simple: most of what an AI agent carries in its context is dead, never used again.

The first test said only 1% was dead. That sounded like a clean refutation, until we looked closer. The test counted a piece of context as "used" if any later output shared any word with it. Common words like file paths and keywords appear everywhere, so almost everything looked used. The metric was meaningless.

We refined it: ignore words that appear in more than 2% of outputs, and measure how much of each piece's distinctive content is never echoed again. Now 54% looked unused. But that's only an upper bound, because a model can use what it read without repeating it word for word.

So neither number answered the question. The real mistake was the question itself. "Is it ever used again?" is the wrong thing to ask. The right question is: "Is it needed at each step in between?"

That question has an exact answer, borrowed from a 1966 result in computer science. The answer changed how we think about AI memory.

All experiments, including the failures, are in the repo's research log.

Next chapter: paging, not forgetting.

## First comment (한국어)

#AntiTokenMaxing · 6/10장

첫 번째 이론은 틀렸습니다. 그 과정을 그대로 보여 드립니다.

가설은 단순했습니다. "AI 에이전트가 컨텍스트에 들고 다니는 것의 대부분은 다시는 쓰이지 않는 죽은 정보다."

첫 실험은 죽은 정보가 1%뿐이라고 했습니다. 깔끔한 반증 같았지만, 들여다보니 측정이 틀렸습니다. 나중의 출력과 단어 하나만 겹쳐도 "사용됨"으로 셌기 때문입니다. 파일 경로나 키워드 같은 흔한 단어는 어디에나 나오니 거의 모든 것이 사용된 것처럼 보였습니다.

그래서 기준을 다듬었습니다. 출력의 2% 넘게 등장하는 단어는 빼고, 각 조각의 고유한 내용이 다시 나오지 않는 비율을 쟀습니다. 이번엔 54%가 쓰이지 않은 것처럼 보였습니다. 하지만 모델은 읽은 것을 그대로 따라 쓰지 않고도 활용할 수 있으니, 이것도 상한일 뿐입니다.

진짜 실수는 질문 자체였습니다. "다시 쓰이는가?"가 아니라 "그 사이의 매 단계에서 필요한가?"를 물어야 했습니다. 이 질문에는 1966년 컴퓨터과학의 결과를 빌린 정확한 답이 있습니다.

다음 장: 잊지 말고, 내려놓았다가 다시 불러라.
