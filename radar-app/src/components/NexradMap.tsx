import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

// Dynamically import components from react-leaflet with ssr: false
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });

const NexradMap = () => {
  const [leaflet, setLeaflet] = useState<any>(null);
  const [stations, setStations] = useState<any[]>([]);
  const [selectedStation, setSelectedStation] = useState<null | string>(null);
  const [overlayImage, setOverlayImage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Ensure this code runs only on the client side
    if (typeof window !== 'undefined') {
      import('leaflet').then((L) => {
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
          iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
          shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
        });

        setLeaflet(L);
      });

      // Fetch the JSON data
      fetch('/nexrad_stations.json')
        .then((response) => response.json())
        .then((data) => setStations(data))
        .catch((error) => console.error('Error fetching the NEXRAD stations:', error));
    }
  }, []);

  const handleMarkerClick = (stationId: string) => {
    setSelectedStation(stationId);
    setLoading(true);
    console.log(stationId);
    fetch(`/api/updateNexradData?site_code=${stationId}&variable_name=reflectivity`)
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        const imageUrl = data.imageUrl; // Update this with the correct key from your response
        console.log(imageUrl);
        console.log('---------');
        setOverlayImage('/nexrad/' + imageUrl);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching the update data:', error);
        setLoading(false);
      });
  };

  const handleMapClick = () => {
    setOverlayImage(null);
    setSelectedStation(null);
  };

  if (!leaflet) {
    return <div>Loading map...</div>;
  }

  return (
    <MapContainer center={[37.8, -96]} zoom={4} style={{ height: '100vh', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {stations.map((station) => (
        <Marker
          key={station.id}
          position={[station.latitude, station.longitude]}
          eventHandlers={{
            click: (e) => {
              e.originalEvent.stopPropagation();
              handleMarkerClick(station.id);
            },
          }}
        >
          <Popup>
            <strong>{station.name}</strong>
            <br />
            {station.id}
          </Popup>
        </Marker>
      ))}
      {selectedStation && (
        <div className="overlay" onClick={() => setSelectedStation(null)}>
          {loading ? (
            <div className="loading">
              <div className="spinner"></div> Loading...
            </div>
          ) : (
            overlayImage && <img src={overlayImage} alt={selectedStation} className="overlay-image" />
          )}
        </div>
      )}
      <style jsx>{`
        .overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .overlay-image {
          max-width: 100%;
          max-height: 100%;
        }

        .loading {
          color: white;
          font-size: 1.5em;
          display: flex;
          align-items: center;
        }

        .spinner {
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          width: 24px;
          height: 24px;
          animation: spin 1s linear infinite;
          margin-right: 8px;
        }

        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </MapContainer>
  );
};

export default NexradMap;
