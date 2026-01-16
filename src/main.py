"""Core business logic for the package assessment agent."""

import base64
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .database import get_vector_store


DEFAULT_API_KEY_B64 = "QUl6YVN5QkRITzBnRVg0bk4zSU1lZnFsb1ExVjd2azdVTFZ0YWM4MA=="
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

def _get_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key

    # Fallback for convenience; consider overriding with your own key via env var.
    return base64.b64decode(DEFAULT_API_KEY_B64).decode("utf-8")


@lru_cache(maxsize=1)
def get_llm():
    os.environ.setdefault("GOOGLE_API_KEY", _get_api_key())
    model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(model=model)


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        snippets = [item.get("text", "") for item in content if isinstance(item, dict) and "text" in item]
        if snippets:
            return "\n".join(snippets)
    return str(content)


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information from the vector store to help answer a query."""
    docs = get_vector_store().similarity_search(query, k=3)
    serialized = "\n\n".join(
        f"Content: {doc.page_content}\nMetadata: {doc.metadata}"
        for doc in docs
    )
    return serialized, docs


@lru_cache(maxsize=1)
def get_agent():
    llm = get_llm()
    system_prompt = (
        "你是一个物流赔付智能助手。"
        "当需要参考赔付规则时，请使用 retrieve_context 工具。"
        "请基于检索到的内容回答，禁止编造。"
    )
    return create_agent(
        model=llm,
        tools=[retrieve_context],
        system_prompt=system_prompt,
    )


def assess_package(
    description: str,
    insured: bool | None = None,
    full_insured: bool | None = None,
) -> str:
    if not description:
        raise ValueError("description is required")

    agent = get_agent()
    insurance_status = (
        "未提供保价信息" if insured is None else "已完成保价" if insured else "未完成保价"
    )
    full_insurance_status = (
        "未提供足额保价信息" if full_insured is None else "已足额保价" if full_insured else "未足额保价"
    )
    query = (
        "这个包裹是否应该赔付？"
        "你需要自己根据检索结果进行决策并给出结果。"
        "我不能给你任何帮助信息，除了下面的描述。"
        "不要询问我任何问题，自己决策。" \
        "只给出结果和文档依据，不要多余的解释内容。"
        "保价情况："
        f"{insurance_status}\n"
        "足额保价情况："
        f"{full_insurance_status}\n"
        "包裹的损坏情况如下："
        f"{description}"
    )
    result = agent.invoke({"messages": [HumanMessage(content=query)]})

    if isinstance(result, dict):
        if "output" in result and isinstance(result["output"], str):
            return result["output"]
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            content = getattr(last_message, "content", last_message)
            return _extract_text(content)
        return json.dumps(result, ensure_ascii=False)

    return _extract_text(result)