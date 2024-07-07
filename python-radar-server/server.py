from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging

from data_sources.mrms import MRMSDataSource, MRMSDataType
from data_sources.nexrad import NexradDataSource


app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

local_data_folder = './data'
next_app_public_dir = '../radar-app/public'
next_tiles_dir = os.path.join(next_app_public_dir,'tiles')



# Initialize data sources
mrms_data_source = MRMSDataSource( 
    raw_data_folder=os.path.join(local_data_folder,'mrms','raw'),
    processed_data_folder=os.path.join(next_tiles_dir,'mrms'),
    data_types=[
        MRMSDataType(
            name='PrecipRate', 
            variable_name='unknown',
            type_of_level=None,
        ),
        MRMSDataType(
            name='SeamlessHSR', 
            variable_name='unknown',
            type_of_level=None,
        )
    ],
    n_files=3
)

data_sources = {}
data_sources['mrms'] = mrms_data_source

nexrad_data_source = NexradDataSource(raw_data_folder='./data/nexrad/raw/', processed_data_folder='../radar-app/public/nexrad', data_types=None)



@app.route('/')
def index():
    return "Welcome to the Spartan Weather Data API!"

@app.route('/update-data', methods=['GET'])
def updateData():
    try:
        update_data_dirs = {}
        for data_source in data_sources:
            print(f'{data_source} found. Updating data...')
            
            data_dirs = data_sources[data_source].download_data()
            update_data_dirs[data_source] = {}
            for data_type in data_dirs:
                update_data_dirs[data_source][data_type] = []
                for dir in data_dirs[data_type]:
                    new_dir = os.path.join(*dir.split('/')[4:])
                    update_data_dirs[data_source][data_type].append(new_dir)
            
            return jsonify({"dataLocs":update_data_dirs}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    else:
        error = f'{data_source} is not an active data source.'
        logging.error(f"Error: {error}")
        return jsonify({"error": str(error)}), 404
    
@app.route('/update-nexrad-site/<path:site_code>/<path:variable_name>', methods=['GET'])
def updateNexradSite(site_code: str, variable_name: str):
    processed_file = nexrad_data_source.download_data(site_code=site_code, variable_name=variable_name)

    return jsonify({'processed_file':processed_file}), 200


if __name__ == '__main__':
    app.run(debug=True)
