from typing import List
from classes import GeoDataFile
from data_source import DataSource
from datetime import datetime, timedelta, timezone
import logging
import os
from utils.data_to_tiles import process_grib2_to_tiles, process_netcdf_to_tiles
import boto3
from botocore import UNSIGNED
from botocore.client import Config

class SatDataSource(DataSource):
    def __init__(self, raw_data_folder, processed_data_folder,
                 n_files=1):
        
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        
        self.variable_name = 'GMGSI_VIS'
        self.s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        self.n_files = n_files
        self.bucket = 'noaa-gmgsi-pds'

        self.color_relief_file = './assets/color_reliefs/PrecipRate_color_relief.txt'

        

        self.processed_variable_data_dir = os.path.join(
            self.processed_data_folder,
            self.variable_name
        )

        self.processed_files: List[GeoDataFile] = []
        self.init_processed_files()
        self.clean_up_processed_files()

    def extract_datetime_from_name(self, name: str):
        # Assuming the filename format is fixed: GLOBCOMPSIR_nc.YYYYMMDDHH
        try:
            datetime_str = name.split('_')[1].split('.')[1]  # Split and get the date part
            extracted_datetime = datetime.strptime(datetime_str, "%Y%m%d%H")
            return extracted_datetime
        except (IndexError, ValueError) as e:
            print(f"Error parsing datetime from filename: {e}")
            return None


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
                    processed_loc=''
                )

                sat_data_files.append(geo_data_file)
        except Exception as e:
            logging.error('Error fetching satellite image files:', e)

        if len(sat_data_files) == 0:
            logging.error('Did not successfully fetch any satellite image files.')
        
        return sat_data_files
    
    def download_file(self, geo_data_file: GeoDataFile) -> GeoDataFile | None:
        if not os.path.exists(self.processed_data_folder):
            os.makedirs(self.processed_data_folder)

        # Define the local path where the file will be saved
        download_path = self.get_download_path(geo_data_file)

        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        logging.info(f'Downloading {geo_data_file.remote_path} to {download_path}')
        try:
            # Download the file from S3
            self.s3_client.download_file(self.bucket, geo_data_file.remote_path, download_path)
        except Exception as e:
            logging.error(f'Error downloading: {geo_data_file.remote_path}')
            return None
        logging.info(f'Download complete: {download_path}')

        # Update the geo_data_file with the local path
        geo_data_file.local_path = download_path

        return geo_data_file

    def process_file(self, file: GeoDataFile) -> GeoDataFile | None:
        logging.info(f'Processing {file.local_path}')
        processed_loc = self.get_processed_loc(file)
        os.makedirs(processed_loc, exist_ok=True)
        try:
            success = process_netcdf_to_tiles(
                file.local_path,
                'data',
                processed_loc,
                self.color_relief_file,
            )
            logging.info(f'{file.local_path} processed successfully to tiles.')
            file.processed_loc = processed_loc
            if not success:
                file.remove_processed_loc()
                return None
        except Exception as e:
            logging.error(f'Error processing satellite netcdf to tiles for {file.local_path}:', e)
            return None
        
        return file
    

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