// "The weight of a line": what re-reading costs in carbon, told with trees and twigs.
// Every number is computed here from carbon.js and the first survey (report/user01.html).
// The figures are estimates and the trees are metaphors; the section says so and cites
// each factor.

import { footprint, WH_PER_TOKEN, WH_PER_TOKEN_UPPER, G_CO2_PER_KWH, PHONE_CHARGE_WH, G_CO2_PER_G_WOOD, TREE_G_CO2, TREE_YEARS, SOURCES } from "./carbon.js";
import { observe } from "./motion.js";

const LINE_TOKENS = 427524; // median re-read per call in a long working session (user01)
const USER01_TOKENS = 5871292005; // user01, all Claude Code input, 2026-07-10 – 10-05
const CARRIED = 0.736; // share of context carried over from finished instructions (user01)
const RESEARCH = "https://github.com/graviton94/pickaxetax/blob/HEAD/research/carbon-factors.md";

const line = footprint(LINE_TOKENS);
const user = footprint(USER01_TOKENS);
const upper = footprint(USER01_TOKENS, WH_PER_TOKEN_UPPER);
const years = Math.round(user.tree_years);
const carriedYears = Math.round(years * CARRIED);

// "The cost": the world's receipt. Global figures are for AI and data centres as a whole;
// only the last line is our own measurement, and the section says so.
const DC_MT_2030 = 320; // IEA Energy and AI (2025): data-centre electricity CO2, 2030 peak, Base Case
const costTrees = (DC_MT_2030 * 1e12) / (TREE_G_CO2 / TREE_YEARS); // tree-years of absorption
const kg = Math.round(user.g_co2 / 1000);

const n1 = (x) => (Math.round(x * 10) / 10).toFixed(1);
const r = (x) => String(Math.round(x));

