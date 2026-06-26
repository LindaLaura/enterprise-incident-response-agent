import React, { useState } from 'react';
import './Sidebar.css';

function Sidebar({ onClearChat, stats }) {
  const [showIncidents, setShowIncidents] = useState(false);

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <button className="nav-button" onClick={onClearChat}>
          🗑️ Clear Chat
        </button>

        <button
          className="nav-button"
          onClick={() => setShowIncidents(!showIncidents)}
        >
          📋 Recent Incidents
        </button>
      </nav>

      {showIncidents && stats?.memory?.total_incidents > 0 && (
        <div className="incidents-panel">
          <h3>Recent Incidents</h3>
          <p className="incident-count">
            Total: {stats.memory.total_incidents}
          </p>
          <div className="incident-info">
            <p>Root causes: {stats.memory.root_cause_types}</p>
            <p>Preferences: {stats.memory.user_preferences}</p>
          </div>
        </div>
      )}

      <div className="sidebar-stats">
        <h3>System Stats</h3>
        <div className="stat-item">
          <span>Memory Usage</span>
          <span className="stat-value">
            {stats?.chatbot?.total_memory_kb || 0}KB
          </span>
        </div>
        <div className="stat-item">
          <span>Messages</span>
          <span className="stat-value">
            {stats?.chatbot?.conversation_history_size || 0}
          </span>
        </div>
        <div className="stat-item">
          <span>Documents</span>
          <span className="stat-value">
            {stats?.chatbot?.uploaded_docs_count || 0}
          </span>
        </div>
        <div className="stat-item">
          <span>Backups</span>
          <span className="stat-value">{stats?.backups || 0}</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
