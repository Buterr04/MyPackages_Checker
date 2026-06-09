"""FastAPI application exposing assessment and vision endpoints."""

import base64
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import date
from pydantic import BaseModel

from .database import get_vector_store, ingest_txt_folder, upsert_text_doc
from .vision_router import analyze_image_bytes_with_provider
from .vision_overlay import annotate_image_bytes, extract_damage_boxes
from .main import assess_package_stateful
from .waybill_db import import_from_excel_bytes, import_from_json, init_db, upsert_waybill
from .waybill import query_waybill_data

app = FastAPI(title="Packages Checker API")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VITE_DIST_DIR = PROJECT_ROOT / "front_end_vite" / "dist"
INDEX_FILE = VITE_DIST_DIR / "index.html"
FAVICON_FILES: dict[str, str] = {
    "favicon.ico": "image/x-icon",
    "favicon-16.png": "image/png",
    "favicon-32.png": "image/png",
    "favicon-48.png": "image/png",
    "glass-box-256.png": "image/png",
}

if (VITE_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=VITE_DIST_DIR / "assets"), name="assets")

class VisionAssessResponse(BaseModel):
    analysis: Any
    result: str | None = None
    reasons: list[str] | None = None
    amount_reference: dict[str, Any] | None = None
    rag: str | None = None
    annotated_image_base64: str | None = None
    annotated_image_mime: str | None = None


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


def ok(data: Any = None, message: str = "ok", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def error_response(
    message: str,
    *,
    status_code: int,
    code: str,
    detail: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "detail": detail,
            },
        },
    )


@app.on_event("startup")
async def _startup():
    # Initialize SQLite tables for waybills.
    init_db()


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Request failed")
        code = str(detail.get("code") or f"http_{exc.status_code}")
    else:
        message = str(detail or "Request failed")
        code = f"http_{exc.status_code}"
    return error_response(message, status_code=exc.status_code, code=code, detail=detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return error_response(
        "Request validation failed",
        status_code=422,
        code="validation_error",
        detail=exc.errors(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return error_response(
        "Internal server error",
        status_code=500,
        code="internal_error",
        detail=str(exc),
    )


@app.get("/", response_class=FileResponse)
async def index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(INDEX_FILE)


for filename, media_type in FAVICON_FILES.items():
    route_path = f"/{filename}"
    file_path = VITE_DIST_DIR / filename

    @app.get(route_path, response_class=FileResponse)
    async def _favicon(file_path: Path = file_path, media_type: str = media_type):
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(file_path, media_type=media_type)


@app.get("/info", response_class=FileResponse)
@app.get("/info.html", response_class=FileResponse)
async def info():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(INDEX_FILE)


@app.get("/detect", response_class=FileResponse)
@app.get("/detect.html", response_class=FileResponse)
async def detect():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(INDEX_FILE)


@app.get("/rules", response_class=FileResponse)
@app.get("/rules.html", response_class=FileResponse)
async def rules_page():
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
    return ok({"status": "ok"})


@app.post("/docs")
async def add_doc(payload: AddDocRequest):
    try:
        upsert_text_doc(payload.id, payload.content, payload.metadata or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok({"id": payload.id}, message="Document saved")


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
    return ok({"filename": file.filename, "saved_to": str(dest)}, message="Document uploaded")


@app.post("/docs/ingest")
async def ingest_docs():
    try:
        ingest_txt_folder("docs")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok({"started": True}, message="Vector store refresh started")


@app.post("/waybills")
async def upsert_waybill_api(payload: WaybillPayload):
    try:
        record = upsert_waybill(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok(record.model_dump(exclude={"id"}), message="Waybill saved")


@app.get("/waybills/{waybill_no}")
async def get_waybill_api(waybill_no: str):
    try:
        record = query_waybill_data(waybill_no)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not record or "error" in record:
        raise HTTPException(status_code=404, detail="waybill_not_found")
    return ok(record)


@app.post("/waybills/import")
async def import_waybills():
    try:
        count = import_from_json(Path("data") / "waybill_mock.json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok({"imported": count}, message="Waybills imported")


@app.post("/waybills/import-excel")
async def import_waybills_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    try:
        content = await file.read()
        imported, skipped = import_from_excel_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok({"imported": imported, "skipped": skipped}, message="Excel imported")


@app.get("/docs/list")
async def list_docs():
    try:
        store = get_vector_store()
        payload = store.get(include=["metadatas"])
        return ok({"ids": payload.get("ids", []), "metadatas": payload.get("metadatas", [])})
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

    payload = analysis if isinstance(analysis, dict) else {"raw": analysis}
    parsed = payload.get("parsed") if isinstance(payload, dict) else None
    boxes = extract_damage_boxes(parsed)
    if boxes:
        try:
            annotated_bytes, annotated_mime = annotate_image_bytes(image_bytes, boxes)
            payload["annotated_image_base64"] = base64.b64encode(annotated_bytes).decode("utf-8")
            payload["annotated_image_mime"] = annotated_mime
        except Exception:
            pass

    return ok(payload, message="Vision analysis completed")


@app.post("/vision-assess")
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

    payload = analysis if isinstance(analysis, dict) else {"raw": analysis}
    raw = payload.get("raw")
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
    annotated_image_base64 = None
    annotated_image_mime = None
    parsed = payload.get("parsed")
    boxes = extract_damage_boxes(parsed)
    if boxes:
        try:
            annotated_bytes, annotated_mime = annotate_image_bytes(image_bytes, boxes)
            annotated_image_base64 = base64.b64encode(annotated_bytes).decode("utf-8")
            annotated_image_mime = annotated_mime
        except Exception:
            pass

    return ok({
        "analysis": payload,
        "result": outcome.get("decision"),
        "reasons": outcome.get("reasons"),
        "amount_reference": outcome.get("amount_reference"),
        "rag": outcome.get("formatted_articles"),
        "annotated_image_base64": annotated_image_base64,
        "annotated_image_mime": annotated_image_mime,
    }, message="Vision assessment completed")
