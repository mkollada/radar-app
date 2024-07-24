import abc
import os
import shutil
import requests
from tqdm import tqdm
from classes import DataType, GeoDataFile
from typing import List
import logging


class DataSource(abc.ABC):
    def __init__(self, raw_data_folder, processed_data_folder, data_types, base_url):
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        self.data_types = data_types
        self.base_url = base_url
        if not os.path.exists(raw_data_folder):
            os.makedirs(raw_data_folder)
        if not os.path.exists(processed_data_folder):
            os.makedirs(processed_data_folder)
    '''
    returns List of GeoDataFiles
    '''
    @abc.abstractmethod
    def fetch_data_files(self, data_type: DataType):
        raise NotImplementedError
    
    def get_download_path(self, file: GeoDataFile) -> str:
        return os.path.join(self.raw_data_folder,file.key)
    
    @abc.abstractmethod
    def get_processed_dir(self, file: GeoDataFile) -> str:
        raise NotImplementedError
    
    '''
    Returns files_to_download: List[GeoDataFile]
    '''
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

    
    '''
    Returns processed_files: List[GeoDataFile]
    '''

    '''
    '''
    @abc.abstractmethod
    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        for file in downloaded_files:
            file.remove_local_file()


    def init_processed_files(self):
        processed_files = {}
        for data_type in self.data_types:
            processed_dir = os.path.join(self.processed_data_folder, data_type.name)
            if os.path.exists(processed_dir):
                raw_dir_files = [os.path.join(processed_dir, dirname) for dirname in os.listdir(processed_dir) if dirname.endswith('grib2')]
                processed_files[data_type.name] = sorted(raw_dir_files, key=lambda x: self.extract_datetime_from_path(x))
            else:
                os.makedirs(processed_dir)
                processed_files[data_type.name] = []

        return processed_files
    
    def update_data(self) -> List[str]:
        recent_data_files = self.fetch_data_files()
        files_to_download = self.check_if_downloaded(recent_data_files)
        downloaded_files = self.download_files(files_to_download)
        self.process_files(downloaded_files)
        self.remove_downloaded_files(downloaded_files)

        return self.get_processed_dirs()
    
    
    def clean_up_processed_files(self):
        for data_type in self.data_types:
            data_type_dir = os.path.join(self.processed_data_folder, data_type.name)
            dirs = [os.path.join(data_type_dir, dirname) for dirname in os.listdir(data_type_dir) if dirname.endswith('grib2')]
            dirs_with_dates = []

            for dir in dirs:
                try:
                    dir_date = self.extract_datetime_from_path(dir)
                    dirs_with_dates.append((dir, dir_date))
                except (IndexError, ValueError) as e:
                    print(f"Error parsing date from {dir}: {e}")
            
            dirs_with_dates.sort(key=lambda x: x[1], reverse=True)
            dirs_to_keep = dirs_with_dates[:self.n_files]
            dirs_to_delete = dirs_with_dates[self.n_files:]
            
            for dir, _ in dirs_to_delete:
                shutil.rmtree(dir)
                print(f"Deleted old dir: {dir}")
                self.processed_files[data_type.name].remove(dir)

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
            if processed_file:
                if processed_file not in self.processed_files:
                    self.processed_files.append(processed_file)

    # def download_file(self, url, save_dir, filename, data_type):
    #     if not os.path.exists(save_dir):
    #         os.makedirs(save_dir)
        
    #     file_path = os.path.join(save_dir, filename)
    #     if not os.path.exists(file_path):
    #         response = requests.get(url, stream=True)
    #         if response.status_code == 200:
    #             total_size = int(response.headers.get('content-length', 0))
    #             with open(file_path, 'wb') as f, tqdm(
    #                 desc=filename,
    #                 total=total_size,
    #                 unit='iB',
    #                 unit_scale=True,
    #                 unit_divisor=1024,
    #             ) as bar:
    #                 for chunk in response.iter_content(chunk_size=1024):
    #                     size = f.write(chunk)
    #                     bar.update(size)
                
    #         else:
    #             raise Exception(f"Failed to download file: {url}")

    #     return file_path
    
    
