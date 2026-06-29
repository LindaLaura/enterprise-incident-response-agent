import React, { useEffect, useState } from 'react';
import '../styles/PipelineVisualization.css';

const PipelineVisualization = ({ steps, isAnalyzing }) => {
  const [animatedSteps, setAnimatedSteps] = useState(steps);

  useEffect(() => {
    setAnimatedSteps(steps);
  }, [steps]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'running':
        return '⟳';
      case 'error':
        return '✕';
      case 'pending':
        return '◯';
      default:
        return '◯';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'status-completed';
      case 'running':
        return 'status-running';
      case 'error':
        return 'status-error';
      case 'pending':
        return 'status-pending';
      default:
        return 'status-pending';
    }
  };

  return (
    <div className="pipeline-visualization">
      <div className="pipeline-header">
        <h2>AI Investigation Pipeline</h2>
        <p>Real-time incident analysis workflow</p>
      </div>

      <div className="pipeline-steps">
        {animatedSteps.map((step, index) => (
          <div key={step.id} className="pipeline-step">
            <div className={`step-indicator ${getStatusClass(step.status)}`}>
              <div className="step-number">
                <span className={`step-icon ${step.status === 'running' ? 'animate-spin' : ''}`}>
                  {getStatusIcon(step.status)}
                </span>
              </div>
              <div className="step-content">
                <div className="step-title">{step.name}</div>
                <div className="step-description">{step.description}</div>
                {step.duration && (
                  <div className="step-duration">
                    {(step.duration / 1000).toFixed(2)}s
                  </div>
                )}
              </div>
            </div>

            {index < animatedSteps.length - 1 && (
              <div className={`step-connector ${getStatusClass(animatedSteps[index + 1]?.status)}`}>
                <div className="connector-line"></div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="pipeline-footer">
        {isAnalyzing ? (
          <div className="analyzing-status">
            <span className="pulse-dot"></span>
            Analyzing incident...
          </div>
        ) : (
          <div className="complete-status">
            ✓ Analysis complete
          </div>
        )}
      </div>
    </div>
  );
};

export default PipelineVisualization;
