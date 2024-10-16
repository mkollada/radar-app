from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
import threading
from datetime import timedelta
from typing import Tuple, Dict

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
    time_delta=timedelta(hours=1)
)
# NEXRAD
nexrad_data_source = NexradDataSource(
    raw_data_folder='./data/raw/nexrad/',
    processed_data_folder='../radar-app/public/nexrad',
    time_delta=timedelta(minutes=30)
)

# GPM
gpm_data_source = GPMDataSource(
    raw_data_folder='./data/raw/gpm/',
    processed_data_folder='../radar-app/public/tiles/gpm/',
    time_delta=timedelta(hours=8)
)

# Satellite
sat_data_source = SatDataSource(
    raw_data_folder='./data/raw/satellite/',
    processed_data_folder='../radar-app/public/tiles/satellite',
    time_delta=timedelta(hours=5)
)

# Global lock for synchronizing all data updates
global_update_lock = threading.Lock()

def prep_data_source_result(result: Tuple[str, str]) -> Dict[str, str]:
    radar_app_locs = {}
    for loc, time in result:
        radar_app_locs[time] = os.path.join(*loc.split('/')[4:])
    return radar_app_locs


@app.route('/')
def index():
    return "Welcome to the Spartan Weather Data API!"

@app.route('/update-gpm-data', methods=['GET'])
def updateGPMData():
    logging.info("Received request to update GPM data")
    with global_update_lock:
        logging.info("Acquired lock for updating GPM data")
        try:
            processed_locs_with_time = gpm_data_source.update_data()
            radar_app_locs = prep_data_source_result(processed_locs_with_time)
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
            processed_locs_with_time = mrms_data_source.update_data()
            radar_app_locs = prep_data_source_result(processed_locs_with_time)
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
            processed_locs_with_time = sat_data_source.update_data()
            radar_app_locs = prep_data_source_result(processed_locs_with_time)
            logging.info("Processed locations: %s", radar_app_locs)
            return jsonify({"directories": radar_app_locs}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating Satellite data")

@app.route('/update-nexrad-data', methods=['GET'])
def updateNexradData():
    logging.info("Received request to update Nexrad data")
    with global_update_lock:
        logging.info("Acquired lock for updating Satellite data")
        try:
            processed_locs = nexrad_data_source.update_data()
            radar_app_locs = []
            for loc in processed_locs:
                radar_app_loc = os.path.join(*loc.split('/')[4:])
                radar_app_locs.append(radar_app_loc)
            logging.info("Processed locations: %s", radar_app_locs)
            return jsonify({"success": True}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            logging.info("Released lock for updating Satellite data")


@app.route('/get-nexrad-site-data/<path:site_code>/<path:variable_name>', methods=['GET'])
def getNexradSiteData(site_code: str, variable_name: str):
    logging.info("Received request to get NEXRAD site data")
    radar_app_dir = f'../radar-app/public/nexrad/{variable_name}/{site_code}/'
    images = os.listdir(radar_app_dir)
    
    
    return images

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

@app.route('/get-most-recent-mrms')
def getMostRecentMRMS():
    logging.info("Received request to get most recent MRMS data.")
    loc = mrms_data_source.get_processed_locs()[-1]

    radar_app_loc = os.path.join('tiles',*loc.split('/')[4:])
    
    print(radar_app_loc)

    return jsonify({'tileDir':radar_app_loc}), 200

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.run(debug=True)
