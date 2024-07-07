from typing import List
from classes import GeoDataFile
from data_source import DataSource
import nexradaws
from datetime import datetime, timedelta, timezone
import logging
from classes import NexradGeoDataFile
from typing import List
import os

class NexradDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder, data_types,):
        super().__init__(raw_data_folder, processed_data_folder, data_types, None)

        self.nexrad_interface = nexradaws.NexradAwsInterface()
    
    def fetch_data_files(self, site_code: str, time_delta: timedelta = timedelta(days=1)):
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
                    nexrad_geo_data_file = NexradGeoDataFile(
                        remote_path=scan.key,
                        datetime=scan.scan_time,
                        scan=scan,
                        local_path='',
                        processed_dir=''
                    )
                    nexrad_geo_data_files.append(nexrad_geo_data_file)
            else:
                raise ValueError('Error, nexrad fetch_data_scans returned no files')

            return nexrad_geo_data_files
        except Exception as e:
            logging.error('Error fetching scans:', e)

    def get_download_path(self, nexrad_geo_data_file: NexradGeoDataFile):
        return os.path.join(self.raw_data_folder,nexrad_geo_data_file.scan.filename)

    def check_if_downloaded(self, nexrad_geo_data_files: List[NexradGeoDataFile]):
        files_to_download: List[NexradGeoDataFile] = []

        for file in nexrad_geo_data_files:
            download_path = self.get_download_path(file)
            if not os.path.exists(download_path):
                files_to_download.append(file)
            else:
                print(f'{download_path} exists, Skipping...')

        return files_to_download
    
    def download_files(self, files_to_download: List[NexradGeoDataFile]):
        downloaded_files: List[NexradGeoDataFile] = []
        for file in files_to_download:
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
    
    def extract_datetime_from_path(self, path):
        return super().extract_datetime_from_path(path)
    
    def download_data(self):
        return super().download_data()
    # def process_files(self, downloaded_files: List[NexradGeoDataFile]):

    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)




        