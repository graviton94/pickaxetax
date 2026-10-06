// #AntiTokenMaxing static site. Everything happens in this tab: the page's CSP
// (connect-src 'none') makes it impossible to send the conversation anywhere.
import { analyzeInput, analyzeTurns, LinkInput } from "./engine.js";
import { skeletonContribution, solvePow, validateContribution } from "./contrib.js";
import { footprint } from "./carbon.js";

export const ENGINE_VERSION = "0.4.0"; // kept equal to pyproject.toml by tests/test_contrib.py
const CONFIG = window.PXT_CONFIG || { contribUrl: "", repo: "graviton94/pickaxetax" };

// ---------- i18n ----------
const T = {
  en: {
    nav_check: "Check",
    nav_weight: "The weight of a line",
    nav_know: "Did you know?",
    nav_bill: "The receipt",
    nav_cost: "The cost",
    intro_tag: "The receipt of the 21st-century gold rush",
    nav_about: "About us",
    know_eyebrow: "You know?",
    know_title: "Measured to the token.",
    know_lede: "Real AI usage, re-measured from the usage the provider recorded for every call. No estimates.",
    k1_v: "73.6%",
    k1_t: "of the context carried on every call was left over from instructions that were already finished.",
    k2_v: "0.2–0.4%",
    k2_t: "is how much the AI wrote compared with what it read, in the 3 sessions whose output was recorded exactly.",
    k3_v: "780K",
    k3_t: "tokens is the ceiling. Context is compacted only when it fills up, so sessions run almost full.",
    k4_v: "45.6%",
    k4_t: "of all input came from the top 10% of instructions. One instruction used 220 million tokens.",
    k5_v: "1.49×",
    k5_t: "more usage than the session list shows. Older sessions showed only a quarter to a half of it.",
    k6_v: "10M",
    k6_t: "tokens re-read per instruction on average, across 586 instructions.",
    know_src: "Source: Receipt No. 01. One user, 10 Claude Code sessions, 2026-07-10 – 10-05, recomputed from a public dataset.",
    bill_eyebrow: "Receipt No. 01",
    bill_title: "The receipt of the 21st-century gold rush",
    bill_f1: "Subject",
    bill_v1: "The project's founder (anonymized)",
    bill_f2: "Period",
    bill_v2: "2026-07-10 – 2026-10-05, 10 Claude Code sessions",
    bill_f3: "Source",
    bill_v3: "Provider-recorded usage for every API call",
    bill_amount: "5.87B",
    bill_amount_note: "input tokens processed (lower bound)",
    bill_lede: "Every number on the receipt is recomputed from a public dataset each time the report is built. Same dataset, same report, byte for byte.",
    bill_open: "Open the full receipt",
    bill_cmd_title: "Get your own receipt",
    bill_cmd_note: "Runs on your machine. The dataset holds numbers only: no text, paths or ids.",
    about_eyebrow: "About us",
    about_title: "Judge AI by how little it needs, not by how much it burns.",
    about_lede: "#AntiTokenMaxing is a public-interest, open-source project. In a gold rush the people who get rich sell the pickaxes; in this one the pickaxes are chips and data centers, and everyone splits the receipt: in power bills, carbon and waste. We read that receipt line by line, and build tools that strike out the lines nobody needed. We are not against AI. We are against waste.",
    p1_t: "Local first",
    p1_d: "Your conversation text never leaves this page. Its security policy blocks every outgoing request except the numbers-only contribution you choose to send.",
    p2_t: "Measured, not guessed",
    p2_d: "Every number comes from recorded usage, with its source and its limits. Failed hypotheses are published too.",
    p3_t: "Open",
    p3_d: "Code under Apache-2.0, data under ODbL. Anyone can recompute every number, including people who disagree.",
    about_research: "Research",
    about_contribute: "Contribute",
    kicker: "Check your own receipt first.",
    hero_title: "Your AI re-reads the whole conversation, every single turn.",
    hero_lede: "Paste a conversation, drop an export file, or use a share link. We keep only its shape (agenda, flow, depth) and show how much of the compute it didn't need.",
    badge: "🔒 Runs in your browser. Nothing is uploaded.",
    input_label: "Conversation text, export JSON, or a share link",
    input_ph: "User: …\nAssistant: …\n\nor a ChatGPT / Claude export JSON\nor https://chatgpt.com/share/…",
    file_btn: "Choose file", sample: "Try an example", analyze: "Analyze", analyzing: "Analyzing…",
    link_title: "Analyze a share link (locally)",
    link_step1: "Drag this button to your bookmarks bar:",
    link_step2: "Open the shared conversation (ChatGPT, Claude, Gemini…).",
    link_step3: "Click the bookmark on that page. The conversation is read from the page you already have open and handed to this tab. No server is involved.",
    link_note: "Why a bookmark? Browsers don't allow one website to read another, and fetching the link through a server would mean someone else's server sees your conversation. The bookmark reads the page you're already looking at.",
    link_detected: "That's a share link. Open it, then click the ⛏ AntiTokenMaxing bookmark on that page (see the steps below).",
    drag_hint: "Drag this button to your bookmarks bar, then click it on a shared conversation page.",
    footer: "Your text is analyzed in this tab and never leaves it. The analyzer calls no AI model: a project about saving tokens shouldn't spend them.",
    engine_note: "same engine as the Python package, parity-tested",
    savings: "Avoidable compute", savings_s: "same results, one focused chat per topic, no waste",
    compute: "Actual → optimal compute units", compute_s: "input ×{w} + output",
    billed: "Billed input tokens", billed_s: "{v} visible tokens re-sent every turn",
    oneshot: "If asked in one go", oneshot_s: "lower bound: every requirement in one prompt",
    energy: "Avoidable energy (est.)", energy_s: "assumes {f} Wh / 1k units",
    co2: "Carbon of the re-reading (est.)", co2_s: "≈ {h} of a tree absorbing it · factors in “The weight of a line”", co2_h: "{v} hours", co2_m: "{v} minutes",
    shape: "Shape", shape_s: "{u} prompts · {b} topic threads · max depth {d}",
    waste_title: "Where it leaked", w_ack: "Thank-you / ok messages", w_sup: "Discarded answers (corrections, retries)", w_off: "Re-sending unrelated topics", w_rest: "Necessary",
    skeleton_title: "Conversation skeleton", skeleton_note: "x = order, y = topic thread & depth, size = tokens. Dashed outline = wasted turn.",
    agenda: "Agenda", prompt_title: "One-shot prompt skeleton", copy: "Copy", copied: "Copied",
    tips_title: "Habits to change next time", tip_none: "Barely any waste here. 👍",
    download: "Download skeleton (JSON)", multi: "Analyzed {n} conversations", from_page: "Read from {src}",
    c_title: "Contribute to the public index", c_lede: "Only numbers and structure are sent (turn intents, depth, token counts). Never your text. No account needed.",
    c_labels: "Also share these topic words (they become public; click × to remove a word)", c_show: "Exactly what will be sent",
    c_anon: "Contribute anonymously", c_github: "Contribute with GitHub (verified)", c_solving: "Proving you're not a bot (a few seconds)…",
    c_thanks: "Thank you! Your contribution is in. It appears in the public index at the next daily update.", c_undo: "Delete my contribution", c_deleted: "Deleted.",
    c_done: "You already contributed this conversation.", c_off: "Anonymous contributions open soon. GitHub works today.", c_clip: "The payload was copied to your clipboard: paste it into the issue form.",
    impact_title: "Public impact", impact_lede: "Aggregated from contributions worldwide. Topics appear only after at least {k} independent contributions.",
    i_convs: "Conversations analyzed", i_avoid: "Compute that was avoidable", i_median: "Typical (median) waste", i_sessions: "Coding-agent sessions", i_contrib: "Contributions ({v} verified)", impact_topics: "What people ask about",
    intents: { ask: "ask", instruct: "instruct", clarify: "clarify", correct: "correct", retry: "retry", continue: "continue", ack: "thanks/ok", context: "big paste", answer: "answer", code: "code", followup_question: "asks back", apology_fix: "apology/fix", refusal: "refusal" },
  },
  ko: {
    nav_check: "진단",
    nav_weight: "한 줄의 무게",
    nav_know: "알고 계셨나요?",
    nav_bill: "영수증",
    nav_cost: "그 대가",
    intro_tag: "21세기 골드러시의 영수증",
    nav_about: "소개",
    know_eyebrow: "You know?",
    know_title: "토큰 단위까지, 다시 쟀습니다.",
    know_lede: "실제 AI 사용 기록을, 제공사가 호출마다 남긴 사용량으로 다시 쟀습니다. 추정은 없습니다.",
    k1_v: "73.6%",
    k1_t: "매 호출이 들고 간 컨텍스트 가운데, 이미 끝난 지시들이 남긴 내용의 비중입니다.",
    k2_v: "0.2~0.4%",
    k2_t: "AI가 읽은 양에 비해 실제로 써낸 양입니다. 출력이 정확히 기록된 세션 3개 기준입니다.",
    k3_v: "78만",
    k3_t: "토큰이 천장입니다. 컨텍스트는 여기에 닿을 때만 압축되고, 세션은 거의 늘 가득 찬 채로 돕니다.",
    k4_v: "45.6%",
    k4_t: "상위 10% 지시가 쓴 입력의 비중입니다. 지시 하나가 2억 2천만 토큰을 쓴 적도 있습니다.",
    k5_v: "1.49배",
    k5_t: "세션 목록에 표시된 것보다 실제 사용량이 이만큼 많았습니다. 오래된 세션은 실제의 4분의 1~2분의 1만 표시됐습니다.",
    k6_v: "1,000만",
    k6_t: "토큰이 지시 한 번에 평균적으로 다시 읽혔습니다. 지시 586번의 평균입니다.",
    know_src: "출처: 영수증 No.01. 한 사용자의 Claude Code 세션 10개, 2026-07-10 ~ 10-05, 공개 데이터셋에서 재계산",
    bill_eyebrow: "Receipt No. 01",
    bill_title: "21세기 골드러시의 영수증",
    bill_f1: "조사 대상",
    bill_v1: "프로젝트 대표 본인 (익명)",
    bill_f2: "조사 기간",
    bill_v2: "2026-07-10 ~ 2026-10-05, Claude Code 세션 10개",
    bill_f3: "측정 원천",
    bill_v3: "제공사가 API 호출마다 기록한 사용량",
    bill_amount: "58.71억",
    bill_amount_note: "토큰의 입력을 처리했습니다 (하한)",
    bill_lede: "영수증의 모든 숫자는 레포트를 만들 때마다 공개 데이터셋에서 다시 계산됩니다. 같은 데이터셋이면 같은 레포트가 바이트 단위까지 똑같이 나옵니다.",
    bill_open: "영수증 전문 보기",
    bill_cmd_title: "내 영수증 받기",
    bill_cmd_note: "내 컴퓨터에서 실행됩니다. 데이터셋에는 숫자만 담기고, 텍스트·경로·ID는 담기지 않습니다.",
    about_eyebrow: "About us",
    about_title: "AI는 얼마나 많이 태웠는지가 아니라, 얼마나 적게 쓰고 해냈는지로 평가받아야 합니다.",
    about_lede: "#AntiTokenMaxing은 공익 오픈소스 프로젝트입니다. 골드러시에서 돈을 버는 건 곡괭이를 파는 쪽입니다. 이번 골드러시의 곡괭이는 반도체와 데이터센터이고, 영수증은 모두가 나눠 냅니다. 전기요금으로, 탄소로, 쓰레기로. 우리는 그 영수증을 한 줄씩 뜯어보고, 아무도 필요하지 않았던 줄을 지우는 도구를 만듭니다. AI를 반대하지 않습니다. 낭비를 반대합니다.",
    p1_t: "로컬 우선",
    p1_d: "대화 원문은 이 페이지 밖으로 나가지 않습니다. 보안 정책이, 직접 선택한 숫자 기여 말고는 모든 외부 요청을 막습니다.",
    p2_t: "추정이 아니라 측정",
    p2_d: "모든 숫자는 기록된 사용량에서 나오고, 출처와 한계를 함께 적습니다. 틀린 가설도 공개합니다.",
    p3_t: "공개",
    p3_d: "코드는 Apache-2.0, 데이터는 ODbL입니다. 동의하지 않는 사람도 모든 숫자를 다시 계산할 수 있어야 합니다.",
    about_research: "연구",
    about_contribute: "기여하기",
    kicker: "당신의 영수증부터 확인하세요.",
    hero_title: "AI는 같은 대화를 매번 처음부터 다시 읽습니다.",
    hero_lede: "대화를 붙여넣거나, 내보내기 파일을 올리거나, 공유 링크를 쓰세요. 대화의 구조(아젠다·흐름·깊이)만 남겨 불필요했던 연산이 얼마인지 보여줍니다.",
    badge: "🔒 브라우저 안에서만 처리됩니다. 아무것도 업로드되지 않습니다.",
    input_label: "대화 텍스트, 내보내기 JSON, 또는 공유 링크",
    input_ph: "User: …\nAssistant: …\n\n또는 ChatGPT / Claude 내보내기 JSON\n또는 https://chatgpt.com/share/…",
    file_btn: "파일 선택", sample: "예시로 해보기", analyze: "분석하기", analyzing: "분석 중…",
    link_title: "공유 링크 분석하기 (로컬)",
    link_step1: "이 버튼을 북마크바로 끌어다 놓으세요:",
    link_step2: "공유된 대화 페이지(ChatGPT, Claude, Gemini 등)를 엽니다.",
    link_step3: "그 페이지에서 북마크를 클릭하세요. 이미 열려 있는 페이지에서 대화를 읽어 이 탭으로 넘깁니다. 서버를 거치지 않습니다.",
    link_note: "왜 북마크인가요? 브라우저는 한 사이트가 다른 사이트를 읽는 것을 막습니다. 서버로 링크를 대신 가져오면 남의 서버가 대화를 보게 됩니다. 북마크는 지금 보고 있는 페이지를 직접 읽습니다.",
    link_detected: "공유 링크입니다. 링크를 연 뒤, 그 페이지에서 ⛏ AntiTokenMaxing 북마크를 클릭하세요 (아래 안내 참고).",
    drag_hint: "이 버튼을 북마크바로 끌어다 놓은 뒤, 공유 대화 페이지에서 클릭하세요.",
    footer: "텍스트는 이 탭 안에서만 분석되고 밖으로 나가지 않습니다. 분석기는 AI 모델을 호출하지 않습니다. 토큰을 아끼자는 프로젝트가 토큰을 쓸 수는 없으니까요.",
    engine_note: "Python 패키지와 동일한 엔진 (동등성 테스트 통과)",
    savings: "줄일 수 있었던 연산", savings_s: "같은 결과, 주제별 새 대화·낭비 제거 기준",
    compute: "실제 → 최적 연산 단위", compute_s: "입력 ×{w} + 출력",
    billed: "실제 과금 입력 토큰", billed_s: "보이는 텍스트 {v} 토큰을 매 턴 재전송",
    oneshot: "한 번에 물었다면", oneshot_s: "모든 요구를 한 프롬프트에 담은 하한선",
    energy: "회피 가능 전력 (추정)", energy_s: "가정치 {f} Wh / 1k 단위",
    co2: "다시 읽기의 탄소 (추정)", co2_s: "나무 한 그루가 {h} 동안 흡수할 양 · 계수는 ‘한 줄의 무게’ 참고", co2_h: "{v}시간", co2_m: "{v}분",
    shape: "대화 형태", shape_s: "{u}개 질문 · {b}개 주제 갈래 · 최대 깊이 {d}",
    waste_title: "어디서 새었나", w_ack: "감사·확인 메시지", w_sup: "버려진 답변 (수정·재질문)", w_off: "관련 없는 주제의 재전송", w_rest: "필요한 연산",
    skeleton_title: "대화 골격", skeleton_note: "x = 순서, y = 주제 갈래·깊이, 크기 = 토큰. 점선 테두리 = 낭비된 턴.",
    agenda: "아젠다", prompt_title: "한 번에 끝내는 프롬프트 골격", copy: "복사", copied: "복사됨",
    tips_title: "다음 대화에서 바꿀 습관", tip_none: "낭비가 거의 없는 대화입니다. 👍",
    download: "골격 내려받기 (JSON)", multi: "{n}개의 대화를 분석했습니다", from_page: "{src}에서 읽음",
    c_title: "공익 지수에 기여하기", c_lede: "숫자와 구조(턴 의도·깊이·토큰 수)만 전송됩니다. 대화 텍스트는 절대 보내지 않습니다. 계정이 필요 없습니다.",
    c_labels: "이 주제 단어도 공유하기 (공개됩니다. ×로 단어를 뺄 수 있습니다)", c_show: "실제로 전송되는 내용",
    c_anon: "익명으로 기여하기", c_github: "GitHub로 기여하기 (검증됨)", c_solving: "봇이 아님을 확인하는 중 (몇 초)…",
    c_thanks: "감사합니다! 기여가 접수되었습니다. 매일 갱신되는 공익 지수에 반영됩니다.", c_undo: "내 기여 삭제", c_deleted: "삭제되었습니다.",
    c_done: "이 대화는 이미 기여하셨습니다.", c_off: "익명 기여는 곧 열립니다. GitHub 기여는 지금 가능합니다.", c_clip: "기여 내용이 클립보드에 복사되었습니다. 이슈 양식에 붙여넣으세요.",
    impact_title: "공익 임팩트", impact_lede: "전 세계 기여를 집계한 결과입니다. 주제는 서로 다른 기여 {k}건 이상에서 나와야 공개됩니다.",
    i_convs: "분석된 대화", i_avoid: "회피 가능했던 연산", i_median: "대화당 낭비 (중앙값)", i_sessions: "코딩 에이전트 세션", i_contrib: "기여 수 (검증 {v}건)", impact_topics: "사람들이 묻는 주제",
    intents: { ask: "질문", instruct: "지시", clarify: "보충", correct: "정정", retry: "재질문", continue: "계속", ack: "감사·확인", context: "대용량 붙여넣기", answer: "답변", code: "코드", followup_question: "되묻기", apology_fix: "사과·수정", refusal: "거절" },
  },
};

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};
let lang = store.get("lang") || ((navigator.language || "en").startsWith("ko") ? "ko" : "en");
const t = (k, vars = {}) => String(T[lang][k] ?? k).replace(/\{(\w+)\}/g, (_, x) => vars[x] ?? "");
const fmt = (n) => (n ?? 0).toLocaleString(lang === "ko" ? "ko-KR" : "en-US");
const $ = (id) => document.getElementById(id);

