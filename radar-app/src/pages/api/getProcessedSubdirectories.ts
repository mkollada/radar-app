// pages/api/getSubdirectories.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { directory } = req.query;

  console.log('here')
  console.log(process.cwd())
  

  if (!directory) {
    return res.status(400).json({ error: 'Directory parameter is required' });
  }

  try {
    const absolutePath = path.join(
      process.cwd(), 'public', 'tiles', directory as string
    );
    const subdirectories = fs.readdirSync(absolutePath).filter(subdir => {
      return fs.statSync(path.join(absolutePath, subdir)).isDirectory();
    });

    res.status(200).json({ subdirectories });
  } catch (error) {
    res.status(500).json({ error: 'Failed to read directory' });
  }
}
