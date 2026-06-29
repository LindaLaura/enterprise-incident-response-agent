import React, { useState, useRef } from 'react';
import { Zap, Clipboard, RefreshCw, Upload } from 'lucide-react';
import PipelineVisualization from '../components/PipelineVisualization';
import DocumentUploadZone from '../components/DocumentUploadZone';
import EvidencePanel from '../components/EvidencePanel';
import MemoryPanel from '../components/MemoryPanel';
import RootCausePanel from '../components/RootCausePanel';
import '../styles/AnalyzeIncident.css';

const AnalyzeIncident = ({ wsRef }) => {
  const [logs, setLogs] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [analysis, setAnalysis] = useState(null);
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
              <button
                onClick={() => {
                  setAnalyzing(false);
                  setAnalysis(null);
                  setLogs('');
                }}
                className="btn-reset"
              >
                ← Analyze Another Incident
              </button>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default AnalyzeIncident;
