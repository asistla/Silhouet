import styled from 'styled-components';

// ==================================================================
// Generic Components for Advertiser Console & Other Future Views
// ==================================================================

export const Container = styled.div`
  padding: ${({ theme }) => theme.spacing(3)};
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  min-height: 100vh;
`;

export const Title = styled.h1`
  font-size: 2.5rem;
  color: ${({ theme }) => theme.colors.accent};
  margin-bottom: ${({ theme }) => theme.spacing(3)};
  text-align: center;
  font-family: ${({ theme }) => theme.font.family};
`;

export const Section = styled.section`
  margin-bottom: ${({ theme }) => theme.spacing(4)};
  padding: ${({ theme }) => theme.spacing(3)};
  background-color: ${({ theme }) => theme.colors.panel};
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
`;

export const SectionTitle = styled.h2`
  font-size: 1.8rem;
  border-bottom: 2px solid ${({ theme }) => theme.colors.accent};
  padding-bottom: ${({ theme }) => theme.spacing(1)};
  margin-bottom: ${({ theme }) => theme.spacing(3)};
  color: ${({ theme }) => theme.colors.text};
`;

export const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: ${({ theme }) => theme.spacing(3)};
`;

// ==================================================================
// Main Application Layout Components
// ==================================================================

export const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden; /* prevent scrollbars if not needed */
`;

export const MainContainer = styled.div`
  flex: 1;
  display: flex;
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  font-family: ${({ theme }) => theme.font.family};
  box-sizing: border-box;
  overflow: hidden; /* Prevents main content from scrolling */
`;

// Left panel
export const LeftPanel = styled.div`
  flex: 0 0 280px; /* Fixed width */
  padding: ${({ theme }) => theme.spacing(3)};
  border-right: 1px solid ${({ theme }) => theme.colors.borderColor};
  box-shadow: 5px 0 15px -5px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
`;

// Center panel
export const CenterPanel = styled.div`
  flex: 1 1 60%;
  padding: ${({ theme }) => theme.spacing(3)};
  display: flex;
  flex-direction: column;
`;

// Right panel
export const RightPanel = styled.div`
  flex: 1 1 40%;
  padding: ${({ theme }) => theme.spacing(3)};
  border-left: 1px solid ${({ theme }) => theme.colors.borderColor};
  background-color: ${({ theme }) => theme.colors.panel};
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing(2)};
  
  /* Children split */
  & > .ad-slot {
    flex: 0 0 40%;
  }

  & > .insight-slot {
    flex: 0 0 60%;
  }
`;

export const ScoreChartContainer = styled.div`
  height: 250px; /* Increased height for the chart */
  background-color: ${({ theme }) => theme.colors.panel};
  border-top: 1px solid ${({ theme }) => theme.colors.borderColor};
  padding: ${({ theme }) => theme.spacing(2)};
  box-sizing: border-box;
`;

// Journal textarea
export const TextArea = styled.textarea`
  flex-grow: 1;
  width: 100%;
  background-color: ${({ theme }) => theme.colors.paper};
  color: ${({ theme }) => theme.colors.textOnPaper};
  border: 1px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
  padding: ${({ theme }) => theme.spacing(2)};
  font-family: ${({ theme }) => theme.font.family};
  font-size: 1.1rem;
  line-height: 1.7;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
  resize: none;
  outline: none;
`;

// Generic styled button
export const StyledButton = styled.button`
  background-color: ${({ theme }) => theme.colors.buttonBg};
  color: ${({ theme }) => theme.colors.buttonText};
  border: none;
  padding: ${({ theme }) => `${theme.spacing(1.5)} ${theme.spacing(3)}`};
  border-radius: 4px;
  cursor: pointer;
  font-family: ${({ theme }) => theme.font.family};
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background-color: ${({ theme }) => theme.colors.accent2};
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    transform: translateY(-2px);
  }
`;

// Auth container for login/register pages
export const AuthContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: ${({ theme }) => theme.spacing(2)};

  > div {
    width: 100%;
    max-width: 45rem; /* Increased max-width */
    padding: ${({ theme }) => theme.spacing(4)}; /* Increased padding */
    background-color: ${({ theme }) => theme.colors.panel};
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    border: 1px solid ${({ theme }) => theme.colors.borderColor};
    color: ${({ theme }) => theme.colors.text};
  }
`;

// Logout button reusing StyledButton
export const LogoutButton = styled(StyledButton)`
  position: absolute;
  top: ${({ theme }) => theme.spacing(2)};
  right: ${({ theme }) => theme.spacing(2)};
  z-index: 10;
`;

export const LogoContainer = styled.div`
  text-align: center;
  padding-bottom: 2rem;

  .logo-svg {
    width: 80%;
    height: auto;
    fill: ${({ theme }) => theme.colors.accent};
    filter: drop-shadow(0 0 5px ${({ theme }) => theme.colors.accent2});
  }
`;
