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

  useEffect(() => {
    updateGPMData();
    updateMRMSData();

    const updateMRMSInterval = setInterval(() => {
      updateMRMSData();
    }, 120000); // 2 minutes

    const updateGPMInterval = setInterval(() => {
      updateGPMData();
    }, 1800000); // 30 minutes

    return () => {
      clearInterval(updateMRMSInterval);
      clearInterval(updateGPMInterval);
    };
  }, []);

  const gpmLegendColors = [
    { value: 0.0, color: 'rgba(0, 0, 0, 0)' },          // Transparent
    { value: 0.1, color: 'rgba(144, 238, 144, 1)' },    // Light Green for very light rain
    { value: 2.5, color: 'rgba(0, 100, 0, 1)' },        // Dark Green for light rain
    { value: 5.0, color: 'rgba(255, 255, 0, 1)' },      // Yellow for moderate rain
    { value: 10.0, color: 'rgba(255, 165, 0, 1)' },     // Orange for heavy rain
    { value: 20.0, color: 'rgba(255, 0, 0, 1)' },       // Red for very heavy rain
    { value: 50.0, color: 'rgba(128, 0, 128, 1)' },     // Purple for intense rain
    { value: 100.0, color: 'rgba(75, 0, 130, 1)' }      // Dark Purple for extreme rain
  ];

  const mrmsLegendColors = [
    { value: 0.0, color: 'rgba(0, 0, 0, 0)' },          // Transparent for no reflectivity
    { value: 10.0, color: 'rgba(144, 238, 144, 1)' },   // Light green for low reflectivity
    { value: 20.0, color: 'rgba(0, 100, 0, 1)' },       // Dark green for moderate reflectivity
    { value: 30.0, color: 'rgba(255, 255, 0, 1)' },     // Yellow for higher reflectivity
    { value: 40.0, color: 'rgba(255, 165, 0, 1)' },     // Orange for intense reflectivity
    { value: 50.0, color: 'rgba(255, 0, 0, 1)' },       // Red for very intense reflectivity
    { value: 65.0, color: 'rgba(139, 0, 139, 1)' }      // Dark magenta for extreme rain or hail
  ];
  
  

  const renderMap = () => {
    switch (mapType) {
      case 'MRMS_Reflectivity_0C':
        return <USLoopingTileMap directories={mrmsDirs} interval={200} legendColors={mrmsLegendColors}/>;
      case 'NEXRAD_reflectivity':
        return <NexradMap />
      case 'GPM_PrecipRate':
        return <GlobalLoopingTileMap directories={gpmDirs} interval={500} legendColors={gpmLegendColors}/>
      case 'Satellite':
        return <GlobalLoopingTileMap directories={satDirs} interval={500} legendColors={mrmsLegendColors}/>
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