const COPY = {
  ko: {
    eyebrow1: "한 줄의 무게",
    title1: "“안녕하세요” 한 줄.",
    unit1: "g CO₂",
    lede1: `긴 작업 세션에서 이 한 줄에 답하려고 AI가 다시 읽는 ${LINE_TOKENS.toLocaleString("ko-KR")}토큰. 그 전력에서 나오는 탄소입니다.`,
    cards: [
      ["i-twig", `${r(line.twig_g)} g`, "마른 나뭇가지 하나를 태운 만큼"],
      ["i-hour", `${r(line.tree_hours)}시간`, "나무 한 그루가 꼬박 흡수해야 하는 시간"],
      ["i-bolt", `${r(line.wh)} Wh`, `스마트폰을 ${n1(line.phone_charges)}번 충전하는 전력`],
    ],
    eyebrow2: "쌓이면",
    title2a: "나무 한 그루의 ",
    title2b: `${years}년`,
    title2c: ".",
    lede2: `AI가 다시 읽은 58억 7천만 토큰. 탄소 ${kg} kg. 나무 한 그루가 ${years}년 동안 흡수해야 하는 양입니다.*`,
    foot2: "* 한 사용자가 석 달 동안 쓴 Claude Code 전체(영수증 No.01) 기준 추정입니다.",
    forestLabel: `나무 한 그루의 ${years}년. 그중 ${carriedYears}년은 이미 끝난 지시를 다시 읽는 데 쓰였습니다.`,
    key: "아이콘 하나 = 나무 한 그루의 1년",
    legendA: `이미 끝난 지시를 다시 읽는 데 쓴 몫 (73.6%) · ${carriedYears}년`,
    legendB: `나머지 · ${years - carriedYears}년`,
    upper: `캐시 할인 없이 계산하면 10배입니다. 나무 ${r(upper.trees_10y)}그루가 10년 동안 흡수할 양.`,
    punch: "그리고 이건, 단 한 사람입니다.",
    punchSub: "이제, 전 세계의 영수증입니다.",
    cta: "내 영수증 확인하기",
    cost: {
      eyebrow: "그 대가",
      title: "21세기 골드러시의 영수증.",
      lede: "곡괭이를 파는 쪽이 돈을 벌고, 영수증은 모두가 나눠 냅니다. 전기요금으로, 탄소로, 쓰레기로.",
      head: ["#ANTITOKENMAXING", "RECEIPT · 2026"],
      items: [
        ["데이터센터 투자", "빅테크 4사, 2026년 한 해", "7,000억 달러+", "1"],
        ["데이터센터 전력", "2030년 전망. 2024년의 2.3배, 오늘 일본 전체가 쓰는 전기보다 많습니다", "945 TWh", "2"],
        ["그 전력의 탄소", `2030년 정점 전망. 나무 ${Math.round(costTrees / 1e8)}억 그루가 1년 내내 흡수해야 하는 양 (비유)`, "3.2억 t CO₂", "2,5"],
        ["전자폐기물", "생성형 AI가 2020~2030년에 남길 수명 다한 GPU·서버, 누적 추정", "최대 500만 t", "3"],
        ["다시 쓰이지 않을 디지털 쓰레기", "매 호출이 다시 읽은 컨텍스트 중 이미 끝난 지시의 잔재. AI는 1,000토큰을 읽고 2~4토큰을 썼습니다", "73.6%", "4"],
      ],
      total: ["결제 수단", "지구"],
      stance: "AI를 반대하지 않습니다. 낭비를 반대합니다.",
      punch: "발전소를 더 짓기 전에,\n다시 읽기부터 멈추십시오.",
      notes: [
        ["CNBC (2026-07-22): Alphabet 2026년 설비투자 가이던스 1,950억~2,050억 달러. Sherwood News: 4사 합계 7,000억 달러 이상. AI 외 설비 포함.", "https://www.cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html", "https://sherwood.news/tech/alphabet-amazon-microsoft-meta-plan-more-than-700-billion-on-capex-this-year/"],
        ["IEA (2025), Energy and AI: 데이터센터 전력 2024년 415 TWh → 2030년 약 945 TWh. 그 전력의 CO₂ 약 1.8억 t → 2030년 약 3.2억 t 정점 (기준 시나리오).", "https://www.iea.org/reports/energy-and-ai/executive-summary"],
        ["Wang 외 (2024), Nature Computational Science: 생성형 AI 전자폐기물 2020~2030년 누적 120만~500만 t.", "https://www.nature.com/articles/s43588-024-00712-6"],
        ["영수증 No.01: 한 사용자의 석 달치 Claude Code 실측. 출력은 입력의 0.19~0.43%.", "report/user01.html"],
        ["나무 비유: 미국 EPA, 도시 묘목 한 그루가 1년에 CO₂ 6 kg 흡수(10년 60 kg)로 환산.", "https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references"],
      ],
      caveat: "각주 1~3은 AI와 데이터센터 전체의 수치이고, 각주 4는 한 사용자의 실측입니다. 73.6%를 전 세계 연산의 낭비율로 읽어서는 안 됩니다. 그 비율을 재는 것이 이 프로젝트가 하려는 일입니다.",
    },
    method: "어떻게 계산했나요? 추정이고, 일부는 비유입니다",
    chain: [
      `토큰당 전력 ${(WH_PER_TOKEN * 1000).toFixed(4)} mWh: Claude 3.7 Sonnet 긴 프롬프트(입력 1만·출력 1,500토큰) 측정치 5.671 Wh를 입력 1만 토큰으로 나누고, 캐시 읽기 요금 비율 0.1을 곱했습니다. [1][2]`,
      `전력 1 kWh당 CO₂ ${G_CO2_PER_KWH} g: 2024년 세계 평균입니다. [3]`,
      "나무 한 그루: 도시 묘목 한 그루가 10년 동안 흡수하는 CO₂ 60 kg. 하루 16.4 g, 한 시간 0.68 g입니다. [4]",
      `스마트폰 1회 충전 ${PHONE_CHARGE_WH} Wh [4] · 마른 나무 1 g을 태우면 CO₂ ${G_CO2_PER_G_WOOD.toFixed(2)} g [5]`,
      "비교하면, 구글이 공개한 Gemini 텍스트 프롬프트 중앙값은 0.24 Wh입니다. [6] 짧은 질문 하나 기준이고, 여기서 계산한 건 42만 토큰을 다시 읽는 호출 하나입니다.",
    ],
    caveat: "토큰당 전력은 어느 제공사도 공개하지 않아, 실제 값은 이보다 낮을 수도 높을 수도 있습니다. 요금을 연산량의 대리 지표로 쓴 것은 가정입니다. ‘나뭇가지’, ‘나무의 시간’은 1 g의 탄소를 떠올리게 하려는 비유이며, 상쇄량도 아니고 실제로 나무가 베였다는 뜻도 아닙니다.",
    full: "계산 전체와 한계 보기",
    bill: [`탄소 (추정) ${kg} kg CO₂`, `나무 한 그루의 ${years}년`],
  },
  en: {
    eyebrow1: "The weight of a line",
    title1: "One line: “Hello.”",
    unit1: "g CO₂",
    lede1: `In a long working session, answering that one line means re-reading ${LINE_TOKENS.toLocaleString("en-US")} tokens. This is the carbon from the electricity it takes.`,
    cards: [
      ["i-twig", `${r(line.twig_g)} g`, "of dry twig, burned"],
      ["i-hour", `${r(line.tree_hours)} hours`, "a tree needs to absorb it"],
      ["i-bolt", `${r(line.wh)} Wh`, `the power of ${n1(line.phone_charges)} smartphone charges`],
    ],
    eyebrow2: "Add it up",
    title2a: "",
    title2b: `${years} years`,
    title2c: " of a tree’s life.",
    lede2: `5.87 billion tokens re-read by AI. ${kg} kg of CO₂: what one tree absorbs in ${years} years.*`,
    foot2: "* All Claude Code use of one user over three months (Receipt No. 01). An estimate.",
    forestLabel: `${years} years of one tree. ${carriedYears} of them went to re-reading instructions that were already finished.`,
    key: "Each icon = one year of one tree",
    legendA: `Re-reading finished instructions (73.6%) · ${carriedYears} years`,
    legendB: `Everything else · ${years - carriedYears} years`,
    upper: `Without the cache discount it is ten times this: what ${r(upper.trees_10y)} trees absorb in ten years.`,
    punch: "And that is just one person.",
    punchSub: "Now, the world’s receipt.",
    cta: "Check your own receipt",
    cost: {
      eyebrow: "The cost",
      title: "The receipt of the 21st-century gold rush.",
      lede: "The ones selling pickaxes get rich. Everyone splits the receipt: in power bills, in carbon, in waste.",
      head: ["#ANTITOKENMAXING", "RECEIPT · 2026"],
      items: [
        ["Data-center capex", "Big Tech’s four, in 2026 alone", "$700B+", "1"],
        ["Data-center electricity", "2030 outlook. 2.3× 2024, more than all of Japan uses today", "945 TWh", "2"],
        ["Its carbon", `2030 peak outlook. What ${Math.round(costTrees / 1e9)} billion trees absorb in a whole year (metaphor)`, "320 Mt CO₂", "2,5"],
        ["E-waste", "GPUs and servers retired by generative AI, 2020–2030, cumulative estimate", "up to 5 Mt", "3"],
        ["Digital waste, never used again", "Context re-read on every call that was left over from finished instructions. The AI read 1,000 tokens to write 2–4", "73.6%", "4"],
      ],
      total: ["Paid by", "Earth"],
      stance: "We are not against AI. We are against waste.",
      punch: "Before building more power plants,\nstop the re-reading.",
      notes: [
        ["CNBC (2026-07-22): Alphabet guides 2026 capex to $195–205B. Sherwood News: the four combined, more than $700B. Includes non-AI capex.", "https://www.cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html", "https://sherwood.news/tech/alphabet-amazon-microsoft-meta-plan-more-than-700-billion-on-capex-this-year/"],
        ["IEA (2025), Energy and AI: data-centre electricity 415 TWh in 2024 → about 945 TWh in 2030; its CO₂ about 180 Mt → a peak of about 320 Mt in 2030 (Base Case).", "https://www.iea.org/reports/energy-and-ai/executive-summary"],
        ["Wang et al. (2024), Nature Computational Science: generative-AI e-waste of 1.2–5.0 Mt accumulated over 2020–2030.", "https://www.nature.com/articles/s43588-024-00712-6"],
        ["Receipt No. 01: one user’s three months of Claude Code, measured. Output was 0.19–0.43% of input.", "report/user01.html"],
        ["Tree metaphor: US EPA, one urban seedling absorbs 6 kg of CO₂ a year (60 kg in 10 years).", "https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references"],
      ],
      caveat: "Notes 1–3 cover AI and data centres as a whole; note 4 is one user’s measurement. 73.6% is not the waste rate of the world’s compute. Measuring that rate is what this project is for.",
    },
    method: "How did we compute this? It is an estimate, and partly a metaphor",
    chain: [
      `Energy per token, ${(WH_PER_TOKEN * 1000).toFixed(4)} mWh: the measured 5.671 Wh for a long Claude 3.7 Sonnet prompt (10k input, 1.5k output tokens), divided by its 10k input tokens, times the cache-read price ratio of 0.1. [1][2]`,
      `${G_CO2_PER_KWH} g of CO₂ per kWh: the 2024 world average. [3]`,
      "One tree: an urban seedling absorbs 60 kg of CO₂ over 10 years. That is 16.4 g a day, 0.68 g an hour. [4]",
      `One smartphone charge, ${PHONE_CHARGE_WH} Wh [4] · burning 1 g of dry wood releases ${G_CO2_PER_G_WOOD.toFixed(2)} g of CO₂ [5]`,
      "For comparison, Google reports 0.24 Wh for the median Gemini text prompt. [6] That is one short question; here it is one call that re-reads 427K tokens.",
    ],
    caveat: "No provider publishes energy per token, so the real figure may be lower or higher. Using price as a proxy for compute is an assumption. The twig and the tree’s hours are metaphors to make a gram of carbon imaginable: they are not offsets, and no tree was cut down.",
    full: "Full calculation and limits",
    bill: [`Carbon (est.) ${kg} kg CO₂`, `${years} years of a tree`],
  },
};

