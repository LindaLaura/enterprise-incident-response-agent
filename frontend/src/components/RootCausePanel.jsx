import React from 'react';
import '../styles/RootCausePanel.css';

const RootCausePanel = ({ analysis = null }) => {
  if (!analysis) {
    return (
      <div className="root-cause-panel">
        <div className="panel-header">
          <h3>🔍 Root Cause Analysis</h3>
        </div>
        <div className="no-data">
          <p>Waiting for analysis...</p>
        </div>
      </div>
    );
  }

  const confidence = analysis.confidence || 92;
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (confidence / 100) * circumference;

  return (
    <div className="root-cause-panel">
      <div className="panel-header">
        <h3>🔍 Root Cause Analysis</h3>
      </div>

      <div className="analysis-content">
        <div className="confidence-section">
          <svg className="confidence-ring" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="45"
              fill="none"
              stroke="rgba(148, 113, 255, 0.1)"
              strokeWidth="8"
            />
            <circle
              cx="60"
              cy="60"
              r="45"
              fill="none"
              stroke="url(#confidenceGradient)"
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
            />
            <defs>
              <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#9471ff" />
                <stop offset="100%" stopColor="#7c3aed" />
              </linearGradient>
            </defs>
            <text x="60" y="70" textAnchor="middle" className="confidence-text">
              {confidence}%
            </text>
          </svg>
          <p className="confidence-label">Confidence</p>
        </div>

        <div className="details-grid">
          <div className="detail-box">
            <div className="box-title">🚨 Severity</div>
            <div className="box-value severity-high">
              {analysis.severity || 'Critical'}
            </div>
          </div>

          <div className="detail-box">
            <div className="box-title">⚙️ Status</div>
            <div className="box-value">
              {analysis.status || 'Investigating'}
            </div>
          </div>

          <div className="detail-box">
            <div className="box-title">👥 Affected Users</div>
            <div className="box-value">
              {analysis.affected_users || 'Unknown'}
            </div>
          </div>

          <div className="detail-box">
            <div className="box-title">⏱️ Duration</div>
            <div className="box-value">
              {analysis.duration || '15 min'}
            </div>
          </div>
        </div>

        <div className="analysis-sections">
          {analysis.primary_cause && (
            <div className="analysis-section">
              <div className="section-title">🎯 Primary Cause</div>
              <div className="section-content">{analysis.primary_cause}</div>
            </div>
          )}

          {analysis.business_impact && (
            <div className="analysis-section">
              <div className="section-title">💼 Business Impact</div>
              <div className="section-content">{analysis.business_impact}</div>
            </div>
          )}

          {analysis.technical_impact && (
            <div className="analysis-section">
              <div className="section-title">🔧 Technical Impact</div>
              <div className="section-content">{analysis.technical_impact}</div>
            </div>
          )}

          {analysis.affected_services && (
            <div className="analysis-section">
              <div className="section-title">🔌 Affected Services</div>
              <div className="section-content">
                {Array.isArray(analysis.affected_services)
                  ? analysis.affected_services.join(', ')
                  : analysis.affected_services}
              </div>
            </div>
          )}

          {analysis.immediate_action && (
            <div className="analysis-section recommended">
              <div className="section-title">⚡ Recommended Immediate Action</div>
              <div className="section-content">{analysis.immediate_action}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RootCausePanel;
