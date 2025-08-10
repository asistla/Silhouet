import React from 'react';

interface InsightSlotProps {
  insightText: string | null;
}

export const InsightSlot: React.FC<InsightSlotProps> = ({ insightText }) => {
  if (!insightText) {
    return null; // Don't render anything if there's no insight
  }

  return (
    <div style={{
      padding: '8px',
      background: '#E0E7FF', // A slightly different background for distinction
      borderRadius: '8px',
      marginTop: '16px',
      border: '1px solid #C7D2FE'
    }}>
      <p style={{ margin: 0, color: '#4338CA', fontSize: '0.9rem' }}>
        <strong>Insight:</strong> {insightText}
      </p>
    </div>
  );
};
