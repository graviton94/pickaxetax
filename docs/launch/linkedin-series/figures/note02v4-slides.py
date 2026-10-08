"""Note 2 v4 figures: 5 slides (1080x1350), Korean. Numbers from research/phase2 (M1, M2, synthesis); schematics are analogies.
run from the repo root: python3 docs/launch/linkedin-series/figures/note02v4-slides.py"""
import os
H = os.path.dirname(os.path.abspath(__file__)) + "/"
src = open(H + "note02-slides.html").read()
CSS = src[src.index("<style>"):src.index("</style>")] + """
.toc b { width: 120px; }
.sub2 { font-size: 18px; line-height: 1.55; color: var(--ink2); }
.legend { display: flex; flex-wrap: wrap; gap: 8px 26px; font-size: 19px; font-weight: 700; }
.legend i { display: inline-block; width: 18px; height: 18px; border-radius: 3px; margin-right: 8px; vertical-align: -2px; }
.kpi { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.kpi div { border: 2px solid var(--ink); border-radius: 8px; padding: 16px 18px; }
.kpi div.hot { border-color: var(--carried); }
.kpi b { display: block; font-size: 54px; font-weight: 850; letter-spacing: -.03em; line-height: 1.05; }
.kpi div.hot b { color: var(--carried); }
.kpi span { font-size: 18px; color: var(--ink2); }
td.r { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.ok { color: var(--current); font-weight: 800; } .ng { color: var(--carried); font-weight: 800; }
</style>"""

W = 936
INK, INK2, RULE, HOT, BR, FIX = "#0b0b0b", "#52514e", "#dedcd6", "#eb6834", "#1baf7a", "#2a78d6"
TOP = '<div class="top"><span>#AntiTokenMaxing · 연구 노트 #2</span><span>{n} / 5</span></div>'
SRC = "출처: research/phase2/synthesis.md, M1-minimal-rules.md, M2-minimal-rules-v2.md, brain-map.md · 연구자 본인의 Claude Code 세션 10개(석 달) · github.com/graviton94/pickaxetax"

def ctx_y(v):  # thousand tokens -> y
    return 230 - v * 0.2625

def saw(x0, x1, lo, hi, slope):
    pts, x = [f"M{x0} {ctx_y(lo):.1f}"], x0
    while x < x1 - 0.1:
        x2 = min(x + (hi - lo) / slope, x1)
        pts.append(f"L{x2:.1f} {ctx_y(lo + (x2 - x) * slope):.1f}")
        if x2 < x1:
            pts.append(f"L{x2:.1f} {ctx_y(lo):.1f}")
        x = x2
    return " ".join(pts)

SLOPE = (783 - 64) / 438
AX = f'''<line x1="60" y1="230" x2="{W}" y2="230" stroke="{INK}" stroke-width="2"/>
<line x1="60" y1="20" x2="60" y2="230" stroke="{INK}" stroke-width="2"/>
<g font-size="17" fill="{INK2}" text-anchor="end"><text x="52" y="{ctx_y(800)+6:.0f}">80만</text><text x="52" y="{ctx_y(400)+6:.0f}">40만</text><text x="52" y="236">0</text></g>
<line x1="60" y1="{ctx_y(400):.1f}" x2="{W}" y2="{ctx_y(400):.1f}" stroke="{RULE}" stroke-dasharray="3 5"/>
<text x="{W}" y="256" font-size="17" fill="{INK2}" text-anchor="end">걸음 →</text>'''

def sawchart(with_r3):
    obs = saw(60, W, 64, 783, SLOPE)
    s = [f'<svg width="{W}" height="262" viewBox="0 0 {W} 262" role="img" aria-label="맥락 크기 톱니">', AX]
    s.append(f'<path d="{obs} L{W} 230 L60 230 Z" fill="{HOT}" opacity=".13"/><path d="{obs}" fill="none" stroke="{HOT}" stroke-width="3"/>')
    s.append(f'<line x1="60" y1="{ctx_y(423):.1f}" x2="{W}" y2="{ctx_y(423):.1f}" stroke="{HOT}" stroke-width="2" stroke-dasharray="8 6"/>')
    s.append(f'<text paint-order="stroke" stroke="#fcfcfb" stroke-width="7" x="536" y="{ctx_y(423)-12:.0f}" font-size="19" font-weight="800" fill="{HOT}">지금: 평균 약 42만, 상한 78.3만</text>')
    if with_r3:
        r3 = saw(60, W, 64, 150, SLOPE)
        s.append(f'<path d="{r3} L{W} 230 L60 230 Z" fill="{BR}" opacity=".25"/><path d="{r3}" fill="none" stroke="{BR}" stroke-width="2.4"/>')
        s.append(f'<line x1="60" y1="{ctx_y(150):.1f}" x2="{W}" y2="{ctx_y(150):.1f}" stroke="{BR}" stroke-width="1.5" stroke-dasharray="4 4"/>')
        s.append(f'<text paint-order="stroke" stroke="#fcfcfb" stroke-width="7" x="76" y="{ctx_y(150)-14:.0f}" font-size="19" font-weight="800" fill="{BR}">역치 15만에서 압축: 평균 약 11만</text>')
    s.append("</svg>")
    return "".join(s)

