from flask import Flask, jsonify, request
import os
import logging
import pandas as pd
import requests

import nexradaws
from goes2go import GOES

from data_sources.mrms_utils import fetch_and_download_mrms_data
from data_sources.nexrad_utils import parse_nexrad_query_params, nexrad_to_geojson
from data_sources.metar_utils import get_metar_data, metar_to_geojson
from data_sources.goes_utils import parse_goes_query_params, copy_files_to_directory

app = Flask(__name__)

local_data_folder = '../data'
mrms_data_folder = os.path.join(local_data_folder, 'mrms')
nexrad_data_folder = os.path.join(local_data_folder, 'nexrad')
goes_data_folder = os.path.join(local_data_folder, 'goes')
default_goes_download_folder = os.path.expanduser('~/data')

# Initialize NEXRAD AWS interface
nexrad_interface = nexradaws.NexradAwsInterface()

@app.route('/')
def index():
    return "Welcome to the NEXRAD Data API!"

@app.route('/mrms/<path:subdir>', methods=['GET'])
def get_mrms_data(subdir):
    base_url = f'https://mrms.ncep.noaa.gov/data/2D/{subdir}/'
    subdir_path = os.path.join(mrms_data_folder, subdir)

    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path, exist_ok=True)
    
    try:
        downloaded_files = fetch_and_download_mrms_data(base_url, subdir_path, subdir)
        return jsonify({'message': 'Downloaded files', 'files': downloaded_files})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/goes', methods=['GET'])
def get_goes_data():
    try:
        start, end = parse_goes_query_params(request.args)
        product = request.args.get('product', 'ABI-L2-ACHAC')
        
        G = GOES(product=product)
        files = G.timerange(start, end)
        
        # Move downloaded files to the specified directory
        copy_files_to_directory(default_goes_download_folder, os.path.dirname(files.file[0]), goes_data_folder)

        return jsonify({'message': 'Downloaded and moved files', 'files': [os.path.join(goes_data_folder, f) for f in files.file.values.tolist()]})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/nexrad', methods=['GET'])
def get_nexrad_data():
    # Extract query parameters
    try:
        start, end, station = parse_nexrad_query_params(request.args)
        if start > end:
            return jsonify({"error": "Start time must be before end time."})

        available_scans = nexrad_interface.get_avail_scans_in_range(start, end, station)
        files = nexrad_interface.download(available_scans, nexrad_data_folder, keep_aws_folders=True)
        # Convert the downloaded NEXRAD files to GeoJSON
        # geojson_files = nexrad_to_geojson(files, nexrad_data_folder)
        return jsonify({"files":[f.key for f in files.iter_success()]})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/metar', methods=['GET'])
def get_metar_data_route():
    try:
        cycle = request.args.get('cycle', '00')
        df = get_metar_data(cycle=cycle)
        geojson = metar_to_geojson(df)
        return jsonify(geojson)
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/weather-alerts', methods=['GET'])
def get_weather_alerts():
    try:
        response = requests.get('https://api.weather.gov/alerts/active')
        response.raise_for_status()  # Check if the request was successful
        alerts_data = response.json()
        return jsonify(alerts_data)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/nomads', methods=['GET'])
def get_nomads_data():
    try:
        response = requests.get('https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gdas.20240618/00/atmos/gdas.t00z.atmf003.nc')
        response.raise_for_status()  # Check if the request was successful
        alerts_data = response.json()
        return jsonify(alerts_data)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching nomads: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
