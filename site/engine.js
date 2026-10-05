// Pickaxe Tax browser engine: conversation text -> skeleton, entirely in the page.
//
// A line-for-line port of the Python engine (pickaxetax/ingest, text, tokens,
// analyze). tests/test_parity.py runs both on the same inputs and requires
// identical output, so change them together.
//
// Python and JavaScript regex/string semantics differ in a few places; the
// helpers below reproduce Python's behaviour:
//   \w \W \b \d  -> Unicode-aware classes (JS versions are ASCII-only)
//   len / slicing -> code points, not UTF-16 units
//   round()       -> round-half-even
//   str(float)    -> "33.0", not "33"

// ---------------------------------------------------------------- helpers

const WC = "\\p{L}\\p{N}_";                       // Python \w (inside a class)
const W = `[^${WC}]`;                              // Python \W
const B = `(?:(?<=[${WC}])(?![${WC}])|(?<![${WC}])(?=[${WC}]))`; // Python \b
const D = "\\p{Nd}";                               // Python \d

const cps = (s) => Array.from(s);
const cpLen = (s) => { let n = 0; for (const _ of s) n++; return n; };
const cpSlice = (s, a, b) => cps(s).slice(a, b).join("");
const pyStrip = (s) => s.trim();
const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

export function pyRound(x, nd = 0) {
  // Python rounds the exact binary value, ties to even. toFixed also rounds the
  // exact value but breaks exact ties upward, so only exact ties need fixing.
  if (!Number.isFinite(x)) return x;
  const ax = Math.abs(x);
  let r = Number(ax.toFixed(nd));
  const [ip, fp] = ax.toFixed(100).split(".");
  if (/^50*$/.test(fp.slice(nd))) {
    const kept = ip + fp.slice(0, nd);
    if (Number(kept[kept.length - 1]) % 2 === 0) r = Number(nd ? `${ip}.${fp.slice(0, nd)}` : ip);
  }
  return x < 0 ? -r : r;
}
const pyFloat = (x) => (Number.isInteger(x) ? x.toFixed(1) : String(x));
const commas = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

class Counter extends Map {
  add(k, n = 1) { this.set(k, (this.get(k) || 0) + n); }
  update(items) { for (const k of items) this.add(k); }
  c(k) { return this.get(k) || 0; }
  mostCommon(n) {
    const arr = [...this.entries()];
    arr.sort((a, b) => b[1] - a[1]); // stable: ties keep insertion order, like Python
    return n === undefined ? arr : arr.slice(0, n);
  }
}

// ---------------------------------------------------------------- tokens

const CJK = /[ᄀ-ᇿ぀-ヿ㄰-㆏㐀-鿿가-힯豈-﫿]/gu;

export function estimateTokens(text) {
  if (!text) return 0;
  const cjk = (text.match(CJK) || []).length;
  const rest = cpLen(pyStrip(text.replace(CJK, "").replace(/\s+/gu, " ")));
  return Math.max(1, Math.ceil(cjk * 1.0 + rest / 4.0));
}

// ---------------------------------------------------------------- text

const PII = [
  new RegExp(`[${WC}.+\\-]+@[${WC}\\-]+\\.[${WC}.\\-]+`, "gu"),
  /https?:\/\/\S+|www\.\S+/gu,
  new RegExp(`${B}(?:${D}{1,3}\\.){3}${D}{1,3}${B}`, "gu"),
  new RegExp(`${B}(?:sk|pk|ghp|gho|xox[abp]|AKIA)[\\-_A-Za-z0-9]{12,}${B}`, "gu"),
  new RegExp(`${B}[A-Za-z0-9_\\-]{32,}${B}`, "gu"),
  new RegExp(`\\+?${D}[${D}\\s\\-().]{7,}${D}`, "gu"),
];

export function scrubPii(text) {
  for (const p of PII) text = text.replace(p, " ");
  return text;
}

const FENCE = /```[^\n]*\n[\s\S]*?(?:```|$)/gu;

export function splitCode(text) {
  let n = 0;
  const prose = text.replace(FENCE, () => { n++; return " "; });
  return [prose, n > 0];
}

