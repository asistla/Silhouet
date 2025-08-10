// frontend/src/components/advertiser/CampaignForm.tsx
import React, { useState } from 'react';
import styled from 'styled-components';
import { StyledButton } from '../StyledComponents';

const FormContainer = styled.div`
  padding: ${({ theme }) => theme.spacing(3)};
  background-color: ${({ theme }) => theme.colors.panel};
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.colors.accent};
  margin-top: 2rem;
`;

const FormGroup = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing(2)};
`;

const Label = styled.label`
  display: block;
  margin-bottom: ${({ theme }) => theme.spacing(1)};
  font-weight: bold;
`;

const Input = styled.input`
  width: 100%;
  padding: ${({ theme }) => theme.spacing(1)};
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  border: 1px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: ${({ theme }) => theme.spacing(1)};
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  border: 1px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
  min-height: 100px;
  resize: vertical;
`;

interface CampaignFormProps {
  getAuthHeaders: () => { [key: string]: string };
  apiBaseUrl: string;
  onCampaignCreated: () => void; // Callback to refresh the list
}

export const CampaignForm: React.FC<CampaignFormProps> = ({ getAuthHeaders, apiBaseUrl, onCampaignCreated }) => {
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [targeting, setTargeting] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    let parsedContent;
    let parsedTargeting;

    try {
      parsedContent = JSON.parse(content);
      parsedTargeting = JSON.parse(targeting);
    } catch (err) {
      setError('Content and Targeting Criteria must be valid JSON.');
      return;
    }

    const campaignData = {
      name,
      campaign_type: 'ad',
      status: 'draft',
      content: parsedContent,
      targeting_criteria: parsedTargeting,
    };

    try {
      const authHeaders = getAuthHeaders();
      if (!authHeaders.Authorization) {
        setError("You are not authenticated.");
        return;
      }
      const headers = { ...authHeaders, 'Content-Type': 'application/json' };

      const response = await fetch(`${apiBaseUrl}/campaigns/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(campaignData),
      });

      if (response.ok) {
        setSuccess('Campaign created successfully!');
        setName('');
        setContent('');
        setTargeting('');
        onCampaignCreated(); // Trigger refresh
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create campaign.');
      }
    } catch (err) {
      setError('An error occurred while creating the campaign.');
      console.error(err);
    }
  };

  return (
    <FormContainer>
      <h3>Create New Campaign</h3>
      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      <form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="name">Campaign Name</Label>
          <Input id="name" type="text" value={name} onChange={e => setName(e.target.value)} required />
        </FormGroup>
        <FormGroup>
          <Label htmlFor="content">Content (JSON)</Label>
          <TextArea id="content" value={content} onChange={e => setContent(e.target.value)} required placeholder='{ "text": "My ad text", "link": "https://example.com" }' />
        </FormGroup>
        <FormGroup>
          <Label htmlFor="targeting">Targeting Criteria (JSON)</Label>
          <TextArea id="targeting" value={targeting} onChange={e => setTargeting(e.target.value)} required placeholder='{ "state": "California", "avg_resentment_score_gt": 0.7 }' />
        </FormGroup>
        <StyledButton type="submit">Create Campaign</StyledButton>
      </form>
    </FormContainer>
  );
};
