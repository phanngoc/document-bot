from transformers import AutoTokenizer, AutoModel
import json
from elasticsearch import *
from langchain_openai import OpenAIEmbeddings
import torch
import requests

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

query_sub = {
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
      }
}
# Thay đổi truy vấn để sử dụng cấu trúc search_body
search_body = {
    "query": query_sub['query'],
    "knn": {
        "field": "embedding",
        "query_vector": query_embedding.tolist(),  # Chuyển đổi numpy array thành list
        "k": 5,  # Số lượng kết quả gần nhất,
        "boost": 4.0  # Tăng điểm số cho kết quả
    }
}

# Hàm để đánh giá DCG
def evaluate_dcg(index, search_body, rated_documents):
    result = client.rank_eval(
        index=index,
        body={
            "requests": [{"id": "exp1", "request": search_body, "ratings": rated_documents}],
            "metric": {"dcg": {"k": 5, "normalize": False}}
        }
    )
    return result

# Khởi tạo rated_documents bên ngoài hàm
def create_rated_documents(ratings):
    return [
        {"_index": "rss_feeds", "_id": "u1vMvJQBu5Dj7_jRYl91", "rating": ratings[0]},
        {"_index": "rss_feeds", "_id": "Z1vLvJQBu5Dj7_jR7F8R", "rating": ratings[1]},
        {"_index": "rss_feeds", "_id": "ilvNvJQBu5Dj7_jRY2JC", "rating": ratings[2]},
        {"_index": "rss_feeds", "_id": "01vRvJQBu5Dj7_jRrGvJ", "rating": ratings[3]},
        {"_index": "rss_feeds", "_id": "VVvLvJQBu5Dj7_jRZl6Q", "rating": ratings[4]}
    ]

# Sau khi thực hiện tìm kiếm
response = client.search(index=index, body=search_body)  # Thực hiện tìm kiếm
print("5 record đầu tiên:")
for hit in response['hits']['hits']:
    print('hit', hit['_score'], "|||", hit['_source']['title'], hit['_source']['description'], hit['_source']['pubDate'])

# Đánh giá DCG
ratings = [3, 2, 1, 0, 0]  # Thay đổi giá trị này theo đánh giá thực tế của bạn
rated_documents = create_rated_documents(ratings)  # Tạo rated_documents
dcg_result = evaluate_dcg(index, search_body, rated_documents)  # Truyền rated_documents vào hàm
print("Kết quả đánh giá DCG:", dcg_result)
    

