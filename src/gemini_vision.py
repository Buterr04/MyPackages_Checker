"""Gemini vision helper functions."""

import base64
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage

DEFAULT_API_KEY_B64 = "QUl6YVN5QkRITzBnRVg0bk4zSU1lZnFsb1ExVjd2azdVTFZ0YWM4MA=="
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)


def _get_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    return base64.b64decode(DEFAULT_API_KEY_B64).decode("utf-8")


@lru_cache(maxsize=1)
def get_vision_llm():
    os.environ.setdefault("GOOGLE_API_KEY", _get_api_key())
    model = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(model=model)


def _build_prompt(image_base64: str) -> HumanMessage:
    return HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Check this image and describe if this package is damaged or not. "
                    "If it is damaged, tell me where is the damage,for example: 'top left corner', or 'inside the box', etc. "
                    "Combine the damaged areas with the whole package,"
                    "give me the percentages."
                    "Return ONLY a JSON object with no markdown or backslash. "
                    "JSON format: {\"is_damaged\": true/false,"
                    "\"damage_location\","
                    "\"damaged_percentage\","
                    "\"damage_severity\": \"low/medium/high\"}"
                ),
            },
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"},
        ]
    )


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    if not image_bytes:
        raise ValueError("image_bytes is empty")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    llm = get_vision_llm()
    message = _build_prompt(image_base64)
    result = llm.invoke([message])
    raw_content = getattr(result, "content", result)

    parsed = None
    if isinstance(raw_content, dict):
        parsed = raw_content
    elif isinstance(raw_content, str):
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            parsed = None

    if parsed is not None:
        return {"raw": parsed, "parsed": parsed}
    return {"raw": raw_content, "parsed": None}


def analyze_image_path(path: str) -> Dict[str, Any]:
    with open(path, "rb") as f:
        return analyze_image_bytes(f.read())
