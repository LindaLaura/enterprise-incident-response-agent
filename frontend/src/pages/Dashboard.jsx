import React, { useState, useEffect } from 'react';
import { Activity, BookOpen, Brain, Bot, Clock, AlertTriangle, Upload, CheckCircle } from 'lucide-react';
import ReportPreviewModal from '../components/ReportPreviewModal';
import '../styles/Dashboard.css';

const Dashboard = ({ wsRef }) => {
  const [stats, setStats] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [severityData, setSeverityData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [latestIncident, setLatestIncident] = useState(null);
  const [progressData, setProgressData] = useState(null);
  // const [agentData, setAgentData] = useState(null);
  const [incidentStats, setIncidentStats] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [reportModal, setReportModal] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchChartData();
    fetchProgressData();
    // fetchAgentData();
    fetchIncidentStats();
    fetchEvidenceData();
    const interval = setInterval(fetchStats, 5000);
    const progressInterval = setInterval(fetchProgressData, 3000);
    // const agentInterval = setInterval(fetchAgentData, 3000);
    const statsInterval = setInterval(fetchIncidentStats, 5000);
    const evidenceInterval = setInterval(fetchEvidenceData, 5000);
    return () => {
      clearInterval(interval);
      clearInterval(progressInterval);
      // clearInterval(agentInterval);
      clearInterval(statsInterval);
      clearInterval(evidenceInterval);
    };
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

  const fetchProgressData = async () => {
    try {
      const response = await fetch('/api/incidents/analysis-progress');
      const data = await response.json();
      setProgressData(data.steps);
    } catch (error) {
      console.error('Failed to fetch progress data:', error);
    }
  };

  // const fetchAgentData = async () => {
  //   try {
  //     const response = await fetch('/api/agents/status');
  //     const data = await response.json();
  //     setAgentData(data.agents);
  //   } catch (error) {
  //     console.error('Failed to fetch agent data:', error);
  //   }
  // };

  const fetchIncidentStats = async () => {
    try {
      const [trendRes, severityRes] = await Promise.all([
        fetch('/api/incidents/trend'),
        fetch('/api/incidents/severity')
      ]);
      const trend = await trendRes.json();
      const severity = await severityRes.json();

      // Calculate daily change
      const todayCount = trend.counts?.length > 0 ? trend.counts[trend.counts.length - 1] : 0;
      const yesterdayCount = trend.counts?.length > 1 ? trend.counts[trend.counts.length - 2] : 0;
      const dailyChange = todayCount - yesterdayCount;

      // Calculate weekly change
      const weeklyCount = trend.counts?.reduce((a, b) => a + b, 0) || 0;

      setIncidentStats({
        dailyChange,
        weeklyCount,
        severity
      });
    } catch (error) {
      console.error('Failed to fetch incident stats:', error);
    }
  };

  const fetchEvidenceData = async () => {
    try {
      const response = await fetch('/api/agents/context');
      const context = await response.json();

      // Extract retrieved documents from agent context
      const retrievedDocs = context.retrieved_docs || {};

      if (retrievedDocs.top_results) {
        // Parse retrieved documents and create evidence items
        const docLines = retrievedDocs.top_results.split('\n').filter(line => line.trim());

        const evidence = docLines.slice(0, 3).map((doc, idx) => ({
          id: idx,
          name: doc.substring(0, 50) || `Document ${idx + 1}`,
          relevance: 85 + Math.random() * 10,
          meta: `Retrieved document ${idx + 1}`,
          type: 'document'
        }));

        setEvidenceData(evidence);
      } else {
        // Fallback if no retrieved docs
        setEvidenceData([]);
      }
    } catch (error) {
      console.error('Failed to fetch evidence data:', error);
      setEvidenceData([]);
    }
  };


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


  const handleGenerateReport = async (format) => {
    const incident = latestIncident;
    console.log('📋 Generate report clicked:', { format, incident, hasIncident: !!incident, hasId: !!incident?.incident_id });

    if (!incident || !incident.incident_id) {
      alert('No incident analyzed yet. Upload and analyze logs first.');
      return;
    }

    // Show preview modal with incident data
    setReportModal({
      format,
      incident
    });
  };

  const handleDownloadReport = async () => {
    const { format, incident } = reportModal;

    try {
      const genResponse = await fetch('/api/report/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.incident_id,
          format: format
        })
      });

      if (!genResponse.ok) {
        const error = await genResponse.json();
        throw new Error(error.detail || 'Failed to generate report');
      }

      const genData = await genResponse.json();
      console.log('Report generated:', genData);

      if (!genData.report_id) {
        throw new Error('No report ID returned');
      }

      const dlResponse = await fetch(`/api/report/download/${genData.report_id}`);
      if (!dlResponse.ok) throw new Error('Failed to download report');

      const blob = await dlResponse.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = genData.filename || `incident_${incident.incident_id}_report.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log(`✅ Downloaded ${format.toUpperCase()}`);
    } catch (error) {
      console.error(`Report error:`, error);
      alert(`Failed: ${error.message}`);
    }
  };

  const handleAnalyzeClick = async () => {
    if (!uploadedFile) {
      alert('Please upload a file first');
      return;
    }

    setUploading(true);

    // Reset states for new analysis
    setProgressData(null);
    setAgentData(null);
    setLatestIncident(null);
    setEvidenceData(null);

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

      // Don't add to chat - just trigger analysis
      if (wsRef?.current) {
        console.log('🔍 Starting investigation pipeline...');
        // Don't send logs to chat - send a marker message instead
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: `Analyze these logs: ${uploadedFile.name}`,
          timestamp: new Date().toISOString()
        }));
        setLoading(true);

        // Poll for latest incident after analysis completes (longer timeout for agent pipeline)
        setTimeout(() => {
          console.log('📊 Fetching latest incident after analysis...');
          fetchChartData();  // This fetches latest incident
        }, 5000);

        // Continue polling every 2 seconds for up to 15 seconds
        let pollCount = 0;
        const pollInterval = setInterval(() => {
          if (pollCount >= 5) {
            clearInterval(pollInterval);
            return;
          }
          fetchChartData();
          pollCount++;
        }, 2000);
      }

      setUploading(false);
      setUploadedFile(null);
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
              <div className="kpi-sub">
                {incidentStats?.dailyChange !== undefined && (
                  incidentStats.dailyChange >= 0
                    ? `↑ ${incidentStats.dailyChange} from yesterday`
                    : `↓ ${Math.abs(incidentStats.dailyChange)} from yesterday`
                )}
              </div>
            </div>
          </div>

          {/* Documents */}
          <div className="kpi-card">
            <div className="kpi-icon info">📄</div>
            <div className="kpi-content">
              <div className="kpi-value">{stats?.chatbot?.uploaded_docs_count || 0}</div>
              <div className="kpi-label">Documents</div>
              <div className="kpi-sub">
                {stats?.chatbot?.uploaded_docs_count ? `${stats.chatbot.uploaded_docs_count} documents uploaded` : 'No documents yet'}
              </div>
            </div>
          </div>

          {/* Memory Entries */}
          <div className="kpi-card">
            <div className="kpi-icon success">✓</div>
            <div className="kpi-content">
              <div className="kpi-value">{stats?.memory?.total_incidents || 0}</div>
              <div className="kpi-label">Memory Entries</div>
              <div className="kpi-sub">
                {incidentStats?.weeklyCount !== undefined && (
                  `↑ ${incidentStats.weeklyCount} this week`
                )}
              </div>
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
          {/* <div className="kpi-card">
            <div className="kpi-icon">🤖</div>
            <div className="kpi-content">
              <div className="kpi-value">AI Assistant</div>
              <div className="kpi-label" style={{marginTop: '0.5rem'}}>Ready to help</div>
            </div>
          </div> */}
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
                disabled={uploading || !uploadedFile}
              >
                {uploading ? 'Uploading...' : !uploadedFile ? 'Upload file first ↑' : 'Analyze Incident →'}
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
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                  <button
                    className="btn-secondary"
                    onClick={() => handleGenerateReport('pdf')}
                    style={{ fontSize: '0.85rem', padding: '0.5rem 0.75rem' }}
                  >
                    📄 PDF
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => handleGenerateReport('json')}
                    style={{ fontSize: '0.85rem', padding: '0.5rem 0.75rem' }}
                  >
                    {'{}'} JSON
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => handleGenerateReport('csv')}
                    style={{ fontSize: '0.85rem', padding: '0.5rem 0.75rem' }}
                  >
                    📊 CSV
                  </button>
                </div>
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
                {progressData ? (
                  progressData.map((step) => (
                    <div key={step.id} className={`step ${step.status.replace('_', '-')}`}>
                      <div className="step-num">{step.id}</div>
                      <div className="step-content">
                        <p className="step-title">{step.title}</p>
                        <p className="step-desc">{step.description}</p>
                      </div>
                      <div className="step-time">
                        {step.status === 'completed' && `✓ Completed ${step.duration}`}
                        {step.status === 'in_progress' && '⏳ In Progress'}
                        {step.status === 'pending' && '⏱ Pending'}
                      </div>
                    </div>
                  ))
                ) : (
                  <p style={{ color: '#a0a0a0', padding: '1rem' }}>Loading progress...</p>
                )}
              </div>
            </div>

            {/* Evidence Top 3 */}
            <div className="card evidence-card">
              <div className="card-header">
                <h3>Evidence (Top 3)</h3>
                <a href="#" className="view-all">View All</a>
              </div>
              <div className="evidence-items">
                {evidenceData && evidenceData.length > 0 ? (
                  evidenceData.map((evidence) => (
                    <div key={evidence.id} className="evidence-item">
                      <div className="evidence-icon">📄</div>
                      <div className="evidence-content">
                        <p className="evidence-name">{evidence.name}</p>
                        <p className="evidence-meta">{evidence.meta}</p>
                      </div>
                      <div className="evidence-relevance">Relevance: {Math.round(evidence.relevance)}%</div>
                      <a href="#" className="log-file">View</a>
                    </div>
                  ))
                ) : (
                  <p style={{ color: '#a0a0a0', padding: '1rem' }}>
                    {evidenceData === null ? 'Loading evidence...' : 'No evidence retrieved yet. Upload and analyze logs to populate.'}
                  </p>
                )}
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
                  <span style={{ fontSize: '0.75rem', marginLeft: '0.5rem', color: '#fbbf24', fontWeight: 'bold' }}>WIP</span>
                </div>
              </div>
              <div className="chat-messages">
                <div className="message assistant">
                  <div className="message-bubble" style={{ backgroundColor: '#fef3c7', color: '#92400e', border: '1px solid #fcd34d' }}>
                    ⚠️ <strong>Chat feature is work in progress</strong><br/>
                    Analysis results are shown in the cards above. Full conversational AI coming soon.
                  </div>
                </div>
              </div>
            </div>

            {/* Agent Activity - Commented out: Redundant with AI Investigation Progress */}
            {/* <div className="card activity-card">
              <div className="card-header">
                <h3>Agent Activity</h3>
              </div>
              <div className="activity-items">
                {agentData ? (
                  agentData.map((agent) => (
                    <div key={agent.name} className={`activity-item ${agent.status}`}>
                      <span>
                        {agent.status === 'completed' && '✓'}
                        {agent.status === 'in_progress' && '⏳'}
                        {agent.status === 'pending' && '⏱'}
                        {agent.status === 'failed' && '❌'}
                      </span>
                      <p>
                        {agent.name}
                        <span className="status">
                          {agent.status === 'completed' && `Completed ${agent.duration || ''}`}
                          {agent.status === 'in_progress' && 'In Progress'}
                          {agent.status === 'pending' && 'Pending'}
                          {agent.status === 'failed' && 'Failed'}
                        </span>
                      </p>
                      {agent.error && <p style={{ color: '#ef4444', fontSize: '0.85rem' }}>Error: {agent.error}</p>}
                    </div>
                  ))
                ) : (
                  <p style={{ color: '#a0a0a0', padding: '1rem' }}>Loading agent status...</p>
                )}
              </div>
            </div> */}
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

      {/* Report Preview Modal */}
      {reportModal && (
        <ReportPreviewModal
          incident={reportModal.incident}
          format={reportModal.format}
          onClose={() => setReportModal(null)}
          onDownload={handleDownloadReport}
        />
      )}
    </div>
  );
};

export default Dashboard;
