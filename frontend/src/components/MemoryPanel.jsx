import React, { useState } from 'react';
import '../styles/MemoryPanel.css';

const MemoryPanel = ({ incidents = [] }) => {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!incidents || incidents.length === 0) {
    return (
      <div className="memory-panel">
        <div className="panel-header">
          <h3>🧠 Similar Incidents</h3>
          <span className="panel-badge">0 found</span>
        </div>
        <div className="no-data">
          <p>No similar incidents in memory</p>
        </div>
      </div>
    );
  }

  return (
    <div className="memory-panel">
      <div className="panel-header">
        <h3>🧠 Similar Incidents</h3>
        <span className="panel-badge">{incidents.length} found</span>
      </div>

      <div className="incidents-list">
        {incidents.map((incident, index) => (
          <div key={index} className="incident-item">
            <div
              className="incident-header"
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
            >
              <div className="incident-info">
                <div className="incident-id">
                  Incident #{incident.id || `${1000 + index}`}
                </div>
                <div className="incident-meta">
                  <span className="similarity-badge">
                    {incident.similarity || incident.score || 88}% Similar
                  </span>
                  {incident.resolution_time && (
                    <span className="resolution-time">
                      Resolved in {incident.resolution_time}
                    </span>
                  )}
                </div>
              </div>
              <button className="expand-btn">
                {expandedIndex === index ? '▼' : '▶'}
              </button>
            </div>

            {expandedIndex === index && (
              <div className="incident-details">
                <div className="detail-section">
                  <div className="detail-label">Summary</div>
                  <div className="detail-value">
                    {incident.summary || incident.description || 'No summary available'}
                  </div>
                </div>

                {incident.root_cause && (
                  <div className="detail-section">
                    <div className="detail-label">Root Cause</div>
                    <div className="detail-value">{incident.root_cause}</div>
                  </div>
                )}

                {incident.resolution && (
                  <div className="detail-section">
                    <div className="detail-label">Resolution</div>
                    <div className="detail-value">{incident.resolution}</div>
                  </div>
                )}

                {incident.timestamp && (
                  <div className="detail-section">
                    <div className="detail-label">Date</div>
                    <div className="detail-value">
                      {new Date(incident.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="memory-stats">
        <div className="stat">
          <span className="stat-label">Average Similarity</span>
          <span className="stat-value">
            {Math.round(
              incidents.reduce((sum, inc) => sum + (inc.similarity || inc.score || 85), 0) /
                incidents.length
            )}%
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Incidents Analyzed</span>
          <span className="stat-value">{incidents.length}</span>
        </div>
      </div>
    </div>
  );
};

export default MemoryPanel;
