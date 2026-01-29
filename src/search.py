"""Vector search helpers built on the shared Chroma store."""

from typing import List

from langchain_core.documents import Document

from .database import get_vector_store, ingest_txt_folder, is_empty


def bootstrap_vector_store(docs_path: str = "docs"):
    # Always scan and upsert docs on startup to keep store in sync
    ingest_txt_folder(docs_path)


def search(query: str, k: int = 2) -> List[Document]:
    store = get_vector_store()
    results = store.similarity_search(query=query, k=k)
    return results
        
