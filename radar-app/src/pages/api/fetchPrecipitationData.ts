// pages/api/fetchPrecipitationData.ts
import type { NextApiRequest, NextApiResponse } from 'next';

const GPM_API_URL = 'https://pmmpublisher.pps.eosdis.nasa.gov/opensearch?q=';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { measurement, count, lat, lon, startTime, endTime } = req.query;

  if (!measurement) {
    res.status(400).json({ error: 'Missing measurement parameter' });
    return;
  }

  if (!count) {
    res.status(400).json({ error: 'Missing count parameter' });
    return;
  }

  if (!lat) {
    res.status(400).json({ error: 'Missing lat parameter' });
    return;
  }

  if (!lon) {
    res.status(400).json({ error: 'Missing lon parameter' });
    return;
  }

  if (!startTime) {
    res.status(400).json({ error: 'Missing startTime parameter' });
    return;
  }

  if (!endTime) {
    res.status(400).json({ error: 'Missing endTime parameter' });
    return;
  }

  const GPM_API_URL_WITH_PARAMS = `${GPM_API_URL}${measurement}&lat=${lat}&lon=${lon}&limit=${count}&startTime=${startTime}&endTime=${endTime}`;

  try {
    console.log('Trying to download inventory');

    const response = await fetch(GPM_API_URL_WITH_PARAMS);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const items = data.items;

    console.log('Downloaded inventory');

    const geojsonData = await Promise.all(
      items.map(async (item: any) => {
        console.log('Item actions:', item.action);

        const exportAction = item.action.find((action: any) => action.displayName === 'export');
        if (!exportAction) {
          throw new Error('Export action not found');
        }

        const geojsonUsing = exportAction.using.find((use: any) => use.mediaType === 'application/json');
        if (!geojsonUsing) {
          throw new Error('GeoJSON URL not found in export action');
        }

        const geojsonUrl = geojsonUsing.url;
        console.log(`Downloading ${geojsonUrl}`);
        const geojsonResponse = await fetch(geojsonUrl);
        if (!geojsonResponse.ok) {
          throw new Error(`HTTP error! status: ${geojsonResponse.status}`);
        }
        const geojsonData = await geojsonResponse.json();
        console.log(`${geojsonUrl} downloaded`);
        return geojsonData;
      })
    );

    res.status(200).json({ geojsonData });
  } catch (error) {
    console.error('Error fetching data:', error);
    res.status(500).json({ error: 'Failed to fetch data' });
  }
}
