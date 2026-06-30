import React, { useState } from 'react';
import { X, Copy, Download, Check } from 'lucide-react';
import '../styles/ReportPreviewModal.css';

const ReportPreviewModal = ({ incident, format, onClose, onDownload }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      const text = JSON.stringify(incident, null, 2);
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
    }
  };

  const handleDownload = () => {
    onDownload();
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>📋 Incident Report</h2>
            <p className="modal-subtitle">ID: {incident.incident_id}</p>
          </div>
          <button className="modal-close" onClick={onClose} title="Close (ESC)">
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Quick Stats */}
          <div className="stats-grid">
            <div className="stat-box">
              <span className="stat-label">Severity</span>
              <span className={`stat-value severity-${incident.severity?.toLowerCase() || 'low'}`}>
                {incident.severity || 'Unknown'}
              </span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Status</span>
              <span className="stat-value">{incident.status || 'Investigating'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Generated</span>
              <span className="stat-value">{new Date(incident.timestamp).toLocaleTimeString()}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Confidence</span>
              <span className="stat-value">{incident.confidence || 92}%</span>
            </div>
          </div>

          {/* Summary */}
          <div className="section">
            <h3>📌 Summary</h3>
            <p>{incident.summary || 'No summary available'}</p>
          </div>

          {/* Root Cause */}
          <div className="section">
            <h3>🎯 Root Cause</h3>
            <p>{incident.root_cause || 'Not determined'}</p>
          </div>

          {/* Affected Services */}
          {incident.affected_services && incident.affected_services.length > 0 && (
            <div className="section">
              <h3>🔌 Affected Services</h3>
              <div className="services-list">
                {incident.affected_services.map((service, idx) => (
                  <span key={idx} className="service-tag">
                    {service}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Impact */}
          <div className="impact-section">
            <div className="impact-box">
              <h4>💼 Business Impact</h4>
              <p>{incident.business_impact || 'N/A'}</p>
            </div>
            <div className="impact-box">
              <h4>🔧 Technical Impact</h4>
              <p>{incident.technical_impact || 'N/A'}</p>
            </div>
          </div>

          {/* Immediate Action */}
          <div className="section recommended">
            <h3>⚡ Immediate Action Required</h3>
            <p>{incident.immediate_action || 'No immediate actions'}</p>
          </div>

          {/* Recommendations */}
          {incident.recommendations && incident.recommendations.length > 0 && (
            <div className="section">
              <h3>✅ Recommendations</h3>
              <ul className="recommendations-list">
                {incident.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Affected Users & Duration */}
          {(incident.affected_users || incident.duration) && (
            <div className="stats-grid">
              {incident.affected_users && (
                <div className="stat-box">
                  <span className="stat-label">Affected Users</span>
                  <span className="stat-value">{incident.affected_users}</span>
                </div>
              )}
              {incident.duration && (
                <div className="stat-box">
                  <span className="stat-label">Duration</span>
                  <span className="stat-value">{incident.duration}</span>
                </div>
              )}
            </div>
          )}

          {/* Raw JSON */}
          <div className="section">
            <h3>📄 Raw Data</h3>
            <div className="json-viewer">
              <pre>{JSON.stringify(incident, null, 2)}</pre>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn-secondary" onClick={handleCopy}>
            {copied ? (
              <>
                <Check size={18} /> Copied!
              </>
            ) : (
              <>
                <Copy size={18} /> Copy to Clipboard
              </>
            )}
          </button>
          <button className="btn-primary" onClick={handleDownload}>
            <Download size={18} /> Download {format.toUpperCase()}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportPreviewModal;
