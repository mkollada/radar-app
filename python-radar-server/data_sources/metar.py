import json
import requests
import pandas as pd
import logging
import os
from metar import Metar
from data_source import DataSource
import tqdm

# Suppress specific warnings and errors from the metar package
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

null_handler = NullHandler()

# Suppress logging from the metar package
logging.getLogger('metar').addHandler(null_handler)
logging.getLogger('metar').propagate = False

class MetarDataSource(DataSource):
    def __init__(self, raw_data_folder='./data/metar/raw', 
                 processed_data_folder='./data/metar/processed', 
                 json_file_path='./assets/metar_stations.json'):
        super().__init__(raw_data_folder, processed_data_folder)
        self.json_file_path = json_file_path
        self.station_coords = self.load_station_coords()

    def load_station_coords(self):
        """Load station coordinates from JSON file."""
        return pd.read_json(self.json_file_path, orient='index')

    def download_data(self):
        cycle = '00'  # Example cycle
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/cycles/{cycle}Z.TXT"
        response = requests.get(url)
        response.raise_for_status()
        with open(os.path.join(self.raw_data_folder, f"{cycle}Z.TXT"), 'w') as f:
            f.write(response.text)

    def process_data(self):
        cycle = '00'  # Example cycle
        raw_file_path = os.path.join(self.raw_data_folder, f"{cycle}Z.TXT")
        processed_file_path = os.path.join(self.processed_data_folder, f"{cycle}.geojson")

        with open(raw_file_path, 'r') as f:
            data = f.read()

        metar_reports = data.strip().split('\n')
        metar_data = []

        for report in tqdm.tqdm(metar_reports, desc='Processing Metar Reports...'):
            if report.split(' ')[0] in self.station_coords.index:
                try:
                    metar_obj = Metar.Metar(report)


                    
                    station_id = metar_obj.station_id
                    # if station_id not in self.station_coords.index:
                    #     logging.warning(f"Coordinates for station {station_id} not found.")
                    #     continue

                    metar_info = {
                        'station_id': station_id,
                        # 'time': metar_obj.time.isoformat() if metar_obj.time else '',
                        # 'temperature': metar_obj.temp.value('C') if metar_obj.temp else '',
                        # 'dew_point': metar_obj.dewpt.value('C') if metar_obj.dewpt else '',
                        'wind_speed': metar_obj.wind_speed.value('KT') if metar_obj.wind_speed else '',
                        'wind_direction': metar_obj.wind_dir.value() if metar_obj.wind_dir else '',
                        # 'visibility': metar_obj.vis.value('M') if metar_obj.vis else '',
                        # 'pressure': metar_obj.press.value('HPA') if metar_obj.press else '',
                        # 'weather': ' '.join([str(w) for w in metar_obj.weather]) if metar_obj.weather else '',
                        'latitude': self.station_coords.loc[station_id, 'latitude'],
                        'longitude': self.station_coords.loc[station_id, 'longitude']
                    }
                    if (metar_info['wind_speed'] == '') or (metar_info['wind_direction'] == '') or \
                            (metar_info['wind_speed'] == 0) or (metar_info['wind_direction'] == 0):
                        pass
                    else:
                        metar_data.append(metar_info)
                except Exception as e:
                    logging.error(f"Failed to parse METAR report: {report}")
                    logging.error(e)

        df = pd.DataFrame(metar_data)
        geojson = self.metar_to_geojson(df)

        with open(processed_file_path, 'w') as f:
            f.write(json.dumps(geojson))  # Convert the geojson dictionary to a JSON string before writing

    def metar_to_geojson(self, df):
        """Convert METAR DataFrame to GeoJSON format."""
        features = []
        for _, row in df.iterrows():
            feature = {
                "type": "Feature",
                "properties": {
                    "station_id": row['station_id'],
                    # "time": row['time'],
                    # "temperature": row['temperature'],
                    # "dew_point": row['dew_point'],
                    "wind_speed": row['wind_speed'],
                    "wind_direction": row['wind_direction'],
                    # "visibility": row['visibility'],
                    # "pressure": row['pressure'],
                    # "weather": row['weather']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        return geojson

    def get_processed_data(self):
        cycle = '00'  # Example cycle
        processed_file_path = os.path.join(self.processed_data_folder, f"{cycle}.geojson")
        with open(processed_file_path, 'r') as f:
            data = f.read()
        
        # Validate JSON
        try:
            json_data = json.loads(data)
            return json_data  # Return the parsed JSON data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON data in {processed_file_path}: {e}")
            return None  # Or handle the error as needed
