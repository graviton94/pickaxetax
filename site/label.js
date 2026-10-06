// Blind labeling under the waste codebook v1 (research/protocol/waste-codebook-v1.md, §5).
// The packet is read from a local file and never leaves this tab (CSP connect-src 'none').
// Labels autosave in this browser and are exported as a file holding ids and choices only.

const CATS = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"];
const CHOICES = ["yes", "no", "unsure"];
const OUTCOMES = ["met", "partial", "not_met", "unsure"];

const T = {
  ko: {
    title: "판정 도구",
    setup_h: "낭비 판정 · 블라인드 라벨링",
    setup_lede: "데이터 주인에게 받은 판정 꾸러미를 불러와, 지시마다 여덟 갈래의 낭비가 있었는지 판정합니다. 다른 판정자의 결과나 기계 판정은 보이지 않습니다. 끝나면 판정 파일을 내려받아 데이터 주인에게 돌려주세요.",
    step1: "판정 꾸러미 파일",
    step2: "판정자 코드 (예: A, B)",
    step3: "단계",
    phase_cal: "연습 (먼저, 끝나면 해석 차이를 맞춥니다)",
    phase_main: "본 판정",
    start: "시작",
    privacy: "🔒 꾸러미는 이 탭 밖으로 나가지 않습니다. 진행 상황은 이 브라우저에만 저장됩니다.",
    bad_packet: "판정 꾸러미 파일이 아닙니다.",
    need_coder: "판정자 코드를 적어 주세요.",
    prev: "이전", next: "다음", next_open: "안 한 항목으로", export: "판정 파일 내려받기",
    progress: "{d} / {n} 판정", instr: "지시", steps: "에이전트가 한 일", final: "마지막 응답",
    no_steps: "도구를 쓰지 않았습니다.", no_final: "(텍스트 응답 없음)",
    meta: "{session} · {index}번째 지시 · 호출 {calls}회 · 입력 {input} 토큰 · 출력 {output} · 오류 {errors} · 하위 에이전트 {subagents}",
    judge_h: "이 지시에서 낭비가 있었나요?",
    judge_lede: "갈래마다 고르세요. 판단할 근거가 화면에 없으면 '모름'입니다. 겹치면 위쪽 갈래에만 표시합니다.",
    yes: "있음", no: "없음", unsure: "모름",
    outcome_h: "결과가 요청을 충족했나요?",
    met: "충족", partial: "일부", not_met: "못 함",
    note: "메모 (선택, 판정 파일에 함께 저장됩니다. 원문을 옮겨 적지 마세요)",
    guide: "판정 기준 v1 전체 보기",
    done: "모든 항목을 판정했습니다. 판정 파일을 내려받아 데이터 주인에게 보내 주세요.",
  },
  en: {
    title: "Labeling",
    setup_h: "Judging waste · blind labeling",
    setup_lede: "Load the packet the data owner gave you and judge, for each instruction, whether each of the eight kinds of waste happened. You will not see other labelers' answers or any machine judgment. When done, download your labels file and send it back to the data owner.",
    step1: "Labeling packet file",
    step2: "Your coder code (e.g. A, B)",
    step3: "Phase",
    phase_cal: "Practice (first; differences are discussed afterwards)",
    phase_main: "Main labeling",
    start: "Start",
    privacy: "🔒 The packet never leaves this tab. Progress is saved in this browser only.",
    bad_packet: "This is not a labeling packet.",
    need_coder: "Enter your coder code.",
    prev: "Previous", next: "Next", next_open: "Next unanswered", export: "Download labels file",
    progress: "{d} / {n} labeled", instr: "Instruction", steps: "What the agent did", final: "Last reply",
    no_steps: "No tools were used.", no_final: "(no text reply)",
    meta: "{session} · instruction {index} · {calls} calls · {input} input tokens · {output} output · {errors} errors · {subagents} sub-agents",
    judge_h: "Was there waste in this instruction?",
    judge_lede: "Choose for each category. If the screen gives no basis to judge, choose 'Unsure'. When categories overlap, mark only the higher one.",
    yes: "Yes", no: "No", unsure: "Unsure",
    outcome_h: "Did the result meet the request?",
    met: "Met", partial: "Partly", not_met: "Not met",
    note: "Note (optional; saved in the labels file. Do not copy conversation text into it)",
    guide: "Show the full codebook v1",
    done: "Every item is labeled. Download the labels file and send it to the data owner.",
  },
};

