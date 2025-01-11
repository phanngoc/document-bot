import os
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'  # Disable fork safety for macOS

from llama_index.llms.openai import OpenAI
import streamlit as st
from model import Page, User, Message, MessageType, db, Assistant  # Import the models and database
from dotenv import load_dotenv
from urllib.parse import urlparse
from build_index_search import build_query_engine
from rq import Queue
from rq.job import Job
from llama_index.core import Settings
from scrapy_job import run_scrapy_job  # Import the run_scrapy_job function
from redis import Redis
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
import logging
from chroma_client import chroma_client  # Import the Chroma client
import time

load_dotenv()  # Load environment variables from a .env file

Settings.llm = OpenAI(model="gpt-4o", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)
Settings.text_splitter = SentenceSplitter(chunk_size=1024)

# Initialize the database
db.create_tables([User, Message, Assistant, Page])  # Add Assistant to the table creation

# Initialize the RQ queue
redis_conn = Redis()
q = Queue(connection=redis_conn, default_timeout=600)  # Increase the default timeout to 600 seconds

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Define your callback function
def job_done(job, connection, result, *args, **kwargs):
    logging.info(f"Job {job.id} completed with result: {result}")
    assistant_id = result[1]
    assistant = Assistant.get(Assistant.id == assistant_id)
    assistant.is_crawled = True
    assistant.save()
    logging.info(f"Assistant {assistant_id} is built successfully!")
    redis_conn.set(f"complete_job_{job.id}", 1)

def start_scrapy_job(start_url):
    # Extract the hostname from the URL
    parsed_url = urlparse(start_url)
    hostname = parsed_url.hostname

    # Check if an assistant with the same hostname already exists
    assistant, created = Assistant.get_or_create(url=start_url, name=hostname, 
        is_builded=False, is_crawled=False)
    if created:
        logging.info(f'Assistant created: {assistant.id}')
    else:
        logging.info(f'Assistant already exists: {assistant.id}')

    # Dispatch the job to the worker
    job = q.enqueue(run_scrapy_job, start_url, assistant.id, on_success='app.job_done')
    logging.info(f"Job {job.id} started for URL: {start_url}")
    st.session_state.current_job_id = job.id

def fn_change_assistant():
    selected_assistant = st.session_state.assistant_selectbox
    assistant = Assistant.get(Assistant.name == selected_assistant)
    if not assistant.is_crawled:
        st.warning(f"Assistant '{selected_assistant}' is not built. Running Scrapy job...")
        start_scrapy_job(assistant.url)
    else:
        st.session_state.query_engine = build_query_engine(assistant.name, assistant.id)
        logging.info(f'query_engine: {st.session_state.query_engine}')
    
    # Reload messages from the database for the selected assistant
    st.session_state["messages"] = [
        {"role": msg.type, "content": msg.message} for msg in Message.select().where(Message.assistant == assistant)
    ]

def on_assistant_change():
    logging.info(f'on_selectbox_change: {st.session_state.assistant_selectbox}')
    fn_change_assistant()

def delete_assistant(assistant_name):
    assistant = Assistant.get(Assistant.name == assistant_name)
    
    try:
        # Delete pages associated with the assistant
        Page.delete().where(Page.assistant == assistant).execute()
        
        # Delete the assistant
        assistant.delete_instance()
        
        st.success(f"Assistant '{assistant_name}' and its pages deleted successfully!")
        logging.info(f"Assistant '{assistant_name}' and its pages deleted successfully!")
        # Optionally, delete the collection name if applicable
        chroma_client.delete_collection(assistant_name)
        # Add code to delete the collection from the query engine if necessary
    except Exception as e:
        logging.error(f"Error deleting collection for assistant '{assistant_name}': {e}")
        st.error(f"Error deleting collection for assistant '{assistant_name}': {e}")

def check_job_status():
    if 'current_job_id' in st.session_state:
        job_id = st.session_state.current_job_id
        if redis_conn.get(f"complete_job_{job_id}") == b'1':
            assistant_id = job_id.split('_')[-1]
            assistant = Assistant.get(Assistant.id == assistant_id)
            st.session_state.query_engine = build_query_engine(assistant.name, assistant.id)
            st.success(f"Job {job_id} completed successfully!")
            redis_conn.delete(f"complete_job_{job_id}")
            del st.session_state.current_job_id

if selected_assistant := st.session_state.get("assistant_selectbox"):
    fn_change_assistant()

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.getenv("OPENAI_API_KEY"))
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    
    # List of Assistants
    assistants = Assistant.select()
    assistant_options = [assistant.name for assistant in assistants]
    selected_assistant = st.selectbox("Choose an Assistant",
        key="assistant_selectbox", options=
        assistant_options, on_change=on_assistant_change)

    # Add a text input and button to submit a URL and run the Scrapy job
    start_url = st.text_input("Enter the start URL for Scrapy")
    if st.button("Run Scrapy Job"):
        if start_url:
            start_scrapy_job(start_url)
            st.success("Scrapy job started successfully!")
        else:
            st.error("Please enter a valid URL.")
    
    # Add a button to delete the selected assistant
    if st.button("Delete Assistant"):
        if selected_assistant:
            delete_assistant(selected_assistant)
        else:
            st.error("Please select an assistant to delete.")

st.title("💬 Chatbot")
st.caption("🚀 A chatbot powered by OpenAI")
if "messages" not in st.session_state:
    # Load messages from the database filtered by the selected assistant's ID
    if selected_assistant:
        assistant = Assistant.get(Assistant.name == selected_assistant)
        st.session_state["messages"] = [
            {"role": msg.type, "content": msg.message} for msg in Message.select().where(Message.assistant == assistant.id)
        ]
    else:
        st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

@st.dialog("Reference Document")
def dialog_document(document_html):
    print('dialog_document:', document_html[:50])
    # st.write(document_html, unsafe_allow_html=True)


if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    assistant = Assistant.get(Assistant.name == selected_assistant)
    # Save user message to the database
    Message.create(user=None, type=MessageType.USER.value, message=prompt, assistant=assistant.id)

    # Use the query engine to generate a response
    if st.session_state.query_engine is not None:
        response = st.session_state.query_engine.query(prompt)
        print('response:', response)
        msg = response.response
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
        
        # Save assistant message to the database
        Message.create(user=None, type=MessageType.ASSISTANT.value, message=msg, assistant=assistant.id)
        message = st.chat_message("document")

    else:
        st.error("Query engine is not initialized. Please run the Scrapy job first.")
