from fastapi import responses
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from scrapy.crawler import CrawlerProcess
import datetime
from typing import List
from spiders.rss_spider import RssSpider
from langchain_community.document_loaders import CSVLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    # SemanticChunker
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch.retrievers import ElasticsearchRetriever
from elasticsearch import Elasticsearch
from langchain_community.vectorstores import (
    Chroma,
    FAISS,
    Pinecone,
    Weaviate,
    Milvus,
    Qdrant
)
from langchain_community.embeddings import OpenAIEmbeddings

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from scrapy.utils.project import get_project_settings
from langchain.prompts import ChatPromptTemplate
from elasticsearch_utils import (
    init_elasticsearch,
    analyze_time_in_query,
    create_es_retriever,
    create_hybrid_es_retriever
)

model = ChatOpenAI(model="gpt-4o")
memory = MemorySaver()

# Get the current date and time
now = datetime.datetime.now()

# Thiết lập User-Agent mặc định
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Thay đổi cách thiết lập settings cho Scrapy
settings = get_project_settings()
settings.set('USER_AGENT', USER_AGENT)

def retrieve_rss_link(url: str):
    """Retrieve rss link from user query."""
    formatted_time = now.strftime("%Y%m%d_%H%M") + ".csv"
    # Sử dụng settings đã được thiết lập
    runner = CrawlerProcess()
    runner.crawl(RssSpider, start_url=url, output_file=formatted_time, max_urls=500)
    runner.start()
    
    return formatted_time

# retrieve_rss_link("https://thanhnien.vn/rss.html")

st.title("Agent tin tức")
st.write("Hỏi tôi :D")

# Khởi tạo Elasticsearch client
es_client = init_elasticsearch()

# Kiểm tra kết nối
try:
    info = es_client.info()
    print("Connected to Elasticsearch:", info)
except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")

def load_retriever(retriever_type: str, data_dir: str = None):
    """
    Khởi tạo retriever dựa trên loại được chọn
    
    Args:
        retriever_type: Loại retriever ("BM25", "Elasticsearch", "ChromaDB")
        file_path: Đường dẫn đến file CSV (nếu None sẽ tự động tìm file mới nhất)
        es_client: Elasticsearch client (cần thiết cho Elasticsearch retriever)
    
    Returns:
        Retriever object
    """
    try:
        # Nếu không có file_path, tìm file CSV mới nhất trong thư mục
        if retriever_type != "Elasticsearch":
            data_dir = "data_temp/rss_data"
            try:
                # Lấy danh sách tất cả các file CSV trong thư mục
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                if not csv_files:
                    raise ValueError(f"No CSV files found in {data_dir}")
                
                # Sắp xếp theo thời gian tạo file, lấy file mới nhất
                latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
                file_path = os.path.join(data_dir, latest_file)
                print(f"Loading most recent CSV file: {file_path}")
            except Exception as e:
                raise ValueError(f"Error finding CSV files: {str(e)}")

        if retriever_type == "BM25":
            if not file_path:
                raise ValueError("No CSV file available for BM25 retriever")
            
            loader = CSVLoader(file_path=file_path,
                csv_args={
                'delimiter': ',',
                'quotechar': '"',
            })
            docs = loader.load()
            return BM25Retriever.from_documents(docs)
            
        elif retriever_type == "Elasticsearch":
            if not es_client:
                raise ValueError("Elasticsearch client is required")
                
            # Sử dụng hybrid search
            return create_hybrid_es_retriever(
                es_client=es_client,
                use_embeddings=True  # Có thể điều chỉnh qua UI
            )
            
        elif retriever_type == "ChromaDB":
            if not file_path:
                raise ValueError("No CSV file available for ChromaDB retriever")
                
            loader = CSVLoader(file_path=file_path,
                csv_args={
                'delimiter': ',',
                'quotechar': '"',
            })
            docs = loader.load()
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma.from_documents(docs, embeddings)
            return vectorstore.as_retriever()
            
        else:
            raise ValueError(f"Unsupported retriever type: {retriever_type}")
            
    except Exception as e:
        print(f"Error loading retriever: {e}")
        raise e


