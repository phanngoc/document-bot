import logging  # Add logging import
from flask import Flask, jsonify, request
from flask_socketio import SocketIO  # Add SocketIO import
from flask_cors import CORS  # Add CORS import
from model import Assistant, Page
from scrapy_job import run_scrapy_process
from rq import Queue
from rq.job import Job
from redis import Redis
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import uuid
from build_index_search import search_similarity

model = ChatOpenAI(model="gpt-4o")
memory = MemorySaver()

def state_modifier(state) -> list[BaseMessage]:
    """Given the agent state, return a list of messages for the chat model."""
    # We're using the message processor defined above.
    return trim_messages(
        state["messages"],
        token_counter=len,  # <-- len will simply count the number of messages rather than tokens
        max_tokens=5,  # <-- allow up to 5 messages.
        strategy="last",
        # Most chat models expect that chat history starts with either:
        # (1) a HumanMessage or
        # (2) a SystemMessage followed by a HumanMessage
        # start_on="human" makes sure we produce a valid chat history
        start_on="human",
        # Usually, we want to keep the SystemMessage
        # if it's present in the original history.
        # The SystemMessage has special instructions for the model.
        include_system=True,
        allow_partial=False,
    )


@tool
def search_chroma_db(query: str) -> str:
    """
    Searches the Chroma database for articles relevant to the user's query.
    Args:
        query (str): The search query string provided by the user.
    Returns:
        str: The text response containing the relevant articles.
    """
    """ return article relevance with user query """
    results = search_similarity(query)
    print("search_chroma_db:Results:", results)
    return results

tools = []
tools.append(search_chroma_db)

agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Initialize the RQ queue
redis_conn = Redis()
q = Queue(connection=redis_conn, default_timeout=600)  # Increase the default timeout to 600 seconds

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # Enable CORS support
socketio = SocketIO(app, cors_allowed_origins="*")  # Initialize SocketIO with CORS support

@app.route('/api/assistants', methods=['GET'])
def get_assistants():
    logging.info("Fetching all assistants")
    assistants = Assistant.select()
    assistant_list = [{"id": assistant.id, "name": assistant.name, "url": assistant.url} for assistant in assistants]
    return jsonify(assistant_list)

@app.route('/api/assistants', methods=['POST'])
def add_assistant():
    try:
        data = request.get_json()
        logging.info(f"Adding new assistant with data: {data}")
        assistant = Assistant.create(
            name=data['name'],
            url=data['url'],
            css_selector=data.get('css_selector')  # Handle css_selector field
        )

        job = q.enqueue(run_scrapy_process, data['name'], assistant.id)
        logging.info(f"Job {job.id} started for URL: {assistant.url}")
        return jsonify({"id": assistant.id, "name": assistant.name, "url": assistant.url, "css_selector": assistant.css_selector, "job_id": job.id}), 201
    except Exception as e:
        logging.error(f"Error adding assistant: {e}")
        return jsonify({"error": "Failed to add assistant"}), 500

@app.route('/api/assistants/<int:id>', methods=['DELETE'])
def delete_assistant(id):
    try:
        logging.info(f"Deleting assistant with id: {id}")
        assistant = Assistant.get(Assistant.id == id)
        assistant.delete_instance()
        # Add logic to delete all pages relevant to the assistant
        pages = Page.select().where(Page.assistant_id == id)
        for page in pages:
            page.delete_instance()
        return '', 204
    except Assistant.DoesNotExist:
        logging.error(f"Assistant with id {id} does not exist")
        return jsonify({"error": "Assistant not found"}), 404
    except Exception as e:
        logging.error(f"Error deleting assistant: {e}")
        return jsonify({"error": "Failed to delete assistant"}), 500

thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        print('api/chat:data:', data)
        query = data.get('query')
        if not query:
            return jsonify({"error": "Query and assistant_id are required"}), 400
    
        input_message = HumanMessage(content=query)
        responses = []
        for event in agent_executor.stream({"messages": [input_message]}, config, stream_mode="values"):
            event["messages"][-1].pretty_print()
            responses.append(event["messages"][-1].content)
        print('responses:', responses)
        response = responses[-1]
        print('response:', response)

        return jsonify({"response": response}), 200
    except Exception as e:
        logging.error(f"Error processing chat request: {e}")
        return jsonify({"error": "Failed to process chat request"}), 500

if __name__ == '__main__':
    logging.info("Starting server on port 5002")
    socketio.run(app, host='0.0.0.0', port=5002)  # Use socketio.run instead of app.run
