import React from 'react';
export const AdSlot = ({ position }: { position: string }) => {
  return (
    <div style={{
      padding: '8px',
      background: '#EEE',
      borderRadius: '8px',
      marginTop: '16px'
    }}>
      <p>Sponsored — Ad placeholder ({position})</p>
    </div>
  );
};
