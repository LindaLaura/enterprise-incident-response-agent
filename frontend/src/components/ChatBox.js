import React, { useState, useEffect, useRef } from 'react';
import './ChatBox.css';

function ChatBox({ messages, onSendMessage, loading }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      handleSend(e);
    }
  };

  return (
    <div className="chatbox">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome to Incident Response Agent</h2>
            <p>Describe your incident or paste logs to get started</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.type}`}>
            <div className="message-header">
              <span className="message-role">{msg.type === 'user' ? 'You' : msg.type === 'error' ? 'Error' : 'Agent'}</span>
              {msg.timestamp && (
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              )}
            </div>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-loading">
            <div className="loading-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>Analyzing incident...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSend}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe the incident or paste logs here..."
          disabled={loading}
          rows="4"
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Analyzing...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default ChatBox;
