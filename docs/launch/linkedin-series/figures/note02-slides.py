"""Note 2 figures: 4 slides (1080x1350), Korean and English, numbers from the committed data."""
import json, os, re
from pickaxetax.survey.dataset import derive
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")) + "/"  # repo root
# run from the repo root: python3 docs/launch/linkedin-series/figures/note02-slides.py
FJ = json.load(open(R + "research/survey/user01/floor-t1.json"))
F = FJ["total"]
D = derive(json.load(open(R + "research/survey/user01/dataset-v2.json")))
D1 = derive(json.load(open(R + "research/survey/user01/dataset.json")))
O = json.load(open(R + "research/survey/user01/opportunity-v1.json"))
OP = O["merged"]["policies"]
OG = [v for k, v in O["sensitivity"].items() if k.endswith(",calibrated")]
orng = lambda p: (min(v["avoidable_pct"][p] for v in OG), max(v["avoidable_pct"][p] for v in OG))
SC = F["steps_spent_only_on"]
step_pct = 100 * (SC["W1"]["input"] + SC["W2"]["input"]) / F["input_processed"]
src01 = open(R + "docs/launch/linkedin-series/figures/note01-slides.template.html").read()
CSS = src01[src01.index("<style>"):src01.index("</style>") + 8]
CSS = CSS.replace("</style>", """
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.pair .cell { border: 2px solid var(--ink); border-radius: 8px; padding: 20px 22px; display: grid; gap: 10px; align-content: start; }
.pair .cell.hot { border-color: var(--carried); }
.pair .cell .lbl { font-size: 22px; font-weight: 800; }
.pair .cell .sub { font-size: 18px; line-height: 1.5; color: var(--ink2); }
.big.hot { color: var(--carried); }
table.n td.r, table.n th.r { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tr.main td { font-weight: 800; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 28px; font-size: 20px; font-weight: 700; }
.legend i { display: inline-block; width: 18px; height: 18px; border-radius: 3px; margin-right: 8px; vertical-align: -2px; }
.toc b { width: 120px; }
.obar { height: 22px; background: var(--carried); border-radius: 3px; }
.obar.dim { background: #a9a7a1; }
table.o td { vertical-align: middle; }
.sub2 { font-size: 17px; line-height: 1.5; color: var(--ink2); }
</style>""")

W = 936
def bar3(parts, colors, labels, sub, aria):
    """A 100% stacked bar; the legend is HTML below it, so labels never collide."""
    out = [f'<svg width="{W}" height="60" viewBox="0 0 {W} 60" role="img" aria-label="{aria}">']
    x = 0.0
    for p, c in zip(parts, colors):
        w = W * p / 100
        out.append(f'<rect x="{x:.1f}" y="0" width="{max(w - 3, 1):.1f}" height="60" fill="{c}"/>')
        x += w
    out.append("</svg>")
    leg = "".join(f'<span><i style="background:{c}"></i>{lab}</span>' for c, lab in zip(colors, labels))
    return "".join(out) + f'<div class="legend">{leg}</div><p class="sub2">{sub}</p>'

def hbar(rows, maxv, unit_fmt, aria, gutter=250, rowh=56):
    # rows: (label, value, color)
    h = rowh * len(rows) + 10
    out = [f'<svg width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{aria}"><g font-size="19" fill="#0b0b0b">']
    x0, span = gutter, W - gutter - 150
    for i, (lab, v, c) in enumerate(rows):
        y = 10 + rowh * i
        w = max(span * v / maxv, 2)
        bh = min(32, rowh - 12)
        ty = y + 6 + bh / 2 + 7
        out.append(f'<text x="0" y="{ty:.1f}" font-weight="700">{lab}</text>')
        out.append(f'<rect x="{x0}" y="{y + 6}" width="{w:.1f}" height="{bh}" rx="3" fill="{c}"/>')
        out.append(f'<text x="{x0 + w + 12:.1f}" y="{ty:.1f}" font-weight="800">{unit_fmt(v)}</text>')
    out.append("</g></svg>")
    return "".join(out)

bc = F["W6"]["by_cause"]; w6 = F["W6"]["tokens"]
pc = {k: 100 * bc[k]["tokens"] / w6 for k in ("gap_under_5m", "gap_5m_to_1h", "gap_over_1h")}
S = F["sensitivity_pct_price_weighted"]
dec = D["decomposition"]; dt = sum(dec.values()); dp = {k: 100 * v / dt for k, v in dec.items()}
avg_w6 = w6 / F["W6"]["count"]

