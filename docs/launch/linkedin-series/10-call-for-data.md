# 연구 노트 10/10 — 세션 하나는 증명이 아닙니다

- 게시일: 화 2026-11-10, 08:00–09:00 KST
- 목적: 요청. 프리프린트 전에 독자를 기여자로 만든다.
- 이미지: 없음
- 선행 조건: `pxt agent bound --export | pxt contribute send -`가 들어간 PyPI 릴리스 (ADR-0010)
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 722자, 게시물 전체 2024자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 10/10] 세션 하나는 증명이 아닙니다

지금까지 보여 드린 결과는 모두 세션 하나에서 나왔습니다. 사례 연구일 뿐, 증명이 아닙니다. 그 이상으로 포장하지 않겠습니다.

그래서 다음 단계를 미리 정해 두었습니다. 무엇을 어떻게 잴지, 어떤 세션을 빼고 어떤 통계를 쓸지, 무엇은 주장하지 않을지를 데이터를 보기 전에 문서로 고정했습니다. ChatGPT, Claude, Gemini, Grok, 코딩 에이전트까지 여러 제품의 세션을 같은 기준으로 잴 것입니다. 사용 여부를 판정하는 방식도 사람이 직접 검증합니다.

기준을 미리 고정한 이유는 하나입니다. 결과를 본 뒤에 기준을 바꾸면, 원하는 숫자는 언제든 만들어 낼 수 있기 때문입니다.

여러분의 도움이 필요합니다. 코딩 에이전트를 쓰신다면 pip install pickaxetax, pxt agent bound 두 줄이면 됩니다. 내 세션이 꼭 필요했던 최소 컨텍스트에 얼마나 가까웠는지를 내 컴퓨터 안에서 계산합니다. 괜찮으시다면 그 숫자를 익명으로 보내 주세요. 텍스트도, 파일 경로도, 프로젝트 이름도 담기지 않습니다.

결과가 여러 세션에서도 유지되면, AI 메모리 수요의 상당 부분을 설계로 피할 수 있다는 증거가 됩니다. 유지되지 않아도 그대로 공개하겠습니다. 다음 데이터센터를 짓기 전에, 어느 쪽이든 알아 둘 가치가 있습니다.

연재를 함께해 주셔서 감사합니다. 다음 노트는 여러분의 데이터로 쓰겠습니다.

— English —

[Research note 10/10] One session is not proof

Every result so far came from a single session. That is a case study, not proof, and I won't dress it up as more.

So the next step is fixed in advance. What we measure and how, which sessions are excluded, which statistics we use, and what we will not claim were all written down before seeing any data. Sessions from ChatGPT, Claude, Gemini, Grok and coding agents will be measured the same way, and the method that decides what counts as "used" will be checked by people.

There is one reason to fix the rules in advance: if you change them after seeing the results, you can always produce the number you wanted.

We need your help. If you use a coding agent, two lines are enough: pip install pickaxetax, then pxt agent bound. It computes, on your own machine, how close your sessions came to the least context they needed. If you're willing, send the numbers anonymously. No text, no file paths, no project names.

If the result holds across sessions, it's evidence that much of AI's memory demand can be avoided by design. If it doesn't, we'll publish that too. Either way, it's worth knowing before the next data center is built.

Thank you for following along. The next note will be written with your data.

#AntiTokenMaxing

## 출처

- `research/protocol/backtest-v1.md` (사전 등록), `research/protocol/data-intake.md`.
