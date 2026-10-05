# ADR-0002: 마스터 브랜드 "Pickaxe Tax"

- 날짜: 2026-10-05
- 상태: 승인
- English summary: the master brand is **Pickaxe Tax**, with descriptive product names (Pickaxe Tax Proxy, Pickaxe Tax Bench) and the Compute Bubble Index. #AntiTokenMaxing stays as the campaign hashtag. Package and CLI are `pickaxetax`, with the alias `pxt`.

## 배경
인터뷰에서 정한 조건:
- **구조:** 마스터 브랜드에 설명형 제품명을 붙인다. 관리할 이름이 하나라 비용 원칙에 맞는다.
- **성격:** 골드러시 서사형
- **기준:** 이름 확보 가능성, 메시지 직관성, 어그로
- **운동명:** ANTITOKENMAXING은 해시태그와 캠페인 이름으로 쓴다.

## 검토한 후보 (2026-10-05 확인)

| 후보 | PyPI | npm | GitHub 계정 | 비고 |
|---|---|---|---|---|
| **Pickaxe Tax** | 비어 있음 | 비어 있음 | 비어 있음 | 어그로와 직관성 모두 높음 |
| Token Assay | 비어 있음 | 비어 있음 | 비어 있음 | 신뢰형, 어그로 중간 |
| Gold Rush Bill | 비어 있음 | 비어 있음 | 비어 있음 | 이름이 김 |
| Overburden | 비어 있음 | 비어 있음 | 선점됨 | 이중 의미 |
| Ghost Town | 비어 있음 | 비어 있음 | 선점됨 | 부정적 어감 |
| Pyrite, Assay, Fool's Gold | 대부분 선점 | 선점 | 선점 | 탈락 |

GitHub는 개인 계정만 검색했다. 조직 이름과 도메인은 확인하지 못했다(네트워크 정책).

## 결정
- 마스터 브랜드: **Pickaxe Tax** (곡괭이세). 슬로건은 "Stop paying the pickaxe tax." / "곡괭이세를 그만 내자."
- 제품명: Pickaxe Tax Proxy, Pickaxe Tax Bench, Compute Bubble Index
- 패키지·import·CLI: `pickaxetax`, 별칭 `pxt`. 환경 변수 `PICKAXETAX_*`, 로컬 데이터 `~/.pickaxetax/`
- 저장소: `graviton94/pickaxetax` (대표가 직접 변경)

## 근거
- 이름 자체가 고발이다. 골드러시에서 돈을 버는 쪽은 곡괭이 판매자다.
- 곡괭이세를 실제로 내는 쪽은 AI 개발사와 사용자다. 그래서 이 이름은 반AI가 아니라 "함께 그만 뜯기자"는 메시지가 되고, 투트랙 전략과 인수 시나리오와도 충돌하지 않는다.

## 결과와 후속 조치 (대표 직접)
- [x] PyPI `pickaxetax` 확보 (0.1.0 배포, 2026-10-05, ADR-0004)
- [ ] npm `pickaxetax` 이름 선점 (npm 패키지가 생길 때)
- [ ] GitHub 조직 `pickaxetax` 생성
- [ ] 도메인 확인과 등록 (pickaxetax.org / .dev)
- [ ] 런칭 전 상표 검색 (법률 검토)
- 위험: 기업 영업에서 공격적으로 들릴 수 있다. 필요하면 엔터프라이즈 문서에서는 "Pickaxe Tax"를 "효율 감사" 맥락으로 설명한다.
