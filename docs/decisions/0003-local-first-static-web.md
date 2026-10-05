# ADR-0003: 로컬 우선 정적 웹 (브라우저 엔진 + 북마클릿)

- 날짜: 2026-10-05
- 상태: 승인
- English summary: the web analyzer becomes a static site (`site/`) that runs a JavaScript port of the engine in the browser. Paste, file and share-link input are all processed locally; links go through a bookmarklet that reads the already-open share page. A strict CSP (`connect-src 'none'`) makes it impossible for the page to send anything. Hosting is GitHub Pages.

## 배경
헌장의 로컬 우선 원칙과 비용 최소화 원칙. 기존 웹 분석기는 원문을 서버로 보낸다(메모리에서만 처리하더라도).

## 검토한 선택지
- **엔진:** JS 포팅(수십 KB)과 Pyodide(약 10MB) 중 JS를 택했다. "가볍게"라는 요구 때문이다.
- **공유 링크:** 정적 페이지는 CORS 때문에 다른 사이트를 읽을 수 없다.
  - 공개 CORS 프록시는 제3자가 원문을 보게 되므로 제외했다.
  - 브라우저 확장은 무겁다. 다음 후보로 둔다.
  - **북마클릿**을 택했다. 사용자가 이미 열어 둔 공유 페이지에서 대화를 읽어 우리 탭으로 넘긴다. 클라이언트 렌더링 페이지도 읽을 수 있어서, 서버가 링크를 가져오는 방식보다 오히려 성공률이 높다.

## 결정
- `site/engine.js`는 Python 엔진을 줄 단위로 포팅한 것이다. `tests/test_parity.py`가 픽스처와 무작위 합성 대화 300개로 두 엔진의 출력이 같은지 CI에서 매번 대조한다.
  - 그 밖에 합성 대화 2,000개로 한 번 더 돌렸고, 불일치는 0건이었다.
  - Python의 지문 해시를 양쪽에서 같게 계산할 수 있는 FNV 기반으로 바꿨다. 배포별 키를 붙여 비교 범위를 한 배포 안으로 묶는 성질은 그대로다.
- 북마클릿은 대화를 URL의 `#fragment`로 넘긴다. fragment는 서버로 전송되지 않는다. 받는 쪽은 즉시 `history.replaceState`로 주소창에서 지운다. 1.5MB를 넘으면 붙여넣기로 안내한다.
- CSP `connect-src 'none'`: 페이지가 어떤 네트워크 요청도 보낼 수 없다. `tests/e2e/site_e2e.mjs`가 분석 중 요청 0건과 CSP 위반 이벤트를 실제 브라우저에서 확인한다.
- 배포는 GitHub Pages(`.github/workflows/pages.yml`)로 한다.

## 결과
- 범위 밖: 공익 그래프 기여 경로(정적 환경에서의 수집 방식). 다음 단계 인터뷰 안건이다. 기존 Python 서버는 셀프 호스팅용으로 유지한다.
- 북마클릿의 사이트별 선택자(ChatGPT `data-message-author-role`, Claude `data-testid="user-message"`·`.font-claude-*`, Gemini `user-query`/`model-response`)는 흉내 낸 테스트 페이지로만 검증했다. 실제 사이트에서는 대표가 직접 한 번 확인해야 하며, 사이트 구조가 바뀌면 고쳐야 한다. 선택자가 하나도 맞지 않으면 페이지 전체 텍스트에서 "You said:" 같은 표지로 대화를 나누는 방식으로 넘어간다.
