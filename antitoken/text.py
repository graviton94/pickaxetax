"""Text utilities: PII scrubbing, word extraction, keywords, fingerprints.

Everything here operates on raw text in memory and returns only derived
values (keyword labels, hashes, flags).
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

# --- PII scrubbing ---------------------------------------------------------
# Applied before any keyword extraction so that personal data can never
# become a stored topic label.

_PII_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # email
    re.compile(r"https?://\S+|www\.\S+"),  # urls
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # ipv4
    re.compile(r"\b(?:sk|pk|ghp|gho|xox[abp]|AKIA)[-_A-Za-z0-9]{12,}\b"),  # api keys
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),  # long opaque tokens / hashes
    re.compile(r"\+?\d[\d\s\-().]{7,}\d"),  # phone / card / id numbers
]


def scrub_pii(text: str) -> str:
    for pat in _PII_PATTERNS:
        text = pat.sub(" ", text)
    return text


# --- code blocks -----------------------------------------------------------

_FENCE = re.compile(r"```[^\n]*\n.*?(?:```|$)", re.S)


def split_code(text: str) -> tuple[str, bool]:
    """Remove fenced code; return (prose, had_code)."""
    prose, n = _FENCE.subn(" ", text)
    return prose, n > 0


# --- words -----------------------------------------------------------------

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#]*(?:[.\-][A-Za-z0-9+#]+)*|[가-힣]{2,}|[一-鿿぀-ヿ]{2,}")

# Common Korean particles / endings, longest first so the greedy strip works.
_KO_SUFFIXES = sorted(
    """
    입니다 습니다 합니다 해주세요 해줘요 해줘 해주 하세요 할까요 인가요 일까요 했는데 하는데 하려면
    에서는 에게서 으로는 으로서 으로써 이라고 이라는 라고 라는 처럼 보다 부터 까지 마다 조차 이나
    이랑 하고 에서 에게 한테 으로 로서 로써 이며 이고 인데 이요 이다 했다 한다 하는 하고 해서 하면
    은 는 이 가 을 를 에 의 도 만 로 와 과 나 랑 요 죠 다 고 며
    """.split(),
    key=len,
    reverse=True,
)


_STOP_KO_PARTICLES = set(_KO_SUFFIXES)


def _strip_ko(word: str) -> str:
    for suf in _KO_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            return word[: -len(suf)]
    return word


_STOP_EN = set(
    """
    a an the and or but if then else of to in on at by for with about from into over under as is are was
    were be been being do does did doing have has had having i me my we our you your he she it its they
    them their this that these those there here what which who whom whose when where why how can could
    would should will shall may might must not no yes ok okay so just also very really more most less
    some any all each every both few many much other such only own same than too s t don doesn didn isn
    aren wasn weren won wouldn shouldn couldn let lets get got make made use used using like want need
    please thanks thank hi hello hey sure great good nice well now one two first second new way thing
    things something anything everything give tell show explain write help know think see look try
    example examples following above below based case cases e.g i.e etc vs via per able
    """.split()
)

_STOP_KO = set(
    """
    그리고 그러나 그런데 하지만 그래서 그러면 또는 혹은 및 등 등등 것 거 수 때 중 더 좀 잘 왜 뭐 무엇
    어떻게 어떤 이런 저런 그런 이것 저것 그것 여기 저기 거기 우리 저희 제가 내가 너무 정말 진짜 아주
    매우 다시 계속 지금 이제 먼저 그냥 혹시 만약 경우 부분 관련 대한 대해 위해 통해 같은 같이 다른
    가능 있다 없다 있는 없는 있어 없어 있습 없습 하다 해요 했어 되다 된다 되는 됩니다 감사 고마워
    감사합니다 안녕 안녕하세요 네 예 아니 아니요 응 그래 알겠 알려 알려줘 설명 설명해 해줘 주세요
    예시 예를 정도 이상 이하 사용 방법 내용 생각 질문 답변 문제 부탁 제발 하나 두 번째 첫째 둘째
    """.split()
)


def detect_language(text: str) -> str:
    hangul = len(re.findall(r"[가-힣]", text))
    cjk = len(re.findall(r"[一-鿿]", text))
    kana = len(re.findall(r"[぀-ヿ]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    best = max(("ko", hangul * 2), ("ja", kana * 2), ("zh", cjk * 2), ("en", latin / 2), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "und"


def words(text: str) -> list[str]:
    """Normalized content words of a text (PII scrubbed, code removed)."""
    prose, _ = split_code(text)
    prose = scrub_pii(prose)
    out = []
    for w in _WORD.findall(prose):
        if w[0].isascii():
            w = w.lower().strip(".-")
            if len(w) < 3 and w not in {"ai", "ui", "ux", "db", "go", "js", "ts", "ml", "os", "c#", "c++", "r"}:
                continue
            if w in _STOP_EN or w.isdigit():
                continue
        elif "가" <= w[0] <= "힣":
            w = _strip_ko(w)
            if w in _STOP_KO or w in _STOP_KO_PARTICLES or len(w) < 2:
                continue
        out.append(w)
    return out


# --- keywords ----------------------------------------------------------------


def rank_keywords(user_texts: list[str], assistant_texts: list[str], top: int = 40) -> list[tuple[str, float]]:
    """Score candidate topic labels for one conversation.

    User words weigh more (they define the agenda); assistant words only
    contribute logarithmically so that verbose answers cannot dominate.
    A label must appear in at least one user turn, or twice overall, to
    qualify -- this keeps one-off rare words (often personal details) out.
    """
    u = Counter()
    u_docs = Counter()
    first = set(words(user_texts[0])) if user_texts else set()
    for t in user_texts:
        ws = words(t)
        u.update(ws)
        u_docs.update(set(ws))
    a = Counter()
    for t in assistant_texts:
        a.update(words(t))
    scores: dict[str, float] = {}
    for w in set(u) | set(a):
        total = u[w] + a[w]
        if u[w] == 0 and total < 3:
            continue
        if u[w] == 1 and a[w] == 0 and len(user_texts) > 3 and w not in first:
            continue  # mentioned once, never picked up: noise or private detail
        scores[w] = 2.0 * u[w] + 1.5 * u_docs[w] + math.log1p(a[w])
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:top]


# --- fingerprints --------------------------------------------------------------


def simhash(text: str, bits: int = 64, key: bytes = b"") -> int:
    """Locality-sensitive fingerprint. With a secret ``key`` the values are only
    comparable inside one deployment, so they cannot confirm a guessed text."""
    feats = words(text) or re.findall(r"\w+", text.lower())
    if not feats:
        return 0
    grams = feats + [f"{x} {y}" for x, y in zip(feats, feats[1:])]
    v = [0] * bits
    for g in grams:
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8, key=key[:64]).digest(), "big")
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(bits) if v[i] > 0)


def simhash_similarity(a: int, b: int, bits: int = 64) -> float:
    if a == 0 or b == 0:
        return 0.0
    return 1.0 - bin(a ^ b).count("1") / bits


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
