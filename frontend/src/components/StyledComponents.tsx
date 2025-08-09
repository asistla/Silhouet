import styled from 'styled-components';

// Main layout container
export const MainContainer = styled.div`
  display: flex;
  height: 100vh;
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  font-family: ${({ theme }) => theme.font.family};
`;

// Left panel
export const LeftPanel = styled.div`
  width: 20%;
  padding: ${({ theme }) => theme.spacing(2)};
  border-right: 1px solid ${({ theme }) => theme.colors.accent};
  box-shadow: 5px 0 15px -5px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
`;

// Center panel
export const CenterPanel = styled.div`
  width: 50%;
  padding: ${({ theme }) => theme.spacing(2)};
  display: flex;
  flex-direction: column;
`;

// Right panel
export const RightPanel = styled.div`
  width: 30%;
  padding: ${({ theme }) => theme.spacing(2)};
  border-left: 1px solid ${({ theme }) => theme.colors.accent};
  background-color: ${({ theme }) => theme.colors.panel};
  overflow-y: auto;
`;

// Journal textarea
export const TextArea = styled.textarea`
  flex-grow: 1;
  width: 100%;
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
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
  padding: ${({ theme }) => `${theme.spacing(1)} ${theme.spacing(2)}`};
  border-radius: 4px;
  cursor: pointer;
  font-family: ${({ theme }) => theme.font.family};
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${({ theme }) => theme.colors.accent};
  }
`;

// Auth container for login/register pages
export const AuthContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: ${({ theme }) => theme.colors.background};
  padding: ${({ theme }) => theme.spacing(2)};
  font-family: ${({ theme }) => theme.font.family};

  > div {
    width: 100%;
    max-width: 40rem;
    padding: ${({ theme }) => theme.spacing(3)};
    background-color: ${({ theme }) => theme.colors.panel};
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    border: 1px solid ${({ theme }) => theme.colors.accent};
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
