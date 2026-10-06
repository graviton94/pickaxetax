# ADR-0009: LinkedIn 연재로 순차 공개

- 날짜: 2026-10-05
- 상태: 승인, 2026-10-05 수정 (10편 고정 계획 → 한 편씩 쓰기)
- English summary: instead of a single launch post, the plan is published on LinkedIn as a series of ten chapters over five weeks (Tue/Thu), plus a results chapter once contributed data allows. The tool goes public in chapter 4, which becomes launch day for the X thread and Reddit. Drafts in `docs/launch/linkedin-series/`. This amends the "Order" section of ADR-0007.

## 배경
한 번에 모든 것을 공개하면 관심이 하루 만에 소진된다. 계획 자체를 장(chapter)으로 나누어 순차적으로 올리면 관심이 쌓이고, 각 장의 댓글을 다음 장에 반영할 수 있다(대표 요청).

## 결정 (수정)
- **처음 안(폐기):** 10편의 순서·일정·내용을 미리 정하고 초안을 한꺼번에 쓴다. → 대표가 거부했다. 노트는 그날의 연구 성과를 담아야 하므로 미리 정할 수 없다.
- **현재:** 연구 노트를 **한 편씩**, 연구가 한 걸음 나아갈 때마다 쓴다. 전체 편수와 순서는 정하지 않는다. 다음 편의 주제는 이전 편의 반응과 그사이의 연구 결과로 정한다.
- **형식:** 한국어 원문 + 영어 번역을 한 게시물에 싣는다(ADR-0010). 합니다체, 한국어 700–900자. 대표의 계기는 1번 노트에만 넣는다.
- **공개하지 않는 것:** 프로젝트를 만든 방식, 그리고 조직·자금·인수 같은 사업 이야기
- **수치:** 모든 숫자는 `docs/launch/README.md`의 Facts 표에 출처가 있어야 한다.
- **X·Reddit:** 도구 공개 시점은 노트를 쓰면서 정한다.

## 결과
- 초안: `docs/launch/linkedin-series/01-the-pickaxe-tax.md` 한 편. 미리 써 두었던 2–11편은 지웠다(git 기록에는 남아 있다).
- 연구 그림은 `research/figures/`에 둔다.
