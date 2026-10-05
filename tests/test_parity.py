"""The browser engine (site/engine.js) must produce exactly what the Python
engine produces. Runs both on fixtures and on randomized synthetic chats."""

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

import pickaxetax.tokens as tokens_mod
from pickaxetax.service import process_text

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")

VOLATILE = {"id", "created_at"}


def run_js(texts):
    r = subprocess.run([NODE, str(ROOT / "tests/parity/run_engine.mjs")], input=json.dumps(texts),
                       capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(r.stdout)


def run_py(texts, monkeypatch):
    monkeypatch.setattr(tokens_mod, "_ENC", None)  # browser has no tiktoken: compare heuristics
    out = []
    for t in texts:
        try:
            out.append({"ok": [r["skeleton"] for r in process_text(t, store=None, save=False)]})
        except ValueError as e:
            out.append({"error": str(e)})
    return out


def strip(result):
    if "ok" not in result:
        return result
    return {"ok": [{k: v for k, v in sk.items() if k not in VOLATILE} for sk in result["ok"]]}


POOL_USER = [
    "React에서 useEffect 무한 루프가 발생하는 이유를 알려줘", "useCallback 의존성 배열 예제 코드 보여줘",
    "How do I configure nginx as a reverse proxy for a node application?", "add websocket support to the nginx config",
    "그런데 파이썬 pandas 데이터프레임 병합 방법도 알려줘", "What is the difference between TCP and UDP?",
    "Explain kubernetes pods and services", "Rust의 소유권(ownership) 개념을 설명해줘", "Dockerfile 최적화 방법은?",
    "PostgreSQL index tuning for large tables", "how to write a binary search in python",
    "東京でおすすめのラーメン屋はどこですか？", "email me at jane.doe@example.org about the kubernetes cluster, call +82 10-9876-5432",
    "Can you summarize this article about climate policy?", "make it shorter and in bullet points",
]
POOL_ACK = ["thanks!", "고마워", "감사합니다 🙏", "ok", "네", "great", "thank you so much", "ㅇㅋ", "cool 👍"]
POOL_CORRECT = ["아니 그게 아니라 TypeScript로 작성해줘", "No, that's wrong. Use async/await.", "still not working, same error",
                "틀렸어 다시 해줘", "you missed the edge case"]
POOL_CONT = ["continue", "계속", "go on", "이어서 써줘", "more"]
POOL_ASST = [
    "useEffect 무한 루프는 의존성 배열에 매 렌더마다 새로 생성되는 객체가 들어갈 때 발생합니다. useCallback으로 고정하세요.",
    "Create a server block with proxy_pass pointing at your node application port and reload nginx.",
    "```python\ndef bsearch(a, x):\n    lo, hi = 0, len(a)\n    while lo < hi:\n        mid = (lo + hi) // 2\n```\nThis is a standard binary search.",
    "You're right, my apologies. Here is the corrected version with async/await.",
    "죄송합니다. 다시 작성했습니다. pandas의 merge와 concat을 사용하세요.",
    "Would you like me to also cover services and ingresses?",
    "TCP is connection-oriented and reliable; UDP is connectionless and faster. " * 6,
    "천만에요! 더 궁금한 점이 있으면 언제든 물어보세요. 😊",
    "I can't help with that request.",
    "Here are the key points:\n- policy A\n- policy B\n- tradeoffs\n" * 3,
]


def synth(seed: int) -> str:
    rnd = random.Random(seed)
    lines = []
    n = rnd.randint(1, 14)
    prev_user = None
    for i in range(n):
        r = rnd.random()
        if i == 0 or r < 0.45:
            u = rnd.choice(POOL_USER)
        elif r < 0.6:
            u = rnd.choice(POOL_ACK)
        elif r < 0.72:
            u = rnd.choice(POOL_CORRECT)
        elif r < 0.8:
            u = rnd.choice(POOL_CONT)
        elif r < 0.9 and prev_user:
            u = prev_user  # retry
        else:
            u = "Here is my code:\n```js\n" + "const x = compute(a, b);\n" * rnd.randint(30, 120) + "```\nwhy is it slow?"
        prev_user = u
        lines.append(f"User: {u}")
        if rnd.random() < 0.93:
            lines.append("Assistant: " + " ".join(rnd.choice(POOL_ASST) for _ in range(rnd.randint(1, 3))))
    return "\n".join(lines)


def fixtures():
    from tests.conftest import EN_CHAT, KO_CHAT  # noqa: WPS433

    mapping = {"current_node": "c2", "mapping": {
        "root": {"message": None, "parent": None, "children": ["u1"]},
        "u1": {"message": {"author": {"role": "user"}, "content": {"parts": ["explain git rebase vs merge"]}}, "parent": "root", "children": ["a1"]},
        "a1": {"message": {"author": {"role": "assistant"}, "content": {"parts": ["Rebase rewrites history; merge preserves it."]}}, "parent": "u1", "children": ["c2"]},
        "c2": {"message": {"author": {"role": "user"}, "content": {"parts": ["thanks!"]}}, "parent": "a1", "children": []},
    }}
    claude = [{"uuid": "x", "chat_messages": [
        {"sender": "human", "text": "Rust 소유권 개념을 설명해줘", "content": []},
        {"sender": "assistant", "text": "", "content": [{"type": "text", "text": "소유권은 메모리 안전성을 보장합니다."}]},
        {"sender": "human", "text": "고마워", "content": []},
    ]}]
    return [
        KO_CHAT, EN_CHAT, json.dumps(mapping), json.dumps(claude), json.dumps([mapping, mapping]),
        json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": "q about sql joins"}]}, {"role": "assistant", "content": "a"}]}),
        "You said:\nexplain monads in haskell\nChatGPT said:\nA monad is a design pattern.",
        "## User\n모나드를 설명해줘\n## Assistant\n모나드는 디자인 패턴입니다.",
        "no roles here at all", "", "[1, 2, 3]", '{"nothing": true}',
        "User: 😀😀😀 emoji heavy prompt about 🚀 rockets?\nAssistant: Rockets 🚀 use thrust.",
    ]


def test_parity_fixtures(monkeypatch):
    texts = fixtures()
    py, js = run_py(texts, monkeypatch), run_js(texts)
    for t, a, b in zip(texts, py, js):
        assert strip(a) == strip(b), f"mismatch for input: {t[:80]!r}"


def test_parity_synthetic(monkeypatch):
    texts = [synth(s) for s in range(300)]
    py, js = run_py(texts, monkeypatch), run_js(texts)
    bad = [i for i, (a, b) in enumerate(zip(py, js)) if strip(a) != strip(b)]
    assert not bad, f"{len(bad)} mismatches, first seed {bad[0]}"
