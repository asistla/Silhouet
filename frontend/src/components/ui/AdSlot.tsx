import React from 'react';
import styled from 'styled-components';

const AdContainer = styled.div`
  background: #ffffff10;
  border-radius: 8px;
  padding: 15px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
`;

const AdTitle = styled.div`
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 1.1rem;
  color: #ffffffcc;
`;

const AdContent = styled.div`
  font-size: 0.9rem;
  line-height: 1.4;
  color: #ffffff;
  margin-bottom: 15px;
`;

const CallToActionButton = styled.a`
  display: inline-block;
  background-color: #c5b358;
  color: #1e1e1e;
  padding: 8px 15px;
  border-radius: 5px;
  text-decoration: none;
  font-weight: bold;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #b3a24f;
  }
`;

interface AdSlotProps {
  title?: string;
  content?: string;
  callToAction?: string;
  position?: string; // Keep position for placeholder usage
}

export const AdSlot: React.FC<AdSlotProps> = ({ title, content, callToAction, position }) => {
  if (title && content) {
    // Render the full ad if we have title and content
    return (
      <AdContainer>
        <div>
          <AdTitle>{title}</AdTitle>
          <AdContent>{content}</AdContent>
        </div>
        {callToAction && <CallToActionButton href="#">{callToAction}</CallToActionButton>}
      </AdContainer>
    );
  }
return null;
};
