import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Header from './components/Header';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './pages/Dashboard';
import AnalyzeIncident from './pages/AnalyzeIncident';

function App() {
  const [connected, setConnected] = useState(false);
  const [activePage, setActivePage] = useState('dashboard');
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = window.location.port === '3000' ? '8000' : window.location.port || '8000';
    const wsUrl = `${protocol}//${host}:${port}/ws/chat`;

    console.log('🔌 Attempting WebSocket connection to:', wsUrl);

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnected(true);
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnected(false);
      };

      wsRef.current.onclose = () => {
        console.log('⚠️  WebSocket closed, reconnecting in 3s...');
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnected(false);
      setTimeout(connectWebSocket, 3000);
    }
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard wsRef={wsRef} />;
      case 'analyze':
        return <AnalyzeIncident wsRef={wsRef} />;
      case 'knowledge':
        return <div className="page-placeholder">📚 Knowledge Base - Coming Soon</div>;
      case 'incidents':
        return <div className="page-placeholder">📋 Previous Incidents - Coming Soon</div>;
      case 'memory':
        return <div className="page-placeholder">🧠 Memory - Coming Soon</div>;
      case 'agents':
        return <div className="page-placeholder">🤖 AI Agents - Coming Soon</div>;
      case 'analytics':
        return <div className="page-placeholder">📈 Analytics - Coming Soon</div>;
      case 'settings':
        return <div className="page-placeholder">⚙️ Settings - Coming Soon</div>;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app">
      <Header connected={connected} />
      <div className="app-layout">
        <Sidebar activePage={activePage} onPageChange={setActivePage} />
        <main className="main-content">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
