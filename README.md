# README

## About
This repo contains workflows to setup the Hanford unstructured, reach scale, PFLOTRAN model with modified perm for the alluvium layer. This model simulates subsurface flow and thermal processes.

![Unstructured mesh of the Hanford riverbed model](./figures/mesh.jpg)

**Citation**: Shuai P, Zeng C, Hammond G, Song X, Chen K, Terry NC, Briggs MA, Gooseff MN, Perkins WA, Richmond MC, and Chen X. Incorporating large-scale high-resolution riverbed permeability survey to characterize river corridor thermal regimes. [Preprint]

## folder structure
```
HFR-riverbed/
├── data/                  # model input datasets referenced by the input decks
│   ├── boundary_conditions/
│   │   ├── HFR_H_Initial.h5               # initial head condition
│   │   ├── stage_2017-2019_6h-smooth/     # river stage BCs (DatumH_River_*.txt, Gradients_River_*.txt)
│   │   └── temp_2017-2019_6h-smooth/      # river temperature BCs (Temp_River_*.txt)
│   ├── mesh/
│   │   └── hanford_mesh_100m-updated-matID-river.h5   # unstructured mesh with material IDs
│   └── perm/
│       ├── perm_data_*.h5                 # permeability fields (alluvium, riverbed, basalt variants)
│       └── riverbed_permeability_input.vtu
├── figures/               # figures used in this README and manuscript
│   └── mesh.jpg
├── model_run/
│   └── inputs/            # PFLOTRAN input decks
│       ├── TH_homo_alluvium_2017-2019.in                   # TH run, homogeneous alluvium perm
│       ├── TH_perm_only_alluvium_2017-2019_daily-output.in # TH run, heterogeneous alluvium perm
│       └── archive/                       # earlier decks, obs/region blocks, USGS data, and run scripts
├── notebooks/             # pre- and post-processing workflows (see notebooks/README.txt)
│   ├── mesh_hanford.ipynb, generate_*.ipynb, PFLOTRAN_input_deck.ipynb   # build mesh, materials, BCs, input deck
│   ├── plot_*.ipynb                   # compare simulations with observations, plot fluxes/temperature/tracer
│   ├── *.py                           # helper modules (myfunc.py, fav_colors.py, ncdump.py, ...)
│   └── src/                           # Python/R script versions of the notebooks
└── spinup/
    └── HFR-model-100m-flow-updated_mesh-restart.h5   # flow spin-up restart file
```

## notes
- `model_run/inputs/archive/data_from_USGS_1.csv` is an updated version and is used in alluvium K
- `data/perm/perm_data_only_alluvium_smoothed_cutoff.h5` is the perm file that has smoothed the K and cutoff the extreme small and large values. 


## to run PFLOTRAN on NERSC
Load/set the following modules/environment variables for the respective PrgEnv.

- **Intel** (not working!)
```
source /global/common/software/pflotran/.pflotran_perl_intel
```

- **GNU** (working)
```
source /global/common/software/pflotran/.bashrc_perl_gnu
```
