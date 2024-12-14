from chromadb import Client
from chromadb.config import Settings

# Initialize Chroma client with persistence settings
settings = Settings(
    persist_directory="./chroma_data",  # Directory for storing SQLite files
    is_persistent=True
)
chroma_client = Client(settings=settings)
