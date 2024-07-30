import React, { useEffect, useState } from 'react';
import styles from '../styles/NexradRegionMap.module.css';

interface NexradRegionMapProps {
  site_code: string;
  interval: number;
}

const NexradRegionMap: React.FC<NexradRegionMapProps> = ({ site_code, interval }) => {
  const [images, setImages] = useState<string[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [zoomedIn, setZoomedIn] = useState(false);

  useEffect(() => {
    const fetchImages = async () => {
      try {
        const response = await fetch(`/api/getNexradImages?site_code=${site_code}&variable_name=reflectivity`);
        if (response.ok) {
          const data = await response.json();
          if (data.images) {
            setImages(data.images);
          }
        } else {
          console.error('Failed to fetch images');
        }
      } catch (error) {
        console.error('Error fetching images:', error);
      }
    };

    fetchImages();
  }, [site_code]);

  useEffect(() => {
    if (images.length > 0) {
      const timer = setInterval(() => {
        setCurrentImageIndex((prevIndex) => (prevIndex + 1) % images.length);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [images, interval]);

  const handleZoomToggle = () => {
    setZoomedIn(!zoomedIn);
  };

  if (images.length === 0) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.container}>
      {/* <div className={styles.controls}>
        <button className={styles.button} onClick={handleZoomToggle}>
          {zoomedIn ? 'Zoom Out' : 'Zoom In'}
        </button>
      </div> */}
      <img
        src={images[currentImageIndex]}
        alt={`Image ${currentImageIndex}`}
        className={`${styles.image} ${zoomedIn ? styles['zoom-in'] : styles['zoom-out']}`}
      />
      <div className={styles.timeDisplay}>
        Time: {new Date().toISOString()}
      </div>
    </div>
  );
};

export default NexradRegionMap;
