import React from "react";

export default function Sidebar({ documents, onFileUpload, uploading }) {
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="sidebar">
      <h2>Documents</h2>
      <div className="upload-section">
        <label htmlFor="file-upload" className="upload-btn">
          {uploading ? "Uploading..." : "+ Upload File"}
        </label>
        <input
          id="file-upload"
          type="file"
          className="file-input"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileChange}
          disabled={uploading}
        />
      </div>

      <div className="document-list">
        <h3>Uploaded Files</h3>
        {documents.length === 0 ? (
          <p style={{ fontSize: "0.85rem", color: "#94a3b8" }}>No files uploaded yet.</p>
        ) : (
          documents.map((doc, idx) => (
            <div key={idx} className="doc-item">
              <span className="doc-icon">📄</span>
              <span>{doc}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}