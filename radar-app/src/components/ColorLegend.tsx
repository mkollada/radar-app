import React from 'react';
import styles from '../styles/PrecipitationMap.module.css';

export interface LegendColor {
  value: number;
  color: string;
}

interface ColorLegendProps {
  legendColors: LegendColor[];
}

export const ColorLegend: React.FC<ColorLegendProps> = ({ legendColors }) => {
  const gradientColors = legendColors.map(color => color.color).join(', ');
  return (
    <div className={styles.legendContainer}>
      <div className={styles.legendGradient} style={{ background: `linear-gradient(${gradientColors})` }}></div>
      <div className={styles.legendLabels}>
        {legendColors.map((item, index) => (
          <div key={index} className={styles.legendLabel}>
            {item.value}
          </div>
        ))}
      </div>
    </div>
  );
};