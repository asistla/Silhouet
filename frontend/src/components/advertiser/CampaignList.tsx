// frontend/src/components/advertiser/CampaignList.tsx
import React, { useState, useEffect } from 'react';
import { Table, Badge } from 'react-bootstrap';

interface Campaign {
  id: string;
  name: string;
  campaign_type: string;
  status: string;
  impressions_count: number;
  created_at: string;
}

interface CampaignListProps {
  getAuthHeaders: () => { [key: string]: string };
  apiBaseUrl: string;
}

export const CampaignList: React.FC<CampaignListProps> = ({ getAuthHeaders, apiBaseUrl }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        const response = await fetch(`${apiBaseUrl}/campaigns/`, { headers });
        if (response.ok) {
          const data = await response.json();
          setCampaigns(data);
        } else {
          setError('Failed to fetch campaigns.');
        }
      } catch (err) {
        setError('An error occurred while fetching campaigns.');
        console.error(err);
      }
    };

    fetchCampaigns();
  }, [getAuthHeaders, apiBaseUrl]);

  const getStatusBadge = (status: string) => {
    const variant = {
      'active': 'success',
      'paused': 'warning',
      'archived': 'secondary',
      'draft': 'primary',
    }[status] || 'light';
    return <Badge bg={variant}>{status.toUpperCase()}</Badge>;
  };

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  return (
    <div style={{ marginTop: '2rem' }}>
      <h3>Your Campaigns</h3>
      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Status</th>
            <th>Impressions</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {campaigns.length > 0 ? (
            campaigns.map(campaign => (
              <tr key={campaign.id}>
                <td>{campaign.name}</td>
                <td>{campaign.campaign_type}</td>
                <td>{getStatusBadge(campaign.status)}</td>
                <td>{campaign.impressions_count}</td>
                <td>{new Date(campaign.created_at).toLocaleDateString()}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} className="text-center">No campaigns found.</td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
};