// short definitions shown next to each choice, and the longer guide
const DEF = {
  ko: {
    W1: ["반복", "같은 일을 같은 결과로 다시 했다. 안 바뀐 파일을 또 읽기, 같은 자료를 다시 가져오기."],
    W2: ["실패·재시도", "오류나 중단된 호출, 같은 실패의 반복, 복구하려고 맥락을 다시 읽은 것."],
    W3: ["조율 손실", "지시가 엉뚱한 곳에 전달됨, 위임이 거절·포기됨, 아무도 안 읽은 하위 작업, 변화 없는 확인 반복."],
    W4: ["버려진 결과물", "쓰이기 전에 지워지거나 통째로 바뀐 파일·초안, 사용자가 거부한 답."],
    W5: ["묵은 맥락", "끝난 지시에서 넘어와 이 지시에서 쓰이지 않은 맥락. 인용하지 않았어도 지켜진 제약은 '쓰인' 것입니다."],
    W6: ["캐시 재작성", "재개·모델 전환·만료로 같은 앞부분을 캐시에 다시 쓴 비용. 화면에 근거가 없으면 '모름'."],
    W7: ["요청 밖 작업", "요청하지 않았고 쓰이지도 않은 작업."],
    W8: ["과잉 탐색", "결과에 반영되지 않은 읽기·검색. 하위 에이전트의 탐색도 포함합니다. 결과가 기댄 탐색은 낭비가 아닙니다."],
  },
  en: {
    W1: ["Duplication", "The same work redone with the same result: reading an unchanged file again, fetching the same data again."],
    W2: ["Failure and retry", "Errored or aborted calls, repeated identical failures, context re-read to recover."],
    W3: ["Coordination loss", "A hand-off sent to the wrong place, refused or abandoned delegation, sub-agent output nobody read, polling with no change."],
    W4: ["Discarded output", "Files or drafts deleted or replaced wholesale before use, answers the user rejected."],
    W5: ["Stale context", "Context carried over from a finished instruction and not used in this one. A constraint that was obeyed counts as used, even if never quoted."],
    W6: ["Cache churn", "Re-writing the same prefix to the cache after a resume, model switch or expiry. Choose 'Unsure' if the screen gives no basis."],
    W7: ["Unrequested work", "Work nobody asked for and nobody used."],
    W8: ["Over-exploration", "Reads and searches the result did not draw on, sub-agents included. Exploration the result used is not waste."],
  },
};
const GUIDE = {
  ko: ["낭비는 '결과를 바꾸지 않고 뺄 수 있었던 토큰'입니다.",
    "낭비가 아닌 것: 매 호출의 기본 설정, 결과에 반영된 탐색, 테스트 같은 검증.",
    "겹치면 위쪽 갈래(W1이 가장 위)에만 '있음'을 표시합니다.",
    "판단할 근거가 화면에 없으면 추측하지 말고 '모름'을 고릅니다. '모름'도 결과로 셉니다.",
    "판정은 다른 사람과 상의하지 않고 혼자 합니다. 연습이 끝난 뒤에만 해석 차이를 맞춥니다."],
  en: ["Waste is tokens that could have been removed without changing the result.",
    "Not waste: the base every call needs, exploration the result used, verification such as tests.",
    "When categories overlap, mark 'Yes' only on the higher one (W1 is highest).",
    "If the screen gives no basis to judge, do not guess: choose 'Unsure'. 'Unsure' counts as an answer.",
    "Label alone, without discussing items. Differences are discussed only after the practice round."],
};

