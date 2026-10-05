import json

import httpx
import pytest
from fastapi.testclient import TestClient

from pickaxetax.proxy import Ledger, ProxyOptions, ResponseCache, create_proxy_app
from pickaxetax.proxy.messages import View, is_gratitude


class Upstream:
    """Fake provider that records what it received."""

    def __init__(self, stream_events=None):
        self.calls = []
        self.stream_events = stream_events

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        self.calls.append({"url": str(request.url), "headers": dict(request.headers), "body": body})
        if body.get("stream"):
            return httpx.Response(200, headers={"content-type": "text/event-stream"},
                                  content="".join(f"data: {json.dumps(e)}\n\n" for e in self.stream_events) + "data: [DONE]\n\n")
        if request.url.path == "/v1/messages":
            return httpx.Response(200, json={"id": "msg_1", "type": "message", "role": "assistant",
                                             "content": [{"type": "text", "text": "hi"}],
                                             "usage": {"input_tokens": 120, "output_tokens": 7}})
        return httpx.Response(200, json={"id": "c1", "object": "chat.completion",
                                         "choices": [{"index": 0, "message": {"role": "assistant", "content": "hello"}}],
                                         "usage": {"prompt_tokens": 100, "completion_tokens": 20,
                                                   "completion_tokens_details": {"reasoning_tokens": 5}}})


@pytest.fixture
def setup(tmp_path):
    def make(opts=None, stream_events=None, with_cache=False):
        up = Upstream(stream_events)
        ledger = Ledger(str(tmp_path / "ledger.sqlite3"))
        cache = ResponseCache(str(tmp_path / "cache.sqlite3")) if with_cache else None
        app = create_proxy_app(opts or ProxyOptions(), ledger=ledger, cache=cache, transport=httpx.MockTransport(up))
        return TestClient(app), up, ledger
    return make


CHAT = [
    {"role": "user", "content": "Explain kubernetes pods"},
    {"role": "assistant", "content": "A pod is the smallest deployable unit."},
]


def test_forward_and_measure(setup):
    client, up, ledger = setup()
    r = client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "and services?"}]},
                    headers={"Authorization": "Bearer sk-test-secret"})
    assert r.status_code == 200 and r.json()["choices"][0]["message"]["content"] == "hello"
    assert up.calls[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert up.calls[0]["headers"]["authorization"] == "Bearer sk-test-secret"
    t = ledger.summary()["totals"]
    assert (t["input_tokens"], t["output_tokens"], t["reasoning_tokens"], t["measured_requests"]) == (100, 20, 5, 1)
    assert t["history_tokens"] > 0


def test_gratitude_answered_locally(setup):
    client, up, ledger = setup()
    r = client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "thanks!"}]})
    assert r.status_code == 200
    assert r.headers["x-pickaxetax-action"] == "gratitude_local"
    assert r.json()["choices"][0]["message"]["role"] == "assistant"
    assert up.calls == []
    assert ledger.summary()["totals"]["avoided_input"] > 0


@pytest.mark.parametrize("last,prev", [
    ("ok", "A pod is the smallest unit."),             # "ok" may mean "go ahead"
    ("네", "A pod is the smallest unit."),
    ("thanks!", "Shall I also explain services?"),     # answering a question
])
def test_not_short_circuited(setup, last, prev):
    client, up, _ = setup()
    msgs = [{"role": "user", "content": "Explain pods"}, {"role": "assistant", "content": prev}, {"role": "user", "content": last}]
    client.post("/v1/chat/completions", json={"model": "m", "messages": msgs})
    assert len(up.calls) == 1


def test_gratitude_with_tools_is_forwarded(setup):
    client, up, _ = setup()
    client.post("/v1/chat/completions", json={"model": "m", "tools": [{"type": "function"}],
                                              "messages": CHAT + [{"role": "user", "content": "thanks"}]})
    assert len(up.calls) == 1


def test_compaction_drops_old_thank_you_exchange(setup):
    client, up, ledger = setup()
    msgs = CHAT + [
        {"role": "user", "content": "고마워요"},
        {"role": "assistant", "content": "천만에요! 더 궁금한 점이 있으면 물어보세요."},
        {"role": "user", "content": "그럼 service는 뭐야?"},
    ]
    r = client.post("/v1/chat/completions", json={"model": "m", "messages": msgs})
    assert r.headers["x-pickaxetax-action"] == "forwarded+compacted"
    sent = up.calls[0]["body"]["messages"]
    assert [m["content"] for m in sent] == [CHAT[0]["content"], CHAT[1]["content"], "그럼 service는 뭐야?"]
    assert ledger.summary()["totals"]["avoided_input"] > 0


def test_options_disable_rewrites(setup):
    client, up, _ = setup(ProxyOptions(gratitude=False, compact=False))
    client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "thanks"}]})
    assert len(up.calls) == 1 and len(up.calls[0]["body"]["messages"]) == 3


