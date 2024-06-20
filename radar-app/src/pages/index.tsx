// pages/index.tsx
import { useEffect, useState } from 'react';
import PrecipitationMap from '@/components/PrecipitationMap';
import MetarMap from '@/components/MetarMap';
import axios from 'axios';
import styles from '../styles/Home.module.css'; // Importing the CSS module for styling


import { FeatureCollection, Geometry, GeoJsonProperties } from 'geojson';
import TileMap from '@/components/TileMap';

const useData = (dataType: 'precipitation' | 'metar' | '') => {
  const [precipGeojsonData, setPrecipGeojsonData] = useState<FeatureCollection<Geometry, GeoJsonProperties>[]>([]);
  const [metarGeojsonData, setMetarGeojsonData] = useState<FeatureCollection<Geometry, GeoJsonProperties>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (dataType === 'precipitation') {
          const response = await axios.get('/api/fetchPrecipitationData', {
            params: {
              count: 5,
              lat: 90,
              lon: 180,
              startTime: '2024-06-17',
              endTime: '2024-06-17',
              measurement: 'precip_30mn',
              file_type: 'geojson',
            },
          });
          setPrecipGeojsonData(response.data.geojsonData);
        } else if (dataType == 'metar'){
          const response = await fetch('http://127.0.0.1:5000/metar');
          console.log(response);
          const data = await response.json();
          setMetarGeojsonData([data]); // Ensure metarGeojsonData is always an array
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [dataType]);

  return { precipGeojsonData, metarGeojsonData, loading };
};

const Home: React.FC = () => {
  const [dataType, setDataType] = useState<'precipitation' | 'metar' | ''>('metar');
  const [mapType, setMapType] = useState<'totalPrecipitation' | 'temperature' | 'humidity' | 'metar' | 'precipitation'>('totalPrecipitation');
  const { precipGeojsonData, metarGeojsonData, loading } = useData(dataType);

  if (loading) {
    return <div>Loading...</div>;
  }

  const renderMap = () => {
    switch (mapType) {
      case 'totalPrecipitation':
        return <TileMap directory='total_precipitation' />
      case 'temperature':
        return <TileMap directory='temperature' />
      case 'humidity':
        return <TileMap directory='humidity' />;
      case 'metar':
        return metarGeojsonData.length ? <MetarMap geojsonData={metarGeojsonData[0]} /> : <div>No METAR data available</div>;
      case 'precipitation':
        return precipGeojsonData.length ? <PrecipitationMap geojsonData={precipGeojsonData} metarData={metarGeojsonData} fileType="geojson" /> : <div>No precipitation data available</div>;
      default:
        return null;
    }
  };

  return (
    <div className={styles.button_container}>
      <div>
        <button className={styles.button} onClick={() => {
          setMapType('totalPrecipitation')
          setDataType('')
          }}>Total Precipitation Map</button>
        <button className={styles.button} onClick={() => {
          setMapType('temperature')
          setDataType('')
          }}>Temperature Map</button>
        <button className={styles.button} onClick={() => {
          setMapType('humidity')
          setDataType('')
          }}>Humidity Map</button>
        <button className={styles.button} onClick={() => {
          setMapType('metar')
          setDataType('metar')
          }}>METAR Wind Data</button>
        <button className={styles.button} onClick={() => {
          setMapType('precipitation')
          setDataType('precipitation')
          }}>Precipitation Data</button>
      </div>
      {renderMap()}
    </div>
  );
};

export default Home;
