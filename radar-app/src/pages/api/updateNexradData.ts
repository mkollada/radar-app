// pages/api/getSubdirectories.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  
  const { site_code, variable_name } = req.query;
  
  const python_server_url = 'http://127.0.0.1:5000/update-nexrad-site/'
  console.log(python_server_url)

  if (site_code) {
    return res.status(400).json({ error: 'data_source parameter is required' });
  } 

  console.log(0)

  if (!variable_name) {
    return res.status(400).json({ error: 'data_type_name parameter is required' });
  } 

  console.log(1)

  try {
    const python_update_data_url = python_server_url + site_code + '/' + variable_name
    console.log(python_update_data_url)
    const response  = await fetch( 
        python_update_data_url
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    } else {
      const data = await response.json()
      return res.status(200).json(data)
    }

  } catch (error) {
    res.status(500).json({ error: 'Failed to read directory' });
  }
}
