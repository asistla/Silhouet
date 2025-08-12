import React from "react";
import styled from "styled-components";

const InsightContainer = styled.div`
  background: #ffffff10;
  border-radius: 8px;
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const InsightTitle = styled.div`
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 1rem;
  color: #ffffffcc;
`;

const InsightText = styled.div`
  font-size: 0.9rem;
  line-height: 1.4;
  color: #ffffff;
  overflow-y: auto;
`;

interface InsightSlotProps {
  text?: string;
}

const InsightSlot: React.FC<InsightSlotProps> = ({ text }) => {
  return (
    <InsightContainer>
      <InsightTitle>Insights</InsightTitle>
      <InsightText>
        {text || "No insights available right now"}
      </InsightText>
    </InsightContainer>
  );
};

export default InsightSlot;
