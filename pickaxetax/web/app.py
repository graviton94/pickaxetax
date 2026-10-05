"""HTTP API + single-page UI."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..graph import GraphStore, skeleton_cypher, skeleton_graph_json, topics_cypher
from ..service import process_bytes, process_text

STATIC = Path(__file__).parent / "static"
MAX_BODY = 10 * 1024 * 1024


class AnalyzeRequest(BaseModel):
    input: str = Field(..., description="share URL, JSON export, or pasted transcript")
    save: bool = Field(True, description="contribute the anonymous skeleton to the public graph")


def create_app(store: GraphStore | None = None) -> FastAPI:
    store = store or GraphStore(os.environ.get("PICKAXETAX_DB", "data/pickaxetax.sqlite3"))
    app = FastAPI(title="Pickaxe Tax", version="0.1.0", docs_url="/api/docs", redoc_url=None)
    app.state.store = store

    @app.middleware("http")
    async def limit_body(request: Request, call_next):
        if int(request.headers.get("content-length") or 0) > MAX_BODY:
            return JSONResponse({"detail": "request too large"}, status_code=413)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def _run(fn, payload, save: bool):
        try:
            return {"results": fn(payload, store=store, save=save)}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from None

    @app.post("/api/analyze")
    def analyze_text(req: AnalyzeRequest):
        return _run(process_text, req.input, req.save)

    @app.post("/api/analyze/file")
    async def analyze_file(file: UploadFile = File(...), save: bool = Form(True)):
        data = await file.read(MAX_BODY + 1)
        if len(data) > MAX_BODY:
            raise HTTPException(status_code=413, detail="file too large")
        return _run(process_bytes, data, save)

    def _get(skeleton_id: str):
        sk = store.get(skeleton_id)
        if sk is None:
            raise HTTPException(status_code=404, detail="not found")
        return sk

    @app.get("/api/conversations/{skeleton_id}")
    def get_conversation(skeleton_id: str):
        return _get(skeleton_id).to_dict()

    @app.get("/api/conversations/{skeleton_id}/graph.json")
    def get_graph(skeleton_id: str):
        return skeleton_graph_json(_get(skeleton_id))

    @app.get("/api/conversations/{skeleton_id}/cypher", response_class=PlainTextResponse)
    def get_cypher(skeleton_id: str):
        return skeleton_cypher(_get(skeleton_id))

    @app.delete("/api/conversations/{skeleton_id}")
    def delete_conversation(skeleton_id: str, x_delete_token: str = Header(...)):
        if not store.delete(skeleton_id, x_delete_token):
            raise HTTPException(status_code=404, detail="not found or wrong token")
        return {"deleted": skeleton_id}

    @app.get("/api/stats")
    def stats():
        return store.stats()

    @app.get("/api/topics")
    def topics(k: int = 0, limit: int = 100):
        return store.topics(k=k, limit=min(limit, 500))

    @app.get("/api/topics/cypher", response_class=PlainTextResponse)
    def topics_export(k: int = 0):
        return topics_cypher(store.topics(k=k, limit=5000))

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/c/{skeleton_id}", include_in_schema=False)
    @app.get("/explore", include_in_schema=False)
    def index(skeleton_id: str | None = None):
        return FileResponse(STATIC / "index.html")

    return app
