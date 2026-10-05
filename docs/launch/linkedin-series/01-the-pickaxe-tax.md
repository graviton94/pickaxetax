# Chapter 1 — The pickaxe tax

- Date: Thu 2026-10-08, 08:00–09:00 KST
- Purpose: name the problem, promise the series. No link yet; the post should spread on the idea alone.
- Image: `docs/img/og.png`

## Post (English)

#AntiTokenMaxing · Chapter 1/10

Every time you send a message to an AI chat, it reads the entire conversation again. Every message, from the start.

That is how these models work. A reply is computed from the whole history, so the cost of a conversation grows with the square of its length. A late requirement, a re-ask, a polite "thanks!" at the end of a long chat: each one makes the machine re-read everything before it.

Multiply that by hundreds of millions of people and by coding agents that run for hours. A real part of the demand for new GPUs, data centers and power comes from re-reading, not from new thinking.

In a gold rush, the people who reliably get rich are the ones selling pickaxes. In the AI boom, the pickaxes are chips and data centers, and the re-reading is a tax we all pay on every turn.

I'm starting a public-interest, open-source project to measure that tax and cut it: Pickaxe Tax.

Over the next five weeks I'll publish the plan chapter by chapter, with the numbers, the theory, the tools, and the experiments that failed.

Next chapter: what happened when we measured one real coding-agent session.

#AI #Sustainability

## First comment (한국어)

#AntiTokenMaxing · 1/10장

AI 채팅에 메시지를 보낼 때마다, AI는 대화 전체를 처음부터 다시 읽습니다.

모델이 원래 그렇게 동작합니다. 답은 전체 기록을 바탕으로 계산되기 때문에 대화 비용은 길이의 제곱으로 커집니다. 늦게 붙인 조건, 재질문, 긴 대화 끝의 "고마워" 한마디도 그 앞의 모든 내용을 다시 읽게 만듭니다.

여기에 수억 명의 사용자와 몇 시간씩 돌아가는 코딩 에이전트를 곱해 보세요. 새 GPU, 데이터센터, 전력 수요의 상당 부분은 새로운 생각이 아니라 "다시 읽기"에서 나옵니다.

골드러시에서 확실히 돈을 버는 건 곡괭이 판매자입니다. AI 붐의 곡괭이는 반도체와 데이터센터이고, 다시 읽기는 우리가 매 턴 내는 세금입니다.

그 세금을 측정하고 줄이는 공익 오픈소스 프로젝트, Pickaxe Tax(곡괭이세)를 시작합니다. 앞으로 5주 동안 계획을 장별로 공개합니다. 숫자, 이론, 도구, 그리고 실패한 실험까지 공개합니다.

다음 장: 실제 코딩 에이전트 세션 하나를 측정했더니.