# Các selectbox cho retriever và text splitter
col3, col4 = st.columns(2)

with col3:
    retriever_type = st.selectbox(
        "Chọn phương pháp tìm kiếm:",
        ["BM25", "Elasticsearch", "ChromaDB"],
        index=1,  # Set default to Elasticsearch
        key="retriever_select"
    )
    # Tạo lại retriever khi thay đổi loại
    try:
        retriever = load_retriever(retriever_type)
        st.success(f"Đã chuyển sang phương pháp tìm kiếm: {retriever_type}")
    except Exception as e:
        st.error(f"Lỗi khi khởi tạo {retriever_type}: {str(e)}")

# retriever_type = "Elasticsearch"
# retriever = load_retriever(retriever_type)

# Thêm input URL và nút crawl
col1, col2 = st.columns([3, 1])
with col1:
    rss_url = st.text_input("Nhập URL RSS:", "", key="rss_url_input")
with col2:
    if st.button("Crawl RSS", key="crawl_button"):
        if rss_url:
            with st.spinner('Đang crawl dữ liệu...'):
                try:
                    csv_path = retrieve_rss_link(rss_url)
                    st.success(f'Đã crawl xong! File được lưu tại: {csv_path}')
                    
                    # Tạo đường dẫn đầy đủ đến file CSV
                    full_path = f"data_temp/rss_data/{csv_path}"
                    
                    # Khởi tạo retriever với file mới
                    retriever = load_retriever(
                        retriever_type=retriever_type
                    )
                    
                except Exception as e:
                    st.error(f'Lỗi khi crawl: {str(e)}')
        else:
            st.warning('Vui lòng nhập URL')


with col4:
    splitter_type = st.selectbox(
        "Chọn phương pháp tách văn bản:",
        ["Semantic Chunking", "Recursive Splitting"],
        key="splitter_select"
    )


# Thêm vào phần đầu UI
st.write("Hỏi tôi :D")


@tool
def search_similarity(query: str):
    """ return article relevance with user query """
    relevance_documents = []
    print('query:', query)
    
    try:
        results = retriever.invoke(query)
        # print('results:', results, 'retriever_type:', retriever_type)
        
        # Khởi tạo embeddings model nếu dùng semantic chunking
        if splitter_type == "Semantic Chunking":
            embeddings = OpenAIEmbeddings()
        
        for result in results:
            try:
                # Lấy URL tùy theo loại retriever
                if retriever_type == "BM25":
                    website_url = result.page_content.split('url: ')[1].split('\n')[0]
                elif retriever_type == "Elasticsearch":
                    website_url = result.metadata.get('_source')['url']
                else:  # ChromaDB
                    website_url = result.metadata.get('source')
                
                print('website_url:', website_url)
                loader = WebBaseLoader(
                    web_paths=(website_url,),
                    requests_kwargs={
                        'headers': {'User-Agent': USER_AGENT}
                    }
                )
                docs = loader.load()
                # print('documents:', docs)
                
                # Chọn text splitter dựa trên lựa chọn của người dùng
                if splitter_type == "Semantic Chunking":
                    text_splitter = SemanticChunker(
                        embeddings=embeddings,
                        breakpoint_threshold_type="percentile",
                        breakpoint_threshold_amount=0.3,
                        min_chunk_size=200,
                        buffer_size=1,
                        add_start_index=True
                    )
                else:  # Recursive Splitting
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200,
                        length_function=len,
                        is_separator_regex=False,
                    )
                
                all_splits = text_splitter.split_documents(docs)
                relevance_documents.extend(all_splits)
            except Exception as e:
                print(f"Lỗi khi tải URL {website_url}", e)
                continue

        st.session_state["relevance_documents"] = relevance_documents
        concatenated_content = "\n".join([
            f"{doc.metadata['source']}: {doc.metadata.get('title', 'Không có tiêu đề')} : {doc.page_content[:200]}" 
            for doc in relevance_documents
        ])
        return concatenated_content

    except Exception as e:
        print(f"Lỗi khi tìm kiếm: {e}", e)
        return f"Xin lỗi, đã có lỗi xảy ra khi tìm kiếm: {str(e)}"

