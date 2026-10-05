# 연구 노트 5/10 — 기록을 그냥 더하면 3배가 됩니다

- 게시일: 목 2026-10-22, 08:00–09:00 KST
- 목적: 개발자(헌장상 첫 사용자)에게 닿는다. 3배 과다 집계라는 의외의 발견.
- 이미지: 없음 (또는 `pxt agent audit` 터미널 화면)
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 741자, 게시물 전체 2149자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 5/10] 기록을 그냥 더하면 3배가 됩니다

코딩 에이전트는 대부분의 사람이 다뤄 볼 작업 가운데 토큰을 가장 많이 씁니다. 그래서 에이전트 세션을 감사하는 도구를 만들었습니다. 내 컴퓨터의 세션 기록을 읽어 캐시 비율, 최대 컨텍스트, 바뀌지 않은 파일을 다시 읽은 횟수, 거대한 출력이 몇 번이나 다시 보내졌는지를 보여 줍니다.

만들면서 가장 먼저 배운 것은 측정의 함정이었습니다. 모델의 응답 하나가 기록에는 여러 줄로 나뉘어 남고, 줄마다 같은 사용량이 되풀이됩니다. 그냥 더하면 약 3배로 부풀려집니다. 한 세션에서는 응답 140개 중 126개가 이렇게 나뉘어 있었습니다. 기록을 줄 단위로 더하는 도구는 틀린 숫자를 낸다는 뜻입니다.

2번 노트의 숫자도 바로 이 도구로 잰 것입니다. 같은 세션으로 계산해 보니, 작업이 바뀔 때마다 짧은 요약만 들고 새 세션을 열었다면 다시 읽은 양이 3분의 2가량 줄었을 것입니다. 결과 끝에는 무엇을 바꾸면 좋을지도 알려 줍니다. 예를 들면 작업이 바뀌었을 때 세션을 새로 시작하라는 식입니다.

선택해서 켤 수 있는 가드도 있습니다. 바뀌지 않은 파일을 다시 읽으려 하면 한 번 막고, 아낀 토큰을 기록합니다. 문제가 생기면 막지 않고 통과시키며, 파일 내용은 저장하지 않습니다.

pip install pickaxetax 한 줄이면 시작할 수 있습니다. Claude Code를 쓰신다면 플러그인으로도 설치할 수 있습니다.

다음 노트: 틀린 가설의 기록.

— English —

[Research note 5/10] Add up the log naively and you get 3×

Coding agents use more tokens than almost anything most people will ever run. So we built a tool to audit agent sessions. It reads the session logs on your machine and shows the cache rate, the peak context, how often unchanged files were re-read, and how many times huge outputs were re-sent.

The first lesson was a measurement trap. One model response is written to the log as several lines, and each line repeats the same usage. Add them up naively and you get about three times the real number. In one session, 126 of 140 responses were split this way. Any tool that sums the log line by line reports the wrong number.

The numbers in note 2 were measured with exactly this tool. On the same session, opening a fresh session with only a short summary whenever the task changed would have cut the re-reading by about two thirds. At the end it also suggests what to change, for example to start a fresh session when the task changes.

There is also an optional guard. When the agent tries to re-read a file that hasn't changed, it blocks that once and records the tokens saved. If anything goes wrong it lets the read through, and it never stores file contents.

One line gets you started: pip install pickaxetax. Claude Code users can also install it as a plugin.

Next: the record of a wrong hypothesis.

#AntiTokenMaxing

## 출처

- Facts 표: 응답 140개 중 126개가 여러 줄로 나뉨(ADR-0005). 작업별 새 세션 + 짧은 요약 시 66–70% 감소(`research/hypotheses.md` H2).
