"use strict";

// ---------- i18n ----------
const T = {
  ko: {
    nav_analyze: "분석", nav_explore: "공익 그래프",
    hero_title: "AI는 같은 대화를 매번 처음부터 다시 읽습니다.",
    hero_lede: "대화 공유 링크나 내보내기 파일을 올리면 원문은 버리고 구조(아젠다·흐름·깊이)만 그래프로 남겨, 그 대화에서 불필요했던 연산이 얼마인지 보여줍니다.",
    c_convs: "개 대화 분석", c_units: "연산 단위 측정", c_avoid: "회피 가능했던 연산",
    input_label: "공유 링크, JSON 내보내기, 또는 대화 텍스트",
    input_ph: "https://chatgpt.com/share/…  ·  https://claude.ai/share/…\n또는 ChatGPT/Claude 내보내기 JSON\n또는\nUser: …\nAssistant: …",
    file_btn: "파일 선택", consent: "익명 구조를 공익 그래프에 기여 (원문 미저장, 언제든 삭제 가능)",
    sample: "예시로 해보기", analyze: "분석하기", analyzing: "분석 중…",
    explore_title: "공익 그래프",
    explore_lede: "기여된 대화 구조의 집계입니다. 개인 식별을 막기 위해 k개 이상의 대화에서 등장한 주제만 공개합니다.",
    topic_graph: "주제 동시출현 그래프", waste_mix: "낭비 유형 누계", dl_cypher: "Cypher 내보내기 (Neo4j)",
    footer: "원문은 메모리에서만 처리되고 즉시 폐기됩니다. 분석기는 LLM을 호출하지 않습니다 — 토큰을 아끼자는 프로젝트가 토큰을 쓸 수는 없으니까요.",
    savings: "줄일 수 있었던 연산", savings_s: "같은 결과, 주제별 새 대화·낭비 제거 기준",
    compute: "실제 → 최적 연산 단위", compute_s: "입력 ×{w} + 출력",
    billed: "실제 과금 입력 토큰", billed_s: "보이는 텍스트 {v} 토큰을 매 턴 재전송",
    energy: "회피 가능 전력 (추정)", energy_s: "가정치 {f} Wh / 1k 단위",
    shape: "대화 형태", shape_s: "{u}개 질문 · {b}개 주제 갈래 · 최대 깊이 {d}",
    oneshot: "한 번에 물었다면", oneshot_s: "모든 요구를 한 프롬프트에 담은 하한선",
    waste_title: "어디서 새었나", w_ack: "감사·확인 메시지", w_sup: "버려진 답변 (수정·재질문)", w_off: "관련 없는 주제의 재전송", w_rest: "필요한 연산",
    skeleton_title: "대화 골격", skeleton_note: "x = 순서, y = 주제 갈래·깊이, 크기 = 토큰. 점선 테두리 = 낭비된 턴.",
    agenda: "아젠다", prompt_title: "한 번에 끝내는 프롬프트 골격", copy: "복사", copied: "복사됨",
    tips_title: "다음 대화에서 바꿀 습관",
    privacy_saved: "원문은 저장되지 않았습니다. 이 브라우저에 삭제 키가 보관되어 있습니다.",
    privacy_unsaved: "기여하지 않음: 아무것도 저장되지 않았습니다.",
    del: "내 기여 삭제", deleted: "삭제되었습니다.", exports: "내보내기",
    convs: "대화", total_units: "총 연산 단위", avoidable: "회피 가능", billed_total: "총 과금 입력 토큰",
    no_topics: "아직 공개 기준(k)을 넘은 주제가 없습니다.",
    multi: "{n}개의 대화를 분석했습니다", tip_none: "낭비가 거의 없는 대화입니다. 👍",
    intents: { ask: "질문", instruct: "지시", clarify: "보충", correct: "정정", retry: "재질문", continue: "계속", ack: "감사·확인", context: "대용량 붙여넣기", answer: "답변", code: "코드", followup_question: "되묻기", apology_fix: "사과·수정", refusal: "거절" },
  },
  en: {
    nav_analyze: "Analyze", nav_explore: "Public graph",
    hero_title: "Your AI re-reads the whole conversation, every single turn.",
    hero_lede: "Upload a shared chat link or export. We throw away the text, keep only its shape — agenda, flow, depth — as a graph, and show how much of the compute it didn't need.",
    c_convs: " conversations", c_units: " compute units measured", c_avoid: " was avoidable",
    input_label: "Share link, JSON export, or conversation text",
    input_ph: "https://chatgpt.com/share/…  ·  https://claude.ai/share/…\nor a ChatGPT/Claude export JSON\nor\nUser: …\nAssistant: …",
    file_btn: "Choose file", consent: "Contribute the anonymous skeleton to the public graph (no text stored, delete anytime)",
    sample: "Try an example", analyze: "Analyze", analyzing: "Analyzing…",
    explore_title: "Public graph",
    explore_lede: "Aggregates of contributed conversation skeletons. Topics are shown only once they appear in at least k conversations.",
    topic_graph: "Topic co-occurrence", waste_mix: "Waste by type (all)", dl_cypher: "Cypher export (Neo4j)",
    footer: "Text is processed in memory and discarded immediately. The analyzer calls no LLM — a project about saving tokens shouldn't spend them.",
    savings: "Avoidable compute", savings_s: "same results, one focused chat per topic, no waste",
    compute: "Actual → optimal compute units", compute_s: "input ×{w} + output",
    billed: "Billed input tokens", billed_s: "{v} visible tokens re-sent every turn",
    energy: "Avoidable energy (est.)", energy_s: "assumes {f} Wh / 1k units",
    shape: "Shape", shape_s: "{u} prompts · {b} topic threads · max depth {d}",
    oneshot: "If asked in one go", oneshot_s: "lower bound: every requirement in one prompt",
    waste_title: "Where it leaked", w_ack: "Thank-you / ok messages", w_sup: "Discarded answers (corrections, retries)", w_off: "Re-sending unrelated topics", w_rest: "Necessary",
    skeleton_title: "Conversation skeleton", skeleton_note: "x = order, y = topic thread & depth, size = tokens. Dashed outline = wasted turn.",
    agenda: "Agenda", prompt_title: "One-shot prompt skeleton", copy: "Copy", copied: "Copied",
    tips_title: "Habits to change next time",
    privacy_saved: "No text was stored. A delete key is kept in this browser.",
    privacy_unsaved: "Not contributed: nothing was stored.",
    del: "Delete my contribution", deleted: "Deleted.", exports: "Export",
    convs: "Conversations", total_units: "Compute units", avoidable: "Avoidable", billed_total: "Billed input tokens",
    no_topics: "No topic has reached the public threshold (k) yet.",
    multi: "Analyzed {n} conversations", tip_none: "Barely any waste here. 👍",
    intents: { ask: "ask", instruct: "instruct", clarify: "clarify", correct: "correct", retry: "retry", continue: "continue", ack: "thanks/ok", context: "big paste", answer: "answer", code: "code", followup_question: "asks back", apology_fix: "apology/fix", refusal: "refusal" },
  },
};

