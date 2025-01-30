"use client";

import { useState, useEffect } from 'react';
import socket from './socket';  // Import the socket connection
import Sidebar from './Sidebar';  // Import the Sidebar component
import FilePicker from './FilePicker';  // Import the FilePicker component
import ReactMarkdown from 'react-markdown';
import { useRouter, useSearchParams } from 'next/navigation';
import LoginPage from './LoginPage';  // Import trang đăng nhập
import { useQuery } from '@tanstack/react-query';  // Thêm import useQuery

export default function Page() {
  const [input, setInput] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [newAssistantName, setNewAssistantName] = useState('');
  const [newAssistantUrl, setNewAssistantUrl] = useState('');
  const [newAssistantCssSelector, setNewAssistantCssSelector] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);  // Thêm trạng thái đăng nhập
  const [user, setUser] = useState(null);  // Thêm state cho thông tin người dùng
  const [selectedAssistants, setSelectedAssistants] = useState({});
  const [assistantType, setAssistantType] = useState('');  // Thêm state cho loại assistant

  const { data: assistants, isLoading: isLoadingAssistants } = useQuery({
    queryKey: ['assistants'],
    queryFn: async () => {
      const response = await fetch('/api/assistants');
      if (!response.ok) throw new Error('Network response was not ok');
      return response.json();
    },
  });

  const { data: messages, isLoading: isLoadingMessages } = useQuery({
    queryKey: ['messages'],
    queryFn: async () => {
      const response = await fetch('/api/messages');
      if (!response.ok) throw new Error('Network response was not ok');
      return response.json();
    },
  });

  useEffect(() => {
    // Handle incoming messages from the server
    socket.on('message', (message) => {
      setMessages((prevMessages) => [...prevMessages, message]);
    });

    return () => {
      socket.off('message');
    };
  }, []);

  // Kiểm tra trạng thái đăng nhập (có thể từ cookie hoặc localStorage)
  useEffect(() => {
    const checkLogin = async () => {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/check-login', {
        method: 'GET',
        headers: {
          'Authorization': token  // Gửi token trong header
        }
      });
      if (response.ok) {
        const data = await response.json();
        setIsLoggedIn(true);
        // Lưu thông tin người dùng vào state
        setUser(data.user);  // Giả sử bạn đã tạo state user
      }
    };
    checkLogin();
  }, []);

  const router = useRouter();
  console.log('router', router);
  const searchParams = useSearchParams()
 
  const threadId = searchParams.get('thread_id')
  console.log('thread_id', threadId)

  const handleSend = async () => {
    if (input.trim()) {
      const userMessage = { message: input, type: 'user' };
      setMessages([...messages, userMessage]);
      setInput('');
      
      console.log('threadId', threadId)
      // Gửi yêu cầu chat đến server với assistant_ids đã chọn
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: input, 
          threadId: threadId, 
          assistant_ids: Object.keys(selectedAssistants).filter(id => selectedAssistants[id]) // Lấy các assistant_id đã chọn
        }), 
      });
      const data = await response.json();
      const botMessage = { message: data.response, type: 'bot' };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSend();
    }
  };

  const handleAddAssistant = async () => {
    const response = await fetch('/api/assistants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name: newAssistantName, 
        url: newAssistantUrl, 
        css_selector: newAssistantCssSelector,
        type: assistantType  // Gửi loại assistant
      }),
    });
    const newAssistant = await response.json();
    setAssistants([...assistants, newAssistant]);
    setShowModal(false);
    setNewAssistantName('');
    setNewAssistantUrl('');
    setNewAssistantCssSelector('');
    setAssistantType('');  // Reset loại assistant
  };

  const handleRemoveAssistant = async (id) => {
    await fetch(`/api/assistants/${id}`, {
      method: 'DELETE',
    });
    setAssistants(assistantsList.filter((assistant) => assistant.id !== id));
  };

  const handleFileSelect = (file) => {
    console.log('Selected file:', file);
    // Handle the selected file
  };

  if (!isLoggedIn) {
    return <LoginPage />;  // Hiển thị trang đăng nhập nếu chưa đăng nhập
  }

  if (user) {
    return <div>Xin chào, {user.name}</div>;  // Hiển thị tên người dùng
  }

  if (isLoadingAssistants || isLoadingMessages) {
    return <div>Loading...</div>;  // Hiển thị loading khi đang tải dữ liệu
  }

  return (
    <div className="flex h-screen">
      <Sidebar assistants={assistants} setShowModal={setShowModal} removeAssistant={handleRemoveAssistant} />
      <div className="chat-container flex flex-col flex-1 w-full mx-auto p-5 border border-gray-300 rounded-lg">
        <h1 className="text-3xl font-bold underline mb-5">Bot AI</h1>
        <div className="messages flex-1 overflow-y-auto mb-5">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`p-3 mb-3 rounded ${msg.type === 'user' ? 'bg-green-100 text-right' : 'bg-gray-100 text-left'}`}
            >
              <ReactMarkdown>{msg.message}</ReactMarkdown>
            </div>
          ))}
        </div>
        <div className="input-container flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}  // Add the event handler for Enter key
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
            <textarea
              placeholder="CSS Selector"
              value={newAssistantCssSelector}
              onChange={(e) => setNewAssistantCssSelector(e.target.value)}
              className="mb-3 p-2 border border-gray-300 rounded w-full"
            />
            <select
              value={assistantType}
              onChange={(e) => setAssistantType(e.target.value)}  // Cập nhật loại assistant
              className="mb-3 p-2 border border-gray-300 rounded w-full"
            >
              <option value="">Chọn loại assistant</option>
              <option value="Q&A bot">Q&A bot</option>
              <option value="SQL query bot">SQL query bot</option>
              <option value="RSS bot">RSS bot</option>
              <option value="Transcript bot">Transcript bot</option>
              <option value="Chat with pdf file">Chat with pdf file</option>
            </select>
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