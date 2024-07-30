import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import styles from '../styles/PrecipitationMap.module.css';
import { ColorLegend, LegendColor } from './ColorLegend';

const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

interface LoopingTileMapProps {
  directories: Record<string, string>;
  interval: number;
  legendColors: LegendColor[];
  maxBounds: [[number, number], [number, number]];
}

export const USLoopingTileMap: React.FC<LoopingTileMapProps> = ({ directories, interval, legendColors, maxBounds }) => {
  const [currentDirectoryIndex, setCurrentDirectoryIndex] = useState(0);
  const [satelliteView, setSatelliteView] = useState(false);
  const directoryEntries = Object.entries(directories);

  useEffect(() => {
    if (directoryEntries.length > 0) {
      const timer = setInterval(() => {
        setCurrentDirectoryIndex((prevIndex) => (prevIndex + 1) % directoryEntries.length);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [directoryEntries, interval]);

  useEffect(() => {
    console.log('Current directory US:')
    console.log(directoryEntries[currentDirectoryIndex]);
  }, [currentDirectoryIndex, directoryEntries]);

  if (directoryEntries.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.mapContainer}>
      <ColorLegend legendColors={legendColors} />
      <button onClick={() => setSatelliteView(!satelliteView)}>
        {satelliteView ? 'Switch to Default View' : 'Switch to Satellite View'}
      </button>
      <MapContainer
        center={[37.8, -96.9]} // Center over the US
        zoom={4} // Appropriate zoom level for the US
        minZoom={3}
        maxZoom={5}
        className={styles.map}
        worldCopyJump={true}
        maxBounds={maxBounds} // Use the maxBounds prop
        maxBoundsViscosity={1.0} // Makes panning to edges smoother
      >
        {satelliteView ? (
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />
        ) : (
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
          />
        )}
        {directoryEntries.map(([key, dir], index) => (
          <TileLayer
            url={`/tiles/${dir}/{z}/{x}/{y}.png`}
            attribution="&copy; MRMS Data Contributors"
            key={dir}
            opacity={index === currentDirectoryIndex ? 1 : 0}
          />
        ))}
      </MapContainer>
      <div className={styles.timeDisplay}>
        Time: {directoryEntries[currentDirectoryIndex][0]}
      </div>
    </div>
  );
};

export const GlobalLoopingTileMap: React.FC<LoopingTileMapProps> = ({ directories, interval, legendColors, maxBounds }) => {
  const [currentDirectoryIndex, setCurrentDirectoryIndex] = useState(0);
  const [satelliteView, setSatelliteView] = useState(false);
  const directoryEntries = Object.entries(directories);

  useEffect(() => {
    if (directoryEntries.length > 0) {
      const timer = setInterval(() => {
        setCurrentDirectoryIndex((prevIndex) => (prevIndex + 1) % directoryEntries.length);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [directoryEntries, interval]);

  useEffect(() => {
    console.log('Current directory Global:')
    console.log(directoryEntries[currentDirectoryIndex]);
  }, [currentDirectoryIndex, directoryEntries]);

  if (directoryEntries.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.mapContainer}>
      <ColorLegend legendColors={legendColors} />
      <button onClick={() => setSatelliteView(!satelliteView)}>
        {satelliteView ? 'Switch to Default View' : 'Switch to Satellite View'}
      </button>
      <MapContainer
        center={[0, 0]} // Center over the globe
        zoom={3} // Appropriate zoom level for the globe
        minZoom={2}
        maxZoom={5}
        className={styles.map}
        worldCopyJump={true}
        maxBounds={maxBounds} // Use the maxBounds prop
        maxBoundsViscosity={1.0} // Makes panning to edges smoother
      >
        {satelliteView ? (
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />
        ) : (
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
          />
        )}
        {directoryEntries.map(([key, dir], index) => (
          <TileLayer
            url={`/tiles/${dir}/{z}/{x}/{y}.png`}
            attribution="&copy; MRMS Data Contributors"
            key={dir}
            opacity={index === currentDirectoryIndex ? 1 : 0}
          />
        ))}
      </MapContainer>
      <div className={styles.timeDisplay}>
        Time: {directoryEntries[currentDirectoryIndex][0]}
      </div>
    </div>
  );
};
