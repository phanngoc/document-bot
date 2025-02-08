import os
from dotenv import load_dotenv
import sqlite3  # Thêm import cho sqlite3
from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import BaseModel

# Tải biến môi trường từ tệp .env
load_dotenv()

# !pip install dsrag

from dsrag.create_kb import create_kb_from_file
from dsrag.knowledge_base import KnowledgeBase

file_path = "data/cong-ty-nam-mo-dat-hiem-lon-nhat-viet-nam-lan-dau-bao-lai-ng.txt"
kb_id = "cong_ty_mo_dat_hiem"
doc_id = "doc_id"

kb = KnowledgeBase(kb_id, exists_ok=True, storage_directory='example_kb_data')


num_chunks = len(kb.chunk_db.data[doc_id])
print (num_chunks)

chunks = []
for i in range(num_chunks):
    chunk = {
        "section_title": kb.chunk_db.get_section_title(doc_id, i),
        "chunk_text": kb.chunk_db.get_chunk_text(doc_id, i),
    }

    chunks.append(chunk)

# print(chunks[2:5])

# Thêm lớp CustomRetriever
class CustomRetriever(BaseRetriever):
    k: int = 3  # Đặt giá trị mặc định cho k

    def _get_relevant_documents(self, query: str) -> List[Document]:
        matching_documents = []
        results = kb.query([query])
        matching_documents = [Document(page_content=str(segment['content']), metadata={}) for segment in results]
        return matching_documents

# Khởi tạo CustomRetriever
retriever = CustomRetriever(k=3)

# Ví dụ sử dụng retriever
results = retriever.invoke("tổng tài sản của Vimico ?")
print(results)