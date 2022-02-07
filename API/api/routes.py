from flask import Flask
from flask_cors import CORS

from .functions.real_time_status import get_latest_run_status

# Init the app
app = Flask(__name__)
cors = CORS(app, resources={r"/interop/": {"origins": "http://sparta.univ-rouen.fr"}})

# Routes
@app.route("/interop/", methods=['GET'])
def real_time_data():
    """
    Gets the real-time data of the sequencers

    Returns:
        [dict]: global SAV result dict
    """
 
    path = '/storage/IN/'
    NS_completed_file = 'RunCompletionStatus.xml'
    MS_completed_file = 'CompletedJobInfo.xml'

    result = get_latest_run_status(path, NS_completed_file, MS_completed_file)
    return result
