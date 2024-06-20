import React from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import styles from '../styles/PrecipitationMap.module.css'; // Importing the CSS module for styling


const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

const TemperatureMap = () => {
  return (
    <div className={styles.mapContainer}>
      <MapContainer
            center={[0, 0]}
            zoom={3}
            className={styles.map}
            worldCopyJump={true}
            maxBounds={[[85, -180], [-85, 180]]} // Set max bounds to prevent wrapping
            maxBoundsViscosity={1.0} // Makes panning to edges smoother
          >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <TileLayer
          url="/tiles/temp2/{z}/{x}/{y}.png"
          attribution="&copy; Your Attribution Here"
          opacity={0.5}
        />
      </MapContainer>
    </div>
  );
};

export default TemperatureMap;
