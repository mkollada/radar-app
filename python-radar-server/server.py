from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import threading
import time
import os

from data_sources.metar import MetarDataSource

app = Flask(__name__)
CORS(app)

local_data_folder = './data'
metar_raw_data_folder = os.path.join(local_data_folder, './metar/raw')
metar_processed_data_folder = os.path.join(local_data_folder, './metar/processed')
json_file_path = './assets/metar_stations.json'

# Initialize data sources
metar_data_source = MetarDataSource(metar_raw_data_folder, metar_processed_data_folder, json_file_path)

def schedule_downloads():
    while True:
        metar_data_source.download_and_process_data()
        time.sleep(1800)  # Sleep for 30 minutes

# Start the download scheduler in a separate thread
# scheduler_thread = threading.Thread(target=schedule_downloads)
# scheduler_thread.daemon = True
# scheduler_thread.start()

@app.route('/')
def index():
    return "Welcome to the NEXRAD Data API!"

@app.route('/metar', methods=['GET'])
def get_metar_data_route():
    try:
        data = metar_data_source.get_processed_data()
        return data
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
