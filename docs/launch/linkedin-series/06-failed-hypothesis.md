# 연구 노트 6/10 — 첫 가설은 틀렸습니다

- 게시일: 화 2026-10-27, 08:00–09:00 KST
- 목적: 실패를 통해 신뢰를 얻는다. 7번 노트의 질문을 연다.
- 이미지: 없음
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 709자, 게시물 전체 2137자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 6/10] 첫 가설은 틀렸습니다

이번 노트는 실패의 기록입니다. 처음 세운 가설은 이랬습니다. "AI 에이전트가 들고 다니는 컨텍스트의 대부분은 다시는 쓰이지 않는 죽은 정보다."

첫 실험은 죽은 정보가 1%뿐이라고 답했습니다. 깔끔한 반증처럼 보였지만, 들여다보니 측정이 틀렸습니다. 나중의 출력과 단어 하나만 겹쳐도 "썼다"고 셌기 때문입니다. 파일 경로나 흔한 키워드는 어디에나 나오니, 거의 모든 것이 쓰인 것처럼 보였습니다.

기준을 다듬었습니다. 흔한 단어를 빼고, 각 조각의 고유한 내용이 다시 나오지 않는 비율을 쟀습니다. 이번에는 54%였습니다. 하지만 모델은 읽은 것을 그대로 옮겨 쓰지 않고도 활용할 수 있으니, 이것도 상한일 뿐입니다. 실제로 버려도 되는 양은 그보다 적을 것입니다.

실패를 굳이 공개하는 이유가 있습니다. 틀린 숫자를 그럴듯하게 발표하는 것이야말로 이 프로젝트가 비판하려는 거품과 같기 때문입니다.

두 숫자 모두 답이 아니었습니다. 이 과정에서 배운 것은, 측정하는 도구부터 의심해야 한다는 점입니다. 진짜 실수는 질문이었습니다. "다시 쓰이는가?"가 아니라 "그 사이의 매 단계에서 필요한가?"를 물어야 했습니다. 이 질문에는 1966년 컴퓨터과학이 남긴 정확한 답이 있습니다. 실패에서 나온 이 질문이, 다음 노트의 가장 중요한 결과로 이어졌습니다.

다음 노트: 잊지 말고, 내려놓았다가 다시 부르세요.

— English —

[Research note 6/10] Our first hypothesis was wrong

This note is a record of failure. The first hypothesis was: "Most of the context an AI agent carries around is dead information that is never used again."

The first experiment said only 1% was dead. It looked like a clean refutation, until we looked closer and found the measurement was wrong. It counted something as "used" if a later output shared even one word with it. File paths and common keywords appear everywhere, so nearly everything looked used.

We refined it: drop the common words, and measure how much of each piece's distinctive content never appears again. This time it was 54%. But a model can use what it read without copying it word for word, so that is only an upper bound. The amount that could really be dropped would be smaller.

There is a reason to publish a failure. Presenting a wrong number convincingly is exactly the kind of bubble this project sets out to criticize.

Neither number was the answer. The lesson along the way: doubt the measuring tool first. The real mistake was the question. We should have asked not "is it ever used again?" but "is it needed at each step in between?" That question has an exact answer, left to us by computer science in 1966. This question, born from a failure, led to the most important result in the next note.

Next: don't forget it; set it aside and call it back.

#AntiTokenMaxing

## 출처

- `research/hypotheses.md` H1 (1%), H1′ (54%, 상한).
