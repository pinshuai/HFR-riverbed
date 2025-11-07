#!/bin/bash -l

#SBATCH -A m3940
#SBATCH -N 16
#SBATCH -t 48:00:00
##SBATCH -t 00:30:00
#SBATCH -L SCRATCH  
#SBATCH -J TH
#SBATCH --qos regular
##SBATCH --qos debug
#SBATCH --mail-type ALL
#SBATCH --mail-user pin.shuai@usu.edu
#SBATCH -C haswell

# cd $SLURM_SUBMIT_DIR
cd /global/cscratch1/sd/pshuai/HFR-thorne/model_run/TH-new_obs-mesh_100m-rst1

srun -n 512 -e job%J.err -o job%J.out pflotran-030821 -pflotranin HFR-model-100m-TH-updated_mesh-rst1.in


