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
    
    if np.isnan(num): return '-' 
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][level])

def format_q30_plot_data(data, is_nextseq):
    """
    Formats the Q30 plot data specifically for the Sparta front-end
    """
    if is_nextseq:
        max_x_label = int(sum(data['widths']) + 10)
    else:
        last_idx = 45
        for idx, val in enumerate(data['data']):
            if val != 0:
                last_idx = idx
        data['data'] = data['data'][:last_idx + 1]
        max_x_label = len(data['data']) + 1

    plot_data = {}
    plot_data['data'] = {
                    'charts': {
                        'level': 'Q score',
                        'dataset_label': data['x_title'],
                        'header': '',
                        'subheader': '',
                        'xaxis_labels': [i for i in range(1, max_x_label + 1)],
                        'x_limits': [{'read': '30', 'cycle_nb': 30}],
                        'yaxis_label': data['y_title'],
                        'series': {
                            'data': [], 
                            'metadata': {
                                'limits': [{'read': '30', 'cycle_nb': 30}],
                            }
                        }
                    }
                }
    
    # Add the qscore serie data, which is different depending on the sequencer type
    if not is_nextseq:
        low_hex_color = ('#f2fbff', '#4db0e8')
        high_hex_color = ('#ebffeb', '#08a11c')
        low_color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                'stops': [[0, low_hex_color[0]], [1, low_hex_color[1]]]
                }
        high_color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                'stops': [[0, high_hex_color[0]], [1, high_hex_color[1]]]
                }

        plot_data['data']['charts']['series']['data'] = [
                {'name': data['x_title'], 'data': [{'x': data['x_labels'][idx], 'y': y} for idx, y in enumerate(data['data'][:29])], 'color': low_color},
                {'name': data['x_title'], 'data': [{'x': data['x_labels'][idx + 29], 'y': y} for idx, y in enumerate(data['data'][29:])], 'color': high_color}
            ]
        chart_type = 'column'

    else:
        chart_type = 'area'
        previous_value = None
        previous_width = 0
        for idx, point in enumerate(data['data']):
            status = 'id' if idx == 0 else 'linkedTo'

            d = []
            if not previous_width:
                for i in range(int(data['widths'][idx])):
                    d.append(None)
                serie = {status: 'nextseq-series', 'name': data['x_title'], 'data': d, 'marker': {'enabled': False}}
                plot_data['data']['charts']['series']['data'].append(serie)
                d = []
                previous_width = previous_width + int(data['widths'][idx]-1)
    
            for i in range(previous_width):
                    d.append(None)

            for i in range(int(data['widths'][idx])+1):
                d.append(point)

            hex_color = ('#f2fbff', '#4db0e8') if previous_width < 29 else ('#faffff', '#95edeb')
            color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                    'stops': [[0, hex_color[0]], [1, hex_color[1]]]
                    } 
            serie = {status: 'nextseq-series', 'name': data['x_title'], 'data': d, 'marker': {'enabled': False}, 'color': color}
            plot_data['data']['charts']['series']['data'].append(serie)
            previous_width = previous_width + int(data['widths'][idx])

    plot_data['options'] = {'value': {'scale': 'interop', 'chart': chart_type}}
    return plot_data


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
def summary(data_folder, result, is_nextseq=False):
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

    plot_data = get_qscore_data(data_folder, run_metrics, valid_to_load, is_nextseq)
    result['q30_plot'] = format_q30_plot_data(plot_data, is_nextseq)
    
    gt30 = human_format(summary.total_summary().percent_gt_q30())
    tot_yield = human_format(summary.total_summary().yield_g())
    perc_alig = human_format(summary.total_summary().percent_aligned())
    clus_dens = human_format(np.mean(density))
    clus_pf_perc = human_format(np.mean(cluster_pf) / np.mean(cluster) * 100)

    result['p_gt_q30'] = gt30 + '%'
    result['total_yield'] = tot_yield + 'Gb'
    result['percent_aligned'] = perc_alig + '%'
    
    result['cluster_density'] = clus_dens + '/mm²'
    result['cluster_pf_percent'] = clus_pf_perc + '%'
    return result

