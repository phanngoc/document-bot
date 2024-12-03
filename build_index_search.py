from llama_index.core import Document
from model import Page
from chromadb.config import Settings
from chromadb import Client
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def build_documents():
    documents = []
    pages = Page.select()
    for page in pages:
        print('page:', page.id)
        doc = Document(
            id=str(page.id) if page.id else None,
            text=page.text_content
        )
        documents.append(doc)
    return documents

def build_query_engine(collection_name, is_builded=True):
    documents = build_documents()
    # Configure persistent storage for Chroma
    settings = Settings(
        persist_directory="./chroma_data",  # Directory for storing SQLite files
        is_persistent = True
    )
    chroma_client = Client(settings=settings)

    chroma_collection = chroma_client.get_or_create_collection(collection_name)

    # Setup vector store and storage context
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    if is_builded:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents, storage_context, show_progress=True
        )
    else:
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    return index.as_query_engine()
