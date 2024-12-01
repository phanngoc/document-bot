import chromadb
from chromadb.config import Settings
from transformers import AutoTokenizer, AutoModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document
from model import Page
import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

openai.api_key = os.environ["OPENAI_API_KEY"]
print('openai.api_key:', openai.api_key)

documents = []
pages = Page.select()
for page in pages:
    print('Page:', page.id)
    doc = Document(
        id=str(page.id) if page.id else None,
        text=page.text_content
    )
    documents.append(doc)


index = VectorStoreIndex.from_documents(
    documents
)

query_engine = index.as_query_engine()
response = query_engine.query("What is llamaindex ?.")
print('response:', response)