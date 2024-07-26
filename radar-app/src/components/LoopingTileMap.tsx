import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import styles from '../styles/PrecipitationMap.module.css';
import {ColorLegend, LegendColor} from './ColorLegend';

const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

interface LoopingTileMapProps {
  directories: string[];
  interval: number;
  legendColors: LegendColor[]
}

export const USLoopingTileMap: React.FC<LoopingTileMapProps> = ({ directories, interval, legendColors }) => {
  const [currentDirectoryIndex, setCurrentDirectoryIndex] = useState(0);

  useEffect(() => {
    if (directories.length > 0) {
      const timer = setInterval(() => {
        setCurrentDirectoryIndex((prevIndex) => (prevIndex + 1) % directories.length);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [directories, interval]);

  useEffect(() => {
    console.log(directories[currentDirectoryIndex])
  }, [currentDirectoryIndex])

  if (directories.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.mapContainer}>
      <ColorLegend legendColors={legendColors} />
      <MapContainer
        center={[37.8, -96.9]} // Center over the US
        zoom={4} // Appropriate zoom level for the US
        minZoom={3}
        maxZoom={5}
        className={styles.map}
        worldCopyJump={true}
        maxBounds={[[50, -125], [24, -66.9]]} // Set max bounds for the continental US
        maxBoundsViscosity={1.0} // Makes panning to edges smoother
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {directories.map((dir, index) => (
          <TileLayer
            url={`/tiles/${dir}/{z}/{x}/{y}.png`}
            attribution="&copy; MRMS Data Contributors"
            key={dir}
            opacity={index === currentDirectoryIndex ? 1 : 0}
          />
        ))}
      </MapContainer>
    </div>
  );
};



export const GlobalLoopingTileMap: React.FC<LoopingTileMapProps> = ({ directories, interval, legendColors }) => {
  const [currentDirectoryIndex, setCurrentDirectoryIndex] = useState(0);

  useEffect(() => {
    if (directories.length > 0) {
      const timer = setInterval(() => {
        setCurrentDirectoryIndex((prevIndex) => (prevIndex + 1) % directories.length);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [directories, interval]);

  useEffect(() => {
    console.log(directories[currentDirectoryIndex])
  }, [currentDirectoryIndex])

  if (directories.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.mapContainer}>
      <ColorLegend legendColors={legendColors} />
      <MapContainer
        center={[0, 0]} // Center over the US
        zoom={3} // Appropriate zoom level for the US
        minZoom={2}
        maxZoom={5}
        className={styles.map}
        worldCopyJump={true}
        maxBounds={[[85, -180], [-85, 180]]} // Set max bounds to prevent wrapping
        maxBoundsViscosity={1.0} // Makes panning to edges smoother
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {directories.map((dir, index) => (
          <TileLayer
            url={`/tiles/${dir}/{z}/{x}/{y}.png`}
            attribution="&copy; MRMS Data Contributors"
            key={dir}
            opacity={index === currentDirectoryIndex ? 1 : 0}
          />
        ))}
      </MapContainer>
    </div>
  );
};
