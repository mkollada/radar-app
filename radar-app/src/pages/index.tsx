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
  const [mapType, setMapType] = useState<'MRMS_Reflectivity_0C' | 'NEXRAD_reflectivity' | 'GPM_PrecipRate'
  >('MRMS_Reflectivity_0C');
  const [dataLocs, setDataLocs] = useState<UpdateDataResponse['dataLocs']>({
    'mrms':{
      'Reflectivity_0C':[],
      'SeamlessHSR':[]
    }
});

  const [gpmDirs, setGpmDirs] = useState<string[]>([])

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

  const updateData = async () => {
    const response = await fetch(`/api/updateData`);
    if (response.ok) {
      const data: UpdateDataResponse = await response.json();
      if (data.dataLocs) {
        setDataLocs(data.dataLocs);
      }
    } else {
      console.error(
        '/updateData call failed'
      )
    }
  };

  // Setting timers for updating each of the data types
  useEffect(() => {
    // updateGPMData()
    updateData()

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
      // case 'MRMS_SeamlessHSR':
      //   return <USLoopingTileMap directories={dataLocs['mrms']['SeamlessHSR']} interval={500} />;
      case 'MRMS_Reflectivity_0C':
        return <USLoopingTileMap directories={dataLocs['mrms']['Reflectivity_0C']} interval={1000} />;
      // case 'MRMS_MergedReflectivityComposite':
      //   return <LoopingTileMap directories={dataLocs['mrms']['MergedReflectivityComposite']} interval={2000} />;
      case 'NEXRAD_reflectivity':
        return <NexradMap />
      case 'GPM_PrecipRate':
        return <GlobalLoopingTileMap directories={gpmDirs} interval={500}/>
      default:
        return null;
    }
  };

  return (
    <div className={styles.button_container}>
      <div>
        {/* <button className={styles.button} onClick={() => setMapType('MRMS_SeamlessHSR')}>MRMS - SeamlessHSR</button> */}
        <button className={styles.button} onClick={() => setMapType('MRMS_Reflectivity_0C')}>MRMS - Reflectivity_0C</button>
        {/* <button className={styles.button} onClick={() => setMapType('MRMS_MergedReflectivityComposite')}>MRMS - MergedReflectivityComposite</button> */}
        <button className={styles.button} onClick={() => setMapType('NEXRAD_reflectivity')}>NEXRAD - Reflectivity</button>
        <button className={styles.button} onClick={() => setMapType('GPM_PrecipRate')}>GPM - Global Precipitation</button>
      </div>
      {renderMap()}
    </div>
  );
};

export default Home;
