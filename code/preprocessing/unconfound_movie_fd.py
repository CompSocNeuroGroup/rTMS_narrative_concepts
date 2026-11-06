#!/usr/bin/env python3
import os
import sys
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

sid = sys.argv[1]
task_list = ['movie_run-1']


dset_dir = f'/scratch/folder/data/output/'
deriv_dir = os.path.join(dset_dir, "derivatives")
custom_confounds_folder = os.path.join(deriv_dir, "custom_confounds_nogsr")

def butter_filter(data, low, high, order=5):
    b, a = butter(order, [low, high], btype='bandstop')
    y = filtfilt(b, a, data, axis=0)
    return y


for rid in range(0,1):
    rid = 0
    # read in confounds file
    func_dir = os.path.join(dset_dir, f"fmriprep/sub-{sid}/func")
    prefix = f"sub-{sid}_task-movie_run-1"
    confounds_file = os.path.join(func_dir,  f"{prefix}_desc-confounds_timeseries.tsv")
    custom_confounds_file = os.path.join(custom_confounds_folder, os.path.basename(confounds_file))
    confounds = pd.read_csv(confounds_file, sep='\t')

    new_mixing_matrix = pd.DataFrame()

    # bp filtered fd
    out_vars = pd.DataFrame()
    nyq = (1/1.5)/2
    lowcut = 0.16/nyq
    highcut = 0.33/nyq

    rp = confounds[['rot_x', 'rot_y', 'rot_z', 'trans_x', 'trans_y', 'trans_z']]
    rp = rp.fillna(0)
    rpy = butter_filter(rp, lowcut, highcut, order=5)
    fd_trans = np.diff(rpy[:,3:7], axis=0)
    fd_rot = np.diff(rpy[:,0:3], axis=0) * 2 * np.pi * 50 / 360
    fd_temp = pd.concat([pd.DataFrame(fd_rot), pd.DataFrame(fd_trans)], axis = 1)
  
    fd = fd_temp.sum(axis = 1).abs()
    data = pd.DataFrame({0}, index=[0])
    fd = pd.concat([pd.DataFrame(data), fd]).reset_index(drop=True)

    spikes = np.zeros(fd.shape)
    spikes[np.where(fd > 0.3)] = 1
    out_vars = pd.concat([out_vars, pd.DataFrame(spikes)], axis=1)
    out_vars.columns = ['fd']

    new_mixing_matrix = pd.concat([new_mixing_matrix,out_vars], axis=1)
    
    new_mixing_matrix.to_csv(custom_confounds_file, sep="\t", index=False)