def handle_initializing_run(result):
    msg = 'Run is initializing'

    result['paired-end'] = msg
    result['total_cycles'] = 0
    result['last_cycle'] = 0
    result['inst_name'] = ''
    result['run_name'] = msg
    result['date'] = ''
    result['flowcell_id'] = msg

    result['p_gt_q30'] = ''
    result['total_yield'] = ''
    result['percent_aligned'] = ''
    result['cluster_density'] = ''
    result['cluster_pf_percent'] = ''
    result['reads'] = []
    result['q30_plot'] = {
        'data':{ 'charts': {
                        'level': 'Q score',
                        'dataset_label': '',
                        'header': '',
                        'subheader': '',
                        'xaxis_labels': [],
                        'x_limits': [],
                        'yaxis_label': '',
                        'series': {
                            'data': [], 
                            'metadata': {
                                'limits': [{'read': '', 'cycle_nb': 0}],
                            }
                        }
                }
            },
        'options': {'value': {'scale': 'interop', 'chart': ''}}
    }
    result['status'] = 'Initializing'
    result['error'] = ''
    return result

def run_parameters(data_folder, result, seq):
    """
    """
    param_file = ('R' if seq == 'NextSeq' else 'r') + 'unParameters.xml'

    param_tree = ET.parse(data_folder + '/' + param_file)
    root = param_tree.getroot()
    
    flowcell_node = root.find('FlowCellRfidTag' if seq == 'NextSeq' else 'FlowcellRFIDTag')
    pr2_node = root.find('PR2BottleRfidTag' if seq == 'NextSeq' else 'PR2BottleRFIDTag')
    reagent_node = root.find('ReagentKitRfidTag' if seq == 'NextSeq' else 'ReagentKitRFIDTag')
    exp_name = root.find('ExperimentName')

    result['reagents'] = {}
    result['reagents']['flowcell'] = {child.tag: child.text for child in flowcell_node}
    result['reagents']['pr2_bottle'] = {child.tag: child.text for child in pr2_node}
    result['reagents']['reagent_kit'] = {child.tag: child.text for child in reagent_node}
    try:
        if exp_name.tag: result['exp_name'] = exp_name.text
    
    except AttributeError:
        result['exp_name'] = ''

def get_latest_run_status(path, ns_tracking_files_dir, NS_completion_file, MS_completion_file, status):
    """
    """
    # Get the latest runs
    latest_runs = {}
    for seq_dir in [f.path for f in os.scandir(path) if f.is_dir()]:
        if 'LOGS' not in seq_dir:
            run_dirs = [run_folder.path for run_folder in os.scandir(seq_dir) if os.path.isdir(run_folder)]
            last_run = max(run_dirs, key=os.path.getmtime)
            latest_runs[seq_dir.split('/')[-1]] = last_run

    # Parse the latest runs
    result = {}
    for seq, last_run_dir in latest_runs.items():
        status = 'Idle'
        completion_dt = ''
        error = ''

        for folder in os.scandir(last_run_dir):
            if NS_completion_file in folder.path:
                                    
                # Run status
                tree = ET.parse(last_run_dir + '/' + NS_completion_file)
                root = tree.getroot()
                status_node = root.find('CompletionStatus')
                error_node = root.find('ErrorDescription')

                # Completion datetime : last modification of the 'NS_completion_file' file
                timestamp = os.path.getmtime(last_run_dir + '/' + NS_completion_file)

                if 'completedasplanned' in status_node.text.lower(): status = 'Completed on' 
                completion_dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d   %H:%M')
                error = error_node.text
            
            if MS_completion_file in folder.path:
                tree = ET.parse(last_run_dir + '/' + MS_completion_file)
                root = tree.getroot()
                status_node = root.find('CompletionTime')
                # dt = status_node.text
                dt = status_node.text.split('T')

                status = 'Completed on'
                completion_dt = dt[0] + '   ' + ':'.join( dt[1].split('.')[0].split(':', 2)[:2] )
        
        # Collects the results & status
        result[seq] = {}

        # ... Handles the run initialization
        if not os.path.isfile(last_run_dir + '/RunInfo.xml'):
            result[seq] = handle_initializing_run(result[seq])
            continue

        # ... Collects the run data
        run_info(last_run_dir, result[seq])
        last_cycle = metrics(last_run_dir, result[seq])
        summary(last_run_dir, result[seq], is_nextseq=seq=='NextSeq')
        run_parameters(last_run_dir, result[seq], seq)

        if last_cycle['last_cycle'] != last_cycle['total_cycles'] and status == 'Idle':
            status = 'Running'

        if last_cycle['last_cycle'] == 0: status = 'Initializing'
        
        result[seq]['status'] = status
        result[seq]['error'] = error
        result[seq]['completion_dt'] = completion_dt

    return result

