from typing import List
from classes import GeoDataFile
from data_source import DataSource
from datetime import datetime, timedelta, timezone
import logging
import requests
import re
import os
import shutil
from utils.data_to_tiles import process_tif_to_tiles

class GPMDataSource(DataSource):
    def __init__(
            self, raw_data_folder: str, 
            processed_data_folder: str, 
            time_delta: timedelta
        ):
        super().__init__(raw_data_folder, processed_data_folder, time_delta)

        self.variable_name = 'precip_30mn'
        self.processed_variable_data_dir = os.path.join(processed_data_folder, self.variable_name)
        self.remote_data_loc = 'https://pmmpublisher.pps.eosdis.nasa.gov/products/s3/'
        self.color_relief_file = './assets/color_reliefs/GPM_color_relief.txt'
        self.base_url='https://pmmpublisher.pps.eosdis.nasa.gov/opensearch'
        self.processed_files: List[GeoDataFile] = []
        self.n_files=15
        self.init_processed_files()
        self.clean_up_processed_files()

    def extract_datetime_from_name(self, name:str):
        # Assuming the filename format is fixed: gpm_30mn.YYYYMMDD.HHMMSS.tif
        try:
            base_name = name.split('.')[1] + name.split('.')[2]
            extracted_datetime = datetime.strptime(base_name, "%Y%m%d%H%M%S")
            extracted_datetime = extracted_datetime.replace(tzinfo=timezone.utc)
            return extracted_datetime
        except (IndexError, ValueError) as e:
            print(f"Error parsing datetime from filename: {e}")
            return None

    def fetch_data_files(self) -> List[GeoDataFile]:
        logging.info('Fetching recent GPM Files...')
        gpm_data_files: List[GeoDataFile] = []
        try:
            today = str(datetime.now(timezone.utc).date())
            yesterday = str((datetime.today() - timedelta(days=1)).date())

            query = f'{self.base_url}?q={self.variable_name}&limit={self.n_files}' + \
                f'&startTime={yesterday}&endTime={today}'
            
            try:
                response = requests.get(query)
            except Exception as e:
                logging.error('Error fetching gpm files:', e, 'With query:', query)
            
            
            items = response.json()['items']
            for item in items:
                if item['action'][1]['displayName'] == 'download':
                    if item['action'][1]['using'][1]['displayName'] == 'geotiff':
                        url = item['action'][1]['using'][1]['url']
                        file_datetime = self.extract_datetime_from_path(url)
                        geo_data_file = GeoDataFile(remote_path=url,
                                                    key=url.split(self.remote_data_loc)[1],
                                                    datetime=file_datetime,
                                                    local_path='',
                                                    processed_loc='')
                        gpm_data_files.append(geo_data_file)
                    else:
                        logging.error(f'Error, geotiff not in expected location in GPM using object')
                else:
                    logging.error(f'Error, download not in expected location in GPM action object')

        except Exception as e:
            logging.error('Error fetching gpm files:', e)
        logging.info('Files fetched.')
        return gpm_data_files

    # def check_if_downloaded(self, geo_data_files: List[GeoDataFile]) -> List[GeoDataFile]:
    #     files_to_download: List[GeoDataFile] = []
    #     for file in geo_data_files:
    #         processed_loc = self.get_processed_loc(file)
    #         if not os.path.exists(processed_loc):
    #             files_to_download.append(file)
    #         else:
    #             logging.info(f'{processed_loc} exists, Skipping download of {file.key}...')
    #             # check if file that's been processed is in self.processed_files
    #             in_processed_files = False
    #             for processed_file in self.processed_files:
    #                 if (processed_file.processed_loc == processed_loc):
    #                     in_processed_files = True
    #             if not in_processed_files:
    #                 logging.info(f'{processed_loc} exists, but was not in self.processed_files. adding...')
    #                 file.processed_loc = processed_loc
    #                 self.processed_files.append(file)
    #     return files_to_download

    
    def get_download_path(self, file: GeoDataFile) -> str:
        return os.path.join(self.raw_data_folder,file.key)
    
    def download_files(self, geo_data_files: List[GeoDataFile]) -> List[GeoDataFile]:
        downloaded_files: List[GeoDataFile] = []
        for file in geo_data_files:
            downloaded_file = self.download_file(file)
            if downloaded_file:
                downloaded_files.append(downloaded_file)
        return downloaded_files

    
    def download_file(self, geo_data_file: GeoDataFile) -> GeoDataFile | None:
        # Send a GET request to the URL
        logging.info(f'Downloading {geo_data_file.remote_path}')
        response = requests.get(geo_data_file.remote_path)

        download_path = self.get_download_path(geo_data_file)
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        if response.status_code == 200:
            # Write the content to a file
            with open(download_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"File downloaded successfully: {download_path}")
            geo_data_file.local_path = download_path
            logging.info('')
            return geo_data_file
        else:
            logging.error(f"Failed to download file: {response.status_code}")
        
            return None

    def extract_datetime_from_path(self, path: str) -> datetime:
        # Define the regex pattern to match the datetime in the path
        pattern = r"\.(\d{8})\.(\d{6})\."
        match = re.search(pattern, path)
        
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            
            # Combine date and time strings
            datetime_str = f"{date_str}{time_str}"
            
            # Parse the combined string into a datetime object
            extracted_datetime = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            extracted_datetime = extracted_datetime.replace(tzinfo=timezone.utc)
            return extracted_datetime
        else:
            raise ValueError("No valid datetime found in the provided path.")
    
    def process_file(self, geo_data_file: GeoDataFile) -> GeoDataFile | None:
        logging.info(f'Processing {geo_data_file.local_path}')
        processed_loc = self.get_processed_loc(geo_data_file)
        try:
            success = process_tif_to_tiles(geo_data_file.local_path, processed_loc, self.color_relief_file)
            logging.info(f'{geo_data_file.local_path} processed successfully to tiles.')
            geo_data_file.processed_loc = processed_loc

            if not success:
                print(f'file: {geo_data_file.processed_loc} failed. REMOVING.....')
                geo_data_file.remove_processed_loc()
                return None

        except Exception as e:
            logging.error(f'Error processing GPM tif to tiles for {geo_data_file.local_path}:', e)
            geo_data_file.remove_processed_loc()
            return None

        return geo_data_file

    
    # ## TODO
    # def get_processed_loc(self, file: GeoDataFile) -> str:
    #     key_dir = os.path.splitext(file.key)[0]
    #     file_dir = key_dir.split('/')[-1]
    #     return os.path.join(self.processed_variable_data_dir, file_dir)

    # def init_processed_files(self):
    #     raise NotImplementedError