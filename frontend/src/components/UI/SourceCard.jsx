import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

export const SourceCard = ({ citation }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="source-card">
      <div className="source-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="source-title-row">
          <FileText className="source-icon" size={14} />
          <span className="source-title">{citation.docTitle}</span>
        </div>
        <div className="source-meta-row">
          <span className="source-ver">v{citation.version}</span>
          <span className="source-score">Match: {Math.round(citation.score * 100)}%</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>
      
      {expanded && (
        <div className="source-card-body">
          <p className="source-details">
            <strong>Issued by:</strong> {citation.author} | <strong>Effective:</strong> {citation.date}
          </p>
          <div className="source-snippet">
            "{citation.content}"
          </div>
        </div>
      )}
    </div>
  );
};
export default SourceCard;