T = {
"ko": dict(
  head="#AntiTokenMaxing · 연구 노트 #2",
  cap1="21세기 골드러시의 영수증 · 첫 판정", h1="버리는 문제가 아니라,<br>들고 다니는 문제",
  lead1="판정 기준 v1에서 기록만으로 정할 수 있는 세 갈래(W1·W2·W6)를 세션 10개에 적용하고,<br>이미 끝난 지시에서 넘어온 맥락이 다시 쓰였는지 추적했습니다.",
  toc=["측정 범위 정정과 기계 판정 하한", "재작성은 언제 생겼나, 그리고 범위", "넘어온 76%는 다시 쓰였나"],
  fig="그림", src1="판정 기준 v1 (2026-10-06 고정) · 기계 판정 규칙 research/protocol/mechanical-tier-v1.md · 조사 대상: 연구자 본인의 Claude Code 세션 10개, 2026-07-10 ~ 10-05 · github.com/graviton94/pickaxetax",
  h2a="토큰으로는 거의 0, 비용으로는 {c:.2f}%",
  ka="A. 측정 범위 정정 <span>· 처리한 입력, 하위 에이전트 포함</span>",
  scope_note="늘어난 {d:.1f}억 토큰은 1편 때 받지 못했던 S09의 앞부분(8월 12~15일)과 그 하위 에이전트, 그리고 S01의 하위 에이전트(44만 토큰)입니다. 10개 세션 모두 세션 첫 이벤트부터 끝까지 받았습니다.",
  kh="C. 세션별 지울 수 있던 비용 <span>· v1 규칙</span>",
  v1lab="1편 (S09 일부만)", v2lab="판 2 (10개 모두 완전)",
  okr=lambda v: f"{v/1e8:.1f}억",
  kb="B. 기계 판정 하한 <span>· 세 갈래 합</span>",
  tok_lbl="지울 수 있던 토큰", tok_sub="중복(W1)과 오류(W2) 결과 ÷ 처리한 입력 전체. W6 토큰은 어차피 처리됐을 토큰이라 넣지 않습니다.",
  cost_lbl="지울 수 있던 비용", cost_sub="W1·W2는 캐시 쓰기 값(1.25), W6은 쓰기와 읽기의 값 차이(1.25 − 0.1)로 매겨 입력 쪽 비용 전체와 비교.",
  step_note="참고 (하한 밖): 중복이나 오류만 받고 끝난 걸음 {n}번이 처리한 입력은 {p:.1f}%입니다. 한 걸음마다 맥락 전체를 다시 읽기 때문입니다. 오류에는 실패한 테스트 같은 검증이 섞여 있어 사람 판정으로 가립니다.",
  kc="C. 갈래별 <span>· 건수와 토큰</span>",
  th=["갈래", "건", "토큰", "어디에 들어가나"],
  rows=[("W1 중복", "토큰·비용"), ("W2 오류", "토큰·비용"), ("W6 캐시 재작성", "비용만")],
  src2="출처: research/survey/user01/floor-t1.json · dataset-v2.json (S09 완전 측정, 판 1은 그대로 보존). 가격 비율은 제공사 정가(비캐시 1, 캐시 읽기 0.1, 캐시 쓰기 1.25).",
  h2b="재작성의 {p:.0f}%는 1시간 넘게 쉬었다 돌아온 직후",
  kd="A. W6가 생긴 때 <span>· 직전 호출과의 간격, 토큰 기준</span>",
  gl=["5분 안 {:.0f}%", "5분~1시간 {:.0f}%", "1시간 넘게 {:.0f}%"],
  gsub="캐시 수명은 기본 5분, 선택 1시간. 모델을 바꾼 직후에 생긴 재작성은 없었습니다.",
  ke="B. 어떤 재작성을 세느냐에 따른 범위 <span>· 지울 수 있던 비용</span>",
  sens=["재작성 모두 (v1 규칙, 본 결과)", "1시간 넘게 쉰 뒤의 재작성 제외", "5분 안의 재작성만"],
  note_b="쉰 것이 낭비는 아닙니다. 돌아올 때마다 맥락 전체(평균 {a:.0f}만 토큰)를 처음부터 다시 처리하게 만드는 구조가 비효율적이고, 한 세션을 며칠씩 이어 쓰는 사용 방식이 그 비용을 키웁니다.",
  src3="본 결과는 미리 정한 v1 규칙입니다. 나머지 두 기준은 결과를 본 뒤에 더한 민감도 분석이며 본 결과를 대신하지 않습니다.",
  h2c="버릴 것은 적고, 들고 다닌 것은 많다",
  kf="A. 매 호출 입력의 구성 <span>· 판 2, 세션 10개 전체 호출 합</span>",
  dl=["고정 {:.1f}%", "이전 지시에서 넘어온 몫 {:.1f}%", "지금 지시 {:.1f}%"],
  dsub="1편의 73.6%는 시계열이 있던 세션 8개 기준이고, 판 2는 10개 모두입니다.",
  kg="B. 넘어온 내용은 다시 쓰였나 <span>· 오라클 최소치, 주 세션 {m:.1f}억 토큰</span>",
  oth=["필요한 것만 들고 갔다면", "덜 읽었을 몫", "탐지 기준 9가지"],
  orows=["다시는 안 쓰인 것만 버리기", "필요할 때 다시 불러오기 (1천 토큰)", "불러오기가 공짜라면"],
  note_c="끝까지 다시 쓰이지 않은 내용은 적었습니다. 대부분은 언젠가 다시 쓰였지만, 그때까지 매 호출마다 다시 읽혔습니다. 미래를 아는 오라클의 값이라 실현 가능한 정책의 결과가 아니라 기회의 크기이고, 재사용은 글자 겹침으로 추정했습니다. 보정 없이 가장 보수적으로 잡으면 필요할 때 불러오기는 {lo:.0f}~{hi:.0f}%입니다.",
  nxt="<b>다음</b>연습 20개 → 본 판정 200개, 두 사람이 서로의 판정을 모른 채 → 갈래별 일치도 κ ≥ 0.70일 때만 결과를 냅니다.",
  src4="출처: dataset-v2.json → pxt survey report (report-v2.html) · research/survey/user01/opportunity-v1.md (pickaxetax.agent.bound, lexical-v1, 기본 기준 min_shared 1, common_frac 0.02, 보정)",
),
"en": dict(
  head="#AntiTokenMaxing · Research note #2",
  cap1="The receipt of the 21st-century gold rush · first judgment", h1="Not what to throw away,<br>but what we carry",
  lead1="The three categories of codebook v1 that the records decide on their own (W1, W2, W6), applied to all ten sessions,<br>and a trace of whether context carried over from finished instructions was used again.",
  toc=["Corrected scope and the mechanical floor", "When re-writes happened, and the range", "Was the carried-over 76% used again?"],
  fig="Figure", src1="Waste codebook v1 (frozen 2026-10-06) · mechanical rules: research/protocol/mechanical-tier-v1.md · subject: the researcher's own 10 Claude Code sessions, 2026-07-10 to 10-05 · github.com/graviton94/pickaxetax",
  h2a="Close to zero in tokens, {c:.2f}% in cost",
  ka="A. Corrected scope <span>· input processed, sub-agents included</span>",
  scope_note="The added {d:.2f} billion tokens are the first part of S09 (August 12–15) that note 1 had not fetched with its sub-agents, plus S01's sub-agents (0.44 M). All ten sessions are now fetched from their first event to their last.",
  kh="C. Removable cost by session <span>· v1 rule</span>",
  v1lab="Note 1 (S09 in part)", v2lab="v2 (all 10 complete)",
  okr=lambda v: f"{v/1e9:.2f} bn",
  kb="B. The mechanical floor <span>· three categories</span>",
  tok_lbl="Removable tokens", tok_sub="Duplicate (W1) and error (W2) results ÷ all input processed. W6 tokens would have been processed anyway, so they are not included.",
  cost_lbl="Removable cost", cost_sub="W1 and W2 at the cache-write price (1.25), W6 at the write premium over a read (1.25 − 0.1), as a share of the input-side cost.",
  step_note="For reference (outside the floor): {n} steps that got back only duplicates or errors processed {p:.1f}% of the input, since every step re-reads the whole context. Errors include verification such as failing tests, so people will sort them.",
  kc="C. By category <span>· events and tokens</span>",
  th=["Category", "Events", "Tokens", "Counted in"],
  rows=[("W1 duplication", "tokens · cost"), ("W2 errors", "tokens · cost"), ("W6 cache re-write", "cost only")],
  src2="Sources: research/survey/user01/floor-t1.json · dataset-v2.json (S09 measured in full; v1 kept as published). Price ratios: provider list prices (uncached 1, cache read 0.1, cache write 1.25).",
  h2b="{p:.0f}% of re-writes followed a break of over an hour",
  kd="A. When W6 happened <span>· gap since the previous call, by tokens</span>",
  gl=["Under 5 min {:.0f}%", "5 min–1 h {:.0f}%", "Over 1 h {:.0f}%"],
  gsub="The cache lives 5 minutes by default, 1 hour as an option. No re-write followed a model switch.",
  ke="B. The range, by which re-writes count <span>· removable cost</span>",
  sens=["All re-writes (v1 rule, primary result)", "Without re-writes after an idle hour", "Re-writes within 5 minutes only"],
  note_b="Taking a break is not waste. The structure is inefficient: every return re-processes the whole context from scratch ({a:.0f},000 tokens on average). Keeping one session going for days makes that cost bigger.",
  src3="The primary result uses the v1 rule fixed in advance. The other two counts are a sensitivity analysis added after the results were seen; they never replace it.",
  h2c="Little to throw away, a lot carried",
  kf="A. What each call's input is made of <span>· v2, all calls of the 10 sessions</span>",
  dl=["Fixed {:.1f}%", "Carried over from finished instructions {:.1f}%", "Current {:.1f}%"],
  dsub="Note 1's 73.6% covered the 8 sessions that had per-call series; v2 covers all 10.",
  kg="B. Was the carried-over content used again? <span>· oracle bound, main sessions, {m:.2f} bn tokens</span>",
  oth=["Carrying only what is needed", "Less input", "9 detection settings"],
  orows=["Drop only what is never used again", "Fetch again when needed (1,000 tokens)", "Fetching is free"],
  note_c="Little was never used again. Most of it was used at some point, but until then it was re-read on every call. These are an oracle's numbers: the size of the opportunity, not the result of a policy one could run, and reuse is estimated from overlapping words. Without calibration, the most conservative range for fetching on demand is {lo:.0f}–{hi:.0f}%.",
  nxt="<b>Next</b>20 practice items → 200 main items, two people labeling without seeing each other's labels → a category is reported only if κ ≥ 0.70.",
  src4="Sources: dataset-v2.json → pxt survey report (report-v2.html) · research/survey/user01/opportunity-v1.md (pickaxetax.agent.bound, lexical-v1; default min_shared 1, common_frac 0.02, calibrated)",
),
}

