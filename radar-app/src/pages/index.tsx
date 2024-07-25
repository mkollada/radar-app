import { useState, useEffect } from 'react';
import styles from '../styles/Home.module.css'; // Importing the CSS module for styling

import { GlobalLoopingTileMap, USLoopingTileMap } from '@/components/LoopingTileMap';
import NexradMap from '@/components/NexradMap';

type UpdateDataResponse = {
  dataLocs: {
    [dataSource: string]: {
      [dataType: string]: string[];
    };
  };
};

const Home: React.FC = () => {
  const [mapType, setMapType] = useState<'MRMS_Reflectivity_0C' | 'NEXRAD_reflectivity' | 'GPM_PrecipRate' | 'Satellite'
  >('MRMS_Reflectivity_0C');
  

  const [gpmDirs, setGpmDirs] = useState<string[]>([])
  const [mrmsDirs, setMrmsDirs] = useState<string[]>([])
  const [satDirs, setSatDirs] = useState<string[]>([])

  const updateGPMData = async () => {
    const response = await fetch(`/api/updateGPMData`);
    if (response.ok) {
      const data = await response.json();
      if (data.directories) {
        setGpmDirs(data.directories);
      }
    } else {
      console.error(
        '/updateGPMData call failed'
      )
    }
  }

  const updateMRMSData = async () => {
    const response = await fetch(`/api/updateMRMSData`);
    if (response.ok) {
      const data = await response.json();
      if (data.directories) {
        setMrmsDirs(data.directories);
      }
    } else {
      console.error(
        '/updateMRMSData call failed'
      )
    }
  }

  const updateSatelliteData = async () => {
    const response = await fetch(`/api/updateSatelliteData`);
    if (response.ok) {
      const data = await response.json();
      if (data.directories) {
        setSatDirs(data.directories);
      }
    } else {
      console.error(
        '/updateSatelliteData call failed'
      )
    }
  }

  // Setting timers for updating each of the data types
  useEffect(() => {
    // updateGPMData()
    // updateMRMSData()

    updateSatelliteData()


    // const updateInterval = setInterval(() => {
    //   updateData();
    // }, 120000); // 2 minutes

    // const gpmUpdateInterval = setInterval(() => {
    //   updateGPMData()
    // }, 1800000)

    // return () => clearInterval(updateInterval);
  }, []);

  const renderMap = () => {
    switch (mapType) {
      case 'MRMS_Reflectivity_0C':
        return <USLoopingTileMap directories={mrmsDirs} interval={200} />;
      case 'NEXRAD_reflectivity':
        return <NexradMap />
      case 'GPM_PrecipRate':
        return <GlobalLoopingTileMap directories={gpmDirs} interval={500}/>
      case 'Satellite':
        return <GlobalLoopingTileMap directories={satDirs} interval={500}/>
      default:
        return null;
    }
  };

  return (
    <div className={styles.button_container}>
      <div>
        <button className={styles.button} onClick={() => setMapType('MRMS_Reflectivity_0C')}>MRMS - Reflectivity_0C</button>
        <button className={styles.button} onClick={() => setMapType('NEXRAD_reflectivity')}>NEXRAD - Reflectivity</button>
        <button className={styles.button} onClick={() => setMapType('GPM_PrecipRate')}>GPM - Global Precipitation</button>
        <button className={styles.button} onClick={() => setMapType('Satellite')}>Satellite</button>
      </div>
      {renderMap()}
    </div>
  );
};

export default Home;
