# ADR-0007: 첫 공개 준비

- 날짜: 2026-10-05
- 상태: 승인
- English summary: launch on X, LinkedIn and Reddit (drafts in `docs/launch/`), move the default branch to `main`, and use anonymized real measurements only. README rewritten for first-time visitors (badges, screenshot, quick start, privacy guarantees). Repo hygiene added: SECURITY, CODE_OF_CONDUCT, CHANGELOG, issue and PR templates, OG card. Released as 0.3.1.

## 결정
- **채널:** X와 LinkedIn(같은 날), 이어서 Reddit(r/ClaudeAI → r/LocalLLaMA → r/ChatGPT, 하루에 하나씩). 초안은 영어와 한국어로 `docs/launch/`에 둔다. 게시는 대표 계정으로 한다.
- **실측 사례:** 실제 코딩 에이전트 세션 하나의 감사 수치만, 익명으로 쓴다(호출 143회, 입력 처리 43,477,948 토큰, 캐시 97.8%, 최대 컨텍스트 507,710). 어떤 작업의 세션인지는 밝히지 않는다. 모든 수치의 출처는 `docs/launch/README.md`의 "Facts" 표에 둔다.
- **기본 브랜치:** 작업 브랜치를 `main`으로 푸시한다(대표가 이번에 한해 허락). 기본 브랜치 전환은 대표가 Settings에서 한다.
- **링크 미리보기:** `site/og.png`(1200×630)와 OG·Twitter 메타 태그를 넣는다.
- **저장소 기본 문서:** SECURITY(GitHub 비공개 취약점 신고 경로), CODE_OF_CONDUCT(Contributor Covenant 2.1 참조), CHANGELOG, 버그·아이디어 이슈 양식, PR 체크리스트를 둔다.

## 대표가 붙여 넣을 저장소 정보 (Settings → General / About의 톱니바퀴)
- Description: `Stop paying the pickaxe tax. Measure and cut wasted AI compute: local-first web app, coding-agent audit, LLM proxy, Compute Bubble Index. #AntiTokenMaxing`
- Website: `https://graviton94.github.io/pickaxetax/`
- Topics: `llm`, `ai-efficiency`, `tokens`, `claude-code`, `openai`, `anthropic`, `proxy`, `privacy`, `sustainability`, `green-ai`, `open-data`
