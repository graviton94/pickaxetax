# ADR-0006: 2단 기여 경로 (익명 원클릭 + GitHub 검증)

- 날짜: 2026-10-05
- 상태: 승인
- English summary: two contribution paths. (1) One-click anonymous contributions from the web app and CLI to a Cloudflare Worker + D1 (free tier): no account, no cookies, no stored IP; abuse is made expensive with a proof-of-work challenge and a daily limit keyed by a daily-rotating salted hash. (2) Verified contributions through a prefilled GitHub issue, validated and stored by Actions on the `contributions` branch. Both accept only allowlisted structural data; the public aggregate is baked into the static site daily with k-anonymous topics.

## 배경
처음에는 서버 없이 GitHub 이슈만 쓰는 안을 냈다. 대표가 "그럼 일반 유저로 확장하기 너무 어렵지 않나?"라고 지적했다. GitHub 계정이 있어야만 기여할 수 있으면 "글로벌 모든 AI 사용자" 목표와 맞지 않는다.

## 결정
- **익명 원클릭:** Cloudflare Workers와 D1 무료 티어(하루 10만 요청)를 쓴다.
  - 원문은 여전히 브라우저를 떠나지 않는다. 사용자가 미리 보기를 확인하고 클릭했을 때만, 허용 목록을 통과한 숫자·구조 데이터가 전송된다. 사이트 CSP는 이 Worker 주소 하나로만 열린다.
  - 도배 방지: 작업증명(SHA-256 선행 0비트, 기본 15비트, 브라우저에서 수 초)과 하루 횟수 제한. 횟수 제한 키는 그날만 유효한 솔트로 IP를 HMAC한 값이며, 원본 IP는 저장하지 않는다.
  - 기여마다 삭제 토큰이 발급된다. 브라우저에 보관되고, 서버에는 토큰의 해시만 남는다.
- **GitHub 검증:** 미리 채워진 이슈 양식으로 제출한다. Actions가 검증해 `contributions` 브랜치에 저장하고 이슈를 닫는다. 작성자 본인이 `/withdraw`를 남기면 삭제된다.
- **단일 검증 규칙:** `site/contrib.js`(브라우저와 Worker가 공유)와 `pickaxetax/contrib.py`(CLI와 CI). 두 구현은 45개 승인·거부 사례에서 판정이 일치해야 한다(`tests/test_contrib.py`).
  - 모르는 키와 자유 텍스트는 거부한다.
  - 정합성 검사로 꾸며낸 숫자를 걸러낸다(턴 수, 토큰 합계, 최적값이 실제보다 큰 경우 등).
  - 주제 라벨은 사용자가 고른 경우에만, 최대 7개의 짧은 단어로 받는다.
- **공개 집계:** Pages 빌드가 매일 Worker의 `/export`와 `/labels`(k=3 미만은 서버에서 차단), GitHub 기여를 합쳐 `site/data/aggregate.js`에 굽는다. 그래서 런타임 요청 없이 사이트가 표시된다. 전형값은 이상치에 강한 중앙값으로 낸다.

## 검증
- 실제 Workers 런타임(wrangler dev --local, workerd + 로컬 D1)에서 14개 시나리오를 확인했다: 정상 기여, 잘못된 작업증명, 재사용, 위조된 만료, 자유 텍스트 밀반입, 꾸며낸 숫자, k-익명 라벨·쌍, export에 라벨·토큰 없음, 삭제. CI에서도 매번 같은 테스트를 돌린다.
- 브라우저에서 분석, 기여, 삭제까지 했고, 외부 요청은 Worker로 가는 3건뿐이었다.
- 실제 에이전트 세션(익명)의 감사 결과를 CLI로 기여해 보았다(로컬 Worker).

## 대표 할 일
Cloudflare 무료 가입, API 토큰 발급, 저장소 시크릿 2개(`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) 입력. 이후 배포, DB 생성, 서브도메인 등록, 사이트 연결은 워크플로가 처리한다. 시크릿이 없으면 익명 기여 버튼은 "곧 열림"으로 표시되고, GitHub 기여는 그대로 동작한다.

## 한계
- 익명 데이터는 조작될 수 있다. 정합성 검사, 작업증명, 횟수 제한, 중앙값으로 비용을 높일 뿐이다. 공개 지수에는 익명·검증 건수를 따로 표시한다.
- GitHub 기여는 기여자 계정과 함께 공개된다.
