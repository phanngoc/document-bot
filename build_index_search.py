from llama_index.core import Document
from model import Assistant, Page
from chromadb.config import Settings
from chromadb import Client
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

def build_documents(assistant_id):
    documents = []
    pages = Page.select().where(Page.assistant_id == assistant_id)
    print(f"Number of pages: {len(pages)}")

    for page in pages:
        doc = Document(
            id=str(page.id) if page.id else None,
            text=page.text_content
        )
        documents.append(doc)
    return documents

def build_query_engine(collection_name, assistant_id):
    documents = build_documents(assistant_id)
    # Configure persistent storage for Chroma
    settings = Settings(
        persist_directory="./chroma_data",  # Directory for storing SQLite files
        is_persistent = True
    )
    chroma_client = Client(settings=settings)

    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    # Count items in the collection
    item_count = chroma_collection.count()
    print(f"Number of items in the collection: {item_count}")
    # Setup vector store and storage context
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    if item_count == 0:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents, storage_context, show_progress=True
        )
        assistant = Assistant.get(assistant_id)
        assistant.is_builded = True
        assistant.save()
    else:
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    return index.as_query_engine(
        chat_mode="context",
        memory=memory,
        system_prompt=(
            "You are a chatbot to help developer research and coding."
        ))
