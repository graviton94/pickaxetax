"""Local LLM proxy: measure every request, skip the ones that need no model.

Point an OpenAI-compatible client at ``http://127.0.0.1:8787/v1`` or the
Anthropic SDK at ``http://127.0.0.1:8787``. Requests are forwarded to the
real provider with the client's own credentials, which are never stored.

Defaults (each can be switched off):
* measure  -- tokens in/out/reasoning/re-sent context per request (counts only)
* compact  -- drop earlier pure thank-you exchanges from the history
* gratitude -- answer a bare "thanks" locally instead of re-reading the chat
Opt-in:
* cache    -- reuse responses to identical deterministic requests (local disk)
"""

from __future__ import annotations

import json
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .cache import ResponseCache, cacheable, request_key
from .formats import StreamMeter, local_reply, usage_from_json
from .ledger import Ledger
from .messages import ANTHROPIC, OPENAI, View, text_of

_HOP = {"host", "content-length", "connection", "accept-encoding", "transfer-encoding", "keep-alive"}
_RESP_DROP = {"content-length", "content-encoding", "transfer-encoding", "connection", "keep-alive"}
GRATITUDE_REPLY = {"ko": "🙏 (pickaxetax: 모델 호출 없이 로컬에서 응답했습니다)",
                   "en": "🙏 (pickaxetax: answered locally, no model call needed)"}
TYPICAL_ACK_REPLY_TOKENS = 40


@dataclass
class ProxyOptions:
    openai_base: str = "https://api.openai.com"
    anthropic_base: str = "https://api.anthropic.com"
    compact: bool = True
    gratitude: bool = True
    cache: bool = False
    cache_all: bool = False


def _fwd_headers(request: Request) -> dict:
    return {k: v for k, v in request.headers.items() if k.lower() not in _HOP}


def _resp_headers(r: httpx.Response, action: str) -> dict:
    h = {k: v for k, v in r.headers.items() if k.lower() not in _RESP_DROP}
    h["x-pickaxetax-action"] = action
    return h


