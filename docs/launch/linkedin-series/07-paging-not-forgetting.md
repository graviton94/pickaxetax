# Chapter 7 — Paging, not forgetting

- Date: Thu 2026-10-29
- Purpose: the headline scientific result. Simple chart, one sentence takeaway: "carry pointers, not payloads".
- Image: `docs/img/series/ch07-paging.png`

## Post (English)

#AntiTokenMaxing · Chapter 7/10

In 1966, László Belady showed that if you know the future, you can compute the best possible cache. Nobody knows the future, but the result gives a bound that no real system can beat.

We applied the same idea to AI agents. For one long real coding-agent session (322 calls, 149 million input tokens), we computed the least context an oracle would have kept: something that knows exactly which earlier content each step will use.

Two policies, two very different answers:
• Forget content after its last use, and never bring it back: 9.1% of the input saved.
• Set content aside between uses and fetch it back exactly when it's needed: 50.1% saved. That's 47.5% even if each fetch costs 1,000 tokens.

Most context does get used again, just not at every step in between. The waste isn't old information. It's information carried around while it isn't needed.

The design lesson is an old one from databases: keep pointers, not payloads. An agent should hold "file X, version Y, lines 10–40" and look it up when needed, not carry the whole file through every step. The largest visible part of that session's context was content the agent had already written to disk itself.

Honest caveats: n = 1, and "use" is detected from the text. The method, the proof and a sensitivity analysis are public.

Next chapter: the third of the input nobody can see.

https://github.com/graviton94/pickaxetax/blob/HEAD/research/belady-bound.md

## First comment (한국어)

#AntiTokenMaxing · 7/10장

1966년 벨레이디는 미래를 안다면 최적의 캐시를 계산할 수 있음을 보였습니다. 미래는 아무도 모르지만, 이 결과는 어떤 실제 시스템도 넘을 수 없는 하한을 줍니다.

같은 원리를 AI 에이전트에 적용했습니다. 긴 실제 코딩 에이전트 세션 하나(호출 322회, 입력 1억 4,900만 토큰)에서, 각 단계가 앞의 어떤 내용을 쓸지 정확히 아는 오라클이라면 컨텍스트를 최소 얼마나 남겼을지 계산했습니다.

두 정책의 답은 크게 달랐습니다.
• 마지막으로 쓴 뒤에 버리고 다시 부르지 않기: 입력 9.1% 절감
• 쓰는 사이에는 내려놓았다가 필요할 때 정확히 다시 부르기: **50.1% 절감** (다시 부를 때마다 1,000토큰이 들어도 47.5%)

대부분의 컨텍스트는 다시 쓰입니다. 다만 그 사이의 모든 단계에서 필요한 것은 아닙니다. 낭비는 오래된 정보가 아니라, 필요 없는 동안에도 들고 다니는 정보입니다.

교훈은 데이터베이스의 오래된 원칙과 같습니다. **내용이 아니라 포인터를 들고 다녀라.** 그 세션의 컨텍스트에서 눈에 보이는 것 중 가장 큰 부분은 에이전트가 이미 디스크에 써 둔 내용이었습니다.

한계: 표본은 세션 1개이고, "사용"은 텍스트로 탐지합니다. 방법, 증명, 민감도 분석은 모두 공개되어 있습니다.