const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
};
let lang = store.get("lang") || ((navigator.language || "ko").startsWith("ko") ? "ko" : "en");
const t = (k, vars = {}) => String(T[lang][k] ?? k).replace(/\{(\w+)\}/g, (_, x) => vars[x] ?? "");
const fmt = (n) => (n ?? 0).toLocaleString(lang === "ko" ? "ko-KR" : "en-US");

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => (el.placeholder = t(el.dataset.i18nPlaceholder)));
  document.getElementById("lang").textContent = lang === "ko" ? "EN" : "한국어";
}

// ---------- DOM helpers (never innerHTML: labels derive from user content) ----------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== undefined && v !== null && v !== false) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid instanceof Node ? kid : String(kid));
  return el;
}
const SVGNS = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}, ...kids) {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) el.setAttribute(k, v);
  for (const kid of kids.flat()) if (kid) el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return el;
}
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const intentColor = (turn) => turn.role === "assistant"
  ? (turn.intent === "apology_fix" || turn.intent === "refusal" ? cssVar("--bad") : cssVar("--i-assistant"))
  : cssVar(`--i-${turn.intent}`) || cssVar("--i-ask");

// ---------- API ----------
async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const body = r.headers.get("content-type")?.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error(body?.detail || r.statusText);
  return body;
}

// ---------- views ----------
const $ = (id) => document.getElementById(id);
function show(view) {
  $("hero").hidden = view === "explore";
  $("analyze").hidden = view !== "home";
  $("result").hidden = view !== "result";
  $("explore").hidden = view !== "explore";
}

