import os
from dotenv import load_dotenv
import sqlite3
from typing import List, Literal
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_neo4j import Neo4jVector
from dsrag.create_kb import create_kb_from_file
from dsrag.knowledge_base import KnowledgeBase

# Load environment variables
load_dotenv()

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# List of test questions for financial information
test_questions = [
    "Tổng công ty Khoáng sản TKV lãi bao nhiêu ?",
    "Giá trị vốn hóa của Vimico ?",
    "Doanh nghiệp nào sở hữu mỏ đất hiếm Đông Pao ?",
    "Giá cổ phiếu của công ty Vimico đã biến động như thế nào ?",
]

file_path = "data/cong-ty-nam-mo-dat-hiem-lon-nhat-viet-nam-lan-dau-bao-lai-ng.txt"
# Document processing
loader = TextLoader(file_path)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# Initialize Neo4j vector store
embeddings = OpenAIEmbeddings()
vector_store = Neo4jVector.from_documents(
    docs, 
    embeddings,
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD
)

class CustomNeo4jRetriever(BaseRetriever):
    k: int = 3

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs_with_score = vector_store.similarity_search_with_score(query, k=self.k)
        print('Querying Neo4j...', docs_with_score)
        return [doc for doc, _ in docs_with_score]

kb_id = "cong_ty_mo_dat_hiem"
doc_id = "doc_id"
kb = KnowledgeBase(kb_id, exists_ok=True, storage_directory='example_kb_data')

class CustomDSRagRetriever(BaseRetriever):
    k: int = 3

    def _get_relevant_documents(self, query: str) -> List[Document]:
        results = kb.query([query])
        print('Querying DSRag...', results)
        # Convert DSRag results to Document objects
        matching_documents = [Document(page_content=str(segment['content']), metadata={}) for segment in results]
        return matching_documents

model = ChatOpenAI(model="gpt-4o", temperature=0)

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()
    if "retriever" not in st.session_state:
        st.session_state.retriever = CustomNeo4jRetriever(k=3)

# Define tools
@tool
def search_information(query: str):
    """Retrieve information based on the query """
    print('Querying retriever...', query, st.session_state.retriever)
    search_result = st.session_state.retriever.invoke(query)
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

def get_chain_answer_with_retriever(query: str, retriever: BaseRetriever):
    st.session_state.retriever = retriever
    messages = [HumanMessage(content=query)]
    response = agent.invoke({"messages": messages})
    return response["messages"][-1].content

def main():
    st.set_page_config(page_title="Bot tài chính", page_icon="🤖", layout="wide")
    st.title("Compare Document Chatbot Retrievers 💬")
    
    # Initialize retrievers
    neo4j_retriever = CustomNeo4jRetriever(k=3)
    dsrag_retriever = CustomDSRagRetriever()
    
    # Single input at the top
    st.markdown("### Enter your question below to compare both retrievers")
    user_prompt = st.chat_input("Ask both retrievers...", key="unified_input")
    
    # Create two columns for side-by-side comparison
    col1, col2 = st.columns(2)
    
    # Initialize session state for both chat histories
    if "messages_neo4j" not in st.session_state:
        st.session_state.messages_neo4j = []
    if "messages_dsrag" not in st.session_state:
        st.session_state.messages_dsrag = []

    # Process input for both retrievers if there's a new prompt
    if user_prompt:
        # Handle Neo4j responses
        st.session_state.messages_neo4j.append({"role": "user", "content": user_prompt})
        neo4j_response = get_chain_answer_with_retriever(user_prompt, neo4j_retriever)
        st.session_state.messages_neo4j.append({"role": "assistant", "content": neo4j_response})
        
        # Handle DSRag responses
        st.session_state.messages_dsrag.append({"role": "user", "content": user_prompt})
        dsrag_response = get_chain_answer_with_retriever(user_prompt, dsrag_retriever)
        st.session_state.messages_dsrag.append({"role": "assistant", "content": dsrag_response})

    # Neo4j Column
    with col1:
        st.header("Neo4j Vector Retriever")
        # Display Neo4j chat messages
        for message in st.session_state.messages_neo4j:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # DSRag Column
    with col2:
        st.header("DSRag Retriever")
        # Display DSRag chat messages
        for message in st.session_state.messages_dsrag:
            with st.chat_message(message["role"]):
                st.write(message["content"])

if __name__ == "__main__":
    main()

