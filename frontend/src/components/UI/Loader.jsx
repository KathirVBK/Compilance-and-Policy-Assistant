import React from 'react';

export const Loader = ({ message }) => {
  const loadingMessages = [
    'Analyzing policy documents...',
    'Searching vector database...',
    'Retrieving relevant clauses...',
    'Formulating compliance response...',
    'Verifying policy alignment...'
  ];
  
  const displayMessage = message || loadingMessages[Math.floor(Math.random() * loadingMessages.length)];

  return (
    <div className="loader-container">
      <div className="loader-wrapper">
        <div className="loader-spinner"></div>
        <span className="loader-text">{displayMessage}</span>
        <div className="loader-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
};
export default Loader;
