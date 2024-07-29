import React, { useState } from 'react';
import NexradMap from './NexradMap';
import NexradRegionMap from './NexradRegionMap';
import styles from '../styles/NexradPage.module.css';

const NexradPage: React.FC = () => {
  const [view, setView] = useState<'map' | 'region'>('region');
  const [siteCode, setSiteCode] = useState<string>('KTLX');

  const handleSiteChange = (newSiteCode: string) => {
    setSiteCode(newSiteCode);
    setView('region');
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        {view === 'region' ? (
          <button className={styles.button} onClick={() => setView('map')}>Select Site</button>
        ) : (
          <button className={styles.button} onClick={() => setView('region')}>View Region</button>
        )}
      </div>
      <div className={styles.mapContainer}>
        {view === 'region' ? (
          <NexradRegionMap site_code={siteCode} interval={1000} />
        ) : (
          <NexradMap onSelectSite={handleSiteChange} />
        )}
      </div>
    </div>
  );
};

export default NexradPage;
