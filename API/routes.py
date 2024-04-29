"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      Routes of the Flask API

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
from flask import Flask
from flask_cors import CORS

from API.status.main import get_latest_run_status

# Init the app
app = Flask(__name__)
cors = CORS(app, resources={r"/interop/": {"origins": "*"}})

# Routes
@app.route("/interop/", methods=['GET'])
def real_time_data():
    """Gets the real-time data of the sequencers
    
    The store_root is expected to hold a directory per sequencer
    This is the main storage path in the local acquisition server
    e.g.
    >$ ls -al /PATH/TO/MAIN/STORAGE/
              - MiSeq1
              - MiSeq2
              - NextSeq1
              - NextSeq2
              - NovaSeq1
              - NovaSeq2

    Returns:
        [dict]: Real-time result per sequencer
    """
    # TODO should use a config file to hold these parameters
    store_root = '/PATH/TO/MAIN/STORAGE'
    seq_list = ['MiSeq', 'NextSeq', 'NovaSeq']   # The different sequencer name. Allows to find their root directory
    seq_nb = 4                                   # number of sequencer. Set the number of sequencer root directory to retrieve

    # Returns main quality metrics of the last run for each sequencer
    result = get_latest_run_status(store_root, seq_list, seq_nb)
    return result