def test_cache_only_deterministic(setup):
    client, up, ledger = setup(ProxyOptions(cache=True), with_cache=True)
    body = {"model": "m", "temperature": 0, "messages": CHAT + [{"role": "user", "content": "define pod"}]}
    client.post("/v1/chat/completions", json=body)
    r = client.post("/v1/chat/completions", json=body)
    assert r.headers["x-pickaxetax-action"] == "cache_hit" and len(up.calls) == 1
    client.post("/v1/chat/completions", json=dict(body, temperature=0.7))
    client.post("/v1/chat/completions", json=dict(body, temperature=0.7))
    assert len(up.calls) == 3
    assert ledger.summary()["totals"]["avoided_output"] == 20


def test_openai_stream_relay_and_usage(setup):
    events = [{"choices": [{"delta": {"content": "Hel"}}]}, {"choices": [{"delta": {"content": "lo"}}]},
              {"choices": [], "usage": {"prompt_tokens": 50, "completion_tokens": 2}}]
    client, up, ledger = setup(stream_events=events)
    with client.stream("POST", "/v1/chat/completions", json={"model": "m", "stream": True, "messages": CHAT + [{"role": "user", "content": "go"}]}) as r:
        text = "".join(r.iter_text())
    assert '"Hel"' in text and "[DONE]" in text
    t = ledger.summary()["totals"]
    assert (t["input_tokens"], t["output_tokens"], t["measured_requests"]) == (50, 2, 1)


def test_openai_stream_without_usage_is_estimated(setup):
    events = [{"choices": [{"delta": {"content": "some streamed answer text"}}]}]
    client, _, ledger = setup(stream_events=events)
    with client.stream("POST", "/v1/chat/completions", json={"model": "m", "stream": True, "messages": CHAT + [{"role": "user", "content": "go"}]}) as r:
        list(r.iter_bytes())
    t = ledger.summary()["totals"]
    assert t["measured_requests"] == 0 and t["output_tokens"] > 0 and t["input_tokens"] > 0


def test_anthropic_forward_and_local_stream(setup):
    client, up, ledger = setup()
    r = client.post("/v1/messages", json={"model": "claude-x", "max_tokens": 100, "messages": CHAT + [{"role": "user", "content": "more"}]},
                    headers={"x-api-key": "secret", "anthropic-version": "2023-06-01"})
    assert r.status_code == 200 and up.calls[0]["url"] == "https://api.anthropic.com/v1/messages"
    assert ledger.summary()["totals"]["input_tokens"] == 120

    with client.stream("POST", "/v1/messages", json={"model": "claude-x", "max_tokens": 100, "stream": True,
                                                     "messages": CHAT + [{"role": "user", "content": "thank you"}]}) as r:
        text = "".join(r.iter_text())
    assert "event: message_start" in text and "event: message_stop" in text
    assert len(up.calls) == 1


def test_upstream_error_passed_through(setup):
    def boom(request):
        return httpx.Response(401, json={"error": {"message": "bad key"}})
    ledger = Ledger(":memory:")
    client = TestClient(create_proxy_app(ledger=ledger, transport=httpx.MockTransport(boom)))
    r = client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "x"}]})
    assert r.status_code == 401
    assert ledger.summary()["groups"][0]["action"] == "error"


def test_ledger_never_stores_text_or_keys(setup, tmp_path):
    client, _, ledger = setup()
    client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "my secret roadmap zebra"}]},
                headers={"Authorization": "Bearer sk-live-verysecret"})
    ledger.close()
    data = (tmp_path / "ledger.sqlite3").read_bytes()
    assert b"zebra" not in data and b"verysecret" not in data and b"kubernetes" not in data


def test_ledger_export_is_aggregate(setup):
    client, _, ledger = setup()
    client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "x y z"}]})
    exp = json.loads(ledger.export())
    assert exp["schema"] == "pickaxetax.ledger.v1" and exp["rows"][0]["requests"] == 1


def test_gratitude_detection():
    assert is_gratitude("Thanks a lot!") and is_gratitude("감사합니다 🙏") and is_gratitude("ありがとう")
    assert not is_gratitude("thanks, now fix the bug in line 3") and not is_gratitude("ok") and not is_gratitude("")


def test_multimodal_messages_untouched():
    v = View("openai", {"messages": [
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "x"}}]},
        {"role": "assistant", "content": "a cat"},
        {"role": "user", "content": "thanks"},
    ]})
    assert v.gratitude_only()  # previous assistant turn is plain text
    v2 = View("openai", {"messages": [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}]},
        {"role": "user", "content": "thanks"},
    ]})
    assert not v2.gratitude_only()


def test_upstream_unreachable_is_502():
    def down(request):
        raise httpx.ConnectError("refused")
    client = TestClient(create_proxy_app(ledger=Ledger(":memory:"), transport=httpx.MockTransport(down)))
    r = client.post("/v1/chat/completions", json={"model": "m", "messages": CHAT + [{"role": "user", "content": "x"}]})
    assert r.status_code == 502 and r.json()["error"]["type"] == "pickaxetax_upstream_error"
