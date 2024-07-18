// pages/api/updateNexradData.ts
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { site_code, variable_name } = req.query;
  
  if (!site_code) {
    return res.status(400).json({ error: 'site_code parameter is required' });
  } else if (typeof site_code !== 'string') {
    return res.status(400).json({ error: 'site_code parameter must be a string' });
  }

  if (!variable_name) {
    return res.status(400).json({ error: 'variable_name parameter is required' });
  } else if (typeof variable_name !== 'string') {
    return res.status(400).json({ error: 'variable_name parameter must be a string' });
  }

  const python_server_url = 'http://127.0.0.1:5000/update-nexrad-site/';
  const python_update_data_url = `${python_server_url}${site_code}/${variable_name}`;

  try {
    const response = await fetch(python_update_data_url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (error) {
    res.status(500).json({ error: 'Failed to read directory' });
  }
}
