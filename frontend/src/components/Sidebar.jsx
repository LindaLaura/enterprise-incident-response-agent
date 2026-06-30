import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Zap,
  BookOpen,
  AlertCircle,
  Brain,
  Bot,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import '../styles/Sidebar.css';

const Sidebar = ({ activePage, onPageChange }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [recentIncidents, setRecentIncidents] = useState([]);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3, section: 'main' },
    { id: 'analyze', label: 'Analyze Incident', icon: Zap, section: 'main' },
    { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen, section: 'explore' },
    { id: 'incidents', label: 'Previous Incidents', icon: AlertCircle, section: 'explore' },
    { id: 'memory', label: 'Memory', icon: Brain, section: 'explore' },
    { id: 'agents', label: 'AI Agents', icon: Bot, section: 'system' },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp, section: 'system' },
    { id: 'settings', label: 'Settings', icon: Settings, section: 'system' }
  ];

  const sections = {
    main: 'Main',
    explore: 'Explore',
    system: 'System'
  };

  const groupedItems = Object.keys(sections).reduce((acc, section) => {
    acc[section] = menuItems.filter(item => item.section === section);
    return acc;
  }, {});

  useEffect(() => {
    fetchRecentIncidents();
    const interval = setInterval(fetchRecentIncidents, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchRecentIncidents = async () => {
    try {
      const response = await fetch('/api/incidents');
      const data = await response.json();

      if (data.incidents && Array.isArray(data.incidents)) {
        // Get last 4 incidents, sorted by timestamp (most recent first)
        const sorted = [...data.incidents]
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 4);

        setRecentIncidents(sorted);
      }
    } catch (error) {
      console.error('Failed to fetch recent incidents:', error);
    }
  };

  const getTimeAgo = (timestamp) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const seconds = Math.floor((now - date) / 1000);

      if (seconds < 60) return `${seconds}s ago`;
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
      if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
      return `${Math.floor(seconds / 86400)}d ago`;
    } catch {
      return 'recently';
    }
  };

  const getSeverityClass = (severity) => {
    if (!severity) return 'low';
    return severity.toLowerCase();
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <Zap className="logo-icon" size={24} strokeWidth={2.5} />
          {!collapsed && <span className="logo-text">Enterprise Incident Respone Agent</span>}
        </div>
        <button
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {Object.keys(sections).map(section => (
          <div key={section} className="nav-section">
            {!collapsed && <div className="section-label">{sections[section]}</div>}
            <ul className="nav-items">
              {groupedItems[section].map(item => {
                const Icon = item.icon;
                return (
                  <li key={item.id}>
                    <button
                      className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                      onClick={() => onPageChange(item.id)}
                      title={item.label}
                    >
                      <Icon className="nav-icon" size={20} strokeWidth={2} />
                      {!collapsed && <span className="nav-label">{item.label}</span>}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sidebar-recent">
        {!collapsed && (
          <>
            <div className="section-label">Recent Incidents</div>
            <div className="recent-incidents">
              {recentIncidents.length > 0 ? (
                recentIncidents.map((incident) => (
                  <div
                    key={incident.incident_id}
                    className={`incident-item ${getSeverityClass(incident.severity)}`}
                  >
                    <div className="incident-indicator"></div>
                    <div className="incident-content">
                      <p className="incident-name">
                        {incident.summary?.substring(0, 25) || incident.incident_id}
                      </p>
                      <p className="incident-meta">{incident.severity || 'Unknown'}</p>
                    </div>
                    <p className="incident-time">{getTimeAgo(incident.timestamp)}</p>
                  </div>
                ))
              ) : (
                <p style={{ color: '#a0a0a0', fontSize: '0.85rem', padding: '1rem' }}>
                  No incidents yet
                </p>
              )}
            </div>
          </>
        )}
      </div>

      <div className="sidebar-footer">
        {!collapsed && (
          <div className="version">v1.0.0</div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
