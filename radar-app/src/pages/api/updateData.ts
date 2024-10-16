// pages/api/updateData.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  
  // const { data_source, data_type_name } = req.query;
  console.log('here')
  
  const python_server_url = 'http://127.0.0.1:5000/update-data'
  console.log(python_server_url)


  try {
    const python_update_data_url = python_server_url // + data_source + '/' + data_type_name
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
