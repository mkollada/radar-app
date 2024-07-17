// pages/api/updateGPMData.ts
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  
  const python_server_url = 'http://127.0.0.1:5000/update-gpm-data'
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
    res.status(500).json({ error: 'Failed to get data from python server: /update-gpm-data' });
  }
}
