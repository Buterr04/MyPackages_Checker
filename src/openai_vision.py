"""OpenAI-compatible vision helper functions."""

import base64
import json
import os
from functools import lru_cache
from typing import Any, Dict

from langchain.messages import HumanMessage


@lru_cache(maxsize=1)
def get_openai_vision_llm():
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("langchain_openai is required for OpenAI vision") from exc
    model = os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    force_json = os.getenv("OPENAI_FORCE_JSON", "true").strip().lower() in {"1", "true", "yes", "on"}
    model_kwargs = {"response_format": {"type": "json_object"}} if force_json else None
    return ChatOpenAI(model=model, base_url=base_url, api_key=api_key, model_kwargs=model_kwargs)


def _build_prompt(image_base64: str) -> HumanMessage:
    return HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Check this image and describe if this package is damaged or not. "
                    "If it is damaged, tell me where is the damage, for example: "
                    "'top left corner', or 'inside the box', etc. "
                    "Combine the damaged areas with the whole package, "
                    "give me the percentages. "
                    "Return ONLY a JSON object with no markdown or backslash. "
                    "JSON format: {\"is_damaged\": true/false, "
                    "\"damage_location\": \"...\","
                    "\"damaged_percentage\": number, "
                    "\"damage_severity\": \"low/medium/high\", "
                    "\"damage_boxes\": [{\"label\": \"...\", "
                    "\"x_min\": 0-1, \"y_min\": 0-1, \"x_max\": 0-1, \"y_max\": 0-1, "
                    "\"confidence\": 0-1}]}"
                ),
            },
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ]
    )


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    if not image_bytes:
        raise ValueError("image_bytes is empty")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    llm = get_openai_vision_llm()
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
