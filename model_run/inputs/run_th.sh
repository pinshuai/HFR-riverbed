#!/bin/bash
#SBATCH -A m1800
#SBATCH -C cpu
#SBATCH --qos=regular   # regular (12 hrs), interactive (4 hrs), debug (0.5 hrs)
# #SBATCH --qos=debug   # regular (12 hrs), interactive (4 hrs), debug (0.5 hrs)
#SBATCH --time=24:00:00 # hh:mm:ss
# #SBATCH --time=00:30:00 # hh:mm:ss
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=128
#SBATCH -J TH
#SBATCH --mail-type ALL
#SBATCH --mail-user pin.shuai@usu.edu

# two CPUs (or sockets) per node
# 64 cores per processor
# you can user fewer than the # of cores per CPU

# the "-n" below must equal "--nodes" * "--ntasks-per-node" above
# the "-c" below must equal "--ntasks-per-node" above

# module load PrgEnv-intel
# source /global/common/software/pflotran/.pflotran_perl_intel
source /global/common/software/pflotran/.bashrc_perl_gnu
# change to working directory (e.g., scratch space)
cd /pscratch/sd/p/pshuai/HFR-riverbed/TH_homo_alluvium_2017-2019
srun -n 1024 --cpu-bind=cores  -e job%J.err -o job%J.out -c 2 $PFLOTRAN_EXE -pflotranin TH_homo_alluvium_2017-2019.in

