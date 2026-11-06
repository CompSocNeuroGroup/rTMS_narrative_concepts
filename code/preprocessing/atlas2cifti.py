# -*- coding: utf-8 -*-
"""
"""

import nibabel as nb
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from subcortex_visualization.plotting import plot_subcortical_data

atlas_dir = f'your_dir'
func_dir = f'your_dir'

# load in stats file
fileio = f'data_file'
stats_file = pd.read_csv(f'{func_dir}/{fileio}.csv',index_col=False)

df = stats_file.loc[0:399]
df.rename(columns = {'label': 'group'}, inplace=True)

# load dlabel and dscalar
dlabel_ref = nb.load(f'{atlas_dir}/Schaefer2018_400Parcels_17Networks_order.dlabel.nii')
scalar_ref  = nb.load(f'{atlas_dir}/Schaefer2018_400Parcels_17Networks_order.dscalar.nii')

# Get the label table and parcel order from the dlabel
label_img   = dlabel_ref.get_fdata(dtype=np.float32)   # shape (1, n_vertices)
brain_models = dlabel_ref.header.get_index_map(1)       # surface/volume structure info

# Extract ordered parcel names from the dlabel label table
label_table = dlabel_ref.header.get_axis(0).label[0]   # dict: {int_key: (name, rgba)}
# Build ordered list of parcel names (key 0 is the background/medial wall)
parcel_keys   = sorted([k for k in label_table.keys() if k != 0])  # 1..400
parcel_names  = [label_table[k][0] for k in parcel_keys]           # 400 names in order

# map stats data to labels
df_indexed = df.set_index('group')

tstat_vector = np.zeros(400, dtype=np.float32)
pval_vector  = np.ones(400,  dtype=np.float32)

for i, name in enumerate(parcel_names):
    if name in df_indexed.index:
        tstat_vector[i] = df_indexed.loc[name, 't_statistic']
        pval_vector[i]  = df_indexed.loc[name, 'corr_p']
    else:
        print(f"Warning: parcel '{name}' not found in CSV")

# Map parcel values back to vertex/voxel space
scalar_data = np.zeros_like(label_img)  # shape (1, n_vertices)

for i, key in enumerate(parcel_keys):
    mask = label_img[0] == key
    scalar_data[0, mask] = tstat_vector[i]

# Create new dscalar using the scalar reference's brain models
scalar_axis = nb.cifti2.ScalarAxis(['t-statistic'])
brain_model_axis = scalar_ref.header.get_axis(1)

new_scalar_img = nb.Cifti2Image(
    scalar_data,
    header=nb.cifti2.Cifti2Header.from_axes((scalar_axis, brain_model_axis))
)
nb.save(new_scalar_img, f'{func_dir}/{fileio}.dscalar.nii')
print("Saved tstat_map.dscalar.nii")


# dlabel from p<0.05
sig_label_data = np.zeros_like(label_img)  # 0 = not significant

# Build a new label table for significant parcels only
new_label_table = nb.cifti2.Cifti2LabelTable()

# Add background (medial wall / non-significant) as label 0
new_label_table[0] = nb.cifti2.Cifti2Label(0, '???', 1.0, 1.0, 1.0, 0.0)  # transparent


for i, key in enumerate(parcel_keys):
    if pval_vector[i] < 0.05:
        mask = label_img[0] == key
        sig_label_data[0, mask] = key  # keep original parcel index

        # Copy label from original table (preserves name and colour)
        orig_label = label_table[key]
        new_label_table[key] = nb.cifti2.Cifti2Label(
            key,
            orig_label[0],           # parcel name
            *orig_label[1]           # RGBA tuple
        )

# Wrap in a LabelAxis
label_axis = nb.cifti2.LabelAxis(
    name=['significant regions (p<0.05)'],
    label=[dict(new_label_table)]   # convert Cifti2LabelTable -> plain dict
)
brain_model_axis = dlabel_ref.header.get_axis(1)


new_dlabel_img = nb.Cifti2Image(sig_label_data, header=dlabel_ref.header)
nb.save(new_dlabel_img, f'{func_dir}/{fileio}.dlabel.nii')
print("Saved significant_regions.dlabel.nii")



##############################subcortical##################################################
#cmap = plt.cm.PuOr
#cmap = plt.cm.PRGn
cmap = plt.cm.PiYG
#cmap = plt.cm.coolwarm

stats_subcortical = stats_file.iloc[400:416,:]

example_continuous_data_R = pd.DataFrame({"region": ["amygdala", "caudate", "pallidum","hippocampus", "accumbens",  "putamen", "thalamus_anterior", "thalamus_posterior"],
                                            "value": stats_subcortical.loc[np.arange(401,417,2),'t_statistic'].values*1}).assign(Hemisphere = "R")

example_continuous_data_L = pd.DataFrame({"region": ["amygdala", "caudate", "pallidum","hippocampus", "accumbens",  "putamen", "thalamus_anterior", "thalamus_posterior"],
                                            "value": stats_subcortical.loc[np.arange(400,416,2),'t_statistic'].values*1}).assign(Hemisphere = "L")

example_continuous_data = pd.concat([example_continuous_data_L, example_continuous_data_R], axis=0)

plot_subcortical_data(subcortex_data=example_continuous_data, atlas = 'Melbourne_S1',
                      hemisphere='both', fill_title = "t_statistic", 
                      cmap=cmap, vmin=-5.0, vmax = 5.0, line_thickness=2)

