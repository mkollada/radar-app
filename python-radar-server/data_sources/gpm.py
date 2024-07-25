from typing import List
from classes import GeoDataFile
from data_source import DataSource
from datetime import datetime, timedelta
import logging
import requests
import re
import os
import shutil
from utils.data_to_tiles import process_tif_to_tiles

class GPMDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder, 
                 base_url='https://pmmpublisher.pps.eosdis.nasa.gov/opensearch', 
                 n_files=1):
        super().__init__(raw_data_folder, processed_data_folder, None, base_url)
        self.n_files = n_files

        self.variable_name = 'precip_30mn'
        self.processed_variable_data_dir = os.path.join(processed_data_folder, self.variable_name)
        self.remote_data_loc = 'https://pmmpublisher.pps.eosdis.nasa.gov/products/s3/'
        self.color_relief_file = './assets/color_reliefs/GPM_color_relief.txt'
        self.processed_files: List[GeoDataFile] = []


    def clean_up_processed_files(self):
        logging.info('Cleaning up processed_files...')
        self.processed_files.sort()
        files_to_remove = self.processed_files[self.n_files:]
        self.processed_files = self.processed_files[:self.n_files]
        for file in files_to_remove:
            file.remove_processed_dir()
        processed_dirs = self.get_processed_dirs()
        
        # delete files that shouldn't be there
        for dir in os.listdir(self.processed_variable_data_dir):
            check_dir = os.path.join(self.processed_variable_data_dir, dir)
            if check_dir not in processed_dirs:
                shutil.rmtree(check_dir)
                logging.info(f'Removing unnecessary dir: {check_dir}')
                        
        logging.info('processed_files cleaned.')

    def fetch_data_files(self) -> List[GeoDataFile]:
        logging.info('Fetching recent GPM Files...')
        gpm_data_files: List[GeoDataFile] = []
        try:
            today = str(datetime.now().date())
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
                                                    processed_dir='')
                        gpm_data_files.append(geo_data_file)
                    else:
                        logging.error(f'Error, geotiff not in expected location in GPM using object')
                else:
                    logging.error(f'Error, download not in expected location in GPM action object')

        except Exception as e:
            logging.error('Error fetching gpm files:', e)
        logging.info('Files fetched.')
        return gpm_data_files

    def check_if_downloaded(self, geo_data_files: List[GeoDataFile]) -> List[GeoDataFile]:
        files_to_download: List[GeoDataFile] = []
        for file in geo_data_files:
            processed_dir = self.get_processed_dir(file)
            if not os.path.exists(processed_dir):
                files_to_download.append(file)
            else:
                logging.info(f'{processed_dir} exists, Skipping download of {file.key}...')
                # check if file that's been processed is in self.processed_files
                in_processed_files = False
                for processed_file in self.processed_files:
                    if (processed_file.processed_dir == processed_dir):
                        in_processed_files = True
                if not in_processed_files:
                    logging.info(f'{processed_dir} exists, but was not in self.processed_files. adding...')
                    file.processed_dir = processed_dir
                    self.processed_files.append(file)
        return files_to_download

    
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
        
    def update_data(self) -> List[str]:
        recent_data_files = self.fetch_data_files()
        files_to_download = self.check_if_downloaded(recent_data_files)
        downloaded_files = self.download_files(files_to_download)
        self.process_files(downloaded_files)
        self.remove_downloaded_files(downloaded_files)
        self.clean_up_processed_files()

        return self.get_processed_dirs()

        

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
            return extracted_datetime
        else:
            raise ValueError("No valid datetime found in the provided path.")

    
    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)
    
    def process_files(self, downloaded_files: List[GeoDataFile]):
        for file in downloaded_files:
            processed_file = self.process_file(file)
            if processed_file:
                self.processed_files.append(processed_file)
    
    def get_processed_dirs(self) -> List[str]:
        processed_dirs = []
        for file in self.processed_files:
            processed_dirs.append(file.processed_dir)
        return processed_dirs
    
    def process_file(self, file: GeoDataFile) -> GeoDataFile | None:
        logging.info(f'Processing {file.local_path}')
        processed_dir = self.get_processed_dir(file)
        try:
            process_tif_to_tiles(file.local_path, processed_dir, self.color_relief_file)
            logging.info(f'{file.local_path} processed successfully to tiles.')
            file.processed_dir = processed_dir
        except Exception as e:
            logging.error(f'Error processing GPM tif to tiles for {file.local_path}:', e)
            return None

        return file

    
    ## TODO
    def get_processed_dir(self, file: GeoDataFile) -> str:
        key_dir = os.path.splitext(file.key)[0]
        file_dir = key_dir.split('/')[-1]
        return os.path.join(self.processed_variable_data_dir, file_dir)

    def init_processed_files(self):
        raise NotImplementedError