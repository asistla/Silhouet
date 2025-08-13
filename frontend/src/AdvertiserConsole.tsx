// frontend/src/AdvertiserConsole.tsx
import React from 'react';
import { usePolling } from './hooks/usePolling';
import { AD_FEED_ENDPOINT, INSIGHT_FEED_ENDPOINT } from './config';
import { AdSlot } from './components/ui/AdSlot';
import InsightSlot from './components/ui/InsightSlot';
import { Container, Title, Section, SectionTitle, Grid } from './components/StyledComponents';
import { Ad, Insight } from './types'; // Import types from the new central file

const AdvertiserConsole: React.FC = () => {
  // Fetch ads using the usePolling hook
  const { data: ads, isLoading: isLoadingAds, error: adsError } = usePolling<Ad>(AD_FEED_ENDPOINT, 5000);

  return (
    <Container>
      <Title>Advertiser & Insight Console</Title>

      <Section>
        <SectionTitle>Live Ad Feed</SectionTitle>
        {isLoadingAds && <p>Loading ads...</p>}
        {adsError && <p>Error loading ads: {adsError.message}</p>}
        <Grid>
          {ads.map((ad) => (
            <AdSlot
              key={ad.id}
              title={ad.title}
              content={ad.content}
              callToAction={ad.call_to_action}
            />
          ))}
        </Grid>
      </Section>
    </Container>
  );
};

export default AdvertiserConsole;
