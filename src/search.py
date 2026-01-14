# search.py
# search documents in the vector store
# include search()

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
import os
from database import add_txt_file

os.environ["GOOGLE_API_KEY"] = "AIzaSyBDHO0gEX4nN3IMefqloQ1V7k7ULVtac80"

# initialize Chroma vector store)
vector_store = Chroma(
    collection_name="foo",
    persist_directory="chroma_store",
    embedding_function=GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
    # other params...
)

# add documents
# TODO: to add documnets with input
# Actually we do not need to add documents because we already have a database
# We only need to add documents when we are developing the system for the first time

folder_path = "docs"
for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        add_txt_file(file_path)
        print(f"已添加文件: {filename}")

# search function to find documents
# TODO: add another search function file, do not mix search and add document functions
# search(query: str, search_type: str, **kwargs: Any) -> list[Document]
# query: search what
# search_type: "similarity", "mmr" or "similarity_score_threshold"
def search(query: str, k: int = 2):
    # This means we search top k similar documents
    results = vector_store.similarity_search(query=query, k=k)
    for doc in results:
        print(f"* {doc.page_content} [{doc.metadata}]")
    print(results)
        