def state_modifier(state) -> List[BaseMessage]:
    """Given the agent state, return a list of messages for the chat model."""
    
    # Thêm SystemMessage nếu chưa có
    if not state["messages"] or not isinstance(state["messages"][0], SystemMessage):
        state["messages"].insert(0, SystemMessage(content="bạn là một người trợ giúp tìm kiếm thông tin và trả lời hợp lí"))

    return trim_messages(
        state["messages"],
        token_counter=len,
        max_tokens=45,
        strategy="last",
        include_system=True,  # Đảm bảo giữ lại SystemMessage
        allow_partial=False,
    )

tools = [search_similarity]


agent_executor = create_react_agent(
    model=model, 
    tools=tools, 
    checkpointer=memory,
    state_modifier=state_modifier
)

threadId = "1234"
user_input = st.text_input("Bạn: ", "", key="chat_input")

if st.button("Gửi"):
    if retriever_type == "Elasticsearch":
        # Phân tích yếu tố thời gian trong query
        time_info = analyze_time_in_query(user_input)
        
        # Tạo retriever mới với time_info
        retriever = create_hybrid_es_retriever(
            es_client=es_client,
            use_embeddings=True,
            time_info=time_info
        )
    
    input_message = HumanMessage(content=user_input)
    
    config = {"configurable": {"thread_id": threadId}}
    responses = []  
    for event in agent_executor.stream({"messages": [input_message]}, config, stream_mode="values"):
        responses.append(event["messages"][-1].content)

    with st.chat_message("assistant"):
        st.markdown(responses[-1])
        
        # Hiển thị các tài liệu liên quan trong card
        if "relevance_documents" in st.session_state:
            st.markdown("### 📑 Các tài liệu liên quan")
            
            # Tạo columns để hiển thị card theo grid
            cols = st.columns(2)
            
            for idx, doc in enumerate(st.session_state["relevance_documents"]):
                with cols[idx % 2]:
                    with st.container():
                        # Tạo card sử dụng CSS
                        st.markdown("""
                            <style>
                            .doc-card {
                                border: 1px solid #ddd;
                                border-radius: 8px;
                                padding: 15px;
                                margin: 10px 0;
                                background-color: #f8f9fa;
                            }
                            .doc-title {
                                color: #1e88e5;
                                font-size: 16px;
                                font-weight: bold;
                                margin-bottom: 10px;
                            }
                            .doc-content {
                                font-size: 14px;
                                color: #424242;
                                margin-bottom: 10px;
                            }
                            .doc-source {
                                font-size: 12px;
                                color: #666;
                                border-top: 1px solid #eee;
                                padding-top: 8px;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                            <div class="doc-card">
                                <div class="doc-title">📰 {doc.metadata.get('title', 'Không có tiêu đề')}</div>
                                <div class="doc-content">{doc.page_content[:200]}...</div>
                                <div class="doc-source">🔗 Nguồn: <a href="{doc.metadata['source']}" target="_blank">{doc.metadata['source']}</a></div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Thêm nút "Đọc thêm" cho mỗi card
                        if st.button(f"Đọc thêm 👉", key=f"read_more_{idx}"):
                            st.session_state[f"show_full_{idx}"] = True
                        
                        # Hiển thị nội dung đầy đủ trong expander
                        if st.session_state.get(f"show_full_{idx}", False):
                            with st.expander("Nội dung đầy đủ"):
                                st.markdown(doc.page_content)

