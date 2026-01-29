"""Model provider factory functions."""

import os
from functools import lru_cache


def _normalize_provider(provider: str | None) -> str:
    if not provider:
        return os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    return provider.strip().lower()


@lru_cache(maxsize=4)
def get_chat_llm(provider: str | None = None):
    provider = _normalize_provider(provider)
    if provider in {"openai", "openai_compat"}:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("langchain_openai is required for OpenAI providers") from exc
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        base_url = os.getenv("OPENAI_BASE_URL") if provider == "openai_compat" else None
        api_key = os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(model=model, base_url=base_url, api_key=api_key)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("langchain_google_genai is required for Gemini provider") from exc

    model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(model=model)
