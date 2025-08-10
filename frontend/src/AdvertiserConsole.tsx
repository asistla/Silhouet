// frontend/src/AdvertiserConsole.tsx
import React, { useState, useCallback } from 'react';
import { MainContainer, LeftPanel, RightPanel, LogoutButton, StyledButton } from './components/StyledComponents';
import { CampaignList } from './components/advertiser/CampaignList';
import { CampaignForm } from './components/advertiser/CampaignForm';
import { ReactComponent as Logo } from './logo.svg';

interface AdvertiserConsoleProps {
  onLogout: () => void;
  getAuthHeaders: () => { [key: string]: string };
  apiBaseUrl: string;
  toggleTheme: () => void;
  isDark: boolean;
}

const AdvertiserConsole: React.FC<AdvertiserConsoleProps> = ({ onLogout, getAuthHeaders, apiBaseUrl, toggleTheme, isDark }) => {
  // A simple key to force re-render of the CampaignList when a new campaign is created
  const [campaignListKey, setCampaignListKey] = useState(0);

  const handleCampaignCreated = useCallback(() => {
    setCampaignListKey(prevKey => prevKey + 1);
  }, []);

  return (
    <MainContainer>
      <StyledButton 
        onClick={toggleTheme} 
        style={{ position: 'absolute', top: '2rem', left: '2rem', zIndex: 10 }}>
          {isDark ? 'Light Mode' : 'Dark Mode'}
      </StyledButton>
      <LogoutButton onClick={onLogout}>Logout</LogoutButton>
      
      <LeftPanel>
        <div className="logo-container"><Logo className="logo-svg" /></div>
        <CampaignForm 
          getAuthHeaders={getAuthHeaders} 
          apiBaseUrl={apiBaseUrl} 
          onCampaignCreated={handleCampaignCreated} 
        />
      </LeftPanel>
      
      <RightPanel style={{ width: '80%' }}>
        <h2>Campaign Dashboard</h2>
        <CampaignList 
          key={campaignListKey} 
          getAuthHeaders={getAuthHeaders} 
          apiBaseUrl={apiBaseUrl} 
        />
      </RightPanel>
    </MainContainer>
  );
};

export default AdvertiserConsole;
