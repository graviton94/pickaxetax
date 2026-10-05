# Chapter 8 — The invisible third

- Date: Tue 2026-11-03
- Purpose: the watchdog face. A specific, reasonable ask to providers, backed by a measurement.
- Image: `docs/img/series/ch08-invisible.png`

## Post (English)

#AntiTokenMaxing · Chapter 8/10

In the session from the last chapter, 32.4% of all the input the model processed could not be matched to anything in the session log.

Not the user's messages, not the tool outputs, not the agent's replies. We know it was there because the provider's own usage numbers grew by that much. We don't know what it was. It could be hidden reasoning, framing added by the software, or something else. Nobody outside can tell.

That invisible third changes the math. If the fixed system prompt and the invisible part can never be removed, no context policy could save more than 57.5% of that session's input. Disclosure could move that ceiling in either direction, and only providers can disclose.

So here's a concrete, reasonable ask to everyone who serves AI models:
1. Report how much of each request is context the user can't see.
2. Report how long cached context stays resident.
3. Publish the memory each token of context occupies (KV-cache bytes per token) for the models you serve.

None of this reveals a trade secret. All of it lets users, researchers and investors see what AI usage actually costs in hardware.

We're not against AI companies. We want the industry measured by how little compute it needs, not how much it burns.

Next chapter: the Compute Bubble Index.

## First comment (한국어)

#AntiTokenMaxing · 8/10장

지난 장의 세션에서, 모델이 처리한 전체 입력의 32.4%는 세션 기록의 어떤 내용과도 연결되지 않았습니다.

사용자 메시지도, 도구 출력도, 에이전트의 답도 아닙니다. 제공사의 사용량 수치가 그만큼 늘었으니 존재했던 것은 확실합니다. 하지만 정체는 알 수 없습니다. 숨겨진 추론일 수도, 소프트웨어가 덧붙인 틀일 수도, 다른 무엇일 수도 있습니다. 바깥에서는 알 길이 없습니다.

이 "보이지 않는 3분의 1" 때문에 계산이 달라집니다. 고정 시스템 프롬프트와 보이지 않는 부분을 뺄 수 없다면, 어떤 컨텍스트 정책도 그 세션 입력의 57.5% 이상은 줄일 수 없습니다.

그래서 AI 모델을 서비스하는 모든 곳에 구체적이고 합리적인 요청을 드립니다.
1. 요청마다 사용자가 볼 수 없는 컨텍스트가 얼마인지 보고해 주십시오.
2. 캐시된 컨텍스트가 얼마나 오래 메모리에 머무는지 보고해 주십시오.
3. 서비스하는 모델의 토큰당 메모리 점유량(KV 캐시 바이트)을 공개해 주십시오.

영업 비밀을 드러내는 요청이 아닙니다. 사용자, 연구자, 투자자가 AI 사용의 실제 하드웨어 비용을 볼 수 있게 하자는 것입니다.

우리는 AI 기업의 반대편에 서려는 것이 아닙니다. 업계가 얼마나 많이 태웠는지가 아니라 얼마나 적게 쓰고 해냈는지로 평가받기를 바랍니다.
