import requests
from metar import Metar
import pandas as pd
import logging
import csv

def fetch_metar_data(cycle):
    """Fetch the raw METAR data for the specified cycle."""
    url = f"https://tgftp.nws.noaa.gov/data/observations/metar/cycles/{cycle}Z.TXT"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching METAR data: {e}")
        raise

def parse_metar_data(data):
    """Parse raw METAR data into a list of dictionaries."""
    metar_reports = data.strip().split('\n')
    metar_data = []

    for report in metar_reports:
        try:
            metar_obj = Metar.Metar(report)
            metar_info = {
                'station_id': metar_obj.station_id,
                'time': metar_obj.time.isoformat() if metar_obj.time else None,
                'temperature': metar_obj.temp.value('C') if metar_obj.temp else None,
                'dew_point': metar_obj.dewpt.value('C') if metar_obj.dewpt else None,
                'wind_speed': metar_obj.wind_speed.value('KT') if metar_obj.wind_speed else None,
                'wind_direction': metar_obj.wind_dir.value() if metar_obj.wind_dir else None,
                'visibility': metar_obj.vis.value('M') if metar_obj.vis else None,
                'pressure': metar_obj.press.value('HPA') if metar_obj.press else None,
                'weather': ' '.join([str(w) for w in metar_obj.weather]) if metar_obj.weather else None
            }
            metar_data.append(metar_info)
        except Exception as e:
            logging.error(f"Failed to parse METAR report: {report}")
            logging.error(e)
    return metar_data

def load_station_coordinates(file_path='metar_station_info.csv'):
    """Load station coordinates from a CSV file."""
    coordinates = {}
    with open(file_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        for rows in reader:
            station_id = rows['station_id']
            latitude = float(rows['latitude'])
            longitude = float(rows['longitude'])
            coordinates[station_id] = {'latitude': latitude, 'longitude': longitude}
    return coordinates

def get_metar_data(cycle='00', station_file='metar_station_info.csv'):
    """Fetch and parse METAR data for a specific cycle, returning a pandas DataFrame."""
    raw_data = fetch_metar_data(cycle)
    metar_data = parse_metar_data(raw_data)
    df = pd.DataFrame(metar_data)
    
    # Load station coordinates
    coordinates = load_station_coordinates(station_file)
    
    # Add coordinates to the DataFrame
    df['latitude'] = df['station_id'].apply(lambda x: coordinates.get(x, {}).get('latitude'))
    df['longitude'] = df['station_id'].apply(lambda x: coordinates.get(x, {}).get('longitude'))
    
    return df

def metar_to_geojson(df):
    """Convert METAR DataFrame to GeoJSON format."""
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "properties": {
                "station_id": row['station_id'],
                "time": row['time'],
                "temperature": row['temperature'],
                "dew_point": row['dew_point'],
                "wind_speed": row['wind_speed'],
                "wind_direction": row['wind_direction'],
                "visibility": row['visibility'],
                "pressure": row['pressure'],
                "weather": row['weather']
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
