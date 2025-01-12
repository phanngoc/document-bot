"use client";

import { useState, useEffect } from 'react';
import socket from './socket';  // Import the socket connection
import Sidebar from './Sidebar';  // Import the Sidebar component

export default function Page() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [assistants, setAssistants] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [newAssistantName, setNewAssistantName] = useState('');
  const [newAssistantUrl, setNewAssistantUrl] = useState('');

  useEffect(() => {
    async function fetchAssistants() {
      const response = await fetch('/api/assistants');
      const data = await response.json();
      setAssistants(data);
    }
    fetchAssistants();

    // Handle incoming messages from the server
    socket.on('message', (message) => {
      setMessages((prevMessages) => [...prevMessages, message]);
    });

    return () => {
      socket.off('message');
    };
  }, []);

  const handleSend = () => {
    if (input.trim()) {
      const userMessage = { text: input, role: 'user' };
      setMessages([...messages, userMessage]);
      setInput('');
      socket.emit('message', userMessage);  // Send the message to the server
    }
  };

  const handleAddAssistant = async () => {
    const response = await fetch('/api/assistants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newAssistantName, url: newAssistantUrl }),
    });
    const newAssistant = await response.json();
    setAssistants([...assistants, newAssistant]);
    setShowModal(false);
    setNewAssistantName('');
    setNewAssistantUrl('');
  };

  const handleRemoveAssistant = async (id) => {
    await fetch(`/api/assistants/${id}`, {
      method: 'DELETE',
    });
    setAssistants(assistants.filter((assistant) => assistant.id !== id));
  };

  return (
    <div className="flex h-screen">
      <Sidebar assistants={assistants} setShowModal={setShowModal} removeAssistant={handleRemoveAssistant} />
      <div className="chat-container flex flex-col flex-1 w-full mx-auto p-5 border border-gray-300 rounded-lg">
        <h1 className="text-3xl font-bold underline mb-5">Chatbot AI</h1>
        <div className="messages flex-1 overflow-y-auto mb-5">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`p-3 mb-3 rounded ${msg.role === 'user' ? 'bg-green-100 text-right' : 'bg-gray-100 text-left'}`}
            >
              {msg.text}
            </div>
          ))}
        </div>
        <div className="input-container flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 p-2 border border-gray-300 rounded"
          />
          <button
            onClick={handleSend}
            className="ml-2 p-2 bg-blue-500 text-white rounded hover:bg-blue-700"
          >
            Send
          </button>
        </div>
      </div>

      {showModal && (
        <div className="modal fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white p-5 rounded">
            <h2 className="text-2xl mb-5">Add New Assistant</h2>
            <input
              type="text"
              placeholder="Name"
              value={newAssistantName}
              onChange={(e) => setNewAssistantName(e.target.value)}
              className="mb-3 p-2 border border-gray-300 rounded w-full"
            />
            <input
              type="text"
              placeholder="URL"
              value={newAssistantUrl}
              onChange={(e) => setNewAssistantUrl(e.target.value)}
              className="mb-3 p-2 border border-gray-300 rounded w-full"
            />
            <div className="flex justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="mr-2 p-2 bg-gray-500 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAddAssistant}
                className="p-2 bg-blue-500 text-white rounded hover:bg-blue-700"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}