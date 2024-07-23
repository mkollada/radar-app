from typing import List
from classes import GeoDataFile
from data_source import DataSource
from datetime import datetime, timedelta, timezone
import logging
import requests
import re
import os
import shutil
from utils.data_to_tiles import process_grib2_to_tiles, process_netcdf_to_tiles
import boto3
from botocore import UNSIGNED
from botocore.client import Config

class SatDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder,
                 n_files=1):
        
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        
        self.variable_name = 'GMGSI_SW'
        self.s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        self.n_files = n_files
        self.bucket = 'noaa-gmgsi-pds'

        self.color_relief_file = './assets/color_reliefs/PrecipRate_color_relief.txt'

        self.processed_files: List[GeoDataFile] = []

        self.processed_variable_data_dir = os.path.join(
            self.processed_data_folder,
            self.variable_name
        )

    def fetch_data_files(self) -> List[GeoDataFile]:
        logging.info('Fetching recent Satellite image files')
        sat_data_files: List[GeoDataFile] = []
        try:
            objects = get_recent_sat_mosaic_files(
                self.s3_client,
                self.bucket, 
                self.variable_name, 
                n_files=self.n_files
            )

            for obj in objects:
                geo_data_file = GeoDataFile(
                    datetime=obj['LastModified'],
                    remote_path=obj['Key'],
                    key=obj['Key'],
                    local_path='',
                    processed_dir=''
                )

                sat_data_files.append(geo_data_file)
        except Exception as e:
            logging.error('Error fetching satellite image files:', e)

        if len(sat_data_files) == 0:
            logging.error('Did not successfully fetch any satellite image files.')
        
        return sat_data_files
    
    def get_download_path(self, file: GeoDataFile) -> str:
        return super().get_download_path(file)
    
    ## TODO
    def get_processed_dir(self, file: GeoDataFile) -> str:
        key_dir = os.path.splitext(file.key)[0]
        file_dir = file.key.split('/')[-1]
        return os.path.join(self.processed_variable_data_dir, file_dir)
    
    def get_processed_dirs(self) -> List[str]:
        processed_dirs = []
        for file in self.processed_files:
            processed_dirs.append(file.processed_dir)
        return processed_dirs
    
    def check_if_downloaded(self, recent_files: List[GeoDataFile]):
        return super().check_if_downloaded(recent_files)
    
    def download_file(self, geo_data_file: GeoDataFile) -> GeoDataFile:
        if not os.path.exists(self.processed_data_folder):
            os.makedirs(self.processed_data_folder)

        # Define the local path where the file will be saved
        download_path = self.get_download_path(geo_data_file)

        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        logging.info(f'Downloading {geo_data_file.remote_path} to {download_path}')

        # Download the file from S3
        self.s3_client.download_file(self.bucket, geo_data_file.remote_path, download_path)

        logging.info(f'Download complete: {download_path}')

        # Update the geo_data_file with the local path
        geo_data_file.local_path = download_path

        return geo_data_file

    def process_file(self, file: GeoDataFile) -> GeoDataFile | None:
        logging.info(f'Processing {file.local_path}')
        processed_dir = self.get_processed_dir(file)
        try:
            process_netcdf_to_tiles(
                file.local_path,
                'data',
                processed_dir,
                self.color_relief_file,
            )
            logging.info(f'{file.local_path} processed successfully to tiles.')
            file.processed_dir = processed_dir
        except Exception as e:
            logging.error(f'Error processing satellite netcdf to tiles for {file.local_path}:', e)
            return None
        
        return file

    def process_files(self, downloaded_files: List[GeoDataFile]):
        return super().process_files(downloaded_files)
    
    def remove_downloaded_files(self, downloaded_files: List[GeoDataFile]):
        return super().remove_downloaded_files(downloaded_files)

    def update_data(self) -> List[str]:
        recent_data_files = self.fetch_data_files()
        files_to_download = self.check_if_downloaded(recent_data_files)
        downloaded_files = self.download_files(files_to_download)
        self.process_files(downloaded_files)
        self.remove_downloaded_files(downloaded_files)

        return self.get_processed_dirs()

def get_recent_sat_mosaic_files(s3_client, bucket, variable_name, n_files=1, delta=timedelta(days=1)):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - delta
    
    # List objects in the bucket with the specified prefix
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=variable_name)

    filtered_objects = []

    for page in page_iterator:
        if 'Contents' not in page:
            continue
        
        # Filter objects by LastModified date
        for obj in page['Contents']:
            if start_time <= obj['LastModified'] <= end_time:
                filtered_objects.append({'Key': obj['Key'], 'LastModified': obj['LastModified']})

    # Sort objects by LastModified date in descending order
    sorted_objects = sorted(filtered_objects, key=lambda x: x['LastModified'], reverse=True)

    # Return the n most recent objects
    return sorted_objects[:n_files]