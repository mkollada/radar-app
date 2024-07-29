// pages/api/getMostRecentMRMS.ts
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
   try {
        const python_server_url = 'http://127.0.0.1:5000/get-most-recent-mrms'
        console.log(python_server_url)

        const response = await fetch(python_server_url)

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        } else {
        const data = await response.json()
        return res.status(200).json(data)
        }
    } catch (error) {
        res.status(500).json({ error: 'Failed to get data from python server: /update-gpm-data' });
    }
};

