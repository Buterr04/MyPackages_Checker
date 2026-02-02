"""FastAPI application exposing assessment and vision endpoints."""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import date
from pydantic import BaseModel

from .database import get_vector_store, ingest_txt_folder, upsert_text_doc
from .vision_router import analyze_image_bytes_with_provider
from .main import assess_package_stateful
from .waybill_db import import_from_excel_bytes, import_from_json, init_db, upsert_waybill
from .waybill import query_waybill_data

app = FastAPI(title="Packages Checker API")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VITE_DIST_DIR = PROJECT_ROOT / "front_end_vite" / "dist"
INDEX_FILE = VITE_DIST_DIR / "index.html"

if (VITE_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=VITE_DIST_DIR / "assets"), name="assets")

class VisionAssessResponse(BaseModel):
    analysis: Any
    result: str | None = None
    reasons: list[str] | None = None
    rag: str | None = None


class AddDocRequest(BaseModel):
    id: str
    content: str
    metadata: dict | None = None


class WaybillPayload(BaseModel):
    waybill_no: str
    company: str | None = None
    insured: bool | None = None
    full_insured: bool | None = None
    weight: float | None = None
    signed: bool | None = None
    signed_at: date | None = None
    status: str | None = None
    cost: float | None = None
    price: float | None = None
    route: list[str] | None = None


@app.on_event("startup")
async def _startup():
    # Initialize SQLite tables for waybills.
    init_db()


@app.get("/", response_class=FileResponse)
async def index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(INDEX_FILE)


@app.get("/info", response_class=FileResponse)
@app.get("/info.html", response_class=FileResponse)
async def info():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(INDEX_FILE)


@app.get("/waybills", response_class=FileResponse)
@app.get("/waybills.html", response_class=FileResponse)
async def waybills_page():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
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


@app.post("/docs/upload")
async def upload_doc(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename is required")
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_dir / file.filename
    try:
        content = await file.read()
        dest.write_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": file.filename, "saved_to": str(dest)}


@app.post("/docs/ingest")
async def ingest_docs():
    try:
        ingest_txt_folder("docs")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "ingest_started"}


@app.post("/waybills")
async def upsert_waybill_api(payload: WaybillPayload):
    try:
        record = upsert_waybill(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return record.model_dump(exclude={"id"})


@app.get("/waybills/{waybill_no}")
async def get_waybill_api(waybill_no: str):
    try:
        record = query_waybill_data(waybill_no)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not record or "error" in record:
        raise HTTPException(status_code=404, detail="waybill_not_found")
    return record


@app.post("/waybills/import")
async def import_waybills():
    try:
        count = import_from_json(Path("data") / "waybill_mock.json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"imported": count}


@app.post("/waybills/import-excel")
async def import_waybills_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    try:
        content = await file.read()
        imported, skipped = import_from_excel_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"imported": imported, "skipped": skipped}


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
