"""Rule-based intent classification (no model calls -- the analyzer itself
must not burn the tokens it is trying to save)."""

from __future__ import annotations

import re

# user intents
ASK = "ask"
INSTRUCT = "instruct"
CLARIFY = "clarify"  # adds constraints / details to the previous request
CORRECT = "correct"  # "no, that's wrong" -- previous answer missed
RETRY = "retry"  # near-duplicate of an earlier prompt
CONTINUE = "continue"  # "go on", "계속"
ACK = "ack"  # thanks / ok -- triggers a full-context reread for nothing
CONTEXT = "context"  # large paste of documents or code

# assistant intents
ANSWER = "answer"
CODE = "code"
FOLLOWUP_Q = "followup_question"
APOLOGY = "apology_fix"
REFUSAL = "refusal"

USER_INTENTS = [ASK, INSTRUCT, CLARIFY, CORRECT, RETRY, CONTINUE, ACK, CONTEXT]
ASSISTANT_INTENTS = [ANSWER, CODE, FOLLOWUP_Q, APOLOGY, REFUSAL]
LOW_VALUE_USER = {CORRECT, RETRY, ACK}


def _rx(*parts: str) -> re.Pattern:
    return re.compile("|".join(parts), re.I)


_ACK = _rx(
    r"^\W*(thanks?( you)?|thx|ty|ok(ay)?|cool|great|nice|perfect|awesome|got it|good|lol|haha)\W*$",
    r"^\W*(감사(합니다|해요)?|고마워(요)?|고맙습니다|ㄳ|ㄱㅅ|오케이|ㅇㅋ|좋아(요)?|굿|알겠(어|습니다)(요)?|넵|네+|응+|ㅎㅎ+|ㅋㅋ+)\W*$",
)
_CONTINUE = _rx(
    r"^\W*(continue|go on|keep going|more|next|and\??|proceed)\W*$",
    r"^\W*(계속(해(줘|주세요)?)?|이어서(\s*(해줘|써줘|작성해줘))?|더|다음|진행(해줘)?)\W*$",
)
_CORRECT = _rx(
    r"^\W*no\b", r"\bthat'?s (not|wrong)\b", r"\b(wrong|incorrect|doesn'?t work|not working|still (not|broken|wrong)|didn'?t work)\b",
    r"\bnot what i\b", r"\btry again\b", r"\byou (missed|forgot|ignored)\b", r"\bi said\b", r"\bstill (getting|the same)\b",
    r"^\W*아니", r"틀렸", r"틀린", r"잘못", r"그게 아니", r"다시 (해|작성|써|만들)", r"안 ?(돼|되|됨|된다)", r"오류", r"에러",
    r"말했잖", r"이해를 못", r"여전히", r"엉뚱",
)
_CLARIFY = _rx(
    r"^\W*(also|and also|but|however|additionally|actually|only|make it|instead|what if)\b", r"\b(in addition|one more thing|more specifically)\b",
    r"^\W*(그리고|추가로|단,?|대신|그럼|그러면|좀 더|조금 더|더 자세히|구체적으로|만약)",
)
_QUESTION = _rx(r"\?\s*$", r"^\W*(what|why|how|when|where|which|who|is|are|can|could|should|does|do)\b", r"(까요|나요|인가요|ㄹ까|는지|을까|가요|니\?|냐)\W*$")
_APOLOGY = _rx(r"^\W*(you'?re (absolutely )?right|my apologies|apologies|i apologi[sz]e|sorry)", r"^\W*(죄송합니다|맞습니다|말씀하신 대로|정확한 지적|사과드립니다)")
_REFUSAL = _rx(r"^\W*(i can'?t|i cannot|i'?m (not able|unable)|i won'?t)", r"(도와드릴 수 없|제공할 수 없|답변드릴 수 없)")


def classify_user(text: str, tokens: int, similar_to_earlier: bool, has_code: bool, first: bool = False) -> str:
    t = text.strip()
    if first:  # nothing to correct, retry, continue or thank yet
        if tokens >= 600 or (has_code and tokens >= 250):
            return CONTEXT
        return ASK if (_QUESTION.search(t[-200:]) or _QUESTION.search(t[:80])) else INSTRUCT
    if similar_to_earlier and tokens > 3:
        return RETRY
    if tokens <= 12 and _ACK.search(t):
        return ACK
    if tokens <= 12 and _CONTINUE.search(t):
        return CONTINUE
    if tokens >= 600 or (has_code and tokens >= 250):
        return CONTEXT
    if _CORRECT.search(t[:240]):
        return CORRECT
    if _CLARIFY.search(t[:120]):
        return CLARIFY
    if _QUESTION.search(t[-200:]) or _QUESTION.search(t[:80]):
        return ASK
    return INSTRUCT


def classify_assistant(text: str, tokens: int, has_code: bool) -> str:
    t = text.strip()
    head = t[:200]
    if _APOLOGY.search(head):
        return APOLOGY
    if _REFUSAL.search(head) and tokens < 300:
        return REFUSAL
    if tokens < 120 and t.endswith("?"):
        return FOLLOWUP_Q
    if has_code:
        return CODE
    return ANSWER
