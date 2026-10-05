import json

import httpx
import pytest

from antitoken.ingest import ingest_text, parse_json, parse_transcript
from antitoken.ingest.share import ShareFetchError, check_url, fetch_share, parse_share_html
from antitoken.models import ASSISTANT, USER


def roles(conv):
    return [t.role for t in conv.turns]


def test_transcript_basic(ko_chat):
    conv = parse_transcript(ko_chat)
    assert len(conv.turns) == 12
    assert roles(conv)[:2] == [USER, ASSISTANT]
    assert "```ts" in conv.turns[5].text


@pytest.mark.parametrize("text", [
    "You said:\nhi there, explain monads\nChatGPT said:\nA monad is...",
    "## User\nexplain monads\n## Assistant\nA monad is...",
    "**User**: explain monads\n**Assistant**: A monad is...",
    "나: 모나드 설명해줘\n답변: 모나드는...",
    "Human: explain monads\n\nClaude: A monad is...",
])
def test_transcript_formats(text):
    conv = parse_transcript(text)
    assert roles(conv) == [USER, ASSISTANT]


def test_transcript_merges_consecutive_roles():
    conv = parse_transcript("User: a b c\nUser: d e f\nAssistant: ok")
    assert roles(conv) == [USER, ASSISTANT]


def test_transcript_without_markers_rejected():
    with pytest.raises(ValueError):
        parse_transcript("just some text without any roles")


def test_chatgpt_mapping_follows_current_branch():
    data = {
        "title": "t",
        "current_node": "c2",
        "mapping": {
            "root": {"message": None, "parent": None, "children": ["u1"]},
            "u1": {"message": {"author": {"role": "user"}, "content": {"parts": ["question one"]}}, "parent": "root", "children": ["a1", "a1b"]},
            "a1": {"message": {"author": {"role": "assistant"}, "content": {"parts": ["discarded regen"]}}, "parent": "u1", "children": []},
            "a1b": {"message": {"author": {"role": "assistant"}, "content": {"parts": ["kept answer"]}}, "parent": "u1", "children": ["c2"]},
            "c2": {"message": {"author": {"role": "user"}, "content": {"parts": ["follow up"]}}, "parent": "a1b", "children": []},
        },
    }
    [conv] = parse_json([data])
    assert conv.source == "chatgpt"
    assert [t.text for t in conv.turns] == ["question one", "kept answer", "follow up"]


def test_claude_export():
    data = [{"uuid": "x", "chat_messages": [
        {"sender": "human", "text": "hello claude", "content": []},
        {"sender": "assistant", "text": "", "content": [{"type": "text", "text": "hi!"}]},
    ]}]
    [conv] = parse_json(data)
    assert conv.source == "claude"
    assert [t.text for t in conv.turns] == ["hello claude", "hi!"]


def test_openai_messages():
    [conv] = parse_json({"messages": [
        {"role": "system", "content": "be nice"},
        {"role": "user", "content": [{"type": "text", "text": "q"}]},
        {"role": "assistant", "content": "a"},
    ]})
    assert roles(conv) == [USER, ASSISTANT]


def test_ingest_text_dispatches_json():
    convs = ingest_text(json.dumps([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]))
    assert len(convs) == 1


def test_share_html_next_data():
    payload = {"props": {"pageProps": {"serverResponse": {"data": {"linear_conversation": [
        {"message": {"author": {"role": "user"}, "content": {"parts": ["what is rust"]}}},
        {"message": {"author": {"role": "assistant"}, "content": {"parts": ["a language"]}}},
    ]}}}}}
    page = f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'
    [conv] = parse_share_html(page)
    assert roles(conv) == [USER, ASSISTANT]


def test_share_html_dom_fallback():
    page = ('<main><div data-message-author-role="user"><p>what is go</p></div>'
            '<div data-message-author-role="assistant"><p>a language &amp; runtime</p></div></main>')
    [conv] = parse_share_html(page)
    assert conv.turns[1].text == "a language & runtime"


@pytest.mark.parametrize("url", [
    "http://chatgpt.com/share/x",
    "https://evil.example.com/share/x",
    "https://169.254.169.254/latest/meta-data",
    "https://chatgpt.com:8443/share/x",
    "https://user:pw@chatgpt.com/share/x",
    "file:///etc/passwd",
])
def test_url_allowlist_rejects(url):
    with pytest.raises(ShareFetchError):
        check_url(url)


def test_fetch_share_blocks_redirect_off_allowlist():
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1:8080/admin"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ShareFetchError):
            fetch_share("https://chatgpt.com/share/abc", client=client)


def test_fetch_share_parses_page():
    page = ('<main><div data-message-author-role="user">explain kubernetes pods</div>'
            '<div data-message-author-role="assistant">a pod groups containers</div></main>')

    def handler(request):
        assert request.url.host == "chatgpt.com"
        return httpx.Response(200, text=page, headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        [conv] = fetch_share("https://chatgpt.com/share/abc", client=client)
    assert conv.source == "chatgpt"
    assert roles(conv) == [USER, ASSISTANT]


def test_fetch_claude_snapshot_api():
    sid = "12345678-1234-1234-1234-123456789abc"

    def handler(request):
        if request.url.path == f"/api/chat_snapshots/{sid}":
            return httpx.Response(200, json={"chat_messages": [
                {"sender": "human", "text": "q"}, {"sender": "assistant", "text": "a"}]})
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        [conv] = fetch_share(f"https://claude.ai/share/{sid}", client=client)
    assert conv.source == "claude"


def test_raw_conversation_repr_hides_text(ko_chat):
    assert "useEffect" not in repr(parse_transcript(ko_chat))
