import os
from dotenv import load_dotenv
import sqlite3  # Thêm import cho sqlite3
from typing import List, Literal
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage

# Tải biến môi trường từ tệp .env
load_dotenv()

# !pip install dsrag

from dsrag.create_kb import create_kb_from_file
from dsrag.knowledge_base import KnowledgeBase

file_path = "data/cong-ty-nam-mo-dat-hiem-lon-nhat-viet-nam-lan-dau-bao-lai-ng.txt"
kb_id = "cong_ty_mo_dat_hiem"
doc_id = "doc_id"

kb = KnowledgeBase(kb_id, exists_ok=True, storage_directory='example_kb_data')

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
# results = retriever.invoke("tổng tài sản của Vimico ?")
# print(results)

model = ChatOpenAI(model="gpt-4o", temperature=0)


# Define tools
@tool
def search_information(query: str):
    """Retrieve information based on the query """
    search_result = retriever.invoke(query)
    if search_result:
        return "\n\n".join([doc.page_content for doc in search_result])
    else:
        return "No relevant information found."

# Create the ReAct agent
model = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [search_information]
agent = create_react_agent(model=model, tools=tools)

def get_chain_answer(query: str):
    messages = [HumanMessage(content=query)]
    response = agent.invoke({"messages": messages})
    return response["messages"][-1].content

def get_db_connection():
    return sqlite3.connect("ds_rag_mes.db")

def create_chat_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_chat_message(role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def load_chat_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history ORDER BY timestamp")
    messages = cursor.fetchall()
    conn.close()
    return [{"role": role, "content": content} for role, content in messages]

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()

def main():
    st.set_page_config(page_title="Bot tài chính", page_icon="🤖")
    st.title("Document Chatbot 💬")
    
    create_chat_table()
    initialize_session_state()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Bạn muốn biết điều gì ?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message("user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            response = get_chain_answer(prompt)
            st.write(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_message("assistant", response)

if __name__ == "__main__":
    main()

