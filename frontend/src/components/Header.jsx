import React from 'react';
import { Bot, Circle } from 'lucide-react';
import '../styles/Header.css';

const Header = ({ connected }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-logo">
          <div className="logo-icon">
            <Bot size={32} strokeWidth={2.5} />
          </div>
          <div className="logo-text">
            <h1>Enterprise Incident Response</h1>
            <p>AI-Powered Investigation Platform</p>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-indicator ${connected ? 'online' : 'offline'}`}>
            <Circle size={8} fill="currentColor" />
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
