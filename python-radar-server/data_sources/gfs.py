from data_source import DataSource
import requests
from bs4 import BeautifulSoup
import tqdm
import os
from datetime import datetime, timedelta
from utils.data_to_tiles import process_grib2_to_tiles

class GFSDataSource(DataSource):
    def __init__(self, raw_data_folder='./data/gfs/raw', 
                 processed_data_folder='./data/gfs/processed',
                 variable_names=['prate'],
                 type_of_level='surface',
                 color_relief_file='./assets/color_reliefs/precipitation_color_relief.txt'):
        super().__init__(raw_data_folder, processed_data_folder)
        self.hour_dir_names = ['00/', '06/', '12/', '18/']

        self.variable_names = ['refc']
        self.downloaded_files = []
        self.type_of_level = type_of_level
        self.color_relief_file = color_relief_file

        self.date = None
        self.hour = None

    # Todo check logic on this
    def get_latest_folder(self):
        base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
        date_format = "gfs.%Y%m%d/"
        hour_format = "%H/"
        
        current_time = datetime.utcnow()
        current_hour = None

        for _ in range(8):  # Check up to the last 48 hours (8 periods of 6 hours)
            
            date_folder = current_time.strftime(date_format)
            date_folder_url = base_url + date_folder
            print(date_folder_url)
            response = requests.get(date_folder_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                hour_folders = [a.text for a in soup.find_all('a') if a.text in self.hour_dir_names]
                if current_hour is None:
                    hour_folder_ints = [ int(i.split('/')[0]) for i in hour_folders]
                    current_hour = max(hour_folder_ints)
                print(current_hour)
                if current_hour < 10:
                    hour_folder = f'0{current_hour}/'
                else:
                    hour_folder = f'{current_hour}/'
                print(hour_folder)
                print(hour_folders)
                if hour_folder in hour_folders:
                    latest_hour_folder = hour_folder
                    print(f"Latest date folder URL: {date_folder_url}")
                    print(f"Latest hour folder: {latest_hour_folder}")
                    check_url = os.path.join(date_folder_url,latest_hour_folder)
                    print(f"Checking url for files: {check_url}")
                    files_exist = self.check_files_exist(check_url)
                    if files_exist:
                        self.hour = hour_folder.split('/')[0]
                        self.date = date_folder.split('/')[0].split('.')[1]
                        return check_url
            
            print('boop')
            current_hour -= 6
            if current_hour < 0:
                current_hour = 18
                current_time -= timedelta(days=1)

        
        raise Exception("No valid folders found in the last 48 hours")

    def check_files_exist(self, folder_url):
        hour = folder_url.split('/')[-2]
        files_to_check = [os.path.join(folder_url, f"atmos/gfs.t{hour}z.sfcf{str(i).zfill(3)}.nc") for i in range(0, 13)]
        
        for file_url in files_to_check:
            print('Checking...')
            print(file_url)
            response = requests.head(file_url)
            if response.status_code != 200:
                return False
        return True

    def download_data(self):
        latest_folder_url = self.get_latest_folder()

        hour = latest_folder_url.split('/')[-2]
        files_to_download = [f"gfs.t{hour}z.pgrb2.0p25.f{str(i).zfill(3)}" for i in range(0, 13)]

        if not os.path.exists(self.raw_data_folder):
            os.makedirs(self.raw_data_folder)

        for file_name in tqdm.tqdm(files_to_download, desc='Downloading GFS Grib FIles...'):
            file_url = f"{latest_folder_url}/atmos/{file_name}"
            response = requests.get(file_url)
            if response.status_code == 200:
                file_write_dir = os.path.join(self.raw_data_folder, self.date, self.hour)
                os.makedirs(file_write_dir, exist_ok=True)
                with open(os.path.join(file_write_dir, file_name), 'wb') as file:
                    file.write(response.content)
                self.downloaded_files.append(file_url)
            else:
                print(f"Failed to download {file_name}")

    def process_data(self):
        # Implement the data processing logic here
        for grib2_file in self.downloaded_files:
            for variable_name in self.variable_names:
                base_temp_file_name = f'output_{variable_name}_{self.type_of_level}'
                file_output_dir = grib2_file.split('/')[-2].split('.')[-1]
                process_grib2_to_tiles(
                    grib2_file, 
                    variable_name, 
                    self.type_of_level, 
                    base_temp_file_name + '.tif', 
                    base_temp_file_name + '_8bit.tif',
                    base_temp_file_name + '_3857.tif',
                    base_temp_file_name + '_colored.tif',
                    os.path.join(self.processed_data_folder,self.date,self.hour,grib2_file.split('/')[-1]),
                    './assets/color_reliefs/prate_color_relief.txt',
                    target_crs='EPSG:3857'
                )

    def get_processed_data(self):
        return self.processed_data_folder