const $ = (id) => document.getElementById(id);
const lang = () => (document.documentElement.lang === "ko" ? "ko" : "en");
const SVGNS = "http://www.w3.org/2000/svg";

function el(tag, cls, ...kids) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  for (const k of kids) if (k != null) e.append(k);
  return e;
}
function icon(id, cls) {
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("class", cls);
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(SVGNS, "use");
  use.setAttribute("href", `#${id}`);
  svg.append(use);
  return svg;
}
function counted(text, cls) {
  const s = el("span", cls, text);
  s.dataset.count = text;
  return s;
}

function forest(c) {
  const box = el("div", "forest");
  box.setAttribute("role", "img");
  box.setAttribute("aria-label", c.forestLabel);
  box.dataset.stagger = "";
  for (let i = 0; i < years; i++) {
    const t = icon("i-tree", "tree" + (i < carriedYears ? " spent" : ""));
    // a sapling grows into a tree across the years
    t.style.setProperty("--s", (0.42 + 0.58 * Math.sqrt((i + 1) / years)).toFixed(3));
    box.append(t);
  }
  return box;
}

function render() {
  const c = COPY[lang()];
  const sec = $("weight");
  if (!sec) return;
  const one = el("div", "scene",
    el("p", "eyebrow", c.eyebrow1),
    el("h2", "display", c.title1),
    el("p", "mega", counted(n1(line.g_co2), "mega-n grad-warn"), el("span", "mega-u", c.unit1)),
    el("p", "scene-lede", c.lede1),
    el("div", "equiv", ...c.cards.map(([ic, v, t]) => el("article", "eq", icon(ic, "eq-ic"), el("b", null, v), el("p", null, t)))),
  );
  one.querySelector(".equiv").dataset.stagger = "";
  one.querySelector("h2").id = "weight-title";
  const two = el("div", "scene",
    el("p", "eyebrow", c.eyebrow2),
    el("h2", "display", c.title2a ? el("span", "nowrap", c.title2a) : null, el("span", "grad-green", c.title2b), c.title2c),
    el("p", "scene-lede", c.lede2),
    forest(c),
    el("div", "forest-legend",
      el("span", "lg spent", c.legendA), el("span", "lg", c.legendB), el("span", "lg-key", c.key)),
    el("p", "scene-note", c.upper),
    el("p", "scene-note", c.foot2),
  );
  const three = el("div", "scene scene-punch", el("p", "punch", c.punch), el("p", "punch-sub", c.punchSub));
  const method = el("details", "method");
  const src = el("ol", "sources");
  SOURCES.forEach((s) => {
    const a = el("a", null, s.label);
    a.href = s.url;
    a.rel = "noopener";
    src.append(el("li", null, a));
  });
  const full = el("a", null, c.full);
  full.href = RESEARCH;
  method.append(el("summary", null, c.method), el("ul", "chain", ...c.chain.map((x) => el("li", null, x))),
    el("p", "caveat", c.caveat), src, el("p", "full", full));
  [one, two, three].forEach((s) => s.setAttribute("data-reveal", ""));
  sec.replaceChildren(one, two, three, el("div", "scene scene-method", method));
  const bill = $("bill-carbon");
  if (bill) bill.replaceChildren(icon("i-tree", "bill-tree"), el("b", null, c.bill[0]), el("span", null, c.bill[1]));
  observe(sec);
  renderCost(c);
}

