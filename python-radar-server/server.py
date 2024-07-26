from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
import threading

from data_sources.mrms import MRMSDataSource
from data_sources.nexrad import NexradDataSource
from data_sources.gpm import GPMDataSource
from data_sources.satellite import SatDataSource

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

local_data_folder = './data'
next_app_public_dir = '../radar-app/public'
next_tiles_dir = os.path.join(next_app_public_dir, 'tiles')

### Initialize data sources
# MRMS
mrms_data_source = MRMSDataSource(
    raw_data_folder=os.path.join(local_data_folder, 'raw', 'mrms'),
    processed_data_folder=os.path.join(next_tiles_dir, 'mrms'),
    n_files=20
)
# NEXRAD
nexrad_data_source = NexradDataSource(
    raw_data_folder='./data/nexrad/raw/',
    processed_data_folder='../radar-app/public/nexrad',
)

# GPM
gpm_data_source = GPMDataSource(
    raw_data_folder='./data/raw/gpm/',
    processed_data_folder='../radar-app/public/tiles/gpm/',
    n_files=3
)

# Satellite
sat_data_source = SatDataSource(
    raw_data_folder='./data/raw/satellite/',
    processed_data_folder='../radar-app/public/tiles/satellite',
    n_files=6
)

# Global lock for synchronizing all data updates
global_update_lock = threading.Lock()

@app.route('/')
def index():
    return "Welcome to the Spartan Weather Data API!"

@app.route('/update-gpm-data', methods=['GET'])
def updateGPMData():
    logging.info("Received request to update GPM data")
    with global_update_lock:
        logging.info("Acquired lock for updating GPM data")
        try:
            processed_locs = gpm_data_source.update_data()
            radar_app_locs = []
            for loc in processed_locs:
                radar_app_loc = os.path.join(*loc.split('/')[4:])
                radar_app_locs.append(radar_app_loc)
            logging.info("Processed locations: %s", radar_app_locs)
            return jsonify({"directories": radar_app_locs}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating GPM data")

@app.route('/update-mrms-data', methods=['GET'])
def updateMRMSData():
    logging.info("Received request to update MRMS data")
    with global_update_lock:
        logging.info("Acquired lock for updating MRMS data")
        try:
            processed_locs = mrms_data_source.update_data()
            radar_app_locs = []
            for loc in processed_locs:
                radar_app_loc = os.path.join(*loc.split('/')[4:])
                radar_app_locs.append(radar_app_loc)
            logging.info("Processed locations: %s", radar_app_locs)
            return jsonify({"directories": radar_app_locs}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating MRMS data")

@app.route('/update-satellite-data', methods=['GET'])
def updateSatelliteData():
    logging.info("Received request to update Satellite data")
    with global_update_lock:
        logging.info("Acquired lock for updating Satellite data")
        try:
            processed_locs = sat_data_source.update_data()
            radar_app_locs = []
            for loc in processed_locs:
                radar_app_loc = os.path.join(*loc.split('/')[4:])
                radar_app_locs.append(radar_app_loc)
            logging.info("Processed locations: %s", radar_app_locs)
            return jsonify({"directories": radar_app_locs}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating Satellite data")

@app.route('/update-nexrad-site/<path:site_code>/<path:variable_name>', methods=['GET'])
def updateNexradSite(site_code: str, variable_name: str):
    logging.info("Received request to update NEXRAD site data")
    with global_update_lock:
        logging.info("Acquired lock for updating NEXRAD site data")
        try:
            processed_file = nexrad_data_source.update_data(site_code=site_code, variable_name=variable_name)
            processed_file_radar_app_loc = os.path.join(*processed_file.split('/')[4:])
            logging.info("Processed file location: %s", processed_file_radar_app_loc)
            return jsonify({'imageUrl': processed_file_radar_app_loc}), 200
        except Exception as e:
            logging.error(f"Error in /nexrad-update-data route: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating NEXRAD site data")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.run(debug=True)
