"""Vector search helpers built on the shared Chroma store."""

from typing import List

from langchain_core.documents import Document

from .carriers import detect_carrier
from .database import get_vector_store, ingest_txt_folder, is_empty


def bootstrap_vector_store(docs_path: str = "docs"):
    # Always scan and upsert docs on startup to keep store in sync
    ingest_txt_folder(docs_path)


def search(query: str, k: int = 2) -> List[Document]:
    store = get_vector_store()
    carrier = detect_carrier(query)
    search_kwargs = {"query": query, "k": k}
    if carrier:
        search_kwargs["filter"] = {"carrier": carrier}
    results = store.similarity_search(**search_kwargs)
    if carrier and not results:
        results = store.similarity_search(query=query, k=k)
    return results
        
