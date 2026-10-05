# 연구 노트 7/10 — 잊지 말고, 내려놓았다가 다시 부르세요

- 게시일: 목 2026-10-29, 08:00–09:00 KST
- 목적: 가장 중요한 과학적 결과. 한 줄 교훈: 내용이 아니라 위치를 들고 다녀라.
- 이미지: `docs/img/series/ch07-paging.png`
- 상태: 초안 (대표와 함께 다듬는 중)
- 분량: 한국어 734자, 게시물 전체 2091자 (LinkedIn 한도 3,000자)

## 게시물 (한 게시물에 그대로 붙여넣기: 한국어 원문 → 영어 번역)

[연구 노트 7/10] 잊지 말고, 내려놓았다가 다시 부르세요

1966년 벨레이디는 미래를 안다면 가장 좋은 캐시를 계산할 수 있음을 보였습니다. 미래를 아는 사람은 없지만, 이 결과는 어떤 현실의 시스템도 넘을 수 없는 하한을 줍니다.

같은 원리를 AI 에이전트에 적용했습니다. 실제 세션 하나(호출 322번, 입력 1억 4,900만 토큰)에서, 각 단계가 앞의 어떤 내용을 쓸지 정확히 아는 오라클이라면 컨텍스트를 얼마나 남겼을지 계산했습니다.

두 방식의 답은 크게 달랐습니다. 마지막으로 쓴 뒤에 버리고 다시 부르지 않으면 9.1%를 아낍니다. 쓰지 않는 동안 내려놓았다가 필요할 때 다시 부르면 50.1%를 아낍니다. 다시 부를 때마다 1,000토큰이 든다고 해도 47.5%입니다.

대부분의 컨텍스트는 다시 쓰입니다. 다만 그 사이의 모든 단계에서 필요하지는 않습니다. 낭비는 오래된 정보가 아니라, 필요 없는 동안에도 들고 다니는 정보였습니다. 눈에 보이는 것 중 가장 큰 부분은 에이전트가 이미 디스크에 써 둔 내용이었습니다.

다시 부른다는 것은 이런 뜻입니다. 파일 전체를 들고 다니는 대신 "이 파일, 이 버전, 10~40번째 줄"이라는 위치만 기억해 두었다가, 필요할 때 다시 여는 것입니다.

교훈은 데이터베이스의 오래된 원칙과 같습니다. 내용이 아니라 위치를 들고 다니세요. 표본은 아직 세션 하나이고, 방법과 증명은 모두 공개했습니다.

다음 노트: 아무도 볼 수 없는 3분의 1.

— English —

[Research note 7/10] Don't forget it; set it aside and call it back

In 1966, Belady showed that if you knew the future, you could compute the best possible cache. Nobody knows the future, but the result gives a bound that no real system can beat.

We applied the same idea to AI agents. For one real session (322 calls, 149 million input tokens), we computed how much context an oracle would have kept: something that knows exactly which earlier content each step will use.

The two approaches gave very different answers. Drop content after its last use and never bring it back: 9.1% saved. Set it aside while it isn't needed and call it back when it is: 50.1% saved. Even if every call-back costs 1,000 tokens, it's 47.5%.

Most context does get used again, just not at every step in between. The waste wasn't old information. It was information carried around while it wasn't needed. The largest visible part was content the agent had already written to disk.

Calling it back means this: instead of carrying a whole file, remember only where it is ("this file, this version, lines 10 to 40") and open it again when it's needed.

The lesson is an old database principle: carry where it is, not what it is. The sample is still one session, and the method and proof are public.

Next: the third that nobody can see.

#AntiTokenMaxing

## 출처

- `research/results/belady-session-01.json`: 호출 322, 입력 149,273,256, 9.1% / 34.7% / 47.5% / 50.1%. 디스크에 쓴 내용이 보이는 것 중 최대(25.1%).
