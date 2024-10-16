import logging
import os
from typing import List
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime, timedelta, timezone

from classes import GeoDataFile
from data_source import DataSource
from utils.data_to_tiles import process_zipped_grib2_to_tiles


class MRMSDataSource(DataSource):
    def __init__(
            self, 
            raw_data_folder='./data/raw/mrms', 
            processed_data_folder='../radar-app/public/tiles/mrms',
            time_delta: timedelta = timedelta(hours=1),
        ):
        super().__init__(raw_data_folder, processed_data_folder, time_delta)
        self.processed_data_folder = processed_data_folder
        self.raw_data_folder = raw_data_folder

        self.base_url = 'https://mrms.ncep.noaa.gov/data/2D/'
        self.variable_name = 'Reflectivity_0C'
        self.variable_url = os.path.join(self.base_url, self.variable_name)
        self.processed_variable_data_dir = os.path.join(processed_data_folder, self.variable_name)
        self.color_relief_file = './assets/color_reliefs/Reflectivity_0C_color_relief.txt'
        self.processed_files = []
        self.init_processed_files()

    # Creates geo_data_files for all dirs in self.processed_data_folder
    def init_processed_files(self):
        os.makedirs(self.processed_variable_data_dir, exist_ok=True)
        
        logging.info('Initializing processed_files...')
        for dir in os.listdir(self.processed_variable_data_dir):
            datetime = self.extract_datetime_from_name(dir)
            geo_data_file = GeoDataFile(
                datetime=datetime,
                remote_path='',
                local_path='',
                processed_loc=os.path.join(
                    self.processed_variable_data_dir,
                    dir 
                ),
                key=dir
            )

            self.processed_files.append(geo_data_file)
        logging.info('processed_files initialized.')
    
    def extract_datetime_from_name(self, name: str):
        try:
            parts = name.split('_')
            date_part = parts[-1].split('.')[0]
            extracted_datetime = datetime.strptime(date_part, '%Y%m%d-%H%M%S')
            extracted_datetime = extracted_datetime.replace(tzinfo=timezone.utc)

            return extracted_datetime
        except (IndexError, ValueError) as e:
            logging.error(f"Error parsing date from {name}: {e}")
            return datetime.min

    def fetch_data_files(self) -> List[GeoDataFile]:
        response = requests.get(self.variable_url)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        
        geo_data_files: List[GeoDataFile] = []
        for link in links:
            href = link.get('href')
            if href.endswith('.gz') and 'latest' not in href:
                try:
                    file_datetime = self.extract_datetime_from_name(href)
                    key = href.split(self.variable_url)[-1]
                    file = GeoDataFile(
                        datetime=file_datetime,
                        remote_path=os.path.join(self.variable_url,href),
                        key=key,
                        local_path='',
                        processed_loc=''
                    )
                    geo_data_files.append(file)
                except Exception as e:
                    logging.error(f"Error createing Geo Data File date from {href}: {e}")

        self.sort_processed_files()
        # recent_geo_data_files = geo_data_files[-self.n_files:]

        return geo_data_files

    def download_file(self, geo_data_file: GeoDataFile) -> GeoDataFile | None:
        if not os.path.exists(self.processed_data_folder):
            os.makedirs(self.processed_data_folder)
        
        download_path = self.get_download_path(geo_data_file)

        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        logging.info(f'Downloading {geo_data_file.remote_path} to {download_path}')


        response = requests.get(geo_data_file.remote_path, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            with open(download_path, 'wb') as f, tqdm(
                desc=download_path,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=1024):
                    size = f.write(chunk)
                    bar.update(size)
            geo_data_file.local_path = download_path
            return geo_data_file
            
        else:
            logging.error(f"Failed to download file: {geo_data_file.remote_path}")
            return None

    def process_file(self, geo_data_file: GeoDataFile) -> GeoDataFile | None:

        output_dir = self.get_processed_loc(geo_data_file)
        os.makedirs(output_dir, exist_ok=True)
        try:
            success = process_zipped_grib2_to_tiles(
                geo_data_file.local_path,
                'unknown',
                None,
                output_tiles=output_dir,
                color_relief_file=self.color_relief_file,
                target_crs='EPSG:3857',
                filter_grib=False
            )
            geo_data_file.processed_loc = output_dir

            if not success:
                geo_data_file.remove_processed_loc()
                return None
        except Exception as e:
            logging.error(f'Error processing {geo_data_file.local_path} to tiles:', e)
            return None
        
        

        return geo_data_file
