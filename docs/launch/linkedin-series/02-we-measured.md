# 연구 노트 2/10 — 1을 쓰려고 124를 읽었습니다

- 게시일: 화 2026-10-13, 08:00–09:00 KST
- 목적: 첫 실측 숫자. 구체적이고 재현 가능하며 익명이다.
- 이미지: 없음
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 727자, 게시물 전체 2082자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 2/10] 1을 쓰려고 124를 읽었습니다

첫 측정 대상은 실제 코딩 에이전트 세션 하나였습니다. 사람이 맡긴 일을 AI가 몇 시간 동안 스스로 처리하는, 요즘 토큰을 가장 많이 쓰는 방식입니다.

결과는 이렇습니다. API 호출 143번. 에이전트가 써낸 양은 약 35만 토큰이었는데, 그걸 쓰려고 읽은 양은 4,348만 토큰이었습니다. 1을 쓰려고 124를 읽은 셈입니다. 한 쪽을 쓰려고 124쪽을 다시 읽은 것과 같습니다.

읽은 것의 97.8%는 캐시로 처리되어 값이 쌌습니다. 하지만 싸다고 해서 없는 것은 아닙니다. 컨텍스트는 최대 50만 7,710토큰까지 불어났고, 세션 후반의 호출은 다음 한 걸음을 정하려고 매번 50만 토큰을 들고 갔습니다.

왜 이렇게 될까요? 대화형 AI는 지난 대화를 기억해 두지 않습니다. 매번 전체를 다시 받아 처음부터 계산합니다. 그래서 대화가 두 배로 길어지면 다시 읽는 양은 네 배 가까이 늘어납니다.

의외였던 것은 원인입니다. 거대한 파일 하나 때문이 아니었습니다. 세션이 길어질수록 모든 단계가 지난 전부를 다시 읽었을 뿐입니다. 에이전트가 일을 잘못한 것이 아니라, 지금의 방식이 원래 그렇게 동작한다는 점이 더 중요합니다.

이 숫자는 추정이 아닙니다. 제공사가 호출마다 기록한 사용량을, 그 컴퓨터 안에서 그대로 읽은 값입니다. 바깥으로는 아무것도 보내지 않았습니다.

다음 노트: "토큰을 아끼자"는 목표로는 왜 부족한가.

— English —

[Research note 2/10] It read 124 to write 1

The first thing we measured was one real coding-agent session: an AI working on its own for hours on a task a person gave it. Today that is the most token-hungry way to use AI.

Here is the result. 143 API calls. The agent wrote about 350 thousand tokens, and to write them it read 43.5 million. It read 124 for every 1 it wrote, like re-reading 124 pages to write one.

97.8% of those reads were served from cache, so they were cheap. But cheap is not free. The context grew to 507,710 tokens, and near the end every call carried half a million tokens just to decide its next step.

Why does this happen? A conversational AI doesn't remember the conversation between turns. It receives the whole thing again and computes from the start each time. So when a conversation gets twice as long, the re-reading grows nearly four times.

The surprise was the cause. It wasn't one huge file. As the session grew longer, every step simply re-read everything before it. What matters more is that the agent did nothing wrong: this is simply how today's approach works.

These numbers are not estimates. They are the usage the provider recorded for each call, read on the machine where the session ran. Nothing was sent anywhere.

Next: why "save tokens" is not a good enough goal.

#AntiTokenMaxing

## 출처

- Facts 표: 호출 143, 입력 43,477,948, 캐시 97.8%, 최대 컨텍스트 507,710, 출력 349,743 (124배).
