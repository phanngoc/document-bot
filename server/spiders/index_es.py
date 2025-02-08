import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_utils import init_elasticsearch
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List, Dict, Any
from datetime import datetime

# Khởi tạo mô hình và tokenizer
tokenizer = AutoTokenizer.from_pretrained("fptai/vibert-base-cased")
model = AutoModel.from_pretrained("fptai/vibert-base-cased")

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

# Hàm chuyển đổi định dạng pubDate
def convert_pubdate_format(pub_date: str) -> str:
    # Chuyển đổi từ định dạng cũ sang định dạng ISO 8601
    try:
        return datetime.strptime(pub_date, '%a, %d %b %y %H:%M:%S %z').isoformat()
    except ValueError as e:
        print(f"Error parsing pubDate: {e}")
        return pub_date  # Trả về giá trị gốc nếu không thể chuyển đổi

def index_documents_with_embeddings(es_client: Elasticsearch, documents: List[Dict[str, Any]], index_name: str = "rss_feeds"):
    """
    Tạo embedding và lưu documents vào Elasticsearch
    
    Args:
        es_client: Elasticsearch client
        documents: List các document cần index
        index_name: Tên index trong Elasticsearch
    """
    try:        
        # Tạo index với mapping cho vector field
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "url": {"type": "keyword"},
                    "pubDate": {"type": "date"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,  # Kích thước vector của OpenAI embedding
                        "index": True,
                        "similarity": "cosine"  # Sử dụng cosine similarity
                    }
                }
            }
        }
        
        # Tạo index nếu chưa tồn tại
        if not es_client.indices.exists(index=index_name):
            es_client.indices.create(index=index_name, body=mapping)
            print(f"Created index {index_name} with embedding mapping")
        
        # Tạo embedding cho tất cả documents trong một lần
        texts_to_embed = [f"{doc.get('title', '')} {doc.get('description', '')}" for doc in documents]
        embeddings_batch = [get_embedding(text) for text in texts_to_embed]
        
        # Lưu từng document vào Elasticsearch
        for doc, embedding in zip(documents, embeddings_batch):
            # Chuyển đổi pubDate trước khi lưu
            if 'pubDate' in doc:
                doc['pubDate'] = convert_pubdate_format(doc['pubDate'])
            
            # Thêm embedding vào document
            doc["embedding"] = embedding.tolist()
            
            # Index document
            es_client.index(index=index_name, document=doc)
        
        print(f"Indexed {len(documents)} documents with embeddings")
        
    except Exception as e:
        print(f"Error indexing documents with embeddings: {e}")
        raise e

def main():
    # Khởi tạo Elasticsearch client
    es_client = init_elasticsearch()
    es_client.indices.delete(index="rss_feeds")
    print("Deleted index rss_feeds")
    # Đọc dữ liệu từ file CSV
    csv_file_path = '../data_temp/rss_data/cleaned_data.csv'
    documents = pd.read_csv(csv_file_path).to_dict(orient='records')
    
    # Chỉ index 300 bản ghi
    for i in range(0, len(documents), 300):
        batch = documents[i:i + 300]  # Lấy 300 bản ghi
        index_documents_with_embeddings(es_client, batch)

if __name__ == "__main__":
    main()
    
