#!/bin/bash
#
#SBATCH --job-name=fmriprep
#SBATCH -J fmriprep
#SBATCH --time=2-00:00:00
#SBATCH --array=1
#SBATCH -n 1
#SBATCH --cpus-per-task=12
#SBATCH --mem-per-cpu=4G
#SBATCH --constraint=$$
#SBATCH -p normal  # Queue names you can submit to

STUDY=/scratch/folder
BIDS_DIR="${STUDY}/data"
DERIVS_DIR="output"
LOCAL_FREESURFER_DIR="${BIDS_DIR}/${DERIVS_DIR}/freesurfer"

# Prepare some writeable bind-mount points.
TEMPLATEFLOW_HOST_HOME=/scratch/folder/.cache/templateflow
FMRIPREP_HOST_CACHE=/scratch/folder/.cache/fmriprep
if [[ ! -d ${TEMPLATEFLOW_HOST_HOME} ]]
    then
    mkdir -p ${TEMPLATEFLOW_HOST_HOME}
    mkdir -p ${FMRIPREP_HOST_CACHE}
fi


# Prepare derivatives folder
mkdir -p ${BIDS_DIR}/${DERIVS_DIR}

# Make sure FS_LICENSE is defined in the container.
export SINGULARITYENV_FS_LICENSE=/home/folder/license.txt

# Designate a templateflow bind-mount point
export SINGULARITYENV_TEMPLATEFLOW_HOME="/templateflow"
module load singularity

SINGULARITY_CMD="singularity run --cleanenv -B $BIDS_DIR:/data -B ${TEMPLATEFLOW_HOST_HOME}:${SINGULARITYENV_TEMPLATEFLOW_HOME} -B /scratch/csng/CSNG/work:/work -B ${LOCAL_FREESURFER_DIR}:/fsdir /containers/dgx/UserContainers/jthompsz/fmriprep-23.1.3.simg"

subject=$( sed "${SLURM_ARRAY_TASK_ID}q;d" /home/folder/participants.csv )

# Remove IsRunning files from FreeSurfer
find ${LOCAL_FREESURFER_DIR}/sub-$subject/ -name "*IsRunning*" -type f -delete

# Compose the command line
cmd="${SINGULARITY_CMD} /data/nifti /data/${DERIVS_DIR} participant --participant-label ${subject} -w /work/ -vv --omp-nthreads 8 --nthreads 12 --mem_mb 30000 --output-spaces MNI152NLin2009cAsym:res-2 T1w --me-output-echos --skip_bids_validation --output-layout legacy"

# Setup done, run the command

echo Commandline: ${cmd}
eval $cmd
exitcode=$?

sleep $[ 60 * ${SLURM_ARRAY_TASK_ID} ]