const $ = (id) => document.getElementById(id);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};
let lang = store.get("lang") || ((navigator.language || "ko").startsWith("ko") ? "ko" : "en");
const t = (k, vars = {}) => String(T[lang][k] ?? k).replace(/\{(\w+)\}/g, (_, x) => vars[x] ?? "");
const fmt = (n) => Number(n || 0).toLocaleString(lang === "ko" ? "ko-KR" : "en-US");

let packet = null;
let state = null; // { coder, phase, order: [ids], pos, labels: {id: {...}} }

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-t]").forEach((e) => { e.textContent = t(e.dataset.t); });
  $("lang").textContent = lang === "ko" ? "EN" : "한국어";
  buildForm();
  if (state) render();
}

// deterministic shuffle: each coder and phase gets its own order
function seeded(str) {
  let h = 2166136261;
  for (const c of str) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
  return () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 1e9) / 1e9; };
}
function shuffled(ids, key) {
  const r = seeded(key), a = ids.slice();
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

function items() { return state.phase === "main" ? packet.items : packet.calibration; }
function byId() { return Object.fromEntries(items().map((x) => [x.id, x])); }
const key = () => `pxt-labels:${packet.sha256}:${state.coder}:${state.phase}`;
const save = () => store.set(key(), JSON.stringify(state));
const complete = (l) => l && CATS.every((c) => l[c]) && l.outcome;

function buildForm() {
  const box = $("cats");
  box.replaceChildren();
  for (const c of CATS) {
    const fs = el("fieldset", "lb-cat");
    const lg = el("legend");
    lg.append(el("b", null, `${c} ${DEF[lang][c][0]}`));
    fs.append(lg, el("p", "lb-def", DEF[lang][c][1]));
    const row = el("div", "lb-choices");
    for (const v of CHOICES) {
      const lab = el("label", "lb-choice");
      const inp = document.createElement("input");
      inp.type = "radio"; inp.name = c; inp.value = v; inp.id = `${c}-${v}`;
      inp.addEventListener("change", () => setLabel(c, v));
      lab.append(inp, el("span", null, t(v)));
      row.append(lab);
    }
    fs.append(row);
    box.append(fs);
  }
  const oc = $("outcome");
  oc.replaceChildren();
  for (const v of OUTCOMES) {
    const lab = el("label", "lb-choice");
    const inp = document.createElement("input");
    inp.type = "radio"; inp.name = "outcome"; inp.value = v; inp.id = `outcome-${v}`;
    inp.addEventListener("change", () => setLabel("outcome", v));
    lab.append(inp, el("span", null, t(v === "unsure" ? "unsure" : v)));
    oc.append(lab);
  }
  const g = $("guide");
  g.replaceChildren(el("ul", null));
  GUIDE[lang].forEach((x) => g.firstChild.append(el("li", null, x)));
  CATS.forEach((c) => g.firstChild.append(el("li", null, `${c} ${DEF[lang][c][0]}: ${DEF[lang][c][1]}`)));
}

function setLabel(field, value) {
  const id = state.order[state.pos];
  state.labels[id] = { ...(state.labels[id] || {}), [field]: value };
  save();
  progress();
}

function progress() {
  const n = state.order.length;
  const d = state.order.filter((id) => complete(state.labels[id])).length;
  $("progress-text").textContent = d === n ? t("done") : t("progress", { d, n });
  $("meter").style.width = `${(100 * d) / n}%`;
  $("export").classList.toggle("lb-ready", d === n);
}

function render() {
  const it = byId()[state.order[state.pos]];
  $("item-meta").textContent = `#${state.pos + 1} · ` + t("meta", { session: it.session, index: it.index + 1, calls: fmt(it.stats.calls),
    input: fmt(it.stats.input), output: fmt(it.stats.output), errors: it.stats.errors, subagents: it.stats.subagents });
  $("item-instruction").textContent = it.instruction;
  const ol = $("item-steps");
  ol.replaceChildren();
  if (!it.steps.length) ol.append(el("li", "muted", t("no_steps")));
  for (const s of it.steps) {
    const li = el("li", s.error ? "lb-err" : "");
    li.append(el("b", null, s.tool), document.createTextNode(s.target ? ` ${s.target}` : ""));
    if (s.result_chars != null) li.append(el("span", "lb-size", ` · ${fmt(s.result_chars)}${lang === "ko" ? "자" : " chars"}`));
    if (s.error) li.append(el("span", "lb-size", lang === "ko" ? " · 오류" : " · error"));
    ol.append(li);
  }
  $("item-final").textContent = it.final || t("no_final");
  const l = state.labels[it.id] || {};
  for (const c of [...CATS, "outcome"]) {
    document.querySelectorAll(`input[name="${c}"]`).forEach((r) => { r.checked = r.value === l[c]; });
  }
  $("note").value = l.note || "";
  $("prev").disabled = state.pos === 0;
  $("next").disabled = state.pos === state.order.length - 1;
  progress();
  save();
}

function go(pos) { state.pos = Math.max(0, Math.min(state.order.length - 1, pos)); render(); window.scrollTo({ top: 0 }); }

function exportLabels() {
  const labels = {};
  for (const id of state.order) if (state.labels[id]) labels[id] = state.labels[id];
  const out = { schema: "pickaxetax.labels.v1", codebook: packet.codebook, packet: packet.sha256, phase: state.phase,
    coder: state.coder, exported: new Date().toISOString(), items: state.order.length, labels };
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = el("a");
  a.href = url; a.download = `labels-${state.coder}-${state.phase}-${packet.sha256.slice(0, 8)}.json`;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function validPacket(p) {
  return p && p.schema === "pickaxetax.labelpacket.v1" && typeof p.sha256 === "string" &&
    Array.isArray(p.items) && Array.isArray(p.calibration) &&
    [...p.items, ...p.calibration].every((x) => x && typeof x.id === "string" && typeof x.instruction === "string" && Array.isArray(x.steps) && x.stats);
}

$("packet").addEventListener("change", async () => {
  const f = $("packet").files[0];
  $("setup-err").textContent = ""; packet = null; $("start").disabled = true; $("packet-info").textContent = "";
  if (!f) return;
  try {
    const p = JSON.parse(await f.text());
    if (!validPacket(p)) throw new Error();
    packet = p;
    $("packet-info").textContent = `codebook ${p.codebook} · ${p.calibration.length} + ${p.items.length} · ${p.sha256.slice(0, 12)}…`;
    $("start").disabled = false;
  } catch { $("setup-err").textContent = t("bad_packet"); }
});

$("start").addEventListener("click", () => {
  const coder = $("coder").value.trim();
  if (!coder) { $("setup-err").textContent = t("need_coder"); return; }
  const phase = document.querySelector('input[name="phase"]:checked').value;
  state = { coder, phase, order: [], pos: 0, labels: {} };
  const saved = store.get(key());
  if (saved) { try { const s = JSON.parse(saved); if (s && s.order) state = s; } catch { /* start fresh */ } }
  if (!state.order.length) state.order = shuffled(items().map((x) => x.id), `${packet.sha256}|${coder}|${phase}`);
  $("setup").hidden = true; $("work").hidden = false;
  render();
});

$("prev").addEventListener("click", () => go(state.pos - 1));
$("next").addEventListener("click", () => go(state.pos + 1));
$("next-open").addEventListener("click", () => {
  const n = state.order.length;
  for (let k = 1; k <= n; k++) { const p = (state.pos + k) % n; if (!complete(state.labels[state.order[p]])) return go(p); }
});
$("export").addEventListener("click", exportLabels);
$("note").addEventListener("input", () => {
  const id = state.order[state.pos];
  state.labels[id] = { ...(state.labels[id] || {}), note: $("note").value };
  save();
});
$("form").addEventListener("submit", (e) => e.preventDefault());
$("lang").addEventListener("click", () => { lang = lang === "ko" ? "en" : "ko"; store.set("lang", lang); applyI18n(); });

applyI18n();
