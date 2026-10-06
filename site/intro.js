// Opening scene: a chat window types "Hello", sends it, and the assistant answers
// with what that one line actually costs. Every number is a measurement from the
// first survey report (report/user01.html); the carbon line is an estimate from
// carbon.js, labelled as such. No network, no inline script (CSP).

import { footprint } from "./carbon.js";

const COPY = {
  ko: {
    typed: "안녕하세요",
    reading: "지금까지의 대화를 처음부터 다시 읽는 중",
    tokens: "토큰",
    lines: [
      "안녕하세요, 사용자님.",
      "방금 보내신 다섯 글자에 답하려고, 저는 이 대화를 처음부터 끝까지 다시 읽었습니다. 427,524토큰입니다.",
      "그 한 줄로, 나무 한 그루가 {h}시간 동안 들이마셔야 할 탄소가 나왔습니다. 마른 나뭇가지 하나를 태운 만큼입니다.",
      "그리고 제가 다시 읽은 것의 4분의 3은, 이미 끝난 대화였습니다.",
      "당신의 대화는 얼마나 다시 읽혔을까요?",
    ],
    carbon: "≈ {g} g CO₂ · 나무 한 그루의 {h}시간 (추정)",
    footnote: "427,524토큰: 긴 작업 세션에서 호출 한 번이 다시 읽은 양의 중앙값. 4분의 3(76.1%): 매 호출의 컨텍스트 가운데 이미 끝난 지시가 남긴 비중. 둘 다 한 사용자의 석 달치 Claude Code 실측(영수증 No.01)입니다. 탄소와 나무는 공개 측정값과 공식 계수로 낸 추정이자 비유이며, 계산과 출처는 아래 ‘한 줄의 무게’에 있습니다.",
    cta1: "내 대화 진단하기",
    cta2: "한 줄의 무게",
    replay: "다시 보기",
    skip: "건너뛰기",
    placeholder: "메시지를 입력하세요",
    you: "나",
  },
  en: {
    typed: "Hello",
    reading: "Re-reading the whole conversation from the start",
    tokens: "tokens",
    lines: [
      "Hello.",
      "To answer those five letters, I just re-read this entire conversation from the very beginning. That was 427,524 tokens.",
      "That one line released the carbon a tree needs {h} hours to breathe in. About what burning a dry twig gives off.",
      "And three quarters of what I re-read was conversation that was already over.",
      "How much of your conversation gets re-read?",
    ],
    carbon: "≈ {g} g CO₂ · {h} hours of a tree (est.)",
    footnote: "427,524 tokens: the median re-read per call in a long working session. Three quarters (76.1%): the share of each call’s context left over from instructions already finished. Both measured from one user’s three months of Claude Code (Receipt No. 01). Carbon and trees are estimates and metaphors built from published measurements and official factors; the calculation and sources are below, in “The weight of a line”.",
    cta1: "Check my conversation",
    cta2: "The weight of a line",
    replay: "Replay",
    skip: "Skip",
    placeholder: "Message",
    you: "You",
  },
};
const TOKENS = 427524;
const LINE = footprint(TOKENS);
const VARS = { h: String(Math.round(LINE.tree_hours)), g: (Math.round(LINE.g_co2 * 10) / 10).toFixed(1) };
const subst = (text) => text.replace(/\{(\w)\}/g, (_, k) => VARS[k]);

const $ = (id) => document.getElementById(id);
const reduce = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const lang = () => (document.documentElement.lang === "ko" ? "ko" : "en");
let run = 0; // bumping this cancels a running sequence

const sleep = (ms, id) => new Promise((ok, no) => setTimeout(() => (id === run ? ok() : no(new Error("cancelled"))), ms));

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function userBubble(c) {
  const row = el("div", "msg msg-user");
  row.append(el("div", "bubble", c.typed));
  return row;
}

function assistantBubble() {
  const row = el("div", "msg msg-ai");
  const mark = el("div", "avatar");
  mark.setAttribute("aria-hidden", "true");
  mark.textContent = "⛏";
  const body = el("div", "ai-body");
  row.append(mark, body);
  return { row, body };
}

