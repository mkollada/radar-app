# nexrad_utils.py
import pyart
import numpy as np
import datetime
import pytz
from geojson import Feature, FeatureCollection, Point
from concurrent.futures import ProcessPoolExecutor

def process_chunk(chunk):
    features = []
    lats, lons, reflectivity = chunk
    for i in range(lats.shape[0]):
        for j in range(lats.shape[1]):
            if not np.isnan(reflectivity[i, j]):  # Only include valid reflectivity values
                point = Point((lons[i, j], lats[i, j]))
                feature = Feature(geometry=point, properties={"reflectivity": float(reflectivity[i, j])})
                features.append(feature)
    return features

def nexrad_to_geojson(file_path, num_workers=4):
    # Read the NEXRAD file
    radar = pyart.io.read_nexrad_archive(file_path)
    
    # Extract the reflectivity field
    reflectivity = radar.fields['reflectivity']['data']
    
    # Extract the geographic information
    lats = radar.gate_latitude['data']
    lons = radar.gate_longitude['data']
    
    # Split the data into chunks for parallel processing
    chunks = [(lats[i::num_workers, :], lons[i::num_workers, :], reflectivity[i::num_workers, :]) 
              for i in range(num_workers)]
    
    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(process_chunk, chunks)
    
    # Combine the results from all workers
    features = []
    for result in results:
        features.extend(result)
    
    # Create a FeatureCollection
    feature_collection = FeatureCollection(features)
    
    return feature_collection

def parse_nexrad_query_params(args):
    start_year = int(args.get('start_year'))
    start_month = int(args.get('start_month'))
    start_day = int(args.get('start_day'))
    start_hour = int(args.get('start_hour'))
    start_minute = int(args.get('start_minute'))
    end_year = int(args.get('end_year'))
    end_month = int(args.get('end_month'))
    end_day = int(args.get('end_day'))
    end_hour = int(args.get('end_hour'))
    end_minute = int(args.get('end_minute'))
    station = args.get('station')

    eastern_timezone = pytz.timezone('US/Eastern')
    start = eastern_timezone.localize(datetime.datetime(start_year, start_month, start_day, start_hour, start_minute))
    end = eastern_timezone.localize(datetime.datetime(end_year, end_month, end_day, end_hour, end_minute))

    if not (start_year and start_month and start_day and station):
        raise ValueError("Missing required parameters: year, month, day, station")

    return start, end, station
