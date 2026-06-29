import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import AnalyzeIncident from './pages/AnalyzeIncident';
import Header from './components/Header';

function App() {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnected(true);
      };

      wsRef.current.onerror = () => {
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

  return (
    <div className="app">
      <Header connected={connected} />
      <AnalyzeIncident wsRef={wsRef} />
    </div>
  );
}

export default App;
