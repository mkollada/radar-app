from typing import List
from classes import GeoDataFile
from data_source import DataSource
from datetime import datetime, timedelta
import logging
import requests
import re

class GPMDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder, 
                 base_url='https://pmmpublisher.pps.eosdis.nasa.gov/opensearch', 
                 n_files=1):
        super().__init__(raw_data_folder, processed_data_folder, None, base_url)
        self.n_files = n_files

        self.variable_name = 'precip_30mn'

        

    ## TODO
    def fetch_data_files(self) -> List[GeoDataFile]:
        gpm_data_files: List[GeoDataFile] = []
        try:
            today = str(datetime.now().date())
            yesterday = str((datetime.today() - timedelta(days=1)).date())

            query = f'{self.base_url}?q={self.variable_name}&limit={self.n_files}' + \
                f'&startTime={yesterday}&endTime={today}'
            
            print(query)
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
        return gpm_data_files
    
    ## TODO
    def check_if_downloaded(self, recent_files: List[GeoDataFile]):
        raise NotImplementedError
    
    ## TODO
    def get_download_path():
        raise NotImplementedError
    
    ## TODO
    def download_files():
        raise NotImplementedError
    
    from datetime import datetime


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

    
    ## TODO 
    def download_data(self):
        return super().download_data()
    
    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)
    
    def process_files(self, downloaded_files: List[GeoDataFile]):
        for file in downloaded_files:
            processed_file = self.process_file(file)
            self.processed_files.append(processed_file)
        return self.processed_files
    
    ## TODO
    def get_processed_path(self, file: GeoDataFile):
        raise NotImplementedError
