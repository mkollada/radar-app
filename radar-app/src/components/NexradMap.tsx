import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

// Dynamically import components from react-leaflet with ssr: false
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });

const NexradMap = ({ onSelectSite }: { onSelectSite: (siteCode: string) => void }) => {
  const [leaflet, setLeaflet] = useState<any>(null);
  const [stations, setStations] = useState<any[]>([]);
  const [tileDir, setTileDir] = useState<string | null>(null);

  useEffect(() => {
    // Ensure this code runs only on the client side
    if (typeof window !== 'undefined') {
      import('leaflet').then((L) => {
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
          iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
          shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
        });

        const customIcon = new L.Icon({
          iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
          iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
          iconSize: [15, 24], // Set the size of the icon (smaller size)
          iconAnchor: [7, 24], // Set the anchor point of the icon
          popupAnchor: [1, -20], // Set the anchor point of the popup
          shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
          shadowSize: [24, 24], // Set the size of the shadow
        });

        setLeaflet({ L, customIcon });
      });

      // Fetch the JSON data for stations
      fetch('/nexrad_stations.json')
        .then((response) => response.json())
        .then((data) => setStations(data))
        .catch((error) => console.error('Error fetching the NEXRAD stations:', error));

      // Fetch the most recent MRMS tiles directory
      fetch('/api/getMostRecentMRMS')
        .then((response) => response.json())
        .then((data) => setTileDir(data.tileDir))
        .catch((error) => console.error('Error fetching the most recent MRMS tiles:', error));
    }
  }, []);

  const handleMarkerClick = (stationId: string) => {
    onSelectSite(stationId);
  };

  if (!leaflet || !tileDir) {
    return <div>Loading map...</div>;
  }

  return (
    <MapContainer center={[37.8, -96]} zoom={4} style={{ height: '100vh', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <TileLayer
        url={`${tileDir}/{z}/{x}/{y}.png`}
        attribution='&copy; MRMS'
      />
      {stations.map((station) => (
        <Marker
          key={station.id}
          position={[station.latitude, station.longitude]}
          icon={leaflet.customIcon}
          eventHandlers={{
            click: () => handleMarkerClick(station.id),
          }}
        >
          <Popup>
            <strong>{station.name}</strong>
            <br />
            {station.id}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default NexradMap;