function link(text, href) {
  const a = el("a", null, text);
  a.href = href;
  if (href.startsWith("http")) a.rel = "noopener";
  return a;
}

function renderCost(c) {
  const sec = $("cost");
  if (!sec) return;
  const k = c.cost;
  const items = el("ul", "rc-items", ...k.items.map(([label, sub, value, note]) =>
    el("li", "rc-item", el("div", "rc-l", el("b", null, label), el("span", null, sub)),
      el("div", "rc-v", value, el("sup", null, note)))));
  items.dataset.stagger = "";
  const bar = el("div", "rc-barcode");
  bar.setAttribute("aria-hidden", "true");
  const receipt = el("div", "receipt",
    el("div", "rc-head", el("span", null, k.head[0]), el("span", null, k.head[1])),
    items,
    el("div", "rc-total", el("span", null, k.total[0]), el("b", null, k.total[1])),
    el("p", "rc-stance", k.stance), bar);
  const notes = el("ol", "rc-notes", ...k.notes.map(([text, ...urls]) =>
    el("li", null, text, ...urls.map((u) => [" ", link("↗", u)]).flat())));
  const scene = el("div", "scene scene-cost",
    el("p", "eyebrow", k.eyebrow), el("h2", "display", k.title), el("p", "scene-lede", k.lede), receipt);
  scene.querySelector("h2").id = "cost-title";
  const close = el("div", "scene scene-punch", el("p", "punch", k.punch), link(c.cta, "#check"));
  close.querySelector("a").className = "btn btn-lg";
  const foot = el("div", "scene scene-method", el("div", "rc-foot", notes, el("p", "caveat", k.caveat)));
  [scene, close].forEach((x) => x.setAttribute("data-reveal", ""));
  sec.replaceChildren(scene, close, foot);
  observe(sec);
}

document.addEventListener("pxt:lang", render);
render();
