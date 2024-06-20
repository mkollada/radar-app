import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { GeoJSONProps } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { LatLngExpression } from 'leaflet';

interface MetarMapProps {
  geojsonData: GeoJSONProps['data'];
}

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

const MetarMap: React.FC<MetarMapProps> = ({ geojsonData }) => {
  const [leaflet, setLeaflet] = useState<any>(null);

  useEffect(() => {
    // Ensure this code runs only on the client side
    import('leaflet').then((L) => {
      setLeaflet(L);
    });
  }, []);

  const onEachFeature = (feature: any, layer: any) => {
    if (feature.properties && feature.properties.METAR_FIELD) {
      const popupContent = `METAR Field: ${feature.properties.METAR_FIELD}<br>Wind Speed: ${feature.properties.wind_speed}<br>Wind Direction: ${feature.properties.wind_direction}`;
      layer.bindPopup(popupContent);
    }
  };

  const getColor = (windSpeed: number) => {
    // Interpolate between green (0, 255, 0) and red (255, 0, 0)
    const r = Math.min(255, Math.max(0, Math.floor((windSpeed / 20) * 255)));
    const g = Math.min(255, Math.max(0, Math.floor(255 - (windSpeed / 20) * 255)));
    return `rgb(${r},${g},0)`;
  };

  const pointToLayer = (feature: any, latlng: LatLngExpression) => {
    const windSpeed = feature.properties.wind_speed || 0; // Default to 0 if wind_speed is not available
    const windDirection = feature.properties.wind_direction || 0; // Default to 0 if wind_direction is not available
    const color = getColor(windSpeed);

    const icon = leaflet.divIcon({
      html: `<div style="transform: rotate(${windDirection}deg); color: ${color};">&#x27A1;</div>`,
      className: '',
    });

    return leaflet.marker(latlng, { icon: icon });
  };

  if (!leaflet) {
    return <div>Loading map...</div>;
  }

  return (
    <MapContainer center={[51.505, -0.09]} zoom={4} style={{ height: '100vh', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <GeoJSON
        data={geojsonData}
        onEachFeature={onEachFeature}
        pointToLayer={pointToLayer}
      />
    </MapContainer>
  );
};

export default MetarMap;
