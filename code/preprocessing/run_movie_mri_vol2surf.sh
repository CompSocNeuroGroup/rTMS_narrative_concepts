#!/bin/bash
set -e



########################################## READ_ARGS ##################################
Subject=${subject}
Run="run-1"
ResultsFolder=""
VolStatsDir="func"

STUDY=/scratch/folder
BIDS_DIR="${STUDY}/data"
DERIVS_DIR="output"
LOCAL_FREESURFER_DIR="${BIDS_DIR}/${DERIVS_DIR}/freesurfer"
LOCAL_SUBJECTS_DIR="${LOCAL_FREESURFER_DIR}"

FS_LICENSE=/home/folder/analysis/license.txt


export SUBJECTS_DIR=$LOCAL_SUBJECTS_DIR
export FS_LICENSE=$FS_LICENSE




set -- ${ResultsFolder}/sub-${sub}/${VolStatsDir}
dirPath=$1

for Hemi in lh rh ; do
    mri_vol2surf --src ${dirPath}/sub-${sub}_task-movie_run-1_space-T1w_optcomDenoised_bold_nogsr_L-S.nii.gz --out ${dirPath}/${Hemi}.task-movie_run-1_space-T1w_optcomDenoised_bold_nogsr_L-S.mgh \
    --trgsubject fsaverage6 \
    --regheader sub-${sub} \
    --projfrac-avg 0 1 0.2 \
    --hemi ${Hemi}

    mris_fwhm --i ${dirPath}/${Hemi}.task-movie_run-1_space-T1w_optcomDenoised_bold_nogsr_L-S.mgh \
    --o ${dirPath}/${Hemi}.task-movie_run-1_space-T1w_optcomDenoised_bold_nogsr_L-S.s2.mgh \
    --so --fwhm 2 --subject fsaverage6 --hemi ${Hemi} --surf midthickness
done



