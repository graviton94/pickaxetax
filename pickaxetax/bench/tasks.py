"""Trivial task set for measuring over-computation (CBI layer M).

Every task has a short, stable, unambiguous answer that needs no
reasoning. A model that spends hundreds of tokens (visible or hidden
reasoning) on them is over-computing. Correctness is graded leniently
(the right answer anywhere in the reply counts) so that verbosity shows
up in the token numbers, not as a failed answer.
"""

from __future__ import annotations

import hashlib
import json

TIER_TRIVIAL = "trivial"

# (id, prompt, accepted answers, kind)  kind: number | word
_RAW = [
    ("arith-add", "What is 17 + 25? Reply with the number only.", ["42"], "number"),
    ("arith-sub", "What is 100 - 37? Reply with the number only.", ["63"], "number"),
    ("arith-mul", "What is 6 times 7? Reply with the number only.", ["42"], "number"),
    ("arith-div", "What is 81 divided by 9? Reply with the number only.", ["9"], "number"),
    ("arith-sq", "What is 12 squared? Reply with the number only.", ["144"], "number"),
    ("count-week", "How many days are in a week? Reply with the number only.", ["7"], "number"),
    ("count-hours", "How many hours are in a day? Reply with the number only.", ["24"], "number"),
    ("count-min", "How many minutes are in an hour? Reply with the number only.", ["60"], "number"),
    ("conv-km", "How many meters are in 3 kilometers? Reply with the number only.", ["3000"], "number"),
    ("conv-dozen", "How many items are in two dozen? Reply with the number only.", ["24"], "number"),
    ("cmp-max", "Which is larger, 48 or 84? Reply with the number only.", ["84"], "number"),
    ("cmp-min", "Which is smallest: 9, 3, 7? Reply with the number only.", ["3"], "number"),
    ("cap-fr", "What is the capital of France? Reply with one word.", ["paris"], "word"),
    ("cap-jp", "What is the capital of Japan? Reply with one word.", ["tokyo"], "word"),
    ("cap-it", "What is the capital of Italy? Reply with one word.", ["rome"], "word"),
    ("cap-eg", "What is the capital of Egypt? Reply with one word.", ["cairo"], "word"),
    ("chem-au", "What is the chemical symbol for gold? Reply with the symbol only.", ["au"], "word"),
    ("chem-o", "What is the chemical symbol for oxygen? Reply with the symbol only.", ["o"], "word"),
    ("planet-big", "What is the largest planet in the Solar System? Reply with one word.", ["jupiter"], "word"),
    ("day-next", "What day comes after Monday? Reply with one word.", ["tuesday"], "word"),
    ("month-first", "What is the first month of the year? Reply with one word.", ["january"], "word"),
    ("opp-hot", "What is the opposite of 'hot'? Reply with one word.", ["cold"], "word"),
    ("opp-up", "What is the opposite of 'up'? Reply with one word.", ["down"], "word"),
    ("plural-mouse", "What is the plural of 'mouse'? Reply with one word.", ["mice"], "word"),
    ("color-mix", "What color do you get by mixing blue and yellow? Reply with one word.", ["green"], "word"),
    ("yesno-gt", "Is 10 greater than 3? Reply yes or no.", ["yes"], "word"),
    ("yesno-even", "Is 7 an even number? Reply yes or no.", ["no"], "word"),
    ("es-hello", "Translate 'hello' into Spanish. Reply with one word.", ["hola"], "word"),
    ("ko-cap", "대한민국의 수도는 어디입니까? 한 단어로만 답하세요.", ["서울"], "word"),
    ("ko-add", "2 더하기 3은 얼마입니까? 숫자만 답하세요.", ["5"], "number"),
]

TASKS = [
    {"id": i, "tier": TIER_TRIVIAL, "prompt": p, "answers": a, "kind": k}
    for i, p, a, k in _RAW
]

TASKSET_VERSION = "trivial-v1-" + hashlib.sha256(json.dumps(TASKS, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
