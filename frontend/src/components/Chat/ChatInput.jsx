import React, { useState } from 'react';
import { Send, Keyboard } from 'lucide-react';
import { VoiceRecorder } from '../Voice/VoiceRecorder';

export const ChatInput = ({ onSend, disabled }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !disabled) {
      onSend(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTranscription = (text) => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-inner">
        <div className="chat-input-helper-text">
          <span>Ask about policies, procedures, leave, dress code, or compliance questions</span>
          <div className="helper-icons">
            <div className="helper-item">
              <Keyboard size={11} />
              <span>Enter to send</span>
            </div>
          </div>
        </div>

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="chat-input-row">
            <VoiceRecorder onTranscriptionComplete={handleTranscription} />
            <input
              type="text"
              className="chat-input-field"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a compliance or operations question..."
              disabled={disabled}
              autoComplete="off"
            />
            <button 
              type="submit" 
              className="chat-send-btn"
              disabled={disabled || !inputValue.trim()}
              title="Send query"
            >
              <Send size={15} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default ChatInput;
