from database import add_txt_file,read_docs, update_doc, delete_doc, persist
from search import vector_store
from search import search
import json
import os

from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage

from gemini_vision import vision_result

os.environ["GOOGLE_API_KEY"] = "AIzaSyBDHO0gEX4nN3IMefqloQ1V7k7ULVtac80"

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


def _extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        snippets = [item.get("text", "") for item in content if isinstance(item, dict) and "text" in item]
        if snippets:
            return "\n".join(snippets)
    return str(content)


# RAG Tools, from official docs
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """
    Retrieve information from vector store to help answer a query.
    """
    docs = vector_store.similarity_search(query, k=3)

    serialized = "\n\n".join(
        f"Content: {doc.page_content}\nMetadata: {doc.metadata}"
        for doc in docs
    )

    return serialized, docs

# 构建 Agent
tools = [retrieve_context]

system_prompt = (
    "你是一个物流赔付智能助手。"
    "当需要参考赔付规则时，请使用 retrieve_context 工具。"
    "请基于检索到的内容回答，禁止编造。"
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)


# 使用
damage_description = vision_result.content
if not isinstance(damage_description, str):
    damage_description = json.dumps(damage_description, ensure_ascii=False)

query = (
    "这个包裹是否应该赔付？"
    "包裹的损坏情况如下："
    f"{damage_description}"
)
result = agent.invoke({"messages": [HumanMessage(content=query)]})

if isinstance(result, dict):
    if "output" in result and isinstance(result["output"], str):
        print(result["output"])
    elif "messages" in result and result["messages"]:
        last_message = result["messages"][-1]
        content = getattr(last_message, "content", last_message)
        print(_extract_text(content))
    else:
        print(result)
else:
    print(_extract_text(result))