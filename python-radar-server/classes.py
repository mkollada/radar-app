from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os
import shutil
import nexradaws
import nexradaws.resources
import nexradaws.resources.awsnexradfile
import logging

@dataclass
class DataType:
    name: str
    variable: str
    color_relief_file: str
    type_of_level: str

@dataclass
class GeoDataFile:
    datetime: datetime
    remote_path: str
    local_path: str
    processed_dir: str
    key: str
    
    # data_type: DataType

    def remove_local_file(self):
        if self.local_path and os.path.exists(self.local_path):
            os.remove(self.local_path)
            logging.info(f'Removed file: {self.local_path}')
            self.local_path = ''
        else:
            logging.info(f'Tried to remove local_path: {self.local_path}, but it does not exist.')

    def remove_processed_dir(self):
        if self.processed_dir and os.path.exists(self.processed_dir):
            shutil.rmtree(self.processed_dir)
            logging.info(f'Removed processed dir: {self.processed_dir}')
            self.remote_path = ''
        else:
            logging.info(f'Tried to remove processed_dir: {self.processed_dir} but it does not exist.')

    def __lt__(self, other):
        if not isinstance(other, GeoDataFile):
            return NotImplemented
        return self.datetime < other.datetime


@dataclass
class NexradGeoDataFile(GeoDataFile):
    scan: nexradaws.resources.awsnexradfile.AwsNexradFile
    processed_path: str
    