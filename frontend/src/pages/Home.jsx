import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, Plus, FolderOpen, History, PlusCircle, 
  Trash2, Clock, Bot, FileText, X, ShieldCheck,
  MessageCircle
} from 'lucide-react';
import { api } from '../services/api';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { ChatInput } from '../components/Chat/ChatInput';
import { UploadPDF } from '../components/Upload/UploadPDF';
import { UploadedFiles } from '../components/Upload/UploadedFiles';
import { Loader } from '../components/UI/Loader';

export const Home = () => {
  const [sessionId, setSessionId] = useState(() => 'sess-' + Math.random().toString(36).substring(2, 10));
  const [messages, setMessages] = useState([]);
  const [_models, setModels] = useState([]);
  const [_selectedModel] = useState('gemini-2.5-flash');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showDocs, setShowDocs] = useState(false);
  const [targetDocument, setTargetDocument] = useState('All Policies');

  const [savedSessions, setSavedSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('compliance_chat_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const modelData = await api.getModels();
      setModels(modelData);
      
      const docData = await api.getDocuments();
      setDocuments(docData);
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
        id: sessId,
        title: title,
        updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        messages: updatedMessages
      };

      let newSessions;
      if (existingIdx >= 0) {
        newSessions = [...prev];
        newSessions[existingIdx] = sessionObj;
      } else {
        newSessions = [sessionObj, ...prev];
      }
      
      try {
        localStorage.setItem('compliance_chat_sessions', JSON.stringify(newSessions));
      } catch (e) {
        console.error("Failed to persist sessions to localStorage:", e);
      }
      return newSessions;
    });
  };

  const handleSendQuery = async (query) => {
    const historyPayload = messages.slice(-6).map(m => ({
      sender: m.sender,
      text: m.text
    }));

    const newMessagesWithUser = [...messages, { sender: 'user', text: query, timestamp: new Date() }];
    setMessages(newMessagesWithUser);
    setLoading(true);

    try {
      const target = targetDocument === 'All Policies' ? null : targetDocument;
      const res = await api.queryAgent(query, _selectedModel, historyPayload, sessionId, target);
      
      const finalMessages = [...newMessagesWithUser, { 
        sender: 'assistant', 
        text: res.answer, 
        status: res.status,
        timestamp: new Date()
      }];
      
      setMessages(finalMessages);
      saveSessionState(sessionId, finalMessages);

    } catch (err) {
      console.error(err);
      const errMessages = [...newMessagesWithUser, { 
        sender: 'assistant', 
        text: "⚠️ Communication Error: The agent backend is offline. Please make sure FastAPI is running on port 3000.", 
        status: 'danger',
        timestamp: new Date()
      }];
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
      try {
        localStorage.setItem('compliance_chat_sessions', JSON.stringify(updated));
      } catch {}
      return updated;
    });
    if (sessionId === sessId) {
      handleNewChat();
    }
  };

  const refreshDocuments = async () => {
    try {
      const docData = await api.getDocuments();
      setDocuments(docData);
    } catch (err) {
      console.error(err);
    }
  };

  const _enterpriseDocs = documents.filter(d => d.source === 'Enterprise');
  const _uploadedDocs = documents.filter(d => d.source !== 'Enterprise');
  const currentSessionMsgs = savedSessions.find(s => s.id === sessionId)?.messages || messages;
  const userMsgCount = currentSessionMsgs.filter(m => m.sender === 'user').length;
  const assistantMsgCount = currentSessionMsgs.filter(m => m.sender === 'assistant').length;

  return (
    <div className="home-dashboard-layout sidebar-layout-container app-shell">
      {/* Left Chat Sidebar */}
      <aside className="chat-history-sidebar">
        {/* Branding Section */}
        <div className="sidebar-branding">
          <div className="brand-logo-wrapper">
            <img src="/logo.png" alt="Policy Buddy Logo" style={{ width: '32px', height: '32px', borderRadius: '8px' }} />
          </div>
          <div className="brand-text-group">
            <h1>POLICY<span> BUDDY</span></h1>
            <span className="sidebar-subtag">Policy Q&A Self-Service</span>
          </div>
        </div>

        {/* New Chat Button */}
        <button className="btn-sidebar-newchat" onClick={handleNewChat}>
          <PlusCircle size={16} />
          <span>New Conversation</span>
        </button>

        {/* Chat History Section */}
        <div className="sidebar-history-section">
          <div className="sidebar-section-header">
            <div className="sidebar-section-title">
              <History size={13} />
              <span>Recent Chats</span>
            </div>
            <span className="history-count-badge">{savedSessions.length}</span>
          </div>

          <div className="sidebar-sessions-scroller">
            {savedSessions.length === 0 ? (
              <div className="sidebar-empty-hint">
                <MessageCircle size={20} style={{ marginBottom: '8px', opacity: 0.4 }} />
                <div>No saved conversations yet.</div>
                <div style={{ marginTop: '4px', fontSize: '10px' }}>Ask a question to get started!</div>
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
                        <span className="session-time-sub">
                          <Clock size={10} /> {sess.updatedAt}
                        </span>
                        <span className="session-message-count">
                          {sess.messages?.length || 0} msgs
                        </span>
                      </div>
                    </div>
                  </div>
                  <button 
                    className="btn-sidebar-delete"
                    onClick={(e) => handleDeleteSession(e, sess.id)}
                    title="Delete conversation"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer Policy Tools */}
        <div className="sidebar-footer-tools">
          <div className="sidebar-tools-label">Document Tools</div>
          <button 
            className={`btn-sidebar-tool ${showUpload ? 'active' : ''}`}
            onClick={() => { setShowUpload(!showUpload); setShowDocs(false); }}
          >
            <Plus size={14} className="tool-icon" />
            <span>Upload Policy</span>
          </button>

          <button 
            className={`btn-sidebar-tool ${showDocs ? 'active' : ''}`}
            onClick={() => { setShowDocs(!showDocs); setShowUpload(false); }}
          >
            <FolderOpen size={14} className="tool-icon" />
            <span>Policy Library ({documents.length})</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <main className="main-chat-area">
        {/* Workspace Top Header */}
        <header className="main-chat-header">
          <div className="header-chat-title">
            <div className="header-chat-title-icon">
              <Bot size={15} />
            </div>
            <h2>Compliance Agent Workspace</h2>
          </div>
          
          <div className="header-right-group">
            <div className="header-stats-row">
              <div className="quick-stat">
                <span className="quick-stat-label">Questions</span>
                <span className="quick-stat-value">{userMsgCount}</span>
              </div>
              <div className="quick-stat">
                <span className="quick-stat-label">Responses</span>
                <span className="quick-stat-value">{assistantMsgCount}</span>
              </div>
              <div className="quick-stat">
                <FileText size={11} style={{ color: 'var(--primary)' }} />
                <span className="quick-stat-label">Policies</span>
                <span className="quick-stat-value">{documents.length}</span>
              </div>
            </div>
            <div className="status-badge">
              <span className="dot-active"></span>
              <span>FAISS Database Ready</span>
            </div>
          </div>
        </header>

        {/* Slide-down Upload / Policy Directory Drawer */}
        {showUpload && (
          <div className="panel-drawer">
            <div className="drawer-header">
              <div className="drawer-title-group">
                <div className="drawer-icon-box">
                  <Plus size={18} />
                </div>
                <div className="drawer-title-text">
                  <h3>Upload Employee Policy Document</h3>
                  <span className="drawer-desc">
                    Upload company handbooks, policy manuals, or operational documents in PDF, TXT, Markdown, or JSON format. 
                    Documents are automatically parsed, chunked, and indexed in the FAISS vector database for semantic retrieval.
                  </span>
                </div>
              </div>
              <button 
                className="drawer-close-btn" 
                onClick={() => setShowUpload(false)}
                title="Close upload panel"
              >
                <X size={15} />
              </button>
            </div>
            <UploadPDF onUploadSuccess={() => { refreshDocuments(); setShowUpload(false); }} />
          </div>
        )}

        {showDocs && (
          <div className="panel-drawer">
            <div className="drawer-header">
              <div className="drawer-title-group">
                <div className="drawer-icon-box">
                  <FolderOpen size={18} />
                </div>
                <div className="drawer-title-text">
                  <h3>Active Compliance Policy Indexes</h3>
                  <span className="drawer-desc">
                    Manage all active policy documents loaded in the FAISS vector database. 
                    Enterprise core policies are read-only. User-uploaded documents can be removed individually.
                  </span>
                </div>
              </div>
              <button 
                className="drawer-close-btn" 
                onClick={() => setShowDocs(false)}
                title="Close policy library"
              >
                <X size={15} />
              </button>
            </div>
            <UploadedFiles documents={documents} onDeleteSuccess={refreshDocuments} />
          </div>
        )}

        <ChatWindow 
          messages={messages} 
          onSuggestClick={handleSendQuery} 
        />

        {loading && <Loader />}

        <div className="target-doc-selector" style={{ 
            padding: '0 24px', 
            marginTop: 'auto', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '12px',
            color: 'var(--text-muted)'
        }}>
            <FileText size={14} />
            <span>Chatting with:</span>
            <select 
                value={targetDocument} 
                onChange={(e) => setTargetDocument(e.target.value)}
                style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    padding: '4px 8px',
                    fontSize: '12px',
                    color: 'var(--text-main)',
                    outline: 'none',
                    cursor: 'pointer'
                }}
            >
                <option value="All Policies">All Policies (Global Search)</option>
                {documents.map((doc, idx) => (
                    <option key={idx} value={doc.title}>{doc.title}</option>
                ))}
            </select>
        </div>

        <ChatInput onSend={handleSendQuery} disabled={loading} />
      </main>
    </div>
  );
};
export default Home;
