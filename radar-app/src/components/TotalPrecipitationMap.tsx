import React from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

const TotalPrecipitationMap = () => {
  return (
    <MapContainer center={[0, 0]} zoom={2} maxZoom={7} style={{ height: '100vh', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <TileLayer
        url="/tiles/total_precipitation/{z}/{x}/{y}.png"
        attribution="&copy; Your Attribution Here"
        opacity={0.5}
      />
    </MapContainer>
  );
};

export default TotalPrecipitationMap;
