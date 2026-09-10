import React from 'react';
import { Bot, User, ShieldAlert, AlertTriangle, ArrowRight, HelpCircle, Clock } from 'lucide-react';
import { VoicePlayer } from '../Voice/VoicePlayer';

export const ChatMessage = ({ message, onSuggestClick }) => {
  const { sender, text, status, timestamp } = message;
  const isUser = sender === 'user';
  
  let mainText = text || '';
  let followUps = [];

  const followUpRegex = /(?:###?\s*)?(?:Follow-up Questions|Suggested Follow-ups|Follow-up Inquiries|Related Questions):\s*([\s\S]*?)$/i;
  const followUpMatch = mainText.match(followUpRegex);

  if (followUpMatch) {
    const rawQuestions = followUpMatch[1].trim();
    mainText = mainText.substring(0, followUpMatch.index).trim();
    followUps = rawQuestions
      .split('\n')
      .map(q => q.replace(/^[•\-*\d.\s]+/, '').replace(/[*]/g, '').trim())
      .filter(q => q.length > 5 && q.endsWith('?'));
  }

  const parseMarkdown = (content) => {
    if (!content) return null;
    
    const lines = content.split('\n');
    return lines.map((line, lineIdx) => {
      let trimmed = line.trim();
      let isBlockquote = false;
      
      if (trimmed.startsWith('>')) {
        isBlockquote = true;
        trimmed = trimmed.substring(1).trim();
      }

      const processInline = (textStr) => {
        const cleanStr = textStr.replace(/[*]/g, '');
        const parts = cleanStr.split(/<b>(.*?)<\/b>/g);
        return parts.map((part, partIdx) => {
          if (partIdx % 2 === 1) {
            return <strong key={partIdx}>{part}</strong>;
          }
          return part;
        });
      };

      let node = null;
      
      if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
        const contentText = trimmed.substring(1).trim();
        node = (
          <li key={lineIdx} className="md-bullet-item">
            {processInline(contentText)}
          </li>
        );
      } 
      else if (trimmed.startsWith('###')) {
        const contentText = trimmed.substring(3).trim();
        node = <h4 key={lineIdx} className="md-h4">{processInline(contentText)}</h4>;
      } 
      else if (trimmed.startsWith('##')) {
        const contentText = trimmed.substring(2).trim();
        node = <h3 key={lineIdx} className="md-h3">{processInline(contentText)}</h3>;
      } 
      else if (line === '') {
        node = <div key={lineIdx} className="md-space" />;
      } 
      else {
        node = <p key={lineIdx} className="md-para">{processInline(line)}</p>;
      }

      if (isBlockquote) {
        return (
          <blockquote key={lineIdx} className="md-blockquote">
            {node}
          </blockquote>
        );
      }

      return node;
    });
  };

  const getBubbleClass = () => {
    if (isUser) return 'bubble-user';
    if (status === 'escalated') return 'bubble-danger';
    if (status === 'conflict') return 'bubble-warning';
    return 'bubble-assistant';
  };

  const getRoleTagClass = () => {
    if (status === 'escalated') return 'tag-escalated';
    if (status === 'conflict') return 'tag-conflict';
    if (isUser) return 'tag-user';
    return 'tag-assistant';
  };

  const getRoleLabel = () => {
    if (isUser) return 'You';
    if (status === 'escalated') return 'Escalated';
    if (status === 'conflict') return 'Conflict';
    return 'Compliance.AI';
  };

  const getAvatarBadge = () => {
    if (status === 'escalated') return 'badge-danger-bg';
    if (status === 'conflict') return 'badge-warning-bg';
    return 'badge-success';
  };

  const formatTime = (ts) => {
    if (!ts) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    try {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  };

  const getIcon = () => {
    if (isUser) return <User size={17} />;
    if (status === 'escalated') return <ShieldAlert size={17} />;
    if (status === 'conflict') return <AlertTriangle size={17} />;
    return <Bot size={17} />;
  };

  return (
    <div className={`chat-message-row ${isUser ? 'row-user' : 'row-assistant'}`}>
      <div className={`message-avatar ${isUser ? 'avatar-user' : 'avatar-assistant'}`}>
        {getIcon()}
        {!isUser && (
          <div className={`avatar-badge ${getAvatarBadge()}`}>
            ✓
          </div>
        )}
      </div>
      
      <div className={`message-bubble ${getBubbleClass()}`}>
        <div className="message-meta-header">
          <div className="meta-sender-info">
            <span className="sender-name">{getRoleLabel()}</span>
            <span className={`sender-role-tag ${getRoleTagClass()}`}>
              {isUser ? 'User' : (status === 'escalated' ? 'Human Review' : status === 'conflict' ? 'Review Needed' : 'AI Agent')}
            </span>
          </div>
          <div className="meta-timestamp">
            <Clock size={10} />
            {formatTime(timestamp)}
          </div>
        </div>

        <div className="message-content-md">
          {parseMarkdown(mainText)}
        </div>

        {!isUser && status !== 'escalated' && mainText && (
          <div className="message-actions-bar" style={{ marginTop: '8px', marginBottom: '8px' }}>
            <VoicePlayer text={mainText} />
          </div>
        )}

        {/* Interactive Follow-up Questions */}
        {!isUser && followUps.length > 0 && (
          <div className="chat-followup-section">
            <div className="followup-header-lbl">
              <HelpCircle size={13} />
              <span>Suggested Follow-up Questions</span>
            </div>
            <div className="followup-buttons-grid">
              {followUps.map((qText, fIdx) => (
                <button
                  key={fIdx}
                  className="btn-followup-chip"
                  onClick={() => onSuggestClick && onSuggestClick(qText)}
                >
                  <span>{qText}</span>
                  <ArrowRight size={12} />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default ChatMessage;
