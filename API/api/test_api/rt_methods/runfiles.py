import os
import xml.etree.ElementTree as ET
from datetime import datetime


def run_parameters(data_folder, result, seq):
    """
    Gets the run parameters, i.e reagents metadata.
    Based on the runParameter.xml file.

    Args:
        data_folder (str): path of the run folder
        result (dict): global SAV result dict
        seq (str): sequencer name
    """
    param_file = ('r' if 'miseq' in seq.lower() else 'R') + 'unParameters.xml'

    param_tree = ET.parse(data_folder + '/' + param_file)
    root = param_tree.getroot()

    try:
        exp_name = root.find('ExperimentName')
        if exp_name.tag: result['exp_name'] = exp_name.text
    except AttributeError:
        result['exp_name'] = ''

    # TODO Find a way to make the returned values more generic
    # Despite of the variability of the input
    result['reagents'] = {}

    if 'novaseq' not in seq.lower():
        rgt_list = ['flowcell', 'pr2_bottle', 'reagent_kit']
        
        for reagent in rgt_list:
            reagents_root = None
            rgt = reagent.replace('_', '')

            for child in root:
                if rgt in child.tag.lower() and len(child):
                    reagents_root = child
                    break

            result['reagents'][reagent] = \
                {
                    child.tag.lower(): child.text 
                    for child in reagents_root
                    if reagents_root is not None
                }

    else:
        nova_rgt_list = ['flowcell', 'library_tube', 'sbs', 'cluster', 'buffer']
        reagents_root = root.find('RfidsInfo')
        
        for reagent in nova_rgt_list:
            rgt = reagent.replace('_', '')
            result['reagents'][reagent] = \
                {
                    child.tag[len(rgt):].lower(): child.text 
                    for child in reagents_root 
                    if rgt in child.tag.lower()
                }
            # Workaround to rename the tag of the serial number
            result['reagents'][reagent]['serialnumber'] = result['reagents'][reagent].pop('serialbarcode')


def check_completion_files(seq, last_rundir, status):
    """
    """
    NS_completion_file = last_rundir + '/RunCompletionStatus.xml'
    MS_completion_file = last_rundir + '/CompletedJobInfo.xml'
    generic_completion_file = last_rundir + '/RTAComplete.txt'
    completion_dt = ''

    if 'nextseq' in seq.lower():
        if os.path.exists(NS_completion_file):
            # Run status
            tree = ET.parse(NS_completion_file)
            root = tree.getroot()
            status_node = root.find('CompletionStatus')

            # Completion datetime : last modification of the 'NS_completion_file' file
            timestamp = os.path.getmtime(NS_completion_file)

            if 'completedasplanned' in status_node.text.lower(): status = 'Completed on' 
            completion_dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d   %H:%M')

    if 'miseq' in seq.lower():
        if os.path.exists(MS_completion_file):
            tree = ET.parse(MS_completion_file)
            root = tree.getroot()
            status_node = root.find('CompletionTime')
            dt = status_node.text.split('T')

            completion_dt = dt[0] + '   ' + ':'.join( dt[1].split('.')[0].split(':', 2)[:2] )
        
        elif os.path.exists(generic_completion_file):
            timestamp = os.path.getmtime(generic_completion_file)
            completion_dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d   %H:%M')

    if 'novaseq' in seq.lower():
        if os.path.exists(generic_completion_file):
            timestamp = os.path.getmtime(generic_completion_file)
            completion_dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d   %H:%M')

    if completion_dt: status = 'Completed on'
    
    return status, completion_dt