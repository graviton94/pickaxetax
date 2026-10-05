"""Turn a skeleton into actionable advice: a one-shot prompt skeleton built
only from topic labels, plus concrete habits ranked by measured waste."""

from __future__ import annotations

from collections import Counter

from ..models import ASSISTANT, USER, Skeleton
from . import intent as I


def _uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _tip(code: str, weight: float, ko: str, en: str) -> dict:
    return {"code": code, "weight": round(weight, 1), "ko": ko, "en": en}


def suggest(sk: Skeleton) -> dict:
    m = sk.metrics
    w = m["waste"]
    users = [t for t in sk.turns if t.role == USER]
    counts = Counter(t.intent for t in sk.turns)

    # main thread = the branch that consumed the most tokens
    branch_tokens = Counter()
    for t in sk.turns:
        branch_tokens[t.branch] += t.tokens
    main = branch_tokens.most_common(1)[0][0] if branch_tokens else 0
    main_users = [t for t in users if t.branch == main]

    goal = _uniq((main_users[0].topics if main_users else []) + sk.agenda)[:3]
    details = _uniq(x for t in main_users[1:] if t.intent not in (I.CORRECT,) for x in t.topics if x not in goal)[:6]
    constraints = _uniq(x for t in users if t.intent in (I.CORRECT, I.CLARIFY) for x in t.topics if x not in goal)[:5]
    others = []
    for b in sorted({t.branch for t in users} - {main}):
        bt = _uniq(x for t in users if t.branch == b for x in t.topics)[:3]
        if bt:
            others.append(bt)
    wants_code = any(t.has_code for t in sk.turns if t.role == ASSISTANT)
    useful = sorted(t.tokens for t in sk.turns if t.role == ASSISTANT and not t.redundant) or [0]
    target_len = useful[len(useful) // 2]

    if sk.language == "ko":
        lines = [f"[목표] {', '.join(goal) or '…'}"]
        if details:
            lines.append(f"[세부 범위] {' → '.join(details)}")
        if constraints:
            lines.append(f"[제약·조건] {', '.join(constraints)} (처음부터 명시)")
        lines.append(f"[출력 형식] {'코드 포함, ' if wants_code else ''}핵심 위주로 약 {max(100, target_len // 2)} 토큰 이내")
        for o in others:
            lines.append(f"[별도 대화로] {', '.join(o)}")
    else:
        lines = [f"[Goal] {', '.join(goal) or '…'}"]
        if details:
            lines.append(f"[Scope] {' → '.join(details)}")
        if constraints:
            lines.append(f"[Constraints] {', '.join(constraints)} (state up front)")
        lines.append(f"[Output] {'include code, ' if wants_code else ''}essentials only, ~{max(100, target_len // 2)} tokens")
        for o in others:
            lines.append(f"[Separate chat] {', '.join(o)}")

    tips = []
    if counts[I.ACK]:
        tips.append(_tip("ack", w["ack_pct"],
            f"감사·확인 메시지 {counts[I.ACK]}회가 전체 연산의 {w['ack_pct']}%를 소모했습니다. 매번 전체 대화를 다시 읽기 때문입니다. 만족했다면 그냥 창을 닫으세요.",
            f"{counts[I.ACK]} thank-you/ok message(s) used {w['ack_pct']}% of all compute — each one re-reads the whole chat. If you're done, just close it."))
    redo = counts[I.CORRECT] + counts[I.RETRY]
    if redo:
        tips.append(_tip("redo", w["superseded_pct"],
            f"수정·재질문 {redo}회로 버려진 답변이 연산의 {w['superseded_pct']}%입니다. 조건({', '.join(constraints) or '대상, 형식, 범위'})을 첫 프롬프트에 넣으세요.",
            f"{redo} correction/retry turn(s) threw away answers worth {w['superseded_pct']}% of compute. Put constraints ({', '.join(constraints) or 'audience, format, scope'}) in the first prompt."))
    if m["branches"] > 1:
        tips.append(_tip("pivot", w["offtopic_context_pct"],
            f"주제가 {m['branches']}갈래로 나뉘었습니다. 관련 없는 이전 대화가 매 답변마다 재전송되어 연산의 {w['offtopic_context_pct']}%를 차지했습니다. 새 주제는 새 대화에서 시작하세요.",
            f"The chat split into {m['branches']} threads; unrelated history was re-sent on every reply ({w['offtopic_context_pct']}% of compute). Start a new chat for a new topic."))
    ctx = [t for t in users if t.intent == I.CONTEXT]
    if ctx:
        later = sum(1 for t in sk.turns if t.role == ASSISTANT and t.index > ctx[0].index)
        tips.append(_tip("paste", min(60.0, sum(t.tokens for t in ctx) * later / max(1, m["billed_input_tokens"]) * 100),
            f"대용량 붙여넣기({sum(t.tokens for t in ctx):,} 토큰)가 이후 {later}번의 답변마다 다시 읽혔습니다. 필요한 부분만 발췌하세요.",
            f"A large paste ({sum(t.tokens for t in ctx):,} tokens) was re-read on {later} later replies. Paste only the relevant excerpt."))
    if (m["verbosity_ratio"] or 0) > 8 and m["assistant_tokens"] > 1500:
        tips.append(_tip("verbose", 10.0,
            f"답변이 질문보다 {m['verbosity_ratio']}배 깁니다. '핵심만 5줄로'처럼 길이를 지정하세요.",
            f"Answers were {m['verbosity_ratio']}x longer than prompts. Ask for a length, e.g. 'five lines, essentials only'."))
    if counts[I.CONTINUE] >= 2:
        tips.append(_tip("continue", 5.0,
            f"'계속' 요청 {counts[I.CONTINUE]}회 — 긴 결과물은 섹션별로 나눠 요청하세요.",
            f"{counts[I.CONTINUE]} 'continue' prompts — request long outputs section by section."))
    if counts[I.FOLLOWUP_Q] >= 2:
        tips.append(_tip("underspecified", 5.0,
            f"AI가 {counts[I.FOLLOWUP_Q]}번 되물었습니다. 목표·대상·형식을 처음에 밝히세요.",
            f"The assistant had to ask back {counts[I.FOLLOWUP_Q]} times. State goal, audience and format first."))
    if len(users) > 20:
        tips.append(_tip("long", 5.0,
            "대화가 매우 깁니다. 턴마다 비용이 커지므로 중간 요약 후 새 대화로 이어가세요.",
            "Very long chat: every turn costs more than the last. Summarize and continue in a fresh chat."))
    tips.sort(key=lambda t: -t["weight"])
    return {"prompt_template": "\n".join(lines), "tips": tips}
