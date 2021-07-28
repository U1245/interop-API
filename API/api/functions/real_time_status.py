import os
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary, py_interop_table
from .parse_interop import get_qscore_data

## -------------- METHODS FOR ONGOING STATUS -------------- ##
## -------------------------------------------------------- ##
def human_format(num):
    """
    """
    level = 0
    while abs(num) >= 1000:
        level += 1
        num /= 1000.0
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][level])

## RUN INFO
def run_info(data_folder, result):
    """
    """
    run_info = py_interop_run.info()
    run_info.read(data_folder)
    total_cycles = run_info.total_cycles()
    date = datetime.strptime(run_info.date(), '%y%m%d')

    result['paired-end'] = run_info.is_paired_end()
    result['total_cycles'] = total_cycles
    result['inst_name'] = run_info.instrument_name()
    result['run_name'] = run_info.name()
    result['date'] = date.strftime('%d/%m/%Y')
    result['flowcell_id'] = run_info.flowcell_id()
    return result

## EXTRACTION METRICS
def metrics(data_folder, result):
    """
    """
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    valid_to_load[py_interop_run.Extraction]=1
    run_metrics.read(data_folder, valid_to_load)

    extraction_metrics = run_metrics.extraction_metric_set()
    last_cycle = extraction_metrics.max_cycle()
    result['last_cycle'] = last_cycle
    return result

## SUMMARY
def summary(data_folder, result):
    """
    """
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0) # Metric selection
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
    run_metrics.read(data_folder, valid_to_load) # Use metric selection to load data

    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary) # Modules : Run summary --> Metric summary

    density = []
    density_pf = []
    cluster= []
    cluster_pf = []
    result['reads'] = []
    for read_id in range(summary.size()):
        result['reads'].append({
            'read_id': summary.at(read_id).read().number(),
            'first_cycle': summary.at(read_id).read().first_cycle(),
            'last_cycle': summary.at(read_id).read().last_cycle(),
            'total_cycles': summary.at(read_id).read().total_cycles(),
            'is_index': summary.at(read_id).read().is_index()
        })

        for lane_id in range(summary.at(read_id).size()):
            density.append(summary.at(read_id).at(lane_id).density().mean())
            density_pf.append(summary.at(read_id).at(lane_id).density_pf().mean())
            cluster.append(summary.at(read_id).at(lane_id).cluster_count().mean())
            cluster_pf.append(summary.at(read_id).at(lane_id).cluster_count_pf().mean())

    result['p_gt_q30'] = summary.total_summary().percent_gt_q30()
    result['q30_plot'] = get_qscore_data(data_folder, run_metrics, valid_to_load) # summary.total_summary().percent_gt_q30()

    result['total_yield'] = human_format(summary.total_summary().yield_g()) + 'Gb'
    result['percent_aligned'] = human_format(summary.total_summary().percent_aligned()) + '%'
    
    result['cluster_density'] = human_format(np.mean(density)) + '/mm²'
    result['cluster_pf_percent'] = human_format(np.mean(cluster_pf) / np.mean(cluster) * 100) + '%'
    return result


def get_latest_run_status(path, ns_tracking_files_dir, NS_completed_file, MS_completed_file, status):
    """
    """
    # Gets the latest runs
    latest_runs = {}
    for seq_dir in [f.path for f in os.scandir(path) if f.is_dir()]:
        if 'LOGS' not in seq_dir:
            run_dirs = [run_folder.path for run_folder in os.scandir(seq_dir) if os.path.isdir(run_folder)]
            last_run = max(run_dirs, key=os.path.getmtime)
            latest_runs[seq_dir.split('/')[-1]] = last_run

    # Parses the latest runs
    result = {}
    for seq, last_run_dir in latest_runs.items():
        status = 'Idle'
        error = ''
        for folder in os.scandir(last_run_dir):
            
            if ns_tracking_files_dir in folder.path:
                track_dir = last_run_dir + '/' + ns_tracking_files_dir
                tracking_files = [track_file.path for track_file in os.scandir(track_dir) if os.path.isfile(track_file)]
                last_track_file = max(tracking_files, key=os.path.getmtime)
                
                spltd_track_file = last_track_file.split('__')
                if spltd_track_file[4] == 'RunCycle': 
                    cycle_nb = spltd_track_file[5].split('.')[0]
                    status = 'Nextseq Running - Current cycle : ' + cycle_nb
                elif spltd_track_file[4] == 'RunSetup': status = 'Run starting'
            
            if NS_completed_file in folder.path:
                tree = ET.parse(last_run_dir + '/' + NS_completed_file)
                ctime = os.path.getmtime(last_run_dir + '/' + NS_completed_file)

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

                status = 'Run completed on ' + dt[0] + ' at ' + dt[1].split('.')[0]
        
        result[seq] = {}
        total_cycle = run_info(last_run_dir, result[seq])
        last_cycle = metrics(last_run_dir, result[seq])
        summary(last_run_dir, result[seq])

        if last_cycle['last_cycle'] != last_cycle['total_cycles']:
            status = 'Running - current cycle :' + str(last_cycle['last_cycle'])
        
        result[seq]['status'] = status
        result[seq]['error'] = error

    return result

