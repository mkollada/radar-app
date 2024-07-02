import abc
import os
import shutil
import requests
from tqdm import tqdm

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

    @abc.abstractmethod
    def download_data(self):
        for data_type in self.data_types:
            files_to_download = self.fetch_data_paths()
            data_type_dir = os.path.join(self.raw_data_folder, data_type.name)
            processed_data_type_dir = os.path.join(self.processed_data_folder, data_type.name)
        
    
    @abc.abstractmethod
    def extract_datetime_from_path(self, path):
        raise NotImplementedError
    
    @abc.abstractmethod
    def fetch_data_paths(self, base_url):
        raise NotImplementedError

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
