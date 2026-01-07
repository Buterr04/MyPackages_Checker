# database.py
# functions to interact with the Chroma vector stores
# include add_txt_file, create_docs, read_docs, update_doc, delete_doc, persist

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyBDHO0gEX4nN3IMefqloQ1V7k7ULVtac80"

vector_store = Chroma(
    collection_name="foo",
    persist_directory="chroma_store",
    embedding_function=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
)

# add txt file to vector store, usage: add_txt_file("path/to/yourfile.txt")
def add_txt_file(file_path: str):
    with open(file_path, 'r') as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": file_path})
    vector_store.add_documents(documents=[doc], ids=[file_path])

# create new documents, maybe deleted later
def create_docs():
    docs = [Document(page_content="new text", metadata={"lang": "en"})]
    vector_store.add_documents(documents=docs, ids=["new-1"])

# read documents based on query, may have no use
def read_docs(query: str):
    return vector_store.similarity_search(query=query, k=2)

# update document by id, usage: update_doc("doc_id", new_doc)
def update_doc(doc_id: str, new_doc: Document):
    vector_store.delete(ids=[doc_id])
    vector_store.add_documents(documents=[new_doc], ids=[doc_id])

# delete document by id, usage: delete_doc("doc_id")
def delete_doc(doc_id: str):
    vector_store.delete(ids=[doc_id])

# persist the vector store
def persist():
    vector_store.persist()