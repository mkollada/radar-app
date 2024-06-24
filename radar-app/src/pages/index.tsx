// pages/index.tsx
import { useState } from 'react';

import styles from '../styles/Home.module.css'; // Importing the CSS module for styling


import {USMap, GlobalMap} from '@/components/TileMap';

const Home: React.FC = () => {
  const [mapType, setMapType] = useState<'GFS_precipitation' | 'MRMS_precipitation' >('GFS_precipitation');

  const renderMap = () => {
    switch (mapType) {
      case 'GFS_precipitation':
        return <GlobalMap directory='GFS_precipitation' />
      case 'MRMS_precipitation':
        return <USMap directory='MRMS_precipitation' />
      default:
        return null;
    }
  };

  return (
    <div className={styles.button_container}>
      <div>
        <button className={styles.button} onClick={() => {
          setMapType('GFS_precipitation')
          }}>Global Precipitation Radar Map</button>
        <button className={styles.button} onClick={() => {
          setMapType('MRMS_precipitation')
          }}>US Precipitation Radar Map</button>
      </div>
      {renderMap()}
    </div>
  );
};

export default Home;
