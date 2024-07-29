import abc
import os
from tqdm import tqdm
from classes import DataType, GeoDataFile
from typing import List
import logging
from datetime import datetime, timezone, timedelta


class DataSource(abc.ABC):
    def __init__(
            self, raw_data_folder: str, 
            processed_data_folder:str , 
            time_delta: timedelta
        ):
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        self.time_delta = time_delta
        if not os.path.exists(raw_data_folder):
            os.makedirs(raw_data_folder)
        if not os.path.exists(processed_data_folder):
            os.makedirs(processed_data_folder)

        self.processed_files: List[GeoDataFile] = []

        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('DataSource initialized.')

    def filter_files_by_time(self, geo_data_files: List[GeoDataFile]):
        now = datetime.now(timezone.utc)
        cutoff_time = now - self.time_delta

        filtered_geo_data_files: List[GeoDataFile] = []
        for geo_data_file in geo_data_files:

            if geo_data_file.datetime > cutoff_time:
                filtered_geo_data_files.append(geo_data_file)
        
        return filtered_geo_data_files

    abc.abstractmethod
    def extract_datetime_from_name(self, name: str):
        raise NotImplementedError

    def sort_processed_files(self, reverse=False):
        self.processed_files.sort(reverse=reverse)

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

    @abc.abstractmethod
    def fetch_data_files(self, data_type: DataType):
        raise NotImplementedError
    
    def get_download_path(self, file: GeoDataFile) -> str:
        return os.path.join(self.raw_data_folder,file.key)
    
    def get_processed_loc(self, file: GeoDataFile) -> str:
        file_dir = file.key.split('/')[-1]
        return os.path.join(self.processed_variable_data_dir, file_dir)
    
    def get_processed_locs(self) -> List[str]:
        processed_locs = []
        for file in self.processed_files:
            processed_locs.append(file.processed_loc)
        return processed_locs
    
    def get_processed_locs_with_time(self) -> List[str]:
        processed_locs = []
        for file in self.processed_files:
            processed_tuple = (file.processed_loc, file.datetime.isoformat())
            processed_locs.append(processed_tuple)
        return processed_locs
    
    '''
    Returns files_to_download: List[GeoDataFile]
    '''
    def check_if_downloaded(self, geo_data_files: List[GeoDataFile]) -> List[GeoDataFile]:
        files_to_download: List[GeoDataFile] = []
        for file in geo_data_files:
            processed_loc = self.get_processed_loc(file)
            if not os.path.exists(processed_loc):
                files_to_download.append(file)
            else:
                logging.info(f'{processed_loc} exists, Skipping download of {file.key}...')
                # check if file that's been processed is in self.processed_files
                in_processed_files = False
                for processed_file in self.processed_files:
                    if (processed_file.processed_loc == processed_loc):
                        in_processed_files = True
                if not in_processed_files:
                    logging.info(f'{processed_loc} exists, but was not in self.processed_files. adding...')
                    file.processed_loc = processed_loc
                    self.processed_files.append(file)
        return files_to_download

    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        for file in downloaded_files:
            if file.local_path != '':
                file.remove_local_file()

    def update_data(self):
        start = datetime.now()
        
        recent_files = self.fetch_data_files()
        fetch_time = datetime.now()
        logging.info(f'Fetch finished in: {fetch_time-start}')
        filtered_recent_files = self.filter_files_by_time(recent_files)

        files_to_download = self.check_if_downloaded(filtered_recent_files)
        downloaded_files = self.download_files(files_to_download)
        download_time = datetime.now()
        logging.info(f'Download finished in: {download_time-fetch_time}')
        self.process_files(downloaded_files)
        process_time = datetime.now()
        self.remove_downloaded_files(downloaded_files)

        logging.info(f'Full run finished in: {process_time-start}')
        logging.info(f'Fetch finished in: {fetch_time-start}')
        logging.info(f'Download finished in: {download_time-fetch_time}')
        logging.info(f'Process finished in: {process_time-download_time}')
    
        self.clean_up_processed_files()

        return self.get_processed_locs_with_time()
    
    def clean_up_processed_files(self):
        logging.info('Cleaning up processed_files...')
        self.sort_processed_files(reverse=True)
        updated_processed_files: List[GeoDataFile] = []
        time_cutoff = datetime.now(timezone.utc) - self.time_delta
        for processed_file in self.processed_files:
            if processed_file.datetime > time_cutoff:
                updated_processed_files.append(processed_file)
            else:
                processed_file.remove_processed_loc()
                if processed_file.local_path != '':
                    processed_file.remove_local_file()

        self.processed_files = updated_processed_files
        self.sort_processed_files()

    def download_files(self, geo_data_files: List[GeoDataFile]) -> List[GeoDataFile]:
        downloaded_files: List[GeoDataFile] = []
        for file in geo_data_files:
            downloaded_file = self.download_file(file)
            if downloaded_file:
                downloaded_files.append(downloaded_file)
        return downloaded_files
    
    def process_files(self, downloaded_files: List[GeoDataFile]):
        for file in downloaded_files:
            processed_file = self.process_file(file)

            processed_locs = self.get_processed_locs()

            if processed_file is not None:
                if processed_file.processed_loc not in processed_locs:
                    self.processed_files.append(processed_file)
            file.remove_local_file()

            


    @abc.abstractmethod
    def download_file(self, geo_data_file: GeoDataFile):
        raise NotImplementedError
    
    
