import abc
import os
from tqdm import tqdm
from classes import DataType, GeoDataFile
from typing import List
import logging


class DataSource(abc.ABC):
    def __init__(self, raw_data_folder, processed_data_folder, base_url):
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        self.base_url = base_url
        if not os.path.exists(raw_data_folder):
            os.makedirs(raw_data_folder)
        if not os.path.exists(processed_data_folder):
            os.makedirs(processed_data_folder)

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
            file.remove_local_file()
    
    def update_data(self) -> List[str]:
        recent_data_files = self.fetch_data_files()
        files_to_download = self.check_if_downloaded(recent_data_files)
        downloaded_files = self.download_files(files_to_download)
        self.process_files(downloaded_files)
        self.remove_downloaded_files(downloaded_files)
        self.clean_up_processed_files()

        return self.get_processed_locs()
    
    def clean_up_processed_files(self):
        logging.info('Cleaning up processed_files...')
        self.sort_processed_files(reverse=True)
        files_to_remove = self.processed_files[self.n_files:]
        if len(self.processed_files) > self.n_files:
            self.processed_files = self.processed_files[:self.n_files]
        for geo_data_file in files_to_remove:
            geo_data_file.remove_processed_loc()
        logging.info('processed_files cleaned.')
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
    
    