async function loadCounter() {
  try {
    const st = await api("/api/stats");
    if (!st.conversations) return;
    $("c-convs").textContent = fmt(st.conversations);
    $("c-units").textContent = fmt(st.compute_units);
    $("c-avoid").textContent = `${st.avoidable_pct}%`;
    $("counter").hidden = false;
  } catch { /* counter is decorative */ }
}

function statCard(k, v, sub, hero = false) {
  return h("div", { class: "stat" + (hero ? " hero" : "") }, h("div", { class: "k" }, k), h("div", { class: "v" }, v), sub ? h("div", { class: "s" }, sub) : null);
}

function wasteBar(parts) {
  const total = parts.reduce((a, p) => a + p.v, 0) || 1;
  return [
    h("div", { class: "bar" }, parts.filter((p) => p.v > 0).map((p) => h("div", { style: `width:${(100 * p.v) / total}%;background:${p.c}`, title: `${p.label}: ${p.pct ?? Math.round((100 * p.v) / total)}%` }))),
    h("div", { class: "legend" }, parts.filter((p) => p.v > 0).map((p) => h("span", {}, h("i", { style: `background:${p.c}` }), `${p.label} ${p.pct ?? Math.round((100 * p.v) / total)}%`))),
  ];
}

function skeletonSvg(sk) {
  const turns = sk.turns;
  const n = turns.length;
  const step = Math.max(26, Math.min(60, 900 / Math.max(1, n)));
  const branches = [...new Set(turns.map((x) => x.branch))].sort((a, b) => a - b);
  const laneDepth = Object.fromEntries(branches.map((b) => [b, Math.max(...turns.filter((x) => x.branch === b).map((x) => x.depth))]));
  const laneTop = {}; let y = 26;
  for (const b of branches) { laneTop[b] = y; y += (laneDepth[b] + 1) * 26 + 22; }
  const W = 50 + n * step, H = y + 10;
  const pos = {};
  turns.forEach((tn, i) => { pos[tn.index] = { x: 40 + i * step, y: laneTop[tn.branch] + tn.depth * 26 + 10 }; });
  const r = (tn) => Math.min(16, 3 + Math.sqrt(tn.tokens) / 2.6);
  const edgeColor = { DEEPENS: cssVar("--accent"), PIVOTS: cssVar("--warn"), RETURNS: cssVar("--i-clarify"), CORRECTS: cssVar("--bad"), RETRIES: cssVar("--i-retry"), CONTINUES: cssVar("--i-continue"), REVISITS: cssVar("--muted") };
  const svg = s("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": t("skeleton_title") });
  for (const b of branches) {
    svg.append(s("line", { class: "axis", x1: 30, x2: W - 10, y1: laneTop[b] - 4, y2: laneTop[b] - 4 }));
    svg.append(s("text", { x: 2, y: laneTop[b] + 12 }, `#${b + 1}`));
  }
  for (let i = 1; i < n; i++) {
    const a = pos[turns[i - 1].index], b = pos[turns[i].index];
    svg.append(s("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: cssVar("--line"), "stroke-width": 1.5 }));
  }
  for (const e of sk.edges) {
    if (!edgeColor[e.type]) continue;
    const a = pos[e.src], b = pos[e.dst];
    const mx = (a.x + b.x) / 2, my = Math.min(a.y, b.y) - 14 - Math.abs(a.x - b.x) / 6;
    svg.append(s("path", { class: "edge", d: `M${a.x},${a.y} Q${mx},${my} ${b.x},${b.y}`, stroke: edgeColor[e.type] }, s("title", {}, e.type)));
  }
  for (const tn of turns) {
    const p = pos[tn.index], rad = r(tn), fill = intentColor(tn);
    const tip = s("title", {}, `#${tn.index + 1} ${tn.role} · ${T[lang].intents[tn.intent] || tn.intent} · ${fmt(tn.tokens)} tok${tn.topics.length ? " · " + tn.topics.join(", ") : ""}`);
    const cls = "node" + (tn.redundant ? " redundant" : "");
    svg.append(tn.role === "user"
      ? s("circle", { class: cls, cx: p.x, cy: p.y, r: rad, fill }, tip)
      : s("rect", { class: cls, x: p.x - rad, y: p.y - rad, width: rad * 2, height: rad * 2, rx: 3, fill }, tip));
  }
  return svg;
}

function intentLegend(sk) {
  const used = [...new Set(sk.turns.map((x) => (x.role === "user" ? x.intent : x.intent === "apology_fix" || x.intent === "refusal" ? x.intent : "answer")))];
  return h("div", { class: "legend" }, used.map((k) => h("span", {}, h("i", { style: `background:${k === "answer" ? cssVar("--i-assistant") : k === "apology_fix" || k === "refusal" ? cssVar("--bad") : cssVar(`--i-${k}`)}` }), T[lang].intents[k] || k)));
}

function renderResult(sk, others = []) {
  const m = sk.metrics, w = m.waste;
  const out = $("result");
  out.replaceChildren();
  if (others.length > 1) {
    out.append(h("div", { class: "card" }, h("h3", {}, t("multi", { n: others.length })),
      h("div", { class: "chips" }, others.map((o) => h("a", { class: "chip" + (o.skeleton.id === sk.id ? " main" : ""), href: "#", onclick: (ev) => { ev.preventDefault(); renderResult(o.skeleton, others); } }, `${o.skeleton.agenda.slice(0, 2).join(" · ") || o.skeleton.id} (${o.skeleton.metrics.savings_pct}%)`)))));
  }
  out.append(h("div", { class: "grid" },
    statCard(t("savings"), `${m.savings_pct}%`, t("savings_s"), true),
    statCard(t("compute"), `${fmt(m.compute_units)} → ${fmt(m.optimized_compute_units)}`, t("compute_s", { w: m.assumptions.input_weight })),
    statCard(t("billed"), fmt(m.billed_input_tokens), t("billed_s", { v: fmt(m.visible_tokens) })),
    statCard(t("oneshot"), `${m.one_shot_savings_pct}%`, t("oneshot_s")),
    statCard(t("energy"), `${m.energy_wh_avoidable} Wh`, t("energy_s", { f: m.assumptions.wh_per_1k_units })),
    statCard(t("shape"), `${m.user_turns}/${m.branches}/${m.max_depth}`, t("shape_s", { u: m.user_turns, b: m.branches, d: m.max_depth })),
  ));
  const rest = Math.max(0, 100 - w.ack_pct - w.superseded_pct - w.offtopic_context_pct);
  out.append(h("div", { class: "card" }, h("h3", {}, t("waste_title")), wasteBar([
    { label: t("w_ack"), v: w.ack_pct, pct: w.ack_pct, c: cssVar("--i-ack") },
    { label: t("w_sup"), v: w.superseded_pct, pct: w.superseded_pct, c: cssVar("--bad") },
    { label: t("w_off"), v: w.offtopic_context_pct, pct: w.offtopic_context_pct, c: cssVar("--warn") },
    { label: t("w_rest"), v: rest, pct: Math.round(rest * 10) / 10, c: cssVar("--accent") },
  ])));
  out.append(h("div", { class: "card" }, h("h3", {}, t("skeleton_title")), h("div", { class: "graph" }, skeletonSvg(sk)), intentLegend(sk), h("p", { class: "note" }, t("skeleton_note"))));
  out.append(h("div", { class: "card" }, h("h3", {}, t("agenda")), h("div", { class: "chips" }, sk.agenda.map((a, i) => h("span", { class: "chip" + (i < 3 ? " main" : "") }, a)))));
  const pre = h("pre", { class: "prompt" }, sk.suggestion.prompt_template);
  const copyBtn = h("button", { class: "ghost", type: "button", onclick: async () => { try { await navigator.clipboard.writeText(sk.suggestion.prompt_template); copyBtn.textContent = t("copied"); } catch { /* clipboard blocked */ } } }, t("copy"));
  out.append(h("div", { class: "card" }, h("h3", {}, t("prompt_title")), pre, copyBtn));
  const tips = sk.suggestion.tips;
  out.append(h("div", { class: "card" }, h("h3", {}, t("tips_title")), tips.length ? h("ol", { class: "tips" }, tips.map((x) => h("li", {}, x[lang] || x.en))) : h("p", {}, t("tip_none"))));
  const token = (store.get("delete_tokens") || {})[sk.id];
  const actions = h("div", { class: "actions" },
    h("span", { class: "note" }, t("exports") + ":"),
    h("a", { href: `/api/conversations/${encodeURIComponent(sk.id)}/graph.json` }, "graph.json"),
    h("a", { href: `/api/conversations/${encodeURIComponent(sk.id)}/cypher` }, "Cypher"));
  if (token) {
    const del = h("button", { class: "ghost", type: "button", onclick: async () => {
      try {
        await api(`/api/conversations/${encodeURIComponent(sk.id)}`, { method: "DELETE", headers: { "X-Delete-Token": token } });
        const all = store.get("delete_tokens") || {}; delete all[sk.id]; store.set("delete_tokens", all);
        del.replaceWith(h("span", { class: "note" }, t("deleted")));
      } catch (e) { alert(e.message); }
    } }, t("del"));
    actions.append(del);
  }
  out.append(h("div", { class: "card" }, h("p", { class: "note" }, sk._saved === false ? t("privacy_unsaved") : t("privacy_saved")), actions));
  show("result");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------- explore ----------
function forceGraph(graph) {
  const W = 900, H = 520;
  const nodes = graph.nodes.map((n, i) => ({ ...n, x: W / 2 + 200 * Math.cos(i), y: H / 2 + 160 * Math.sin(i), vx: 0, vy: 0 }));
  const idx = Object.fromEntries(nodes.map((n, i) => [n.label, i]));
  const links = graph.links.filter((l) => l.source in idx && l.target in idx);
  const maxC = Math.max(1, ...nodes.map((n) => n.conversations));
  for (let it = 0; it < 300; it++) {
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j]; let dx = a.x - b.x, dy = a.y - b.y; const d2 = dx * dx + dy * dy + 0.01;
      const f = 1800 / d2; dx *= f; dy *= f; a.vx += dx; a.vy += dy; b.vx -= dx; b.vy -= dy;
    }
    for (const l of links) {
      const a = nodes[idx[l.source]], b = nodes[idx[l.target]]; const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1; const f = (d - 90) * 0.01;
      a.vx += (dx / d) * f * d * 0.05; a.vy += (dy / d) * f * d * 0.05; b.vx -= (dx / d) * f * d * 0.05; b.vy -= (dy / d) * f * d * 0.05;
    }
    for (const n of nodes) { n.vx += (W / 2 - n.x) * 0.01; n.vy += (H / 2 - n.y) * 0.01; n.x += Math.max(-8, Math.min(8, n.vx * 0.5)); n.y += Math.max(-8, Math.min(8, n.vy * 0.5)); n.vx *= 0.6; n.vy *= 0.6; n.x = Math.max(30, Math.min(W - 30, n.x)); n.y = Math.max(20, Math.min(H - 20, n.y)); }
  }
  const svg = s("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": t("topic_graph") });
  for (const l of links) { const a = nodes[idx[l.source]], b = nodes[idx[l.target]]; svg.append(s("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: cssVar("--line"), "stroke-width": Math.min(6, 1 + Math.log2(l.count)) })); }
  for (const n of nodes) {
    const rad = 5 + 14 * Math.sqrt(n.conversations / maxC);
    svg.append(s("circle", { cx: n.x, cy: n.y, r: rad, fill: cssVar("--accent"), opacity: 0.85 }, s("title", {}, `${n.label}: ${n.conversations}`)));
    svg.append(s("text", { class: "tlabel", x: n.x + rad + 3, y: n.y + 4 }, n.label));
  }
  return svg;
}

async function renderExplore() {
  show("explore");
  const [st, tg] = await Promise.all([api("/api/stats"), api("/api/topics")]);
  $("ex-stats").replaceChildren(
    statCard(t("convs"), fmt(st.conversations)),
    statCard(t("total_units"), fmt(st.compute_units)),
    statCard(t("avoidable"), `${st.avoidable_pct}%`, fmt(st.avoidable_units), true),
    statCard(t("billed_total"), fmt(st.billed_input_tokens)),
  );
  $("ex-graph").replaceChildren(tg.nodes.length ? forceGraph(tg) : h("p", { class: "muted" }, t("no_topics")));
  const wv = st.waste || {};
  $("ex-waste").replaceChildren(...wasteBar([
    { label: t("w_ack"), v: wv.ack_units || 0, c: cssVar("--i-ack") },
    { label: t("w_sup"), v: wv.superseded_units || 0, c: cssVar("--bad") },
    { label: t("w_off"), v: (wv.offtopic_context_tokens || 0) * 0.25, c: cssVar("--warn") },
  ]));
}

// ---------- form ----------
const SAMPLE = {
  ko: "User: React에서 useEffect 무한 루프가 발생하는 이유를 알려줘\nAssistant: useEffect 무한 루프는 의존성 배열에 매 렌더마다 새로 생성되는 객체나 함수가 들어갈 때 발생합니다. 상태 업데이트가 effect 안에서 일어나고 그 상태가 의존성 배열에 있으면 렌더링이 반복됩니다. useCallback과 useMemo로 참조를 고정하세요.\nUser: useCallback 의존성 배열 예제 코드 보여줘\nAssistant: 다음은 예제입니다.\n```js\nconst fetchData = useCallback(() => api.get(id), [id]);\nuseEffect(() => { fetchData() }, [fetchData]);\n```\nUser: 아니 그게 아니라 TypeScript로 작성해줘\nAssistant: 죄송합니다. TypeScript 버전입니다.\n```ts\nconst fetchData = useCallback((): void => { api.get(id) }, [id]);\n```\nUser: 고마워\nAssistant: 천만에요! 더 궁금한 점이 있으면 언제든 물어보세요.\nUser: 그런데 파이썬 pandas 데이터프레임 병합 방법도 알려줘\nAssistant: pandas에서는 merge, join, concat을 사용합니다. pd.merge(df1, df2, on='key')처럼 키 기준으로 병합합니다.\nUser: 고마워요\nAssistant: 별말씀을요! 즐거운 코딩 되세요.",
  en: "User: Why does my React useEffect run in an infinite loop?\nAssistant: An infinite loop happens when the dependency array contains an object or function that is recreated on every render, or when the effect updates state that is itself a dependency. Stabilize references with useCallback and useMemo.\nUser: Show me a useCallback dependency array example\nAssistant: Here is an example:\n```js\nconst fetchData = useCallback(() => api.get(id), [id]);\nuseEffect(() => { fetchData() }, [fetchData]);\n```\nUser: No, that's not what I asked, write it in TypeScript\nAssistant: You're right, here is the TypeScript version:\n```ts\nconst fetchData = useCallback((): void => { api.get(id) }, [id]);\n```\nUser: thanks!\nAssistant: You're welcome! Let me know if you have any other questions about React hooks.\nUser: How do I merge two pandas dataframes in Python?\nAssistant: Use pd.merge(df1, df2, on='key') to join on a key column, or concat to stack them.\nUser: thank you\nAssistant: Happy coding!",
};

async function submit(ev) {
  ev.preventDefault();
  const btn = $("go"), err = $("error");
  err.hidden = true; btn.disabled = true; btn.textContent = t("analyzing");
  try {
    const save = $("save").checked;
    const file = $("file").files[0];
    let res;
    if (file) {
      const fd = new FormData(); fd.append("file", file); fd.append("save", String(save));
      res = await api("/api/analyze/file", { method: "POST", body: fd });
    } else {
      res = await api("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ input: $("input").value, save }) });
    }
    const tokens = store.get("delete_tokens") || {};
    for (const r of res.results) { r.skeleton._saved = r.saved; if (r.delete_token) tokens[r.skeleton.id] = r.delete_token; }
    store.set("delete_tokens", tokens);
    $("input").value = ""; $("file").value = ""; $("file-name").textContent = "";
    const first = res.results[0];
    if (first.saved) history.pushState({}, "", `/c/${first.skeleton.id}`);
    renderResult(first.skeleton, res.results);
    loadCounter();
  } catch (e) {
    err.textContent = e.message; err.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = t("analyze");
  }
}

async function route() {
  const p = location.pathname;
  if (p.startsWith("/c/")) {
    try { renderResult(await api(`/api/conversations/${encodeURIComponent(p.slice(3))}`)); }
    catch (e) { show("home"); $("error").textContent = e.message; $("error").hidden = false; }
  } else if (p === "/explore") {
    renderExplore().catch((e) => { $("ex-stats").replaceChildren(h("p", { class: "error" }, e.message)); });
  } else {
    show("home");
  }
}

$("form").addEventListener("submit", submit);
$("sample").addEventListener("click", () => { $("input").value = SAMPLE[lang]; });
$("file").addEventListener("change", () => { $("file-name").textContent = $("file").files[0]?.name || ""; });
$("lang").addEventListener("click", () => { lang = lang === "ko" ? "en" : "ko"; store.set("lang", lang); applyI18n(); route(); });
window.addEventListener("popstate", route);
applyI18n();
loadCounter();
route();
