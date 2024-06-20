// pages/api/fetchMetarData.ts
import type { NextApiRequest, NextApiResponse } from 'next';

const METAR_API_URL = 'https://tgftp.nws.noaa.gov/data/observations/metar/cycles/';

const metarRegex = /^(METAR|SPECI)\s+(\w{4})\s+(\d{2})(\d{2})(\d{2})Z\s+(\d{3})(\d{2})(G\d{2})?(KT)\s+(\d+(?:SM|\/\d+SM)?)\s+(CLR|FEW|SCT|BKN|OVC|SKC|CAVOK)\s+((?:M?\d{2})\/(?:M?\d{2}))\s+A(\d{4})(.*)$/;

interface Metar {
  type: string;
  stationId: string;
  day: string;
  hour: string;
  minute: string;
  windDirection: string;
  windSpeed: string;
  gust: string | null;
  windUnit: string;
  visibility: string;
  skyCondition: string;
  temperature: string;
  dewPoint: string;
  altimeter: string;
  remarks: string;
}

const parseMetar = (line: string): Metar | null => {
  const match = line.match(metarRegex);
  if (!match) {
    console.log('Failed to match METAR line:', line);
    return null;
  }
  return {
    type: match[1],
    stationId: match[2],
    day: match[3],
    hour: match[4],
    minute: match[5],
    windDirection: match[6],
    windSpeed: match[7],
    gust: match[8] || null,
    windUnit: match[9],
    visibility: match[10],
    skyCondition: match[11],
    temperature: match[12],
    dewPoint: match[13],
    altimeter: match[14],
    remarks: match[15]?.trim() || '',
  };
};

const processMetarData = async (url: string): Promise<Metar[]> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.text();
  const lines = data.split('\n').filter(line => line.trim());
  console.log('METAR lines:', lines);
  return lines.map(parseMetar).filter((entry): entry is Metar => entry !== null);
};

const createTable = (metarData: Metar[]) => {
  const headers = [
    'Type', 'Station ID', 'Day', 'Hour', 'Minute', 
    'Wind Direction', 'Wind Speed', 'Gust', 'Wind Unit', 
    'Visibility', 'Sky Condition', 'Temperature', 'Dew Point', 
    'Altimeter', 'Remarks'
  ];
  const rows = metarData.map(entry => [
    entry.type, entry.stationId, entry.day, entry.hour, entry.minute,
    entry.windDirection, entry.windSpeed, entry.gust, entry.windUnit,
    entry.visibility, entry.skyCondition, entry.temperature, entry.dewPoint,
    entry.altimeter, entry.remarks
  ]);

  return { headers, rows };
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { cycle } = req.query;

  if (!cycle) {
    res.status(400).json({ error: 'Missing cycle parameter' });
    return;
  }

  const METAR_API_URL_WITH_PARAMS = `${METAR_API_URL}${cycle}Z.TXT`;

  try {
    console.log('Trying to download METAR data');

    const metarData = await processMetarData(METAR_API_URL_WITH_PARAMS);
    const table = createTable(metarData);

    res.status(200).json(table);
  } catch (error) {
    console.error('Error fetching METAR data:', error);
    res.status(500).json({ error: 'Failed to fetch METAR data' });
  }
}
