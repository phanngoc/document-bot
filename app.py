from openai import OpenAI
import streamlit as st
from model import User, Message, MessageType, db, Assistant  # Import the models and database
from dotenv import load_dotenv
import os
import threading
import subprocess
from urllib.parse import urlparse
from build_index_search import build_query_engine  # Import the build_query_engine function

load_dotenv()  # Load environment variables from a .env file

# Initialize the database
db.connect()
db.create_tables([User, Message, Assistant])  # Add Assistant to the table creation

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.getenv("OPENAI_API_KEY"))
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"
    
    # List of Assistants
    assistants = Assistant.select()
    assistant_options = [assistant.name for assistant in assistants]
    selected_assistant = st.selectbox("Choose an Assistant", assistant_options)

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")
if "messages" not in st.session_state:
    # Load messages from the database
    st.session_state["messages"] = [
        {"role": msg.type, "content": msg.message} for msg in Message.select()
    ]

def build_query_engine_worker(collection_name):
    build_query_engine(collection_name)
    st.success("Query engine built successfully!")

# Add a button to run the build_query_engine function in a worker thread
if st.button("Build Query Engine"):
    threading.Thread(target=build_query_engine_worker, args=(selected_assistant,)).start()

# Initialize the query engine
query_engine = None

def run_scrapy_job(start_url):
    progress_bar = st.progress(0)
    os.chdir("crawler")
    subprocess.run(["scrapy", "crawl", "link_spider", "-a", f"start_url={start_url}"])
    os.chdir("..")
    global query_engine
    st.info("Building index...")
    progress_bar.progress(50)
    query_engine = build_query_engine(start_url, is_builded=True)
    st.success("Scrapy job and query engine build completed successfully!")

    # Extract the hostname from the URL
    parsed_url = urlparse(start_url)
    hostname = parsed_url.hostname

    # Create a record in the Assistant table with the hostname as the name
    assistant = Assistant.create(url=start_url, name=hostname, is_builded=True)
    
    # Update progress bar
    progress_bar.progress(100)
    
    # Append the new assistant to the options
    assistant_options.append(assistant.name)
    st.experimental_rerun()

# Add a text input and button to submit a URL and run the Scrapy job
start_url = st.text_input("Enter the start URL for Scrapy")
if st.button("Run Scrapy Job"):
    if start_url:
        threading.Thread(target=run_scrapy_job, args=(start_url,)).start()
        st.success("Scrapy job started successfully!")
    else:
        st.error("Please enter a valid URL.")

# Check if the selected assistant is built, and if not, run run_scrapy_job
if selected_assistant:
    assistant = Assistant.get(Assistant.name == selected_assistant)
    if not assistant.is_builded:
        st.warning(f"Assistant '{selected_assistant}' is not built. Running Scrapy job...")
        threading.Thread(target=run_scrapy_job, args=(assistant.url,)).start()
    else:
        query_engine = build_query_engine(assistant.url, is_builded=False)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Save user message to the database
    Message.create(user=None, type=MessageType.USER.value, message=prompt)

    # Use the query engine to generate a response
    if query_engine:
        response = query_engine.query(prompt)
        msg = response['result']
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
        
        # Save assistant message to the database
        Message.create(user=None, type=MessageType.ASSISTANT.value, message=msg)
    else:
        st.error("Query engine is not initialized. Please run the Scrapy job first.")