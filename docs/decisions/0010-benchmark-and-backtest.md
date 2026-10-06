# ADR-0010: 누구나 인정할 수 있는 벤치마크·백테스트, 그리고 하한 수치 기여

- 날짜: 2026-10-05
- 상태: 승인
- English summary: the bound joins the anonymous `agent` contribution (counts and percentages only, one row per session, method-versioned, mirrored in both validators). Cross-provider benchmarking runs as a pre-registered, trace-driven backtest (`pxt backtest`), frozen as protocol backtest-v1 before any benchmark data is seen. Online policies are tuned on a hash-assigned dev split and reported on the held-out test split. The lexical use detector must be validated by hand before publication. LinkedIn essays become Korean-first, with English as the translation.

## 배경
대표가 Gemini, Grok, GPT, Claude 등 여러 제품의 대화 기록을 제공하기로 했다. 이 측정은 비판적인 사람도 인정할 수 있는 방식이어야 한다(대표 요청). 그리고 10장의 데이터 요청이 실제로 동작하려면 하한 수치를 익명으로 기여할 수 있어야 한다.

## 결정
- **하한 수치 기여:** `agent` 기여에 선택 항목 `bound`를 추가한다. 내용은 방법 버전(`lexical-v1`), 세션·호출·입력·고정분, 정책별 회피율, 세션별 행(최대 200개)이며 숫자만 담는다. 정책 순서, 고정분 상한, 세션 합계의 일관성을 검사한다. JS·Python 검증기가 55개 사례에서 같은 판정을 내린다. 공개 집계는 세션을 단위로 한 중앙값과 사분위수다.
- **사전 등록:** 질문, 포함·제외 규칙, 지표, 정책, 튜닝, 통계, 하지 않을 주장을 데이터를 보기 전에 `research/protocol/backtest-v1.md`에 고정한다. 코드 상수와 문서가 다르면 테스트가 실패한다. 바꾸려면 v2를 만든다.
- **백테스트:** 실제 세션의 참조열에 온라인 정책(window, recency, pointer)을 재생해 실현 절감률과 미스율을 측정하고, 오라클 하한과의 격차를 잰다. N은 해시로 정한 개발 분할(약 20%)에서만 고르고, 결과는 시험 분할에서만 보고한다.
- **통계:** 세션이 분석 단위다. 중앙값과 부트스트랩 95% 신뢰구간(10,000회, 고정 시드)을 쓴다. 출처 간 비교는 같은 길이 구간 안에서만 하고, 세션 10개 미만인 칸은 결과로 보고하지 않는다. 민감도 격자 18칸에서 방향이 모두 같아야 "강건하다"고 말한다.
- **탐지기 검증:** 공개 전에 사람이 100쌍 이상을 블라인드로 판정해 정밀도와 재현율을 함께 보고한다.
- **기여자 수:** 보고서에 기여자 수를 밝힌다. 한 사람의 데이터는 "기여자 1명"으로 표시한다.
- **어댑터:** Gemini API 형식은 지원한다. Gemini 앱, Grok, 다른 코딩 에이전트는 첫 실제 샘플로 만든다. 형식을 추측해서 만들지 않는다.
- **에세이:** LinkedIn 연재는 한국어가 원문이고 영어는 번역이다. 두 언어를 한 게시물에 싣는다. 합니다체로 쓰고, 한국어는 700–900자로 한다. 각 노트는 그날의 연구 성과처럼 쓰며, 대표의 계기는 1번 노트에만 넣는다. 초안은 대표와 함께 다듬는다(ADR-0009의 언어 기본값을 바꾼다).

## 첫 관찰
이 세션 하나에서는 미스율 5% 이하를 지키는 온라인 정책이 없었다. 오라클 하한(49%)은 크지만, 미래를 모르는 단순한 정책으로 그것을 실현하기는 어렵다. 이것이 다음 연구 과제(H5)다.
