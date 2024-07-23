import os
import shutil
from typing import List
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

from classes import DataType
from classes import GeoDataFile
from data_source import DataSource
from utils.data_to_tiles import process_zipped_grib2_to_tiles

class MRMSDataType():
    def __init__(self, name, variable_name, type_of_level):
        self.name = name
        self.variable_name = variable_name
        self.color_relief_file = f'./assets/color_reliefs/{name}_color_relief.txt'
        self.type_of_level = type_of_level

class MRMSDataSource(DataSource):
    def __init__(
            self, 
            raw_data_folder='./data/mrms/raw', 
            processed_data_folder='./data/mrms/processed',
            data_types=[
                MRMSDataType(
                    name='PrecipRate', 
                    variable_name='unknown',
                    type_of_level=None,
                )
            ],
            n_files=4,
            base_url='https://mrms.ncep.noaa.gov/data/2D/'
        ):
        super().__init__(raw_data_folder, processed_data_folder, data_types, base_url)
        self.data_types = data_types
        self.n_files = n_files
        self.processed_files = self.init_processed_files()
        self.clean_up_processed_files()

    def extract_datetime_from_path(self, path):
        try:
            parts = path.split('_')
            date_part = parts[-1].split('.')[0]
            return datetime.strptime(date_part, '%Y%m%d-%H%M%S')
        except (IndexError, ValueError):
            return datetime.min

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
    
    def fetch_data_paths(self, base_url):
        response = requests.get(base_url)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        
        file_links = []
        for link in links:
            href = link.get('href')
            if href.endswith('.gz') and 'latest' not in href:
                try:
                    parts = href.split('_')
                    date_part = parts[-1].split('.')[0]
                    file_date = datetime.strptime(date_part, '%Y%m%d-%H%M%S')
                    file_links.append((href, file_date))
                except (IndexError, ValueError) as e:
                    print(f"Error parsing date from {href}: {e}")

        file_links.sort(key=lambda x: x[1])
        recent_file_links = file_links[-self.n_files:]

        return recent_file_links

    
    def fetch_and_download_data(self, data_type):
        base_url = os.path.join(self.base_url, data_type.name)

        recent_file_links = self.fetch_data_paths(base_url)

        data_type_dir = os.path.join(self.raw_data_folder, data_type.name)
        processed_data_type_dir = os.path.join(self.processed_data_folder, data_type.name)

        for filename, _ in recent_file_links:
            file_url = os.path.join(base_url, filename)
            output_dir = os.path.join(processed_data_type_dir, os.path.splitext(filename)[0])
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                file_path = self.download_file(file_url, data_type_dir, filename, data_type)
                self.process_data_file(file_path, data_type, output_dir)
                print(f'{file_path} processed to {output_dir}. Removing raw file...')
                os.remove(file_path)
                os.remove(os.path.join(os.path.dirname(file_path), os.path.splitext(filename)[0] + '.9093e.idx'))
                print(f'{file_path} removed.')
            else:
                if output_dir not in self.processed_files[data_type.name]:
                    self.processed_files[data_type.name].append(output_dir)
                print(f'Processed files already exist at {output_dir}. Skipping...')

        self.processed_files[data_type.name] = sorted(self.processed_files[data_type.name], key=lambda x: self.extract_datetime_from_path(x))

        return True

    def process_data_file(self, file_path: str, data_type: MRMSDataType, output_dir: str):
        file_processed = process_zipped_grib2_to_tiles(
            file_path,
            data_type.variable_name,
            data_type.type_of_level,
            output_tiles=output_dir,
            color_relief_file=data_type.color_relief_file,
            target_crs='EPSG:3857',
            filter_grib=False
        )

        if output_dir not in self.processed_files[data_type.name]:
            self.processed_files[data_type.name].append(output_dir)
        
        self.processed_files[data_type.name] = sorted(self.processed_files[data_type.name], key=lambda x: self.extract_datetime_from_path(x))

    def download_data(self):
        for data_type in self.data_types:
            self.fetch_and_download_data(data_type)
            self.clean_up_processed_files()

        return self.processed_files
            
    def process_data(self):
        return super().process_data()
    
    def get_processed_data(self):
        return super().get_processed_data()
    
    

    def check_if_downloaded(self, recent_files: List[GeoDataFile]):
        return super().check_if_downloaded(recent_files)




    def download_file(self, url, save_dir, filename, data_type):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        file_path = os.path.join(save_dir, filename)
        if not os.path.exists(file_path):
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                with open(file_path, 'wb') as f, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=1024):
                        size = f.write(chunk)
                        bar.update(size)
                
            else:
                raise Exception(f"Failed to download file: {url}")

        return file_path



    def fetch_data_files(self, data_type: DataType):
        return super().fetch_data_files(data_type)
    
    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)