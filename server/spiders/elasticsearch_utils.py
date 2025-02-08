from elasticsearch import Elasticsearch
from langchain_elasticsearch.retrievers import ElasticsearchRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
import json
from typing import List, Dict, Any
from datetime import datetime

# Khởi tạo embedding model
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1536)

# Khởi tạo Elasticsearch client
def init_elasticsearch():
    """Khởi tạo và kiểm tra kết nối Elasticsearch"""
    try:
        es_client = Elasticsearch(
            hosts=["http://localhost:9200"],
            request_timeout=30,
            verify_certs=False,
            ssl_show_warn=False
        )
        info = es_client.info()
        print("Connected to Elasticsearch:", info)
        return es_client
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        raise e

# Prompt template để phân tích thời gian
time_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", """Bạn là một trợ lý phân tích câu hỏi. Nhiệm vụ của bạn là:
    1. Xác định xem câu hỏi có yếu tố thời gian không
    2. Trích xuất thông tin thời gian nếu có
    3. Trả về kết quả dưới dạng JSON với format:
    {{
        "has_time": true/false,
        "time_type": "range/specific/recent/none",
        "start_date": "YYYY-MM-DD" hoặc null,
        "end_date": "YYYY-MM-DD" hoặc null,
        "original_query": "phần query không bao gồm yếu tố thời gian"
    }}
    
    Ví dụ:
    - "tin tức về covid từ tháng 1/2024" -> {{"has_time": true, "time_type": "range", "start_date": "2024-01-01", "end_date": null}}
    - "tin mới nhất về thời tiết" -> {{"has_time": true, "time_type": "recent", "start_date": null, "end_date": null}}
    - "tin về bóng đá" -> {{"has_time": false, "time_type": "none", "start_date": null, "end_date": null}}
    """),
    ("human", "{query}")
])

# Khởi tạo model để phân tích thời gian
time_analyzer = ChatOpenAI(temperature=0)

def analyze_time_in_query(query: str) -> dict:
    """Phân tích yếu tố thời gian trong query"""
    try:
        chain = time_analysis_prompt | time_analyzer
        result = chain.invoke({"query": query})
        print("analyze_time_in_query", result)
        # Sử dụng json.loads thay vì eval để parse JSON string
        return json.loads(result.content)
    except Exception as e:
        print(f"Lỗi khi phân tích thời gian: {str(e)}")
        # Trả về dict mặc định nếu có lỗi
        return {
            "has_time": False,
            "time_type": "none",
            "start_date": None,
            "end_date": None,
            "original_query": query
        }

def build_es_query(query: str, time_info: dict) -> dict:
    """Tạo Elasticsearch query với điều kiện thời gian nếu có"""
    base_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": time_info["original_query"] if time_info["has_time"] else query,
                            "fields": ["title^2", "description"],
                            "type": "best_fields",
                            "tie_breaker": 0.3
                        }
                    }
                ]
            }
        }
    }
    
    if time_info["has_time"]:
        time_filter = {}
        if time_info["time_type"] == "range":
            time_filter = {
                "range": {
                    "pubDate": {
                        "gte": time_info["start_date"] if time_info["start_date"] else None,
                        "lte": time_info["end_date"] if time_info["end_date"] else "now"
                    }
                }
            }
        elif time_info["time_type"] == "specific":
            # Xử lý khoảng thời gian cụ thể
            time_filter = {
                "range": {
                    "pubDate": {
                        "gte": time_info["start_date"],
                        "lte": time_info["end_date"] if time_info["end_date"] else time_info["start_date"]
                    }
                }
            }
        elif time_info["time_type"] == "recent":
            time_filter = {
                "range": {
                    "pubDate": {
                        "gte": "now-7d/d",
                        "lte": "now"
                    }
                }
            }
        
        if time_filter:
            base_query["query"]["bool"]["filter"] = time_filter
    
    print("build_es_query:query:", base_query)
    return base_query

def create_es_retriever(es_client: Elasticsearch, time_info: dict = None) -> ElasticsearchRetriever:
    """Tạo ElasticsearchRetriever với cấu hình cụ thể"""
    return ElasticsearchRetriever(
        es_client=es_client,
        index_name="rss_feeds",
        query_field="description",
        content_field="description",
        metadata_fields=["url", "title", "pubDate"],
        embedding_field=None,
        vector_query_field=None,
        search_type="match",
        k=10,
        source_excludes=[],
        body_func=lambda q: build_es_query(q, time_info) if time_info else build_es_query(q, {
            "has_time": False,
            "time_type": "none",
            "start_date": None,
            "end_date": None,
            "original_query": q
        })
    )

# Thêm hàm để chuyển đổi định dạng ngày tháng
def convert_pubdate_format(pubdate: str) -> str:
    """Chuyển đổi định dạng pubDate từ string sang định dạng ISO 8601"""
    try:
        # Chuyển đổi từ định dạng 'Tue, 13 Oct 20 11:37:41 +0700' sang 'YYYY-MM-DDTHH:MM:SSZ'
        return datetime.strptime(pubdate, '%a, %d %b %y %H:%M:%S %z').isoformat()
    except ValueError:
        print(f"Lỗi khi chuyển đổi pubDate: {pubdate}")
        return None  # Trả về None nếu không thể chuyển đổi

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
                        "dims": 1536,  # Kích thước vector của OpenAI embedding
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
        embeddings_batch = embeddings.embed_documents(texts_to_embed)
        
        # Lưu từng document vào Elasticsearch
        for doc, embedding in zip(documents, embeddings_batch):
            # Chuyển đổi pubDate trước khi lưu
            if 'pubDate' in doc:
                doc['pubDate'] = convert_pubdate_format(doc['pubDate'])
            
            # Thêm embedding vào document
            doc["embedding"] = embedding
            
            # Index document
            es_client.index(index=index_name, document=doc)
        
        print(f"Indexed {len(documents)} documents with embeddings")
        
    except Exception as e:
        print(f"Error indexing documents with embeddings: {e}")
        raise e

def create_hybrid_es_retriever(
    es_client: Elasticsearch,
    time_info: dict = None,
    use_embeddings: bool = True
) -> ElasticsearchRetriever:
    """
    Tạo ElasticsearchRetriever với tìm kiếm kết hợp (hybrid search)
    
    Args:
        es_client: Elasticsearch client
        time_info: Thông tin thời gian từ query
        use_embeddings: Có sử dụng embedding search không
    """
    def build_hybrid_query(query: str) -> dict:
        # Tạo embedding cho query
        query_embedding = embeddings.embed_query(query)
        
        # Base query từ hàm build_es_query
        base_query = build_es_query(query, time_info) if time_info else build_es_query(query, {
            "has_time": False,
            "time_type": "none",
            "start_date": None,
            "end_date": None,
            "original_query": query
        })
        
        if use_embeddings:
            # Thêm vector search vào bool query
            base_query["query"]["bool"]["should"] = [
                {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                }
            ]
            # Điều chỉnh trọng số giữa text search và vector search
            base_query["query"]["bool"]["minimum_should_match"] = 0

        print('build_hybrid_query:', base_query) 
        return base_query
    
    return ElasticsearchRetriever(
        es_client=es_client,
        index_name="rss_feeds",
        query_field="description",
        content_field="description",
        metadata_fields=["url", "title", "pubDate"],
        embedding_field="embedding",
        vector_query_field="embedding",
        search_type="similarity",
        k=10,
        source_excludes=["embedding"],  # Không trả về vector trong kết quả
        body_func=build_hybrid_query
    ) 