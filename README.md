# Pickaxe Tax

> **Stop paying the pickaxe tax.** `#AntiTokenMaxing`
> In a gold rush, the people selling pickaxes get rich. Your AI re-reads the whole conversation every single turn, and you pay for every re-read.
> Build less. Waste less. Use the compute we already have.

[한국어](#한국어) · [Charter (KO)](docs/CHARTER.md) · [Decisions](docs/decisions/README.md) · [Architecture](docs/ARCHITECTURE.md) · [Privacy](docs/PRIVACY.md)

**Chat models re-read the entire conversation on every turn.** Late constraints, re-asks, "thanks!" messages and topic switches inside one chat make that cost grow quadratically. Pickaxe Tax takes a shared conversation (share link, export JSON or pasted transcript) and **throws the text away**. What it keeps is a graph skeleton: agenda (topic labels), structure (per-turn intents and typed edges such as DEEPENS, PIVOTS, CORRECTS and RETRIES), depth (topic threads and drill-down level) and token flow. It then shows:

- actual vs. optimal compute (one focused chat per topic, with the waste removed) and a one-shot lower bound
- where the compute leaked: thank-you messages, discarded answers, re-sent off-topic history
- a one-shot prompt skeleton built only from topic labels
- habits to change, ranked by measured waste

Contributed skeletons feed a public, **k-anonymous** topic graph (a topic is shown only once it appears in ≥ k conversations) plus aggregate waste statistics. The analyzer itself calls **no LLM**: a project about saving tokens shouldn't spend them.

```bash
pip install -e ".[dev]"
pickaxetax serve                      # conversation skeleton analyzer (web); `pxt` is a short alias
pickaxetax proxy                      # local proxy: OpenAI-compatible /v1, Anthropic base URL
pickaxetax ledger                     # tokens spent, context re-sent, tokens avoided
pickaxetax bench run --base-url http://localhost:11434 --model llama3.2   # donate benchmark compute
pytest
```

**Local proxy.** Point your client at it and it forwards to the real provider with your own key, which it never stores. It measures every request (input, output, reasoning, re-sent context). By default it also drops earlier pure thank-you exchanges from the history and answers a bare "thanks" locally instead of re-reading the whole chat. "ok"/"yes" are never short-circuited, because in agent workflows they mean "go ahead". Requests with tools are never rewritten. Opt-in: `--cache` reuses responses to identical temperature-0 requests, stored on your disk.

**Web app (local-first).** `site/` is a static page that runs the same engine in your browser. You can paste text, drop an export file, or use a share link through a bookmarklet that reads the page you already have open. Its Content-Security-Policy (`connect-src 'none'`) makes it impossible for the page to send your conversation anywhere. It is deployed to GitHub Pages; to run it locally: `cd site && python3 -m http.server`.

**How to help at zero cost:** see [CONTRIBUTING.md](CONTRIBUTING.md).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/PRIVACY.md](docs/PRIVACY.md).

### Where this is going

The AI boom is turning into a gold rush where only the pick-and-shovel sellers win: more GPUs, more data centers, more power. The waste is not only in conversations. It runs through the whole compute stack: infrastructure built ahead of revenue, oversized models and needless reasoning tokens, and wasteful usage. Pickaxe Tax is the open toolkit of **#AntiTokenMaxing**, a global effort to **prove that with public data and remove it with open tools**:

- **Shared brain**: solution-path graph + open efficiency dataset, built from conversation *skeletons* contributed by users worldwide
- **Prompt compiler**: a local proxy/SDK and coding-agent plugin that compile wasteful requests into minimal ones and measure the savings
- **Watchdog — Compute Bubble Index**: how much of the deployed AI compute actually produced value? Top-down capital data (capex vs. AI revenue, circular deals, depreciation assumptions) meets bottom-up measurements (model over-computation, avoidable usage), published as a dashboard and a quarterly "gold rush bill" report ([design, KO](docs/BUBBLE_INDEX.md))
- **Standard**: a Token Efficiency Index for models and products

