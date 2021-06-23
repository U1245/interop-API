import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from parse_interop import summary, run_info, metrics

def get_latest_run_status(path, ns_tracking_files_dir, status):

    latest_runs = {}
    for seq_dir in [f.path for f in os.scandir(path) if f.is_dir()]:
        if 'LOGS' not in seq_dir:
            run_dirs = [run_folder.path for run_folder in os.scandir(seq_dir) if os.path.isdir(run_folder)]
            last_run = max(run_dirs, key=os.path.getmtime)
            latest_runs[seq_dir.split('/')[-1]] = last_run

    for seq, last_run_dir in latest_runs.items():
        status = 'Idle'
        error = ''
        for folder in os.scandir(last_run_dir):
        
            if ns_tracking_files_dir in folder.path:
                
                track_dir = last_run_dir + '/' + ns_tracking_files_dir
                tracking_files = [track_file.path for track_file in os.scandir(track_dir) if os.path.isfile(track_file)]
                last_track_file = max(tracking_files, key=os.path.getmtime)
                
                spltd_track_file = last_track_file.split('__')
                # if spltd_track_file[4] == 'Run.imf1' and spltd_track_file[3] != '0001': status = 'Run over'
                if spltd_track_file[4] == 'RunCycle': 
                    cycle_nb = spltd_track_file[5].split('.')[0]
                    status = 'Nextseq Running - Current cycle : ' + cycle_nb
                elif spltd_track_file[4] == 'RunSetup': status = 'Run starting'
            
            if NS_completed_file in folder.path:
                tree = ET.parse(last_run_dir + '/' + NS_completed_file)
                ctime = os.path.getmtime(last_run_dir + '/' + NS_completed_file)
                print(ctime)

                root = tree.getroot()
                status_node = root.find('CompletionStatus')
                error_node = root.find('ErrorDescription')

                status = status_node.text
                error = error_node.text
            
            if MS_completed_file in folder.path:
                tree = ET.parse(last_run_dir + '/' + MS_completed_file)
                root = tree.getroot()
                status_node = root.find('CompletionTime')
                dt = status_node.text
                dt = status_node.text.split('T')

                status = 'Run completed in ' + dt[0] + ' at ' + dt[1].split('.')[0]

        
        print('\n\n################################ ' + seq.upper() + ' ################################')
        total_cycle = run_info(last_run_dir)
        last_cycle = metrics(last_run_dir)
        summary(last_run_dir)
        if last_cycle != total_cycle:
            status = 'Running - current cycle :' + str(last_cycle)

        print('\n## ----- STATUS ----- ##')
        print('Status :', status, ', Error :', error)
            




path = '/storage/IN/'
ns_tracking_files_dir = 'InstrumentAnalyticsLogs'
NS_completed_file = 'RunCompletionStatus.xml'
MS_completed_file = 'CompletedJobInfo.xml'
status = 'Idle'

get_latest_run_status(path, ns_tracking_files_dir, status)