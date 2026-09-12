import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield, Users, FileText, Activity, Database,
  Plus, Trash2, RefreshCw, ChevronLeft, AlertTriangle,
  CheckCircle, Info, X, Tag, Lock, UserCheck, BarChart3,
  Loader2, Edit3
} from 'lucide-react';
import { api } from '../services/api';

const ROLES       = ['admin', 'hr', 'employee'];
const ROLE_COLORS = { admin:'#ef4444', hr:'#8b5cf6', employee:'#00f2fe' };
const SEV_COLORS  = { info:'var(--primary)', warning:'var(--warning)', high:'var(--danger)' };

// ── Tiny helpers ──────────────────────────────────────────────────────────────
const RoleBadge = ({ role }) => (
  <span className="rbac-role-badge" style={{ backgroundColor: ROLE_COLORS[role] || '#64748b', borderColor: ROLE_COLORS[role] || '#64748b', color: '#fff' }}>
    {role}
  </span>
);

const SevBadge = ({ sev }) => (
  <span className="audit-sev-badge" style={{ color: SEV_COLORS[sev] || 'var(--text-muted)', borderColor: (SEV_COLORS[sev] || '#64748b') + '44' }}>
    {sev}
  </span>
);

// ── Tab: Users ────────────────────────────────────────────────────────────────
const UsersTab = () => {
  const [users, setUsers]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm]             = useState({ username:'', password:'', role:'employee', name:'', email:'' });
  const [saving, setSaving]         = useState(false);
  const [msg, setMsg]               = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { const d = await api.getUsers(); setUsers(d.users || []); } catch(e){ setMsg(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true); setMsg('');
    try {
      await api.createUser(form);
      setMsg('User created successfully!');
      setShowCreate(false);
      setForm({ username:'', password:'', role:'employee', name:'', email:'' });
      load();
    } catch(e){ setMsg(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (username) => {
    if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    try { await api.deleteUser(username); load(); }
    catch(e){ setMsg(e.message); }
  };

  const handleRoleChange = async (username, role) => {
    try { await api.updateUserRole(username, role); load(); }
    catch(e){ setMsg(e.message); }
  };

  return (
    <div className="admin-tab-content">
      <div className="admin-tab-header">
        <div>
          <h3>User Management</h3>
          <p>Create accounts and assign roles to control document access.</p>
        </div>
        <button className="admin-action-btn" onClick={() => setShowCreate(v => !v)}>
          <Plus size={14} /> New User
        </button>
      </div>

      {msg && <div className="admin-msg">{msg}</div>}

      {/* Create Form */}
      {showCreate && (
        <form className="admin-create-form" onSubmit={handleCreate}>
          <h4>Create New User</h4>
          <div className="admin-form-grid">
            <input className="admin-input" placeholder="Username *" value={form.username} onChange={e=>setForm(f=>({...f,username:e.target.value}))} required />
            <input className="admin-input" type="password" placeholder="Password *" value={form.password} onChange={e=>setForm(f=>({...f,password:e.target.value}))} required />
            <input className="admin-input" placeholder="Full Name *" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} required />
            <input className="admin-input" placeholder="Email (optional)" value={form.email} onChange={e=>setForm(f=>({...f,email:e.target.value}))} />
            <select className="admin-select" value={form.role} onChange={e=>setForm(f=>({...f,role:e.target.value}))}>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="admin-form-actions">
            <button type="submit" className="admin-action-btn" disabled={saving}>
              {saving ? <Loader2 size={13} className="spinning" /> : <UserCheck size={13} />}
              {saving ? 'Creating...' : 'Create User'}
            </button>
            <button type="button" className="admin-cancel-btn" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        </form>
      )}

      {/* Users Table */}
      {loading ? (
        <div className="admin-loading"><Loader2 size={20} className="spinning" /> Loading users...</div>
      ) : (
        <div className="admin-users-list">
          <div className="admin-list-actions">
            <div className="admin-search-wrapper">
              <input type="text" className="admin-input admin-search" placeholder="Filter accounts..." />
            </div>
          </div>
          {users.map(u => {
            const initials = u.name ? u.name.substring(0, 2).toUpperCase() : 'U';
            const roleColor = ROLE_COLORS[u.role] || '#64748b';
            
            return (
              <div key={u.id} className="admin-user-card">
                <div className="admin-user-card-left">
                  <div className="admin-user-avatar" style={{ backgroundColor: roleColor }}>
                    {initials}
                  </div>
                  <div className="admin-user-details">
                    <div className="admin-user-name-row">
                      <span className="admin-row-title">{u.name}</span>
                      <RoleBadge role={u.role} />
                    </div>
                    <div className="admin-row-sub email-sub">{u.email || u.username}</div>
                    <div className="admin-row-sub date-sub">
                      Created: {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                    </div>
                  </div>
                </div>
                
                <div className="admin-user-card-right">
                  <div className="admin-access-tier">
                    <label>ACCESS TIER</label>
                    <div className="admin-role-dropdown-wrapper">
                      <select
                        className="admin-role-select-modern"
                        value={u.role}
                        style={{ color: roleColor, borderColor: roleColor + '55' }}
                        onChange={e => handleRoleChange(u.username, e.target.value)}
                      >
                        {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </div>
                  </div>
                  {u.role !== 'admin' && (
                    <button className="admin-del-btn" onClick={() => handleDelete(u.username)}>
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ── Tab: Documents ─────────────────────────────────────────────────────────────
const DocumentsTab = () => {
  const [docs, setDocs]           = useState([]);
  const [loading, setLoading]     = useState(true);
  const [editing, setEditing]     = useState(null);  // doc title being edited
  const [editRoles, setEditRoles] = useState([]);
  const [editTags, setEditTags]   = useState('');
  const [msg, setMsg]             = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      // Admin sees all docs regardless of role
      const d = await api.getDocuments();
      setDocs(d);
    } catch(e){ setMsg(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const startEdit = (doc) => {
    setEditing(doc.title);
    setEditRoles(doc.allowed_roles || []);
    setEditTags((doc.tags || []).join(', '));
  };

  const saveEdit = async () => {
    try {
      const tagArr  = editTags.split(',').map(t=>t.trim()).filter(Boolean);
      await api.updateDocRoles(editing, editRoles);
      await api.updateDocTags(editing, tagArr);
      setMsg('Document updated!');
      setEditing(null);
      load();
    } catch(e){ setMsg(e.message); }
  };

  const toggleRole = (role) => {
    setEditRoles(prev => prev.includes(role) ? prev.filter(r=>r!==role) : [...prev, role]);
  };

  return (
    <div className="admin-tab-content">
      <div className="admin-tab-header">
        <div>
          <h3>Document Access Control</h3>
          <p>Assign tags and role restrictions to policy documents.</p>
        </div>
        <button className="admin-action-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      {msg && <div className="admin-msg">{msg}</div>}

      {loading ? (
        <div className="admin-loading"><Loader2 size={20} className="spinning" /> Loading...</div>
      ) : (
        <div className="admin-table-wrap">
          <div className="admin-table-head admin-doc-cols">
            <span>Document</span><span>Category</span><span>Tags</span><span>Access</span><span></span>
          </div>
          {docs.map((doc, i) => (
            <React.Fragment key={i}>
              <div className="admin-table-row admin-doc-cols">
                <div>
                  <div className="admin-row-title">{doc.title}</div>
                  <div className="admin-row-sub">{doc.source} · v{doc.version}</div>
                </div>
                <div><span className="admin-cat-chip">{doc.category}</span></div>
                <div className="admin-tags-cell">
                  {(doc.tags||[]).length > 0
                    ? doc.tags.map((t,ti) => <span key={ti} className="admin-tag-chip">{t}</span>)
                    : <span className="admin-row-sub">—</span>
                  }
                </div>
                <div className="admin-roles-cell">
                  {(doc.allowed_roles||[]).length === 0
                    ? <span className="admin-public-badge">Public</span>
                    : doc.allowed_roles.map(r => <RoleBadge key={r} role={r} />)
                  }
                </div>
                <div>
                  <button className="admin-edit-btn" onClick={() => editing === doc.title ? setEditing(null) : startEdit(doc)}>
                    <Edit3 size={13} />
                  </button>
                </div>
              </div>

              {/* Inline edit panel */}
              {editing === doc.title && (
                <div className="admin-inline-edit">
                  <div className="admin-edit-section">
                    <label><Tag size={12} /> Tags (comma-separated)</label>
                    <input className="admin-input" value={editTags} onChange={e=>setEditTags(e.target.value)} placeholder="e.g. HR, Salary, Benefits" />
                  </div>
                  <div className="admin-edit-section">
                    <label><Lock size={12} /> Role Restrictions (empty = public)</label>
                    <div className="admin-roles-toggle">
                      {ROLES.filter(r=>r!=='admin').map(r => (
                        <button
                          key={r}
                          type="button"
                          className={`admin-role-toggle-btn ${editRoles.includes(r) ? 'active' : ''}`}
                          style={{ '--role-color': ROLE_COLORS[r] }}
                          onClick={() => toggleRole(r)}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                    {editRoles.length > 0 && (
                      <p className="admin-role-hint">⚠ This doc will be hidden from users not in: {editRoles.join(', ')}</p>
                    )}
                  </div>
                  <div className="admin-form-actions">
                    <button className="admin-action-btn" onClick={saveEdit}><CheckCircle size={13} /> Save</button>
                    <button className="admin-cancel-btn" onClick={() => setEditing(null)}>Cancel</button>
                  </div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Tab: Audit Log ─────────────────────────────────────────────────────────────
const AuditTab = () => {
  const [entries, setEntries]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [filter, setFilter]     = useState('all');
  const [clearing, setClearing] = useState(false);
  const [msg, setMsg]           = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api.getAuditLog(200, filter === 'all' ? null : filter);
      setEntries(d.entries || []);
    } catch(e){ setMsg(e.message); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const handleClear = async () => {
    if (!window.confirm('Clear entire audit log? This cannot be undone.')) return;
    setClearing(true);
    try { await api.clearAuditLog(); load(); }
    catch(e){ setMsg(e.message); }
    finally { setClearing(false); }
  };

  return (
    <div className="admin-tab-content">
      <div className="admin-tab-header">
        <div>
          <h3>Compliance Audit Log</h3>
          <p>All system events — logins, queries, escalations, document changes.</p>
        </div>
        <div style={{ display:'flex', gap:'8px' }}>
          <select className="admin-select" value={filter} onChange={e=>setFilter(e.target.value)}>
            <option value="all">All Severity</option>
            <option value="info">Info Only</option>
            <option value="warning">Warnings</option>
            <option value="high">High Risk</option>
          </select>
          <button className="admin-action-btn" onClick={load}><RefreshCw size={14} /></button>
          <button className="admin-danger-btn" onClick={handleClear} disabled={clearing}>
            {clearing ? <Loader2 size={13} className="spinning" /> : <Trash2 size={13} />}
            Clear Log
          </button>
        </div>
      </div>

      {msg && <div className="admin-msg">{msg}</div>}

      {loading ? (
        <div className="admin-loading"><Loader2 size={20} className="spinning" /> Loading audit entries...</div>
      ) : (
        <div className="audit-log-scroll">
          {entries.length === 0 ? (
            <div className="admin-empty">No audit log entries found.</div>
          ) : entries.map(e => (
            <div key={e.id} className={`audit-entry audit-sev-${e.severity}`}>
              <div className="audit-entry-left">
                <SevBadge sev={e.severity} />
                <div>
                  <div className="audit-action">{e.action}</div>
                  <div className="audit-details">{e.details}</div>
                </div>
              </div>
              <div className="audit-entry-right">
                <RoleBadge role={e.role} />
                <span className="audit-user">{e.user}</span>
                <span className="audit-time">{new Date(e.timestamp).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Tab: Stats ────────────────────────────────────────────────────────────────
const StatsTab = () => {
  const [stats, setStats]   = useState(null);
  const [loading, setLoad]  = useState(true);
  const [msg, setMsg]       = useState('');

  const load = useCallback(async () => {
    setLoad(true);
    try { const d = await api.getAdminStats(); setStats(d); }
    catch(e){ setMsg(e.message); }
    finally { setLoad(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="admin-loading"><Loader2 size={20} className="spinning" /> Loading stats...</div>;
  if (!stats) return <div className="admin-empty">{msg || 'No stats available.'}</div>;

  return (
    <div className="admin-tab-content">
      <div className="admin-tab-header">
        <div><h3>Vector Database Health</h3><p>Real-time stats on indexed documents and chunks.</p></div>
        <button className="admin-action-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-icon" style={{ background:'rgba(0,242,254,0.1)', color:'var(--primary)' }}><Database size={20} /></div>
          <div className="stat-card-value">{stats.total_chunks}</div>
          <div className="stat-card-label">Total Chunks Indexed</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{ background:'rgba(245,158,11,0.1)', color:'var(--warning)' }}><FileText size={20} /></div>
          <div className="stat-card-value">{stats.enterprise.document_count}</div>
          <div className="stat-card-label">Enterprise Documents</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{ background:'rgba(16,185,129,0.1)', color:'var(--success)' }}><FileText size={20} /></div>
          <div className="stat-card-value">{stats.uploaded.document_count}</div>
          <div className="stat-card-label">Uploaded Documents</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon" style={{ background:'rgba(239,68,68,0.1)', color:'var(--danger)' }}><Lock size={20} /></div>
          <div className="stat-card-value">{stats.role_restricted_docs.length}</div>
          <div className="stat-card-label">Role-Restricted Docs</div>
        </div>
      </div>

      <div className="stats-two-col">
        {/* Enterprise Store */}
        <div className="stats-section-card">
          <h4><Shield size={14} style={{color:'var(--warning)'}} /> Enterprise Index</h4>
          <div className="stats-detail-row"><span>Chunks</span><strong>{stats.enterprise.chunk_count}</strong></div>
          <div className="stats-detail-row"><span>Categories</span><strong>{stats.enterprise.categories.join(', ') || '—'}</strong></div>
          <div className="stats-doc-list">
            {stats.enterprise.documents.map((d,i) => <div key={i} className="stats-doc-item">{d}</div>)}
          </div>
        </div>

        {/* Uploaded Store */}
        <div className="stats-section-card">
          <h4><Database size={14} style={{color:'var(--info)'}} /> Uploaded Index</h4>
          <div className="stats-detail-row"><span>Chunks</span><strong>{stats.uploaded.chunk_count}</strong></div>
          <div className="stats-detail-row"><span>Categories</span><strong>{stats.uploaded.categories.join(', ') || '—'}</strong></div>
          {stats.uploaded.documents.length === 0
            ? <div className="admin-empty" style={{marginTop:'12px'}}>No uploaded documents yet.</div>
            : <div className="stats-doc-list">
                {stats.uploaded.documents.map((d,i) => <div key={i} className="stats-doc-item">{d}</div>)}
              </div>
          }
        </div>
      </div>

      {/* Role-restricted docs */}
      {stats.role_restricted_docs.length > 0 && (
        <div className="stats-section-card" style={{ marginTop:'16px' }}>
          <h4><Lock size={14} style={{color:'var(--danger)'}} /> Role-Restricted Documents</h4>
          {stats.role_restricted_docs.map((d,i) => (
            <div key={i} className="stats-restricted-row">
              <span>{d.title}</span>
              <div>{d.allowed_roles.map(r => <RoleBadge key={r} role={r} />)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main Admin Panel ──────────────────────────────────────────────────────────
export const AdminPanel = ({ currentUser, onBack }) => {
  const [activeTab, setActiveTab] = useState('users');

  const TABS = [
    { id:'users',     label:'Users',      icon: Users },
    { id:'documents', label:'Documents',  icon: FileText },
    { id:'audit',     label:'Audit Log',  icon: Activity },
    { id:'stats',     label:'DB Stats',   icon: BarChart3 },
  ];

  return (
    <div className="admin-panel-root">
      {/* Top Bar */}
      <div className="admin-topbar">
        <div className="admin-topbar-left">
          <button className="admin-back-btn" onClick={onBack}>
            <ChevronLeft size={16} /> Back to Chat
          </button>
          <div className="admin-topbar-brand">
            <Shield size={18} style={{ color:'var(--danger)' }} />
            <span>Admin Panel</span>
          </div>
        </div>
        <div className="admin-topbar-user">
          <span className="admin-user-chip">
            <span className="admin-user-dot" />
            {currentUser?.name || currentUser?.username}
          </span>
          <RoleBadge role={currentUser?.role} />
        </div>
      </div>

      <div className="admin-body">
        {/* Sidebar nav */}
        <nav className="admin-sidenav">
          {TABS.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={`admin-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Content */}
        <main className="admin-main">
          {activeTab === 'users'     && <UsersTab />}
          {activeTab === 'documents' && <DocumentsTab />}
          {activeTab === 'audit'     && <AuditTab />}
          {activeTab === 'stats'     && <StatsTab />}
        </main>
      </div>
    </div>
  );
};

export default AdminPanel;