// ---------- DOM helpers (never innerHTML: labels derive from user content) ----------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") el.className = v;
    else if (k === "style") el.style.cssText = v; // CSSOM, allowed under style-src 'self'
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
const BAD = new Set(["apology_fix", "refusal"]);
const intentColor = (turn) => turn.role === "assistant"
  ? (BAD.has(turn.intent) ? cssVar("--bad") : cssVar("--i-assistant"))
  : cssVar(`--i-${turn.intent}`) || cssVar("--i-ask");

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => (el.placeholder = t(el.dataset.i18nPlaceholder)));
  $("lang").textContent = lang === "ko" ? "EN" : "한국어";
}

// ---------- rendering ----------
function statCard(k, v, sub, hero = false) {
  return h("div", { class: "stat" + (hero ? " hero" : "") }, h("div", { class: "k" }, k), h("div", { class: "v" }, v), sub ? h("div", { class: "s" }, sub) : null);
}

function co2Card(tokens) {
  const f = footprint(tokens || 0);
  const g = f.g_co2 >= 10 ? fmt(Math.round(f.g_co2)) : f.g_co2.toFixed(f.g_co2 >= 1 ? 1 : 2);
  const span = f.tree_hours >= 1 ? t("co2_h", { v: f.tree_hours.toFixed(f.tree_hours >= 10 ? 0 : 1) }) : t("co2_m", { v: Math.max(1, Math.round(f.tree_hours * 60)) });
  return statCard(t("co2"), `${g} g CO₂`, t("co2_s", { h: span }));
}