const WORD = /[A-Za-z][A-Za-z0-9+#]*(?:[.\-][A-Za-z0-9+#]+)*|[가-힣]{2,}|[一-鿿぀-ヿ]{2,}/gu;

const KO_SUFFIXES = `
입니다 습니다 합니다 해주세요 해줘요 해줘 해주 하세요 할까요 인가요 일까요 했는데 하는데 하려면
에서는 에게서 으로는 으로서 으로써 이라고 이라는 라고 라는 처럼 보다 부터 까지 마다 조차 이나
이랑 하고 에서 에게 한테 으로 로서 로써 이며 이고 인데 이요 이다 했다 한다 하는 하고 해서 하면
은 는 이 가 을 를 에 의 도 만 로 와 과 나 랑 요 죠 다 고 며`.split(/\s+/).filter(Boolean)
  .map((s, i) => [s, i]).sort((a, b) => cpLen(b[0]) - cpLen(a[0]) || a[1] - b[1]).map((x) => x[0]);
const STOP_KO_PARTICLES = new Set(KO_SUFFIXES);

function stripKo(word) {
  for (const suf of KO_SUFFIXES) {
    if (word.endsWith(suf) && cpLen(word) - cpLen(suf) >= 2) return word.slice(0, word.length - suf.length);
  }
  return word;
}

const STOP_EN = new Set(`
a an the and or but if then else of to in on at by for with about from into over under as is are was
were be been being do does did doing have has had having i me my we our you your he she it its they
them their this that these those there here what which who whom whose when where why how can could
would should will shall may might must not no yes ok okay so just also very really more most less
some any all each every both few many much other such only own same than too s t don doesn didn isn
aren wasn weren won wouldn shouldn couldn let lets get got make made use used using like want need
please thanks thank hi hello hey sure great good nice well now one two first second new way thing
things something anything everything give tell show explain write help know think see look try
example examples following above below based case cases e.g i.e etc vs via per able`.split(/\s+/).filter(Boolean));

const STOP_KO = new Set(`
그리고 그러나 그런데 하지만 그래서 그러면 또는 혹은 및 등 등등 것 거 수 때 중 더 좀 잘 왜 뭐 무엇
어떻게 어떤 이런 저런 그런 이것 저것 그것 여기 저기 거기 우리 저희 제가 내가 너무 정말 진짜 아주
매우 다시 계속 지금 이제 먼저 그냥 혹시 만약 경우 부분 관련 대한 대해 위해 통해 같은 같이 다른
가능 있다 없다 있는 없는 있어 없어 있습 없습 하다 해요 했어 되다 된다 되는 됩니다 감사 고마워
감사합니다 안녕 안녕하세요 네 예 아니 아니요 응 그래 알겠 알려 알려줘 설명 설명해 해줘 주세요
예시 예를 정도 이상 이하 사용 방법 내용 생각 질문 답변 문제 부탁 제발 하나 두 번째 첫째 둘째`.split(/\s+/).filter(Boolean));

const SHORT_OK = new Set(["ai", "ui", "ux", "db", "go", "js", "ts", "ml", "os", "c#", "c++", "r"]);

export function detectLanguage(text) {
  const n = (re) => (text.match(re) || []).length;
  const cands = [["ko", n(/[가-힣]/gu) * 2], ["ja", n(/[぀-ヿ]/gu) * 2], ["zh", n(/[一-鿿]/gu) * 2], ["en", n(/[A-Za-z]/gu) / 2]];
  let best = cands[0];
  for (const c of cands.slice(1)) if (c[1] > best[1]) best = c;
  return best[1] > 0 ? best[0] : "und";
}

export function words(text) {
  let [prose] = splitCode(text);
  prose = scrubPii(prose);
  const out = [];
  for (let w of prose.match(WORD) || []) {
    const c0 = w[0];
    if (c0.charCodeAt(0) < 128) {
      w = w.toLowerCase().replace(/^[.\-]+|[.\-]+$/g, "");
      if (cpLen(w) < 3 && !SHORT_OK.has(w)) continue;
      if (STOP_EN.has(w) || /^[0-9]+$/.test(w)) continue;
    } else if (c0 >= "가" && c0 <= "힣") {
      w = stripKo(w);
      if (STOP_KO.has(w) || STOP_KO_PARTICLES.has(w) || cpLen(w) < 2) continue;
    }
    out.push(w);
  }
  return out;
}

export function rankKeywords(userTexts, assistantTexts, top = 40) {
  const u = new Counter(), uDocs = new Counter(), a = new Counter();
  const first = new Set(userTexts.length ? words(userTexts[0]) : []);
  for (const t of userTexts) {
    const ws = words(t);
    u.update(ws);
    uDocs.update(new Set(ws));
  }
  for (const t of assistantTexts) a.update(words(t));
  const scores = [];
  for (const w of new Set([...u.keys(), ...a.keys()])) {
    const total = u.c(w) + a.c(w);
    if (u.c(w) === 0 && total < 3) continue;
    if (u.c(w) === 1 && a.c(w) === 0 && userTexts.length > 3 && !first.has(w)) continue;
    scores.push([w, 2.0 * u.c(w) + 1.5 * uDocs.c(w) + Math.log1p(a.c(w))]);
  }
  scores.sort((x, y) => y[1] - x[1] || cmp(x[0], y[0]));
  return scores.slice(0, top);
}

// fingerprints: two FNV-1a 32-bit halves (same as pickaxetax/text.py)
const ENC = new TextEncoder();
function fnv1a32(bytes, h) {
  for (const b of bytes) h = Math.imul(h ^ b, 0x01000193) >>> 0;
  return h;
}
function hash64(bytes) { return [fnv1a32(bytes, 0x050c5d1f), fnv1a32(bytes, 0x811c9dc5)]; } // [hi, lo]

export function simhash(text, key = new Uint8Array()) {
  let feats = words(text);
  if (!feats.length) feats = text.toLowerCase().match(new RegExp(`[${WC}]+`, "gu")) || [];
  if (!feats.length) return [0, 0];
  const grams = feats.concat(feats.slice(0, -1).map((x, i) => `${x} ${feats[i + 1]}`));
  const v = new Array(64).fill(0);
  for (const g of grams) {
    const gb = ENC.encode(g);
    const bytes = new Uint8Array(key.length + 1 + gb.length);
    bytes.set(key, 0); bytes[key.length] = 0; bytes.set(gb, key.length + 1);
    const [hi, lo] = hash64(bytes);
    for (let i = 0; i < 32; i++) v[i] += (lo >>> i) & 1 ? 1 : -1;
    for (let i = 0; i < 32; i++) v[32 + i] += (hi >>> i) & 1 ? 1 : -1;
  }
  let lo = 0, hi = 0;
  for (let i = 0; i < 32; i++) if (v[i] > 0) lo |= 1 << i;
  for (let i = 0; i < 32; i++) if (v[32 + i] > 0) hi |= 1 << i;
  return [hi >>> 0, lo >>> 0];
}
const popcount = (x) => { let c = 0; while (x) { x &= x - 1; c++; } return c; };
const isZero = (f) => f[0] === 0 && f[1] === 0;
function simhashSimilarity(a, b) {
  if (isZero(a) || isZero(b)) return 0.0;
  return 1.0 - (popcount((a[0] ^ b[0]) >>> 0) + popcount((a[1] ^ b[1]) >>> 0)) / 64;
}
const hex64 = (f) => f[0].toString(16).padStart(8, "0") + f[1].toString(16).padStart(8, "0");
function jaccard(a, b) {
  if (!a.size || !b.size) return 0.0;
  let inter = 0;
  for (const x of a) if (b.has(x)) inter++;
  return inter / new Set([...a, ...b]).size;
}

// ---------------------------------------------------------------- ingest

export const USER = "user", ASSISTANT = "assistant";

const escapeRe = (s) => s.replace(/[\\^$.*+?()[\]{}|/]/g, "\\$&");
const USER_MARKERS = ["you said", "user", "you", "me", "human", "q", "question", "prompt", "나", "사용자", "질문", "유저", "저"];
const ASSISTANT_MARKERS = ["chatgpt said", "claude said", "gemini said", "copilot said", "assistant", "chatgpt", "gpt", "claude",
  "gemini", "copilot", "grok", "perplexity", "ai", "bot", "a", "answer", "model", "답변", "답", "어시스턴트", "챗봇"];
function markerRegex(names) {
  const alts = names.map((n, i) => [n, i]).sort((x, y) => cpLen(y[0]) - cpLen(x[0]) || x[1] - y[1]).map((x) => escapeRe(x[0])).join("|");
  return `(?:#+[ \\t]*(?:${alts})[ \\t]*\\n|(?:\\*\\*|\\[)?(?:${alts})(?:\\*\\*|\\])?[ \\t]*(?::|：))`;
}
const LINE = new RegExp(`^\\s*(?:(?<u>${markerRegex(USER_MARKERS)})|(?<a>${markerRegex(ASSISTANT_MARKERS)}))`, "gimu");

export function parseTranscript(text) {
  text = text.split("\r\n").join("\n");
  const matches = [...text.matchAll(LINE)];
  if (!matches.length) throw new Error("no role markers found (expected lines like 'User:' / 'Assistant:')");
  const turns = [];
  matches.forEach((m, i) => {
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const body = pyStrip(text.slice(m.index + m[0].length, end));
    if (!body) return;
    const role = m.groups.u !== undefined ? USER : ASSISTANT;
    if (turns.length && turns[turns.length - 1].role === role) turns[turns.length - 1].text += "\n\n" + body;
    else turns.push({ role, text: body });
  });
  if (!turns.some((t) => t.role === USER)) throw new Error("transcript has no user turns");
  return { turns, source: "text" };
}

const ROLE = { user: USER, human: USER, assistant: ASSISTANT, model: ASSISTANT, bot: ASSISTANT, ai: ASSISTANT };
const isObj = (x) => x !== null && typeof x === "object" && !Array.isArray(x);
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const roleOf = (x) => (has(ROLE, x) ? ROLE[x] : undefined);

function contentText(c) {
  if (c === null || c === undefined) return "";
  if (typeof c === "string") return c;
  if (Array.isArray(c)) return c.map(contentText).filter(Boolean).join("\n");
  if (isObj(c)) {
    if (has(c, "parts")) return contentText(c.parts);
    const ty = c.type;
    if ((ty === undefined || ty === null || ["text", "output_text", "input_text"].includes(ty)) && has(c, "text")) return contentText(c.text);
    if (has(c, "content")) return contentText(c.content);
  }
  return "";
}

function finish(turns, source) {
  const merged = [];
  for (const t of turns) {
    if (!pyStrip(t.text)) continue;
    if (merged.length && merged[merged.length - 1].role === t.role) merged[merged.length - 1].text += "\n\n" + t.text;
    else merged.push({ role: t.role, text: t.text });
  }
  if (!merged.some((t) => t.role === USER)) return null;
  return { turns: merged, source };
}

function fromChatgptMapping(obj) {
  const mapping = obj.mapping;
  let nodeId = obj.current_node;
  if (typeof nodeId !== "string" || !has(mapping, nodeId)) {
    const leaves = Object.keys(mapping).filter((k) => !(isObj(mapping[k]) && mapping[k].children && mapping[k].children.length));
    nodeId = leaves.length ? leaves[leaves.length - 1] : null;
  }
  const chain = [], seen = new Set();
  while (nodeId && has(mapping, nodeId) && !seen.has(nodeId)) {
    seen.add(nodeId);
    chain.push(mapping[nodeId]);
    nodeId = mapping[nodeId].parent;
  }
  const turns = [];
  for (const node of chain.reverse()) {
    const msg = node.message || {};
    const role = roleOf(String((msg.author || {}).role || "").toLowerCase());
    if (role && !(msg.metadata || {}).is_visually_hidden_from_conversation) turns.push({ role, text: contentText(msg.content) });
  }
  return finish(turns, "chatgpt");
}

function fromMessageList(items, source) {
  const turns = [];
  for (let m of items) {
    if (!isObj(m)) continue;
    if (has(m, "message") && isObj(m.message)) m = m.message;
    const raw = m.role || m.sender || (m.author || {}).role || "";
    const role = roleOf(String(raw).toLowerCase());
    if (!role) continue;
    const text = typeof m.text === "string" && m.text ? m.text : null;
    turns.push({ role, text: text || contentText(m.content) });
  }
  return finish(turns, source);
}

export function parseJson(obj) {
  if (Array.isArray(obj)) {
    if (obj.length && obj.every((x) => isObj(x) && (has(x, "role") || has(x, "sender")))) {
      const c = fromMessageList(obj, "openai-messages");
      return c ? [c] : [];
    }
    return obj.flatMap(parseJson);
  }
  if (!isObj(obj)) return [];
  let conv = null;
  if (isObj(obj.mapping)) conv = fromChatgptMapping(obj);
  else if (Array.isArray(obj.linear_conversation)) conv = fromMessageList(obj.linear_conversation, "chatgpt");
  else if (Array.isArray(obj.chat_messages)) conv = fromMessageList(obj.chat_messages, "claude");
  else if (Array.isArray(obj.messages)) conv = fromMessageList(obj.messages, "openai-messages");
  else {
    for (const v of Object.values(obj)) {
      if (v !== null && typeof v === "object") {
        const found = parseJson(v);
        if (found.length) return found;
      }
    }
  }
  return conv ? [conv] : [];
}

export class LinkInput extends Error {
  constructor(url) { super("share link"); this.url = url; }
}

export function ingestText(text) {
  text = pyStrip(text);
  if (text.length > 4_000_000) throw new Error("input too large");
  if (text.startsWith("https://") && !text.includes("\n")) throw new LinkInput(text);
  if (text === "" || "[{".includes(text[0])) {
    let obj = null;
    try { obj = JSON.parse(text); } catch { obj = null; }
    if (obj !== null) {
      const convs = parseJson(obj);
      if (!convs.length) throw new Error("JSON did not contain a recognizable conversation");
      return convs;
    }
  }
  return [parseTranscript(text)];
}

// ---------------------------------------------------------------- intents

const rx = (...parts) => new RegExp(parts.join("|"), "iu");
const ACK = rx(
  `^${W}*(thanks?( you)?|thx|ty|ok(ay)?|cool|great|nice|perfect|awesome|got it|good|lol|haha)${W}*$`,
  `^${W}*(감사(합니다|해요)?|고마워(요)?|고맙습니다|ㄳ|ㄱㅅ|오케이|ㅇㅋ|좋아(요)?|굿|알겠(어|습니다)(요)?|넵|네+|응+|ㅎㅎ+|ㅋㅋ+)${W}*$`,
);
const CONTINUE = rx(
  `^${W}*(continue|go on|keep going|more|next|and\\??|proceed)${W}*$`,
  `^${W}*(계속(해(줘|주세요)?)?|이어서(\\s*(해줘|써줘|작성해줘))?|더|다음|진행(해줘)?)${W}*$`,
);
const CORRECT = rx(
  `^${W}*no${B}`, `${B}that'?s (not|wrong)${B}`, `${B}(wrong|incorrect|doesn'?t work|not working|still (not|broken|wrong)|didn'?t work)${B}`,
  `${B}not what i${B}`, `${B}try again${B}`, `${B}you (missed|forgot|ignored)${B}`, `${B}i said${B}`, `${B}still (getting|the same)${B}`,
  `^${W}*아니`, "틀렸", "틀린", "잘못", "그게 아니", "다시 (해|작성|써|만들)", "안 ?(돼|되|됨|된다)", "오류", "에러",
  "말했잖", "이해를 못", "여전히", "엉뚱",
);
const CLARIFY = rx(
  `^${W}*(also|and also|but|however|additionally|actually|only|make it|instead|what if)${B}`, `${B}(in addition|one more thing|more specifically)${B}`,
  `^${W}*(그리고|추가로|단,?|대신|그럼|그러면|좀 더|조금 더|더 자세히|구체적으로|만약)`,
);
const QUESTION = rx("\\?\\s*$", `^${W}*(what|why|how|when|where|which|who|is|are|can|could|should|does|do)${B}`, `(까요|나요|인가요|ㄹ까|는지|을까|가요|니\\?|냐)${W}*$`);
const APOLOGY = rx(`^${W}*(you'?re (absolutely )?right|my apologies|apologies|i apologi[sz]e|sorry)`, `^${W}*(죄송합니다|맞습니다|말씀하신 대로|정확한 지적|사과드립니다)`);
const REFUSAL = rx(`^${W}*(i can'?t|i cannot|i'?m (not able|unable)|i won'?t)`, "(도와드릴 수 없|제공할 수 없|답변드릴 수 없)");

const tail = (s, n) => cpSlice(s, Math.max(0, cpLen(s) - n));
const isQuestion = (t) => QUESTION.test(tail(t, 200)) || QUESTION.test(cpSlice(t, 0, 80));

function classifyUser(text, tokens, similar, hasCode, first) {
  const t = pyStrip(text);
  if (first) {
    if (tokens >= 600 || (hasCode && tokens >= 250)) return "context";
    return isQuestion(t) ? "ask" : "instruct";
  }
  if (similar && tokens > 3) return "retry";
  if (tokens <= 12 && ACK.test(t)) return "ack";
  if (tokens <= 12 && CONTINUE.test(t)) return "continue";
  if (tokens >= 600 || (hasCode && tokens >= 250)) return "context";
  if (CORRECT.test(cpSlice(t, 0, 240))) return "correct";
  if (CLARIFY.test(cpSlice(t, 0, 120))) return "clarify";
  if (isQuestion(t)) return "ask";
  return "instruct";
}

function classifyAssistant(text, tokens, hasCode) {
  const t = pyStrip(text);
  const head = cpSlice(t, 0, 200);
  if (APOLOGY.test(head)) return "apology_fix";
  if (REFUSAL.test(head) && tokens < 300) return "refusal";
  if (tokens < 120 && t.endsWith("?")) return "followup_question";
  if (hasCode) return "code";
  return "answer";
}

const USER_INTENTS = ["ask", "instruct", "clarify", "correct", "retry", "continue", "ack", "context"];
const ASSISTANT_INTENTS = ["answer", "code", "followup_question", "apology_fix", "refusal"];

// ---------------------------------------------------------------- structure

function buildStructure(turns, retryOf, cues) {
  const edges = [], branches = [];
  let current = -1, lastUser = null;
  const E = (s, d, type) => edges.push({ src: s, dst: d, type });
  const union = (set, items) => { for (const x of items) set.add(x); };
  turns.forEach((t, i) => {
    if (i > 0) E(turns[i - 1].index, t.index, "NEXT");
    if (t.role === ASSISTANT) {
      if (lastUser) {
        t.branch = lastUser.branch; t.depth = lastUser.depth;
        E(t.index, lastUser.index, "ANSWERS");
        union(branches[t.branch].topics, t.topics);
        union(branches[t.branch].cues, cues.get(t.index) || []);
      }
      return;
    }
    if (t.role !== USER) return;
    const topics = new Set(t.topics);
    const cue = new Set([...(cues.get(t.index) || []), ...topics]);
    if (current < 0) {
      branches.push({ topics: new Set(topics), cues: new Set(cue), depth: 0, last: t.index });
      current = 0; t.branch = 0; t.depth = 0;
    } else if (t.intent === "retry") {
      const src = retryOf.get(t.index);
      const srcTurn = turns.find((x) => x.index === src) || lastUser;
      t.branch = srcTurn.branch; t.depth = srcTurn.depth;
      current = t.branch;
      E(t.index, srcTurn.index, "RETRIES");
    } else if (["correct", "ack", "continue"].includes(t.intent) || cue.size === 0) {
      t.branch = lastUser.branch; t.depth = lastUser.depth;
      E(t.index, lastUser.index, { correct: "CORRECTS", continue: "CONTINUES" }[t.intent] || "REVISITS");
      if (t.intent === "correct") { union(branches[t.branch].topics, topics); union(branches[t.branch].cues, cue); }
    } else {
      let cur = branches[current];
      const overlap = [...cue].some((x) => cur.cues.has(x));
      if (overlap || (t.intent === "clarify" && t.tokens < 40)) {
        const fresh = [...topics].filter((x) => !cur.topics.has(x));
        if (fresh.length) { cur.depth += 1; E(t.index, cur.last, "DEEPENS"); }
        else E(t.index, cur.last, "REVISITS");
        union(cur.topics, topics); union(cur.cues, cue);
      } else {
        let best = -1, bestOv = 0;
        branches.forEach((b, bi) => {
          const ov = [...cue].filter((x) => b.cues.has(x)).length;
          if (bi !== current && ov > bestOv) { best = bi; bestOv = ov; }
        });
        if (best >= 0) {
          current = best; cur = branches[best];
          E(t.index, cur.last, "RETURNS");
          if ([...topics].some((x) => !cur.topics.has(x))) cur.depth += 1;
          union(cur.topics, topics); union(cur.cues, cue);
        } else {
          E(t.index, lastUser.index, "PIVOTS");
          branches.push({ topics: new Set(topics), cues: new Set(cue), depth: 0, last: t.index });
          current = branches.length - 1; cur = branches[current];
        }
      }
      t.branch = current; t.depth = cur.depth;
      cur.last = t.index;
    }
    lastUser = t;
  });
  return edges;
}

// ---------------------------------------------------------------- accounting

const INPUT_WEIGHT = 0.25;
const WH_PER_1K = 0.5;
const units = (inp, out) => inp * INPUT_WEIGHT + out;

function replay(pairs) {
  let ctx = 0, inp = 0, out = 0;
  for (const [u, a] of pairs) {
    ctx += u.tokens;
    if (a) { inp += ctx; out += a.tokens; ctx += a.tokens; }
  }
  return [inp, out];
}

function account(turns) {
  const pairs = [];
  for (const t of turns) {
    if (t.role === USER) pairs.push([t, null]);
    else if (t.role === ASSISTANT && pairs.length && pairs[pairs.length - 1][1] === null) pairs[pairs.length - 1][1] = t;
  }
  const [actualIn, actualOut] = replay(pairs);
  let ackUnits = 0.0, supUnits = 0.0, drag = 0, ctx = 0;
  const history = [], superseded = new Set();
  pairs.forEach(([u, a], k) => {
    const nxt = k + 1 < pairs.length ? pairs[k + 1][0] : null;
    ctx += u.tokens;
    history.push(u);
    if (a) {
      const replyIn = ctx;
      drag += history.filter((h) => h.branch !== u.branch).reduce((s, h) => s + h.tokens, 0);
      if (u.intent === "ack") {
        u.redundant = a.redundant = true;
        ackUnits += units(replyIn, a.tokens);
      } else if (nxt && (nxt.intent === "correct" || nxt.intent === "retry")) {
        a.redundant = true;
        superseded.add(a.index);
        supUnits += units(replyIn, a.tokens);
      }
      ctx += a.tokens;
      history.push(a);
    }
    if (u.intent === "retry") u.redundant = true;
  });

  const byBranch = new Map();
  pairs.forEach(([u, a], k) => {
    if (u.intent === "ack") return;
    if (a && superseded.has(a.index)) {
      if (pairs[k + 1][0].intent === "retry") return;
      a = null;
    }
    if (!byBranch.has(u.branch)) byBranch.set(u.branch, []);
    byBranch.get(u.branch).push([u, a]);
  });
  let optIn = 0, optOut = 0, usefulUser = 0, usefulOut = 0;
  for (const seq of byBranch.values()) {
    const [i, o] = replay(seq);
    optIn += i; optOut += o;
    for (const [u, a] of seq) { usefulUser += u.tokens; if (a) usefulOut += a.tokens; }
  }
  const actualU = units(actualIn, actualOut), optU = units(optIn, optOut), oneU = units(usefulUser, usefulOut);
  const users = turns.filter((t) => t.role === USER), assts = turns.filter((t) => t.role === ASSISTANT);
  const userTok = users.reduce((s, t) => s + t.tokens, 0), asstTok = assts.reduce((s, t) => s + t.tokens, 0);
  const counts = {};
  for (const k of USER_INTENTS.concat(ASSISTANT_INTENTS)) {
    const v = turns.filter((t) => t.intent === k).length;
    if (v) counts[k] = v;
  }
  const pct = (x) => (actualU ? pyRound((100.0 * x) / actualU, 1) : 0.0);
  const maxDepth = turns.reduce((m, t) => Math.max(m, t.depth), 0);
  return {
    user_turns: users.length,
    assistant_turns: assts.length,
    visible_tokens: userTok + asstTok,
    user_tokens: userTok,
    assistant_tokens: asstTok,
    verbosity_ratio: userTok ? pyRound(asstTok / userTok, 2) : null,
    billed_input_tokens: actualIn,
    billed_output_tokens: actualOut,
    compute_units: pyRound(actualU),
    optimized_compute_units: pyRound(optU),
    one_shot_compute_units: pyRound(oneU),
    savings_pct: actualU ? pyRound(100.0 * (1 - optU / actualU), 1) : 0.0,
    one_shot_savings_pct: actualU ? pyRound(100.0 * (1 - oneU / actualU), 1) : 0.0,
    waste: {
      ack_units: pyRound(ackUnits),
      ack_pct: pct(ackUnits),
      superseded_units: pyRound(supUnits),
      superseded_pct: pct(supUnits),
      offtopic_context_tokens: drag,
      offtopic_context_pct: pct(drag * INPUT_WEIGHT),
    },
    intent_counts: counts,
    max_depth: maxDepth,
    branches: new Set(users.map((t) => t.branch)).size,
    depth_efficiency: users.length ? pyRound(maxDepth / users.length, 2) : 0.0,
    energy_wh_estimate: pyRound((actualU / 1000) * WH_PER_1K, 2),
    energy_wh_avoidable: pyRound(((actualU - optU) / 1000) * WH_PER_1K, 2),
    assumptions: { input_weight: INPUT_WEIGHT, wh_per_1k_units: WH_PER_1K },
  };
}

// ---------------------------------------------------------------- suggestions

function uniq(seq) {
  const seen = new Set(), out = [];
  for (const x of seq) if (!seen.has(x)) { seen.add(x); out.push(x); }
  return out;
}
const tip = (code, weight, ko, en) => ({ code, weight: pyRound(weight, 1), ko, en });

function suggest(sk) {
  const m = sk.metrics, w = m.waste;
  const users = sk.turns.filter((t) => t.role === USER);
  const counts = new Counter();
  for (const t of sk.turns) counts.add(t.intent);
  const bt = new Counter();
  for (const t of sk.turns) bt.add(t.branch, t.tokens);
  let main = 0, mainTok = -Infinity;
  for (const [b, v] of bt) if (v > mainTok) { main = b; mainTok = v; }
  const mainUsers = users.filter((t) => t.branch === main);

  const goal = uniq((mainUsers.length ? mainUsers[0].topics : []).concat(sk.agenda)).slice(0, 3);
  const details = uniq(mainUsers.slice(1).filter((t) => t.intent !== "correct").flatMap((t) => t.topics).filter((x) => !goal.includes(x))).slice(0, 6);
  const constraints = uniq(users.filter((t) => t.intent === "correct" || t.intent === "clarify").flatMap((t) => t.topics).filter((x) => !goal.includes(x))).slice(0, 5);
  const others = [];
  for (const b of [...new Set(users.map((t) => t.branch))].filter((b) => b !== main).sort((x, y) => x - y)) {
    const top = uniq(users.filter((t) => t.branch === b).flatMap((t) => t.topics)).slice(0, 3);
    if (top.length) others.push(top);
  }
  const wantsCode = sk.turns.some((t) => t.role === ASSISTANT && t.has_code);
  const useful = sk.turns.filter((t) => t.role === ASSISTANT && !t.redundant).map((t) => t.tokens).sort((x, y) => x - y);
  if (!useful.length) useful.push(0);
  const targetLen = useful[Math.floor(useful.length / 2)];
  const outLen = Math.max(100, Math.floor(targetLen / 2));

  let lines;
  if (sk.language === "ko") {
    lines = [`[목표] ${goal.join(", ") || "…"}`];
    if (details.length) lines.push(`[세부 범위] ${details.join(" → ")}`);
    if (constraints.length) lines.push(`[제약·조건] ${constraints.join(", ")} (처음부터 명시)`);
    lines.push(`[출력 형식] ${wantsCode ? "코드 포함, " : ""}핵심 위주로 약 ${outLen} 토큰 이내`);
    for (const o of others) lines.push(`[별도 대화로] ${o.join(", ")}`);
  } else {
    lines = [`[Goal] ${goal.join(", ") || "…"}`];
    if (details.length) lines.push(`[Scope] ${details.join(" → ")}`);
    if (constraints.length) lines.push(`[Constraints] ${constraints.join(", ")} (state up front)`);
    lines.push(`[Output] ${wantsCode ? "include code, " : ""}essentials only, ~${outLen} tokens`);
    for (const o of others) lines.push(`[Separate chat] ${o.join(", ")}`);
  }

  const tips = [];
  const ack = counts.c("ack");
  if (ack) {
    tips.push(tip("ack", w.ack_pct,
      `감사·확인 메시지 ${ack}회가 전체 연산의 ${pyFloat(w.ack_pct)}%를 소모했습니다. 매번 전체 대화를 다시 읽기 때문입니다. 만족했다면 그냥 창을 닫으세요.`,
      `${ack} thank-you/ok message(s) used ${pyFloat(w.ack_pct)}% of all compute — each one re-reads the whole chat. If you're done, just close it.`));
  }
  const redo = counts.c("correct") + counts.c("retry");
  if (redo) {
    const cs = constraints.join(", ");
    tips.push(tip("redo", w.superseded_pct,
      `수정·재질문 ${redo}회로 버려진 답변이 연산의 ${pyFloat(w.superseded_pct)}%입니다. 조건(${cs || "대상, 형식, 범위"})을 첫 프롬프트에 넣으세요.`,
      `${redo} correction/retry turn(s) threw away answers worth ${pyFloat(w.superseded_pct)}% of compute. Put constraints (${cs || "audience, format, scope"}) in the first prompt.`));
  }
  if (m.branches > 1) {
    tips.push(tip("pivot", w.offtopic_context_pct,
      `주제가 ${m.branches}갈래로 나뉘었습니다. 관련 없는 이전 대화가 매 답변마다 재전송되어 연산의 ${pyFloat(w.offtopic_context_pct)}%를 차지했습니다. 새 주제는 새 대화에서 시작하세요.`,
      `The chat split into ${m.branches} threads; unrelated history was re-sent on every reply (${pyFloat(w.offtopic_context_pct)}% of compute). Start a new chat for a new topic.`));
  }
  const ctxTurns = users.filter((t) => t.intent === "context");
  if (ctxTurns.length) {
    const later = sk.turns.filter((t) => t.role === ASSISTANT && t.index > ctxTurns[0].index).length;
    const pasted = ctxTurns.reduce((s, t) => s + t.tokens, 0);
    tips.push(tip("paste", Math.min(60.0, (pasted * later) / Math.max(1, m.billed_input_tokens) * 100),
      `대용량 붙여넣기(${commas(pasted)} 토큰)가 이후 ${later}번의 답변마다 다시 읽혔습니다. 필요한 부분만 발췌하세요.`,
      `A large paste (${commas(pasted)} tokens) was re-read on ${later} later replies. Paste only the relevant excerpt.`));
  }
  if ((m.verbosity_ratio || 0) > 8 && m.assistant_tokens > 1500) {
    tips.push(tip("verbose", 10.0,
      `답변이 질문보다 ${pyFloat(m.verbosity_ratio)}배 깁니다. '핵심만 5줄로'처럼 길이를 지정하세요.`,
      `Answers were ${pyFloat(m.verbosity_ratio)}x longer than prompts. Ask for a length, e.g. 'five lines, essentials only'.`));
  }
  if (counts.c("continue") >= 2) {
    tips.push(tip("continue", 5.0,
      `'계속' 요청 ${counts.c("continue")}회 — 긴 결과물은 섹션별로 나눠 요청하세요.`,
      `${counts.c("continue")} 'continue' prompts — request long outputs section by section.`));
  }
  if (counts.c("followup_question") >= 2) {
    tips.push(tip("underspecified", 5.0,
      `AI가 ${counts.c("followup_question")}번 되물었습니다. 목표·대상·형식을 처음에 밝히세요.`,
      `The assistant had to ask back ${counts.c("followup_question")} times. State goal, audience and format first.`));
  }
  if (users.length > 20) {
    tips.push(tip("long", 5.0,
      "대화가 매우 깁니다. 턴마다 비용이 커지므로 중간 요약 후 새 대화로 이어가세요.",
      "Very long chat: every turn costs more than the last. Summarize and continue in a fresh chat."));
  }
  tips.sort((a, b) => b.weight - a.weight);
  return { prompt_template: lines.join("\n"), tips };
}

// ---------------------------------------------------------------- analyze

export function analyze(raw, key = new Uint8Array()) {
  const turnsRaw = raw.turns.filter((t) => (t.role === USER || t.role === ASSISTANT) && pyStrip(t.text));
  if (!turnsRaw.some((t) => t.role === USER)) throw new Error("conversation has no user turns");
  const language = detectLanguage(turnsRaw.map((t) => cpSlice(t.text, 0, 2000)).join(" "));
  const ranked = rankKeywords(turnsRaw.filter((t) => t.role === USER).map((t) => t.text),
                              turnsRaw.filter((t) => t.role === ASSISTANT).map((t) => t.text));
  const score = new Map(ranked);
  const agenda = ranked.slice(0, 7).map((x) => x[0]);

  const nodes = [], userPrints = [], retryOf = new Map(), cues = new Map();
  turnsRaw.forEach((rt, idx) => {
    const tokens = estimateTokens(rt.text);
    const [, hasCode] = splitCode(rt.text);
    const ws = words(rt.text);
    const wset = new Set(ws);
    const limit = rt.role === USER ? 5 : 3;
    const topics = [...wset].filter((w) => score.has(w)).sort((a, b) => score.get(b) - score.get(a) || cmp(a, b)).slice(0, limit);
    const fp = simhash(rt.text, key);
    if (rt.role === USER) cues.set(idx, wset);
    else { const cnt = new Counter(); cnt.update(ws); cues.set(idx, new Set(cnt.mostCommon(8).map((x) => x[0]))); }
    let intent;
    if (rt.role === USER) {
      const first = userPrints.length === 0;
      let similar = false;
      if (wset.size >= 3) {
        for (let j = userPrints.length - 1; j >= 0; j--) {
          const [ji, jfp, jset] = userPrints[j];
          if (simhashSimilarity(fp, jfp) >= 0.9 || jaccard(wset, jset) >= 0.8) { retryOf.set(idx, ji); similar = true; break; }
        }
      }
      userPrints.push([idx, fp, wset]);
      intent = classifyUser(rt.text, tokens, similar, hasCode, first);
    } else {
      intent = classifyAssistant(rt.text, tokens, hasCode);
    }
    nodes.push({ index: idx, role: rt.role, tokens, intent, topics, depth: 0, branch: 0, redundant: false,
                 has_code: hasCode, fingerprint: hex64(fp) });
  });

  const edges = buildStructure(nodes, retryOf, cues);
  cues.clear();
  const metrics = account(nodes);
  const id = hex64(hash64(ENC.encode(nodes.map((n) => `${n.role}:${n.fingerprint}:${n.tokens}`).join("|"))));
  const sk = {
    id, source: raw.source, language, agenda, turns: nodes, edges, metrics, suggestion: {},
    created_at: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
  };
  sk.suggestion = suggest(sk);
  return sk;
}

/** Text in, skeletons out. Raw text never leaves this function. */
export function analyzeInput(text, maxConversations = 200) {
  const convs = ingestText(text).slice(0, maxConversations);
  const out = [];
  for (const raw of convs) {
    try { out.push(analyze(raw)); } catch { /* skip unanalyzable */ } finally { raw.turns.length = 0; }
  }
  if (!out.length) throw new Error("no analyzable conversation found");
  return out;
}

export function analyzeTurns(turns, source = "page") {
  const raw = { turns: turns.filter((t) => t && (t.role === USER || t.role === ASSISTANT) && typeof t.text === "string"), source };
  const merged = finish(raw.turns, source);
  if (!merged) throw new Error("no user turns found on that page");
  return [analyze(merged)];
}
