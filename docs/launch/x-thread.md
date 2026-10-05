# X thread

## English

**1/**
Your AI re-reads the entire conversation on every turn.

You pay for every re-read. Your "thanks!" at turn 40 re-processes all 40 turns.

I built a free, open-source tool that shows how much of that compute you didn't need. It runs in your browser and nothing is uploaded. #AntiTokenMaxing
[link to web app + OG card]

**2/**
Paste a chat (or use a share link) and you get its skeleton: agenda, topic threads, depth. Then you see where it leaked:
- thank-you / ok messages
- answers thrown away by corrections and re-asks
- unrelated old topics re-sent on every reply

The example chat: 61.8% avoidable.

**3/**
Coding agents are where it gets wild.

One real Claude Code session, audited:
• 143 API calls
• 43.5M input tokens processed (97.8% from cache)
• peak context 508K
• ~350K tokens of output

It read about 120 tokens for every token it wrote.

**4/**
`pxt agent audit` finds this in your own sessions: re-reads of unchanged files, huge tool outputs, repeated failures, and how many times each was re-sent afterwards.

A small guard hook blocks re-reads of unchanged files and logs what it saved.

**5/**
Why "Pickaxe Tax"?

In a gold rush, the people selling pickaxes get rich. In the AI boom, more GPUs and more data centers are the pickaxes, and a large share of the demand for them is waste we can measure.

**6/**
Privacy by construction:
• the web app's CSP blocks all outgoing requests
• the proxy and auditor store counts only
• contributions are allowlisted numbers you preview first, one click and no account

The analyzer calls no LLM. A tool about saving tokens shouldn't spend them.

**7/**
It's alpha and open source (Apache-2.0, data ODbL).
`pip install pickaxetax`
Web: [link]
Code: github.com/graviton94/pickaxetax

Try it on your longest chat and tell me your number. #AntiTokenMaxing

## 한국어

**1/**
AI는 매 턴마다 대화 전체를 처음부터 다시 읽습니다.
그 재독 비용은 우리가 냅니다. 40번째 턴의 "고마워"는 40턴을 통째로 다시 처리합니다.

얼마나 불필요했는지 보여 주는 무료 오픈소스를 만들었습니다. 브라우저 안에서만 돌아가고, 아무것도 업로드되지 않습니다. #AntiTokenMaxing
[웹앱 링크]

**2/**
대화를 붙여넣으면(공유 링크도 가능) 대화의 골격(아젠다·주제 갈래·깊이)과 새어 나간 지점이 보입니다.
- 감사·확인 메시지
- 정정·재질문으로 버려진 답변
- 관련 없는 이전 주제의 재전송

예시 대화는 61.8%가 회피 가능했습니다.

**3/**
코딩 에이전트에서는 차원이 다릅니다. 실제 Claude Code 세션 하나를 감사해 보니:
• API 호출 143회
• 입력 처리 4,348만 토큰 (97.8%가 캐시)
• 최대 컨텍스트 50.8만
• 출력 약 35만

쓰는 토큰 1개마다 약 120개를 읽었습니다.

**4/**
`pxt agent audit`로 내 세션에서도 찾을 수 있습니다. 바뀌지 않은 파일을 다시 읽은 것, 거대한 도구 출력, 반복된 실패, 그리고 그것들이 이후 몇 번이나 재전송됐는지까지 보여 줍니다. 가드 훅은 그런 재독을 막고, 아낀 양을 기록합니다.

**5/**
왜 "곡괭이세(Pickaxe Tax)"일까요? 골드러시에서 돈을 버는 건 곡괭이 판매자입니다. AI 붐의 곡괭이는 GPU와 데이터센터이고, 그 수요의 상당 부분은 측정 가능한 낭비입니다.

**6/**
구조부터 프라이버시를 지킵니다. 웹앱은 외부 전송이 원천 차단되어 있고, 측정은 숫자만 남깁니다. 기여는 미리 본 숫자만 원클릭으로, 계정 없이 합니다. 분석기는 AI를 호출하지 않습니다.

**7/**
알파 버전, 오픈소스입니다.
`pip install pickaxetax`
github.com/graviton94/pickaxetax
가장 긴 대화로 해 보시고 숫자를 알려 주세요. #AntiTokenMaxing
