import { useState, useEffect } from 'react';
import styles from '../styles/Home.module.css'; // Importing the CSS module for styling

import { USMap, GlobalMap } from '@/components/TileMap';
import { LoopingTileMap } from '@/components/LoopingTileMap';
import NexradMap from '@/components/NexradMap';

type UpdateDataResponse = {
  dataLocs: {
    [dataSource: string]: {
      [dataType: string]: string[];
    };
  };
};

const Home: React.FC = () => {
  const [mapType, setMapType] = useState<
  'MRMS_SeamlessHSR' | 'MRMS_PrecipRate' | 'MRMS_MergedReflectivityComposite' | 'NEXRAD_reflectivity'
  >('MRMS_PrecipRate');
  const [dataLocs, setDataLocs] = useState<UpdateDataResponse['dataLocs']>({
    'mrms':{
      'PrecipRate':[],
      'SeamlessHSR':[]
    }
});

  const updateData = async () => {
    const response = await fetch(`/api/updateData`);
    console.log(response)
    if (response.ok) {
      const data: UpdateDataResponse = await response.json();
      if (data.dataLocs) {
        setDataLocs(data.dataLocs);
      }
    } else {
      console.error(
        '/update-data call failed'
      )
    }
  };

  useEffect(() => {
    updateData();

    const updateInterval = setInterval(() => {
      updateData();
    }, 120000); // 2 minutes

    return () => clearInterval(updateInterval);
  }, []);

  const renderMap = () => {
    switch (mapType) {
      case 'MRMS_SeamlessHSR':
        return <LoopingTileMap directories={dataLocs['mrms']['SeamlessHSR']} interval={2000} />;
      case 'MRMS_PrecipRate':
        return <LoopingTileMap directories={dataLocs['mrms']['PrecipRate']} interval={2000} />;
      case 'MRMS_MergedReflectivityComposite':
        return <LoopingTileMap directories={dataLocs['mrms']['MergedReflectivityComposite']} interval={2000} />;
      case 'NEXRAD_reflectivity':
        return <NexradMap />
      default:
        return null;
    }
  };

  return (
    <div className={styles.button_container}>
      <div>
        <button className={styles.button} onClick={() => setMapType('MRMS_SeamlessHSR')}>MRMS - SeamlessHSR</button>
        <button className={styles.button} onClick={() => setMapType('MRMS_PrecipRate')}>MRMS - PrecipRate</button>
        <button className={styles.button} onClick={() => setMapType('MRMS_MergedReflectivityComposite')}>MRMS - MergedReflectivityComposite</button>
        <button className={styles.button} onClick={() => setMapType('NEXRAD_reflectivity')}>NEXRAD - Reflectivity</button>
      </div>
      {renderMap()}
    </div>
  );
};

export default Home;
