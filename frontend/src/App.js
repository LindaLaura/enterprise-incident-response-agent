import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatBox from './components/ChatBox';
import DocumentUpload from './components/DocumentUpload';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

function App() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    fetchStats();
    const statsInterval = setInterval(fetchStats, 5000);
    return () => clearInterval(statsInterval);
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnected(true);
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      };

      wsRef.current.onclose = () => {
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnected(false);
      setTimeout(connectWebSocket, 3000);
    }
  };

  const handleWebSocketMessage = (data) => {
    if (data.type === 'message') {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: data.content,
        timestamp: data.timestamp
      }]);
      setLoading(false);
    } else if (data.type === 'loading') {
      setLoading(true);
    } else if (data.type === 'error') {
      setMessages(prev => [...prev, {
        type: 'error',
        content: data.content
      }]);
      setLoading(false);
    } else if (data.type === 'stats') {
      setStats(data.content);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const sendMessage = (content) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      alert('Not connected to server');
      return;
    }

    const message = {
      type: 'message',
      content,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, {
      type: 'user',
      content,
      timestamp: message.timestamp
    }]);

    wsRef.current.send(JSON.stringify(message));
  };

  const clearChat = () => {
    setMessages([]);
    fetch('/api/chat/clear', { method: 'POST' })
      .catch(error => console.error('Failed to clear chat:', error));
  };

  return (
    <div className="app">
      <Header connected={connected} stats={stats} />
      <div className="app-container">
        <Sidebar onClearChat={clearChat} stats={stats} />
        <main className="main-content">
          <DocumentUpload onUploadSuccess={fetchStats} />
          <ChatBox
            messages={messages}
            onSendMessage={sendMessage}
            loading={loading}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
