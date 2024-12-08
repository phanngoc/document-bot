from llama_index.llms.openai import OpenAI
import streamlit as st
from model import Page, User, Message, MessageType, db, Assistant  # Import the models and database
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
from build_index_search import build_query_engine
from rq import Queue
from llama_index.core import Settings
from scrapy_job import run_scrapy_job  # Import the run_scrapy_job function
from redis import Redis
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

load_dotenv()  # Load environment variables from a .env file

Settings.llm = OpenAI(model="gpt-4o", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)
Settings.text_splitter = SentenceSplitter(chunk_size=1024)

# Initialize the database
db.connect()
db.create_tables([User, Message, Assistant, Page])  # Add Assistant to the table creation

# Initialize the query engine
query_engine = None


# Initialize the RQ queue
q = Queue(connection=Redis())

# Define your callback function
def job_done(job, connection, result, *args, **kwargs):
    print(f"Job {job.id} completed with result: {result}")
    assistant_id = result[1]
    assistant = Assistant.get(Assistant.id == assistant_id)
    assistant.is_crawled = True
    assistant.save()
    print(f"Assistant {assistant_id} is built successfully!")

def start_scrapy_job(start_url):
    # Extract the hostname from the URL
    parsed_url = urlparse(start_url)
    hostname = parsed_url.hostname

    # Check if an assistant with the same hostname already exists
    assistant, created = Assistant.get_or_create(url=start_url, defaults={"name": hostname, "is_builded": True})
    if created:
        print('Assistant created:', assistant.id)
    else:
        print('Assistant already exists:', assistant.id)

    # Dispatch the job to the worker
    job = q.enqueue(run_scrapy_job, start_url, assistant.id, on_success='app.job_done')
    print(f"Job {job.id} started for URL: {start_url}")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.getenv("OPENAI_API_KEY"))
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    
    # List of Assistants
    assistants = Assistant.select()
    assistant_options = [assistant.name for assistant in assistants]
    selected_assistant = st.selectbox("Choose an Assistant", assistant_options)

    # Add a text input and button to submit a URL and run the Scrapy job
    start_url = st.text_input("Enter the start URL for Scrapy")
    if st.button("Run Scrapy Job"):
        if start_url:
            start_scrapy_job(start_url)
            st.success("Scrapy job started successfully!")
        else:
            st.error("Please enter a valid URL.")

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")
if "messages" not in st.session_state:
    # Load messages from the database
    st.session_state["messages"] = [
        {"role": msg.type, "content": msg.message} for msg in Message.select()
    ]

# Check if the selected assistant is built, and if not, run run_scrapy_job
if selected_assistant:
    assistant = Assistant.get(Assistant.name == selected_assistant)
    if not assistant.is_builded:
        st.warning(f"Assistant '{selected_assistant}' is not built. Running Scrapy job...")
        start_scrapy_job(assistant.url)
    else:
        query_engine = build_query_engine(assistant.name, assistant.id)
        print('query_engine:', query_engine)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Save user message to the database
    Message.create(user=None, type=MessageType.USER.value, message=prompt)

    # Use the query engine to generate a response
    if query_engine:
        response = query_engine.query(prompt)
        print('response:', response)
        msg = response.response
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
        
        # Save assistant message to the database
        Message.create(user=None, type=MessageType.ASSISTANT.value, message=msg)
    else:
        st.error("Query engine is not initialized. Please run the Scrapy job first.")