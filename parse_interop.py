import sys
import json
import collections
import numpy as np
import pandas as pd

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary, py_interop_table, py_interop_metrics, index_summary, py_interop_plot


## -------------- METRICS FOR ONGOING STATUS -------------- ##
## -------------------------------------------------------- ##
## RUN INFO -- ONGOING STATUS
def run_info(data_folder):
    run_info = py_interop_run.info()
    run_info.read(data_folder)
    total_cycles = run_info.total_cycles()
    print('\n\n## ----- RUN INFO ----- ##')
    print('... paired-end:', run_info.is_paired_end())
    print('... Total cycle :', total_cycles)
    return total_cycles


## EXTRACTION METRICS -- ONGOING STATUS
def metrics(data_folder):
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    valid_to_load[py_interop_run.Extraction]=1
    run_metrics.read(data_folder, valid_to_load)

    extraction_metrics = run_metrics.extraction_metric_set()
    last_cycle = extraction_metrics.max_cycle()
    print('\n\n## ----- METRICS ----- ##')
    print("... Last Cycle: ", last_cycle)
    return last_cycle

## SUMMARY -- ONGOING STATUS
def summary(data_folder):
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0) # Metric selection
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)

    run_folder = run_metrics.read(data_folder, valid_to_load) # Use metric selection to load data

    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary) # Modules : Run summary --> Metric summary

    print('\n\n## ----- SUMMARY ----- ##')
    print('... Global summary')
    print('... ... q30+:', summary.total_summary().percent_gt_q30())
    print('... ... total yield (G):', summary.total_summary().yield_g())
    print('... ... % aligned:', summary.total_summary().percent_aligned())

    print('\n... Per read summary')
    columns = ( ('Yield Total (G)', 'yield_g'), ('Projected Yield (G)', 'projected_yield_g'), ('% Aligned', 'percent_aligned'))
    rows = [("Read %s%d"%("(I)" if summary.at(i).read().is_index()  else " ", summary.at(i).read().number()), summary.at(i).summary()) for i in range(summary.size())]
    d = []
    for label, func in columns:
        d.append( (label, pd.Series([getattr(r[1], func)() for r in rows], index=[r[0] for r in rows])))
    df = pd.DataFrame.from_dict(dict(d))
    print(df)


## -------------- SAV METRICS FOR SPARTA -------------- ##
## ---------------------------------------------------- ##
def run_summary(data_folder, run_metrics, valid_to_load):
    """
    Gets the summary of a run
    """

    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
    run_metrics.read(data_folder, valid_to_load)

    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)

    # print("\n".join([method for method in dir(summary.total_summary()) if not method.startswith('_') and method not in ("this", "resize")]))

    columns = (
        ('Yield Total (G)', 'yield_g'), 
        ('Projected Yield (G)', 'projected_yield_g'), 
        ('% Aligned', 'percent_aligned'), 
        ('% Occupied', 'percent_occupied'), 
        ('% > Q30', 'percent_gt_q30'), 
        ('Error rate', 'error_rate')
        )

    rows = [("Read %s%d"%("(I)" if summary.at(i).read().is_index()  else " ", summary.at(i).read().number()), summary.at(i).summary()) for i in range(summary.size())]
    rows.append(('Non-Indexed Total', summary.nonindex_summary()))
    rows.append(('Total', summary.total_summary()))

    d = {}
    indexes = [r[0] for r in rows]

    for label, func in columns:
        d[label] = {}
        d[label]['serie'] = [getattr(r[1], func)() for r in rows]
        # d[label]['index'] = [r[0] for r in rows]
        # d.append( (label, pd.Series([getattr(r[1], func)() for r in rows], index=[r[0] for r in rows])))
    # df = pd.DataFrame.from_dict(dict(d))

    result = {}
    for idx in indexes:
        result[idx] = {}
        for label in d.keys():
            val = d[label]['serie'][indexes.index(idx)]
            if np.isnan(val): val = 'NaN'
            result[idx][label] = val

    return result



def get_qscore_data(data_folder, run_metrics, valid_to_load):
    """
    Gets the QScore plot data (Number of cluster vs qscore)
    """

    valid_to_load[py_interop_run.Q]=1
    run_metrics.read(data_folder, valid_to_load)

    bar_data = py_interop_plot.bar_plot_data()
    boundary = 30
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

    for x_lbl in range(int(bar_data.xyaxes().x().max())):
        if x_lbl + 1 not in values.keys():
            values[x_lbl + 1] = 0
            widths[x_lbl + 1] = 0

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


def sav_metrics(data_folder, run_metrics, valid_to_load):
    """
    Gets the 'by cycle' and 'by lane' SAV data
    """
    # Load the interop files
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load, False)
    run_metrics.read(data_folder, valid_to_load)

    # The column headers for the imaging table can be created as follows:
    columns = py_interop_table.imaging_column_vector()
    py_interop_table.create_imaging_table_columns(run_metrics, columns)

    # Convert the columns object to a list of strings.
    headers = []
    for i in range(columns.size()):
        column = columns[i]
        if column.has_children():
            headers.extend([column.name()+"("+subname+")" for subname in column.subcolumns()])
        else:
            headers.append(column.name())

    # The data from the imaging table populates a numpy ndarray
    column_count = py_interop_table.count_table_columns(columns)
    row_offsets = py_interop_table.map_id_offset()
    py_interop_table.count_table_rows(run_metrics, row_offsets)

    data = np.zeros((row_offsets.size(), column_count), dtype=np.float32)
    py_interop_table.populate_imaging_table_data(run_metrics, columns, row_offsets, data.ravel())

    # Convert the header list and data ndarray into a Pandas table.
    # index the table with the 3 first columns : lane / read / tile
    d = []
    for col, label in enumerate(headers):
        d.append( (label, pd.Series([val for val in data[:, col]], index=[tuple(r) for r in data[:, :3]])))
    df = pd.DataFrame.from_dict(dict(d))
    
    return df


def main(argv):
    """
    Core method made to parse the Illumina InterOp files.
    Produce 4 main results designed from the SAV summary tab:
        - Data by cycle, written within a csv file
        - Data by lane, written within a csv file
        - QScore data, written within a json file
        - Run summary data, written within a json file
    """
    if len(argv) != 2:
        exit('ERROR : wrong argument number')
        
    data_folder = argv[1]

    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)

    sav_df = sav_metrics(data_folder, run_metrics, valid_to_load)

    summary_result = {}
    summary_result['qscore'] = get_qscore_data(data_folder, run_metrics, valid_to_load)
    summary_result['summary'] = run_summary(data_folder, run_metrics, valid_to_load)

    
    # Write the SAV file to a csv file
    sav_df.to_csv(data_folder + '/00_Ressources/SAV_data.csv', index=False)

    # Write the run summary file to a json file
    with open(data_folder + '/00_Ressources/Run_summary.json', 'w') as f:
        f.write(json.dumps(summary_result, indent=4))


if __name__ == "__main__":
    main(sys.argv)








