from flask import Flask, jsonify, send_file
from flask_cors import CORS
import logging
import threading
import time
import os
import zipfile
import io

from data_sources.metar import MetarDataSource
from data_sources.gfs import GFSDataSource

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

local_data_folder = './data'

metar_raw_data_folder = os.path.join(local_data_folder, 'metar/raw')
metar_processed_data_folder = os.path.join(local_data_folder, 'metar/processed')
json_file_path = './assets/metar_stations.json'

gfs_raw_data_folder = os.path.join(local_data_folder, 'gfs/raw')
gfs_processed_data_folder = os.path.join(local_data_folder, 'gfs/processed')

# Initialize data sources
metar_data_source = MetarDataSource(metar_raw_data_folder, metar_processed_data_folder, json_file_path)
gfs_data_source = GFSDataSource(raw_data_folder=gfs_raw_data_folder,
                                processed_data_folder=gfs_processed_data_folder)

def schedule_downloads():
    while True:
        metar_data_source.download_and_process_data()
        gfs_data_source.download_data()  # Assuming you also want to schedule GFS data downloads
        time.sleep(1800)  # Sleep for 30 minutes

# Start the download scheduler in a separate thread
# scheduler_thread = threading.Thread(target=schedule_downloads)
# scheduler_thread.daemon = True
# scheduler_thread.start()

def zip_directory(folder_path):
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zf.write(os.path.join(root, file),
                         os.path.relpath(os.path.join(root, file),
                                         os.path.join(folder_path, '..')))
    memory_file.seek(0)
    return memory_file

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

@app.route('/gfs', methods=['GET'])
def get_gfs_data_route():
    try:
        memory_file = zip_directory(gfs_processed_data_folder)
        return send_file(memory_file, download_name='gfs_data.zip', as_attachment=True)
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
