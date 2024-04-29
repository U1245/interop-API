"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      Core method gathering real time quality data for each sequencer

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
import os

from .lib.interop import run_info, metrics, summary
from .lib.runfolders import get_sequencer_rootdir, get_sequencer_latest_run
from .lib.runfiles import run_parameters, check_completion_files


def handle_initializing_run(result):
    """
    Allows to avoid errors when the run is initializing

    Args:
        result (dict): empty SAV result

    Returns:
        [dict]: filled SAV result dict
    """
    msg = 'Run is initializing'

    return {**result,
            'paired-end': msg,
            'total_cycles': 0,
            'last_cycles': 0,
            'run-name': msg,
            'flowcell_id': msg,
            'inst_name': '',
            'date': '',

            'p_gt_q30': '',
            'total_yield': '',
            'percent_aligned': '',
            'cluster_density': '',
            'cluster_pf_percent': '',
            'reads': '',
            'status': 'Initializing',
            'error': '',
            'q30_plot': {
                            'data':{
                                'charts': {
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
                            'options': {
                                'value': {'scale': 'interop', 'chart': ''}
                            }
                        }
            }


def get_latest_run_status(store_root, seq_list, seq_nb):
    """Core method to get the main quality metrics for the latest runs of each sequencer.
    Based on the real time copy of the sequenceur files to the acquisition server.

    Parse a -store_root- folder containing the sequencer directories.
    Gets the latest run folder for each sequencer (in each seq directory).

    Args:
        store_root (str): path to the main storage. Should contain 1 dir per sequencer.

    Returns:
        dict: Per-sequencer real time quality metrics
    """
    # Find the root dir for each sequencer
    rootdirs = get_sequencer_rootdir(store_root, seq_list, seq_nb)

    # Get the latest runfolder for each sequencer
    latest_runs = get_sequencer_latest_run(rootdirs)

    # Parse the latest runs
    result = {}
    for seq, last_run_dir in latest_runs.items():
        # Collect the results & status
        result[seq] = {}
        result[seq]['status'] = 'Idle'
        status = 'Idle'
        completion_date = ''

        # ... Handles the run initialization
        if not os.path.isfile(last_run_dir + '/RunInfo.xml'):
            result[seq] = handle_initializing_run(result[seq])
            continue

        # ... Collect the ongoing run quality data
        run_info(last_run_dir, result[seq])
        last_cycle = metrics(last_run_dir, result[seq])
        summary(last_run_dir, result[seq], seq) #is_nextseq=seq=='NextSeq'

        # ... Gather the run parameters & check if the run is completed
        run_parameters(last_run_dir, result[seq], seq)
        status, completion_date = check_completion_files(seq, last_run_dir, status)

        # Update the run status based on some metrics
        if 'init' in result[seq]['status'].lower():
            result[seq] = handle_initializing_run(result[seq])
            continue
    
        if last_cycle['last_cycle'] != last_cycle['total_cycles'] and status == 'Idle':
            status = 'Running'

        if last_cycle['last_cycle'] == 0: status = 'Initializing'
        
        # Set the global status and the completion date
        result[seq]['status'] = status
        result[seq]['completion_dt'] = completion_date

    return result


if __name__ == "__main__":
    get_latest_run_status()