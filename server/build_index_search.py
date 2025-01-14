from model import Assistant, Page
from chromadb.config import Settings
from chromadb import Client
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from uuid import uuid4
from langchain_core.documents import Document

# https://www.linkedin.com/pulse/beginners-guide-retrieval-chain-using-langchain-vijaykumar-kartha-kuinc
# https://python.langchain.com/docs/integrations/vectorstores/chroma/
# https://python.langchain.com/api_reference/chroma/vectorstores/langchain_chroma.vectorstores.Chroma.html#langchain_chroma.vectorstores.Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)

def build_documents(assistant_id):
    documents = []
    pages = Page.select().where(Page.assistant_id == assistant_id)
    print(f"Number of pages: {len(pages)}")

    for page in pages:
        doc = Document(
            id=str(page.id) if page.id else None,
            page_content=page.text_content,
            metadata={"url": page.url, "assistant_id": page.assistant_id},
        )
        documents.append(doc)
    
    print('build_documents:documents:', len(documents))
    uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=uuids)
    return documents

def search_similarity(query):
    results = vector_store.similarity_search(
        query=query,
        k=2,
    )

    print("Results:", results)

    return results