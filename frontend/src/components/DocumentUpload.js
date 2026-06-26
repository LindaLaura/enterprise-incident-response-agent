import React, { useState, useCallback } from 'react';
import './DocumentUpload.css';

function DocumentUpload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const uploadFile = useCallback(async (file) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setUploadedFiles(prev => [...prev, {
        name: data.filename,
        chunks: data.chunks,
        type: data.doc_type,
        timestamp: new Date().toLocaleTimeString()
      }]);

      onUploadSuccess();
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files);
      files.forEach(uploadFile);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const files = Array.from(e.target.files);
      files.forEach(uploadFile);
    }
  };

  return (
    <div className="document-upload">
      <div
        className={`drag-drop-zone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          onChange={handleChange}
          multiple
          accept=".txt,.pdf,.md,.docx,.log"
          disabled={uploading}
          style={{ display: 'none' }}
        />

        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">📄</div>
          <h3>Drop documents here or click to upload</h3>
          <p>Supported: .txt, .pdf, .md, .docx, .log</p>
          {uploading && <p className="uploading">Uploading...</p>}
        </label>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          <h4>Uploaded Documents</h4>
          <div className="files-list">
            {uploadedFiles.map((file, idx) => (
              <div key={idx} className="file-item">
                <span className="file-icon">✓</span>
                <div className="file-info">
                  <span className="file-name">{file.name}</span>
                  <span className="file-meta">{file.chunks} chunks • {file.type}</span>
                </div>
                <span className="file-time">{file.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;
