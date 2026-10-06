# Carbon factors: tokens → energy → CO₂ → trees

Status: **estimate and metaphor, not measurement.** No AI provider publishes the
energy used per token, so this page chains public figures. Each factor carries its
source so anyone can swap it and recompute. Code: `pickaxetax/survey/carbon.py`,
mirrored in `site/carbon.js` (`tests/test_carbon.py` checks they match).

## The chain

| Step | Factor | Source |
|---|---|---|
| Energy per input token, **upper** | 5.671 Wh ÷ 10,000 = **0.567 mWh** | Jegham et al. 2025, *How Hungry is AI?* ([arXiv 2505.09598](https://arxiv.org/abs/2505.09598)). Claude 3.7 Sonnet, long prompt (10,000 input + 1,500 output tokens): 5.671 ± 0.302 Wh per query. Charging the whole query to its input over-counts. |
| Energy per **re-read** token, **central** | upper × 0.1 = **0.0567 mWh** | Re-read context is served from the prompt cache, which Anthropic prices at 0.1× base input ([prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)). Using price as a proxy for compute is an **assumption**. |
| Grid carbon intensity | **445 g CO₂/kWh** | IEA, [Electricity 2025](https://www.iea.org/reports/electricity-2025/emissions): world average, 2024. |
| One tree | **60 kg CO₂ in 10 years** (6 kg a year, 16.4 g a day, 0.68 g an hour) | US EPA, [GHG Equivalencies](https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references): a medium-growth urban seedling grown for 10 years sequesters 0.060 t CO₂. |
| One smartphone charge | **19 Wh** | US EPA, same page. |
| One dry twig | **1.72 g CO₂ per g of dry wood** (0.47 g carbon × 44/12) | IPCC 2006 Guidelines, [Vol. 4](https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html), default carbon fraction of dry wood. |

Sanity anchor: Google reports 0.24 Wh and 0.03 g CO₂e for the *median* Gemini Apps
text prompt (Elsworth et al. 2025, [arXiv 2508.15734](https://arxiv.org/abs/2508.15734)).
That is a short chat prompt. The call below re-reads 427,524 tokens.

## What it gives (central; upper = ×10)

| | Tokens | Energy | CO₂ | As trees and twigs |
|---|---|---|---|---|
| One line ("Hello") in a long working session: the median re-read per call | 427,524 | 24 Wh (1.3 phone charges) | **10.8 g** | one tree's **16 hours**; burning a **6 g dry twig** |
| user01, three months of Claude Code (dataset v2) | 6,839,974,268 | 388 kWh | **173 kg** | one tree's **29 years** (2.9 trees grown for 10 years) |
| …of which context carried over from finished instructions (76.1%) | | | ≈131 kg | one tree's ≈22 years |
| Upper bound (no cache discount) for user01 | | 3,880 kWh | 1.73 t | ≈29 trees grown for 10 years |

Research note 1 used dataset v1 (5,871,292,005 tokens, a lower bound because S09 was partial): 333 kWh, 148 kg, one tree's 25 years.

## Limits, stated plainly

- The energy factor comes from a 2025 benchmark of an older model, served through a
  public API and inferred from latency and hardware assumptions. Providers' real
  numbers may be lower (newer hardware, batching) or higher (larger models, longer
  contexts: attention cost grows with context length).
- The cache ratio is a price, not a physical measurement.
- Grid intensity is the world average. A data center on a cleaner grid emits less; a
  market-based figure with renewable contracts would be lower still.
- "Burning a twig" and "a tree's hours" are metaphors that make a gram of CO₂
  imaginable. They are not offsets and not a claim that any tree was cut down.

---

# 탄소 계수: 토큰 → 전력 → CO₂ → 나무

상태: **측정이 아니라 추정이고 비유입니다.** 토큰당 전력을 공개하는 AI 제공사가 없어서
공개된 수치를 이어 붙였습니다. 계수마다 출처를 달아, 누구든 바꿔 넣고 다시 계산할 수 있습니다.

- 입력 토큰당 전력 (상한): 0.567 mWh. Jegham 외 2025, Claude 3.7 Sonnet 긴 프롬프트(입력 1만, 출력 1,500토큰) 한 번에 5.671 Wh. 쿼리 전체 전력을 입력에만 매겨서 실제보다 큽니다.
- 다시 읽는 토큰당 전력 (중심값): 상한 × 0.1 = 0.0567 mWh. 다시 읽는 컨텍스트는 프롬프트 캐시에서 나오고, Anthropic은 캐시 읽기를 기본 입력의 0.1배로 받습니다. 요금을 연산량의 대리 지표로 쓴 것은 **가정**입니다.
- 전력 탄소집약도: 445 g CO₂/kWh (IEA, 2024 세계 평균).
- 나무 한 그루: 10년 동안 60 kg CO₂ 흡수 (미국 EPA, 도시 묘목 1그루). 하루 16.4 g, 한 시간 0.68 g.
- 스마트폰 1회 충전: 19 Wh (미국 EPA).
- 마른 나뭇가지: 마른 나무 1 g에 탄소 0.47 g (IPCC 2006), CO₂로 1.72 g.

결과 (중심값, 상한은 ×10):

- "안녕하세요" 한 줄 (긴 작업 세션에서 호출 한 번이 다시 읽는 양의 중앙값 427,524토큰): 24 Wh, CO₂ **10.8 g**. 나무 한 그루의 **16시간**, 마른 나뭇가지 **6 g**을 태운 만큼.
- user01의 석 달 (판 2, 68억 4천만 토큰): 388 kWh, CO₂ **173 kg**. 나무 한 그루의 **29년**. 그중 이미 끝난 지시의 컨텍스트(76.1%)가 약 131 kg, 나무 한 그루의 약 22년. (노트 1편은 판 1의 58억 7천만 토큰, 148 kg, 25년을 썼습니다. S09 부분 측정이라 하한이었습니다.)

"나뭇가지를 태운 만큼", "나무의 몇 시간"은 1 g의 CO₂를 떠올리게 하려는 비유입니다. 상쇄량도 아니고, 실제로 나무가 베였다는 뜻도 아닙니다.

---

# The world's receipt (site section "The cost")

Global figures for AI and data centres as a whole, each from its source. Only the last
line is our own measurement; it is not the waste rate of the world's compute.

| Line | Figure | Source |
|---|---|---|
| Data-centre capex, Alphabet + Amazon + Microsoft + Meta, 2026 | more than $700B (Alphabet alone guides $195–205B); includes non-AI capex | [CNBC, 2026-07-22](https://www.cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html); [Sherwood News](https://sherwood.news/tech/alphabet-amazon-microsoft-meta-plan-more-than-700-billion-on-capex-this-year/) |
| Data-centre electricity | 415 TWh (2024) → about 945 TWh (2030), "slightly more than Japan's total electricity consumption today" | [IEA, Energy and AI (2025)](https://www.iea.org/reports/energy-and-ai/executive-summary) |
| Its CO₂ | about 180 Mt today → a peak of about 320 Mt in 2030 (Base Case) ≈ what 53 billion urban trees absorb in a year at EPA's 6 kg each (metaphor) | IEA, same report; EPA (above) |
| Generative-AI e-waste | 1.2–5.0 Mt accumulated over 2020–2030 | [Wang et al. 2024, Nature Computational Science](https://www.nature.com/articles/s43588-024-00712-6) |
| Leftovers of finished instructions (ours; not yet judged as waste, see `research/protocol/waste-codebook-v1.md`) | 76.1% of context re-read on each call was carried over from finished instructions (dataset v2; 73.6% in v1); output 0.19–0.43% of input | `research/survey/user01/` |
