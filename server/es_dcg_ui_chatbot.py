from transformers import AutoTokenizer, AutoModel
import json
from elasticsearch import *
from langchain_openai import OpenAIEmbeddings
from langchain_deepseek import ChatDeepSeek
from langchain_elasticsearch import ElasticsearchRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
import torch
import requests
import streamlit as st
import pandas as pd
import os

from dotenv import load_dotenv

load_dotenv()


# if not os.getenv("DEEPSEEK_API_KEY"):
os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")

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


total_docs = client.count(index=index)['count']
print(f"Tổng số tài liệu trong index '{index}': {total_docs}")


query_sample = [
    "Thủy sản",
    "các dự án bất động sản",
    "tài chính ngân hàng",
]
query = query_sample[1]

print('Truy vấn:', query)
# Tạo embedding cho truy vấn


# Khởi tạo model cho chatbot bằng ChatDeepSeek
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Khởi tạo PromptTemplate
prompt_template = "Dựa trên thông tin sau: {context}, hãy trả lời câu hỏi: {user_input}"
prompt = PromptTemplate(
    input_variables=["context", "user_input"], 
    template=prompt_template
)

# Hàm để xử lý truy vấn từ người dùng
def handle_user_query(user_input):
    # Tạo embedding cho truy vấn
    query_embedding = get_embedding(user_input)

    # Khởi tạo cấu trúc truy vấn
    query_sub = {
        "query": {
            "bool": {
                "must": [
                    {
                        "function_score": {
                            "query": {
                                "multi_match": {
                                    "query": user_input,
                                    "fields": ["title^3", "description^2"],
                                    "fuzziness": "AUTO",
                                    "minimum_should_match": "75%"
                                }
                            },
                            "min_score": 0.3
                        }
                    }
                ],
                "filter": [],
                "should": [],
                "must_not": []
            }
        },
        "size": 5
    }

    # Thay đổi truy vấn để sử dụng cấu trúc search_body
    search_body = {
        "query": query_sub['query'],
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding.tolist(),
            "k": 5,
            "boost": 4.0
        }
    }
    
    retriever = ElasticsearchRetriever.from_es_params(
        index_name=index,
        body_func=lambda x: search_body,
        content_field="title",
        url="http://localhost:9200"
    )
    
    # Lấy context từ Elasticsearch
    context_docs = retriever.invoke(user_input)
    context = "\n\n".join(doc.page_content for doc in context_docs)

    # Tạo prompt và gọi model
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "user_input": user_input})

    return response

# Giao diện Streamlit
st.title("Chatbot Tìm kiếm và trả lời tin tức")

# Nhập truy vấn từ người dùng
user_input = st.text_input("Nhập truy vấn:", value="")

# Nút gửi truy vấn
if st.button("Gửi"):
    if user_input:
        response = handle_user_query(user_input)
        st.write(f"**Bot:** {response}")  # Hiển thị phản hồi từ bot
