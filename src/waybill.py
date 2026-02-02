"""Waybill query helper (DB first, fallback to mock)."""

import json
from pathlib import Path

from .waybill_db import query_waybill_db


WAYBILL_MOCK_PATH = Path(__file__).resolve().parent.parent / "data" / "waybill_mock.json"


def query_waybill_data(waybill_no: str) -> dict:
    """Return mock waybill data for the given waybill number."""
    if not waybill_no:
        return {"error": "waybill_no_required"}
    db_result = query_waybill_db(waybill_no)
    if db_result:
        return db_result
    if not WAYBILL_MOCK_PATH.exists():
        return {"error": "waybill_data_not_found"}
    with WAYBILL_MOCK_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(waybill_no, {"error": "waybill_not_found"})
