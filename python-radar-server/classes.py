from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os
import nexradaws
import nexradaws.resources
import nexradaws.resources.awsnexradfile

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
    
    # data_type: DataType

    def remove_local_file(self):
        if self.local_path and os.path.exists(self.local_path):
            os.remove(self.local_path)
            print(f"Removed file: {self.local_path}")
        else:
            print("File does not exist or local_path is None")


@dataclass
class NexradGeoDataFile(GeoDataFile):
    scan: nexradaws.resources.awsnexradfile.AwsNexradFile
    