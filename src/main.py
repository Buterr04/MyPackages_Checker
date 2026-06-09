"""Core business logic for the package assessment agent."""

import base64
import json
import os
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from .carriers import detect_carrier
from .database import get_vector_store
from .providers import get_chat_llm
from .vision_router import analyze_image_bytes_with_provider, analyze_image_path_with_provider
from .waybill import query_waybill_data
from .regulation_extractor import format_articles_for_llm, format_articles_for_output


DEFAULT_API_KEY_B64 = "QUl6YVN5QkRITzBnRVg0bk4zSU1lZnFsb1ExVjd2azdVTFZ0YWM4MA=="
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

def _get_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key

    # Fallback for convenience; consider overriding with your own key via env var.
    return base64.b64decode(DEFAULT_API_KEY_B64).decode("utf-8")


@lru_cache(maxsize=4)
def get_llm(provider: str | None = None):
    os.environ.setdefault("GOOGLE_API_KEY", _get_api_key())
    return get_chat_llm(provider)


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        snippets = [item.get("text", "") for item in content if isinstance(item, dict) and "text" in item]
        if snippets:
            return "\n".join(snippets)
    return str(content)


def retrieve_context_data(query: str):
    """Retrieve information from the vector store.
    
    With chunk-based ingestion, each article/section is a separate document,
    so similarity_search naturally returns article-level content.
    """
    store = get_vector_store()
    carrier = detect_carrier(query)
    search_kwargs: dict[str, Any] = {"query": query, "k": 5}
    if carrier:
        search_kwargs["filter"] = {"carrier": carrier}
    docs = store.similarity_search(**search_kwargs)
    if carrier and not docs:
        docs = store.similarity_search(query=query, k=5)
    
    # Format articles with metadata for display
    articles = []
    for doc in docs:
        article_num = doc.metadata.get("article", "相关内容")
        source_file = doc.metadata.get("source_file") or doc.metadata.get("source", "")
        carrier_name = doc.metadata.get("carrier")
        label = article_num
        if article_num == "相关内容" and source_file:
            label = source_file
        if carrier_name and carrier_name not in str(label):
            label = f"{carrier_name} - {label}"
        articles.append((label, doc.page_content))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_articles = []
    for article in articles:
        if article[0] not in seen:
            seen.add(article[0])
            unique_articles.append(article)
    
    # Format for LLM usage
    formatted_for_llm = format_articles_for_llm(unique_articles[:3])
    
    return formatted_for_llm, unique_articles


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Tool wrapper for retrieval."""
    return retrieve_context_data(query)


@tool
def query_waybill(waybill_no: str) -> dict:
    """Query a mock waybill data source using a waybill number."""
    return query_waybill_data(waybill_no)


@tool
def detect_damage_from_path(image_path: str, provider: str | None = None) -> dict:
    """Analyze an image file path and return structured damage information."""
    if not image_path:
        return {"error": "image_path_required"}
    try:
        return analyze_image_path_with_provider(image_path, provider)
    except FileNotFoundError:
        return {"error": "image_not_found"}
    except Exception as exc:  # pragma: no cover - defensive for runtime errors
        return {"error": f"vision_failed: {exc}"}


@tool
def detect_damage_from_base64(image_base64: str, provider: str | None = None) -> dict:
    """Analyze base64 image content and return structured damage information."""
    if not image_base64:
        return {"error": "image_base64_required"}
    try:
        image_bytes = base64.b64decode(image_base64)
    except (ValueError, TypeError):
        return {"error": "invalid_base64"}
    try:
        return analyze_image_bytes_with_provider(image_bytes, provider)
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
    llm_provider: str | None = None
    vision_provider: str | None = None
    image_path: str | None = None
    image_bytes: bytes | None = None
    damage_result: dict | None = None
    waybill_result: dict | None = None
    amount_reference: dict | None = None
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
    llm = get_llm(ctx.llm_provider)
    insurance_status = (
        "未提供保价信息" if ctx.insured is None else "已完成保价" if ctx.insured else "未完成保价"
    )
    full_insurance_status = (
        "未提供足额保价信息" if ctx.full_insured is None else "已足额保价" if ctx.full_insured else "未足额保价"
    )
    damage_payload = ctx.damage_result or {}
    waybill_payload = ctx.waybill_result or {}
    amount_reference = ctx.amount_reference or {}
    cost = waybill_payload.get("cost")
    price = waybill_payload.get("price")
    company = waybill_payload.get("company") or ctx.company
    prompt = (
        "你是一个物流赔付智能助手。"
        "请根据提供的规则内容与结构化信息给出赔付结论。"
        "若存在对应快递公司的条款，则以公司条款为准；否则使用邮政法作为规则。"
        "赔付金额需要参考给定的金额期望模型，但最终结论仍需受规则约束。"
        "要求：只输出“结论 + 依据”，并在依据中简要说明是否参考了金额模型，不要提问，不要虚构。"
        "结构化信息如下：\n"
        f"保价情况：{insurance_status}\n"
        f"足额保价情况：{full_insurance_status}\n"
        f"包裹描述：{ctx.description}\n"
        f"图像检测结果：{json.dumps(damage_payload, ensure_ascii=False)}\n"
        f"运单信息：{json.dumps(waybill_payload, ensure_ascii=False)}\n"
        f"金额参考模型：{json.dumps(amount_reference, ensure_ascii=False)}\n"
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


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _damage_weight_from_result(ctx: AgentContext) -> tuple[float, str]:
    damage = _normalize_damage(ctx)
    severity = str(damage.get("damage_severity") or "").strip().lower()
    is_damaged = damage.get("is_damaged")

    severity_map = {
        "轻微": 0.2,
        "轻度": 0.2,
        "minor": 0.2,
        "mild": 0.2,
        "中等": 0.5,
        "中度": 0.5,
        "moderate": 0.5,
        "严重": 0.8,
        "重度": 0.8,
        "severe": 0.8,
        "完全损毁": 1.0,
        "完全破损": 1.0,
        "totally_damaged": 1.0,
        "destroyed": 1.0,
    }
    if severity in severity_map:
        return severity_map[severity], f"按破损等级“{severity}”映射"
    if is_damaged is True:
        return 0.5, "已识别为破损，但缺少明确破损等级，使用默认中度权重"
    return 0.0, "未识别到破损，破损权重记为 0"


def _estimate_depreciation_rate(waybill: dict[str, Any]) -> tuple[float, str]:
    signed_at = _parse_date(waybill.get("signed_at"))
    if not signed_at:
        return 0.0, "缺少签收日期，折旧率记为 0"

    days_elapsed = max((date.today() - signed_at).days, 0)
    monthly_rate = 0.01
    depreciation = min((days_elapsed / 30.0) * monthly_rate, 0.3)
    return depreciation, f"按签收日期推算经过 {days_elapsed} 天，采用月折旧 1% 且最高 30% 的启发式估计"


def _estimate_residual_value(market_value: float, damage_weight: float) -> tuple[float, str]:
    if market_value <= 0 or damage_weight <= 0:
        return 0.0, "无有效货值或无破损，残值记为 0"
    residual_rate = max(0.0, 1.0 - damage_weight) * 0.2
    residual_value = market_value * residual_rate
    return residual_value, f"按剩余完好比例估算残值，残值率={residual_rate:.2%}"


def _build_amount_reference(ctx: AgentContext) -> dict:
    waybill = ctx.waybill_result or {}
    market_value = _to_float(waybill.get("price")) or 0.0
    insured_declared_value = market_value if ctx.insured else 0.0
    damage_weight, damage_weight_note = _damage_weight_from_result(ctx)
    depreciation_rate, depreciation_note = _estimate_depreciation_rate(waybill)
    residual_value, residual_note = _estimate_residual_value(market_value, damage_weight)

    capped_value = min(insured_declared_value, market_value)
    expected_amount = capped_value * damage_weight * (1 - depreciation_rate) - residual_value
    expected_amount = round(max(expected_amount, 0.0), 2)

    assumptions: list[str] = []
    if ctx.insured is not True:
        assumptions.append("未明确已保价时，保价声明价值按 0 处理")
    else:
        assumptions.append("当前运单未单独记录保价金额，暂以货值(price)代替保价声明价值")
    assumptions.append(damage_weight_note)
    assumptions.append(depreciation_note)
    assumptions.append(residual_note)

    formula = "E(x)=min(保价声明价值, 市场评估价值) × 破损权重 × (1-折旧率) - 残值"
    return {
        "formula": formula,
        "expected_amount": expected_amount,
        "insured_declared_value": round(insured_declared_value, 2),
        "market_value": round(market_value, 2),
        "damage_weight": round(damage_weight, 4),
        "depreciation_rate": round(depreciation_rate, 4),
        "residual_value": round(residual_value, 2),
        "assumptions": assumptions,
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
    llm_provider: str | None = None,
    vision_provider: str | None = None,
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
        llm_provider=llm_provider,
        vision_provider=vision_provider,
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
                ctx.damage_result = analyze_image_bytes_with_provider(
                    ctx.image_bytes, ctx.vision_provider
                )
            elif ctx.image_path:
                ctx.damage_result = analyze_image_path_with_provider(
                    ctx.image_path, ctx.vision_provider
                )
            state = AgentState.NEED_WAYBILL if ctx.waybill_no else AgentState.NEED_RULES
            continue

        if state == AgentState.NEED_WAYBILL:
            if ctx.waybill_no:
                ctx.waybill_result = query_waybill_data(ctx.waybill_no)
                _maybe_fill_insurance_from_waybill(ctx)
            state = AgentState.NEED_RULES
            continue

        if state == AgentState.NEED_RULES:
            ctx.amount_reference = _build_amount_reference(ctx)
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

    # Format rag_docs for output
    formatted_articles = format_articles_for_output(ctx.rag_docs) if ctx.rag_docs else None
    
    return {
        "decision": ctx.decision,
        "reasons": None,
        "damage_result": ctx.damage_result,
        "waybill_result": ctx.waybill_result,
        "amount_reference": ctx.amount_reference,
        "rag_text": ctx.rag_text,
        "formatted_articles": formatted_articles,
        "state_trace": ctx.state_trace,
    }
