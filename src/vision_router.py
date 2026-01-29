"""Vision provider router."""

from typing import Any, Dict

from .gemini_vision import analyze_image_bytes as gemini_analyze_bytes
from .gemini_vision import analyze_image_path as gemini_analyze_path
from .openai_vision import analyze_image_bytes as openai_analyze_bytes
from .openai_vision import analyze_image_path as openai_analyze_path


def _normalize_provider(provider: str | None) -> str:
    return (provider or "gemini").strip().lower()


def analyze_image_bytes_with_provider(image_bytes: bytes, provider: str | None = None) -> Dict[str, Any]:
    provider = _normalize_provider(provider)
    if provider in {"openai", "openai_compat"}:
        return openai_analyze_bytes(image_bytes)
    return gemini_analyze_bytes(image_bytes)


def analyze_image_path_with_provider(image_path: str, provider: str | None = None) -> Dict[str, Any]:
    provider = _normalize_provider(provider)
    if provider in {"openai", "openai_compat"}:
        return openai_analyze_path(image_path)
    return gemini_analyze_path(image_path)
