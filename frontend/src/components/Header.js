import React from 'react';
import { Bot } from 'lucide-react';
import './Header.css';

function Header({ connected, stats }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-title">
          <h1><Bot size={28} strokeWidth={2.5} style={{display: 'inline-block', marginRight: '0.5rem', verticalAlign: 'middle'}} /> Incident Response Agent</h1>
          <p>AI-Powered Incident Analysis with RAG & Memory</p>
        </div>

        <div className="header-status">
          <div className={`status-badge ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {connected ? 'Connected' : 'Disconnected'}
          </div>

          {stats && (
            <div className="stats-display">
              <div className="stat">
                <span className="stat-label">Incidents</span>
                <span className="stat-value">{stats.memory?.total_incidents || 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Backups</span>
                <span className="stat-value">{stats.backups || 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Memory</span>
                <span className="stat-value">{stats.chatbot?.total_memory_kb || 0}KB</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
