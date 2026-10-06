#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: jthompsz
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, false_discovery_control

from nibabel import freesurfer as fs


func_dir = f'your_dir'
atlas_dir = f'your_dir'
cond_dir = f'your_dir'

times = pd.DataFrame()

conds = pd.read_csv(f'{cond_dir}/yourfile.tsv')

dat = f'datafile.csv'

annot = fs.io.read_annot(f'{atlas_dir}/lh.Schaefer2018_400Parcels_17Networks_order.annot')
regions = np.unique(annot[0])
lh_cort_labels = annot[2][:]
annot = fs.io.read_annot(f'{atlas_dir}/rh.Schaefer2018_400Parcels_17Networks_order.annot')
rh_cort_labels = annot[2][:]

lh_labels = [np.bytes_(lh_cort_labels[i]).decode('utf-8') for i in range(1,len(lh_cort_labels))]
rh_labels = [np.bytes_(rh_cort_labels[i]).decode('utf-8') for i in range(1,len(rh_cort_labels))]
cort_labels = lh_labels + rh_labels
    
atlas_dseg = pd.read_csv(f'{atlas_dir}/Tian-S2-Parcels_dseg.csv')
labels = atlas_dseg['label']
label_idx = atlas_dseg['index']

all_labels = cort_labels + labels.to_list()

subject = conds['id']

for s in subject:
    df = pd.DataFrame()
    # load dlabel and dscalar
    df = pd.read_csv(f'{func_dir}/sub-{s}_{dat}', header=None)
    df.columns = all_labels
    df['subject'] = s
    df['stim'] = conds[conds['id']==s]['stim'].repeat(len(df)).values
    times = pd.concat([times, df], axis = 0)

times.to_csv(f'{func_dir}/group_{dat}',index=False)




for S in subject:
    notS = [x for i,x in enumerate(subject) if x!=S]
    print(notS)
    V = pd.DataFrame()
    V = pd.concat([V, pd.Series(all_labels)], axis=1)
    V = V.rename(columns={0: 'parcels'})
    
    for nS in notS:
        #print(nS)
        a = times[times['subject']==S].drop(['subject', 'stim'], axis=1).T.values
        b = times[times['subject']==nS].drop(['subject', 'stim'], axis=1).values
        c =np.arctanh(np.dot(a, b)/b.shape[0])
        v = pd.DataFrame(np.diag(c))
        v = v.rename(columns={0: nS})
        V = pd.concat([V, v], axis=1)

    V.to_csv(f'{func_dir}/datfile.csv', index=False)

v = pd.DataFrame()
for S in subject:
    V = pd.read_csv(f'{func_dir}/datfile.csv', index_col=False)
    parcels = V['parcels'].T
    for p in parcels:
        x = V.loc[V['parcels'] == p]
        tmp = pd.DataFrame(x.iloc[:,2:].values.T)
        tmp = tmp.rename(columns={0: 'cor'})
        tmp['sub1'] = S
        tmp['sub2'] = x.columns[2:].values.T
        tmp['parcels'] = p
        v = pd.concat([v, tmp], axis=0)

v.to_csv(f'{func_dir}/datfile.csv',index=False)

v = pd.read_csv(f'{func_dir}/datfile.csv', index_col=False)

sham = conds[conds['stim']==0]['id'].reset_index(drop=True)
ctbs = conds[conds['stim']==1]['id'].reset_index(drop=True)

sham_v = v[v['sub1'].isin(sham) & v['sub2'].isin(sham)]
ctbs_v = v[v['sub1'].isin(ctbs) & v['sub2'].isin(ctbs)]

x = []
for s in sham:
    tmp = sham_v[sham_v['sub1']==s]
    for l in all_labels:
        x.append([tmp[tmp['parcels']==l]['cor'].mean(axis=0),l,s])
shamX = pd.DataFrame(x)
shamX = shamX.rename(columns={0: 'cor', 1: 'parcels', 2:'sub'})
shamX['stim'] = 0

x = []
for s in ctbs:
    tmp = ctbs_v[ctbs_v['sub1']==s]
    for l in all_labels:
        x.append([tmp[tmp['parcels']==l]['cor'].mean(axis=0),l,s])
ctbsX = pd.DataFrame(x)
ctbsX = ctbsX.rename(columns={0: 'cor', 1: 'parcels', 2:'sub'})
ctbsX['stim'] = 1

df = pd.concat([shamX, ctbsX], axis=0).reset_index(drop=True)

results = []
grouped_data = df.groupby('parcels')
for name, group in grouped_data:
    group0 = group[group['stim']==0]
    group1 = group[group['stim']==1]
    t_statistic, p_value = ttest_ind(group0['cor'], group1['cor'], permutations=5000)
    results.append([name, t_statistic, p_value])


results_df = pd.DataFrame(results, columns=['group', 't_statistic', 'p_value'])

fdr_p = pd.DataFrame(false_discovery_control(results_df[~results_df['p_value'].isna()]['p_value']))
fdr_p.columns = {'corr_p'}

nans = np.where(results_df['p_value'].isna())[0]
df2 = pd.DataFrame(np.insert(fdr_p.values, nans, values=1, axis=0))
df2.columns = {'corr_p'}
results_df = pd.concat([results_df, df2], axis=1)

df1 = results_df.copy()
df1 = df1.set_index('group')
df1 = df1.reindex(index=atlas['label'])

results_df.to_csv(f'{func_dir}/ISC_stats.csv',index=False)
