#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 10:41:29 2019

@author: jthompsz
"""
import numpy as np
import pandas as pd
import sys
import nilearn.image as nii
from nilearn import input_data, plotting
from nilearn.input_data import NiftiMasker
import matplotlib.pyplot as plt
import scipy.signal as signal
from scipy.interpolate import CubicSpline
from scipy.interpolate import make_interp_spline
import seaborn as sns

func_dir = '/scratch/folder/data/output/fmriprep'
conf_dir = f'/scratch/folder/data/output/derivatives/custom_confounds_nogsr'
subject = sys.argv[1]

# define functional time series
func_file = f'{func_dir}/sub-{subject}/func/sub-{subject}_task-movie_run-1_space-T1w_desc-optcomDenoised_bold.nii.gz'
mask_file = f'{func_dir}/sub-{subject}/func/sub-{subject}_task-movie_run-1_space-T1w_desc-brain_mask.nii.gz'
output_censored = f'{func_dir}/sub-{subject}/func/sub-{subject}_task-movie_run-1_space-T1w_optcomDenoised_bold_censored.nii.gz'
output_interp = f'{func_dir}/sub-{subject}/func/sub-{subject}_task-movie_run-1_space-T1w_optcomDenoised_bold_nogsr_L-S.nii.gz'

# read in confounds file
confounds_fpt = f'{conf_dir}/sub-{subject}_task-movie_run-1_desc-confounds_timeseries.tsv'
confounds = pd.read_table(confounds_fpt)

fd_clean = np.where(confounds['fd'].values!=1)

# censor original timeseries
img = nii.load_img(func_file)
dat = nii.get_data(img).astype('float32')
dout = dat[:,:,:, np.squeeze(np.where(confounds['fd'].values!=1))]
img_out = nii.new_img_like(img, dout)

img_out.to_filename(output_censored)

# load in censored data, detrend, zscore, remove gm signal
masker = NiftiMasker(
    mask_img=mask_file,
    detrend=True,
    standardize="zscore_sample",
    standardize_confounds=False,
    t_r=1.5)

cort_good = masker.fit_transform(output_censored)

# scrub motion outliers, make nan
temp_mask = confounds['fd'].values
sample_mask = np.where(temp_mask!=1, True, False)

t_r = 1.5
frame_times = np.arange(sample_mask.shape[0])*t_r
remained_vol = frame_times[sample_mask]
                    
#%Input t is a column vector listing the time points for which observations
#%are present.  Input h is a matrix with observations in columns and the
#%number of rows equals the number the time points.  For our purposes number
#%of voxels = number of columns.  Ofac = oversampling frequency (generally
#%>=4), hifac = highest frequency allowed.  hifac = 1 means 1*nyquist limit
#%is highest frequency sampled.  
#%Adapted from:  Anish Mitra, October 25 2012
re_vol_shape = remained_vol.shape[0]
h = cort_good
t = remained_vol
t = np.reshape(t, [re_vol_shape,1])
ofac = 5
hifac = 1
N = h.shape[0] #Number of time points
T = np.max(t) - np.min(t) #Total time span

#calculate sampling frequencies
f = np.arange(1/(T*ofac),hifac*N/(2*T), 1/(T*ofac))
f = np.reshape(f, [1,f.shape[0]])
fw = f.shape[1]

#angular frequencies and constant offsets
w = 2*np.pi*f
tau = np.arctan2(np.sum(np.sin(2*w*t)),np.sum(np.cos(2*w*t)))/(2*w)

#spectral power sin and cosine terms
cterm = np.cos(w*t - w*tau)
sterm = np.sin(w*t - w*tau)

num_tseries = h.shape[1] #Number of time series

D = h
#D = np.reshape(D,[N, 1,num_tseries])
dat_dims = tuple([sample_mask.shape[0], cort_good.shape[1]])
Hout = np.empty(shape=dat_dims)
c = np.empty(shape=(w.shape[1],dat_dims[1]))
s = np.empty(shape=(w.shape[1],dat_dims[1]))
T_rep = np.reshape(np.arange(0,dat_dims[0]*1.5, 1.5),[dat_dims[0],1])
w = 2*np.pi*f;
prod = T_rep*w
sin_t = np.sin(prod)
cos_t = np.cos(prod)

for vx in range(0,num_tseries):
    Cmult = np.reshape(D[:,vx], [re_vol_shape,1])*cterm
    numerator = np.sum(Cmult,axis=0) #Modify the numerator to get the cw term
    denominator = np.sum(Cmult**2,axis=0) #use Cterm in place of cterm to make it exactly the denominator in the original expression
    C_final_new = numerator/denominator
    c[:,vx] = C_final_new

    Smult = np.reshape(D[:,vx], [re_vol_shape,1])*sterm
    numerator = np.sum(Smult,axis=0) #Modify the numerator to get the cw term
    denominator = np.sum(Smult**2,axis=0) #use Cterm in place of cterm to make it exactly the denominator in the original expression
    S_final_new = numerator/denominator
    s[:,vx] = S_final_new

    # The inverse function to re-construct the original time series
    sw_p = sin_t*np.reshape(s[:,vx],[1,fw])
    cw_p = cos_t*np.reshape(c[:,vx],[1,fw])
    S = np.sum(sw_p, axis=1)
    C = np.sum(cw_p, axis=1)
    H = C + S

    #Normalize the reconstructed spectrum, needed when ofac > 1
    Std_H = np.std(H)
    Std_h = np.std(h[:,vx], axis=0)
    norm_fac = Std_H/Std_h
    Hout[:,vx] = H/norm_fac

Cout = np.empty(dat_dims)
Cout[sample_mask,:] = cort_good
Cout[~sample_mask, :] = Hout[~sample_mask,:]

sbc_img = masker.inverse_transform(Cout)
sbc_img = nii.smooth_img(sbc_img, fwhm=None)

sbc_img.to_filename(output_interp)