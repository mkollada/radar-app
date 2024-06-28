from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging

from data_sources.mrms import MRMSDataSource, MRMSDataType


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
            name='SeamlessHSR', 
            variable_name='unknown',
            type_of_level=None,
        )
    ],
    n_files=10
)

data_sources = {}
data_sources['mrms'] = mrms_data_source


@app.route('/')
def index():
    return "Welcome to the Spartan Weather Data API!"

@app.route('/update-data/<data_source>/<data_type_name>', methods=['GET'])
def updateData(data_source, data_type_name):
    if data_source in data_sources:
        print(f'{data_source} found. Updating data...')
        try:
            data_dirs = data_sources[data_source].download_data(data_type_name)
            return jsonify({"directories":data_dirs}), 200
        except Exception as e:
            logging.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500

    else:
        error = f'{data_source} is not an active data source.'
        logging.error(f"Error: {error}")
        return jsonify({"error": str(error)}), 404


if __name__ == '__main__':
    app.run(debug=True)
