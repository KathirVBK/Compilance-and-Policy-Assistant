import React, { useState } from 'react';
import { UploadCloud, Loader2, FileText, Info, Tag, Lock } from 'lucide-react';
import { api } from '../../services/api';
import { Loader } from '../UI/Loader';

const ROLE_OPTIONS = [
  { value: 'hr',         label: 'HR Only' },
  { value: 'finance',    label: 'Finance Only' },
  { value: 'legal',      label: 'Legal Only' },
  { value: 'operations', label: 'Operations Only' },
  { value: 'admin',      label: 'Admin Only' },
];

const TAG_SUGGESTIONS = ['HR Policy', 'Finance', 'Operations', 'Compliance', 'IT Security', 'Benefits', 'Health & Safety', 'Legal', 'Payroll', 'Salary'];

export const UploadPDF = ({ onUploadSuccess }) => {
  const [file, setFile]           = useState(null);
  const [title, setTitle]         = useState('');
  const [category, setCategory]   = useState('');
  const [version, setVersion]     = useState('1.0');
  const [date, setDate]           = useState('');
  const [author, setAuthor]       = useState('');
  const [tags, setTags]           = useState([]);
  const [allowedRoles, setAllowedRoles] = useState([]);  // empty = public
  const [tagInput, setTagInput]   = useState('');
  const [loading, setLoading]     = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
      if (!title) {
        const name = e.target.files[0].name.split('.')[0];
        setTitle(name.replace(/[-_]/g, ' '));
      }
    }
  };

  const addTag = (tag) => {
    const clean = tag.trim();
    if (clean && !tags.includes(clean)) setTags(prev => [...prev, clean]);
    setTagInput('');
  };

  const removeTag = (tag) => setTags(prev => prev.filter(t => t !== tag));

  const toggleRole = (role) => {
    setAllowedRoles(prev => prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role]);
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
    formData.append('tags', tags.join(','));
    formData.append('allowed_roles', allowedRoles.join(','));

    try {
      await api.uploadDocument(formData);
      alert('Policy document processed successfully! The agent now has access to this document.');
      setFile(null); setTitle(''); setCategory(''); setVersion('1.0');
      setDate(''); setAuthor(''); setTags([]); setAllowedRoles([]);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error(err);
      alert(`Upload failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const categorySuggestions = ['HR Policy', 'Finance', 'Operations', 'Compliance', 'IT Security', 'Benefits', 'Health & Safety'];

  return (
    <form className="upload-pdf-form" onSubmit={handleFormSubmit}>
      {/* Document Metadata */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box icon-info"><Info size={16} /></div>
          <span className="section-title">Document Information</span>
        </div>
        <div className="upload-form-grid">
          <div className="upload-group full-width">
            <label>Document Title <span className="label-required">*</span></label>
            <input type="text" placeholder="e.g. Employee Leave Policy 2025" value={title} onChange={e => setTitle(e.target.value)} required />
          </div>
          <div className="upload-group">
            <label>Category <span className="label-required">*</span></label>
            <input type="text" list="category-suggestions" placeholder="e.g. HR, Finance, Compliance" value={category} onChange={e => setCategory(e.target.value)} required />
            <datalist id="category-suggestions">
              {categorySuggestions.map((c, i) => <option key={i} value={c} />)}
            </datalist>
          </div>
          <div className="upload-group">
            <label>Version <span className="label-required">*</span></label>
            <input type="text" placeholder="e.g. 2.1, 1.0" value={version} onChange={e => setVersion(e.target.value)} required />
          </div>
          <div className="upload-group">
            <label>Effective Date <span className="label-required">*</span></label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} required />
          </div>
          <div className="upload-group full-width">
            <label>Issuing Office / Department <span className="label-required">*</span></label>
            <input type="text" placeholder="e.g. Human Resources Department" value={author} onChange={e => setAuthor(e.target.value)} required />
          </div>
        </div>
      </div>

      {/* Tags Section */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box" style={{ background:'rgba(139,92,246,0.15)', color:'#8b5cf6', border:'1px solid rgba(139,92,246,0.25)' }}>
            <Tag size={16} />
          </div>
          <span className="section-title">Document Tags</span>
        </div>
        <p style={{ fontSize:'11px', color:'var(--text-muted)', marginBottom:'10px' }}>
          Tags help users filter and discover documents by topic.
        </p>
        <div className="tag-input-row">
          <input
            type="text"
            className="tag-text-input"
            placeholder="Add a tag and press Enter..."
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag(tagInput); } }}
          />
          <button type="button" className="tag-add-btn" onClick={() => addTag(tagInput)}>+ Add</button>
        </div>
        {/* Quick add suggestions */}
        <div className="tag-suggestions-row">
          {TAG_SUGGESTIONS.filter(s => !tags.includes(s)).slice(0, 6).map((s, i) => (
            <button key={i} type="button" className="tag-suggest-chip" onClick={() => addTag(s)}>{s}</button>
          ))}
        </div>
        {tags.length > 0 && (
          <div className="tag-active-row">
            {tags.map((t, i) => (
              <span key={i} className="tag-active-chip">
                {t}
                <button type="button" onClick={() => removeTag(t)} style={{ background:'none', border:'none', color:'inherit', cursor:'pointer', padding:'0 0 0 4px' }}>×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* RBAC Role Restriction */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box" style={{ background:'rgba(239,68,68,0.1)', color:'var(--danger)', border:'1px solid rgba(239,68,68,0.2)' }}>
            <Lock size={16} />
          </div>
          <span className="section-title">Access Restriction (Optional)</span>
        </div>
        <p style={{ fontSize:'11px', color:'var(--text-muted)', marginBottom:'12px' }}>
          Leave unchecked to make this document visible to all users. Check roles to restrict access.
        </p>
        <div className="role-toggle-grid">
          {ROLE_OPTIONS.map(({ value, label }) => (
            <label key={value} className={`role-toggle-label ${allowedRoles.includes(value) ? 'active' : ''}`}>
              <input
                type="checkbox"
                checked={allowedRoles.includes(value)}
                onChange={() => toggleRole(value)}
                style={{ display:'none' }}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
        {allowedRoles.length > 0 && (
          <div className="rbac-warning-note">
            ⚠ This document will only be visible to: {allowedRoles.join(', ')} and admins.
          </div>
        )}
      </div>

      {/* File Upload */}
      <div className="form-section-card">
        <div className="form-section-header">
          <div className="section-icon-box icon-primary"><FileText size={16} /></div>
          <span className="section-title">Upload Document File</span>
        </div>
        <div className="upload-form-grid">
          <div className="upload-group full-width">
            <label>Select Policy File <span className="label-required">*</span></label>
            <input type="file" accept=".pdf,.txt,.md,.json" onChange={handleFileChange} required />
          </div>
        </div>
        {file && (
          <div style={{ marginTop:'16px', padding:'12px 16px', background:'var(--primary-soft)', border:'1px solid var(--primary-border)', borderRadius:'var(--radius-md)', display:'flex', alignItems:'center', gap:'12px' }}>
            <div style={{ width:'36px', height:'36px', background:'var(--bg-card)', border:'1px solid var(--border-color)', borderRadius:'var(--radius-sm)', display:'flex', alignItems:'center', justifyContent:'center', color:'var(--primary)' }}>
              <FileText size={16} />
            </div>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:'13px', fontWeight:600, color:'var(--text-main)' }}>{file.name}</div>
              <div style={{ fontSize:'11px', color:'var(--text-muted)' }}>{(file.size/1024).toFixed(1)} KB · Ready for processing</div>
            </div>
          </div>
        )}
      </div>

      {/* Submit */}
      <div className="form-actions-row">
        <button type="submit" className="upload-submit-btn-react" disabled={loading || !file}>
          {loading ? (
            <><Loader2 className="spinning" size={15} /><span>Parsing & Indexing Document...</span></>
          ) : (
            <><UploadCloud size={15} /><span>Upload & Index to Vector Database</span></>
          )}
        </button>
      </div>

      {loading && <Loader message="Parsing PDF & Extracting Knowledge for the Agent..." />}
    </form>
  );
};

export default UploadPDF;
