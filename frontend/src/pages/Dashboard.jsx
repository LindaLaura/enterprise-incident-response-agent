import React, { useState, useEffect } from 'react';
import { Activity, BookOpen, Brain, Bot, Clock, AlertTriangle, Upload, CheckCircle, MessageSquare, Send } from 'lucide-react';
import '../styles/Dashboard.css';

const Dashboard = ({ wsRef }) => {
  const [stats, setStats] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Why is this incident critical?' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState(null);
  const [severityData, setSeverityData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [latestIncident, setLatestIncident] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchChartData();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchChartData = async () => {
    try {
      const [trendRes, severityRes, incidentRes] = await Promise.all([
        fetch('/api/incidents/trend'),
        fetch('/api/incidents/severity'),
        fetch('/api/incidents/latest')
      ]);
      const trend = await trendRes.json();
      const severity = await severityRes.json();
      const incident = await incidentRes.json();
      setTrendData(trend);
      setSeverityData(severity);
      setLatestIncident(incident);
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
    }
  };

  useEffect(() => {
    if (!wsRef || !wsRef.current) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('💬 WebSocket message received:', data);

      if (data.type === 'message') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
        setLoading(false);
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.content}` }]);
        setLoading(false);
      }
    };

    wsRef.current.addEventListener('message', handleMessage);
    return () => wsRef.current?.removeEventListener('message', handleMessage);
  }, [wsRef]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleFileUpload = (file) => {
    setUploadedFile(file);
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !wsRef?.current) return;

    const userMsg = inputMessage.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInputMessage('');
    setLoading(true);

    console.log('📤 Sending message via WebSocket:', userMsg);
    wsRef.current.send(JSON.stringify({
      type: 'message',
      content: userMsg,
      timestamp: new Date().toISOString()
    }));
  };

  const handleAnalyzeClick = async () => {
    if (!uploadedFile) {
      alert('Please upload a file first');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');

      const result = await response.json();
      console.log('✅ File uploaded:', result);

      // Send analysis request via WebSocket
      if (wsRef?.current) {
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: `Analyze these logs: ${uploadedFile.name}`,
          timestamp: new Date().toISOString()
        }));
        setLoading(true);
      }

      setUploading(false);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + error.message);
      setUploading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Monitor and manage AI-powered incident response</p>
      </div>

      <div className="dashboard-grid">
        {/* Top KPI Cards */}
        <div className="kpi-row">
          {/* Active Incidents */}
          <div className="kpi-card">
            <div className="kpi-icon alert">⚠️</div>
            <div className="kpi-content">
              <div className="kpi-value">{stats?.memory?.total_incidents || 0}</div>
              <div className="kpi-label">Active Incidents</div>
              <div className="kpi-sub">↑ 2 from yesterday</div>
            </div>
          </div>

          {/* Documents */}
          <div className="kpi-card">
            <div className="kpi-icon info">📄</div>
            <div className="kpi-content">
              <div className="kpi-value">{stats?.chatbot?.uploaded_docs_count || 0}</div>
              <div className="kpi-label">Documents</div>
              <div className="kpi-sub">↑ 24 this week</div>
            </div>
          </div>

          {/* Memory Entries */}
          <div className="kpi-card">
            <div className="kpi-icon success">✓</div>
            <div className="kpi-content">
              <div className="kpi-value">{stats?.memory?.total_incidents || 0}</div>
              <div className="kpi-label">Memory Entries</div>
              <div className="kpi-sub">↑ 18 this week</div>
            </div>
          </div>

          {/* AI Agents */}
          <div className="kpi-card">
            <div className="kpi-icon">👤</div>
            <div className="kpi-content">
              <div className="kpi-value">6</div>
              <div className="kpi-label">AI Agents</div>
              <div className="kpi-sub">AI systems operational</div>
            </div>
          </div>

          {/* AI Assistant */}
          <div className="kpi-card">
            <div className="kpi-icon">🤖</div>
            <div className="kpi-content">
              <div className="kpi-value">AI Assistant</div>
              <div className="kpi-label" style={{marginTop: '0.5rem'}}>Ready to help</div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="content-grid">

          {/* LEFT: Upload & Root Cause */}
          <div className="col-left">
            {/* Upload Logs */}
            <div className="card upload-card">
              <div className="card-header">
                <h3>Upload Logs / Files</h3>
              </div>
              <div
                className="upload-zone"
                onClick={() => document.getElementById('file-input')?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const files = e.dataTransfer.files;
                  if (files.length > 0) setUploadedFile(files[0]);
                }}
              >
                <Upload size={48} strokeWidth={1.5} />
                <p>Drag and drop your log files here</p>
                <p className="upload-sub">or click to browse</p>
                {uploadedFile && (
                  <div className="uploaded-file">
                    <span>📄 {uploadedFile.name}</span>
                  </div>
                )}
              </div>
              <input
                id="file-input"
                type="file"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files?.length) setUploadedFile(e.target.files[0]);
                }}
              />
              <button
                className="btn-primary"
                onClick={handleAnalyzeClick}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Analyze Incident →'}
              </button>
              <p className="upload-support">Supports .log, .txt, .json, .pdf, .csv</p>
            </div>

            {/* Root Cause */}
            {latestIncident && (
              <div className="card root-cause-card">
                <div className="root-cause-icon">⚠️</div>
                <h3>Root Cause</h3>
                <div className="root-cause-value">{latestIncident.confidence}%</div>
                <p className="root-cause-label">Confidence</p>
                <p className="root-cause-desc"><strong>{latestIncident.primary_cause?.split(' ').slice(0, 5).join(' ')}</strong></p>
                <p className="root-cause-detail">{latestIncident.technical_impact}</p>
                <p className="root-cause-impact"><span className="impact-high">{latestIncident.severity}</span> {latestIncident.affected_users}</p>
                <p className="root-cause-rec"><strong>Recommendation</strong></p>
                <p className="root-cause-rec-text">{latestIncident.immediate_action}</p>
                <button className="btn-secondary">View Runbook</button>
              </div>
            )}
          </div>

          {/* MIDDLE: Analysis & Evidence */}
          <div className="col-middle">
            {/* AI Investigation Progress */}
            <div className="card progress-card">
              <div className="card-header">
                <h3>AI Investigation Progress</h3>
              </div>
              <div className="progress-steps">
                <div className="step completed">
                  <div className="step-num">1</div>
                  <div className="step-content">
                    <p className="step-title">Parse Logs</p>
                    <p className="step-desc">Extracting relevant log data</p>
                  </div>
                  <div className="step-time">✓ Completed 2.1s</div>
                </div>
                <div className="step completed">
                  <div className="step-num">2</div>
                  <div className="step-content">
                    <p className="step-title">Retrieve Documents (RAG)</p>
                    <p className="step-desc">Searching knowledge base for relevant info</p>
                  </div>
                  <div className="step-time">✓ Completed 3.4s</div>
                </div>
                <div className="step completed">
                  <div className="step-num">3</div>
                  <div className="step-content">
                    <p className="step-title">Search Memory</p>
                    <p className="step-desc">Looking for similar past incidents</p>
                  </div>
                  <div className="step-time">✓ Completed 1.8s</div>
                </div>
                <div className="step in-progress">
                  <div className="step-num">4</div>
                  <div className="step-content">
                    <p className="step-title">Root Cause Analysis</p>
                    <p className="step-desc">Analyzing patterns and identifying cause</p>
                  </div>
                  <div className="step-time">⏳ In Progress</div>
                </div>
                <div className="step pending">
                  <div className="step-num">5</div>
                  <div className="step-content">
                    <p className="step-title">Generate Report</p>
                    <p className="step-desc">Creating incident report & recommendations</p>
                  </div>
                  <div className="step-time">⏱ Pending</div>
                </div>
              </div>
            </div>

            {/* Evidence Top 3 */}
            <div className="card evidence-card">
              <div className="card-header">
                <h3>Evidence (Top 3)</h3>
                <a href="#" className="view-all">View All</a>
              </div>
              <div className="evidence-items">
                <div className="evidence-item">
                  <div className="evidence-icon">📄</div>
                  <div className="evidence-content">
                    <p className="evidence-name">payment_failure.log</p>
                    <p className="evidence-meta">Error rate: 53%</p>
                  </div>
                  <div className="evidence-relevance">Relevance: 89%</div>
                  <a href="#" className="log-file">Log File</a>
                </div>
                <div className="evidence-item">
                  <div className="evidence-icon">📄</div>
                  <div className="evidence-content">
                    <p className="evidence-name">Payment Gateway Runbook</p>
                    <p className="evidence-meta">PDF Document</p>
                  </div>
                  <div className="evidence-relevance">Relevance: 94%</div>
                  <a href="#" className="log-file">Log File</a>
                </div>
                <div className="evidence-item">
                  <div className="evidence-icon">📄</div>
                  <div className="evidence-content">
                    <p className="evidence-name">Similar Incident #INC-143</p>
                    <p className="evidence-meta">Past Incident</p>
                  </div>
                  <div className="evidence-relevance">Relevance: 92%</div>
                  <a href="#" className="log-file">Log File</a>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT: Chat & Activity */}
          <div className="col-right">
            {/* Chat Box */}
            <div className="card chat-card">
              <div className="chat-header">
                <div className="chat-title">
                  <span>🤖</span> AI Assistant
                  <span className="online-badge">●</span>
                </div>
              </div>
              <div className="chat-messages">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message ${msg.role}`}>
                    <div className="message-bubble">{msg.content}</div>
                  </div>
                ))}
                {loading && (
                  <div className="message assistant">
                    <div className="message-bubble typing">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                )}
              </div>
              <div className="chat-input">
                <input
                  type="text"
                  placeholder="Ask the agent anything..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button onClick={handleSendMessage} className="send-btn">
                  <Send size={18} />
                </button>
              </div>
            </div>

            {/* Agent Activity */}
            <div className="card activity-card">
              <div className="card-header">
                <h3>Agent Activity</h3>
              </div>
              <div className="activity-items">
                <div className="activity-item completed">
                  <span>✓</span>
                  <p>Parser Agent <span className="status">Completed</span></p>
                </div>
                <div className="activity-item completed">
                  <span>✓</span>
                  <p>Retriever Agent <span className="status">Completed</span></p>
                </div>
                <div className="activity-item completed">
                  <span>✓</span>
                  <p>Memory Agent <span className="status">Completed</span></p>
                </div>
                <div className="activity-item in-progress">
                  <span>⏳</span>
                  <p>Reasoning Agent <span className="status">In Progress</span></p>
                </div>
                <div className="activity-item pending">
                  <span>⏱</span>
                  <p>Recommendation Agent <span className="status">Pending</span></p>
                </div>
                <div className="activity-item pending">
                  <span>⏱</span>
                  <p>Reporter Agent <span className="status">Pending</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Charts */}
        <div className="charts-row">
          {/* Incident Trend */}
          <div className="card chart-card">
            <div className="card-header">
              <h3>Incident Trend</h3>
              <select className="select-period">
                <option>Last 7 Days</option>
              </select>
            </div>
            {trendData ? (
              <svg viewBox="0 0 400 200" className="chart-svg">
                <g>
                  {/* Y-axis labels */}
                  <text x="10" y="20" fontSize="12" fill="#a0a0a0">30</text>
                  <text x="10" y="110" fontSize="12" fill="#a0a0a0">15</text>
                  <text x="10" y="200" fontSize="12" fill="#a0a0a0">0</text>

                  {/* X-axis */}
                  <line x1="30" y1="180" x2="390" y2="180" stroke="rgba(148, 113, 255, 0.2)" strokeWidth="1" />

                  {/* Data points and lines */}
                  {trendData.counts && (
                    <>
                      <polyline
                        points={trendData.counts.map((count, i) => `${40 + i * 50},${180 - (count / 30) * 160}`).join(' ')}
                        fill="none"
                        stroke="url(#chartGradient)"
                        strokeWidth="3"
                      />
                      {trendData.counts.map((count, i) => (
                        <circle
                          key={i}
                          cx={40 + i * 50}
                          cy={180 - (count / 30) * 160}
                          r="4"
                          fill="#9471ff"
                        />
                      ))}
                    </>
                  )}
                </g>
                <defs>
                  <linearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#9471ff" />
                    <stop offset="100%" stopColor="#7c3aed" />
                  </linearGradient>
                </defs>
              </svg>
            ) : (
              <p style={{ color: '#a0a0a0' }}>Loading chart...</p>
            )}
          </div>

          {/* Incidents by Severity */}
          <div className="card chart-card">
            <div className="card-header">
              <h3>Incidents by Severity</h3>
            </div>
            {severityData ? (
              <div className="severity-chart">
                <svg viewBox="0 0 200 200" className="donut">
                  {(() => {
                    const total = severityData.total;
                    const low = (severityData.low / total) * 502;
                    const medium = (severityData.medium / total) * 502;
                    const high = (severityData.high / total) * 502;
                    const critical = (severityData.critical / total) * 502;

                    return (
                      <>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#10b981" strokeWidth="40" strokeDasharray={`${low} 502`} />
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#f59e0b" strokeWidth="40" strokeDasharray={`${medium} 502`} strokeDashoffset={`-${low}`} />
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#ef4444" strokeWidth="40" strokeDasharray={`${high} 502`} strokeDashoffset={`-${low + medium}`} />
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#3b82f6" strokeWidth="40" strokeDasharray={`${critical} 502`} strokeDashoffset={`-${low + medium + high}`} />
                        <text x="100" y="105" textAnchor="middle" fontSize="24" fill="#e0e0e0" fontWeight="bold">{total}</text>
                        <text x="100" y="125" textAnchor="middle" fontSize="12" fill="#a0a0a0">Total</text>
                      </>
                    );
                  })()}
                </svg>
                <div className="legend">
                  <div><span style={{color: '#10b981'}}>● Low</span> {Math.round((severityData.low / severityData.total) * 100)}%</div>
                  <div><span style={{color: '#f59e0b'}}>● Medium</span> {Math.round((severityData.medium / severityData.total) * 100)}%</div>
                  <div><span style={{color: '#ef4444'}}>● High</span> {Math.round((severityData.high / severityData.total) * 100)}%</div>
                  <div><span style={{color: '#3b82f6'}}>● Critical</span> {Math.round((severityData.critical / severityData.total) * 100)}%</div>
                </div>
              </div>
            ) : (
              <p style={{ color: '#a0a0a0' }}>Loading chart...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
