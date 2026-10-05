# Chapter 4 — The tool: see your own waste

- Date: Tue 2026-10-20 — **launch day**. The X thread (`../x-thread.md`) goes out the same morning, and Reddit starts that day (one subreddit per day, see `../README.md`).
- Purpose: first link. Try it in 10 seconds, with privacy you can verify.
- Image: `docs/img/result.png`
- Prerequisite: the launch checklist in `../README.md` (site live on `main`, OG preview checked).

## Post (English)

#AntiTokenMaxing · Chapter 4/10

Today the first tool is public. Paste an AI conversation and see how much of its compute you didn't need.

In the built-in example, 61.8% of the compute was avoidable. Three things caused it:
• thank-you messages that made the model re-read everything;
• answers that were thrown away after a correction;
• unrelated topics re-sent with every reply.

It shows the conversation's skeleton (agenda, flow, depth), where the compute leaked, and a single prompt that would have done the job in one go.

The part I care about most: it runs entirely in your browser. The page's security policy blocks every outgoing request, so it cannot upload your conversation even by mistake. That's verified in a real browser on every change.

It also works with ChatGPT/Claude exports and, through a bookmarklet, with share links.

Free and open source. No account. Nothing uploaded.

Try it: https://graviton94.github.io/pickaxetax/
Code: https://github.com/graviton94/pickaxetax

Next chapter: coding agents, where the numbers get much bigger.

## First comment (한국어)

#AntiTokenMaxing · 4/10장

첫 번째 도구를 공개합니다. AI 대화를 붙여넣으면, 쓰지 않아도 됐던 연산이 얼마인지 보여 줍니다.

내장 예시에서는 연산의 61.8%가 피할 수 있는 것이었습니다. 원인은 셋이었습니다.
• 전체를 다시 읽게 만든 "고마워" 메시지
• 정정 뒤에 버려진 답변
• 매 답변마다 함께 다시 보내진, 관계없는 주제

대화의 골격(아젠다·흐름·깊이), 연산이 샌 지점, 그리고 한 번에 끝냈을 프롬프트를 보여 줍니다.

가장 중요한 점: 전부 브라우저 안에서만 동작합니다. 페이지의 보안 정책이 모든 외부 요청을 막기 때문에, 실수로도 대화를 업로드할 수 없습니다. 변경할 때마다 실제 브라우저에서 이를 검증합니다.

ChatGPT·Claude 내보내기 파일도, 북마클릿으로 공유 링크도 읽습니다. 무료 오픈소스이고, 가입이 필요 없으며, 아무것도 업로드하지 않습니다.

https://graviton94.github.io/pickaxetax/
