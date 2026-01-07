from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from langchain_chroma import Chroma

os.environ["GOOGLE_API_KEY"] = "AIzaSyBDHO0gEX4nN3IMefqloQ1V7k7ULVtac80"

# persist directory
PERSIST_DIR = "chroma_store"

# initialize Chroma vector store
vector_store = Chroma(
    collection_name="foo",
    embedding_function=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
    persist_directory=PERSIST_DIR,
    # other params...
)
    
from langchain_core.documents import Document

# add documents
document_1 = Document(page_content="foo", metadata={"baz": "bar"})
document_2 = Document(page_content="thud", metadata={"bar": "baz"})
document_3 = Document(page_content="i will be deleted :(")

documents = [document_1, document_2, document_3]
ids = ["1", "2", "3"]
vector_store.add_documents(documents=documents, ids=ids)

# add texts
texts = ["hello world", "goodbye world"]
metadatas = [{"lang": "en"}, {"lang": "en"}]
vector_store.add_texts(texts=texts, metadatas=metadatas)


# created by GPT-5 ---IGNORE---
# make sure the database is persisted
if vector_store._collection.count() == 0:
    # ...existing code...
    vector_store.add_documents(documents=documents, ids=ids)
    vector_store.add_texts(texts=texts, metadatas=metadatas)
    vector_store.persist()
else:
    print("已加载持久化向量库，无需重新嵌入。")