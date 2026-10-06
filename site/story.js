// "The weight of a line": what re-reading costs in carbon, told with trees and twigs.
// Every number is computed here from carbon.js and the first survey (report/user01.html).
// The figures are estimates and the trees are metaphors; the section says so and cites
// each factor.

import { footprint, WH_PER_TOKEN, WH_PER_TOKEN_UPPER, G_CO2_PER_KWH, PHONE_CHARGE_WH, G_CO2_PER_G_WOOD, SOURCES } from "./carbon.js";
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
    eyebrow2: "석 달, 한 사람",
    title2a: "나무 한 그루의 ",
    title2b: `${years}년`,
    title2c: ".",
    lede2: `이 프로젝트를 만든 사람이 석 달 동안 Claude Code에 다시 읽힌 토큰은 58억 7천만. 탄소로 ${r(user.g_co2 / 1000)} kg, 나무 한 그루가 ${years}년 동안 흡수해야 하는 양입니다.`,
    forestLabel: `나무 한 그루의 ${years}년. 그중 ${carriedYears}년은 이미 끝난 지시를 다시 읽는 데 쓰였습니다.`,
    key: "아이콘 하나 = 나무 한 그루의 1년",
    legendA: `이미 끝난 지시를 다시 읽는 데 쓴 몫 (73.6%) · ${carriedYears}년`,
    legendB: `나머지 · ${years - carriedYears}년`,
    upper: `캐시 할인 없이 계산하면 10배입니다. 나무 ${r(upper.trees_10y)}그루가 10년 동안 흡수할 양.`,
    punch: "그리고 이건, 한 사람입니다.",
    cta: "내 대화 재 보기",
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
    bill: [`탄소 (추정) ${r(user.g_co2 / 1000)} kg CO₂`, `나무 한 그루의 ${years}년`],
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
    eyebrow2: "One person, three months",
    title2a: "",
    title2b: `${years} years`,
    title2c: " of a tree’s life.",
    lede2: `The person who started this project had Claude Code re-read 5.87 billion tokens in three months. That is ${r(user.g_co2 / 1000)} kg of CO₂: what one tree absorbs in ${years} years.`,
    forestLabel: `${years} years of one tree. ${carriedYears} of them went to re-reading instructions that were already finished.`,
    key: "Each icon = one year of one tree",
    legendA: `Re-reading finished instructions (73.6%) · ${carriedYears} years`,
    legendB: `Everything else · ${years - carriedYears} years`,
    upper: `Without the cache discount it is ten times this: what ${r(upper.trees_10y)} trees absorb in ten years.`,
    punch: "And that is one person.",
    cta: "Measure my conversation",
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
    bill: [`Carbon (est.) ${r(user.g_co2 / 1000)} kg CO₂`, `${years} years of a tree`],
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
  );
  const three = el("div", "scene scene-punch", el("p", "punch", c.punch), (() => {
    const a = el("a", "btn btn-lg", c.cta);
    a.href = "#check";
    return a;
  })());
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
}

document.addEventListener("pxt:lang", render);
render();
