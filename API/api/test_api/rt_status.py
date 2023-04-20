import os

from .rt_methods.interop import run_info, metrics, summary
from .rt_methods.runfolders import get_sequencer_rootdir, get_sequencer_latest_run
from .rt_methods.runfiles import run_parameters, check_completion_files


def handle_initializing_run(result):
    """
    Allows to avoid errors when the run is initializing

    Args:
        result (dict): global SAV result dict

    Returns:
        [dict]: filled SAV result dict
    """
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


def get_latest_run_status():
    """
    """
    # Find the root dir for each sequencer
    rootdirs = get_sequencer_rootdir("/storage/IN")

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