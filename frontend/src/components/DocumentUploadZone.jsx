import React, { useState } from 'react';
import { Upload } from 'lucide-react';
import '../styles/DocumentUploadZone.css';

const DocumentUploadZone = ({ onFileSelect }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect({ target: { files } });
    }
  };

  return (
    <div
      className={`upload-zone ${isDragging ? 'dragging' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <div className="upload-content">
        <div className="upload-icon">
          <Upload size={48} strokeWidth={1.5} />
        </div>
        <h3>Drag incident logs here</h3>
        <p>Supported formats: .log, .txt, .json, .csv</p>
        <p className="upload-hint">or click to select</p>
      </div>
    </div>
  );
};

export default DocumentUploadZone;
