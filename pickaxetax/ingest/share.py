"""Fetch public share links (ChatGPT, Claude, Gemini, ...) safely.

The server only fetches URLs on an explicit allowlist of AI share hosts
(SSRF protection), follows redirects manually and only within that list,
caps the response size, and keeps the page in memory only.

Share pages change format often, so parsing is best effort and layered:
1. provider JSON API (Claude snapshots)
2. JSON embedded in the HTML (``__NEXT_DATA__`` and similar)
3. role-attributed DOM (``data-message-author-role``)
"""

from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import urljoin, urlparse

import httpx

from ..models import ASSISTANT, USER, RawConversation, RawTurn
from .exports import parse_json

ALLOWED_HOSTS = {
    "chatgpt.com", "chat.openai.com",
    "claude.ai",
    "gemini.google.com", "g.co",
    "copilot.microsoft.com",
    "grok.com", "x.com",
    "www.perplexity.ai", "perplexity.ai",
    "chat.deepseek.com",
}
MAX_BYTES = 8 * 1024 * 1024
TIMEOUT = 15.0
UA = "pickaxetax/0.1 (+https://github.com/graviton94/pickaxetax; public-interest research)"


class ShareFetchError(ValueError):
    pass


def check_url(url: str) -> str:
    p = urlparse(url.strip())
    if p.scheme != "https":
        raise ShareFetchError("only https share links are accepted")
    host = (p.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise ShareFetchError(f"host not allowed: {host or '?'}")
    if p.port not in (None, 443) or p.username or p.password:
        raise ShareFetchError("unexpected port or credentials in url")
    return p.geturl()


def _get(client: httpx.Client, url: str, accept: str = "text/html,application/json") -> tuple[int, str]:
    """GET with allowlist-checked manual redirects and a size cap -> (status, body)."""
    for _ in range(5):
        url = check_url(url)
        with client.stream("GET", url, headers={"User-Agent": UA, "Accept": accept}) as r:
            if r.is_redirect:
                url = urljoin(url, r.headers.get("location", ""))
                continue
            body = bytearray()
            for chunk in r.iter_bytes():
                body += chunk
                if len(body) > MAX_BYTES:
                    raise ShareFetchError("share page too large")
            return r.status_code, body.decode(r.encoding or "utf-8", errors="replace")
    raise ShareFetchError("too many redirects")


_CLAUDE_SHARE = re.compile(r"/share/([0-9a-f-]{36})")


def _claude_snapshot(client: httpx.Client, url: str) -> list[RawConversation]:
    m = _CLAUDE_SHARE.search(urlparse(url).path)
    if not m:
        return []
    api = f"https://claude.ai/api/chat_snapshots/{m.group(1)}?rendering_mode=messages&render_all_tools=true"
    try:
        status, body = _get(client, api, accept="application/json")
        if status == 200:
            return parse_json(json.loads(body))
    except (ValueError, httpx.HTTPError):
        pass
    return []


_SCRIPT_JSON = re.compile(
    r"<script[^>]*(?:id=\"__NEXT_DATA__\"|type=\"application/json\")[^>]*>(.*?)</script>", re.S | re.I
)
_ROLE_DIV = re.compile(r"data-message-author-role=\"(user|assistant)\"[^>]*>(.*?)(?=data-message-author-role=|</main>|$)", re.S)
_TAG = re.compile(r"<[^>]+>")


def parse_share_html(page: str) -> list[RawConversation]:
    for m in _SCRIPT_JSON.finditer(page):
        try:
            found = parse_json(json.loads(m.group(1)))
        except ValueError:
            continue
        if found:
            return found
    turns = []
    for role, chunk in _ROLE_DIV.findall(page):
        text = htmllib.unescape(_TAG.sub(" ", chunk))
        text = re.sub(r"[ \t]+", " ", text).strip()
        if text:
            turns.append(RawTurn(USER if role == "user" else ASSISTANT, text))
    if any(t.role == USER for t in turns):
        return [RawConversation(turns=turns, source="html")]
    return []


def _source_for(host: str) -> str:
    if "openai" in host or "chatgpt" in host:
        return "chatgpt"
    if "claude" in host:
        return "claude"
    if "gemini" in host or host == "g.co":
        return "gemini"
    return host.split(".")[-2] if "." in host else host


def fetch_share(url: str, client: httpx.Client | None = None) -> list[RawConversation]:
    url = check_url(url)
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=False)
    try:
        host = urlparse(url).hostname or ""
        convs = _claude_snapshot(client, url) if host == "claude.ai" else []
        if not convs:
            status, body = _get(client, url)
            if status != 200:
                raise ShareFetchError(f"share page returned HTTP {status}")
            convs = parse_share_html(body)
        if not convs:
            raise ShareFetchError(
                "could not read this share page (it may be rendered client-side). "
                "Paste the conversation text or upload the JSON export instead."
            )
        for c in convs:
            c.source = _source_for(host)
        return convs
    except httpx.HTTPError as e:
        raise ShareFetchError(f"network error: {type(e).__name__}") from None
    finally:
        if own:
            client.close()
