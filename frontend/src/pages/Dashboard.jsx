import React, { useState, useEffect } from 'react';
import { Activity, BookOpen, Brain, Bot, Clock, AlertTriangle } from 'lucide-react';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Real-time incident response metrics</p>
      </div>

      <div className="masonry-grid">
        {/* System Health - Large Card */}
        <div className="card card-lg card-success">
          <div className="card-header">
            <h3>System Health</h3>
            <Activity size={24} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">98.5%</div>
            <div className="metric-label">Uptime (24h)</div>
            <div className="metric-change positive">+2.1%</div>
          </div>
        </div>

        {/* Documents Indexed - Medium Card */}
        <div className="card card-md card-info">
          <div className="card-header">
            <h3>Documents</h3>
            <BookOpen size={20} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">{stats?.chatbot?.uploaded_docs_count || 0}</div>
            <div className="metric-label">KB Entries</div>
            <div className="metric-change positive">+3</div>
          </div>
        </div>

        {/* Memory Entries - Medium Card */}
        <div className="card card-md card-warning">
          <div className="card-header">
            <h3>Memory</h3>
            <Brain size={20} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">{stats?.memory?.total_incidents || 0}</div>
            <div className="metric-label">Past Incidents</div>
            <div className="metric-change positive">+12</div>
          </div>
        </div>

        {/* AI Agents - Small Card */}
        <div className="card card-sm card-success">
          <div className="card-header">
            <h3>AI Agents</h3>
            <Bot size={18} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">6/6</div>
            <div className="metric-label">Online</div>
          </div>
        </div>

        {/* Avg Resolution - Small Card */}
        <div className="card card-sm card-success">
          <div className="card-header">
            <h3>Resolution</h3>
            <Clock size={18} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">12m</div>
            <div className="metric-label">Avg Time</div>
          </div>
        </div>

        {/* Incidents Today - Small Card */}
        <div className="card card-sm card-info">
          <div className="card-header">
            <h3>Incidents</h3>
            <AlertTriangle size={18} strokeWidth={2} />
          </div>
          <div className="card-content">
            <div className="metric-value">4</div>
            <div className="metric-label">Today</div>
          </div>
        </div>

        {/* Incident Trend - Large Card */}
        <div className="card card-lg card-chart">
          <div className="card-header">
            <h3>Incident Trend (7 days)</h3>
          </div>
          <div className="card-content">
            <svg viewBox="0 0 300 180" className="mini-chart">
              <polyline
                points="10,160 50,130 90,100 130,80 170,90 210,60 250,40"
                fill="none"
                stroke="url(#trendGradient)"
                strokeWidth="3"
              />
              <defs>
                <linearGradient id="trendGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#9471ff" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Severity Distribution - Large Card */}
        <div className="card card-lg card-chart">
          <div className="card-header">
            <h3>Severity Distribution</h3>
          </div>
          <div className="card-content">
            <div className="severity-breakdown">
              <div className="severity-item">
                <span className="severity-label">Critical</span>
                <div className="severity-bar">
                  <div className="severity-fill critical" style={{ width: '35%' }}></div>
                </div>
                <span className="severity-count">14</span>
              </div>
              <div className="severity-item">
                <span className="severity-label">High</span>
                <div className="severity-bar">
                  <div className="severity-fill high" style={{ width: '52%' }}></div>
                </div>
                <span className="severity-count">21</span>
              </div>
              <div className="severity-item">
                <span className="severity-label">Medium</span>
                <div className="severity-bar">
                  <div className="severity-fill medium" style={{ width: '45%' }}></div>
                </div>
                <span className="severity-count">18</span>
              </div>
              <div className="severity-item">
                <span className="severity-label">Low</span>
                <div className="severity-bar">
                  <div className="severity-fill low" style={{ width: '28%' }}></div>
                </div>
                <span className="severity-count">11</span>
              </div>
            </div>
          </div>
        </div>

        {/* Top Root Causes - Medium Card */}
        <div className="card card-md card-list">
          <div className="card-header">
            <h3>Top Root Causes</h3>
          </div>
          <div className="card-content">
            <div className="root-causes">
              <div className="cause-item">
                <span className="cause-name">Database Issues</span>
                <span className="cause-count">18</span>
              </div>
              <div className="cause-item">
                <span className="cause-name">Memory Leaks</span>
                <span className="cause-count">12</span>
              </div>
              <div className="cause-item">
                <span className="cause-name">Network Timeout</span>
                <span className="cause-count">9</span>
              </div>
              <div className="cause-item">
                <span className="cause-name">Config Error</span>
                <span className="cause-count">6</span>
              </div>
              <div className="cause-item">
                <span className="cause-name">Resource Exhaustion</span>
                <span className="cause-count">5</span>
              </div>
            </div>
          </div>
        </div>

        {/* Resolution Time Stats - Small Card */}
        <div className="card card-sm card-stats">
          <div className="card-header">
            <h3>Resolution (Hrs)</h3>
          </div>
          <div className="card-content">
            <div className="stat-mini">
              <div className="stat-value">0.8</div>
              <div className="stat-label">Avg</div>
            </div>
            <div className="stat-mini">
              <div className="stat-value">5m</div>
              <div className="stat-label">Min</div>
            </div>
            <div className="stat-mini">
              <div className="stat-value">2.5</div>
              <div className="stat-label">Max</div>
            </div>
          </div>
        </div>

        {/* AI Performance - Small Card */}
        <div className="card card-sm card-stats">
          <div className="card-header">
            <h3>AI Performance</h3>
          </div>
          <div className="card-content">
            <div className="stat-mini">
              <div className="stat-value">94%</div>
              <div className="stat-label">Accuracy</div>
            </div>
            <div className="stat-mini">
              <div className="stat-value">91%</div>
              <div className="stat-label">Confidence</div>
            </div>
          </div>
        </div>

        {/* Memory Usage - Small Card */}
        <div className="card card-sm card-stats">
          <div className="card-header">
            <h3>Memory Usage</h3>
          </div>
          <div className="card-content">
            <div className="stat-mini">
              <div className="stat-value">{stats?.chatbot?.total_memory_kb || 0}</div>
              <div className="stat-label">KB</div>
            </div>
            <div className="stat-mini">
              <div className="stat-value">{stats?.backups || 0}</div>
              <div className="stat-label">Backups</div>
            </div>
          </div>
        </div>

        {/* Recent Incidents Table - XL Card */}
        <div className="card card-xl card-table">
          <div className="card-header">
            <h3>Recent Incidents</h3>
          </div>
          <div className="card-content">
            <div className="incidents-table">
              <div className="table-header">
                <div className="col-id">ID</div>
                <div className="col-severity">Severity</div>
                <div className="col-cause">Root Cause</div>
                <div className="col-time">Time</div>
                <div className="col-status">Status</div>
              </div>
              <div className="table-body">
                {[
                  { id: 'INC-1847', severity: 'Critical', cause: 'DB Pool Exhaustion', time: '12m', status: 'Resolved' },
                  { id: 'INC-1846', severity: 'High', cause: 'Memory Leak', time: '34m', status: 'Resolved' },
                  { id: 'INC-1845', severity: 'High', cause: 'API Timeout', time: '8m', status: 'Resolved' },
                  { id: 'INC-1844', severity: 'Medium', cause: 'Config Error', time: '22m', status: 'Resolved' }
                ].map((incident, idx) => (
                  <div key={idx} className="table-row">
                    <div className="col-id">{incident.id}</div>
                    <div className={`col-severity severity-${incident.severity.toLowerCase()}`}>
                      {incident.severity}
                    </div>
                    <div className="col-cause">{incident.cause}</div>
                    <div className="col-time">{incident.time}</div>
                    <div className="col-status">
                      <span className="status-badge resolved">{incident.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
