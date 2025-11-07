# README

## About
This repo contains workflows to setup Chao's Hanford reach scale model with modified perm for the alluvium layer. It was then extended to include thermal processes in the model.


## notes
- data_from_USGS_1.csv is an updated version and is used in alluvium K
- perm_data_only_alluvium_smoothed_cutoff.h5 is the perm file that has smoothed the K and cutoff the extreme small and large values. 


## to run PFLOTRAN
Load/set the following modules/environment variables for the respective PrgEnv.

- **Intel** (not working!)
```
source /global/common/software/pflotran/.pflotran_perl_intel
```

- **GNU** (working)
```
source /global/common/software/pflotran/.bashrc_perl_gnu
```
