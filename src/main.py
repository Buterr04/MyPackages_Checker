"""Core business logic for the package assessment agent."""

import base64
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .database import get_vector_store
from .gemini_vision import analyze_image_bytes, analyze_image_path
from .waybill import query_waybill_data


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


def retrieve_context_data(query: str):
    """Retrieve information from the vector store to help answer a query."""
    docs = get_vector_store().similarity_search(query, k=3)
    serialized = "\n\n".join(
        f"Content: {doc.page_content}\nMetadata: {doc.metadata}"
        for doc in docs
    )
    return serialized, docs


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Tool wrapper for retrieval."""
    return retrieve_context_data(query)


@tool
def query_waybill(waybill_no: str) -> dict:
    """Query a mock waybill data source using a waybill number."""
    return query_waybill_data(waybill_no)


@tool
def detect_damage_from_path(image_path: str) -> dict:
    """Analyze an image file path and return structured damage information."""
    if not image_path:
        return {"error": "image_path_required"}
    try:
        return analyze_image_path(image_path)
    except FileNotFoundError:
        return {"error": "image_not_found"}
    except Exception as exc:  # pragma: no cover - defensive for runtime errors
        return {"error": f"vision_failed: {exc}"}


@tool
def detect_damage_from_base64(image_base64: str) -> dict:
    """Analyze base64 image content and return structured damage information."""
    if not image_base64:
        return {"error": "image_base64_required"}
    try:
        image_bytes = base64.b64decode(image_base64)
    except (ValueError, TypeError):
        return {"error": "invalid_base64"}
    try:
        return analyze_image_bytes(image_bytes)
    except Exception as exc:  # pragma: no cover - defensive for runtime errors
        return {"error": f"vision_failed: {exc}"}


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
        tools=[retrieve_context, query_waybill, detect_damage_from_path, detect_damage_from_base64],
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


class AgentState(str, Enum):
    INIT = "init"
    NEED_DAMAGE_INFO = "need_damage_info"
    NEED_WAYBILL = "need_waybill"
    NEED_RULES = "need_rules"
    DECIDE = "decide"
    DONE = "done"


@dataclass
class AgentContext:
    description: str
    insured: bool | None = None
    full_insured: bool | None = None
    waybill_no: str | None = None
    company: str | None = None
    image_path: str | None = None
    image_bytes: bytes | None = None
    damage_result: dict | None = None
    waybill_result: dict | None = None
    rag_text: str | None = None
    rag_docs: list[Any] = field(default_factory=list)
    decision: str | None = None
    state_trace: list[str] = field(default_factory=list)


def _maybe_fill_insurance_from_waybill(ctx: AgentContext) -> None:
    if not ctx.waybill_result or "error" in ctx.waybill_result:
        return
    if ctx.company is None:
        ctx.company = ctx.waybill_result.get("company")
    if ctx.insured is None:
        ctx.insured = ctx.waybill_result.get("insured")
    if ctx.full_insured is None:
        ctx.full_insured = ctx.waybill_result.get("full_insured")


def _build_rag_query(ctx: AgentContext) -> str:
    insurance_status = (
        "未提供保价信息" if ctx.insured is None else "已完成保价" if ctx.insured else "未完成保价"
    )
    full_insurance_status = (
        "未提供足额保价信息" if ctx.full_insured is None else "已足额保价" if ctx.full_insured else "未足额保价"
    )
    damage_hint = ""
    if ctx.damage_result and isinstance(ctx.damage_result.get("parsed"), dict):
        parsed = ctx.damage_result["parsed"]
        damage_hint = (
            f"图像检测结果：是否破损={parsed.get('is_damaged')}，"
            f"位置={parsed.get('damage_location')}，"
            f"程度={parsed.get('damage_severity')}。"
        )
    waybill_hint = ""
    if ctx.waybill_result and "error" not in ctx.waybill_result:
        cost = ctx.waybill_result.get("cost")
        price = ctx.waybill_result.get("price")
        company = ctx.waybill_result.get("company") or ctx.company
        if cost is not None or price is not None:
            waybill_hint = f"运费={cost}，货值={price}。"
        if company:
            waybill_hint += f"快递公司={company}。"
    return (
        "请检索与赔付规则相关的内容，优先匹配对应快递公司的条款；"
        "如果无匹配公司条款，请使用邮政法或通用规则。"
        "重点关注是否破损、保价与足额保价、签收状态等因素。"
        f"保价情况：{insurance_status}。"
        f"足额保价情况：{full_insurance_status}。"
        f"包裹描述：{ctx.description}。"
        f"{damage_hint}"
        f"{waybill_hint}"
    )


def _llm_decide(ctx: AgentContext) -> str:
    llm = get_llm()
    insurance_status = (
        "未提供保价信息" if ctx.insured is None else "已完成保价" if ctx.insured else "未完成保价"
    )
    full_insurance_status = (
        "未提供足额保价信息" if ctx.full_insured is None else "已足额保价" if ctx.full_insured else "未足额保价"
    )
    damage_payload = ctx.damage_result or {}
    waybill_payload = ctx.waybill_result or {}
    cost = waybill_payload.get("cost")
    price = waybill_payload.get("price")
    company = waybill_payload.get("company") or ctx.company
    prompt = (
        "你是一个物流赔付智能助手。"
        "请根据提供的规则内容与结构化信息给出赔付结论。"
        "若存在对应快递公司的条款，则以公司条款为准；否则使用邮政法作为规则。"
        "要求：只输出“结论 + 依据”，不要提问，不要虚构。"
        "结构化信息如下：\n"
        f"保价情况：{insurance_status}\n"
        f"足额保价情况：{full_insurance_status}\n"
        f"包裹描述：{ctx.description}\n"
        f"图像检测结果：{json.dumps(damage_payload, ensure_ascii=False)}\n"
        f"运单信息：{json.dumps(waybill_payload, ensure_ascii=False)}\n"
        f"快递公司：{company}\n"
        f"运费(cost)：{cost}\n"
        f"货值(price)：{price}\n"
        f"规则内容：\n{ctx.rag_text or ''}\n"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    content = getattr(result, "content", result)
    return _extract_text(content)


def _normalize_damage(ctx: AgentContext) -> dict:
    parsed = {}
    if ctx.damage_result and isinstance(ctx.damage_result.get("parsed"), dict):
        parsed = ctx.damage_result["parsed"]
    return {
        "is_damaged": parsed.get("is_damaged"),
        "damage_severity": parsed.get("damage_severity"),
        "damage_location": parsed.get("damage_location"),
    }


def _rule_engine_decide(ctx: AgentContext) -> dict:
    damage = _normalize_damage(ctx)
    is_damaged = damage.get("is_damaged")
    insured = ctx.insured
    full_insured = ctx.full_insured
    waybill = ctx.waybill_result or {}
    signed = waybill.get("signed")

    reasons: list[str] = []
    if is_damaged is False:
        reasons.append("图像识别结果显示未破损")
    elif is_damaged is True:
        reasons.append("图像识别结果显示存在破损")
    else:
        reasons.append("缺少明确的破损识别结果")

    if insured is True:
        reasons.append("运单显示已保价")
    elif insured is False:
        reasons.append("运单显示未保价")
    else:
        reasons.append("保价信息缺失")

    if full_insured is True:
        reasons.append("运单显示足额保价")
    elif full_insured is False:
        reasons.append("运单显示未足额保价")
    else:
        reasons.append("足额保价信息缺失")

    if signed is True:
        reasons.append("运单显示已签收")
    elif signed is False:
        reasons.append("运单显示未签收")
    else:
        reasons.append("签收信息缺失")

    decision = "待补充信息"
    if is_damaged is False:
        decision = "不予赔付"
    elif is_damaged is True:
        if insured is True:
            decision = "可赔付"
        elif insured is False:
            decision = "不予赔付"
        else:
            decision = "待补充信息"
    return {
        "decision": decision,
        "reasons": reasons,
        "damage": damage,
    }


def assess_package_stateful(
    description: str,
    insured: bool | None = None,
    full_insured: bool | None = None,
    waybill_no: str | None = None,
    image_path: str | None = None,
    image_bytes: bytes | None = None,
) -> dict:
    if not description:
        raise ValueError("description is required")

    ctx = AgentContext(
        description=description,
        insured=insured,
        full_insured=full_insured,
        waybill_no=waybill_no,
        image_path=image_path,
        image_bytes=image_bytes,
    )
    state = AgentState.INIT

    while state != AgentState.DONE:
        ctx.state_trace.append(state.value)

        if state == AgentState.INIT:
            if ctx.image_bytes or ctx.image_path:
                state = AgentState.NEED_DAMAGE_INFO
            elif ctx.waybill_no and (ctx.insured is None or ctx.full_insured is None):
                state = AgentState.NEED_WAYBILL
            else:
                state = AgentState.NEED_RULES
            continue

        if state == AgentState.NEED_DAMAGE_INFO:
            if ctx.image_bytes:
                ctx.damage_result = analyze_image_bytes(ctx.image_bytes)
            elif ctx.image_path:
                ctx.damage_result = analyze_image_path(ctx.image_path)
            state = AgentState.NEED_WAYBILL if ctx.waybill_no else AgentState.NEED_RULES
            continue

        if state == AgentState.NEED_WAYBILL:
            if ctx.waybill_no:
                ctx.waybill_result = query_waybill_data(ctx.waybill_no)
                _maybe_fill_insurance_from_waybill(ctx)
            state = AgentState.NEED_RULES
            continue

        if state == AgentState.NEED_RULES:
            query = _build_rag_query(ctx)
            rag_text, rag_docs = retrieve_context_data(query)
            ctx.rag_text = rag_text
            ctx.rag_docs = rag_docs
            state = AgentState.DECIDE
            continue

        if state == AgentState.DECIDE:
            ctx.decision = _llm_decide(ctx)
            state = AgentState.DONE
            continue

    return {
        "decision": ctx.decision,
        "reasons": None,
        "damage_result": ctx.damage_result,
        "waybill_result": ctx.waybill_result,
        "rag_text": ctx.rag_text,
        "state_trace": ctx.state_trace,
    }
