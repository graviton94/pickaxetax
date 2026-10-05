# ADR-0008: 연구 트랙 — 근본 단위와 첫 번째 이론적 경계

- 날짜: 2026-10-05
- 상태: 승인 (단위·입장·첫 증명·공개 형식). 프리프린트 개요는 초안이며 대표 승인을 기다린다.
- English summary: the unit of account becomes compute per valuable outcome, extended to memory residency (KV-cache byte-seconds). The Jevons stance is efficiency plus value measurement, to shift incentives. The first theoretical result is an offline-optimal (Belady-type) bound on context residency, shipped as `pxt agent bound`. Results are published as an English preprint with a Korean summary, after data from more than one session is collected.

## 배경
"누구나 떠올릴 수 있는 토큰 절약 도구"와 차별화하려면 다른 차원의 근거가 필요했다. 측정 단위가 무엇인지, 낭비의 하한을 증명할 수 있는지, 효율 개선이 사용량 증가로 상쇄되는 문제(제번스 역설)에 어떻게 답하는지가 그것이다. 이 세션 자체를 대상으로 한 실험(H0–H3, [research/hypotheses.md](../../research/hypotheses.md))에서 출발했다.

## 검토한 선택지
1. **근본 단위:** (1) 메모리 상주량 × 시간, (2) 가치 있는 결과 1건당 연산, (3) 토큰 유지 → **2를 기반으로 1까지 확장**
2. **제번스 역설:** 효율만 추구 / 총량 규제 주장 / **효율 + 가치 측정으로 인센티브 전환**
3. **첫 증명:** **벨레이디 최적 컨텍스트 하한** / 정보이론적 최소 컨텍스트 / 작업 단위 컨텍스트 상한
4. **공개 형식:** **영문 프리프린트 + 한글 요약** / 블로그 / 학회 투고

## 결정
- **단위:** U1(가치 있는 결과 1건당 토큰·FLOPs)을 기본으로 하고, U2(KV 캐시 바이트·초)로 확장한다. 공통 측정량은 토큰·호출(Σ 호출별 컨텍스트)이다. U2 수치는 β(토큰당 KV 바이트)와 τ(상주 시간)의 출처를 밝힐 때만 공개한다. ([research/framework.md](../../research/framework.md))
- **가치 측정:** V0(수용)–V3(채택) 사다리를 두고, 어느 단계로 쟀는지 항상 밝힌다. V1(디스크에 쓴 토큰)은 같은 종류의 작업 안에서 비교하는 분모로만 쓰고 목표로 삼지 않는다.
- **제번스 입장:** 절감량만이 아니라 가치 대비 수치(T/V, R/V)를 공개한다. 제공사에는 보이지 않는 컨텍스트, 캐시 보존 시간, β의 공개를 요구한다. CBI에는 절대량과 정규화 수치를 함께 싣는다.
- **첫 증명:** 미래를 아는 오라클의 최소 상주량. 세그먼트별·사용 간격별로 분해되므로 이 모델에서 정확한 최적이고, 대본에서 바로 계산된다. 실측 사용량으로 보정해 매 호출의 실측과 일치시킨다. `pxt agent bound`로 누구나 재현할 수 있다. ([research/belady-bound.md](../../research/belady-bound.md))
- **첫 결과 (n = 1):** 마지막 사용 뒤에 버리기 9.1%, 다시 부르기 오라클 50.1%, 보이지 않는 입력 32.4%. 핵심 주장은 "잊기가 아니라 페이징"이다.
- **공개:** 영문 프리프린트 + 한글 요약. 세션 1개짜리 결과로는 투고하지 않는다. 여러 세션·여러 에이전트의 기여 데이터를 먼저 모은다(H4).

## 결과와 후속
- 연구 문서는 `research/`에 두고, 실패한 가설도 기록한다.
- 다음 단계: (1) 익명 `agent` 기여 형식에 경계 수치를 추가한다(두 검증기 동시 수정). (2) 포인터 + 최근성 정책을 구현해 경계와 비교한다(H5). (3) 보이지 않는 입력의 정체를 조사한다(H6).
- 헌장의 북극성 지표("검증된 회피 연산량")는 운영 지표로 유지하고, 그 단위를 이 ADR의 U1/U2로 정의한다.