function wasteBar(parts) {
  const total = parts.reduce((a, p) => a + p.v, 0) || 1;
  const shown = parts.filter((p) => p.v > 0);
  return [
    h("div", { class: "bar" }, shown.map((p) => h("div", { style: `width:${(100 * p.v) / total}%;background:${p.c}`, title: `${p.label}: ${p.v}%` }))),
    h("div", { class: "legend" }, shown.map((p) => h("span", {}, h("i", { style: `background:${p.c}` }), `${p.label} ${p.v}%`))),
  ];
}

function skeletonSvg(sk) {
  const turns = sk.turns, n = turns.length;
  const step = Math.max(26, Math.min(60, 900 / Math.max(1, n)));
  const branches = [...new Set(turns.map((x) => x.branch))].sort((a, b) => a - b);
  const laneDepth = Object.fromEntries(branches.map((b) => [b, Math.max(...turns.filter((x) => x.branch === b).map((x) => x.depth))]));
  const laneTop = {};
  let y = 26;
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
  const used = [...new Set(sk.turns.map((x) => (x.role === "user" ? x.intent : BAD.has(x.intent) ? x.intent : "answer")))];
  const color = (k) => (k === "answer" ? cssVar("--i-assistant") : BAD.has(k) ? cssVar("--bad") : cssVar(`--i-${k}`));
  return h("div", { class: "legend" }, used.map((k) => h("span", {}, h("i", { style: `background:${color(k)}` }), T[lang].intents[k] || k)));
}