function counter(c) {
  const box = el("div", "reading");
  const label = el("div", "reading-label", c.reading);
  const num = el("div", "reading-num");
  const n = el("span", "n", "0");
  num.append(n, el("span", "u", " " + c.tokens));
  const bar = el("div", "reading-bar");
  const fill = el("i");
  bar.append(fill);
  const co2 = el("div", "reading-co2", subst(c.carbon));
  box.append(label, num, bar, co2);
  return { box, n, fill, label };
}

function cta(c) {
  const row = el("div", "intro-cta");
  const a = el("a", "btn", c.cta1);
  a.href = "#analyze";
  const b = el("a", "btn ghost-btn", c.cta2);
  b.href = "#weight";
  row.append(a, b);
  return row;
}

// the carbon line is the punch; the last line is the question
function lineClass(c, i) {
  return i === c.lines.length - 1 ? "ask" : i === 2 ? "hit" : "";
}

function fmt(n, l) {
  return n.toLocaleString(l === "ko" ? "ko-KR" : "en-US");
}

// final, static state: used for reduced motion, "skip", and language changes
function renderFinal() {
  run++;
  const c = COPY[lang()];
  const log = $("chat-log");
  log.replaceChildren(userBubble(c));
  const { row, body } = assistantBubble();
  const k = counter(c);
  k.n.textContent = fmt(TOKENS, lang());
  k.fill.style.transform = "scaleX(1)";
  k.box.classList.add("done");
  body.append(k.box);
  c.lines.forEach((line, i) => body.append(el("p", lineClass(c, i), subst(line))));
  body.append(cta(c), el("p", "foot", c.footnote));
  log.append(row);
  $("composer-text").textContent = "";
  $("composer-text").dataset.placeholder = c.placeholder;
  $("intro-skip").hidden = true;
  $("intro-replay").hidden = false;
  $("intro-replay").textContent = c.replay;
}

async function play() {
  const id = ++run;
  const l = lang();
  const c = COPY[l];
  const log = $("chat-log");
  const text = $("composer-text");
  const send = $("composer-send");
  log.replaceChildren();
  text.textContent = "";
  text.dataset.placeholder = c.placeholder;
  $("intro-skip").hidden = false;
  $("intro-skip").textContent = c.skip;
  $("intro-replay").hidden = true;
  try {
    await sleep(700, id);
    text.classList.add("typing");
    for (const ch of c.typed) {
      text.textContent += ch;
      await sleep(l === "ko" ? 170 : 120, id);
    }
    await sleep(450, id);
    send.classList.add("pressed");
    await sleep(160, id);
    send.classList.remove("pressed");
    text.classList.remove("typing");
    text.textContent = "";
    log.append(userBubble(c));
    await sleep(500, id);
    const { row, body } = assistantBubble();
    const k = counter(c);
    body.append(k.box);
    log.append(row);
    const t0 = performance.now();
    const dur = 1900;
    await new Promise((ok, no) => {
      const tick = (t) => {
        if (id !== run) return no(new Error("cancelled"));
        const p = Math.min(1, (t - t0) / dur);
        const e = 1 - Math.pow(1 - p, 3);
        k.n.textContent = fmt(Math.round(TOKENS * e), l);
        k.fill.style.transform = `scaleX(${e})`;
        if (p < 1) requestAnimationFrame(tick); else ok();
      };
      requestAnimationFrame(tick);
    });
    k.box.classList.add("done");
    await sleep(300, id);
    for (let i = 0; i < c.lines.length; i++) {
      const p = el("p", lineClass(c, i));
      body.append(p);
      const words = subst(c.lines[i]).split(/(\s+)/);
      for (const w of words) {
        p.textContent += w;
        if (w.trim()) await sleep(l === "ko" ? 70 : 45, id);
      }
      await sleep(380, id);
    }
    body.append(cta(c), el("p", "foot", c.footnote));
    $("intro-skip").hidden = true;
    $("intro-replay").hidden = false;
    $("intro-replay").textContent = c.replay;
  } catch {
    /* a newer run took over */
  }
}

function start() {
  if (!$("intro")) return;
  $("intro-skip").addEventListener("click", renderFinal);
  $("intro-replay").addEventListener("click", play);
  document.addEventListener("pxt:lang", () => renderFinal());
  if (reduce()) renderFinal(); else play();
}

start();