Principles: local-first (raw text never leaves your device), two-step consent, no LLM calls in the analysis path, cold data and bold messages, and a mirror rather than an enemy to model developers. Public goods (data, standard, core engine) are held by a foundation under irrevocable open licenses. Full charter: [docs/CHARTER.md](docs/CHARTER.md).

## License

Code: [Apache-2.0](LICENSE) · Data: [ODbL 1.0](DATA_LICENSE.md)

---

## 한국어

**Pickaxe Tax (곡괭이세)**: 골드러시에서 돈을 버는 건 곡괭이 판매자다. 우리는 그 세금을 그만 낸다. 운동명은 **#AntiTokenMaxing**이다.

> **AI는 같은 대화를 매 턴 처음부터 다시 읽습니다.**
> 원문은 버리고, 대화의 *모양*만 남겨, 불필요했던 연산을 드러냅니다.

프로젝트의 핵심 가치, 방향성, 조직 구조는 [프로젝트 헌장](docs/CHARTER.md)에 정리되어 있습니다.

### 왜 만드나

"토큰맥싱"(token-maxing)은 습관입니다. 조건을 나중에 덧붙이고, 같은 질문을 다시 하고, 답이 끝난 뒤 "고마워"를 보내고, 한 창에서 주제를 바꿔 계속 이어 갑니다. 채팅형 AI는 답할 때마다 **이전 대화 전체를 다시 입력으로 읽기** 때문에 이런 습관의 비용은 대화 길이에 따라 제곱으로 커집니다. 40번째 턴의 "고마워" 한 마디는 수만 토큰을 다시 처리하게 만듭니다.

이렇게 불어난 연산은 GPU, 데이터센터, 전력 수요로 이어집니다. 이 프로젝트는 그 낭비를 **측정 가능한 숫자**로 보여 주고, 다음 대화에서 바로 쓸 수 있는 습관과 프롬프트 골격으로 되돌려 주는 공익 프로젝트입니다. 배경과 원칙은 [docs/MANIFESTO.md](docs/MANIFESTO.md)에 있습니다.

### 무엇을 하나

1. **올리기**: ChatGPT·Claude·Gemini 등의 공유 링크, 데이터 내보내기 JSON, 또는 `User:` / `Assistant:` 형식의 텍스트
2. **골격 추출**: 원문을 메모리에서만 분석해 다음 항목을 뽑습니다
   - **아젠다**: 대화의 핵심 주제 라벨
   - **스트럭처**: 턴마다의 의도(질문·지시·보충·정정·재질문·계속·감사·대용량 붙여넣기)와 턴 사이의 관계(DEEPENS, PIVOTS, RETURNS, CORRECTS, RETRIES …)
   - **뎁스**: 주제 갈래(branch)와 각 갈래 안의 파고들기 깊이
   - **토큰 흐름**: 보이는 토큰, 실제 과금 입력(이력 재전송), 출력
3. **원문 폐기**: 텍스트는 저장하지 않습니다. 저장되는 것은 골격(숫자, 의도 라벨, 주제 라벨, 솔트된 지문)뿐입니다
4. **그래프 DB화**: `(:Conversation)-[:HAS_TURN]->(:Turn)-[:ABOUT]->(:Topic)` 형태의 속성 그래프로 저장합니다. Neo4j로 보낼 수 있는 Cypher 내보내기도 제공합니다
5. **되돌려 주기**
   - 실제 연산과 최적 연산 비교 (주제별 새 대화 + 낭비 제거 기준, 한 번에 물었을 때의 하한선)
   - 낭비 유형별 비중: 감사 메시지, 버려진 답변, 무관한 주제 재전송
   - 주제 라벨만으로 만든 **한 번에 끝내는 프롬프트 골격**
   - 측정된 낭비 순으로 정렬한 습관 교정 팁