function download(sk) {
  const blob = new Blob([JSON.stringify(sk, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = h("a", { href: url, download: `pickaxetax-skeleton-${sk.id}.json` });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

let current = null; // { skeletons, index, origin }

function renderResult() {
  if (!current) return;
  const { skeletons, index, origin } = current;
  const sk = skeletons[index];
  const m = sk.metrics, w = m.waste;
  const out = $("result");
  out.replaceChildren();
  if (origin) out.append(h("p", { class: "note" }, t("from_page", { src: origin })));
  if (skeletons.length > 1) {
    out.append(h("div", { class: "card" }, h("h3", {}, t("multi", { n: skeletons.length })),
      h("div", { class: "chips" }, skeletons.map((o, i) => h("a", {
        class: "chip" + (i === index ? " main" : ""), href: "#",
        onclick: (ev) => { ev.preventDefault(); current.index = i; renderResult(); },
      }, `${o.agenda.slice(0, 2).join(" · ") || "#" + (i + 1)} (${o.metrics.savings_pct}%)`)))));
  }
  out.append(h("div", { class: "grid" },
    statCard(t("savings"), `${m.savings_pct}%`, t("savings_s"), true),
    statCard(t("compute"), `${fmt(m.compute_units)} → ${fmt(m.optimized_compute_units)}`, t("compute_s", { w: m.assumptions.input_weight })),
    statCard(t("billed"), fmt(m.billed_input_tokens), t("billed_s", { v: fmt(m.visible_tokens) })),
    statCard(t("oneshot"), `${m.one_shot_savings_pct}%`, t("oneshot_s")),
    statCard(t("energy"), `${m.energy_wh_avoidable} Wh`, t("energy_s", { f: m.assumptions.wh_per_1k_units })),
    co2Card(m.billed_input_tokens),
    statCard(t("shape"), `${m.user_turns}/${m.branches}/${m.max_depth}`, t("shape_s", { u: m.user_turns, b: m.branches, d: m.max_depth })),
  ));
  const rest = Math.max(0, Math.round((100 - w.ack_pct - w.superseded_pct - w.offtopic_context_pct) * 10) / 10);
  out.append(h("div", { class: "card" }, h("h3", {}, t("waste_title")), wasteBar([
    { label: t("w_ack"), v: w.ack_pct, c: cssVar("--i-ack") },
    { label: t("w_sup"), v: w.superseded_pct, c: cssVar("--bad") },
    { label: t("w_off"), v: w.offtopic_context_pct, c: cssVar("--warn") },
    { label: t("w_rest"), v: rest, c: cssVar("--accent") },
  ])));
  out.append(h("div", { class: "card" }, h("h3", {}, t("skeleton_title")), h("div", { class: "graph" }, skeletonSvg(sk)), intentLegend(sk), h("p", { class: "note" }, t("skeleton_note"))));
  out.append(h("div", { class: "card" }, h("h3", {}, t("agenda")), h("div", { class: "chips" }, sk.agenda.map((a, i) => h("span", { class: "chip" + (i < 3 ? " main" : "") }, a)))));
  const copyBtn = h("button", { class: "ghost", type: "button", onclick: async () => {
    try { await navigator.clipboard.writeText(sk.suggestion.prompt_template); copyBtn.textContent = t("copied"); } catch { /* clipboard blocked */ }
  } }, t("copy"));
  out.append(h("div", { class: "card" }, h("h3", {}, t("prompt_title")), h("pre", { class: "prompt" }, sk.suggestion.prompt_template), copyBtn));
  const tips = sk.suggestion.tips;
  out.append(h("div", { class: "card" }, h("h3", {}, t("tips_title")),
    tips.length ? h("ol", { class: "tips" }, tips.map((x) => h("li", {}, x[lang] || x.en))) : h("p", {}, t("tip_none"))));
  out.append(h("div", { class: "card actions" }, h("button", { class: "ghost", type: "button", onclick: () => download(sk) }, t("download"))));
  out.append(contributionCard(sk));
  out.hidden = false;
  out.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- contributions ----------
const contributed = {
  all() { try { return JSON.parse(store.get("pxt_contrib") || "{}"); } catch { return {}; } },
  get(id) { return this.all()[id]; },
  set(id, v) { const a = this.all(); if (v) a[id] = v; else delete a[id]; store.set("pxt_contrib", JSON.stringify(a)); },
};

function contributionCard(sk) {
  const labels = sk.agenda.slice(0, 5);
  let share = false;
  const pre = h("pre", { class: "payload" });
  const status = h("p", { class: "status", role: "status" });
  const payload = () => skeletonContribution(sk, { labels: share ? labels : [], version: ENGINE_VERSION });
  const refresh = () => { pre.textContent = JSON.stringify(payload(), null, 1); };
  const chips = h("div", { class: "chips" });
  const drawChips = () => chips.replaceChildren(...labels.map((l, i) => h("span", { class: "chip" }, l,
    h("button", { type: "button", "aria-label": "remove", onclick: () => { labels.splice(i, 1); drawChips(); refresh(); } }, "×"))));
  drawChips();
  const box = h("input", { type: "checkbox", onchange: (e) => { share = e.target.checked; refresh(); } });
  refresh();

  const say = (msg, cls = "") => { status.className = "status " + cls; status.textContent = msg; };
  const prior = contributed.get(sk.id);
  const anonBtn = h("button", { type: "button", disabled: !CONFIG.contribUrl || !!prior ? "" : null, onclick: async () => {
    const p = payload();
    const errs = validateContribution(p);
    if (errs.length) return say(errs.join("; "), "err");
    anonBtn.disabled = true;
    try {
      say(t("c_solving"));
      const ch = await (await fetch(CONFIG.contribUrl + "/challenge")).json();
      const nonce = await solvePow(ch.seed, ch.bits);
      const r = await fetch(CONFIG.contribUrl + "/contribute", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload: p, pow: { ...ch, nonce } }) });
      const res = await r.json();
      if (r.status !== 201) throw new Error(res.error || r.statusText);
      contributed.set(sk.id, { id: res.id, token: res.delete_token });
      say(t("c_thanks"), "ok");
      actions.append(undoBtn());
    } catch (e) {
      anonBtn.disabled = false;
      say(e.message, "err");
    }
  } }, t("c_anon"));
  const ghBtn = h("button", { type: "button", class: "ghost", onclick: async () => {
    const body = JSON.stringify(payload());
    const base = `https://github.com/${CONFIG.repo}/issues/new?template=contribution.yml&title=${encodeURIComponent("[contribution] skeleton")}`;
    let url = `${base}&payload=${encodeURIComponent(body)}`;
    if (url.length > 7500) {
      try { await navigator.clipboard.writeText(body); say(t("c_clip"), "ok"); } catch { /* clipboard blocked */ }
      url = base;
    }
    window.open(url, "_blank", "noopener");
  } }, t("c_github"));
  const undoBtn = () => h("button", { type: "button", class: "ghost", onclick: async (ev) => {
    const c = contributed.get(sk.id);
    if (!c) return;
    try {
      const r = await fetch(`${CONFIG.contribUrl}/contribute/${c.id}`, { method: "DELETE", headers: { "X-Delete-Token": c.token } });
      if (r.status !== 200) throw new Error((await r.json()).error || r.statusText);
      contributed.set(sk.id, null);
      ev.target.remove();
      anonBtn.disabled = !CONFIG.contribUrl;
      say(t("c_deleted"), "ok");
    } catch (e) { say(e.message, "err"); }
  } }, t("c_undo"));
  const actions = h("div", { class: "actions" }, anonBtn, ghBtn);
  if (prior && CONFIG.contribUrl) { actions.append(undoBtn()); say(t("c_done")); }
  else if (!CONFIG.contribUrl) say(t("c_off"));
  return h("div", { class: "card contrib" },
    h("h3", {}, t("c_title")), h("p", { class: "note" }, t("c_lede")),
    h("label", { class: "check" }, box, h("span", {}, t("c_labels"))), chips,
    h("details", {}, h("summary", {}, t("c_show")), pre),
    actions, status);
}

function renderImpact() {
  const a = window.PXT_AGGREGATE;
  if (!a || !a.contributions || !a.contributions.total) return;
  const stats = [];
  if (a.skeleton) {
    stats.push(statCard(t("i_convs"), fmt(a.skeleton.conversations)));
    stats.push(statCard(t("i_avoid"), `${a.skeleton.avoidable_pct}%`, null, true));
    stats.push(statCard(t("i_median"), `${a.skeleton.median_savings_pct}%`));
  }
  if (a.agent) stats.push(statCard(t("i_sessions"), fmt(a.agent.sessions)));
  stats.push(statCard(t("i_contrib", { v: fmt(a.contributions.verified) }), fmt(a.contributions.total)));
  $("impact-stats").replaceChildren(...stats);
  $("impact").querySelector("[data-i18n=impact_lede]").textContent = t("impact_lede", { k: a.topics ? a.topics.k : 3 });
  if (a.topics && a.topics.nodes.length) {
    $("impact-chips").replaceChildren(...a.topics.nodes.slice(0, 40).map((n) => h("span", { class: "chip" }, `${n.label} · ${n.count}`)));
    $("impact-topics").hidden = false;
  }
  $("impact").hidden = false;
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = !msg;
}

function run(fn, origin = null) {
  showError("");
  try {
    current = { skeletons: fn(), index: 0, origin };
    renderResult();
  } catch (e) {
    if (e instanceof LinkInput) {
      showError(t("link_detected"));
      $("link").scrollIntoView({ behavior: "smooth" });
    } else {
      showError(e.message);
    }
  }
}

// ---------- bookmarklet: runs on the share page, hands the conversation to this tab ----------
function pxtBookmarklet(SITE) {
  var q = function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); };
  var outer = function (els) { return els.filter(function (el) { return !els.some(function (o) { return o !== el && o.contains(el); }); }); };
  var txt = function (el) { return (el.innerText || el.textContent || "").trim(); };
  var turns = [];
  outer(q("[data-message-author-role]")).forEach(function (el) {
    var r = el.getAttribute("data-message-author-role");
    if (r === "user" || r === "assistant") turns.push({ role: r, text: txt(el) });
  });
  if (!turns.length) outer(q('[data-testid="user-message"], [data-testid="assistant-message"], .font-claude-message, .font-claude-response')).forEach(function (el) {
    turns.push({ role: el.matches('[data-testid="user-message"]') ? "user" : "assistant", text: txt(el) });
  });
  if (!turns.length) q("user-query, model-response").forEach(function (el) {
    turns.push({ role: el.tagName.toLowerCase() === "user-query" ? "user" : "assistant", text: txt(el) });
  });
  var payload = turns.length ? { v: 1, source: location.hostname, turns: turns } : { v: 1, source: location.hostname, text: txt(document.body) };
  var bytes = new TextEncoder().encode(JSON.stringify(payload)), bin = "";
  for (var i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  var b64 = btoa(bin);
  if (b64.length > 1500000) {
    alert("#AntiTokenMaxing: this conversation is too long to hand over by link. Select all (Ctrl/Cmd+A), copy, and paste it into the page instead.");
    window.open(SITE, "_blank");
    return;
  }
  // the #fragment is never sent to any server
  var url = SITE + "#pxt=" + b64;
  if (!window.open(url, "_blank")) location.href = url;
}

function setupBookmarklet() {
  const site = location.origin + location.pathname;
  const a = $("bookmarklet");
  a.href = "javascript:" + encodeURIComponent(`(${pxtBookmarklet.toString()})(${JSON.stringify(site)});void 0`);
  a.addEventListener("click", (ev) => { ev.preventDefault(); alert(t("drag_hint")); });
}

function receiveFromBookmarklet() {
  const m = location.hash.match(/^#pxt=([A-Za-z0-9+/=]+)$/);
  if (!m) return;
  history.replaceState(null, "", location.pathname + location.search); // drop the text from the URL right away
  try {
    const bin = atob(m[1]);
    const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    const origin = typeof payload.source === "string" ? payload.source.slice(0, 80) : null;
    if (Array.isArray(payload.turns) && payload.turns.length) run(() => analyzeTurns(payload.turns, origin || "page"), origin);
    else if (typeof payload.text === "string") run(() => analyzeInput(payload.text), origin);
  } catch {
    showError("Could not read the conversation handed over by the bookmark.");
  }
}

// ---------- form ----------
const SAMPLE = {
  en: "User: Why does my React useEffect run in an infinite loop?\nAssistant: An infinite loop happens when the dependency array contains an object or function that is recreated on every render, or when the effect updates state that is itself a dependency. Stabilize references with useCallback and useMemo.\nUser: Show me a useCallback dependency array example\nAssistant: Here is an example:\n```js\nconst fetchData = useCallback(() => api.get(id), [id]);\nuseEffect(() => { fetchData() }, [fetchData]);\n```\nUser: No, that's not what I asked, write it in TypeScript\nAssistant: You're right, here is the TypeScript version:\n```ts\nconst fetchData = useCallback((): void => { api.get(id) }, [id]);\n```\nUser: thanks!\nAssistant: You're welcome! Let me know if you have any other questions about React hooks.\nUser: How do I merge two pandas dataframes in Python?\nAssistant: Use pd.merge(df1, df2, on='key') to join on a key column, or concat to stack them.\nUser: thank you\nAssistant: Happy coding!",
  ko: "User: React에서 useEffect 무한 루프가 발생하는 이유를 알려줘\nAssistant: useEffect 무한 루프는 의존성 배열에 매 렌더마다 새로 생성되는 객체나 함수가 들어갈 때 발생합니다. 상태 업데이트가 effect 안에서 일어나고 그 상태가 의존성 배열에 있으면 렌더링이 반복됩니다. useCallback과 useMemo로 참조를 고정하세요.\nUser: useCallback 의존성 배열 예제 코드 보여줘\nAssistant: 다음은 예제입니다.\n```js\nconst fetchData = useCallback(() => api.get(id), [id]);\nuseEffect(() => { fetchData() }, [fetchData]);\n```\nUser: 아니 그게 아니라 TypeScript로 작성해줘\nAssistant: 죄송합니다. TypeScript 버전입니다.\n```ts\nconst fetchData = useCallback((): void => { api.get(id) }, [id]);\n```\nUser: 고마워\nAssistant: 천만에요! 더 궁금한 점이 있으면 언제든 물어보세요.\nUser: 그런데 파이썬 pandas 데이터프레임 병합 방법도 알려줘\nAssistant: pandas에서는 merge, join, concat을 사용합니다. pd.merge(df1, df2, on='key')처럼 키 기준으로 병합합니다.\nUser: 고마워요\nAssistant: 별말씀을요! 즐거운 코딩 되세요.",
};

$("form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const btn = $("go");
  btn.disabled = true;
  btn.textContent = t("analyzing");
  try {
    const file = $("file").files[0];
    const text = file ? (await file.text()).replace(/^﻿/, "") : $("input").value;
    run(() => analyzeInput(text));
  } finally {
    btn.disabled = false;
    btn.textContent = t("analyze");
  }
});
$("sample").addEventListener("click", () => { $("input").value = SAMPLE[lang]; $("file").value = ""; $("file-name").textContent = ""; });
$("file").addEventListener("change", () => { $("file-name").textContent = $("file").files[0]?.name || ""; });
$("lang").addEventListener("click", () => {
  lang = lang === "ko" ? "en" : "ko"; store.set("lang", lang); applyI18n(); renderResult(); renderImpact();
  document.dispatchEvent(new CustomEvent("pxt:lang", { detail: lang }));
});

applyI18n();
renderImpact();
setupBookmarklet();
receiveFromBookmarklet();
