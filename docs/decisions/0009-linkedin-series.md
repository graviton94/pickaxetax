# ADR-0009: LinkedIn 연재로 순차 공개

- 날짜: 2026-10-05
- 상태: 승인 (연재 방식). 일정·언어·형식의 기본값은 대표가 바꿀 수 있다.
- English summary: instead of a single launch post, the plan is published on LinkedIn as a series of ten chapters over five weeks (Tue/Thu), plus a results chapter once contributed data allows. The tool goes public in chapter 4, which becomes launch day for the X thread and Reddit. Drafts in `docs/launch/linkedin-series/`. This amends the "Order" section of ADR-0007.

## 배경
한 번에 모든 것을 공개하면 관심이 하루 만에 소진된다. 계획 자체를 장(chapter)으로 나누어 순차적으로 올리면 관심이 쌓이고, 각 장의 댓글을 다음 장에 반영할 수 있다(대표 요청).

## 결정
- **구성:** 문제 → 증거 → 도구 → 과학 → 요청 순서로 10장, 그리고 기여 데이터가 모이면 결과 장(11장). 도구는 독자가 문제에 관심을 가진 뒤인 4장에 공개하고, 데이터 요청은 결과가 신뢰를 얻은 뒤인 10장에 한다.
- **일정(기본값):** 2026-10-08(목) 시작, 화·목 08:00–09:00 KST, 5주.
- **언어:** ~~본문은 영어, 한국어판은 첫 댓글~~ → ADR-0010에서 변경. 한국어 원문 + 영어 번역을 한 게시물에 싣는다. 합니다체, 한국어 700–900자, 각 노트는 그날의 연구 성과처럼 쓰고 대표의 계기는 1번 노트에만 넣는다.
- **ADR-0007 수정:** X 스레드와 Reddit은 첫날이 아니라 4장(도구 공개일, 2026-10-20)에 맞춘다. 공개 전 점검 목록은 4장 전까지 끝낸다.
- **공개하지 않는 것:** 프로젝트를 만든 방식, 그리고 조직·자금·인수 같은 사업 이야기
- **수치:** 모든 숫자는 `docs/launch/README.md`의 Facts 표에 출처가 있어야 한다. 3장의 KV 캐시 용량은 공개 70B급 구조로 계산한 예시임을 본문에 밝힌다.
- **선행 조건:** 10장 전에 경계 수치를 익명 `agent` 기여 형식에 넣는다(ADR-0008 후속 1). 늦어지면 10장의 요청을 "GitHub 이슈에 요약 붙여넣기"로 바꾼다.

## 결과
- 초안: `docs/launch/linkedin-series/` (장별 영어 본문 + 한국어 첫 댓글 + 목적·이미지·선행 조건)
- 이미지: `docs/img/series/ch07-paging.png`, `ch08-invisible.png` (1200×1200)
- 장마다 반응 지표를 기록하고, 저조하면 다음 장의 첫 문장(후크)을 고친다.
