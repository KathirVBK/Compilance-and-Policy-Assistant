import React, { useState } from 'react';
import { UploadCloud, Loader2, FileText, Info } from 'lucide-react';
import { api } from '../../services/api';

export const UploadPDF = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [version, setVersion] = useState('1.0');
  const [date, setDate] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
      if (!title) {
        const name = e.target.files[0].name.split('.')[0];
        setTitle(name.replace(/[-_]/g, ' '));
      }
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('category', category);
    formData.append('version', version);
    formData.append('date', date);
    formData.append('author', author);

    try {
      await api.uploadDocument(formData);
      alert('✅ Policy document processed and indexed successfully!');
      setFile(null);
      setTitle('');
      setCategory('');
      setVersion('1.0');
      setDate('');
      setAuthor('');
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error(err);
      alert(`❌ Upload failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const categorySuggestions = ['HR Policy', 'Finance', 'Operations', 'Compliance', 'IT Security', 'Benefits', 'Health & Safety'];

  return (
    <form className="upload-pdf-form" onSubmit={handleFormSubmit}>
      {/* Document Metadata Section */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box icon-info">
            <Info size={16} />
          </div>
          <span className="section-title">Document Information</span>
        </div>
        
        <div className="upload-form-grid">
          <div className="upload-group full-width">
            <label>Document Title <span className="label-required">*</span></label>
            <input 
              type="text" 
              placeholder="e.g. Employee Leave Policy 2025" 
              value={title} 
              onChange={(e) => setTitle(e.target.value)} 
              required 
            />
          </div>
          
          <div className="upload-group">
            <label>Category <span className="label-required">*</span></label>
            <input 
              type="text" 
              list="category-suggestions"
              placeholder="e.g. HR, Finance, Compliance" 
              value={category} 
              onChange={(e) => setCategory(e.target.value)} 
              required 
            />
            <datalist id="category-suggestions">
              {categorySuggestions.map((c, i) => (
                <option key={i} value={c} />
              ))}
            </datalist>
          </div>
          
          <div className="upload-group">
            <label>Version <span className="label-required">*</span></label>
            <input 
              type="text" 
              placeholder="e.g. 2.1, 1.0" 
              value={version} 
              onChange={(e) => setVersion(e.target.value)} 
              required 
            />
          </div>
          
          <div className="upload-group">
            <label>Effective Date <span className="label-required">*</span></label>
            <input 
              type="date" 
              value={date} 
              onChange={(e) => setDate(e.target.value)} 
              required 
            />
          </div>
          
          <div className="upload-group full-width">
            <label>Issuing Office / Department <span className="label-required">*</span></label>
            <input 
              type="text" 
              placeholder="e.g. Human Resources Department, Legal Operations" 
              value={author} 
              onChange={(e) => setAuthor(e.target.value)} 
              required 
            />
          </div>
        </div>
      </div>

      {/* File Upload Section */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box icon-primary">
            <FileText size={16} />
          </div>
          <span className="section-title">Upload Document File</span>
        </div>
        
        <div className="upload-form-grid">
          <div className="upload-group full-width">
            <label>Select Policy File <span className="label-required">*</span></label>
            <input 
              type="file" 
              accept=".pdf,.txt,.md,.json" 
              onChange={handleFileChange} 
              required 
            />
          </div>
        </div>
        
        {file && (
          <div style={{
            marginTop: '16px',
            padding: '12px 16px',
            background: 'var(--primary-soft)',
            border: '1px solid var(--primary-border)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)'
            }}>
              <FileText size={16} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                {file.name}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {(file.size / 1024).toFixed(1)} KB • Ready for processing
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Form Actions */}
      <div className="form-actions-row">
        <button 
          type="submit" 
          className="upload-submit-btn-react"
          disabled={loading || !file}
        >
          {loading ? (
            <>
              <Loader2 className="spinning" size={15} />
              <span>Parsing & Indexing Document...</span>
            </>
          ) : (
            <>
              <UploadCloud size={15} />
              <span>Upload & Index to Vector Database</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
export default UploadPDF;