def neuron_trace():
    # schematic membrane potential: ramps to threshold, spike, reset (analogy figure)
    y_rest, y_th, y_top, y_low = 150, 90, 14, 166
    d, x = [f"M60 {y_rest}"], 60
    for _ in range(8):
        x += 78; d.append(f"Q{x-30} {y_rest-4} {x} {y_th}")
        d.append(f"L{x+6} {y_top} L{x+14} {y_low} L{x+26} {y_rest}"); x += 26
    s = [f'<svg width="{W}" height="180" viewBox="0 0 {W} 180" role="img" aria-label="뉴런 막전위 모식도: 문턱에서 발화 후 리셋">']
    s.append(f'<line x1="60" y1="{y_th}" x2="{W}" y2="{y_th}" stroke="{BR}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    s.append(f'<path d="{" ".join(d)}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    s.append(f'<g font-size="17" fill="{INK2}"><text x="52" y="{y_th+6}" text-anchor="end" fill="{BR}" font-weight="800">문턱</text><text x="52" y="{y_rest+6}" text-anchor="end">휴지</text></g>')
    s.append('</svg>')
    return "".join(s)

def bars(groups):
    rowh, gut = 50, 330
    n = sum(len(g[1]) + 1 for g in groups)
    h = rowh * n + 6
    s = [f'<svg width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="뇌 기전별 규칙의 입력 절약"><g font-size="19" fill="{INK}">']
    y, span = 0, W - gut - 140
    for title, rows, col in groups:
        s.append(f'<text x="0" y="{y+30}" font-size="18" font-weight="800" fill="{col}">{title}</text>'); y += rowh
        for lab, brain, v, txt in rows:
            s.append(f'<text x="0" y="{y+28}" font-weight="700">{lab}</text><text x="{gut-14}" y="{y+28}" text-anchor="end" fill="{INK2}" font-size="17">{brain}</text>')
            if v is None:
                s.append(f'<rect x="{gut}" y="{y+10}" width="{span}" height="26" fill="{HOT}" opacity=".14"/>')
                s.append(f'<text x="{gut+12}" y="{y+29}" font-weight="800" fill="{HOT}">{txt}</text>')
            else:
                w = max(span * v / 80, 3)
                s.append(f'<rect x="{gut}" y="{y+10}" width="{w:.1f}" height="26" rx="3" fill="{col}"/><text x="{gut+w+12:.1f}" y="{y+29}" font-weight="800">{txt}</text>')
            y += rowh
    s.append("</g></svg>")
    return "".join(s)

BRAIN_VS = f'''<svg width="{W}" height="430" viewBox="0 0 {W} 430" role="img" aria-label="뇌와 에이전트의 기억 구조 모식도">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{INK}"/></marker>
<marker id="ab" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{BR}"/></marker>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{HOT}"/></marker></defs>
<g font-size="19" fill="{INK}">
<text x="0" y="24" font-size="22" font-weight="800" fill="{BR}">뇌 (비유)</text>
<text x="490" y="24" font-size="22" font-weight="800" fill="{HOT}">AI 에이전트 (측정)</text>
<line x1="468" y1="0" x2="468" y2="430" stroke="{RULE}" stroke-width="2"/>
<!-- brain: working memory -->
<rect x="0" y="50" width="200" height="96" rx="8" fill="none" stroke="{INK}" stroke-width="2"/>
<text x="14" y="76" font-weight="800">작업기억</text><text x="14" y="98" font-size="16" fill="{INK2}">몇 덩이만 담음</text>
<g fill="{BR}"><circle cx="34" cy="124" r="9"/><circle cx="64" cy="124" r="9"/><circle cx="94" cy="124" r="9"/><circle cx="124" cy="124" r="9"/></g>
<!-- brain: long-term network -->
<g stroke="{BR}" stroke-width="2" opacity=".75"><line x1="40" y1="300" x2="110" y2="260"/><line x1="110" y1="260" x2="190" y2="300"/><line x1="110" y1="260" x2="120" y2="350"/><line x1="40" y1="300" x2="120" y2="350"/><line x1="190" y1="300" x2="260" y2="250"/><line x1="190" y1="300" x2="250" y2="360"/><line x1="120" y1="350" x2="250" y2="360"/><line x1="260" y1="250" x2="330" y2="300"/><line x1="250" y1="360" x2="330" y2="300"/><line x1="330" y1="300" x2="410" y2="270"/><line x1="330" y1="300" x2="400" y2="360"/></g>
<g fill="#fcfcfb" stroke="{BR}" stroke-width="2.5"><circle cx="40" cy="300" r="11"/><circle cx="110" cy="260" r="11"/><circle cx="190" cy="300" r="11"/><circle cx="120" cy="350" r="11"/><circle cx="260" cy="250" r="11"/><circle cx="250" cy="360" r="11"/><circle cx="330" cy="300" r="11"/><circle cx="410" cy="270" r="11"/><circle cx="400" cy="360" r="11"/></g>
<text x="0" y="404" font-weight="800">장기기억 = 시냅스 연결</text><text x="0" y="426" font-size="16" fill="{INK2}">경험이 연결의 세기로 새겨짐</text>
<path d="M150 146 C150 190 120 210 112 244" fill="none" stroke="{BR}" stroke-width="2.4" marker-end="url(#ab)"/>
<text x="160" y="196" font-size="16" font-weight="700" fill="{BR}">응고(잠잘 때)</text>
<path d="M265 236 C280 170 240 120 204 104" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#a)"/>
<text x="272" y="160" font-size="16" font-weight="700">단서 하나로 인출 · 쌈</text>
<!-- agent: model -->
<rect x="490" y="50" width="170" height="96" rx="8" fill="#f3f2ee" stroke="{INK}" stroke-width="2"/>
<text x="504" y="80" font-weight="800">모델 가중치</text><text x="504" y="104" font-size="16" fill="{INK2}">작업 중엔 고정</text>
<text x="504" y="128" font-size="16" fill="{INK2}">(새기지 못함)</text>
<!-- agent: context stack -->
<g>{''.join(f'<rect x="{490 + i*0}" y="{196 + i*16}" width="{430}" height="13" rx="2" fill="{HOT if i < 9 else BR}" opacity="{0.35 if i < 9 else 0.8}"/>' for i in range(11))}</g>
<text x="490" y="388" font-weight="800">맥락 = 매 걸음 처음부터 다시 읽는 수첩</text>
<text x="490" y="410" font-size="16" fill="{INK2}">최대 78.3만 토큰 · 약 80%가 이미 끝난 일(주황)</text>
<path d="M720 190 C720 150 700 120 664 104" fill="none" stroke="{HOT}" stroke-width="3" marker-end="url(#ah)"/>
<text x="732" y="140" font-size="16" font-weight="800" fill="{HOT}">매 걸음 전체를 다시 읽음</text>
<path d="M580 146 C580 166 600 176 620 190" fill="none" stroke="{INK}" stroke-width="2" marker-end="url(#a)"/>
<text x="512" y="182" font-size="15" fill="{INK2}">결과·생각을 덧붙임</text>
<line x1="676" y1="66" x2="700" y2="90" stroke="{HOT}" stroke-width="3"/><line x1="700" y1="66" x2="676" y2="90" stroke="{HOT}" stroke-width="3"/>
<text x="708" y="84" font-size="15" fill="{INK2}">응고 경로 없음</text>
</g></svg>'''

slides = []
slides.append(f'''<section class="slide" id="s1">{TOP.format(n=1)}
<div style="margin-top:110px; display:grid; gap:34px"><p class="cap">21세기 골드러시의 영수증 · 왜 생기나</p>
<h1>AI는 왜<br>끝난 일을 다시 읽을까</h1>
<p class="lead">1편에서 잰 비효율이 어디서 오는지 찾고,<br>사람의 뇌와 무엇이 다른지 비교한 뒤,<br>뇌 기전 아홉 가지를 규칙으로 바꿔 기록 위에서 재연했습니다.</p></div>
<div class="toc" style="margin-top:80px"><div><b>그림 1</b>입력 = 걸음 × 평균 맥락</div><div><b>그림 2</b>뇌와 어디가 다른가</div><div><b>그림 3</b>뇌 기전 아홉 가지를 재연하면</div><div><b>그림 4</b>남은 규칙 하나: 역치</div></div>
<p class="src">뇌 비유는 규칙을 떠올리는 데 쓴 영감(inspired by)이며 뇌에 대한 주장이 아닙니다. 판정은 결과를 보기 전에 등록한 기준으로 했습니다(research/protocol/minimal-rules-v1.md, v2.md). · {SRC}</p></section>''')

slides.append(f'''<section class="slide" id="s2">{TOP.format(n=2)}
<div><p class="cap">그림 1</p><h2>입력 = 걸음 × 평균 맥락</h2></div>
<div class="panel"><p class="k">A. 맥락 크기의 톱니 <span>· 압축 상한까지 차올랐다 떨어짐 (모양은 모식, 높이는 측정값)</span></p>{sawchart(False)}
<p class="sub2">AI는 한 걸음 내딛을 때마다 지금까지의 맥락 전체를 처음부터 다시 읽습니다. 톱니 아래 넓이가 처리한 입력입니다. 지시마다 처리량이 다른 이유의 87%는 걸음 수로 설명됩니다.</p></div>
<div class="panel"><p class="k">B. 돈은 어디로 갔나 <span>· 목록가 비율, 근사</span></p>
<svg width="{W}" height="60" viewBox="0 0 {W} 60"><rect x="0" y="0" width="{W*.53-3:.0f}" height="60" fill="{HOT}"/><rect x="{W*.53:.0f}" y="0" width="{W*.19-3:.0f}" height="60" fill="{HOT}" opacity=".45"/><rect x="{W*.72:.0f}" y="0" width="{W*.16-3:.0f}" height="60" fill="{FIX}" opacity=".7"/><rect x="{W*.88:.0f}" y="0" width="{W*.12:.0f}" height="60" fill="#a9a7a1"/>
<text x="20" y="40" font-size="26" font-weight="850" fill="#fff">52~54%</text></svg>
<div class="legend"><span><i style="background:{HOT}"></i>끝난 지시의 맥락 다시 읽기</span><span><i style="background:{HOT};opacity:.45"></i>그 밖의 캐시 읽기</span><span><i style="background:{FIX};opacity:.7"></i>캐시 쓰기 16%</span><span><i style="background:#a9a7a1"></i>출력 9~12%</span></div></div>
<div class="panel"><p class="k">C. 한 걸음의 구조 <span>· 모식</span></p><svg width="936" height="172" viewBox="0 0 936 172" role="img" aria-label="지시, 걸음, 맥락 재독의 고리">
<defs><marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#0b0b0b"/></marker><marker id="mh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#eb6834"/></marker></defs>
<g font-size="20" font-weight="800" fill="#0b0b0b">
<rect x="0" y="60" width="170" height="70" rx="8" fill="none" stroke="#0b0b0b" stroke-width="2"/><text x="85" y="102" text-anchor="middle">지시</text>
<rect x="250" y="60" width="200" height="70" rx="8" fill="none" stroke="#0b0b0b" stroke-width="2"/><text x="350" y="102" text-anchor="middle">한 걸음 (호출)</text>
<rect x="530" y="60" width="406" height="70" rx="8" fill="none" stroke="#eb6834" stroke-width="3"/><text x="733" y="102" text-anchor="middle" fill="#eb6834">맥락 전체를 처음부터 다시 읽기</text>
<line x1="170" y1="95" x2="246" y2="95" stroke="#0b0b0b" stroke-width="2.4" marker-end="url(#m)"/>
<line x1="450" y1="95" x2="526" y2="95" stroke="#0b0b0b" stroke-width="2.4" marker-end="url(#m)"/>
<path d="M733 60 C733 8 350 8 350 56" fill="none" stroke="#eb6834" stroke-width="3" marker-end="url(#mh)"/>
<text x="936" y="164" text-anchor="end" font-size="18" fill="#eb6834">↺ 다음 걸음마다 반복 · 결과와 생각이 맥락에 덧붙음</text></g></svg></div>
<p class="note">다시 안 쓰일 내용만 버렸다면 줄었을 입력은 약 6~13%. 버리지 못한 게 아니라, <b>전부를 늘 들고 다닌 것</b>이 문제였습니다.</p>
<p class="src">{SRC}</p></section>''')

slides.append(f'''<section class="slide" id="s3">{TOP.format(n=3)}
<div><p class="cap">그림 2</p><h2>뇌와 어디가 다른가</h2></div>
{BRAIN_VS}
<table><tr><th></th><th>뇌 (교과서 수준의 사실)</th><th>AI 에이전트 (측정)</th></tr>
<tr><td class="c">작업 공간</td><td>몇 덩이 (Cowan 2001)</td><td>최대 78.3만 토큰, 평균 약 42만</td></tr>
<tr><td class="c">배운 것이 남는 곳</td><td>시냅스, 잠잘 때 응고 (Diekelmann &amp; Born 2010)</td><td>맥락뿐. 압축 뒤 1만~2만을 다시 가져감</td></tr>
<tr><td class="c">꺼내 오기</td><td>단서로 인출, 쌈 (Teyler &amp; DiScenna 1986)</td><td>한 번 꺼낼 때마다 맥락 전체를 다시 읽음</td></tr></table>
<p class="note" style="font-size:22px">뇌는 작업기억을 작게 두고 경험은 시냅스에 새깁니다. 지금의 AI는 작업 중에 새길 곳이 없어서 배운 것을 전부 맥락에 들고 다니고, 그 수첩을 매 걸음 처음부터 읽습니다. 그렇다면 흉내 낼 수 있는 뇌의 방식은 <b>작업기억을 작게 두는 것</b>입니다. 그림 3이 그것을 확인합니다.</p>
<p class="src">모식도는 비유이며 해부학적 묘사가 아닙니다. · {SRC}</p></section>''')

G = [("곱셈 자리 · 모든 걸음에 곱해지는 맥락 크기", [("R3 역치 관문", "뉴런 발화 문턱", 72.85, "72.9%"), ("R4 사건 경계의 응고", "사건 단위 기억", 52.05, "52.1%"), ("R5 휴식 중 응고", "부교감·수면", 15.70, "15.7%")], BR),
     ("덧셈 자리 · 드문 걸음 몇 개", [("R1 반사", "무조건반사", 0.92, "0.9%"), ("R9 모드 전환", "신경조절물질", 0.86, "0.9%"), ("R2 습관화", "습관화", 0.26, "0.3%"), ("R8 반사궁", "척수 반사", 0.04, "0.04%")], INK2),
     ("싼 인출을 전제 · R3 위에 더하면", [("R6 헵 강화", "자주 쓰면 강해짐", None, "−2.8%p (손해)"), ("R7 해마 색인", "단서로 불러오기", None, "입력 ×224 (파멸)")], HOT)]
slides.append(f'''<section class="slide" id="s4">{TOP.format(n=4)}
<div><p class="cap">그림 3</p><h2>뇌 기전 아홉 가지를 재연하면</h2></div>
<p class="sub2" style="font-size:20px">규칙 하나씩, 입력 절약(단독). 재시작 시동, 다시 읽기, 불러오기 걸음은 모두 비용으로 물렸습니다. 입력 2%p·비용 1%p 이상 보태는 규칙만 남깁니다.</p>
{bars(G)}
<p class="note">R4·R5는 R3이 있으면 보탬이 0입니다(15만 상한이면 경계 규칙이 할 일이 없음). 남는 규칙은 <b>하나</b>입니다. 세션을 반으로 나눠 골라도 같았습니다.</p>
<p class="src">{SRC}</p></section>''')

slides.append(f'''<section class="slide" id="s5">{TOP.format(n=5)}
<div><p class="cap">그림 4</p><h2>남은 규칙 하나: 역치</h2></div>
<div class="panel"><p class="k">A. 뉴런 <span>· 문턱을 넘으면 발화하고 리셋 (모식)</span></p>{neuron_trace()}</div>
<div class="panel"><p class="k">B. 맥락 <span>· 15만을 넘으려 하면 압축하고 리셋</span></p>{sawchart(True)}</div>
<div class="kpi"><div class="hot"><b>−72.9%</b><span>입력 (기록상)</span></div><div class="hot"><b>−64.7%</b><span>비용 (기록상)</span></div><div><b>+3.4%</b><span>추가 호출</span></div></div>
<table><tr><th>결과 전에 적은 예측</th><th class="r">결과</th><th class="r">판정</th></tr>
<tr><td>남는 규칙은 경계 규칙 몇 개</td><td class="r">역치 하나</td><td class="r ng">틀림</td></tr>
<tr><td>반사궁 단독 1~5%</td><td class="r">0.04%</td><td class="r ng">틀림</td></tr>
<tr><td>헵 강화·색인은 보탬이 없음</td><td class="r">손해</td><td class="r ok">맞음</td></tr></table>
<p class="src">아직 모르는 것: 품질. 압축이 34번에서 323번으로 늘어도 일이 잘 되는지는 기록으로 알 수 없어, 3단계에서 테스트가 붙은 실제 작업으로 확인합니다. · {SRC}</p></section>''')

html = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Note 2 v4</title>' + CSS + "</head><body>" + "\n".join(slides) + "</body></html>"
open(H + "note02v4-slides.html", "w").write(html)
print("ok", len(html))
