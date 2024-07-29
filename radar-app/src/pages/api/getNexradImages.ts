// pages/api/getNexradImages.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

const getNexradImages = (req: NextApiRequest, res: NextApiResponse) => {
    console.log('bop')
    const { site_code, variable_name } = req.query;
    const imagesDir = path.join(process.cwd(), 'public', 'nexrad', variable_name as string, site_code as string);
    console.log('here')
    fs.readdir(imagesDir, (err, files) => {
        if (err) {
        return res.status(500).json({ error: 'Failed to read directory' });
        }

        const images = files
        .filter(file => file.endsWith('.png'))
        .map(file => `/nexrad/${variable_name}/${site_code}/${file}`);

        res.status(200).json({ images });
    });
};

export default getNexradImages;
