#!/bin/bash -l

#SBATCH -A m1800
#SBATCH -N 16
#SBATCH -t 00:30:00
#SBATCH -L SCRATCH  
#SBATCH -J Thorne-TH
#SBATCH --qos debug
#SBATCH --mail-type ALL
#SBATCH --mail-user pin.shuai@pnnl.gov
#SBATCH -C haswell

# cd $SLURM_SUBMIT_DIR
cd /global/cscratch1/sd/pshuai/HFR-thorne/model_run/mesh-100m-TH

srun -n 512 pflotran-030821 -pflotranin HFR-model-100m-TH.in


