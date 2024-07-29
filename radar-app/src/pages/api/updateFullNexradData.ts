// pages/api/updateNexradData.ts
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {


  const python_server_url = 'http://127.0.0.1:5000/update-nexrad-data';

  try {
    const response = await fetch(python_server_url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (error) {
    res.status(500).json({ error: 'Failed to read directory' });
  }
}