import React, { useState, useRef } from 'react';
import { Zap, Clipboard, RefreshCw, Upload } from 'lucide-react';
import PipelineVisualization from '../components/PipelineVisualization';
import DocumentUploadZone from '../components/DocumentUploadZone';
import EvidencePanel from '../components/EvidencePanel';
import MemoryPanel from '../components/MemoryPanel';
import RootCausePanel from '../components/RootCausePanel';
import ReportPreviewModal from '../components/ReportPreviewModal';
import '../styles/AnalyzeIncident.css';

const AnalyzeIncident = ({ wsRef }) => {
  const [logs, setLogs] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [reportModal, setReportModal] = useState(null);
  const fileInputRef = useRef(null);

  const pipelineConfig = [
    { id: 1, name: 'Parse Logs', description: 'Extracting key information' },
    { id: 2, name: 'Retrieve Documentation', description: 'Searching knowledge base' },
    { id: 3, name: 'Search Memory', description: 'Finding similar incidents' },
    { id: 4, name: 'Root Cause Analysis', description: 'Analyzing root cause' },
    { id: 5, name: 'Generate Recommendations', description: 'Creating action items' },
    { id: 6, name: 'Generate Report', description: 'Structuring report' },
  ];

  const handleAnalyze = async () => {
    if (!logs.trim()) {
      alert('Please enter logs to analyze');
      return;
    }

    setAnalyzing(true);
    setPipelineSteps(pipelineConfig.map(step => ({ ...step, status: 'pending', startTime: null })));
    setAnalysis(null);

    try {
      // Simulate pipeline steps animating
      for (let i = 0; i < pipelineConfig.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 800));
        setPipelineSteps(prev => {
          const updated = [...prev];
          updated[i].status = 'running';
          return updated;
        });
        await new Promise(resolve => setTimeout(resolve, 1500));
        setPipelineSteps(prev => {
          const updated = [...prev];
          updated[i].status = 'completed';
          updated[i].duration = Math.random() * 2000 + 500;
          return updated;
        });
      }

      const response = await fetch('/api/chat/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs })
      });

      if (!response.ok) throw new Error('Analysis failed');
      const result = await response.json();
      setAnalysis(result);
    } catch (error) {
      alert(`Error: ${error.message}`);
      setPipelineSteps(pipelineConfig.map(step => ({ ...step, status: 'error' })));
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setLogs(event.target.result);
      };
      reader.readAsText(file);
    }
  };

  const handlePasteLogs = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setLogs(text);
    } catch (err) {
      alert('Failed to read clipboard');
    }
  };

  const handleLoadDemo = () => {
    const demoLogs = `2026-06-26 10:15:23 ERROR [DatabaseService] Connection pool exhausted: 500 connections in use
2026-06-26 10:15:24 CRITICAL [DatabaseService] Failed to acquire connection within 30s timeout
2026-06-26 10:15:25 ERROR [OrderService] Cannot insert order - database unavailable
2026-06-26 10:15:25 ERROR [OrderService] Failed attempt 1/3 to insert order ID: ORD-98765432
2026-06-26 10:15:26 ERROR [PaymentService] Payment gateway timeout - database connection pool full
2026-06-26 10:15:27 ERROR [OrderService] Failed attempt 2/3 to insert order ID: ORD-98765432
2026-06-26 10:15:28 CRITICAL [APIGateway] 50% of requests failing - internal server errors
2026-06-26 10:15:29 ALERT [Monitoring] Alert: API error rate > 40% for 2 consecutive minutes
2026-06-26 10:15:30 ERROR [OrderService] Failed attempt 3/3 to insert order ID: ORD-98765432 - giving up
2026-06-26 10:15:31 ERROR [DatabaseService] Query queue depth: 1,250 queries waiting
2026-06-26 10:15:32 CRITICAL [DatabaseService] Long-running query detected: SELECT * FROM orders WHERE status='processing' (runtime: 45s)
2026-06-26 10:15:33 WARN [Replication] Replication lag detected: Primary 45s ahead of replica
2026-06-26 10:15:34 INFO [SystemAdmin] Incident escalated to database team`;
    setLogs(demoLogs);
  };

  const handleGenerateReport = (format) => {
    if (!analysis) {
      alert('No analysis available to export');
      return;
    }

    // Generate incident_id if not present
    const incident_id = `INC-${Date.now()}`;

    const incident = {
      incident_id: incident_id,
      timestamp: new Date().toISOString(),
      summary: analysis.summary || analysis.full_analysis || 'Incident Summary',
      severity: analysis.severity || 'Unknown',
      status: analysis.status || 'Analyzed',
      root_cause: analysis.root_cause || analysis.primary_cause || 'Unknown',
      primary_cause: analysis.primary_cause || 'Unknown',
      business_impact: analysis.business_impact || 'N/A',
      technical_impact: analysis.technical_impact || 'N/A',
      affected_services: analysis.affected_services || [],
      affected_users: analysis.affected_users || 'N/A',
      duration: analysis.duration || 'N/A',
      immediate_action: analysis.immediate_action || 'No immediate actions',
      recommendations: analysis.recommendations || [],
      confidence: analysis.confidence || 85,
      // Comprehensive analysis fields
      incident_timestamp: analysis.incident_timestamp,
      incident_summary: analysis.incident_summary || analysis.summary,
      source_analysis: analysis.source_analysis,
      rag_context: analysis.rag_context,
      memory_context: analysis.memory_context,
      root_cause_analysis: analysis.root_cause_analysis,
      events_by_severity: analysis.events_by_severity,
      timeline: analysis.timeline,
      next_steps: analysis.next_steps,
      metadata: analysis.metadata
    };

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
          format: format,
          incident_data: incident
        })
      });

      if (!genResponse.ok) {
        const error = await genResponse.json();
        throw new Error(error.detail || 'Failed to generate report');
      }

      const genData = await genResponse.json();

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

  return (
    <div className="analyze-incident">
      <div className="analyze-container">
        {!analyzing && !analysis ? (
          <div className="upload-section">
            <div className="upload-header">
              <h1>Analyze Production Incident</h1>
              <p>Upload logs or paste error messages to investigate</p>
            </div>

            <DocumentUploadZone onFileSelect={handleFileUpload} />

            <div className="logs-input-section">
              <textarea
                value={logs}
                onChange={(e) => setLogs(e.target.value)}
                placeholder="Or paste your logs here..."
                className="logs-textarea"
              />
            </div>

            <div className="action-buttons">
              <button
                onClick={handleAnalyze}
                disabled={!logs.trim()}
                className="btn-primary"
              >
                <Zap size={18} />
                Analyze Incident
              </button>
              <button
                onClick={handleLoadDemo}
                className="btn-secondary"
              >
                <RefreshCw size={18} />
                Load Demo Logs
              </button>
              <button
                onClick={handlePasteLogs}
                className="btn-secondary"
              >
                <Clipboard size={18} />
                Paste Logs
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary"
              >
                <Upload size={18} />
                Upload File
              </button>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                accept=".log,.txt,.json,.csv"
                style={{ display: 'none' }}
              />
            </div>
          </div>
        ) : null}

        {analyzing || analysis ? (
          <div className="analysis-section">
            <PipelineVisualization
              steps={pipelineSteps}
              isAnalyzing={analyzing}
            />

            {analysis && (
              <div className="results-grid">
                <div className="results-column">
                  <RootCausePanel analysis={analysis} />
                  <EvidencePanel evidence={analysis.evidence || []} />
                </div>
                <div className="results-column">
                  <MemoryPanel incidents={analysis.similar_incidents || []} />
                </div>
              </div>
            )}

            {!analyzing && (
              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleGenerateReport('pdf')}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  📄 Download PDF
                </button>
                <button
                  onClick={() => handleGenerateReport('json')}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {'{}'} Export JSON
                </button>
                <button
                  onClick={() => handleGenerateReport('csv')}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  📊 Export CSV
                </button>
                <button
                  onClick={() => {
                    setAnalyzing(false);
                    setAnalysis(null);
                    setLogs('');
                  }}
                  className="btn-secondary"
                >
                  ← Analyze Another Incident
                </button>
              </div>
            )}
          </div>
        ) : null}
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

export default AnalyzeIncident;
