"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      Methods to manage the run directories

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""
import re
import os


def get_latest_runfolder(run_dirs):
    """Get the most recent run folder for a given sequencer

    Args:
        run_dirs (list): list of all the runfolders for a sequencer

    Returns:
        str: the most recent run folder
    """
    return max(run_dirs, key=os.path.getmtime)


def get_sequencer_rootdir(root, seq_list, seq_nb):
    """Get the main runfolder storage path of a sequencer.
    Some sequencer root folder may not contain the runs.
    A regex allows to find a match on the Illumina runfolder name format.

    Args:
        root (str): path to the main storage. Should contain 1 dir per sequencer.

    Returns:
        list: a rootdir path for each sequencer
    """
    # Find the root dir for each sequencer
    # seq_list = ['MiSeq', 'NextSeq', 'NovaSeq']
    # seq_nb = 
    seq_rootdirs = []

    # regex matching the run folder name format
    regex = re.compile('.*\d{6}_[\w\d]+_\d{4}_[\w\d]+')

    for seq_dir in [f.path for f in os.scandir(root) if f.is_dir()]:
        if any([x in seq_dir for x in seq_list]):
            for root, dirs, files in os.walk(seq_dir):
                current_root = '/'.join(root.split('/')[:-1])

                if len(seq_rootdirs) >= seq_nb: break
                if current_root in seq_rootdirs: break
                if regex.match(root):
                    seq_rootdirs.append(current_root)
                    break

    return seq_rootdirs


def get_sequencer_latest_run(rootdirs):
    """Get the latest runfolderfor each sequencer

    Args:
        rootdirs (str): path of the root directory for a sequencer. e.g /PATH/TO/MAIN/STORAGE/MiSeq

    Returns:
        dict: the last run of each sequencer, even the completed ones
    """
    # Get the latest runfolder for each sequencer
    latest_runs = {}
    for seq_dir in rootdirs:
        run_dirs = [run_folder.path for run_folder in os.scandir(seq_dir) if os.path.isdir(run_folder)]
        # Chose to not display the sequencers with no runfolder
        if run_dirs:
            seq = seq_dir.split('/')[3]

            # Novaseq has 2 sequencers onboard
            if 'novaseq' in seq.lower():
                A_side_runs = [run for run in run_dirs if run.split('_')[-1].startswith('A')]
                B_side_runs = [run for run in run_dirs if run.split('_')[-1].startswith('B')]

                if A_side_runs:
                    latest_runs[seq + '_A'] = get_latest_runfolder(A_side_runs)
                if B_side_runs:
                    latest_runs[seq + '_B'] = get_latest_runfolder(B_side_runs)

            else:
                latest_runs[seq] = get_latest_runfolder(run_dirs)

    return latest_runs