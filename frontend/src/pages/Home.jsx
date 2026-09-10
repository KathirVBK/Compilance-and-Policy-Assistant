import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Plus, FolderOpen, History, PlusCircle,
  Trash2, Clock, Bot, FileText, X, ShieldCheck,
  MessageCircle, LogOut, Shield, Tag, ChevronDown
} from 'lucide-react';
import { api } from '../services/api';
import { ChatWindow }    from '../components/Chat/ChatWindow';
import { ChatInput }     from '../components/Chat/ChatInput';
import { UploadPDF }     from '../components/Upload/UploadPDF';
import { UploadedFiles } from '../components/Upload/UploadedFiles';
import { Loader }        from '../components/UI/Loader';

const ROLE_COLORS = {
  admin:'#ef4444', hr:'#8b5cf6', finance:'#f59e0b',
  legal:'#3b82f6', operations:'#10b981', employee:'#00f2fe'
};

export const Home = ({ currentUser, onLogout, onGoAdmin }) => {
  const [sessionId, setSessionId]         = useState(() => 'sess-' + Math.random().toString(36).substring(2, 10));
  const [messages, setMessages]           = useState([]);
  const [_models, setModels]              = useState([]);
  const [_selectedModel]                  = useState('gemini-2.5-flash');
  const [documents, setDocuments]         = useState([]);
  const [loading, setLoading]             = useState(false);
  const [showUpload, setShowUpload]       = useState(false);
  const [showDocs, setShowDocs]           = useState(false);
  const [targetDocument, setTargetDocument] = useState('All Policies');
  const [categories, setCategories]       = useState([]);
  const [activeCategoryFilter, setActiveCategoryFilter] = useState(null);

  const [savedSessions, setSavedSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('compliance_chat_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  useEffect(() => { loadInitialData(); }, []);

  const loadInitialData = async () => {
    try {
      const modelData = await api.getModels();
      setModels(modelData);
      const docData = await api.getDocuments();
      setDocuments(docData);
      // Load available categories for filter chips
      try {
        const catData = await api.getCategories();
        setCategories(catData.categories || []);
      } catch { /* non-critical */ }
    } catch (err) {
      console.error("Failed to load initial workspace data:", err);
    }
  };

  const saveSessionState = (sessId, updatedMessages) => {
    if (!updatedMessages || updatedMessages.length === 0) return;
    setSavedSessions(prev => {
      const firstUserMsg = updatedMessages.find(m => m.sender === 'user')?.text || 'Policy Inquiry';
      const title = firstUserMsg.length > 34 ? firstUserMsg.substring(0, 34) + '...' : firstUserMsg;
      const existingIdx = prev.findIndex(s => s.id === sessId);
      const sessionObj = {
        id: sessId, title,
        updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        messages: updatedMessages
      };
      let newSessions;
      if (existingIdx >= 0) {
        newSessions = [...prev]; newSessions[existingIdx] = sessionObj;
      } else {
        newSessions = [sessionObj, ...prev];
      }
      try { localStorage.setItem('compliance_chat_sessions', JSON.stringify(newSessions)); } catch {}
      return newSessions;
    });
  };

  const handleSendQuery = async (query) => {
    // Send up to 20 messages of history to the backend for long-context support
    const historyPayload = messages.slice(-20).map(m => ({ sender: m.sender, text: m.text }));

    const newMessagesWithUser = [...messages, { sender: 'user', text: query, timestamp: new Date() }];
    setMessages(newMessagesWithUser);
    setLoading(true);

    try {
      const target = targetDocument === 'All Policies' ? null : targetDocument;
      const res = await api.queryAgent(query, _selectedModel, historyPayload, sessionId, target);

      const finalMessages = [
        ...newMessagesWithUser,
        { sender: 'assistant', text: res.answer, status: res.status, timestamp: new Date() }
      ];
      setMessages(finalMessages);
      saveSessionState(sessionId, finalMessages);
    } catch (err) {
      console.error(err);
      const errMessages = [
        ...newMessagesWithUser,
        { sender: 'assistant', text: "Communication Error: The agent backend is offline. Please make sure FastAPI is running on port 3000.", status: 'danger', timestamp: new Date() }
      ];
      setMessages(errMessages);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    const newSessId = 'sess-' + Math.random().toString(36).substring(2, 10);
    setSessionId(newSessId);
    setMessages([]);
    setShowUpload(false);
    setShowDocs(false);
  };

  const handleSelectSession = (sess) => {
    setSessionId(sess.id);
    setMessages(sess.messages || []);
    setShowUpload(false);
    setShowDocs(false);
  };

  const handleDeleteSession = (e, sessId) => {
    e.stopPropagation();
    setSavedSessions(prev => {
      const updated = prev.filter(s => s.id !== sessId);
      try { localStorage.setItem('compliance_chat_sessions', JSON.stringify(updated)); } catch {}
      return updated;
    });
    if (sessionId === sessId) handleNewChat();
  };

  const refreshDocuments = async () => {
    try {
      const docData = await api.getDocuments(activeCategoryFilter);
      setDocuments(docData);
    } catch (err) { console.error(err); }
  };

  const handleCategoryFilter = async (cat) => {
    const next = activeCategoryFilter === cat ? null : cat;
    setActiveCategoryFilter(next);
    try {
      const docData = await api.getDocuments(next);
      setDocuments(docData);
    } catch {}
  };

  const currentSessionMsgs = savedSessions.find(s => s.id === sessionId)?.messages || messages;
  const userMsgCount      = currentSessionMsgs.filter(m => m.sender === 'user').length;
  const assistantMsgCount = currentSessionMsgs.filter(m => m.sender === 'assistant').length;
  const roleColor         = ROLE_COLORS[currentUser?.role] || 'var(--primary)';

  return (
    <div className="home-dashboard-layout sidebar-layout-container app-shell">
      {/* ── Left Chat Sidebar ── */}
      <aside className="chat-history-sidebar">
        {/* Branding */}
        <div className="sidebar-branding">
          <div className="brand-logo-wrapper">
            <img src="/logo.png" alt="Policy Buddy Logo" style={{ width:'32px', height:'32px', borderRadius:'8px' }} />
          </div>
          <div className="brand-text-group">
            <h1>POLICY<span> BUDDY</span></h1>
            <span className="sidebar-subtag">Policy Q&A Self-Service</span>
          </div>
        </div>

        {/* Logged-in user chip */}
        {currentUser && (
          <div className="sidebar-user-chip">
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{currentUser.name || currentUser.username}</span>
              <span className="sidebar-user-role" style={{ color: roleColor }}>{currentUser.role}</span>
            </div>
            <div className="sidebar-user-actions">
              {onGoAdmin && (
                <button className="sidebar-icon-btn" title="Admin Panel" onClick={onGoAdmin}>
                  <Shield size={14} />
                </button>
              )}
              <button className="sidebar-icon-btn" title="Logout" onClick={onLogout}>
                <LogOut size={14} />
              </button>
            </div>
          </div>
        )}

        {/* New Chat */}
        <button className="btn-sidebar-newchat" onClick={handleNewChat}>
          <PlusCircle size={16} />
          <span>New Conversation</span>
        </button>

        {/* Category Filter Chips */}
        {categories.length > 0 && (
          <div className="sidebar-cat-filters">
            <div className="sidebar-section-title" style={{ marginBottom:'6px' }}>
              <Tag size={12} /> <span>Filter by Category</span>
            </div>
            <div className="cat-chips-row">
              {categories.map((cat, i) => (
                <button
                  key={i}
                  className={`cat-filter-chip ${activeCategoryFilter === cat ? 'active' : ''}`}
                  onClick={() => handleCategoryFilter(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat History */}
        <div className="sidebar-history-section">
          <div className="sidebar-section-header">
            <div className="sidebar-section-title">
              <History size={13} /><span>Recent Chats</span>
            </div>
            <span className="history-count-badge">{savedSessions.length}</span>
          </div>

          <div className="sidebar-sessions-scroller">
            {savedSessions.length === 0 ? (
              <div className="sidebar-empty-hint">
                <MessageCircle size={20} style={{ marginBottom:'8px', opacity:0.4 }} />
                <div>No saved conversations yet.</div>
                <div style={{ marginTop:'4px', fontSize:'10px' }}>Ask a question to get started!</div>
              </div>
            ) : (
              savedSessions.map((sess) => (
                <div
                  key={sess.id}
                  className={`sidebar-session-item ${sess.id === sessionId ? 'active-sidebar-session' : ''}`}
                  onClick={() => handleSelectSession(sess)}
                >
                  <div className="sidebar-session-meta">
                    <MessageSquare size={14} className="session-item-icon" />
                    <div className="session-text-wrapper">
                      <span className="session-title-label">{sess.title}</span>
                      <div className="session-meta-row">
                        <span className="session-time-sub"><Clock size={10} /> {sess.updatedAt}</span>
                        <span className="session-message-count">{sess.messages?.length || 0} msgs</span>
                      </div>
                    </div>
                  </div>
                  <button className="btn-sidebar-delete" onClick={(e) => handleDeleteSession(e, sess.id)} title="Delete conversation">
                    <Trash2 size={12} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer Tools */}
        <div className="sidebar-footer-tools">
          <div className="sidebar-tools-label">Document Tools</div>
          <button className={`btn-sidebar-tool ${showUpload ? 'active' : ''}`} onClick={() => { setShowUpload(!showUpload); setShowDocs(false); }}>
            <Plus size={14} className="tool-icon" /><span>Upload Policy</span>
          </button>
          <button className={`btn-sidebar-tool ${showDocs ? 'active' : ''}`} onClick={() => { setShowDocs(!showDocs); setShowUpload(false); }}>
            <FolderOpen size={14} className="tool-icon" /><span>Policy Library ({documents.length})</span>
          </button>
        </div>
      </aside>

      {/* ── Main Chat Workspace ── */}
      <main className="main-chat-area">
        {/* Header */}
        <header className="main-chat-header">
          <div className="header-chat-title">
            <div className="header-chat-title-icon"><Bot size={15} /></div>
            <h2>Compliance Agent Workspace</h2>
          </div>
          <div className="header-right-group">
            <div className="header-stats-row">
              <div className="quick-stat"><span className="quick-stat-label">Questions</span><span className="quick-stat-value">{userMsgCount}</span></div>
              <div className="quick-stat"><span className="quick-stat-label">Responses</span><span className="quick-stat-value">{assistantMsgCount}</span></div>
              <div className="quick-stat">
                <FileText size={11} style={{ color:'var(--primary)' }} />
                <span className="quick-stat-label">Policies</span>
                <span className="quick-stat-value">{documents.length}</span>
              </div>
            </div>
            <div className="status-badge">
              <span className="dot-active" />
              <span>FAISS Database Ready</span>
            </div>
          </div>
        </header>

        {/* Upload Drawer */}
        {showUpload && (
          <div className="panel-drawer">
            <div className="drawer-header">
              <div className="drawer-title-group">
                <div className="drawer-icon-box"><Plus size={18} /></div>
                <div className="drawer-title-text">
                  <h3>Upload Employee Policy Document</h3>
                  <span className="drawer-desc">
                    Upload company handbooks, policy manuals, or operational documents.
                    Documents are automatically parsed, chunked, and indexed in FAISS.
                  </span>
                </div>
              </div>
              <button className="drawer-close-btn" onClick={() => setShowUpload(false)} title="Close"><X size={15} /></button>
            </div>
            <UploadPDF onUploadSuccess={() => { refreshDocuments(); setShowUpload(false); }} />
          </div>
        )}

        {/* Policy Library Drawer */}
        {showDocs && (
          <div className="panel-drawer">
            <div className="drawer-header">
              <div className="drawer-title-group">
                <div className="drawer-icon-box"><FolderOpen size={18} /></div>
                <div className="drawer-title-text">
                  <h3>Active Compliance Policy Indexes</h3>
                  <span className="drawer-desc">
                    Manage all active policy documents in the FAISS vector database.
                    Enterprise core policies are read-only.
                  </span>
                </div>
              </div>
              <button className="drawer-close-btn" onClick={() => setShowDocs(false)} title="Close"><X size={15} /></button>
            </div>
            <UploadedFiles documents={documents} onDeleteSuccess={refreshDocuments} />
          </div>
        )}

        <ChatWindow messages={messages} onSuggestClick={handleSendQuery} />
        {loading && <Loader />}

        {/* Document Selector */}
        <div className="target-doc-selector" style={{ padding:'0 24px', marginTop:'auto', display:'flex', alignItems:'center', gap:'8px', fontSize:'12px', color:'var(--text-muted)' }}>
          <FileText size={14} />
          <span>Chatting with:</span>
          <select
            value={targetDocument}
            onChange={(e) => setTargetDocument(e.target.value)}
            style={{ background:'var(--bg-card)', border:'1px solid var(--border-color)', borderRadius:'4px', padding:'4px 8px', fontSize:'12px', color:'var(--text-main)', outline:'none', cursor:'pointer' }}
          >
            <option value="All Policies">All Policies (Global Search)</option>
            {documents.map((doc, idx) => <option key={idx} value={doc.title}>{doc.title}</option>)}
          </select>
          {activeCategoryFilter && (
            <span className="cat-filter-active-badge">
              <Tag size={10} /> {activeCategoryFilter}
              <button onClick={() => handleCategoryFilter(activeCategoryFilter)} style={{ background:'none', border:'none', color:'inherit', cursor:'pointer', marginLeft:'4px', padding:0 }}><X size={10} /></button>
            </span>
          )}
        </div>

        <ChatInput onSend={handleSendQuery} disabled={loading} />
      </main>
    </div>
  );
};

export default Home;
