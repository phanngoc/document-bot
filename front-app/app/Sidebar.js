"use client"

import { useState, useEffect } from 'react';  // Add useEffect import
import { v4 as uuidv4 } from 'uuid';  // Add uuid import
import { useRouter } from 'next/navigation';  // Correct import for useRouter

export default function Sidebar({ setShowModal, removeAssistant }) {
  const [threadId, setThreadId] = useState(null);  // Add state for threadId
  const [threads, setThreads] = useState([]);  // Add state for threads
  const [assistants, setAssistants] = useState([]);  // Add state for assistants
  const [selectedAssistants, setSelectedAssistants] = useState({}); // State để lưu trợ lý đã chọn
  const [newAssistantName, setNewAssistantName] = useState(''); // Thêm state cho tên
  const [newAssistantUrl, setNewAssistantUrl] = useState(''); // Thêm state cho URL
  const [newAssistantCssSelector, setNewAssistantCssSelector] = useState(''); // Thêm state cho CSS selector
  const [newAssistantTool, setNewAssistantTool] = useState(''); // Thêm state cho tool
  const router = useRouter();  // Initialize useRouter

  useEffect(() => {
    const fetchUserAssistants = async () => {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/user/assistants', {
        method: 'GET',
        headers: {
          'Authorization': token,
        },
      });
      const data = await response.json();
      setAssistants(data);
    };

    fetchUserAssistants();
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

  const handleAssistantChange = (assistantId) => {
    setSelectedAssistants((prev) => ({
      ...prev,
      [assistantId]: !prev[assistantId], // Chuyển đổi trạng thái chọn
    }));
  };

  const handleAddAssistant = async () => {
    const response = await fetch('/api/assistants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            name: newAssistantName, 
            url: newAssistantUrl, 
            css_selector: newAssistantCssSelector,
            tool: newAssistantTool.split(',').map(tool => tool.trim()) // Chia tách và loại bỏ khoảng trắng
        }),
    });
    const newAssistant = await response.json();
    setAssistants([...assistants, newAssistant]);
    setShowModal(false);
    setNewAssistantName('');
    setNewAssistantUrl('');
    setNewAssistantCssSelector('');
    setNewAssistantTool(''); // Reset tool
  };

  return (
    <div className="sidebar w-1/4 bg-gray-800 text-white p-5">
      <h2 className="text-2xl font-bold mb-5">Chọn Trợ Lý</h2>
      <ul>
        {assistants.map((assistant) => (
          <li key={assistant.id} className="mb-3 flex items-center">
            <input
              type="checkbox"
              checked={!!selectedAssistants[assistant.id]}
              onChange={() => handleAssistantChange(assistant.id)}
            />
            <span className="ml-2">{assistant.name}</span>
          </li>
        ))}
      </ul>
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
      <input
        type="text"
        placeholder="Tool (phân cách bởi dấu phẩy)"
        value={newAssistantTool}
        onChange={(e) => setNewAssistantTool(e.target.value)}
        className="mb-3 p-2 border border-gray-300 rounded w-full"
      />
    </div>
  );
}