for lang, t in T.items():
    top = lambda n: f'<div class="top"><span>{t["head"]}</span><span>{n} / 4</span></div>'
    s1 = f'''<section class="slide" id="s1">{top(1)}
  <div style="margin-top:110px; display:grid; gap:34px"><p class="cap">{t["cap1"]}</p><h1>{t["h1"]}</h1><p class="lead">{t["lead1"]}</p></div>
  <div class="toc" style="margin-top:90px">{"".join(f'<div><b>{t["fig"]} {i+1}</b>{x}</div>' for i, x in enumerate(t["toc"]))}</div>
  <p class="src">{t["src1"]}</p></section>'''
    v1, v2 = D1["total_input"], D["total_input"]
    scope = hbar([(t["v1lab"], v1, "#52514e"), (t["v2lab"], v2, "#0b0b0b")], v2, t["okr"], f"{t['okr'](v1)} → {t['okr'](v2)}")
    rows = [("W1", F["W1"]), ("W2", F["W2"]), ("W6", F["W6"])]
    trs = "".join(f'<tr><td class="c">{lab}</td><td class="r">{v["count"]:,}</td><td class="r">{v["tokens"]:,}</td><td>{inn}</td></tr>'
                  for (lab, inn), (_, v) in zip(t["rows"], rows))
    s2 = f'''<section class="slide" id="s2">{top(2)}
  <div><p class="cap">{t["fig"]} 1</p><h2>{t["h2a"].format(c=F["floor_pct_price_weighted"])}</h2></div>
  <div class="panel"><p class="k">{t["ka"]}</p>{scope}<p class="sub2">{t["scope_note"].format(d=(v2 - v1) / (1e8 if lang == "ko" else 1e9))}</p></div>
  <div class="panel"><p class="k">{t["kb"]}</p><div class="pair">
    <div class="cell"><span class="lbl">{t["tok_lbl"]}</span><span class="big">{F["floor_pct_of_input"]:.4f}<small>%</small></span><span class="sub">{t["tok_sub"]}</span></div>
    <div class="cell hot"><span class="lbl">{t["cost_lbl"]}</span><span class="big hot">{F["floor_pct_price_weighted"]:.2f}<small>%</small></span><span class="sub">{t["cost_sub"]}</span></div></div>
    <p class="sub2">{t["step_note"].format(n=SC["W1"]["calls"] + SC["W2"]["calls"], p=step_pct)}</p></div>
  <div class="panel"><p class="k">{t["kc"]}</p><table class="n"><thead><tr><th>{t["th"][0]}</th><th class="r">{t["th"][1]}</th><th class="r">{t["th"][2]}</th><th>{t["th"][3]}</th></tr></thead><tbody>{trs}</tbody></table></div>
  <p class="src">{t["src2"]}</p></section>'''
    gaps = bar3([pc["gap_under_5m"], pc["gap_5m_to_1h"], pc["gap_over_1h"]], ["#2a78d6", "#a9a7a1", "#eb6834"],
                [g.format(p) for g, p in zip(t["gl"], (pc["gap_under_5m"], pc["gap_5m_to_1h"], pc["gap_over_1h"]))], t["gsub"], "W6")
    sv = [S["all_w6 (v1)"], S["without_gap_over_1h"], S["only_gap_under_5m"]]
    sens_rows = "".join(f'<tr class="{"main" if i == 0 else ""}"><td>{lab}</td><td class="r">{v:.2f}%</td></tr>' for i, (lab, v) in enumerate(zip(t["sens"], sv)))
    a = round(avg_w6 / 1e4) * (1 if lang == "ko" else 10)  # 44만 / 440,000
    ss = sorted(FJ["sessions"].items())
    persess = hbar([(k, v["floor_pct_price_weighted"], "#eb6834") for k, v in ss], max(v["floor_pct_price_weighted"] for _, v in ss),
                   lambda v: f"{v:.2f}%", "by session", gutter=70, rowh=31)
    s3 = f'''<section class="slide" id="s3">{top(3)}
  <div><p class="cap">{t["fig"]} 2</p><h2>{t["h2b"].format(p=pc["gap_over_1h"])}</h2></div>
  <div class="panel"><p class="k">{t["kd"]}</p>{gaps}</div>
  <div class="panel"><p class="k">{t["ke"]}</p><table class="n"><tbody>{sens_rows}</tbody></table></div>
  <p class="note">{t["note_b"].format(a=a)}</p>
  <div class="panel"><p class="k">{t["kh"]}</p>{persess}</div>
  <p class="src">{t["src3"]}</p></section>'''
    decbar = bar3([dp["fixed"], dp["carried"], dp["current"]], ["#2a78d6", "#eb6834", "#1baf7a"],
                  [g.format(p) for g, p in zip(t["dl"], (dp["fixed"], dp["carried"], dp["current"]))], t["dsub"], "decomposition")
    pols = ["P=inf", "P=1000", "P=0"]
    raw = [v for k, v in O["sensitivity"].items() if k.endswith(",raw")]
    lo, hi = min(v["avoidable_pct"]["P=1000"] for v in raw), max(v["avoidable_pct"]["P=1000"] for v in raw)
    orows = "".join(
        f'<tr><td>{lab}</td><td style="width:38%"><div class="obar{"" if p == "P=1000" else " dim"}" style="width:{OP[p]["avoidable_pct"] / 60 * 100:.1f}%"></div></td>'
        f'<td class="r"><b>{OP[p]["avoidable_pct"]:.1f}%</b></td><td class="r">{orng(p)[0]:.1f}{"~" if lang == "ko" else "–"}{orng(p)[1]:.1f}%</td></tr>'
        for lab, p in zip(t["orows"], pols))
    omain = O["merged"]["measured_input"] / (1e8 if lang == "ko" else 1e9)
    otable = f'<table class="n o"><thead><tr><th>{t["oth"][0]}</th><th></th><th class="r">{t["oth"][1]}</th><th class="r">{t["oth"][2]}</th></tr></thead><tbody>{orows}</tbody></table>'

    s4 = f'''<section class="slide" id="s4">{top(4)}
  <div><p class="cap">{t["fig"]} 3</p><h2>{t["h2c"]}</h2></div>
  <div class="panel"><p class="k">{t["kf"]}</p>{decbar}</div>
  <div class="panel"><p class="k">{t["kg"].format(m=omain)}</p>{otable}<p class="note">{t["note_c"].format(lo=lo, hi=hi)}</p></div>
  <div class="box">{t["nxt"]}</div>
  <p class="src">{t["src4"]}</p></section>'''
    html = '<!doctype html><meta charset="utf-8">\n' + CSS + "\n" + "\n".join([s1, s2, s3, s4]) + "\n"
    name = "note02-slides.html" if lang == "ko" else "note02-slides.en.html"
    open(R + "docs/launch/linkedin-series/figures/" + name, "w").write(html)
    print(name, len(html))
