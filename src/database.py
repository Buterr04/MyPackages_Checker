"""Shared vector store utilities (Chroma + Gemini embeddings)."""

import base64
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

PERSIST_DIR = "chroma_store"
COLLECTION_NAME = "foo"
DEFAULT_API_KEY_B64 = "QUl6YVN5QkRITzBnRVg0bk4zSU1lZnFsb1ExVjd2azdVTFZ0YWM4MA=="
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)


def _get_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    return base64.b64decode(DEFAULT_API_KEY_B64).decode("utf-8")


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    # Lazy init so imports do not trigger side effects
    os.environ.setdefault("GOOGLE_API_KEY", _get_api_key())
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
        embedding_function=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
    )


def add_txt_file(file_path: str):
    store = get_vector_store()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": file_path})
    store.add_documents(documents=[doc], ids=[file_path])


def add_documents(docs: Iterable[Document], ids: Iterable[str]):
    store = get_vector_store()
    store.add_documents(documents=list(docs), ids=list(ids))


def upsert_text_doc(doc_id: str, content: str, metadata: Optional[Dict] = None, persist_after: bool = True):
    if not doc_id:
        raise ValueError("doc_id is required")
    if not content:
        raise ValueError("content is required")

    store = get_vector_store()
    metadata = metadata or {}
    store.delete(ids=[doc_id])
    doc = Document(page_content=content, metadata=metadata)
    store.add_documents(documents=[doc], ids=[doc_id])
    if persist_after:
        _persist_store(store)


def read_docs(query: str, k: int = 2):
    store = get_vector_store()
    return store.similarity_search(query=query, k=k)


def update_doc(doc_id: str, new_doc: Document):
    store = get_vector_store()
    store.delete(ids=[doc_id])
    store.add_documents(documents=[new_doc], ids=[doc_id])


def delete_doc(doc_id: str):
    store = get_vector_store()
    store.delete(ids=[doc_id])


def persist():
    store = get_vector_store()
    _persist_store(store)


def is_empty() -> bool:
    store = get_vector_store()
    try:
        return store._collection.count() == 0  # type: ignore[attr-defined]
    except Exception:
        return False


def ingest_txt_folder(folder_path: str):
    folder = Path(folder_path)
    if not folder.exists():
        return
    for file_path in folder.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        upsert_text_doc(str(file_path), content, metadata={"source": str(file_path)}, persist_after=False)
    _persist_store(get_vector_store())


def _persist_store(store: Chroma):
    """Persist if the current Chroma backend supports it."""
    if hasattr(store, "persist"):
        store.persist()
