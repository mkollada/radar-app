from typing import List
from classes import GeoDataFile
from data_source import DataSource
import nexradaws
from datetime import datetime, timedelta, timezone
import logging
from classes import NexradGeoDataFile
from typing import List
import os
import pyart
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import json
from tqdm import tqdm

from datetime import datetime, timedelta, timezone

class NexradDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder):
        super().__init__(raw_data_folder, processed_data_folder, None)

        self.nexrad_interface = nexradaws.NexradAwsInterface()
        self.processed_files: List[NexradGeoDataFile] = []

        file_path = './assets/nexrad_stations.json'
        with open(file_path, 'r') as file:
            self.nexrad_stations = json.load(file)

        self.site_codes = []
        for station in self.nexrad_stations:
            self.site_codes.append(station['id'])

        self.time_delta = timedelta(minutes=5)

        self.variable_name = 'reflectivity'

    def fetch_data_files(self) -> List[NexradGeoDataFile]:
        nexrad_geo_data_files: List[NexradGeoDataFile] = []
        for site_code in tqdm(self.site_codes, desc='fetching NEXRAD site scans'):
            try:
                now = datetime.now(timezone.utc)
                cutoff_time = now - self.time_delta
                scans = self.nexrad_interface.get_avail_scans_in_range(
                    now - timedelta(days=1), 
                    now,
                    site_code, 
                )
                
                if scans:
                    for scan in scans:
                        if scan.scan_time >= cutoff_time:
                            if 'MDM' not in scan.filename:
                                nexrad_geo_data_file = NexradGeoDataFile(
                                    remote_path=scan.key,
                                    key=scan.key,
                                    datetime=scan.scan_time,
                                    scan=scan,
                                    local_path='',
                                    processed_loc='',
                                    processed_path=''
                                )
                            nexrad_geo_data_files.append(nexrad_geo_data_file)
                else:
                    logging.error(f'Error, nexrad fetch_data_scans for site {site_code} returned no files')

            
            except Exception as e:
                logging.error(f'Error fetching scans at site: {site_code}')
        return nexrad_geo_data_files

    # def check_if_downloaded(
    #         self, nexrad_geo_data_files: List[NexradGeoDataFile], variable_name: str
    # ) -> List[NexradGeoDataFile]:
    #     files_to_download: List[NexradGeoDataFile] = []

    #     for file in nexrad_geo_data_files:
    #         processed_path = self.get_processed_loc(file, variable_name)
    #         if not os.path.exists(processed_path):
    #             files_to_download.append(file)
    #         else:
    #             print(f'{processed_path} exists, Skipping download of {file.key}...')

    #     return files_to_download
    

    def extract_datetime_from_name(self, name: str):
        # Assuming the filename format is fixed: KESXYYYYMMDD_HHMMSS_V06
        try:
            # Extract the date and time parts from the filename
            date_part = name[4:12]
            time_part = name[13:19]
            
            # Combine the date and time parts
            datetime_str = date_part + time_part
            
            # Parse the combined string into a datetime object
            extracted_datetime = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            return extracted_datetime
        except (IndexError, ValueError) as e:
            print(f"Error parsing datetime from filename: {e}")
            return None

    # TODO modularize to download file
    def download_files(self, files_to_download: List[NexradGeoDataFile]) -> List[NexradGeoDataFile]:
        downloaded_files: List[NexradGeoDataFile] = []
        scans_to_download = []
        for file in files_to_download:
            scans_to_download.append(file.scan)
        
        logging.info(f'Downloading {len(scans_to_download)} NEXRAD Scans...')
        try:
            results = self.nexrad_interface.download(scans_to_download,self.raw_data_folder)
        except Exception as e:
            logging.error('Failed to download NEXRAD scans', e)

        if results.success:
            for download in results.success:
                print(download.filepath)
                name = download.filepath.split('/')[-1]
                geo_data_file = GeoDataFile(
                    datetime=self.extract_datetime_from_name(name),
                    remote_path='',
                    local_path=download.filepath,
                    processed_loc='',
                    key=download.filepath.split('/')[-1],
                )
                downloaded_files.append(geo_data_file)

            print(f'Successfully downloaded {len(results.success)} files')
                
        elif results.failed:
            failed_file, exception = results.failed[0]
            print(f'Failed to download: {failed_file}, Error: {exception}')
        else:
            raise ValueError('No success or failure in downloading Nexrad files.')
        return downloaded_files
    
    def extract_datetime_from_path(self, path: str):
        raise NotImplementedError


    def process_files(self, downloaded_files: List[NexradGeoDataFile]) -> List[NexradGeoDataFile]:
        for file in downloaded_files:
            processed_file = self.process_file(file)
            if processed_file not in self.processed_files:
                self.processed_files.append(processed_file)
            else:
                print(f'{processed_file} already in self.processed_files, skipping appending.')
        return self.processed_files

    def process_file(self, geo_data_file: GeoDataFile) -> NexradGeoDataFile:
        
        output_path = self.get_processed_loc(geo_data_file)
        output_dir = os.path.dirname(output_path)
        print(f'Checking if {output_path} exists...')
        if not os.path.exists(output_path):
            print(f'{output_path} does not exist, generating...')
        
            radar = pyart.io.read_nexrad_archive(geo_data_file.local_path)
            fig = plt.figure(figsize=(8, 6))
            display = pyart.graph.RadarMapDisplay(radar,)

            ax = plt.subplot(111, projection=ccrs.PlateCarree())

            display.plot_ppi_map(
                self.variable_name,
                sweep=0,
                ax=ax,
                colorbar_label="Equivalent Relectivity ($Z_{e}$) \n (dBZ)",
                vmin=-20,
                vmax=60,
                lat_lines=[],
                lon_lines=[]
            )

            # Add coastlines and borders
            # ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.add_feature(cfeature.STATES, linestyle=':', edgecolor='gray')

            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(output_path)
            geo_data_file.processed_loc = output_dir
        else:
            print(f'{output_path} exists. Skipping generation...')
            geo_data_file.processed_loc = output_dir

        return geo_data_file
    
    def get_processed_loc(self, geo_data_file: GeoDataFile) -> str:
        output_path = os.path.join(
            self.processed_data_folder,
            self.variable_name,
            geo_data_file.key[:4],
            f'{geo_data_file.key}.png'
        )
        return output_path

    
    def update_data(self, site_code: str, variable_name: str) -> str:
        recent_data_files = self.fetch_data_files(site_code=site_code)
        use_file = recent_data_files[-1]

        processed_path = self.get_processed_loc(use_file, variable_name)

        files_to_download: List[NexradGeoDataFile] = []
        if not os.path.exists(processed_path):
            files_to_download.append(use_file)
            downloaded_files = self.download_files(files_to_download)
            processed_files = self.process_files(downloaded_files)
            print('Processed files array:', processed_files)
            self.remove_downloaded_files(downloaded_files)
            return processed_files[-1].processed_path
        else:
            print(f'{processed_path} exists, Skipping download of {use_file.scan.awspath}...')
            return processed_path
        
    def download_file(self, geo_data_file: GeoDataFile):
        pass
    
    def init_processed_files(self):
        raise NotImplementedError
        


        

        










        