6. **공익 그래프**: 기여된 골격을 집계해 주제 동시출현 그래프와 전체 낭비 통계를 공개합니다. **k-익명성**을 적용해 k개(기본 3개) 이상의 대화에서 등장한 주제만 노출합니다

분석기 자체는 **LLM을 호출하지 않습니다.** 규칙 기반 의도 분류, 키워드 랭킹, SimHash를 쓰므로 분석에 드는 연산은 거의 0입니다.

### 빠른 시작

```bash
pip install -e ".[dev]"
pickaxetax serve                    # http://127.0.0.1:8000
# 또는
pickaxetax analyze chat.txt         # 로컬 분석 (기본값은 저장 안 함)
pickaxetax analyze conversations.json --save
pickaxetax analyze https://chatgpt.com/share/... --json
pickaxetax export > public_graph.cypher
pytest
```

| 환경 변수 | 기본값 | 설명 |
|---|---|---|
| `PICKAXETAX_DB` | `data/pickaxetax.sqlite3` | 그래프 저장소 경로 |
| `PICKAXETAX_SECRET` | 자동 생성 후 DB에 보관 | ID와 지문에 쓰는 솔트. 운영 환경에서는 직접 지정 권장 |
| `PICKAXETAX_K_ANON` | `3` | 공개 그래프의 k-익명성 임계값 (API로는 낮출 수 없음) |
| `PICKAXETAX_INPUT_WEIGHT` | `0.25` | 입력 토큰 연산 가중치 (출력 = 1) |
| `PICKAXETAX_WH_PER_1K` | `0.5` | 1k 연산 단위당 Wh. **예시용 가정치** |

### API

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/analyze` | `{"input": "<링크|JSON|텍스트>", "save": true}` |
| POST | `/api/analyze/file` | multipart 파일 업로드 (`file`, `save`) |
| GET | `/api/conversations/{id}` | 골격 조회 |
| GET | `/api/conversations/{id}/graph.json` · `/cypher` | 내보내기 |
| DELETE | `/api/conversations/{id}` | `X-Delete-Token` 헤더로 내 기여 삭제 |
| GET | `/api/stats` | 전체 임팩트 집계 |
| GET | `/api/topics` · `/api/topics/cypher` | k-익명 주제 그래프 |

대화형 문서는 `/api/docs`에 있습니다.

### 구조

```
pickaxetax/
  ingest/     공유 링크(SSRF 방지 허용 목록), 내보내기 JSON, 텍스트 파서
  analyze/    의도 분류 · 깊이/갈래 · 토큰 회계 · 제안 생성 (LLM 미사용)
  graph/      SQLite 속성 그래프 저장소 + Cypher/JSON 내보내기
  web/        FastAPI + 의존성 없는 단일 페이지 UI (한/영)
  cli.py
docs/         MANIFESTO · ARCHITECTURE · PRIVACY
```

자세한 설계는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), 개인정보 설계는 [docs/PRIVACY.md](docs/PRIVACY.md)를 보세요.

### 로드맵

- [ ] 브라우저 확장 또는 WASM으로 **클라이언트 측 골격 추출** (원문이 서버로 아예 가지 않게)
- [ ] 공유 페이지 파서 강화 (클라이언트 렌더링되는 ChatGPT와 Gemini 신규 포맷)
- [ ] 집계 통계에 차등 프라이버시 노이즈 추가
- [ ] 주제별 "최단 경로" 패턴 라이브러리: 같은 아젠다를 가장 적은 턴으로 끝낸 구조 공유
- [ ] 다국어 형태소 처리 (일본어, 중국어 분절)
- [ ] Neo4j·Memgraph 백엔드 어댑터, 공개 데이터셋 정기 배포
- [ ] 측정 기반 에너지 계수 (공개 벤치마크 연동)
- [ ] 요청 속도 제한과 악용 방지

### 라이선스

코드는 [Apache-2.0](LICENSE), 데이터는 [ODbL 1.0](DATA_LICENSE.md)을 따릅니다.
