# Chapter 10 — n = 1 is not proof

- Date: Tue 2026-11-10
- Purpose: the ask. Turn readers into contributors before the preprint.
- Image: none
- Prerequisite: the bound must be part of the anonymous `agent` contribution, so that `pxt agent bound --export | pxt contribute send -` works (ADR-0008 follow-up 1). Until it ships, ask people to run `pxt agent bound` and post the summary in a GitHub issue instead.

## Post (English)

#AntiTokenMaxing · Chapter 10/10

Everything I showed in the last chapters comes from one session. One. That's a case study, not proof, and I won't present it as more than that.

Before we publish the paper ("Paging, Not Forgetting", an English preprint with a Korean summary), we need many sessions, from different people, different agents and different kinds of work. The target is at least 30 sessions from at least two agents.

If you use a coding agent, it takes a minute:

```
pip install pickaxetax
pxt agent bound
```

It computes, on your machine, how close each of your sessions came to the least context it needed. If you're willing, send the numbers anonymously: counts only, no text, no file paths, no project names. You see exactly what is sent.

If the result holds across sessions, it's evidence that a large share of today's AI memory demand is avoidable by design. If it doesn't hold, we'll publish that too. Both outcomes are worth knowing before the world builds the next hundred data centers.

Thank you for following the series. The next posts will be the results, from your data.

https://github.com/graviton94/pickaxetax

## First comment (한국어)

#AntiTokenMaxing · 10/10장

지난 장들에서 보여 드린 결과는 모두 세션 하나에서 나왔습니다. 단 하나입니다. 사례 연구이지 증명이 아니고, 그 이상으로 포장하지 않겠습니다.

논문("Paging, Not Forgetting", 영문 프리프린트 + 한글 요약)을 내기 전에 서로 다른 사람, 다른 에이전트, 다른 작업의 세션이 많이 필요합니다. 목표는 에이전트 2종 이상, 세션 30개 이상입니다.

코딩 에이전트를 쓰신다면 1분이면 됩니다.

    pip install pickaxetax
    pxt agent bound

내 컴퓨터에서, 각 세션이 꼭 필요했던 최소 컨텍스트에 얼마나 가까웠는지 계산합니다. 괜찮으시다면 그 숫자를 익명으로 보내 주세요. 숫자만 담기고, 텍스트·파일 경로·프로젝트 이름은 담기지 않습니다. 무엇이 전송되는지 정확히 보여 드립니다.

여러 세션에서도 결과가 유지된다면, 오늘날 AI 메모리 수요의 상당 부분은 설계로 피할 수 있다는 증거가 됩니다. 유지되지 않는다면 그것도 공개하겠습니다. 세상이 다음 데이터센터 백 개를 짓기 전에, 두 결과 모두 알 가치가 있습니다.

연재를 따라와 주셔서 감사합니다. 다음 글은 여러분의 데이터로 만든 결과입니다.