def create_proxy_app(
    options: ProxyOptions | None = None,
    ledger: Ledger | None = None,
    cache: ResponseCache | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    opts = options or ProxyOptions()
    ledger = ledger or Ledger()
    if (opts.cache or opts.cache_all) and cache is None:
        raise ValueError("cache enabled but no ResponseCache given")
    client = httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(600.0, connect=15.0))

    @asynccontextmanager
    async def lifespan(_app):
        yield
        await client.aclose()

    app = FastAPI(title="pickaxetax proxy", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.ledger = ledger

    async def handle(request: Request, provider: str, path: str) -> Response:
        try:
            return await _handle(request, provider, path)
        except httpx.HTTPError as e:
            return JSONResponse({"error": {"type": "pickaxetax_upstream_error", "message": type(e).__name__}},
                                status_code=502)

    async def _handle(request: Request, provider: str, path: str) -> Response:
        raw = await request.body()
        try:
            body = json.loads(raw)
            assert isinstance(body, dict)
        except (ValueError, AssertionError):
            return await passthrough(request, provider, path, raw)

        view = View(provider, body)
        model = view.model
        est_in = view.input_estimate()

        # 1. a bare "thanks": answer locally, skip re-reading the whole chat
        if opts.gratitude and view.gratitude_only():
            last = text_of(view.messages[-1].get("content")) or ""
            lang = "ko" if re.search(r"[가-힣]", last) else "en"
            out, ctype = local_reply(provider, model, GRATITUDE_REPLY[lang], view.stream)
            ledger.record(provider=provider, model=model, action="gratitude_local", streamed=view.stream,
                          measured=False, avoided_input=est_in, avoided_output=TYPICAL_ACK_REPLY_TOKENS)
            return Response(out, media_type=ctype, headers={"x-pickaxetax-action": "gratitude_local"})

        # 2. drop earlier thank-you exchanges from the history
        compacted = view.compact() if opts.compact else 0
        if compacted:
            est_in -= compacted
            raw = json.dumps(body, ensure_ascii=False).encode()

        # 3. exact-duplicate cache (non-streaming, deterministic by default)
        key = None
        if cache is not None and not view.stream and cacheable(body, opts.cache_all):
            key = request_key(provider, body)
            hit = cache.get(key)
            if hit:
                ledger.record(provider=provider, model=model, action="cache_hit", streamed=False, measured=False,
                              avoided_input=est_in + compacted, avoided_output=hit[1])
                return Response(hit[0], media_type="application/json", headers={"x-pickaxetax-action": "cache_hit"})

        base = opts.openai_base if provider == OPENAI else opts.anthropic_base
        url = base.rstrip("/") + path
        if request.url.query:
            url += "?" + request.url.query
        headers = _fwd_headers(request)
        last_user = view.last_user_tokens()
        action = "forwarded+compacted" if compacted else "forwarded"

        if view.stream:
            req = client.build_request("POST", url, headers=headers, content=raw)
            r = await client.send(req, stream=True)
            if r.status_code >= 400:
                content = await r.aread()
                await r.aclose()
                ledger.record(provider=provider, model=model, action="error", streamed=True, measured=False)
                return Response(content, status_code=r.status_code, headers=_resp_headers(r, "error"))
            meter = StreamMeter(provider)

            async def relay():
                try:
                    async for chunk in r.aiter_bytes():
                        meter.feed(chunk)
                        yield chunk
                finally:
                    await r.aclose()
                    u, measured = meter.result(est_in)
                    ledger.record(provider=provider, model=model, action=action, streamed=True, measured=measured,
                                  history_tokens=max(0, u["input_tokens"] - last_user), avoided_input=compacted, **u)

            return StreamingResponse(relay(), status_code=r.status_code, headers=_resp_headers(r, action))

        r = await client.post(url, headers=headers, content=raw)
        if r.status_code >= 400:
            ledger.record(provider=provider, model=model, action="error", streamed=False, measured=False)
            return Response(r.content, status_code=r.status_code, headers=_resp_headers(r, "error"))
        try:
            u = usage_from_json(provider, r.json())
        except ValueError:
            u = None
        measured = u is not None
        u = u or {"input_tokens": est_in, "output_tokens": 0, "reasoning_tokens": 0, "cached_input_tokens": 0}
        ledger.record(provider=provider, model=model, action=action, streamed=False, measured=measured,
                      history_tokens=max(0, u["input_tokens"] - last_user), avoided_input=compacted, **u)
        if key is not None:
            cache.put(key, r.content, u["output_tokens"])
        return Response(r.content, status_code=r.status_code, headers=_resp_headers(r, action))

    async def passthrough(request: Request, provider: str, path: str, raw: bytes) -> Response:
        base = opts.openai_base if provider == OPENAI else opts.anthropic_base
        url = base.rstrip("/") + path + (("?" + request.url.query) if request.url.query else "")
        r = await client.request(request.method, url, headers=_fwd_headers(request), content=raw)
        return Response(r.content, status_code=r.status_code, headers=_resp_headers(r, "passthrough"))

    @app.post("/v1/chat/completions")
    async def openai_chat(request: Request):
        return await handle(request, OPENAI, "/v1/chat/completions")

    @app.post("/v1/messages")
    async def anthropic_messages(request: Request):
        return await handle(request, ANTHROPIC, "/v1/messages")

    @app.get("/pickaxetax/ledger")
    async def ledger_summary():
        return JSONResponse(ledger.summary())

    @app.api_route("/v1/{rest:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def other(request: Request, rest: str):
        # Anthropic-only endpoints go to Anthropic; everything else is OpenAI-compatible
        provider = ANTHROPIC if "anthropic-version" in request.headers else OPENAI
        return await passthrough(request, provider, f"/v1/{rest}", await request.body())

    return app
