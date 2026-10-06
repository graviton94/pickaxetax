"""Render a survey dataset as one self-contained HTML report.

Deterministic: the output depends only on the dataset (no clock, no randomness),
so `pxt survey report dataset.json` reproduces the same page byte for byte.
Charts are inline SVG drawn to one scale each; colors come from theme tokens.
"""

from __future__ import annotations

import html
import json

from .. import __version__
from .dataset import derive, digest, input_of

W = 720  # SVG drawing width (scales down with the page)


def eok(x: float) -> str:
    """Korean large-number style: 억 above 1e8, 만 above 1e4."""
    if x >= 1e8:
        return f"{x / 1e8:.2f}억"
    if x >= 1e4:
        return f"{x / 1e4:,.0f}만"
    return f"{x:,.0f}"


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- charts

def chart_decomposition(dv: dict, order: list[str]) -> str:
    rows = [("전체", dv["decomposition"])] + [(sid, dv["decomposition_by_session"][sid]) for sid in order
                                              if sid in dv["decomposition_by_session"]]
    lab_w, bar_x, bar_w, row_h, gap = 64, 72, W - 72 - 8, 30, 12
    h = len(rows) * (row_h + gap) + 8
    parts = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="컨텍스트 분해">']
    keys = [("fixed", "var(--s3)", "고정분"), ("carried", "var(--s1)", "이전 지시에서 넘어온 것"), ("current", "var(--s2)", "이번 지시에서 생긴 것")]
    for i, (name, d) in enumerate(rows):
        y = i * (row_h + gap) + 4
        tot = sum(d.values()) or 1
        weight = "700" if name == "전체" else "500"
        parts.append(f'<text x="0" y="{y + row_h / 2 + 5}" class="lab" font-weight="{weight}">{esc(name)}</text>')
        x = bar_x
        for k, color, label in keys:
            w = bar_w * d[k] / tot
            if w <= 0:
                continue
            seg = max(0.0, w - 2)  # 2px surface gap between segments
            share = d[k] / tot
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{seg:.1f}" height="{row_h}" rx="3" fill="{color}" '
                         f'data-tip="{esc(name)} · {label} {pct(share)} ({eok(d[k])} 토큰)"><title>{label} {pct(share)}</title></rect>')
            if seg > 46:
                parts.append(f'<text x="{x + 8:.1f}" y="{y + row_h / 2 + 5}" class="inbar">{pct(share, 0)}</text>')
            x += w
    parts.append("</svg>")
    return "".join(parts)


def chart_measured_vs_listed(ds: dict, order: list[str]) -> str:
    ss = {s["id"]: s for s in ds["sessions"]}
    vals = [(sid, input_of(ss[sid]), (ss[sid].get("session_list") or {}).get("input")) for sid in order]
    vmax = max(max(v for _, v, _ in vals), max(l or 0 for _, _, l in vals))
    lab_w, bar_x, row_h, gap = 64, 72, 22, 14
    bar_w = W - bar_x - 170
    h = len(vals) * (row_h + gap) + 30
    parts = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="세션별 실측 입력과 세션 목록 표시값">']
    for i, (sid, v, l) in enumerate(vals):
        y = i * (row_h + gap) + 6
        part = " (부분)" if ss[sid].get("partial") else ""
        parts.append(f'<text x="0" y="{y + row_h / 2 + 5}" class="lab">{esc(sid)}</text>')
        w = max(2, bar_w * v / vmax)
        ratio = f" · 표시값의 {v / l:.1f}배" if l else ""
        parts.append(f'<rect x="{bar_x}" y="{y}" width="{w:.1f}" height="{row_h}" rx="3" fill="var(--s1)" '
                     f'data-tip="{esc(sid)}{part} 실측 {eok(v)}{ratio}"><title>{eok(v)}</title></rect>')
        if l:
            lx = bar_x + bar_w * l / vmax
            parts.append(f'<rect x="{lx - 1.5:.1f}" y="{y - 4}" width="3" height="{row_h + 8}" fill="var(--ink)" '
                         f'data-tip="{esc(sid)} 세션 목록 표시값 {eok(l)}"><title>표시값 {eok(l)}</title></rect>')
        parts.append(f'<text x="{bar_x + max(w, bar_w * (l or 0) / vmax) + 10:.1f}" y="{y + row_h / 2 + 5}" class="val">'
                     f'{eok(v)}{part}{f" · {v / l:.1f}배" if l else ""}</text>')
    yl = len(vals) * (row_h + gap) + 14
    parts.append(f'<rect x="{bar_x}" y="{yl - 9}" width="14" height="10" rx="2" fill="var(--s1)"/>'
                 f'<text x="{bar_x + 20}" y="{yl}" class="lab">실측 (호출별 기록의 합)</text>'
                 f'<rect x="{bar_x + 200}" y="{yl - 12}" width="3" height="14" fill="var(--ink)"/>'
                 f'<text x="{bar_x + 210}" y="{yl}" class="lab">세션 목록 표시값</text>')
    parts.append("</svg>")
    return "".join(parts)


