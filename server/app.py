import logging  # Add logging import
from flask import Flask, jsonify, request
from flask_socketio import SocketIO  # Add SocketIO import
from flask_cors import CORS  # Add CORS import
from model import Assistant, Page
from scrapy_job import run_scrapy_process
from rq import Queue
from rq.job import Job
from redis import Redis

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

if __name__ == '__main__':
    logging.info("Starting server on port 5002")
    socketio.run(app, host='0.0.0.0', port=5002)  # Use socketio.run instead of app.run
