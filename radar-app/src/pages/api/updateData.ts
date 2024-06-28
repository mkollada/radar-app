// pages/api/getSubdirectories.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { data_source, variable_name } = req.query;
  
  const python_server_url = 'https://127.0.0.1:5000'

  if (!data_source) {
    return res.status(400).json({ error: 'data_source parameter is required' });
  } else if (typeof data_source != 'string') {
    return res.status(400).json({ error: 'data_source parameter must be a string' });
  }

  if (!variable_name) {
    return res.status(400).json({ error: 'variable_name parameter is required' });
  } else if (typeof variable_name != 'string') {
    return res.status(400).json({ error: 'variable_name parameter must be a string' });
  }

  try {
    const response  = await fetch( 
        path.join(python_server_url, data_source, variable_name)
    )
    if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
    }

  } catch (error) {
    res.status(500).json({ error: 'Failed to read directory' });
  }
}
