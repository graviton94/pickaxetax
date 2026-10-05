# Chapter 2 — We measured one session

- Date: Tue 2026-10-13
- Purpose: the first hard number. Concrete, reproducible, anonymized.
- Image: none (or a screenshot of the `pxt agent audit` summary lines in the README)

## Post (English)

#AntiTokenMaxing · Chapter 2/10

One real coding-agent session. 143 API calls. To write about 350 thousand tokens, the agent read 43.5 million.

For every token it wrote, it read about 124.

Most of those reads were served from cache (97.8%), which made them cheap, but not free. The context peaked at 507,710 tokens: every call near the end carried half a million tokens of history to decide its next step.

The surprise was where the volume came from. It wasn't one huge file or one runaway tool output. The session simply kept growing, and every step re-read all of it.

We didn't estimate this. The figures come from the usage numbers the provider reports for each call, read from the agent's own session log, on the machine where it ran. Nothing was uploaded.

If a single session looks like this, what does the whole industry's usage look like? That's the question this project exists to answer with data instead of opinions.

Next chapter: why "save tokens" is the wrong goal, and what to measure instead.

## First comment (한국어)

#AntiTokenMaxing · 2/10장

실제 코딩 에이전트 세션 하나. API 호출 143번. 약 35만 토큰을 쓰려고 에이전트는 4,348만 토큰을 읽었습니다.

1토큰을 쓸 때마다 약 124토큰을 읽은 셈입니다.

대부분(97.8%)은 캐시에서 처리돼 싸졌지만 공짜는 아닙니다. 컨텍스트는 최대 507,710토큰까지 커졌습니다. 세션 후반의 호출은 다음 한 걸음을 정하려고 매번 50만 토큰의 기록을 들고 갔습니다.

놀라운 건 출처였습니다. 거대한 파일 하나나 폭주한 도구 출력 하나가 아니었습니다. 세션이 계속 길어졌고, 매 단계가 그 전부를 다시 읽었습니다.

추정치가 아닙니다. 제공사가 호출마다 보고하는 사용량을, 에이전트가 실행된 컴퓨터에서 세션 로그로 읽은 값입니다. 아무것도 업로드하지 않았습니다.

다음 장: 왜 "토큰 절약"은 잘못된 목표인가, 그리고 대신 무엇을 재야 하는가.
