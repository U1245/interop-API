"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      Methods to manage the run files

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
import os
import glob
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

    # Get the run parameter file, no matter the syntax is
    param_file = glob.glob(data_folder + '/*unParameters.xml')[0]

    param_tree = ET.parse(param_file)
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
    """Verify if the completion files are presents in a run folder

    Args:
        seq (str): sequencer name
        last_rundir (str): path to the latest run directory for the current sequencer
        status (str): current status of the sequencer

    Returns:
        tuple(str,datetime): updated status & completion datetime
    """
    # Init vars
    generic_completion_file = last_rundir + '/CopyComplete.txt'
    partial_completion_file = last_rundir + '/RTAComplete.txt'
    # MS_completion_file = last_rundir + '/Basecalling_Netcopy_complete.txt'

    completion_dt = ''

    # Choose the completion file based on the sequencer
    completion_file = partial_completion_file if 'miseq' in seq.lower() else generic_completion_file

    # Check if the completion file exists
    if os.path.exists(completion_file):
        timestamp = os.path.getmtime(completion_file)
        completion_dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d   %H:%M')

    # Determine the status based on the existing --completion-- files
    if completion_dt: status = 'Completed on'
    elif os.path.exists(partial_completion_file) and 'miseq' not in seq.lower(): 
        status = 'Finalizing'
    
    return status, completion_dt