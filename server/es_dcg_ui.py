from transformers import AutoTokenizer, AutoModel
import json
from elasticsearch import *
from langchain_openai import OpenAIEmbeddings
import torch
import requests
import streamlit as st  # Thêm import cho Streamlit
import pandas as pd

# Khởi tạo biến toàn cục cho tokenizer và model
if 'tokenizer' not in st.session_state:
    st.session_state.tokenizer = AutoTokenizer.from_pretrained("fptai/vibert-base-cased")
if 'model' not in st.session_state:
    st.session_state.model = AutoModel.from_pretrained("fptai/vibert-base-cased")

def embed_query(query):
    return get_embedding(query)

def get_embedding(text):
    inputs = st.session_state.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = st.session_state.model(**inputs)
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
      },
      "size": 5  # Đặt kích thước kết quả trả về là 5
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
def create_rated_documents(ratings, ids):
    return [
        {"_index": "rss_feeds", "_id": ids[i], "rating": ratings[i]} for i in range(len(ratings))
    ]

# Khởi tạo giao diện Streamlit
st.title("Tìm kiếm và Đánh giá DCG")

# Nhập truy vấn từ người dùng
query = st.text_input("Nhập truy vấn:", value="các dự án bất động sản")

# Nhập số lượng kết quả trả về
num_results = st.number_input("Nhập số lượng kết quả trả về:", min_value=1, max_value=20, value=5)

# Tải lại kết quả từ session_state nếu có
if 'search_results' in st.session_state:
    results_df = pd.DataFrame(st.session_state.search_results)  # Chuyển đổi danh sách kết quả thành DataFrame
    st.write("Kết quả tìm kiếm trước đó:")
    # Sử dụng một khóa duy nhất cho data_editor
    edited_results = st.data_editor(results_df, key=f"editable_results_{query}")  # Cho phép chỉnh sửa
else:
    edited_results = pd.DataFrame(columns=["Score", "Rating", "Title", "Description", "ID", "PubDate"])

# Nút tìm kiếm
if st.button("Tìm kiếm"):
    # Xóa kết quả cũ trong session_state
    if 'search_results' in st.session_state:
        del st.session_state.search_results

    # Tạo embedding cho truy vấn
    query_embedding = get_embedding(query)

    # Cập nhật search_body với số lượng kết quả
    search_body['knn']['k'] = num_results

    # Thực hiện tìm kiếm
    response = client.search(index=index, body=search_body)
    
    # Tạo danh sách để lưu trữ kết quả
    results = []
    for hit in response['hits']['hits']:
        results.append({
            "Score": hit['_score'],
            "Rating": 0,
            "Title": hit['_source']['title'],
            "Description": hit['_source']['description'],
            "ID": hit['_id'],  # Lưu ID của tài liệu
            "PubDate": hit['_source']['pubDate'],
        })

    # Lưu kết quả vào session_state
    st.session_state.search_results = results

    # Hiển thị kết quả dưới dạng bảng có thể chỉnh sửa
    st.write("5 record đầu tiên:")
    results_df = pd.DataFrame(results)  # Chuyển đổi danh sách kết quả thành DataFrame
    # Sử dụng một khóa duy nhất cho data_editor
    edited_results = st.data_editor(results_df, key=f"editable_results_{query}")  # Cho phép chỉnh sửa

    # Tạo rated_documents và đánh giá DCG
    rated_documents = create_rated_documents(edited_results['Rating'].tolist(), edited_results['ID'].tolist())  # Lấy đánh giá và ID từ bảng
    dcg_result = evaluate_dcg(index, search_body, rated_documents)
    st.write("Kết quả đánh giá DCG:", dcg_result)

# Tính toán lại DCG khi bảng được chỉnh sửa
if edited_results is not None and not edited_results.empty:
    rated_documents = create_rated_documents(edited_results['Rating'].tolist(), edited_results['ID'].tolist())
    dcg_result = evaluate_dcg(index, search_body, rated_documents)
    st.write("Kết quả đánh giá DCG sau khi chỉnh sửa:", dcg_result)
    

