# 연구 노트 8/10 — 보이지 않는 3분의 1

- 게시일: 화 2026-11-03, 08:00–09:00 KST
- 목적: 감시자 역할. 측정에 근거한 구체적이고 합리적인 공개 요청.
- 이미지: `docs/img/series/ch08-invisible.png`
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 706자, 게시물 전체 2041자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 8/10] 보이지 않는 3분의 1

지난 노트의 세션에서, 모델이 처리한 입력의 32.4%는 기록 속 어떤 내용과도 연결되지 않았습니다.

사용자의 메시지도, 도구의 출력도, 에이전트의 답도 아니었습니다. 제공사가 기록한 사용량이 그만큼 늘었으니 분명히 존재했지만, 정체는 알 수 없습니다. 숨겨진 추론일 수도, 소프트웨어가 덧붙인 틀일 수도 있습니다. 바깥에서는 확인할 방법이 없습니다.

이 비율은 우리가 볼 수 있는 기록과 제공사가 기록한 사용량의 차이로 계산했습니다. 기록에 보이는 내용은 실측에 맞춰 보정했고, 남는 차이를 보이지 않는 부분으로 두었습니다.

이 3분의 1 때문에 계산이 달라집니다. 고정된 시스템 프롬프트와 보이지 않는 부분을 줄일 수 없다면, 어떤 방법으로도 그 세션 입력의 57.5% 이상은 줄일 수 없습니다.

그래서 AI 모델을 서비스하는 곳에 세 가지를 요청합니다. 요청마다 사용자가 볼 수 없는 컨텍스트가 얼마인지, 캐시된 컨텍스트가 메모리에 얼마나 오래 머무는지, 토큰 하나가 메모리를 얼마나 차지하는지 공개해 주십시오. 영업 비밀을 묻는 것이 아닙니다. AI를 쓰는 데 실제로 어떤 하드웨어가 드는지 모두가 볼 수 있게 하자는 것입니다.

우리는 AI 기업의 반대편에 서려는 것이 아닙니다. 얼마나 많이 태웠는지가 아니라 얼마나 적게 쓰고 해냈는지로 평가받는 산업을 바랍니다.

다음 노트: 연산 버블 지수.

— English —

[Research note 8/10] The invisible third

In the session from the last note, 32.4% of the input the model processed could not be linked to anything in the log.

It wasn't the user's messages, the tool outputs or the agent's replies. The provider's recorded usage grew by that much, so it was certainly there, but what it was is unknown. It could be hidden reasoning, or framing added by the software. From the outside there is no way to check.

We computed it as the gap between the log we can see and the usage the provider recorded. The visible content was calibrated to the measured usage, and whatever remained was counted as invisible.

That third changes the math. If the fixed system prompt and the invisible part can't be reduced, no method could cut more than 57.5% of that session's input.

So we ask those who serve AI models for three things: disclose how much of each request is context the user can't see, how long cached context stays in memory, and how much memory one token occupies. This is not a request for trade secrets. It's so that everyone can see what hardware using AI actually takes.

We aren't trying to stand against AI companies. We want an industry judged not by how much it burned, but by how little it needed to get the job done.

Next: the Compute Bubble Index.

#AntiTokenMaxing

## 출처

- 같은 파일: 보이지 않는 입력 32.4%, 고정 기반 10.1%, 상한 57.5%. 보정 방법은 `research/belady-bound.md` §3.
