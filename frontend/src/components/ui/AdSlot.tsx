import React from 'react';

interface AdData {
  campaign_id: string;
  content: {
    text: string;
    link: string;
  };
}

interface AdSlotProps {
  adData: AdData | null;
}

export const AdSlot: React.FC<AdSlotProps> = ({ adData }) => {
  if (!adData) {
    return (
      <div style={{
        padding: '8px',
        background: '#F3F4F6',
        borderRadius: '8px',
        marginTop: '16px',
        textAlign: 'center',
        color: '#6B7280',
        fontSize: '0.8rem'
      }}>
        <p style={{ margin: 0 }}>Ad slot available</p>
      </div>
    );
  }

  return (
    <div style={{
      padding: '8px',
      background: '#FFFBEB',
      borderRadius: '8px',
      marginTop: '16px',
      border: '1px solid #FBBF24'
    }}>
      <a 
        href={adData.content.link} 
        target="_blank" 
        rel="noopener noreferrer"
        style={{ textDecoration: 'none', color: 'inherit' }}
      >
        <p style={{ margin: 0, fontWeight: 'bold', fontSize: '0.75rem', color: '#92400E' }}>Sponsored</p>
        <p style={{ margin: 0, color: '#B45309' }}>{adData.content.text}</p>
      </a>
    </div>
  );
};
