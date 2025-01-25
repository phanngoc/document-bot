"use client"

import { useState, useEffect } from 'react';  // Add useEffect import
import { v4 as uuidv4 } from 'uuid';  // Add uuid import
import { useRouter } from 'next/navigation';  // Correct import for useRouter

export default function Sidebar({ setShowModal, removeAssistant }) {
  const [threadId, setThreadId] = useState(null);  // Add state for threadId
  const [threads, setThreads] = useState([]);  // Add state for threads
  const [assistants, setAssistants] = useState([]);  // Add state for assistants
  const router = useRouter();  // Initialize useRouter

  useEffect(() => {
    // Fetch threads when the component mounts
    const fetchThreads = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5002/api/threads');
        const data = await response.json();
        console.log('data thread', data);
        setThreads(data);
      } catch (error) {
        console.error('Error fetching threads:', error);
      }
    };

    // Fetch assistants when the component mounts
    const fetchAssistants = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5002/api/assistants');
        const data = await response.json();
        console.log('data assistants', data);
        setAssistants(data);
      } catch (error) {
        console.error('Error fetching assistants:', error);
      }
    };

    fetchThreads();
    fetchAssistants();
  }, []);

  const addAssistant = () => {
    setShowModal(true);
  };

  const newThread = async () => {
    const newThreadId = uuidv4();
    try {
      const response = await fetch('http://127.0.0.1:5002/api/threads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uuid: newThreadId }),
      });
      const data = await response.json();
      setThreads([...threads, data]);
      router.push(`/?thread_id=${newThreadId}`);  // Append thread_id to URL
    } catch (error) {
      console.error('Error creating new thread:', error);
    }
  };

  const loadMessages = async (threadId) => {
    try {
      const response = await fetch(`http://127.0.0.1:5002/api/messages?thread_id=${threadId}`);
      const data = await response.json();
      console.log('Messages:', data);
      // Handle messages data as needed
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  return (
    <div className="sidebar w-1/4 bg-gray-800 text-white p-5">
      <h2 className="text-2xl font-bold mb-5">Sidebar</h2>
      <ul>
        {assistants.map((assistant) => (
          <li key={assistant.id} className="mb-3 flex justify-between items-center">
            <a
              href="#"
              className="hover:underline max-w-xs overflow-hidden block whitespace-nowrap text-ellipsis"
              style={{ maxWidth: '320px' }}
            >
              {assistant.name}
            </a>
            <button onClick={() => removeAssistant(assistant.id)} className="ml-2 text-red-500 hover:text-red-700">
              &#x2716; {/* Unicode for a cross mark */}
            </button>
          </li>
        ))}
      </ul>
      <button
        onClick={addAssistant}  // Use addAssistant function
        className="mt-5 p-2 bg-blue-500 text-white rounded hover:bg-blue-700"
      >
        Add Assistant
      </button>
      <h3 className="text-xl font-bold mt-5">Threads</h3>
      <ul>
        {threads.map((thread) => (
          <li key={thread.id} className="mb-3">
            <a
              href="#"
              className="hover:underline"
              onClick={() => {
                setThreadId(thread.uuid);
                loadMessages(thread.uuid);
                router.push(`/?thread_id=${thread.uuid}`);  // Append thread_id to URL
              }}
            >
              {thread.uuid}
            </a>
          </li>
        ))}
      </ul>
      <button
        onClick={newThread}  // Use newThread function
        className="mt-5 p-2 bg-blue-500 text-white rounded hover:bg-blue-700"
      >
        New Thread
      </button>
    </div>
  );
}