def chart_sawtooth(ctx: list[int], sid: str) -> str:
    h, l, r, t, b = 280, 52, 12, 14, 30
    pw, ph = W - l - r, h - t - b
    ymax = 800_000
    n = len(ctx)
    step = max(1, n // 900)
    pts = [(i, ctx[i]) for i in range(0, n, step)]
    sx = lambda i: l + pw * i / max(1, n - 1)
    sy = lambda v: t + ph * (1 - min(v, ymax) / ymax)
    parts = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="{esc(sid)} 호출별 컨텍스트 크기" class="line" data-n="{n}">']
    for v in range(0, ymax + 1, 200_000):
        y = sy(v)
        parts.append(f'<line x1="{l}" x2="{W - r}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                     f'<text x="{l - 8}" y="{y + 4:.1f}" class="tick" text-anchor="end">{eok(v) if v else "0"}</text>')
    for k in range(0, n, 500):
        parts.append(f'<text x="{sx(k):.1f}" y="{h - 8}" class="tick" text-anchor="middle">{k:,}</text>')
    yc = sy(780_000)
    parts.append(f'<line x1="{l}" x2="{W - r}" y1="{yc:.1f}" y2="{yc:.1f}" class="ceiling"/>'
                 f'<text x="{W - r}" y="{yc - 6:.1f}" class="tick" text-anchor="end">압축이 일어나는 천장 ≈ 78만</text>')
    d = " ".join(f"{'M' if j == 0 else 'L'}{sx(i):.1f},{sy(v):.1f}" for j, (i, v) in enumerate(pts))
    parts.append(f'<path d="{d}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>')
    parts.append(f'<line class="xhair" x1="0" x2="0" y1="{t}" y2="{t + ph}" hidden/>')
    parts.append("</svg>")
    return "".join(parts)


def chart_concentration(cum: list[float], shares: dict) -> str:
    h, l, r, t, b = 300, 44, 16, 14, 34
    pw, ph = W - l - r, h - t - b
    n = len(cum)
    sx = lambda f: l + pw * f
    sy = lambda f: t + ph * (1 - f)
    parts = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="지시 단위 누적 입력 비중">']
    for f in (0, .25, .5, .75, 1):
        parts.append(f'<line x1="{l}" x2="{W - r}" y1="{sy(f):.1f}" y2="{sy(f):.1f}" class="grid"/>'
                     f'<text x="{l - 8}" y="{sy(f) + 4:.1f}" class="tick" text-anchor="end">{int(f * 100)}%</text>'
                     f'<text x="{sx(f):.1f}" y="{h - 12}" class="tick" text-anchor="middle">{int(f * 100)}%</text>')
    parts.append(f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(1)}" y2="{sy(1)}" class="ref"/>')
    pts = [(0.0, 0.0)] + [((i + 1) / n, c) for i, c in enumerate(cum)]
    d = " ".join(f"{'M' if j == 0 else 'L'}{sx(x):.1f},{sy(y):.1f}" for j, (x, y) in enumerate(pts))
    parts.append(f'<path d="{d}" fill="none" stroke="var(--s1)" stroke-width="2"/>')
    for f in (0.10, 0.20):
        k = max(1, round(f * n))
        x, y = k / n, cum[k - 1]
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2" '
                     f'data-tip="상위 {int(f * 100)}% 지시({k}번)가 입력의 {pct(y)}"><title>{pct(y)}</title></circle>'
                     f'<text x="{sx(x) + 10:.1f}" y="{sy(y) + 16:.1f}" class="val">상위 {int(f * 100)}% → {pct(y)}</text>')
    parts.append(f'<text x="{sx(0.62):.1f}" y="{sy(0.55):.1f}" class="tick">고르게 썼다면 이 대각선</text>')
    parts.append("</svg>")
    return "".join(parts)


def chart_steps(ds: dict, order: list[str]) -> str:
    ss = {s["id"]: s for s in ds["sessions"]}
    pts = []
    for sid in order:
        m = ss[sid]["measurement"]
        ser = m.get("series")
        if not ser or not m["user_instructions"]:
            continue
        mean_ctx = sum(ser["context"]) / len(ser["context"])
        pts.append((sid, m["api_calls"] / m["user_instructions"], mean_ctx, input_of(ss[sid])))
    h, l, r, t, b = 300, 52, 20, 16, 36
    pw, ph = W - l - r, h - t - b
    xmax, ymax = 45, 500_000
    imax = max(p[3] for p in pts)
    sx = lambda v: l + pw * v / xmax
    sy = lambda v: t + ph * (1 - v / ymax)
    parts = [f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="지시당 걸음 수와 걸음당 컨텍스트">']
    for v in range(0, ymax + 1, 100_000):
        parts.append(f'<line x1="{l}" x2="{W - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" class="grid"/>'
                     f'<text x="{l - 8}" y="{sy(v) + 4:.1f}" class="tick" text-anchor="end">{eok(v) if v else "0"}</text>')
    for v in range(0, xmax + 1, 10):
        parts.append(f'<text x="{sx(v):.1f}" y="{h - 16}" class="tick" text-anchor="middle">{v}</text>')
    parts.append(f'<text x="{l + pw / 2}" y="{h - 2}" class="tick" text-anchor="middle">지시당 호출 수 (평균)</text>')
    labels = []
    for sid, x, y, inp in sorted(pts, key=lambda p: -p[3]):
        rad = 6 + 22 * (inp / imax) ** 0.5
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{rad:.1f}" fill="var(--s1)" fill-opacity="0.35" '
                     f'stroke="var(--s1)" stroke-width="2" data-tip="{esc(sid)} · 지시당 {x:.1f}걸음 · 걸음당 {eok(y)} · 입력 {eok(inp)}">'
                     f'<title>{esc(sid)}</title></circle>')
        labels.append([sx(x) + rad + 4, sy(y) + 4, sid, sx(x), sy(y)])
    # nudge labels apart vertically so close sessions stay readable; draw a leader when a label moved
    labels.sort(key=lambda a: (round(a[0] / 60), a[1]))
    placed = []
    for lab in labels:
        for q in placed:
            if abs(q[0] - lab[0]) < 46 and abs(q[1] - lab[1]) < 15:
                lab[1] = q[1] + 15
        placed.append(lab)
    for lx, ly, sid, cx, cy in placed:
        if abs(ly - (cy + 4)) > 1:
            parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{lx - 2:.1f}" y2="{ly - 4:.1f}" class="grid"/>')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="lab">{esc(sid)}</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------- page

CSS = """
/* Layout: a receipt (영수증) header with the amount due, then one figure per finding, then method and data. */
:root {
  --bg: #f4f6f8; --surface: #ffffff; --ink: #121519; --ink-2: #464d59; --muted: #737c8a; --rule: #d9dee5;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a;
  --font-body: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif;
  --font-num: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #111317; --surface: #1a1c21; --ink: #f1f3f6; --ink-2: #c2c7d0; --muted: #8c94a1; --rule: #2d3139;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #111317; --surface: #1a1c21; --ink: #f1f3f6; --ink-2: #c2c7d0; --muted: #8c94a1; --rule: #2d3139;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.65; }
.wrap { max-width: 860px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 64px; display: grid; gap: 28px; }
h1, h2, h3 { text-wrap: balance; line-height: 1.3; margin: 0; }
h1 { font-size: 1.55rem; font-weight: 700; }
h2 { font-size: 1.15rem; font-weight: 700; }
p { margin: 0; max-width: 68ch; }
.num, .tick, .val, td.n, .field dd { font-family: var(--font-num); font-variant-numeric: tabular-nums; }
.bill { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 20px; display: grid; gap: 18px; }
.bill-top { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 16px; align-items: baseline; }
.eyebrow { font-size: .78rem; letter-spacing: .08em; color: var(--muted); text-transform: uppercase; }
.fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px 20px; margin: 0; }
.field { margin: 0; min-width: 0; }
.field dt { font-size: .78rem; color: var(--muted); }
.field dd { margin: 0; font-size: .86rem; color: var(--ink-2); overflow-wrap: anywhere; }
.amount { border-top: 1px dashed var(--rule); padding-top: 14px; display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: baseline; }
.amount .big { font-family: var(--font-num); font-size: clamp(2rem, 7vw, 2.9rem); font-weight: 600; letter-spacing: -.02em; }
.amount .note { color: var(--ink-2); font-size: .92rem; }
.tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px 12px; }
@media (max-width: 520px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.tile { border-left: 2px solid var(--rule); padding: 2px 0 2px 12px; min-width: 0; }
.tile b { display: block; font-family: var(--font-num); font-size: 1.35rem; font-weight: 600; }
.tile span { color: var(--ink-2); font-size: .86rem; }
section.fig { display: grid; gap: 10px; }
section.fig .lead { color: var(--ink-2); }
.figbox { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px; overflow-x: auto; }
svg { width: 100%; height: auto; display: block; overflow: visible; }
svg .lab { fill: var(--ink-2); font-size: 13px; font-family: var(--font-body); }
svg .tick { fill: var(--muted); font-size: 11.5px; }
svg .val { fill: var(--ink); font-size: 12.5px; }
svg .inbar { fill: #ffffff; font-size: 12px; font-family: var(--font-num); font-weight: 600; pointer-events: none; }
svg .grid { stroke: var(--rule); stroke-width: 1; }
svg .ref { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 4 4; }
svg .ceiling { stroke: var(--s2); stroke-width: 1.5; stroke-dasharray: 6 4; }
svg .xhair { stroke: var(--muted); stroke-width: 1; }
svg [data-tip] { cursor: pointer; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .86rem; color: var(--ink-2); }
.legend i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.insight { display: grid; gap: 6px; padding-left: 14px; border-left: 2px solid var(--s1); }
.tablebox { overflow-x: auto; background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; }
table { border-collapse: collapse; width: 100%; font-size: .84rem; }
th, td { padding: 8px 10px; border-bottom: 1px solid var(--rule); text-align: left; white-space: nowrap; }
th { color: var(--muted); font-weight: 500; }
td.n { text-align: right; }
code, pre { font-family: var(--font-num); font-size: .82rem; }
pre { background: var(--surface); border: 1px solid var(--rule); border-radius: 8px; padding: 12px; overflow-x: auto; margin: 0; }
ul { margin: 0; padding-left: 20px; display: grid; gap: 4px; }
.small { color: var(--muted); font-size: .82rem; }
#tip { position: fixed; z-index: 10; pointer-events: none; background: var(--ink); color: var(--bg); font-size: .8rem;
  padding: 6px 9px; border-radius: 6px; max-width: 280px; font-family: var(--font-body); }
@media (prefers-reduced-motion: no-preference) { svg [data-tip] { transition: opacity .15s; } }
"""

JS = """
(function () {
  var tip = document.getElementById('tip');
  function show(text, x, y) { tip.textContent = text; tip.hidden = false;
    var r = tip.getBoundingClientRect();
    tip.style.left = Math.max(8, Math.min(window.innerWidth - r.width - 8, x + 12)) + 'px';
    tip.style.top = Math.max(8, y - r.height - 12) + 'px'; }
  function hide() { tip.hidden = true; }
  document.addEventListener('pointerover', function (e) {
    var el = e.target.closest && e.target.closest('[data-tip]');
    if (el) show(el.getAttribute('data-tip'), e.clientX, e.clientY);
  });
  document.addEventListener('pointerout', function (e) {
    if (e.target.closest && e.target.closest('[data-tip]')) hide();
  });
  var series = window.SAWTOOTH || [];
  document.querySelectorAll('svg.line').forEach(function (svg) {
    var hair = svg.querySelector('.xhair'), n = series.length;
    if (!n) return;
    svg.addEventListener('pointermove', function (e) {
      var r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      var x = (e.clientX - r.left) * vb.width / r.width, l = 52, pw = vb.width - 52 - 12;
      var i = Math.round((x - l) / pw * (n - 1));
      if (i < 0 || i >= n) { hair.setAttribute('hidden', ''); hide(); return; }
      var xx = l + pw * i / (n - 1);
      hair.setAttribute('x1', xx); hair.setAttribute('x2', xx); hair.removeAttribute('hidden');
      show('호출 #' + (i + 1).toLocaleString() + ' · 컨텍스트 ' + Math.round(series[i] / 10000).toLocaleString() + '만 토큰', e.clientX, e.clientY);
    });
    svg.addEventListener('pointerleave', function () { hair.setAttribute('hidden', ''); hide(); });
  });
})();
"""


def render(ds: dict, sawtooth_session: str | None = None) -> str:
    dv = derive(ds)
    ss = {s["id"]: s for s in ds["sessions"]}
    sub = ds["subject"]
    order = dv["ranked"]
    dec = dv["decomposition"]
    dtot = sum(dec.values()) or 1
    saw_id = sawtooth_session or max((s for s in ds["sessions"] if (s["measurement"].get("series") and not s.get("partial"))),
                                     key=lambda s: len(s["measurement"]["series"]["context"]))["id"]
    saw = ss[saw_id]["measurement"]["series"]["context"]
    ts = dv["top_shares"]
    orr = dv["output_ratio_range"]
    partial = ", ".join(dv["partial"]) or "없음"
    h = []
    h.append(f"<title>21세기 골드러시의 영수증 {esc(sub['label'])}</title>")
    h.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+KR:wght@400;500;700&display=swap">')
    h.append(f"<style>{CSS}</style>")
    h.append('<div class="wrap">')
    # bill
    h.append('<header class="bill"><div class="bill-top"><div><div class="eyebrow">#AntiTokenMaxing · 현상조사</div>'
             f'<h1>21세기 골드러시의 영수증 · {esc(sub["label"])}</h1></div><div class="small">{esc(sub["scope"])}</div></div>')
    fields = [("조사 대상", sub["who"]), ("조사 기간", sub["period"]), ("측정 원천", sub["sources"]),
              ("세션", f'{len(ds["sessions"])}개 (부분 측정: {partial})'), ("데이터셋 SHA-256", digest(ds)[:16] + "…"), ("생성 도구", f"pickaxetax {__version__} · pxt survey report")]
    h.append('<dl class="fields">' + "".join(f'<div class="field"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in fields) + "</dl>")
    listed = (f'세션 목록에 표시된 합계 {eok(dv["listed_input"])}의 {dv["total_input"] / dv["listed_input"]:.2f}배.'
              if dv["listed_input"] else "")
    h.append(f'<div class="amount"><span class="big">{eok(dv["total_input"])}</span><span class="note">토큰을 처리했습니다 (입력'
             f'{", 하한" if dv["partial"] else ""}). {listed}</span></div></header>')
    # tiles
    tiles = [(f'{dv["instructions"]:,}', "대표의 지시"), (eok(dv["per_instruction_mean"]), "지시 1건당 평균 입력"),
             (pct(dec["carried"] / dtot), "이전 지시에서 넘어온 컨텍스트"), (pct(ts[0.10]), "상위 10% 지시가 쓴 입력"),
             (f'{dv["calls"]:,}', "API 호출"), (f'{dv["active_hours"]:.0f}시간', "실제 작업 시간")]
    h.append('<div class="tiles">' + "".join(f'<div class="tile"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in tiles) + "</div>")
    # finding 1
    h.append('<section class="fig"><h2>연산의 4분의 3은 이미 끝난 지시를 다시 읽는 데 쓰였습니다</h2>'
             f'<p class="lead">매 호출의 컨텍스트를 세 부분으로 나눴습니다. 고정분(시스템 프롬프트와 도구)은 {pct(dec["fixed"] / dtot)}, '
             f'이번 지시가 시작될 때 이미 쌓여 있던 것은 {pct(dec["carried"] / dtot)}, 이번 지시 동안 새로 생긴 것은 {pct(dec["current"] / dtot)}입니다. '
             '필요했는지는 판단하지 않았습니다. 구조만 보여 줍니다.</p>'
             '<div class="legend"><span><i style="background:var(--s3)"></i>고정분</span><span><i style="background:var(--s1)"></i>이전 지시에서 넘어온 것</span>'
             '<span><i style="background:var(--s2)"></i>이번 지시에서 생긴 것</span></div>'
             f'<div class="figbox">{chart_decomposition(dv, order)}</div>'
             '<p class="small">호출별 기록이 있는 세션만 분해했습니다.'
             + (' 부분 측정 세션은 받은 구간의 첫 호출이 세션 중간이어서, 고정분을 새 세션의 일반적인 첫 호출 크기(5만)로 두었습니다.' if dv["partial"] else '')
             + '</p></section>')
    # finding 2
    h.append('<section class="fig"><h2>세션은 늘 천장 근처에서 돕니다</h2>'
             f'<p class="lead">{esc(saw_id)}의 호출 {len(saw):,}번의 컨텍스트 크기입니다. 컨텍스트는 약 78만 토큰에 닿을 때만 압축되고, 다시 차오르기를 반복합니다. '
             '잊는 시점을 정하는 것은 작업의 끝이 아니라 용량입니다.</p>'
             f'<div class="figbox">{chart_sawtooth(saw, saw_id)}</div>'
             '<p class="small">가로축은 호출 순서, 세로축은 그 호출이 처리한 입력 토큰입니다.</p></section>')
    # finding 3
    h.append('<section class="fig"><h2>지시 하나의 비용은 걸음 수 × 걸음마다 지는 짐입니다</h2>'
             '<p class="lead">원 하나가 세션 하나입니다. 오른쪽일수록 지시 하나에 에이전트가 많은 걸음을 밟았고, 위쪽일수록 걸음마다 무거운 컨텍스트를 들고 갔습니다. 원의 넓이는 세션의 총입력입니다.</p>'
             f'<div class="figbox">{chart_steps(ds, order)}</div></section>')
    # finding 4
    n_i = len(dv["instruction_inputs"])
    if n_i:
        h.append('<section class="fig"><h2>비용은 소수의 지시에 몰립니다</h2>'
             f'<p class="lead">지시별로 나눠 볼 수 있었던 {n_i}번을 입력이 큰 순서로 늘어놓고 누적했습니다. 상위 1%가 {pct(ts[0.01])}, 상위 10%가 {pct(ts[0.10])}, '
             f'상위 20%가 {pct(ts[0.20])}를 썼습니다. 가장 큰 지시 하나는 {eok(dv["instruction_inputs"][0])} 토큰이었습니다.</p>'
                 f'<div class="figbox">{chart_concentration(dv["instruction_cum"], ts)}</div>'
                 '<p class="small">가로축은 상위 몇 %의 지시인지, 세로축은 그 지시들이 쓴 입력의 비중입니다.</p></section>')
    # finding 5
    if dv["listed_input"]:
        h.append('<section class="fig"><h2>표시되는 사용량은 실제보다 작습니다</h2>'
             '<p class="lead">세션 목록에 표시된 값과, 호출마다 기록된 입력을 더한 값을 비교했습니다. 오래된 세션일수록 차이가 컸습니다.</p>'
                 f'<div class="figbox">{chart_measured_vs_listed(ds, order)}</div></section>')
    # insights
    out_txt = f"{pct(orr[0])}~{pct(orr[1])}" if orr else "기록 없음"
    insights = [
        ("과거가 현재보다 무겁습니다", f"며칠씩 이어 쓴 세션 5개가 입력의 {pct(dv['top5_sessions_share'])}를 차지했고, 그 안에서 매 호출이 지고 간 짐의 {pct(dec['carried'] / dtot)}는 이미 끝난 지시들의 내용이었습니다."),
        ("에이전트는 아주 작은 걸음으로 일합니다", f"도구 호출의 대부분은 셸 명령입니다. 출력은 입력의 {out_txt}입니다(호출마다 최종 출력이 기록된 세션 기준). 걸음 수를 줄이는 것은 짐을 줄이는 것만큼 큰 레버입니다."),
        ("가격 신호가 꺼져 있습니다", "다시 읽기의 대부분은 캐시로 싸게 청구되고, 표시되는 사용량은 실제보다 작습니다. 줄일 이유가 보이지 않는 구조입니다."),
        ("다음 질문", "지시 경계에서 넘겨주는 컨텍스트를 얼마나 줄여도 결과가 같은가. 실제 지시를 짐을 줄인 조건에서 다시 실행해 입력과 결과물을 비교하는 것이 다음 실험입니다."),
    ]
    h.append('<section class="fig"><h2>그래서 알게 된 것</h2>' + "".join(f'<div class="insight"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in insights) + "</section>")
    # table
    cols = ["세션", "작업 종류", "모델", "원천", "API 호출", "지시", "입력", "표시값", "압축", "컨텍스트 최대", "지시당 입력 중앙값", "작업 시간"]
    rows = []
    for sid in order:
        s = ss[sid]
        m = s["measurement"]
        pi = m["per_instruction"]
        med = pi["input_quartiles"][1] if len(pi.get("input_quartiles") or []) == 3 else (pi.get("input_quartiles") or [0])[0]
        lst = (s.get("session_list") or {}).get("input")
        rows.append([sid + (" (부분)" if s.get("partial") else ""), s.get("type", ""), s.get("model", ""),
                     {"events_api": "이벤트 기록", "local": "세션 안 기록"}.get(s["source"], s["source"]),
                     f'{m["api_calls"] + (m.get("subagents") or {}).get("api_calls", 0):,}', f'{m["user_instructions"]:,}',
                     eok(input_of(s)), eok(lst) if lst else "-", str(m["compactions"]), f'{m["context"]["peak"]:,}', eok(med), f'{m["active_hours"]}시간'])
    num = {4, 5, 6, 7, 8, 9, 10, 11}
    h.append('<section class="fig"><h2>세션별 수치</h2><div class="tablebox"><table><thead><tr>' + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>"
             + "".join("<tr>" + "".join(f'<td class="{"n" if i in num else ""}">{esc(v)}</td>' for i, v in enumerate(r)) + "</tr>" for r in rows)
             + "</tbody></table></div></section>")
    # method
    h.append('<section class="fig"><h2>측정 방법과 한계</h2><ul>'
             '<li>원천은 제공사가 API 호출마다 기록한 사용량(입력, 캐시 읽기, 캐시 쓰기)입니다. 추정이나 판정은 쓰지 않았습니다.</li>'
             '<li>"지시"는 사용자가 직접 입력한 메시지입니다. 도구 결과, 시스템 알림, 압축 요약은 세지 않았습니다.</li>'
             '<li>이벤트 기록의 출력 토큰은 응답이 시작될 때의 값이라 쓰지 않았습니다. 출력 비율은 세션 안 기록이 있는 세션에서만 계산했습니다.</li>'
             + (f'<li>부분 측정 세션({esc(partial)})은 받은 구간만 들어 있어서 합계는 하한입니다.</li>' if dv["partial"] else '')
             + '<li>표본은 한 사람입니다. 이 사람의 사용 방식을 기술할 뿐, 사람들 일반에 대한 주장이 아닙니다.</li>'
             '<li>컨텍스트 분해는 구조를 보여 줄 뿐, 넘어온 내용이 필요했는지는 판단하지 않습니다.</li>'
             + "".join(f'<li>{esc(n)}</li>' for n in sub.get("notes", [])) + '</ul></section>')
    h.append('<section class="fig"><h2>재현</h2><p>같은 데이터셋이면 같은 레포트가 나옵니다(시계나 난수를 쓰지 않습니다).</p>'
             f'<pre>pip install pickaxetax\npxt survey report {esc(sub.get("dataset_path", "dataset.json"))} --out report.html\n# 데이터셋 SHA-256: {digest(ds)}</pre>'
             '<p class="small">자기 세션을 재려면: <code>pxt survey measure ~/.claude/projects</code>로 데이터셋을 만든 뒤 같은 명령으로 레포트를 만듭니다. 텍스트, 경로, ID는 데이터셋에 들어가지 않습니다.</p></section>')
    h.append('</div><div id="tip" hidden></div>')
    h.append(f"<script>window.SAWTOOTH={json.dumps(saw, separators=(',', ':'))};</script>")
    h.append(f"<script>{JS}</script>")
    return "\n".join(h)
