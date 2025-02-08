import os
from dotenv import load_dotenv
import sqlite3  # Thêm import cho sqlite3

# Tải biến môi trường từ tệp .env
load_dotenv()

# !pip install dsrag

from dsrag.create_kb import create_kb_from_file
from dsrag.knowledge_base import KnowledgeBase

file_path = "data/cong-ty-nam-mo-dat-hiem-lon-nhat-viet-nam-lan-dau-bao-lai-ng.txt"
kb_id = "cong_ty_mo_dat_hiem"
doc_id = "doc_id"
# kb = create_kb_from_file(kb_id, file_path)

kb = KnowledgeBase(kb_id, exists_ok=True, storage_directory='example_kb_data')
# with open(file_path, 'r', encoding='utf-8') as file:
#     document_text = file.read()
# print('document_text[:200]', document_text[:200])
# kb.add_document(doc_id=doc_id, text=document_text)

# search_queries = ["tổng tài sản của Vimico ?"]
# results = kb.query(search_queries)
# for segment in results:
#     print('segment:', segment)

num_chunks = len(kb.chunk_db.data[doc_id])
print (num_chunks)

chunks = []
for i in range(num_chunks):
    chunk = {
        "section_title": kb.chunk_db.get_section_title(doc_id, i),
        "chunk_text": kb.chunk_db.get_chunk_text(doc_id, i),
    }

    chunks.append(chunk)

print(chunks[2:5])