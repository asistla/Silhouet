// frontend/src/components/ui/Spinner.tsx
import React from 'react';
import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const SpinnerContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
`;

const StyledSpinner = styled.div`
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid ${({ theme }) => theme.colors.accent};
  width: 40px;
  height: 40px;
  animation: ${spin} 1s linear infinite;
`;

const Spinner: React.FC = () => (
  <SpinnerContainer>
    <StyledSpinner />
  </SpinnerContainer>
);

export default Spinner;
