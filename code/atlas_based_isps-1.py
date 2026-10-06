#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""

@author: jthompsz
"""

import numpy as np
import pandas as pd
import nilearn.image as nii
from nilearn import signal
import nibabel as nb
from nilearn.image import index_img, get_data, new_img_like
from nilearn.image import math_img
import nibabel as nib
from nibabel import freesurfer as fs

sub = 'subject'

out_dir = f'outdir'
fmriprep_dir = f'dir/fmriprep/sub-{sub}/func'
atlas_dir = f'atlas_dir'

scenes = pd.read_csv(f'scenes.csv')
atlas = f'{atlas_dir}/Tian_Subcortex_S1_3T_2009cAsym.nii.gz'


mni_data = f'{fmriprep_dir}/mni_data.nii.gz'
mask_file = f'{fmriprep_dir}/boldref.nii.gz'
mask_img = nib.load(mask_file)

ts = []
for hemi in ['lh', 'rh']:
    hemi = 'rh'
    annot = fs.io.read_annot(f'{atlas_dir}/{hemi}.Schaefer2018_200Parcels_17Networks_order.annot')
    regions = np.unique(annot[0])
    mgh = nb.load(f'{fmriprep_dir}/{hemi}.surface_data.mgh')
    data = np.asanyarray(mgh.dataobj)
    data = np.squeeze(data)

    dat_clean = signal.clean(data.T, t_r=1.5, detrend=True,standardize='zscore')

    new_mgh = np.reshape(dat_clean.T,(40962,1,1,800))
   
    final_mgh = nib.Nifti1Image(new_mgh, mgh.affine)
    nb.save(final_mgh, f'{func_dir}/{hemi}.cleaned.mgh')

    for start, stop in zip (scenes.start, scenes.stop):
        x = np.nanmean(new_mgh[:,:, :, range(start,stop)], axis=3)
        x = np.reshape(x, (40962,1,1))
        mgh_x = nib.Nifti1Image(x, mgh.affine)
        nb.save(mgh_x, f'{out_dir}/sub-{sub}.{hemi}.cleanded.{start}-{stop}.mgh')


# extract data from atlas
fmri_img = nii.clean_img(
    mni_data,
    detrend=True,
    standardize="zscore",
    n_jobs= 4,
    t_r=1.5)

fmri_img = nii.smooth_img(fmri_img, fwhm=2.0)
cort_time_series = get_data(fmri_img)


for start, stop in zip (scenes.start, scenes.stop):
    x = np.nanmean(cort_time_series[:,:, :, range(start,stop)], axis=3)
    new_img = new_img_like(mask_img, x)
    new_img.to_filename(f'{out_dir}/cleanded.{start}-{stop}.nii.gz')
