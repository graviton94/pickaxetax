# Chapter 5 — Coding agents

- Date: Thu 2026-10-22
- Purpose: reach developers (the first users per the charter). Show a non-obvious finding, the 3× overcount.
- Image: none (or a terminal screenshot of `pxt agent audit`)

## Post (English)

#AntiTokenMaxing · Chapter 5/10

If you use a coding agent, you're running the most token-hungry workload most people will ever touch. So we built an auditor for it.

`pxt agent audit` reads your Claude Code session logs locally and reports:
• how much input was processed and how much came from cache;
• the peak context;
• files re-read without changes;
• huge tool outputs, and how many times each was re-sent afterwards;
• failed attempts that were repeated.

The first thing we learned was about measurement itself. A single model response is written to the log as several lines, and each line repeats the same usage numbers. Add them up naively and you overcount by about 3×. In one session, 126 of 140 responses were split that way. Any tool that sums the log line by line is wrong.

There's also an optional guard hook. It blocks re-reading a file that hasn't changed (once, then allows), and it logs the tokens it saved. It fails open and stores no file contents.

```
pip install pickaxetax
pxt agent audit
```

Using another agent? Adapters are built from real (redacted) logs, never guessed. Send one and we'll add it.

Next chapter: the hypothesis that failed, and why I'm publishing it.

https://github.com/graviton94/pickaxetax

## First comment (한국어)

#AntiTokenMaxing · 5/10장

코딩 에이전트를 쓴다면, 대부분의 사람이 다뤄 볼 작업 중 토큰을 가장 많이 먹는 작업을 돌리고 있는 겁니다. 그래서 감사 도구를 만들었습니다.

`pxt agent audit`는 Claude Code 세션 로그를 로컬에서 읽고 다음을 보여 줍니다.
• 처리한 입력과 그중 캐시 비율
• 최대 컨텍스트
• 바뀌지 않은 파일의 재독
• 거대한 도구 출력과 그것이 이후에 몇 번 다시 보내졌는지
• 반복된 실패

첫 번째 교훈은 측정 자체에 관한 것이었습니다. 모델 응답 하나가 로그에는 여러 줄로 기록되고, 줄마다 같은 사용량이 반복됩니다. 그냥 더하면 약 3배 과다 집계됩니다. 한 세션에서는 응답 140개 중 126개가 이렇게 나뉘어 있었습니다.

선택형 가드 훅도 있습니다. 바뀌지 않은 파일을 다시 읽으려 하면 한 번 막고, 절약한 토큰을 기록합니다. 오류가 나면 막지 않고 통과시키며, 파일 내용은 저장하지 않습니다.

다른 에이전트를 쓰신다면 개인정보를 지운 로그 샘플을 보내 주세요. 추측이 아니라 실제 로그로 지원을 추가합니다.
