import React from 'react';
import { Trash2, ShieldCheck, Database, FileText, Building2, FolderOpen, Users } from 'lucide-react';
import { api } from '../../services/api';

export const UploadedFiles = ({ documents, onDeleteSuccess }) => {
  const handleDelete = async (title, source) => {
    if (source === 'Enterprise') {
      alert("Enterprise Core policies are read-only and cannot be deleted.");
      return;
    }
    
    if (!window.confirm(`Are you sure you want to delete "${title}" from the vector database? This action cannot be undone.`)) return;

    try {
      await api.deleteDocument(title);
      if (onDeleteSuccess) onDeleteSuccess();
    } catch (err) {
      console.error(err);
      alert("Failed to delete document. Please try again.");
    }
  };

  const enterpriseCount = documents.filter(d => d.source === 'Enterprise').length;
  const uploadedCount = documents.filter(d => d.source !== 'Enterprise').length;
  const uniqueCategories = [...new Set(documents.map(d => d.category))].length;
  const totalDocs = documents.length;

  return (
    <div>
      {/* Summary Stats Bar */}
      <div className="documents-summary-bar">
        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--primary-soft)', color: 'var(--primary)', border: '1px solid var(--primary-border)' }}>
            <FileText size={18} />
          </div>
          <div className="summary-content">
            <span className="summary-label">Total Policies</span>
            <span className="summary-value">{totalDocs}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--warning-soft)', color: 'var(--warning)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
            <Building2 size={18} />
          </div>
          <div className="summary-content">
            <span className="summary-label">Enterprise</span>
            <span className="summary-value">{enterpriseCount}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--success-soft)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <FolderOpen size={18} />
          </div>
          <div className="summary-content">
            <span className="summary-label">Uploaded</span>
            <span className="summary-value">{uploadedCount}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--secondary-soft)', color: 'var(--secondary)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <Users size={18} />
          </div>
          <div className="summary-content">
            <span className="summary-label">Categories</span>
            <span className="summary-value">{uniqueCategories}</span>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="uploaded-files-container">
        {documents.length === 0 ? (
          <div className="no-docs-text">
            <FolderOpen size={28} className="empty-docs-icon" />
            <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
              No Active Policies Yet
            </div>
            <div style={{ fontSize: '11px' }}>
              Upload a policy document to start building your knowledge base.
            </div>
          </div>
        ) : (
          <>
            <div className="docs-list-header">
              <span>Document</span>
              <span>Category</span>
              <span>Version</span>
              <span>Effective Date</span>
              <span></span>
            </div>
            <div className="uploaded-files-list">
              {documents.map((doc, idx) => (
                <div key={idx} className="docs-list-row">
                  <div className="doc-main-info">
                    <div className={`doc-icon-wrapper ${doc.source === 'Enterprise' ? 'doc-icon-enterprise' : ''}`}>
                      {doc.source === 'Enterprise' ? (
                        <ShieldCheck size={16} style={{ color: 'var(--warning)' }} />
                      ) : (
                        <Database size={16} style={{ color: 'var(--info)' }} />
                      )}
                    </div>
                    <div className="doc-title-text">
                      <span className="file-row-title">{doc.title}</span>
                      <span className={`doc-source-tag ${doc.source === 'Enterprise' ? 'source-enterprise' : 'source-uploaded'}`}>
                        {doc.source === 'Enterprise' ? 'Core Policy' : 'Uploaded'}
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <span className="meta-category">{doc.category}</span>
                  </div>
                  
                  <div className="file-row-meta">
                    v{doc.version}
                  </div>
                  
                  <div className="file-row-meta">
                    {doc.date || '—'}
                  </div>
                  
                  <div>
                    {doc.source !== 'Enterprise' ? (
                      <button 
                        className="file-delete-btn"
                        onClick={() => handleDelete(doc.title, doc.source)}
                        title="Remove document from index"
                      >
                        <Trash2 size={14} />
                      </button>
                    ) : (
                      <div style={{ 
                        width: '32px', 
                        height: '32px', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        opacity: 0.3
                      }}>
                        <ShieldCheck size={14} style={{ color: 'var(--warning)' }} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
export default UploadedFiles;
