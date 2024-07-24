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

class NexradDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder, data_types,):
        super().__init__(raw_data_folder, processed_data_folder, data_types, None)

        self.nexrad_interface = nexradaws.NexradAwsInterface()
        self.processed_files: List[NexradGeoDataFile] = []
    
    def fetch_data_files(self, site_code: str, time_delta: timedelta = timedelta(days=1)) -> List[NexradGeoDataFile]:
        try:
            now = datetime.now(timezone.utc)
            scans = self.nexrad_interface.get_avail_scans_in_range(
                now - time_delta, 
                now,
                site_code, 
            )
            nexrad_geo_data_files: List[NexradGeoDataFile] = []
            if scans:
                for scan in scans:
                    if 'MDM' not in scan.filename:
                        nexrad_geo_data_file = NexradGeoDataFile(
                            remote_path=scan.key,
                            key=scan.key,
                            datetime=scan.scan_time,
                            scan=scan,
                            local_path='',
                            processed_dir='',
                            processed_path=''
                        )
                    nexrad_geo_data_files.append(nexrad_geo_data_file)
            else:
                raise ValueError('Error, nexrad fetch_data_scans returned no files')

            
        except Exception as e:
            logging.error('Error fetching scans:', e)
        return nexrad_geo_data_files

    def get_download_path(self, nexrad_geo_data_file: NexradGeoDataFile) -> str:
        return os.path.join(self.raw_data_folder,nexrad_geo_data_file.scan.filename)

    def check_if_downloaded(
            self, nexrad_geo_data_files: List[NexradGeoDataFile], variable_name: str
    ) -> List[NexradGeoDataFile]:
        files_to_download: List[NexradGeoDataFile] = []

        for file in nexrad_geo_data_files:
            processed_path = self.get_processed_path(file, variable_name)
            if not os.path.exists(processed_path):
                files_to_download.append(file)
            else:
                print(f'{processed_path} exists, Skipping download of {file.scan.awspath}...')

        return files_to_download
    
    def download_files(self, files_to_download: List[NexradGeoDataFile]) -> List[NexradGeoDataFile]:
        downloaded_files: List[NexradGeoDataFile] = []
        for file in files_to_download:
            print(f'Downloading {file.scan.key}...')
            results = self.nexrad_interface.download(file.scan, self.raw_data_folder)
            if results.success:
                file.local_path = results.success[0].filepath
                print(f'Successfully downloaded: {file.local_path}')
                downloaded_files.append(file)
            elif results.failed:
                failed_file, exception = results.failed[0]
                print(f'Failed to download: {failed_file}, Error: {exception}')
            else:
                raise ValueError('No success or failure in downloading Nexrad files.')
        return downloaded_files
    
    def extract_datetime_from_path(self, path: str):
        return super().extract_datetime_from_path(path)

    def remove_downloaded_files(self, downloaded_files: List[NexradGeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)

    def process_files(self, downloaded_files: List[NexradGeoDataFile]) -> List[NexradGeoDataFile]:
        for file in downloaded_files:
            processed_file = self.process_file(file)
            if processed_file not in self.processed_files:
                self.processed_files.append(processed_file)
            else:
                print(f'{processed_file} already in self.processed_files, skipping appending.')
        return self.processed_files

    def process_file(self, file: NexradGeoDataFile, variable_name='reflectivity') -> NexradGeoDataFile:
        
        output_path = self.get_processed_path(file=file, variable_name=variable_name)
        output_dir = os.path.dirname(output_path)
        print(f'Checking if {output_path} exists...')
        if not os.path.exists(output_path):
            print(f'{output_path} does not exist, generating...')
        
            radar = pyart.io.read_nexrad_archive(file.local_path)
            fig = plt.figure(figsize=(8, 6))
            display = pyart.graph.RadarMapDisplay(radar,)

            ax = plt.subplot(111, projection=ccrs.PlateCarree())

            display.plot_ppi_map(
                variable_name,
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
            file.processed_dir = output_dir
            file.processed_path = output_path
        else:
            print(f'{output_path} exists. Skipping generation...')
            file.processed_dir = output_dir
            file.processed_path = output_path

        return file
    
    def get_processed_path(self, file: NexradGeoDataFile, variable_name: str) -> str:
        output_dir = os.path.join(self.processed_data_folder,variable_name,file.scan.awspath)
        output_path = os.path.join(output_dir, f'{file.scan.filename}.png')
        return output_path
    
    def get_processed_dir(self, file: GeoDataFile) -> str:
        return super().get_processed_dir(file)
    
    def update_data(self, site_code: str, variable_name: str) -> str:
        recent_data_files = self.fetch_data_files(site_code=site_code)
        use_file = recent_data_files[-1]

        processed_path = self.get_processed_path(use_file, variable_name)

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
        


        

        










        