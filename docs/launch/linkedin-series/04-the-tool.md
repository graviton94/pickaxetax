# 연구 노트 4/10 — 내 대화의 낭비를 직접 보세요

- 게시일: 화 2026-10-20 (**출시일**: 같은 날 X 스레드, Reddit 시작), 08:00–09:00 KST
- 목적: 첫 링크. 10초 안에 써 보게 하고, 검증 가능한 개인정보 보호를 보여 준다.
- 이미지: `docs/img/result.png`
- 선행 조건: `../README.md`의 출시 점검 목록 (main에서 사이트 갱신, OG 미리보기 확인)
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 724자, 게시물 전체 2122자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 4/10] 내 대화의 낭비를 직접 보세요

오늘은 첫 번째 도구를 공개합니다. AI와 나눈 대화를 붙여넣으면, 쓰지 않아도 됐던 연산이 얼마인지 보여 줍니다. 붙여넣고 분석을 누르면 몇 초 안에 결과가 나옵니다.

예시 대화로 돌려 보면 연산의 61.8%가 피할 수 있는 것이었습니다. 원인은 세 가지였습니다. 전체를 다시 읽게 만든 "고마워" 메시지, 정정한 뒤 버려진 답변, 그리고 매 답변마다 함께 다시 보내진 관계없는 주제입니다. 도구는 대화의 뼈대(주제, 흐름, 깊이)를 그려 주고, 한 번에 끝낼 수 있었던 질문도 제안합니다.

"피할 수 있었다"의 기준도 화면에 함께 적어 두었습니다. 주제마다 새 대화를 열고, 인사와 버려진 답을 뺐을 때와 비교한 값입니다. 과장하지 않기 위해 숫자의 정의를 숨기지 않았습니다.

가장 신경 쓴 것은 개인정보입니다. 이 페이지는 브라우저 안에서만 동작하고, 보안 정책으로 모든 외부 전송을 막아 두었습니다. 실수로라도 대화가 업로드될 수 없습니다. 코드가 바뀔 때마다 실제 브라우저에서 이를 다시 검증합니다.

ChatGPT·Claude 내보내기 파일과 공유 링크도 읽습니다. 무료이고, 가입도 필요 없습니다. 직접 해 보시고 결과가 이상하면 알려 주세요. 틀린 부분은 고쳐서 다음 노트에 밝히겠습니다.

https://graviton94.github.io/pickaxetax/

다음 노트: 코딩 에이전트, 숫자가 훨씬 커지는 곳.

— English —

[Research note 4/10] See the waste in your own conversations

Today the first tool goes public. Paste a conversation you had with an AI, and it shows how much of the compute was never needed. Paste, press Analyze, and the result appears in seconds.

On the built-in example, 61.8% of the compute was avoidable. Three things caused it: "thanks" messages that made the model re-read everything, answers thrown away after a correction, and unrelated topics re-sent with every reply. The tool draws the conversation's skeleton (topics, flow, depth) and suggests the one prompt that would have done it in one go.

The definition of "avoidable" is shown right next to the number: the same useful exchanges with a fresh chat per topic, without the thank-yous and the discarded answers. To avoid overclaiming, the definition is never hidden.

Privacy got the most care. The page runs entirely in your browser, and its security policy blocks every outgoing request, so your conversation cannot be uploaded even by mistake. That is checked again in a real browser every time the code changes.

It also reads ChatGPT and Claude export files and share links. It's free, with no sign-up. Try it, and tell me if a result looks wrong. I'll fix it and say so in a later note.

https://graviton94.github.io/pickaxetax/

Next: coding agents, where the numbers get much bigger.

#AntiTokenMaxing

## 출처

- Facts 표: 예시 대화 61.8% (367 → 140 연산 단위), CSP `connect-src 'none'` (CI에서 검증).
