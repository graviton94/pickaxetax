# ADR-0005: 코딩 에이전트 감사 도구와 가드 훅

- 날짜: 2026-10-05
- 상태: 승인
- English summary: `pxt agent audit` reads Claude Code transcripts and reports where tokens went (cache hits, peak context, re-reads of unchanged files, large tool results, repeated failures, and how long each result was carried in context). `pxt agent hook install` (or the Claude Code plugin in this repo) adds a PreToolUse guard that denies one re-read of an unchanged file and logs the avoided tokens to the ledger.

## 근거 (실물 검증)
- 실제 Claude Code 기록에서 **응답 하나가 블록마다 여러 줄로 기록되고, 줄마다 같은 usage가 반복**됨을 확인했다(140개 응답 중 126개). 그래서 message.id로 중복을 제거한다. 그대로 더하면 약 3배로 과대 집계된다.
- 이 작업 세션 자체를 감사해 보니 다음과 같았다: API 호출 143회, 입력 처리 4,348만 토큰(캐시 적중 97.8%), 컨텍스트 최대 50.8만 토큰, 이후 재전송된 도구 결과 3.3%. 긴 세션의 누적 컨텍스트가 가장 큰 비용이었고, 감사 도구도 "새 세션" 팁을 1순위로 낸다.
- 훅 입출력과 PreCompact 이벤트, 플러그인과 마켓 형식은 공식 문서(code.claude.com/docs/en/hooks, plugins)로 확인했다. 세션 기록 형식은 공식 문서에 없는 내부 사양이라 방어적으로 파싱한다.

## 결정
- **감사 (읽기 전용):** v0은 Claude Code만 지원한다. 다른 에이전트는 실물 샘플을 기여받아 어댑터를 추가한다(추측으로 만들지 않는다).
- **가드 (선택):** 같은 세션에서 같은 파일·같은 범위를 크기와 수정 시각이 그대로인 채 다시 읽으면 한 번 거부한다. 같은 요청이 다시 오면 허용하고, PreCompact가 오면 초기화한다. 어떤 오류든 허용 쪽으로 처리한다(fail open). 상태 파일에는 경로·크기·시각만 담고 내용은 담지 않으며, 세션 ID는 해시한다.
- **설치:** `pxt agent hook install`은 설정을 병합하고 백업을 남긴다. 다시 실행해도 결과가 같고, 제거도 지원한다. 저장소 자체를 Claude Code 플러그인 마켓으로 쓸 수 있다: `/plugin marketplace add graviton94/pickaxetax`, 이어서 `/plugin install pickaxetax@pickaxetax`. pxt가 설치되어 있지 않으면 훅은 아무것도 하지 않는다.
- **기여 내보내기:** `pxt agent audit --export`는 숫자만 담는다. MCP 도구 이름은 사적인 서비스명이 드러날 수 있어 "mcp"로 묶는다.

## 한계
- 가드는 실제 Claude Code 세션에서 돌려 보지 않았다. Claude Code가 훅에 보내는 입력을 흉내 낸 테스트와, 설정에 실제로 기록되는 명령을 셸로 실행하는 테스트까지 했다. 대표의 실사용 피드백으로 보완한다.
- 서브에이전트처럼 컨텍스트가 별도인 경우에는 불필요한 거부가 한 번 생길 수 있다. 같은 요청을 다시 하면 허용되므로 작업이 막히지는 않는다.
