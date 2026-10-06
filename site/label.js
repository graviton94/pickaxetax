// Blind labeling under the waste codebook v1 (research/protocol/waste-codebook-v1.md, §5).
// The packet is read from a local file and never leaves this tab (CSP connect-src 'none').
// Labels autosave in this browser and are exported as a file holding ids and choices only.

const CATS = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"];
const CHOICES = ["yes", "no", "unsure"];
const OUTCOMES = ["met", "partial", "not_met", "unsure"];

const T = {
  ko: {
    title: "판정 도구",
    chars: "자", error: "오류",
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
    chars: "chars", error: "error",
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
  ja: {
    title: "判定ツール",
    chars: "文字", error: "エラー",
    setup_h: "ムダの判定 · ブラインド・ラベリング",
    setup_lede: "データの持ち主から受け取った判定パケットを読み込み、指示ごとに8種類のムダがあったかを判定します。他の判定者の結果や機械判定は表示されません。終わったら判定ファイルをダウンロードして、データの持ち主に返してください。",
    step1: "判定パケットのファイル",
    step2: "判定者コード (例: A, B)",
    step3: "段階",
    phase_cal: "練習 (先に行い、終わったら解釈の違いを合わせます)",
    phase_main: "本判定",
    start: "開始",
    privacy: "🔒 パケットはこのタブの外に出ません。進行状況はこのブラウザにだけ保存されます。",
    bad_packet: "判定パケットのファイルではありません。",
    need_coder: "判定者コードを入力してください。",
    prev: "前へ", next: "次へ", next_open: "未判定の項目へ", export: "判定ファイルをダウンロード",
    progress: "{d} / {n} 判定済み", instr: "指示", steps: "エージェントがしたこと", final: "最後の応答",
    no_steps: "ツールは使われていません。", no_final: "(テキストの応答なし)",
    meta: "{session} · {index}番目の指示 · 呼び出し {calls}回 · 入力 {input} トークン · 出力 {output} · エラー {errors} · サブエージェント {subagents}",
    judge_h: "この指示にムダはありましたか?",
    judge_lede: "種類ごとに選んでください。判断の根拠が画面にない場合は「不明」です。重なる場合は上の種類にだけ印を付けます。",
    yes: "あり", no: "なし", unsure: "不明",
    outcome_h: "結果は依頼を満たしましたか?",
    met: "満たした", partial: "一部", not_met: "満たさない",
    note: "メモ (任意。判定ファイルに保存されます。会話の原文は書き写さないでください)",
    guide: "判定基準 v1 をすべて表示",
    done: "すべての項目を判定しました。判定ファイルをダウンロードして、データの持ち主に送ってください。",
  },
  zh: {
    title: "判定工具",
    chars: "字符", error: "错误",
    setup_h: "浪费判定 · 盲法标注",
    setup_lede: "载入数据所有者给你的判定包，针对每条指令判断八类浪费是否发生。你看不到其他标注者的结果，也看不到机器判定。完成后下载标注文件，交还给数据所有者。",
    step1: "判定包文件",
    step2: "标注者代码 (例如 A, B)",
    step3: "阶段",
    phase_cal: "练习 (先做，完成后统一理解上的差异)",
    phase_main: "正式标注",
    start: "开始",
    privacy: "🔒 判定包不会离开此标签页。进度只保存在此浏览器中。",
    bad_packet: "这不是判定包文件。",
    need_coder: "请填写标注者代码。",
    prev: "上一条", next: "下一条", next_open: "下一条未完成", export: "下载标注文件",
    progress: "已标注 {d} / {n}", instr: "指令", steps: "智能体做了什么", final: "最后的回复",
    no_steps: "没有使用工具。", no_final: "(没有文本回复)",
    meta: "{session} · 第 {index} 条指令 · 调用 {calls} 次 · 输入 {input} token · 输出 {output} · 错误 {errors} · 子智能体 {subagents}",
    judge_h: "这条指令中有浪费吗?",
    judge_lede: "逐类选择。如果屏幕上没有判断依据，请选「不确定」。类别重叠时，只标记排在上面的类别。",
    yes: "有", no: "没有", unsure: "不确定",
    outcome_h: "结果满足了请求吗?",
    met: "满足", partial: "部分", not_met: "未满足",
    note: "备注 (可选，会保存在标注文件中。请勿抄录对话原文)",
    guide: "查看完整的判定标准 v1",
    done: "所有条目都已标注。请下载标注文件并发给数据所有者。",
  },
  es: {
    title: "Etiquetado",
    chars: "caracteres", error: "error",
    setup_h: "Juzgar el desperdicio · etiquetado ciego",
    setup_lede: "Carga el paquete que te dio el dueño de los datos y decide, para cada instrucción, si ocurrió cada uno de los ocho tipos de desperdicio. No verás las respuestas de otras personas ni ningún juicio automático. Al terminar, descarga tu archivo de etiquetas y envíalo al dueño de los datos.",
    step1: "Archivo del paquete",
    step2: "Tu código de etiquetador (p. ej. A, B)",
    step3: "Fase",
    phase_cal: "Práctica (primero; después se comparan las diferencias)",
    phase_main: "Etiquetado principal",
    start: "Empezar",
    privacy: "🔒 El paquete nunca sale de esta pestaña. El progreso se guarda solo en este navegador.",
    bad_packet: "Este no es un paquete de etiquetado.",
    need_coder: "Escribe tu código de etiquetador.",
    prev: "Anterior", next: "Siguiente", next_open: "Siguiente sin responder", export: "Descargar archivo de etiquetas",
    progress: "{d} / {n} etiquetadas", instr: "Instrucción", steps: "Lo que hizo el agente", final: "Última respuesta",
    no_steps: "No se usaron herramientas.", no_final: "(sin respuesta de texto)",
    meta: "{session} · instrucción {index} · {calls} llamadas · {input} tokens de entrada · {output} de salida · {errors} errores · {subagents} subagentes",
    judge_h: "¿Hubo desperdicio en esta instrucción?",
    judge_lede: "Elige para cada tipo. Si la pantalla no da base para juzgar, elige «No sé». Si dos tipos se solapan, marca solo el de más arriba.",
    yes: "Sí", no: "No", unsure: "No sé",
    outcome_h: "¿El resultado cumplió lo pedido?",
    met: "Cumplió", partial: "En parte", not_met: "No cumplió",
    note: "Nota (opcional; se guarda en el archivo de etiquetas. No copies texto de la conversación)",
    guide: "Ver el código de desperdicio v1 completo",
    done: "Todas las instrucciones están etiquetadas. Descarga el archivo de etiquetas y envíalo al dueño de los datos.",
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
  ja: {
    W1: ["反復", "同じ作業を同じ結果でやり直した。変わっていないファイルの再読み込み、同じ資料の再取得。"],
    W2: ["失敗・再試行", "エラーや中断した呼び出し、同じ失敗の繰り返し、復旧のために文脈を読み直したこと。"],
    W3: ["連携の損失", "指示が別の場所に届いた、委任が拒否・放棄された、誰も読まなかったサブ作業、変化のない確認の繰り返し。"],
    W4: ["捨てられた成果物", "使われる前に削除・全面的に置き換えられたファイルや下書き、ユーザーが拒否した回答。"],
    W5: ["古い文脈", "終わった指示から持ち越され、この指示で使われなかった文脈。引用されなくても守られた制約は「使われた」とみなします。"],
    W6: ["キャッシュの再書き込み", "再開・モデル切り替え・期限切れで同じ前半部分をキャッシュに書き直したコスト。画面に根拠がなければ「不明」。"],
    W7: ["依頼外の作業", "依頼されておらず、使われもしなかった作業。"],
    W8: ["過剰な探索", "結果に反映されなかった読み込み・検索。サブエージェントの探索も含みます。結果が拠った探索はムダではありません。"],
  },
  zh: {
    W1: ["重复", "以相同结果重做了同样的工作：再次读取未改动的文件、再次获取同样的资料。"],
    W2: ["失败与重试", "出错或中断的调用、重复同样的失败、为恢复而重新读取的上下文。"],
    W3: ["协作损耗", "指令被送错地方、委托被拒绝或放弃、无人阅读的子任务、没有变化的反复检查。"],
    W4: ["被丢弃的产出", "在使用前被删除或整体替换的文件或草稿、被用户拒绝的回答。"],
    W5: ["陈旧上下文", "从已完成的指令带过来、在本条指令中未被使用的上下文。即使没有被引用，被遵守的约束也算「被使用」。"],
    W6: ["缓存重写", "因恢复会话、切换模型或过期而把相同的前缀重新写入缓存的成本。屏幕上没有依据时选「不确定」。"],
    W7: ["请求之外的工作", "没有人要求、也没有被使用的工作。"],
    W8: ["过度探索", "没有反映到结果中的读取和搜索，包括子智能体的探索。结果所依赖的探索不算浪费。"],
  },
  es: {
    W1: ["Duplicación", "El mismo trabajo rehecho con el mismo resultado: volver a leer un archivo sin cambios, volver a traer los mismos datos."],
    W2: ["Fallo y reintento", "Llamadas con error o interrumpidas, el mismo fallo repetido, contexto releído para recuperarse."],
    W3: ["Pérdida de coordinación", "Un traspaso enviado al lugar equivocado, una delegación rechazada o abandonada, trabajo de subagentes que nadie leyó, comprobaciones repetidas sin cambios."],
    W4: ["Resultado descartado", "Archivos o borradores borrados o reemplazados por completo antes de usarse, respuestas rechazadas por el usuario."],
    W5: ["Contexto obsoleto", "Contexto arrastrado de una instrucción terminada que no se usó en esta. Una restricción que se cumplió cuenta como usada aunque no se cite."],
    W6: ["Reescritura de caché", "Volver a escribir el mismo prefijo en la caché tras reanudar, cambiar de modelo o caducar. Elige «No sé» si la pantalla no da base."],
    W7: ["Trabajo no pedido", "Trabajo que nadie pidió y nadie usó."],
    W8: ["Exploración excesiva", "Lecturas y búsquedas que el resultado no usó, incluidas las de subagentes. La exploración en la que se apoyó el resultado no es desperdicio."],
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
  ja: ["ムダとは「結果を変えずに省けたトークン」です。",
    "ムダでないもの: 各呼び出しの基本設定、結果に反映された探索、テストなどの検証。",
    "種類が重なる場合は、上の種類 (W1 が一番上) にだけ「あり」を付けます。",
    "判断の根拠が画面にない場合は推測せず「不明」を選びます。「不明」も結果として数えます。",
    "判定は他の人と相談せず一人で行います。解釈の違いは練習の後にだけ合わせます。"],
  zh: ["浪费是指「不改变结果就能省去的 token」。",
    "不算浪费的：每次调用都需要的基本设定、结果所依赖的探索、测试等验证。",
    "类别重叠时，只在排在上面的类别 (W1 最上) 标记「有」。",
    "屏幕上没有判断依据时不要猜，选「不确定」。「不确定」也算作结果。",
    "独自标注，不与他人商量。只有在练习结束后才统一理解上的差异。"],
  es: ["El desperdicio son los tokens que podían quitarse sin cambiar el resultado.",
    "No es desperdicio: la base que necesita cada llamada, la exploración que usó el resultado, la verificación como las pruebas.",
    "Si dos tipos se solapan, marca «Sí» solo en el de más arriba (W1 es el más alto).",
    "Si la pantalla no da base para juzgar, no adivines: elige «No sé». «No sé» cuenta como respuesta.",
    "Etiqueta a solas, sin comentar los casos. Las diferencias se comentan solo después de la práctica."],
};

const $ = (id) => document.getElementById(id);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};
const LANGS = [["ko", "한국어"], ["en", "English"], ["ja", "日本語"], ["zh", "简体中文"], ["es", "Español"]];
const pick = (code) => (LANGS.find(([k]) => (code || "").toLowerCase().startsWith(k)) || [])[0];
let lang = pick(store.get("label-lang")) || pick(navigator.language) || "en";
const t = (k, vars = {}) => String(T[lang][k] ?? k).replace(/\{(\w+)\}/g, (_, x) => vars[x] ?? "");
const fmt = (n) => Number(n || 0).toLocaleString({ ko: "ko-KR", ja: "ja-JP", zh: "zh-CN", es: "es-ES" }[lang] || "en-US");

let packet = null;
let state = null; // { coder, phase, order: [ids], pos, labels: {id: {...}} }

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

function applyI18n() {
  document.documentElement.lang = lang === "zh" ? "zh-Hans" : lang;
  document.querySelectorAll("[data-t]").forEach((e) => { e.textContent = t(e.dataset.t); });
  $("lang").value = lang;
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
    if (s.result_chars != null) li.append(el("span", "lb-size", ` · ${fmt(s.result_chars)} ${t("chars")}`));
    if (s.error) li.append(el("span", "lb-size", ` · ${t("error")}`));
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
    coder: state.coder, ui_lang: lang, exported: new Date().toISOString(), items: state.order.length, labels };
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
for (const [k, name] of LANGS) { const o = el("option", null, name); o.value = k; $("lang").append(o); }
$("lang").addEventListener("change", () => { lang = $("lang").value; store.set("label-lang", lang); applyI18n(); });

applyI18n();
