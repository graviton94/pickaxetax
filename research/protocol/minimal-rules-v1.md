# Minimal rule set v1: the fewest rules that capture the most (pre-registration)

Status: **pre-registered 2026-10-07, before any replay of these rules.** The design, the candidates,
the cost model and the selection procedure below are fixed. A change after results are seen is v2,
reported as such.

## Question

The codebook names eight kinds of waste. Phase 2 measured where the input goes and which levers move
it (`research/phase2/synthesis.md`). This step asks the prescriptive question: **which smallest set of
simple rules, none of which needs foresight, captures most of the opportunity**, and at what cost in
extra steps? The oracle reference is 41.5% (lexical-v1, P = 1,000; 40–50% under behaviour-supported
definitions).

## Inspiration (analogies, not claims)

The candidate rules are inspired by how biological nervous systems keep complex behaviour cheap with
a few simple mechanisms. The analogies name the *shape* of each rule. They are not claims about how
brains or models work, and the replay alone decides which rules stay.

| Rule | Inspired by | Rule shape |
|---|---|---|
| R1 | unconditioned reflex | a fixed response with no deliberation |
| R2 | habituation | stop responding to an unchanged stimulus |
| R3 | threshold gate (a neuron fires above a level) | act when a quantity crosses a threshold |
| R4 | consolidation at event boundaries | compress an episode at its boundary, drop the raw trace |
| R5 | rest and consolidation (parasympathetic mode, sleep) | consolidate when activity pauses |
| R6 | Hebbian strengthening with decay (ACT-R base-level activation) | keep what is used often and recently |
| R7 | hippocampal index | keep pointers to content and fetch it on cue |

## Candidate rules (fixed)

All rules act on the segment replay of cycles B3 and A4. Context is the base plus the live segments
plus the unattributed growth. An observed compaction applies only if the replay reached 90% of its
size; otherwise the replay compacts by itself at 790k to the observed post-compaction size. With no
rule, it must reproduce measured input exactly (6,579,410,935).

- **R1 reflex: no duplicate reading.** A reading call whose result is at least 95% already resident in
  the current context does not happen. That is cycle B7's W1b rule: lines of 12+ characters, 3-line
  runs, results of 200+ tokens. The call and its result segment are removed from the replay.
- **R2 habituation: no identical repeats.** A call that repeats an earlier call's signature with an
  identical result in the same context, or repeats an identical failing call, does not happen
  (codebook W1, and W2's identical retries). The call and its result are removed.
- **R3 threshold gate: compact at C.** The context is compacted when it would pass C = 150k (primary;
  100k and 200k are sensitivity runs) to the observed post-compaction size of 64k (42k prefix + 22k).
  Each compaction is charged D2's re-read cost (82.7k input; price 0.25 per token, as in B4).
- **R4 consolidation at task boundaries.** At an instruction boundary where the replayed context is
  above 200k, start fresh: base + 10k summary. Charge B5's median cold start (22.5k tokens written
  fresh, 0.5 extra calls), plus the re-reads observed after real compactions, as in A5 and A6.
- **R5 consolidation at rest.** At an instruction boundary that follows an idle gap of more than one
  hour, start fresh with the same charges as R4, whatever the context size.
- **R6 usage-weighted keep (needs R3, R4 or R5 to act).** When the context is consolidated or
  compacted, segments with a high base-level activation are kept instead of dropped:
  A = ln Σ_j (t − t_j)^−0.5 over the segment's earlier use times, in calls. Uses are its birth and
  its lexical refs. The highest-activation segments are kept up to a budget of 20k tokens.
- **R7 index: fetch on need (needs R3, R4 or R5 to act).** A dropped segment that is needed later is
  fetched again. Need is a lexical-v1 ref at min_shared 1, the upper bound on need. Each fetch costs
  one extra call at the current context, plus the segment's tokens written fresh. Without R7, needed
  content dropped by a consolidation is charged as in A4/A5: re-obtained at the observed rate.
  Sensitivity: need thinned to the behaviour-calibrated rate of cycle A7.

## Costs and measures

- **Input saved:** % of measured main-session input.
- **Price saved:** B3/B4 price model (0.1 per token kept, 2.0 per new token, 0.25 per re-read
  token), and in total money per cycle C5.
- **Extra steps:** fetches, cold starts and compactions, per instruction and in total.
- **Removed calls:** for R1 and R2, a removed call takes its input with it. This assumes the work
  succeeded without it, which is reported as an assumption.

Quality cannot be measured from the logs. Every saving assumes the rule loses nothing needed, beyond
what its charges cover. Phase 3 tests that.

## Selection (fixed)

1. **Forward selection.** Start with no rule. At each step, add the eligible rule with the largest
   marginal price saving. R6 and R7 are eligible only once R3, R4 or R5 is in the set.
2. **Keep rule.** A rule is kept only if it adds **at least 2 points of input and at least 1 point of
   price**. Selection stops when no rule passes.
3. **Validation by sessions.** Selection runs on sessions S01, S03, S05, S07 and S09, and the chosen
   set is evaluated on S02, S04, S06, S08 and S10, then the halves are swapped. The result stands if
   both halves choose the same rules, or the held-out half loses less than 5 points against the set
   chosen on all ten sessions.
4. **Report.**
   - The chosen set (n rules), with its pooled input and price savings and its share of the oracle
     (41.5%).
   - Extra steps per instruction, and every rule's marginal contribution, chosen or not.
   - The R3 threshold sensitivity, the R7 need sensitivity, and a session bootstrap of the final set
     (cycle E4's method).

## Expectation (stated so it can fail)

Phase 2 suggests a small set built around boundaries: R4 or R3, perhaps R5, with R1 and R2 adding a
point or two. R6 and R7 add little under these charges. The pre-registered falsifiers:
- the chosen set captures less than half of the oracle in input; or
- its extra steps exceed 10% of all steps; or
- the two session halves choose different sets.

---

## 한국어 요약

8대 낭비에 더해 미래를 몰라도 되는 **최소 규칙 n개**가 기회(오라클 41.5%)의 얼마를 거두는지 찾습니다. 후보 규칙 일곱 개는 뇌신경과학에서 영감을 받은 모양입니다(무조건반사, 습관화, 역치 관문, 경계에서의 기억 응고, 휴식 중 응고, 헵 강화와 망각, 해마 색인). 비유일 뿐 주장은 아니고, 어떤 규칙이 남을지는 기존 데이터로 재연해 정합니다.

규칙을 하나씩 더하되 입력 2%p, 비용 1%p 이상 보태는 규칙만 남깁니다. 세션을 반으로 나눠 고르고 나머지 절반으로 검증합니다. 시동 비용, 다시 읽기, 불러오기 걸음은 모두 비용으로 물립니다. 결과가 기대와 다를 수 있는 조건(오라클의 절반 미만, 추가 걸음 10% 초과, 두 절반의 선택이 다름)도 미리 적었습니다.
