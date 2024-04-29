
"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
    Methods to format the data

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
import numpy as np


def convert_number_format(num):
    """
    Converts a number into a human readable format, with size suffix

    Args:
        num [int]: number to format

    Returns:
        [str]: formatted number
    """
    level = 0
    while abs(num) >= 1000:
        level += 1
        num /= 1000.0
    
    if np.isnan(num): return '-' 
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][level])


def format_q30_plot_data(data, seq): #is_nextseq
    """
    Formats the Q30 plot data specifically for the Sparta front-end
    
    Args:
        data (): [description]
        seq (str): sequencer name

    Returns:
        [dict]: formatted data to display the real time Qscore bar-chart 
    """
    # Set-up the result format that has to be returned for the Sparta highchart component needs
    max_x_label = data['x_labels'][-1] if 'miseq' in seq.lower() else int(sum(data['widths']) + 10)

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
    
    # Adds the qscore serie data, which is different depending on the sequencer type
    if 'miseq' in seq.lower(): #not is_nextseq:

        # Format the data and complete the missing values
        labels = [i for i in range(1, max_x_label + 1)]
        data['widths'] = [1.0 for x in labels]
        values = [0] * len(labels)
        for idx, x_pos in enumerate(data['x_labels']):
            values[x_pos - 1] = data['data'][idx]

        # Define the chart serie options
        chart_type = 'column'
        low_hex_color = ('#f2fbff', '#4db0e8')
        high_hex_color = ('#ebffeb', '#08a11c')
        low_color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                     'stops': [[0, low_hex_color[0]], [1, low_hex_color[1]]]
                    }
        high_color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                      'stops': [[0, high_hex_color[0]], [1, high_hex_color[1]]]
                     }

        # plot_data['data']['charts']['series']['data'] = [
        #         {'name': data['x_title'], 'data': [{'x': data['x_labels'][idx], 'y': y} for idx, y in enumerate(data['data'][:29])], 'color': low_color},
        #         {'name': data['x_title'], 'data': [{'x': data['x_labels'][idx + 29], 'y': y} for idx, y in enumerate(data['data'][29:])], 'color': high_color}
        #     ]
        plot_data['data']['charts']['series']['data'] = [
            {'name': data['x_title'], 'data': [{'x': labels[idx], 'y': y} for idx, y in enumerate(values[:29])], 'color': low_color},
            {'name': data['x_title'], 'data': [{'x': labels[idx + 29], 'y': y} for idx, y in enumerate(values[29:])], 'color': high_color}
        ]

    else:
        chart_type = 'area'
        width_idx = 0
        current_width = int(data['widths'][width_idx])

        for idx, point in enumerate(data['data']):
            if int(point) == 0: continue
            status = 'id' if width_idx == 0 else 'linkedTo'

            d = []
            # Fill with None values to shift the start of the displayed serie
            previous_width = idx
            for i in range(previous_width):
                d.append(None)

            # Fill with the serie values
            for i in range(current_width):
                d.append(point)
            
            width_idx += 1
            if width_idx < len(data['widths']):
                current_width = int(data['widths'][width_idx])

            hex_color = ('#f2fbff', '#4db0e8') if previous_width < 29 else ('#faffff', '#95edeb')
            color = {'linearGradient': {'x1': 0, 'y1': 1, 'x2': 0, 'y2': 0},
                    'stops': [[0, hex_color[0]], [1, hex_color[1]]]
                    } 
            serie = {status: seq + '-series', 'name': data['x_title'], 'data': d, 'marker': {'enabled': False}, 'color': color}
            plot_data['data']['charts']['series']['data'].append(serie)

    plot_data['options'] = {'value': {'scale': 'interop', 'chart': chart_type}}
    return plot_data