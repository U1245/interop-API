import re
import os


def get_latest_runfolder(run_dirs):
    return max(run_dirs, key=os.path.getmtime)


def get_sequencer_rootdir(root):
    # Find the root dir for each sequencer
    # rootdir = "/storage/IN"
    seq_list = ['MiSeq', 'NextSeq', 'NovaSeq']
    seq_nb = 4
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

                latest_runs[seq + '_A'] = get_latest_runfolder(A_side_runs)
                latest_runs[seq + '_B'] = get_latest_runfolder(B_side_runs)

            else:
                latest_runs[seq] = get_latest_runfolder(run_dirs)

    return latest_runs