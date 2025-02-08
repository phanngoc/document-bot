# https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html#:~:text=Reciprocal%20rank%20fusion%20(RRF)%20is,to%20achieve%20high%2Dquality%20results.

from transformers import AutoTokenizer, AutoModel
import json
from elasticsearch import *
from langchain_openai import OpenAIEmbeddings
import torch

# Khởi tạo mô hình và tokenizer
tokenizer = AutoTokenizer.from_pretrained("fptai/vibert-base-cased")
model = AutoModel.from_pretrained("fptai/vibert-base-cased")

def embed_query(query):
    return get_embedding(query)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

index = "rss_feeds"
client = Elasticsearch(
    "http://localhost:9200",
    headers={"x-elastic-product-required": "false"},
    meta_header=True
)

# Lấy danh sách tất cả các indices
indices = client.indices.get_alias(index="*")
# In danh sách tất cả các indices
print("Danh sách các indices:")
for index_name in indices:
    print(index_name)


total_docs = client.count(index=index)['count']
print(f"Tổng số tài liệu trong index '{index}': {total_docs}")

# Khởi tạo embeddings
# embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1536)

query_sample = [
    "Thủy sản",
    "các dự án bất động sản",
    "tài chính ngân hàng",
]
query = query_sample[1]

print('Truy vấn:', query)
# Tạo embedding cho truy vấn
query_embedding = get_embedding(query)

# Thay đổi truy vấn để sử dụng cấu trúc search_body
search_body = {
    "query": {
        "bool": {
            "must": [
                {
                    "function_score": {
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "description^2"],  # Tăng trọng số cho trường title
                                "fuzziness": "AUTO",  # Cho phép tìm kiếm gần đúng
                                "minimum_should_match": "75%"  # Yêu cầu ít nhất 75% từ khóa phải khớp
                            }
                        },
                        "min_score": 0.3  # Đặt min_score cho truy vấn
                    }
                }
            ],
            "filter": [],
            "should": [],
            "must_not": []
        }
    },
    "knn": {
        "field": "embedding",
        "query_vector": query_embedding.tolist(),  # Chuyển đổi numpy array thành list
        "k": 5,  # Số lượng kết quả gần nhất,
        "boost": 4.0  # Tăng điểm số cho kết quả
    }
}

response = client.search(index=index, body=search_body)  # Thực hiện tìm kiếm
print("5 record đầu tiên:")
for hit in response['hits']['hits']:
    print('hit', hit['_score'], "|||", hit['_source']['title'], hit['_source']['description'], hit['_source']['pubDate'])
    
