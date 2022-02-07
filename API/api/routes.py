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
    ns_tracking_files_dir = 'InstrumentAnalyticsLogs'
    NS_completed_file = 'RunCompletionStatus.xml'
    MS_completed_file = 'CompletedJobInfo.xml'
    status = 'Idle'

    result = get_latest_run_status(path, ns_tracking_files_dir, NS_completed_file, MS_completed_file, status)
    return result
