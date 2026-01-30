"""FastAPI application exposing assessment and vision endpoints."""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .database import get_vector_store, ingest_txt_folder, upsert_text_doc
from .vision_router import analyze_image_bytes_with_provider
from .main import assess_package_stateful

app = FastAPI(title="Packages Checker API")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "front_end"
INDEX_FILE = FRONTEND_DIR / "index.html"
INFO_FILE = FRONTEND_DIR / "info.html"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class VisionAssessResponse(BaseModel):
    analysis: Any
    result: str | None = None
    reasons: list[str] | None = None
    rag: str | None = None


class AddDocRequest(BaseModel):
    id: str
    content: str
    metadata: dict | None = None


@app.on_event("startup")
async def _startup():
    # Startup is kept lightweight; ingestion is manual via endpoint.
    pass


@app.get("/", response_class=FileResponse)
async def index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not found")
    return FileResponse(INDEX_FILE)


@app.get("/info.html", response_class=FileResponse)
async def info():
    if not INFO_FILE.exists():
        raise HTTPException(status_code=404, detail="info not found")
    return FileResponse(INFO_FILE)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/docs")
async def add_doc(payload: AddDocRequest):
    try:
        upsert_text_doc(payload.id, payload.content, payload.metadata or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": payload.id, "message": "ok"}


@app.post("/docs/ingest")
async def ingest_docs():
    try:
        ingest_txt_folder("docs")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "ingest_started"}


@app.get("/docs/list")
async def list_docs():
    try:
        store = get_vector_store()
        payload = store.get(include=["metadatas"])
        return {"ids": payload.get("ids", []), "metadatas": payload.get("metadatas", [])}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/vision")
async def vision(
    file: UploadFile = File(...),
    provider: str | None = Form(default=None),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    image_bytes = await file.read()
    try:
        analysis = analyze_image_bytes_with_provider(image_bytes, provider)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return analysis


@app.post("/vision-assess", response_model=VisionAssessResponse)
async def vision_assess(
    file: UploadFile = File(...),
    insured: bool | None = Form(default=None),
    full_insured: bool | None = Form(default=None),
    waybill_no: str | None = Form(default=None),
    provider: str | None = Form(default=None),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    image_bytes = await file.read()
    try:
        analysis = analyze_image_bytes_with_provider(image_bytes, provider)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw = analysis.get("raw") if isinstance(analysis, dict) else analysis
    description = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    try:
        outcome = assess_package_stateful(
            description=description,
            insured=insured,
            full_insured=full_insured,
            waybill_no=waybill_no,
            llm_provider=provider,
            vision_provider=provider,
            image_bytes=image_bytes,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "analysis": analysis,
        "result": outcome.get("decision"),
        "reasons": outcome.get("reasons"),
        "rag": outcome.get("rag_text"),
    }
