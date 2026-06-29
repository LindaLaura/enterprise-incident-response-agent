import React from 'react';
import '../styles/Header.css';

const Header = ({ connected }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-logo">
          <div className="logo-icon">⚡</div>
          <div className="logo-text">
            <h1>Enterprise Incident Response</h1>
            <p>AI-Powered Investigation Platform</p>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-indicator ${connected ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            <span className="status-text">
              {connected ? 'Connected' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
