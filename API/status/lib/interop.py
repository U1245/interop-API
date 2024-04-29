"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      InterOP based methods. Gather the main interOP / SAV metrics

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
import collections
import numpy as np
from datetime import datetime

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary, py_interop_plot

from .format import convert_number_format, format_q30_plot_data


def run_info(data_folder, result):
    """Picks some metadata about the sequencing run

    Args:
        data_folder (str): path of the run folder
        result (dict): global SAV result dict
    """
    # Defines some class instances
    run_info = py_interop_run.info()
    run_info.read(data_folder)

    # Gets the results
    total_cycles = run_info.total_cycles()
    try:
        date = datetime.strptime(run_info.date(), '%y%m%d')
    except ValueError:
        date = datetime.strptime(run_info.date(), '%m/%d/%Y %I:%M:%S %p')

    result['paired-end'] = run_info.is_paired_end()
    result['total_cycles'] = total_cycles
    result['inst_name'] = run_info.instrument_name()
    result['run_name'] = run_info.name()
    result['date'] = date.strftime('%d/%m/%Y')
    result['flowcell_id'] = run_info.flowcell_id()


## EXTRACTION METRICS
def metrics(data_folder, result):
    """Gets the last cycle of the current sequencing run

    Args:
        data_folder (str): path of the run folder
        result (dict): global SAV result dict

    Returns:
        [dict]: gathered results for the current method
    """
    # Defines some class instances
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    valid_to_load[py_interop_run.Extraction]=1
    run_metrics.read(data_folder, valid_to_load)

    # Gets the last cycle
    extraction_metrics = run_metrics.extraction_metric_set()
    last_cycle = extraction_metrics.max_cycle()
    result['last_cycle'] = last_cycle
    return result


def summary(data_folder, result, seq):
    """Collects the data to build a SAV-like summary table

    Args:
        data_folder (str): path of the run folder
        result (dict): global SAV result dict
        is_nextseq (bool, optional): wether the current sequencer is a nextseq. Defaults to False.

    Returns:
        [dict]: gathered results for the current method
    """
    # Defines some class instances
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0) # Metric selection
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
    run_metrics.read(data_folder, valid_to_load) # Use metric selection to load data

    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)

    # prevents from getting empty data when run is intialiazing
    if not summary.size():
        result['status'] = 'Initializing'
        return result

    # Gets a per-read summary
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

    plot_data = get_qscore_data(data_folder, run_metrics, valid_to_load, seq) #is_nextseq
    
    # prevents from getting empty data when run is intialiazing
    if not plot_data['widths']:
        result['status'] = 'Initializing'
        return result
    
    result['q30_plot'] = format_q30_plot_data(plot_data, seq) #is_nextseq
    
    gt30 = convert_number_format(summary.total_summary().percent_gt_q30())
    tot_yield = convert_number_format(summary.total_summary().yield_g())
    perc_alig = convert_number_format(summary.total_summary().percent_aligned())
    clus_dens = convert_number_format(np.mean(density))
    clus_pf_perc = convert_number_format(np.mean(cluster_pf) / np.mean(cluster) * 100)

    result['p_gt_q30'] = gt30 + '%'
    result['total_yield'] = tot_yield + 'Gb'
    result['percent_aligned'] = perc_alig + '%'
    
    result['cluster_density'] = clus_dens + '/mm²'
    result['cluster_pf_percent'] = clus_pf_perc + '%'
    return result


def get_qscore_data(data_folder, run_metrics, valid_to_load, seq):
    """Gets the QScore plot data (Number of cluster vs qscore)

    Args:
        run_folder (str): path of the run folder to analyse
        run_metrics (class): run_metrics class instance. Holding the binary interOP data.
        valid_to_load (uchar_vector): array indicating which InterOp files (== metrics) to load
        seq (str): sequencer name

    Returns:
        dict: qscore plot data
    """

    # Defines some class instances
    valid_to_load[py_interop_run.Q]=1
    run_metrics.read(data_folder, valid_to_load)

    # Collects the qscore data
    # No boundary is defined because it generates a weird display
    bar_data = py_interop_plot.bar_plot_data()
    options = py_interop_plot.filter_options(run_metrics.run_info().flowcell().naming_method())

    py_interop_plot.plot_qscore_histogram(run_metrics, options, bar_data)
    
    values = {}
    widths = {}
    for i in range(bar_data.size()):
        for j in range(bar_data.at(i).size()):
            x = bar_data.at(i).at(j).x()
            y = bar_data.at(i).at(j).y()
            width = bar_data.at(i).at(j).width()
            values[int(x)] = y
            widths[int(x)] = width
    
    if 'miseq' not in seq.lower():
        for x_lbl in range(int(bar_data.xyaxes().x().max())):
            if x_lbl + 1 not in values.keys():
                values[x_lbl + 1] = 0

    # Builds the results
    ordered_values = collections.OrderedDict(sorted(values.items()))
    ordered_widths = collections.OrderedDict(sorted(widths.items()))

    result = {
        'x_labels' : list(ordered_values.keys()),
        'data': list(ordered_values.values()),
        'widths': list(ordered_widths.values()),
        'title': bar_data.title(),
        'x_title': bar_data.xyaxes().x().label(),
        'y_title': bar_data.xyaxes().y().label(),
        'y_min': bar_data.xyaxes().y().min(),
        'y_max': bar_data.xyaxes().y().max()
    }
    return result

