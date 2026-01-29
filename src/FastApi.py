"""FastAPI application exposing assessment and vision endpoints."""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .database import get_vector_store, upsert_text_doc
from .gemini_vision import analyze_image_bytes
from .main import assess_package_stateful
from .search import bootstrap_vector_store

app = FastAPI(title="Packages Checker API")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "front_end"
INDEX_FILE = FRONTEND_DIR / "index.html"


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
    # Load default txt rules into the vector store if missing
    bootstrap_vector_store()


@app.get("/", response_class=FileResponse)
async def index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not found")
    return FileResponse(INDEX_FILE)


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


@app.get("/docs/list")
async def list_docs():
    try:
        store = get_vector_store()
        payload = store.get(include=["metadatas"])
        return {"ids": payload.get("ids", []), "metadatas": payload.get("metadatas", [])}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/vision")
async def vision(file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    image_bytes = await file.read()
    try:
        analysis = analyze_image_bytes(image_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return analysis


@app.post("/vision-assess", response_model=VisionAssessResponse)
async def vision_assess(
    file: UploadFile = File(...),
    insured: bool | None = Form(default=None),
    full_insured: bool | None = Form(default=None),
    waybill_no: str | None = Form(default=None),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    image_bytes = await file.read()
    try:
        analysis = analyze_image_bytes(image_bytes)
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
