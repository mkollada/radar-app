import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import styles from '../styles/PrecipitationMap.module.css'; // Importing the CSS module for styling

// Dynamically import MapContainer, TileLayer, and GeoJSON from react-leaflet
const MapContainer = dynamic(
  () => import('react-leaflet').then(mod => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then(mod => mod.TileLayer),
  { ssr: false }
);
const GeoJSON = dynamic(
  () => import('react-leaflet').then(mod => mod.GeoJSON),
  { ssr: false }
);

let L: typeof import('leaflet');

interface MapProps {
  geojsonData: GeoJSON.FeatureCollection[];
  metarData: any[];
  fileType: 'geotiff' | 'geojson' | 'metar';
}

const PrecipitationMap: React.FC<MapProps> = ({ geojsonData, metarData, fileType }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (geojsonData.length > 0) {
      const interval = setInterval(() => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % geojsonData.length);
      }, 500); // Change every 3 seconds

      return () => clearInterval(interval);
    }
  }, [geojsonData]);

  useEffect(() => {
    if (fileType === 'metar' && metarData.length > 0) {
      import('leaflet').then(leaflet => {
        L = leaflet;
        const map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors',
        }).addTo(map);

        metarData.forEach((entry) => {
          const { stationId, windSpeed, lat, lon } = entry;
          if (lat && lon) {
            L.marker([lat, lon]).addTo(map).bindPopup(`Station: ${stationId}, Wind Speed: ${windSpeed}KT`);
          }
        });

        return () => {
          map.remove();
        };
      });
    }
  }, [metarData, fileType]);

  return (
    <div className={styles.mapContainer}>
      {fileType === 'geojson' && geojsonData.length > 0 && (
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
          <GeoJSON key={currentIndex} data={geojsonData[currentIndex]} />
        </MapContainer>
      )}
      {fileType === 'metar' && metarData.length > 0 && <div id="map" className={styles.map} />}
    </div>
  );
};

export default PrecipitationMap;
