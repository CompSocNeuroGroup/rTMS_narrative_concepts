
task="movie"
data_dir="/scratch/folder/data/output/fmriprep/sub-${subject}/func"
for run in 1
    do

    func_file=/scratch/folder/data/output/tedana/sub-${subject}/sub-${subject}_task-${task}_run-${run}_desc-optcomDenoised_bold.nii.gz
    func_out=/scratch/folder/data/output/fmriprep/sub-${subject}/func/sub-${subject}_task-${task}_run-${run}_space-T1w_desc-optcomDenoised_bold.nii.gz

    itk_xforms=/scratch/folder/data/output/fmriprep/sub-${subject}/func/sub-${subject}_task-${task}_run-${run}_from-scanner_to-T1w_mode-image_xfm.txt
    sT1w=/scratch/folder/data/output/fmriprep/sub-${subject}/func/sub-${subject}_task-${task}_run-${run}_space-T1w_boldref.nii.gz

    antsApplyTransforms --dimensionality 3 \
    --input-image-type 3 \
    --input ${func_file} \
    --reference-image ${sT1w} \
    --output ${func_out} \
    --interpolation LanczosWindowedSinc \
    --transform ${itk_xforms} \
    --default-value 0 \
    --float 1 \
    --verbose 1

    done
