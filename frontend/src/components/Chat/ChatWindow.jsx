import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ShieldCheck, Sparkles } from 'lucide-react';

export const ChatWindow = ({ messages, onSuggestClick }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const suggestions = [
    {
      text: "What is the dress code policy? Can I wear shorts?",
      category: "Workplace"
    },
    {
      text: "How much notice do I need to give if I decide to resign?",
      category: "HR Policy"
    },
    {
      text: "Can I offer a cash bribe to a public official?",
      category: "Compliance"
    },
    {
      text: "What are the bereavement leave limits for full-time employees?",
      category: "Benefits"
    }
  ];

  return (
    <div className="chat-window-container">
      <div className="chat-messages-scroller">
        {messages.length === 0 ? (
          <div className="chat-welcome-screen">
            <div className="welcome-icon-wrapper">
              <div className="welcome-icon-ring"></div>
              <div className="welcome-icon-bg">
                <ShieldCheck size={32} style={{ color: '#0a0d16' }} />
              </div>
            </div>
            
            <h2 className="welcome-title">Enterprise Compliance Assistant</h2>
            <p className="welcome-subtitle">
              Your AI-powered guide to company policies and procedures. 
              Ask questions about workplace rules, HR guidelines, ethics, and operational protocols.
            </p>

            <div className="suggestions-panel">
              <div className="suggestions-header">
                <Sparkles size={14} className="suggest-icon" />
                <span className="suggest-title">Suggested Inquiries to Get Started</span>
              </div>
              
              <div className="suggest-list">
                {suggestions.map((s, idx) => (
                  <button 
                    key={idx} 
                    className="suggest-item-btn"
                    onClick={() => onSuggestClick(s.text)}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ 
                        fontSize: '10px', 
                        color: 'var(--primary)', 
                        fontWeight: 600, 
                        marginBottom: '4px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em'
                      }}>
                        {s.category}
                      </div>
                      <div>{s.text}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className="message-wrapper">
              <ChatMessage message={msg} onSuggestClick={onSuggestClick} />
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
export default ChatWindow;
