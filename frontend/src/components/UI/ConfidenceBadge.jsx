import React from 'react';

export const ConfidenceBadge = ({ riskLevel }) => {
  const getBadgeClass = () => {
    switch (riskLevel?.toUpperCase()) {
      case 'SAFE':
        return 'badge-safe';
      case 'MEDIUM RISK':
      case 'LOW RISK':
      case 'WARNING':
        return 'badge-warning';
      case 'HIGH RISK':
        return 'badge-danger';
      default:
        return 'badge-muted';
    }
  };

  return (
    <span className={`confidence-badge ${getBadgeClass()}`}>
      {riskLevel || 'UNKNOWN'}
    </span>
  );
};
