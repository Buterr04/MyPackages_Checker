"""Utilities for drawing detection boxes on images."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any, Iterable, List


@dataclass
class DamageBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    label: str = "damage"
    confidence: float | None = None


def _pick_box_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ("damage_boxes", "boxes", "bboxes", "bounding_boxes"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _coerce_box(raw: dict[str, Any]) -> DamageBox | None:
    def _first(*keys: str) -> Any:
        for key in keys:
            if key in raw:
                return raw[key]
        return None

    x_min = _first("x_min", "xmin", "left")
    y_min = _first("y_min", "ymin", "top")
    x_max = _first("x_max", "xmax", "right")
    y_max = _first("y_max", "ymax", "bottom")

    try:
        x_min = float(x_min)
        y_min = float(y_min)
        x_max = float(x_max)
        y_max = float(y_max)
    except (TypeError, ValueError):
        return None

    if x_max <= x_min or y_max <= y_min:
        return None

    label = str(_first("label", "name", "type") or "damage")
    confidence = _first("confidence", "score")
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None

    return DamageBox(
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
        label=label,
        confidence=confidence,
    )


def extract_damage_boxes(payload: Any) -> list[DamageBox]:
    return [box for raw in _pick_box_list(payload) if (box := _coerce_box(raw))]


def _is_normalized(boxes: Iterable[DamageBox]) -> bool:
    max_value = max((max(box.x_max, box.y_max) for box in boxes), default=0.0)
    return max_value <= 1.5


def annotate_image_bytes(image_bytes: bytes, boxes: List[DamageBox]) -> tuple[bytes, str]:
    from PIL import Image, ImageDraw, ImageFont

    if not boxes:
        raise ValueError("boxes is empty")

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    normalized = _is_normalized(boxes)

    for idx, box in enumerate(boxes, start=1):
        x_min = box.x_min * width if normalized else box.x_min
        x_max = box.x_max * width if normalized else box.x_max
        y_min = box.y_min * height if normalized else box.y_min
        y_max = box.y_max * height if normalized else box.y_max

        x_min = max(0, min(width - 1, x_min))
        x_max = max(0, min(width - 1, x_max))
        y_min = max(0, min(height - 1, y_min))
        y_max = max(0, min(height - 1, y_max))

        color = (255, 80, 80)
        draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=3)

        label = box.label or f"damage {idx}"
        if box.confidence is not None:
            label = f"{label} {box.confidence:.2f}"
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        text_x = x_min
        text_y = max(0, y_min - text_h - 4)

        draw.rectangle(
            [text_x, text_y, text_x + text_w + 6, text_y + text_h + 4],
            fill=(0, 0, 0),
        )
        draw.text((text_x + 3, text_y + 2), label, fill=(255, 255, 255), font=font)

    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue(), "image/png"
