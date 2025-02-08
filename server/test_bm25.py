from langchain_community.document_loaders import CSVLoader
from langchain_community.retrievers import BM25Retriever
import os
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, SystemMessage, trim_messages  # Sửa import cho BaseMessage, SystemMessage và trim_messages
from typing import List

folder_path = "data_temp/rss_data"

def load_and_retrieve():
    all_docs = []
    
    # Liệt kê tất cả các file trong folder_path
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):  # Giả sử bạn chỉ muốn tải file CSV
            file_path = os.path.join(folder_path, filename)
            loader = CSVLoader(file_path=file_path,
                csv_args={
                'delimiter': ',',
                'quotechar': '"',
            })
            docs = loader.load()
            all_docs.extend(docs)  # Hợp nhất tài liệu

    return BM25Retriever.from_documents(all_docs)

# Định nghĩa công cụ cho agent
def search_tool(query: str):
    """Công cụ tìm kiếm tin tức sử dụng BM25Retriever."""
    print("search_tool:Tìm kiếm thông tin với query:", query)
    results = bm25_retriever.invoke(query)
    print("search_tool:Kết quả tìm kiếm:", results)
    return results

# Gọi hàm để sử dụng
bm25_retriever = load_and_retrieve()

# Khởi tạo LLM và Memory
llm = ChatOpenAI(model="gpt-4o")
memory = MemorySaver()

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

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)

# Tạo agent executor
tools = [search_tool]  # Sử dụng công cụ tìm kiếm
agent_executor = create_react_agent(
    model=llm, 
    tools=tools, 
    checkpointer=memory,
    state_modifier=state_modifier
)


# Ví dụ sử dụng agent_executor để tìm kiếm thông tin
query = "Tin tức công nghệ mới nhất"
input_message = HumanMessage(content=query)
threadId = "1234"

config = {"configurable": {"thread_id": threadId}}
responses = []  
for event in agent_executor.stream({"messages": [input_message]}, config, stream_mode="values"):
    responses.append(event["messages"][-1].content)

print('Kết quả tìm kiếm:', responses[-1])


# response = agent_executor.invoke(query)
# print("Kết quả từ agent_executor:")
# print(response)
