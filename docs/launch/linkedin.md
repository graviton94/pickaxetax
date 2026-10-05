# LinkedIn

## English

**Your AI re-reads the whole conversation on every turn, and someone pays for every re-read.**

Chat models process the entire history again for each reply, so the cost of a conversation grows with the square of its length. Late requirements, re-asks, a polite "thanks!" at the end, switching topics in the same chat: each of those quietly multiplies the compute behind the answer.

We measured it. One long coding-agent session processed **43.5 million input tokens** (97.8% served from cache) to produce about 350 thousand tokens of output, with the context peaking at 508K tokens.

So we built **Pickaxe Tax**, a free, open-source toolkit that makes this visible and cuts it:
• a web app that shows a conversation's skeleton and where the compute leaked. It runs entirely in the browser; nothing is uploaded.
• an auditor and guard hook for coding agents
• a local proxy that measures every request and skips the ones that need no model
• a public, privacy-preserving index of how much deployed AI compute actually produced value

Why the name? In a gold rush, the people selling pickaxes get rich. The AI boom's pickaxes are GPUs and data centers. Before we build more, let's use what we already have.

Try it: https://graviton94.github.io/pickaxetax/
Code: https://github.com/graviton94/pickaxetax
#AntiTokenMaxing #AI #Sustainability #OpenSource

## 한국어

**AI는 매 턴 대화 전체를 다시 읽고, 그 비용은 누군가가 냅니다.**

채팅형 AI는 답할 때마다 전체 대화를 다시 처리합니다. 그래서 대화 비용은 길이의 제곱으로 커집니다. 늦게 붙인 조건, 재질문, 마지막의 "고마워", 한 창에서의 주제 전환은 모두 답 뒤의 연산을 조용히 불립니다.

직접 측정해 봤습니다. 긴 코딩 에이전트 세션 하나가 약 35만 토큰을 쓰려고 **4,348만 토큰을 읽었습니다**(97.8%는 캐시). 최대 컨텍스트는 50.8만 토큰이었습니다.

그래서 **Pickaxe Tax(곡괭이세)**를 만들었습니다. 이 낭비를 보이게 하고 줄이는 무료 오픈소스입니다.
• 대화의 골격과 낭비 지점을 보여 주는 웹앱 (브라우저 안에서만 동작하고, 업로드하지 않습니다)
• 코딩 에이전트 감사 도구와 가드 훅
• 모든 요청을 측정하고, 모델이 필요 없는 요청은 건너뛰는 로컬 프록시
• 배치된 AI 연산 중 실제로 가치를 만든 비율을 보여 주는, 프라이버시를 지키는 공개 지수

골드러시에서 돈을 버는 건 곡괭이 판매자입니다. 더 짓기 전에, 가진 것부터 제대로 씁시다.

https://graviton94.github.io/pickaxetax/
#AntiTokenMaxing
