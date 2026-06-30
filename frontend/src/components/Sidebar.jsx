import React, { useState } from 'react';
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

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <Zap className="logo-icon" size={24} strokeWidth={2.5} />
          {!collapsed && <span className="logo-text">EIRA</span>}
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
              <div className="incident-item critical">
                <div className="incident-indicator"></div>
                <div className="incident-content">
                  <p className="incident-name">Payment Failure</p>
                  <p className="incident-meta">Critical</p>
                </div>
                <p className="incident-time">2m ago</p>
              </div>
              <div className="incident-item high">
                <div className="incident-indicator"></div>
                <div className="incident-content">
                  <p className="incident-name">Checkout API 500</p>
                  <p className="incident-meta">High</p>
                </div>
                <p className="incident-time">1h ago</p>
              </div>
              <div className="incident-item medium">
                <div className="incident-indicator"></div>
                <div className="incident-content">
                  <p className="incident-name">User Login Issue</p>
                  <p className="incident-meta">Medium</p>
                </div>
                <p className="incident-time">3h ago</p>
              </div>
              <div className="incident-item low">
                <div className="incident-indicator"></div>
                <div className="incident-content">
                  <p className="incident-name">Email Service Down</p>
                  <p className="incident-meta">Low</p>
                </div>
                <p className="incident-time">1d ago</p>
              </div>
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
