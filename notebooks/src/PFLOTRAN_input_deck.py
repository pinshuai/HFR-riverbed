#!/usr/bin/env python
# coding: utf-8

# # Generate PFLOTRAN input deck

# Note: the `sink` and `cat` function is not directing output to file. The alternative is to redefine `cat` function ([post](https://stackoverflow.com/questions/51292852/how-to-use-sink-to-save-r-output-in-jupyter-notebook)).

# In[2]:


ipak <- function(pkg){
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg)) 
        install.packages(new.pkg, dependencies = TRUE)
    sapply(pkg, require, character.only = TRUE)
}

packages <- c('geoR', "raster", "maptools")
ipak(packages)


# ## I/O files

# In[2]:


imodel=c("HFR-thorne/spinup/")
# imodel= c("AT-sgrid/s2x05m/")

model_dir = paste0("/global/cscratch1/sd/pshuai/", imodel) 
out_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/"
# result_dir = "/global/project/projectdirs/m1800/pin/AT-model/results/AT-sgrid/"
## inputs
fname_WellScreen = "/global/project/projectdirs/m1800/pin/Reach_scale_model/data/well_data/HEIS_300A_well_screen.csv"
# fname_WellScreen = "/global/project/projectdirs/m1800/pin/Reach_scale_model/data/well_data/HEIS_300A_well_screen.csv"

fname_DEM = "/global/project/projectdirs/m1800/pin/HFR-thorne/data/thorne_dem_10m_asc/throne_dem_10m.asc"
fname_boundary = "/global/project/projectdirs/m1800/pin/HFR-thorne/data/boundary_polygon_v3/geometry.csv"

fname_mass1_list = "/global/cscratch1/sd/pshuai/HFR-thorne/inputs/mass1_list.txt"
# fname_material.h5 = c("../meshes/AT-mesh-alluvium-rivershape.h5")
fname_material.h5 = c("../meshes/Thorne-mesh-matID-river.h5")
fname_H.initial.h5 = c("../inputs/HFR_H_Initial.h5")

fname_ens_perm.h5 = c("../inputs/HFR_unstructured_coarse_perm.h5")
# fname_H.BC.h5 = c("../inputs/AT_H_BC.h5")wwads

# fname_Temp.initial.h5 = c("../inputs/AT_Temp_Initial.h5")
# fname_Temp.BC.h5 = c("../inputs/AT_Temp_BC.h5")

# fname_bc_dir = "../model_bcs/stage_6h_smooth_2009_2018/"
fname.DatumH = c("../inputs/river_bc/stage_2007-2019/DatumH_River_")
fname.Gradient = c("../inputs/river_bc/stage_2007-2019/Gradients_River_")

# fname.River.Temp = c("../inputs/Temp_River_321.txt")

# fname_mass_section = paste(model_dir, "results/TH_", imodel, "/mass_section.txt", sep = "")
# fname_model_inputs.r = paste(out_dir, "results/AT-sgrid/model_inputs.r", sep = "")
# fname_geoFramework.r = paste(model_dir, "results/", imodel, "/geoframework.r", sep = "")
## outputs
# fname_pflotran.in = paste(model_dir, "inputs/", imodel, "/AT-model.in", sep = "")
fname_pflotran.in = paste0(model_dir, 'HFR-model.in')
fname_selected_wells = paste0(model_dir, 'selected_well.txt')
# conditional statements
has.obs.wells = TRUE
ugrid = TRUE
has.solute = TRUE
is.flowBC = TRUE
ensemble.perm = TRUE
#====#
has.basalt = FALSE
has.injection.well = FALSE
has.age = FALSE
vary.mesh = FALSE


# choose the model mode (`TH`, `RICHARDS` ...)

# In[3]:


# mode = "TH"
mode = "RICHARDS"


# ## model parameters

# In[4]:


# model_origin = c(594140, 116060) # 400x400 m domain


# In[5]:


min_z = 2 # set minimum screen interval in m (i.e., top_screen - bot_screen)
aqui_thk = 110 # aquifer thickness (m) depending on the # of stacked layers


# In[6]:


#-------------PARAMETERIZATION------------------#
start.time = as.POSIXct("2007-01-01 00:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")
end.time =  as.POSIXct("2019-10-31 23:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")


# In[7]:


# --------------------------times----------------------------------
time.index = seq(from=start.time,to=end.time,by="1 hour")
ntime = length(time.index)
nhours = ntime-1 # from 2010-02-27 12:00:00 to 2017-07-01 00:00:00

# nyears = 100 # year

final.time = paste(nhours, 'hr')

ini.ts = 0.01 #hour
max.ts = "6 h"#hour

max.ts.ini = "0.1 h"
# max.ts = "10 day"#day


# In[8]:


if (!ugrid) {
    load(fname_model_inputs.r)
    
    # model corner coordinates
#     xrange = c(0, xlen)
#     yrange = c(0, ylen)
    xrange = c(model_origin[1], model_origin[1] + xlen)
    yrange = c(model_origin[2], model_origin[2] + ylen)
    zrange = c(z0, z0+zlen)

    grid.n_pts = c(nx, ny, nz)
    grid.d_pts = c(idx,  idy,  idz)
#     model_domain_origin = c(0,0,z0)
    model_domain_origin = c(model_origin[1], model_origin[2], z0)
    a = 0 #rotation angle
}


# In[10]:


wall.stop = 3.8 # wallclock stop time, h
check.pt = "720 h" # check point, h
# check.pt = "1 y" # check point, h

# solver
ts.acceleration = 8
max.ts.cuts = 20

diff.coeff = 1e-9 # default diffusion coefficient


# In[11]:


# output opitons
output.ts = "6 h" 
# h5.files = 73 # number of hdf5 files to write
# obs.ts = 6 # hour


# **use characteristic curve (cc) for RICHARDS mode; use saturation function (sf) for TH mode**

# In[12]:


# saturation functions
cc1 = list(M = 0.3391, alpha = 7.2727e-4, rsat = 0.16, max.cp = 1e8)
cc2 = list(M = 0.7479, alpha = 1.4319e-4, rsat = 0.1299, max.cp = 1e8)

# sf1 = list(M = 0.3391, alpha = 7.2727e-4, rsat = 0.16, max.cp = 1e8, betac = 0, power = 1.0)
# sf2 = list(M = 0.7479, alpha = 1.4319e-4, rsat = 0.1299, max.cp = 1e8, betac = 0, power = 1.0)

# if (mode == "TH") {
#     cc.names = c("sf1", "sf2")
#     cc.list = list(sf1 = sf1, sf2 = sf2) 
# } else {
    cc.names = c("cc1", "cc2")
    cc.list = list(cc1 = cc1, cc2 = cc2)
# }


# ### material properties 

# note: thermal parameters are from [Ma et al., 2012 WRR](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2011WR011281) (Table 1).
# $$Thermal\_conductivity\_dry = solid\_thermal\_conductivity*(1-porosity)$$
# $$Thermal\_conductivity\_wet = solid\_thermal\_conductivity*(1-porosity) + fluid\_thermal\_conductivity*porosity$$
# 
# para|unit
# ---|---
# thermal conductivity|W/(m*K) or (J/s)/(m*K)
# heat capacity|J/(kg*K)
# permeability|$m^2$

# Conversion from $K$ to $k$:
# 
# $$K = \dfrac{k{\rho}g}{\mu}$$
# 
# where $K$ is saturated hydraulic conductivity [$m/s$], $k$ is permeability [$m^2$], $g$ is gravitational acceleration constant [$m/s^2$], $\rho$ is fluid density [$kg/m^3$], and $\mu$ is fluid dynamic viscosity [$kg/(m{\cdot}s)$]. 
# 
# Then when T=25 deg C, 
# 
# $$k = K\dfrac{\mu}{{\rho}g} = K\dfrac{0.89{\times}10^{-3} [kg/(m{\cdot}s)]}{997 [kg/m^3] {\cdot} 9.81 [m/s^2]} = K [m/s] {\cdot} 9.1{\times}10^{-8} [m{\cdot}s] = K [m/d] {\cdot} 1/86400 [d/s] {\cdot} 9.1{\times}10^{-8} [m{\cdot}s] = K [m/d] {\cdot} 1.05{\times}10^{-12}[m{\cdot}d]$$
# 
# For a complete list of conversion factor, see the [table](https://www.sedgeochem.uni-bremen.de/perm_kf_en.html).

# In[13]:


conv_factor = 1.05e-12 # convert from K[m/d] to k[m^2]


# In[14]:


# recharge = 1.757e-9 #recharge rate 5.54 cm/yr from Fayer and Walters (1995)

##----------------------- material -------------------------------##
material.list = c("hanford", "cold_creek", "taylor_flats", "ringold_e", "ringold_lm", "ringold_a", "basalt", "alluvium")
# material.list = c("hanford", "ringold", "alluvium")


# material properties
Khf = 7000 #m/d from 300A model, William's 2008
hanford = list(ID = 1, porosity = 0.2, tortuosity = 1, perm.x = Khf*conv_factor, perm.y = Khf*conv_factor, perm.z = Khf*conv_factor/10, cc = cc.names[1],
              density = 2.76e3, sp_heat = 7.15e2, th_cond_dry = 2.2*(1-0.2), th_cond_wet = 2.2*(1-0.2) + 0.58*0.2)

# Kcc = 4.8 #m/d from Last et al
Kcc = 100 #m/d from Paul's report
cold_creek = list(ID = 2, porosity = 0.25, tortuosity = 1, perm.x = Kcc/(9.5e11), perm.y = Kcc/(9.5e11), perm.z = Kcc/(9.5e12), cc = cc.names[1],
                 density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =1.2*(1-0.25), th_cond_wet = 1.2*(1-0.25) + 0.58*0.25)
Ktf = 1 # m/d from franklin county report
taylor_flats = list(ID = 3, porosity = 0.43, tortuosity = 1, perm.x = Ktf/(9.5e11), perm.y = Ktf/(9.5e11), perm.z = Ktf/(9.5e12), cc = cc.names[2],
                   density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =1.2*(1-0.43), th_cond_wet = 1.2*(1-0.43) + 0.58*0.43)
Kre = 40 # m/d from Paul's report
ringold_e = list(ID = 4, porosity = 0.25, tortuosity = 1, perm.x = Kre/(9.5e11), perm.y = Kre/(9.5e11), perm.z = Kre/(9.5e12), cc = cc.names[1],
                density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =1.2*(1-0.25), th_cond_wet = 1.2*(1-0.25) + 0.58*0.25)
Krlm = 1 #m/d from franklin
ringold_lm = list(ID = 5, porosity = 0.43, tortuosity = 1, perm.x = Krlm/(9.5e11), perm.y = Krlm/(9.5e11), perm.z = Krlm/(9.5e12), cc = cc.names[2],
                 density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =1.2*(1-0.43), th_cond_wet = 1.2*(1-0.43) + 0.58*0.43)
Kra = 1 # similar to krlm
ringold_a = list(ID = 6, porosity = 0.43, tortuosity = 1, perm.x = Kra/(9.5e11), perm.y = Kra/(9.5e11), perm.z = Kra/(9.5e12), cc = cc.names[2],
                density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =1.2*(1-0.43), th_cond_wet = 1.2*(1-0.43) + 0.58*0.43)

Kb = 1e-3 # from Franklin
basalt = list(ID = 9, porosity = 0.2, tortuosity = 1, perm.x = Kb/(9.5e11), perm.y = Kb/(9.5e11), perm.z = Kb/(9.5e12), cc = cc.names[1],
             density = 2.76e3, sp_heat = 7.15e2, th_cond_dry = 2.2*(1-0.2), th_cond_wet = 2.2*(1-0.2) + 0.58*0.2)

Kal = 10 # from William et al. 2008, assume isotropy for perm
alluvium = list(ID = 10, porosity = 0.43, tortuosity = 1, perm.x = Kal*conv_factor, perm.y = Kal*conv_factor, perm.z = Kal*conv_factor, cc = cc.names[2],
                density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =0.7163971, th_cond_wet = 0.9334)
# Kr = 1
# ringold = list(ID = 4, porosity = 0.43, tortuosity = 1, perm.x = Kr*conv_factor, perm.y = Kr*conv_factor, perm.z = Kr*conv_factor/10, cc = cc.names[2],
#                  density = 2.65e3, sp_heat = 9.2e2, th_cond_dry =0.684, th_cond_wet = 0.9334)

# K.list = list(hanford = hanford, ringold = ringold, alluvium = alluvium)
K.list = list(hanford = hanford, cold_creek = cold_creek, taylor_flats = taylor_flats, ringold_e = ringold_e, ringold_lm = ringold_lm, 
              ringold_a = ringold_a, basalt =  basalt, alluvium = alluvium)


# In[15]:


# cond = 4.65e-13 # river conductance


# **ensemble permeability field**

# In[16]:


if (ensemble.perm) {
    ens_list = c("perm_meanX", "perm_meanY", "perm_meanZ")
    perm_dset = "perm_mean"
}


# ## injection wells

# In[18]:


if (has.injection.well) {
    

# injection well coordinates
inj_wellname = c("inj_well_s", "inj_well_m", "inj_well_d" )

inj_well_x = inj_coord.model[1]
inj_well_y = inj_coord.model[2]
inj_depth = list(s = 0.15, m = 0.35, d = 0.55)
screen_len = 0.0254 # 1 inch screen
inj_well_s = list(screen_top = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$s), 
                  screen_bot = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$s - max(idz, screen_len)))
inj_well_m = list(screen_top = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$m), 
                  screen_bot = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$m - max(idz, screen_len)))
inj_well_d = list(screen_top = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$d), 
                  screen_bot = c(inj_well_x, inj_well_y , inj_well_top - inj_depth$d - max(idz, screen_len)))

inj_well.list = list(inj_well_s = inj_well_s, inj_well_m = inj_well_m, inj_well_d = inj_well_d)

# screen_top = c(10, 10, 105) # tube T6_104.5_100cm
# screen_bot = c(10, 10, 104.95)

inj_rate = 0.002 # m3/h (or 2 Liter/h)

inj_start.time  = as.POSIXct("2016-08-14 18:00:00",tz="GMT",format="%Y-%m-%d %H:%M:%S")

inj_start.hr = length(seq(from=start.time, to=inj_start.time, by="1 hour")) -1
inj_end.hr = inj_start.hr + 8

inj_hr.list = rep(seq(inj_start.hr, inj_end.hr-0.5, by= 0.5), 3)

inj_name.list = paste0("Injection_", inj.list)
    
}


# ## obs wells

# ### import well screen

# In[19]:


## read into watershed geometry
watershed.geometry = read.csv(fname_boundary)
watershed.geometry = watershed.geometry[, 3:4]


# In[20]:


if (has.obs.wells) {

    #--------------- generate well obs input deck in Pflotran-----------------
    
#     obs_name = c("obs_s", "obs_m", "obs_d")
#     obs_east = list(screen_top = c(inj_well_x + 0.5, inj_well_y, inj_well_top),
#                    screen_bot = c(inj_well_x + 0.5, inj_well_y, inj_well_top - 1))
#     obs_west = list(screen_top = c(inj_well_x - 0.5, inj_well_y, inj_well_top),
#                    screen_bot = c(inj_well_x - 0.5, inj_well_y, inj_well_top - 1))
#     obs_south = list(screen_top = c(inj_well_x, inj_well_y - 0.5, inj_well_top),
#                    screen_bot = c(inj_well_x, inj_well_y - 0.5, inj_well_top - 1))
#     obs_north = list(screen_top = c(inj_well_x, inj_well_y + 0.5, inj_well_top),
#                    screen_bot = c(inj_well_x, inj_well_y + 0.5, inj_well_top - 1))
    
#     obs.list = list(obs_s = inj_well_s, obs_m = inj_well_m, obs_d = inj_well_d, 
#                     obs_east = obs_east, obs_west = obs_west, obs_south = obs_south, obs_north = obs_north)
    

    # read well screen info
    Wells = read.csv(fname_WellScreen, header = TRUE, stringsAsFactors=FALSE)
    Wells$WellName = paste("Well_", Wells$WellName, sep="")
    # Wells[,1] = paste("Well_", Wells[,1], sep="")
    rownames(Wells) = Wells$WellName
    # names(Wells) = c("wellname", "x", "y", "elev", "screen_top", "screen_bot")
#     Well = as.matrix(Wells[,3:7])

# selecte wells within domain
    pts_in_poly = point.in.polygon(point.x = Wells[,"Easting"], point.y= Wells[,"Northing"], pol.x = watershed.geometry[, 1], pol.y = watershed.geometry[, 2])
    Wells = Wells[which(pts_in_poly==1), ]
    
    Easting = Wells[,'Easting',drop=FALSE]
    Northing = Wells[,'Northing',drop=FALSE]
    elev = Wells[,'CASING_ELEVATION',drop=FALSE]
    screen_top = Wells[,'SCREEN_ELEV_TOP',drop=FALSE]
    screen_bot = Wells[,'SCREEN_ELEV_BOTTOM',drop=FALSE]
    
    

#     AT.list = Wells[grepl("cm", Wells$WellName), "WellName"]

#     well.list = Wells[!grepl("cm", Wells$WellName), "WellName"]
    well.list = Wells$WellName
    
    

    
}


# ### get surface dem at points

# In[21]:


if (ugrid) {
    
  
    DEM = raster(fname_DEM) # only work for .ASC file

    # plot(DEM, main= 'Surface DEM (m)')
    coordinates(Wells)= ~ Easting + Northing
    point_dem = extract(DEM, Wells)
    Wells$surface_dem = point_dem

    # surface_dem = Wells[,'surface_dem',drop=FALSE]
    names(point_dem) = Wells$WellName
    
}


# ## add flow regions

# In[22]:


slice.list = scan(fname_mass1_list, what="", sep="\n")

# flow_region = c(paste0("Injection_", inj.list))
# flow_region = c("River")

# slice.list = as.character(seq(40, 332, 1)) 

river_region = paste("Mass1_", slice.list, sep = "")
flow_region = paste("Flow_Mass1_", slice.list, sep = "")
names(river_region)  = flow_region
names(slice.list) = flow_region


# In[23]:


## create river flow bc list

fname.river_datum = paste(fname.DatumH, slice.list, ".txt", sep = "")
fname.river_gradient = paste(fname.Gradient, slice.list, ".txt", sep = "")
names(fname.river_datum)= flow_region
names(fname.river_gradient)= flow_region


# ## add solutes

# In[24]:


# ## inject every 0.5 hr for a total of 8 hrs at three different depths (15cm, 35cm, and 55cm)
# inj.list = c(paste0('s',as.character(seq(1, 16, 1))), paste0('m',as.character(seq(1, 16, 1))), 
#              paste0('d',as.character(seq(1, 16, 1))))

# solute.list = c("Solute_river", paste0("Solute_inj_", inj.list))

solute.list = c("Solute_river")

## condition coupler, each flow region corresponds to one solute
solute.coupler.list = c(rep(solute.list, length(flow_region)))
names(solute.coupler.list)= flow_region

## concentration list should have same number as of solute list
# concentration.list = c("Concentration_river", paste0("Concentration_inj_", inj.list))
concentration.list = c("Concentration_river")
names(concentration.list) = solute.list

## tracer list should has same num. of solute list
# tracer.list = c("Tracer_river", paste0("Tracer_inj_", inj.list))
tracer.list = c("Tracer_river")
names(tracer.list) = concentration.list


# In[9]:


if (ugrid) {
    region.list = c('All', 'Top', 'Bottom', 'Sides')
}


# ## add inland bc

# **Max Buffer Size**: Optional attribute specifying the maximum number of
# time slices to load into the buffer during each file access. Buffering helps
# balance file access with memory use. Smaller buffers require more file
# accesses and less memory.

# In[219]:


# # datasets
# flow.BC = c("Flow_West", "Flow_South", "Flow_North", "Flow_East")
# # BC.all = c("BC_East", "BC_West", "BC_South", "BC_North")
# BC.list = c("BC_West", "BC_South", "BC_North", "BC_East")
# BC.face = c("West", "South", "North", "East")
# names(flow.BC) = BC.face
# names(BC.list) = flow.BC
# max.buff = 250


# # write input deck

# In[28]:


f <- file(fname_pflotran.in, open = "wt")
cat <- function(...){
    base::cat(..., file=f)
    }
# cat("Hello World\n")
# close(f)


# ## beginning of file

# In[29]:


# sink(file = fname_pflotran.in, append = FALSE, type = "output")


# In[30]:


cat("## ===============BEGINNING of FILE=========================")
cat("\n")
cat("SIMULATION\n")
cat("  SIMULATION_TYPE SUBSURFACE\n")
cat("  PROCESS_MODELS\n")
cat("  SUBSURFACE_FLOW flow\n")
# cat("#  MODE RICHARDS\n")
cat(paste0("    MODE ", mode, "\n"))
cat("  /\n")

if (has.solute) {
cat("  SUBSURFACE_TRANSPORT transport\n")
cat("    MODE GIRT\n")
cat("  /\n")
}
cat("END\n")
cat("\n")

cat("CHECKPOINT\n")
cat(paste("  PERIODIC TIME"), check.pt, "\n")
cat("  FORMAT HDF5\n") # .chk is not supported for ugrid
cat("/\n")
cat("\n")

# cat("#  RESTART pflotran_bigplume-restart.chk\n")
# use result from previoius simulaiton and reset time to zero
cat("#  RESTART \n") 
cat("#  FILENAME pflotran_bigplume-restart.chk \n") 
cat("#  RESET_TO_TIME_ZERO\n")
cat("##  REALIZATION_DEPENDENT\n")
cat("#  END\n")
cat("\n")

cat("INPUT_RECORD_FILE\n")
cat("END\n")
cat("\n")
cat("\n")

cat("SUBSURFACE")
cat("\n")
cat(paste("WALLCLOCK_STOP"), wall.stop, "h")
cat("\n")
cat("\n")


# ## chemistry

# need to add `Tracer_Age`, `DATABASE`, `ACTIVITY` , `AGE`, if simulate age

# In[31]:


if (has.solute) {
    

cat('#=======================chemistry========================\n')

cat("CHEMISTRY\n")
cat("  PRIMARY_SPECIES\n")

if (has.age) {

    for (itracer in tracer.list) {
      cat(paste("   ", itracer), "\n")
    }
    cat("    Tracer_Age\n") # for age
    cat("  /\n")
    cat("  DATABASE tracer_HFR.dat\n") # for age
    cat("  ACTIVITY_COEFFICIENTS OFF\n") # for age
    cat("  OUTPUT\n")
    cat("    ALL\n")
    cat("    AGE\n") # for age
    cat("    TOTAL\n")
    cat("/\n")
    cat("END\n")
    
    } else {
    
    for (itracer in tracer.list) {
      cat(paste("   ", itracer), "\n")
    }
    cat("  /\n")
    cat("  OUTPUT\n")
    cat("    ALL\n")
    cat("    TOTAL\n")
    cat("/\n")
    cat("END\n")    
}
    
}


# ## solver options

# **note: options to tweak the solver**
# 1. Increase `TS_ACCELERATION` (default is 8)
# 2. Increase `TIMESTEP_MAXIMUM_GROWTH_FACTOR` (default is 2)
# 3. Increase `RTOL`,`STOL` and `ATOL` (default is 1e-8, 1e-8 and 1e-50 respectively)

# In[32]:


cat('#=======================solver options========================')
cat("\n")
cat("TIMESTEPPER FLOW")
cat("\n")
cat(paste("  TS_ACCELERATION", ts.acceleration), "\n")
cat(paste("  MAX_TS_CUTS", max.ts.cuts), "\n")
cat("#  MAX_STEPS 100\n")
cat("END\n")
cat("\n")

cat("NEWTON_SOLVER FLOW")
cat("\n")
cat("  VERBOSE_ERROR_MESSAGING") ## add detailed error message
cat("\n")
cat("  MAXIT 20")
cat("\n")
cat("#  RTOL 1.d-8")
cat("\n")
cat("#  ATOL 1.d-50")
cat("\n")
cat("#  STOL 1.d-8")
cat("\n")
cat("#  ITOL_UPDATE 1.d0")
cat("\n")
cat("END")
cat("\n")
cat("\n")

cat("LINEAR_SOLVER FLOW")
cat("\n")
cat("END")
cat("\n")
cat("\n")

if (has.solute) {
    
cat("\n")
cat("TIMESTEPPER TRANSPORT")
cat("\n")
cat(paste("  TS_ACCELERATION", ts.acceleration))
cat("\n")
cat(paste("  MAX_TS_CUTS", max.ts.cuts))
cat("\n")
cat("END")
cat("\n")
cat("\n")

cat("NEWTON_SOLVER TRANSPORT")
cat("\n")
cat("  NO_INFINITY_NORM")
cat("\n")
cat("END")
cat("\n")
cat("\n")

cat("LINEAR_SOLVER TRANSPORT")
cat("\n")
cat("END")
cat("\n")
cat("\n")
    
}


# ## discretization

# `DXYZ` may not be used with `BOUNDS`

# In[33]:


cat('#=======================discretization========================\n')

if (ugrid) {
    cat("GRID\n")
    cat(paste0("  TYPE unstructured ", fname_material.h5, "\n"))
} else {
    

    cat("GRID\n")
    cat("  TYPE structured\n")
    cat("  NXYZ ")
    cat(grid.n_pts)
    cat("\n")
    cat("  ORIGIN ")
    cat(model_domain_origin)
    cat("\n")
    cat("  DXYZ \n")
    cat("  ")

    if (vary.mesh) {
    #--------- write varying discretization---------
        lx = nx %/% 5 +1
        for (ilx in 1:(lx-2)) {
            cat(paste("    ",paste(dx[((ilx-1)*5+1):(ilx*5)],collapse=" "),"\\", "\n"))
        }
        cat(paste("    ",paste(dx[(ilx*5+1):nx],collapse=" "), "\n"))

        ly = ny %/% 5 +1
        for (ily in 1:(ly-2)) {
            cat(paste("    ",paste(dy[((ily-1)*5+1):(ily*5)],collapse=" "),"\\", "\n"))
        }
        cat(paste("    ",paste(dy[(ily*5+1):ny],collapse=" "), "\n"))

        lz = nz %/% 5 +1
        for (ilz in 1:(lz-2)) {
            cat(paste("    ",paste(dz[((ilz-1)*5+1):(ilz*5)],collapse=" "),"\\", "\n"))
        }
        cat(paste("    ",paste(dz[(ilz*5+1):nz],collapse=" "), "\n"))
    #------------------------------------------------
    } else {

        cat(grid.d_pts[1])
        cat("\n")
        cat("  ")
        cat(grid.d_pts[2])
        cat("\n")
        cat("  ")
        cat(grid.d_pts[3])
        cat("\n")
    }

    cat("/\n")
    cat("\n")
}
    
cat("END\n")


# ## fluid properties

# In[34]:


cat('#=======================fluid properties========================')
cat("\n")
cat("FLUID_PROPERTY")
cat("\n")
cat(paste("  DIFFUSION_COEFFICIENT", diff.coeff))
cat("\n")
cat("END")
cat("\n")


# ## datasets

# In[35]:


cat('#=======================datasets========================')
cat("\n")
# cat("skip\n")
cat("DATASET Initial_Head\n")
cat(paste("  FILENAME", fname_H.initial.h5), "\n")
cat("  HDF5_DATASET_NAME Initial_Head\n")
cat("END\n")
cat("\n")
# cat("noskip\n")

if (mode == 'TH') {
    

cat("DATASET Initial_Temp\n")
cat(paste("  FILENAME", fname_Temp.initial.h5), "\n")
cat("  HDF5_DATASET_NAME Initial_Temp\n")
cat("END\n")
cat("\n")

cat("DATASET BC_Temp\n")
cat(paste("  FILENAME", fname_Temp.BC.h5), "\n")
cat("  HDF5_DATASET_NAME BC_Temp\n")
cat(paste("  MAX_BUFFER_SIZE", max.buff), "\n")
cat("END\n")
cat("\n")
}


# if (ugrid) {
    
#     cat("DATASET BC_Head\n")
#     cat(paste("  FILENAME", fname_H.BC.h5), "\n")
#     cat("  HDF5_DATASET_NAME BC_Head\n")
#     cat(paste("  MAX_BUFFER_SIZE", max.buff), "\n")
#     cat("END\n")
#     cat("\n")

# } else {

# #     if (is.flowBC) {
# #         for (iBC in BC.list) {
# #           cat(paste("DATASET", iBC))
# #           cat("\n")
# #           cat(paste("  FILENAME", fname_H.BC.h5))
# #           cat("\n")
# # #           cat(paste("  HDF5_DATASET_NAME", iBC))
# #           cat(paste("  HDF5_DATASET_NAME BC_Head"))  
# #           cat("\n")
# #           cat(paste("  MAX_BUFFER_SIZE", max.buff))
# #           cat("\n")
# #           cat("END")
# #           cat("\n")
# #           cat("\n")
# #         }
# #     }
    
#     cat("DATASET BC_Head\n")
#     cat(paste("  FILENAME", fname_H.BC.h5), "\n")
#     cat("  HDF5_DATASET_NAME BC_Head\n")
#     cat(paste("  MAX_BUFFER_SIZE", max.buff), "\n")
#     cat("END\n")
#     cat("\n")
# }


# In[36]:


if (ensemble.perm) {

    for (iperm in ens_list) {
    
        cat("DATASET", iperm, "\n")
        cat(paste("  FILENAME", fname_ens_perm.h5), "\n")
        cat("END\n")
        cat("\n")
    }
}


# ## material properties

# In[37]:


cat('#=======================material properties========================\n')

# if (mode == "TH") {
#     for (imaterial in material.list) {  
#       cat(paste("MATERIAL_PROPERTY", imaterial, "\n"))
#       cat("  ID", K.list[[imaterial]]$ID, "\n")
#       cat("  POROSITY", K.list[[imaterial]]$porosity, "\n")
#       cat("  TORTUOSITY", K.list[[imaterial]]$tortuosity, "\n")    
#       cat(paste("  SATURATION_FUNCTION", K.list[[imaterial]]$cc, "\n"))    
#       cat("  PERMEABILITY\n")
#         cat("  PERM_X", K.list[[imaterial]]$perm.x, "\n")
#         cat("  PERM_Y", K.list[[imaterial]]$perm.y, "\n")
#         cat("  PERM_Z", K.list[[imaterial]]$perm.z, "\n")
#       cat('  /\n')
#         cat("  ROCK_DENSITY", K.list[[imaterial]]$density, "\n")
#         cat("  SPECIFIC_HEAT", K.list[[imaterial]]$sp_heat, "\n")
#         cat("  THERMAL_CONDUCTIVITY_DRY", K.list[[imaterial]]$th_cond_dry, "\n")
#         cat("  THERMAL_CONDUCTIVITY_WET", K.list[[imaterial]]$th_cond_wet, "\n")
#       cat('END\n')
#       cat("\n")  
#     }
# } else {
    for (imaterial in material.list) {  
      cat(paste("MATERIAL_PROPERTY", imaterial, "\n"))
      cat("  ID", K.list[[imaterial]]$ID, "\n")
      cat("  POROSITY", K.list[[imaterial]]$porosity, "\n")
      cat("  TORTUOSITY", K.list[[imaterial]]$tortuosity, "\n")    
      cat(paste("  CHARACTERISTIC_CURVES", K.list[[imaterial]]$cc, "\n"))    
      cat("  PERMEABILITY\n")
        if (ensemble.perm) {
            cat("    ANISOTROPIC\n")
            cat("    DATASET", perm_dset, "\n")
            } else {
            cat("  PERM_X", K.list[[imaterial]]$perm.x, "\n")
            cat("  PERM_Y", K.list[[imaterial]]$perm.y, "\n")
            cat("  PERM_Z", K.list[[imaterial]]$perm.z, "\n")
            }
      cat('  /\n')
#         cat("  ROCK_DENSITY", K.list[[imaterial]]$density, "\n")
#         cat("  SPECIFIC_HEAT", K.list[[imaterial]]$sp_heat, "\n")
#         cat("  THERMAL_CONDUCTIVITY_DRY", K.list[[imaterial]]$th_cond_dry, "\n")
#         cat("  THERMAL_CONDUCTIVITY_WET", K.list[[imaterial]]$th_cond_wet, "\n")
      cat('END\n')
      cat("\n")  
    }
# }



# ## saturation functions

# In[38]:


cat('#=======================saturation fuctions========================\n')

# if (mode == "TH") {
#     for (icc in cc.names) {
  
#       cat(paste("SATURATION_FUNCTION", icc), "\n")
#       cat("  SATURATION_FUNCTION_TYPE VAN_GENUCHTEN\n")
#       cat("  PERMEABILITY_FUNCTION_TYPE BURDINE\n")
#       cat(paste("    RESIDUAL_SATURATION"), cc.list[[icc]]$rsat, "\n")
#       cat(paste("    LAMBDA"), cc.list[[icc]]$M, "\n")
#       cat(paste("    ALPHA"), cc.list[[icc]]$alpha, "\n")      
#       cat(paste("    MAX_CAPILLARY_PRESSURE"), cc.list[[icc]]$max.cp, "\n")
#       cat(paste("    BETAC"), cc.list[[icc]]$betac, "\n")
#       cat(paste("    POWER"), cc.list[[icc]]$power, "\n")
#       cat('/\n')
#       cat("\n")
#     }

# } else {
    for (icc in cc.names) {
  
      cat(paste("CHARACTERISTIC_CURVES", icc), "\n")
      cat("  SATURATION_FUNCTION VAN_GENUCHTEN\n")
      cat(paste("    M"), cc.list[[icc]]$M, "\n")
      cat(paste("    ALPHA"), cc.list[[icc]]$alpha, "\n")
      cat(paste("    LIQUID_RESIDUAL_SATURATION"), cc.list[[icc]]$rsat, "\n")
      cat(paste("    MAX_CAPILLARY_PRESSURE"), cc.list[[icc]]$max.cp, "\n")
      cat('  /\n')
      cat("  PERMEABILITY_FUNCTION BURDINE_VG_LIQ\n")
      cat(paste("    M"), cc.list[[icc]]$M, "\n")
      cat(paste("    LIQUID_RESIDUAL_SATURATION"), cc.list[[icc]]$rsat, "\n")
      cat('  /\n')
      cat('END\n')
      cat("\n")
    }
# }


# ## output options

# In[39]:


cat("\n")
cat('#=======================output options========================\n')
cat("OUTPUT\n")
cat("  TIME_UNITS h\n")
cat("  VARIABLES\n")
cat("    LIQUID_PRESSURE\n")
# cat("#    LIQUID_HEAD\n")
cat("    LIQUID_SATURATION\n")
# cat("#    MATERIAL_ID_KLUDGE_FOR_VISIT\n")  # add composite material ids
# cat("#    RESIDUAL\n")
# cat("    TEMPERATURE\n") # output thermal results
cat('  /\n')
cat("\n")

cat("  SNAPSHOT_FILE\n")
# cat("#  NO_PRINT_INITIAL\n")
cat(paste("  PERIODIC TIME"), output.ts, "\n")
# cat("#  PERIODIC TIME 6 h between 32400 h and 76800 h\n")
# cat("#  FORMAT HDF5 MULTIPLE_FILES TIMES_PER_FILE 73\n")
cat("  FORMAT HDF5 SINGLE_FILE\n")
# cat("  FORMAT VTK\n")
cat('  /\n')
cat("\n")

cat("  MASS_BALANCE_FILE\n")
# cat("#  NO_PRINT_INITIAL\n")
cat(paste("  PERIODIC TIME"), output.ts, "\n")
# cat("#  PERIODIC TIME 6 h between 32400 h and 76800 h\n")
cat('  /\n')
cat("\n")

cat("  OBSERVATION_FILE\n")
# cat("#  NO_PRINT_INITIAL\n")
cat(paste("  PERIODIC TIME"), output.ts, "\n")
cat('  /\n')
cat("\n")

cat("#  VELOCITY_AT_CENTER\n ") # OUTPUT darcy velocity at cell center
cat("#  VELOCITY_AT_FACE\n ")  # output darcy velocity at cell face
cat('END\n')
cat("\n")
cat("\n")


# ## times

# In[40]:


cat('#=======================times========================')
cat("\n")
cat("TIME")
cat("\n")
# cat(paste("  FINAL_TIME", nhours, "h"))
cat(paste("  FINAL_TIME", final.time), "\n")

cat(paste("  INITIAL_TIMESTEP_SIZE", ini.ts, "h"), "\n")
cat(paste("  MAXIMUM_TIMESTEP_SIZE", max.ts), "\n")
# cat(paste("  MAXIMUM_TIMESTEP_SIZE", max.ts, "at 0. h"), "\n")
# cat(paste("  MAXIMUM_TIMESTEP_SIZE", max.ts.ini, "at", inj_start.hr, "h"), "\n")
# cat(paste("  MAXIMUM_TIMESTEP_SIZE", max.ts, "at", inj_end.hr, "h"), "\n")

cat('END\n')
cat("\n")


# ## regions

# In[41]:


cat('#=======================regions========================\n')
cat("\n")

if (ugrid) {
    for (i in region.list) {
        cat(paste0('REGION ', i), '\n')
        cat(paste0('  FILE ', fname_material.h5), '\n')
        cat('END\n')
        cat('\n')
    }
    
} else {
    

    cat('REGION All\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[1], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[2], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION Bottom\n')
    cat('FACE BOTTOM\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[1], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[2], zrange[1])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION Top\n')
    cat('FACE TOP\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[1], zrange[2])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[2], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION South\n')
    cat('FACE SOUTH\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[1], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[1], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION North\n')
    cat('FACE NORTH\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[2], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[2], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION West\n')
    cat('FACE WEST\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[1], yrange[1], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[1], yrange[2], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')

    cat('REGION East\n')
    cat('FACE EAST\n')
    cat('  COORDINATES\n')
    cat("  ")
    cat(xrange[2], yrange[1], zrange[1])
    cat('\n')
    cat("  ")
    cat(xrange[2], yrange[2], zrange[2])
    cat('\n')
    cat('  /\n')
    cat('END\n')
    cat('\n')   
    
}


# In[42]:


# %%%%%%%%%%%%%%%%%%%river regions%%%%%%%%%%%%%%%%%%%%%%%%%%

for (iriver in river_region) {
  cat(paste('REGION ', iriver, sep = '' ), "\n")
  cat(paste('  FILE ', fname_material.h5), "\n")
  cat('END\n')
  cat("\n")
}
cat("\n")

#     cat('REGION River\n') 
#     cat(paste0('  FILE ', fname_material.h5), '\n')
#     cat('END\n')


# ### injection location

# In[43]:


# # %%%%%%%%%%%% add injection well %%%%%%%%%%%% ##
# for (iname in inj_wellname) {
    
#     cat(paste0('REGION ', iname), '\n')
#     cat('  COORDINATES\n')
#     cat(inj_well.list[[iname]]$screen_bot, '\n')
#     cat(inj_well.list[[iname]]$screen_top, '\n')
#     cat('  /\n')
#     cat('/\n')
#     cat('\n')
# }


# ### add obs wells

# In[44]:


selected.wells = c()

if (has.obs.wells) {
    

#------------- %put observation wells in "regions" of input deck----------------------
    cat('#---------- Observation wells--------------#\n')
    cat("\n")
  
    if (ugrid) {
    
        for (iwell in well.list) {
            if (screen_top[iwell, ] >= point_dem[iwell] - aqui_thk & screen_bot[iwell, ] <= point_dem[iwell] & round(screen_top[iwell,] - screen_bot[iwell, ]) >= min_z) {

                screen_length = screen_top[iwell, ] - screen_bot[iwell, ]
                screen.list = screen_top[iwell, ] - seq(1, screen_length, 2) # set screen interval every 2 m 
                screen.list = screen.list[screen.list > point_dem[iwell] - aqui_thk + 5] # add 1m to ensure the bottom of screen does not fall out of the model bottom
                nscreen = length(screen.list)

                if (nscreen > 0) {
                    selected.wells = c(selected.wells, iwell)

                     for (i in 1:nscreen) {
                      cat(paste0('REGION ', iwell, '_', i), '\n')
                      cat('  COORDINATE ')
                      cat(Easting[iwell,],Northing[iwell,], screen.list[i], '\n')
                      cat('/\n')
                      cat('\n')
                     }
                }

            }
        }
    } else {
        
        for (iwell in well.list) {

          if (screen_top[iwell, ] >= z0 & screen_bot[iwell, ] <= z0 + zlen & round(screen_top[iwell,] - screen_bot[iwell, ]) >= idz) {
            ind = which((z >= round(screen_bot[iwell, ], 3)) & (z <= round(screen_top[iwell,], 3)))
            iscreen = z[ind]
            nscreen = length(iscreen)
              
            selected.wells = c(selected.wells, iwell)
              
            for (j in 1:nscreen) {
              cat(paste0('REGION ', iwell, '_', j), '\n')
              cat('  COORDINATE ')
              cat(Easting[iwell,], Northing[iwell,], z[ind[j]], '\n')
              cat('/\n')
              cat('\n')
            }
          }
        }
        
    }
    
##-------------add aquifer tubes and riverbed thermistors--------------##    
#     if (ugrid) {
#         for (iwell in AT.list) {

#             if (screen_top[iwell, ] <= point_dem[iwell] - 0.25) {

#               selected.wells = c(selected.wells, iwell)  

#               cat(paste0('REGION ', iwell), '\n')
#               cat('  COORDINATE ')
#               cat(Easting[iwell,],Northing[iwell,], screen_top[iwell,], '\n')
#               cat('/\n')
#               cat('\n')
#           }

#        }
#     } else {
#         for (iwell in AT.list) {

#               selected.wells = c(selected.wells, iwell)  

#               cat(paste0('REGION ', iwell), '\n')
#               cat('  COORDINATE ')
#               cat(Easting[iwell,],Northing[iwell,], screen_top[iwell,], '\n')
#               cat('/\n')
#               cat('\n')
          

#        }
#     }

}

write.table(selected.wells, file = fname_selected_wells, sep = '\t', row.names = FALSE, col.names = FALSE)


# ## flow conditions

# In[45]:


cat("#==================flow conditions=========================\n")

cat("MINIMUM_HYDROSTATIC_PRESSURE -1.d0\n")
cat("\n")

cat("FLOW_CONDITION Initial\n")
cat("  TYPE\n")
cat("    PRESSURE hydrostatic\n")
if (mode == "TH") {
    cat("   TEMPERATURE dirichlet\n")
}
cat('  /\n')
# cat("  CYCLIC\n")
cat("  DATUM DATASET Initial_Head\n")
# cat("#  DATUM 0 0 105\n")
cat("  PRESSURE 101325\n")
if (mode == "TH") {
#    cat(paste('  TEMPERATURE ', gw_temp, "\n"))
    cat('  TEMPERATURE DATASET Initial_Temp\n')
}
cat("END\n")
cat("\n")


# In[46]:


# ## flow BCs for model four sides (East, West, North, South)

# if (ugrid) {
#     cat("FLOW_CONDITION Inland\n")
#     cat("  TYPE\n")
#     cat("    PRESSURE hydrostatic\n")
#     if (mode == "TH") {
#         cat("    TEMPERATURE dirichlet\n")
#     }
#     cat('  /\n')
#     cat("  CYCLIC\n")
#     cat("  DATUM DATASET BC_Head\n")
# #     cat("#  DATUM 0 0 105\n")
#     cat("  PRESSURE 101325\n")
#     if (mode == "TH") {
# #        cat(paste('  TEMPERATURE ', gw_temp, "\n"))
#        cat('  TEMPERATURE DATASET BC_Temp\n')
#     }
#     cat("END\n")
#     cat("\n")

# } else {
#     if (is.flowBC) {
#         for (iflow.BC in flow.BC) {

# #            if (iflow.BC == "Flow_East") {
# #               cat(paste("FLOW_CONDITION"), iflow.BC, "\n")
# #               cat("  TYPE\n")
# #               cat("    PRESSURE seepage\n")
# #     #           cat("    PRESSURE conductance\n")
# #                 if (mode == "TH") {
# #                 cat("    TEMPERATURE dirichlet\n")
# #                 }

# #               cat("  /\n")
# #     #           cat("  CONDUCTANCE", cond, "\n")
# #     #           cat("  CYCLIC\n")
# #               cat(paste("  DATUM file"), fname.DatumH, "\n")
# #               cat("  PRESSURE 101325\n")
# #                 if (mode == "TH") {
# # #                 cat(paste('  TEMPERATURE ', gw_temp, "\n"))
# #                     cat('  TEMPERATURE DATASET BC_Temp\n')
# #                 }
# #               cat("  GRADIENT\n")
# #               cat(paste("   PRESSURE file"), fname.Gradient, "\n")
# #               cat("  /\n")
# #               cat("/\n")
# #               cat("\n")

# #            } else {


#               cat(paste("FLOW_CONDITION"), iflow.BC, "\n")

#               cat("  TYPE\n")
#               cat("    PRESSURE hydrostatic\n")
#                 if (mode == "TH") {
#                 cat("    TEMPERATURE dirichlet\n")
#                 }
#               cat("  /\n")
#               cat("  CYCLIC\n")
# #               cat(paste("  DATUM DATASET"), BC.list[iflow.BC], "\n")
#               cat(paste("  DATUM DATASET BC_Head"), "\n")
#               cat("  PRESSURE 101325\n")
#                 if (mode == "TH") {
# #                 cat(paste('  TEMPERATURE ', gw_temp, "\n"))
#                     cat('  TEMPERATURE DATASET BC_Temp\n')
#                 }

#               cat("/\n")
#               cat("\n")
#                }
#         }
# #     }

# }


# In[47]:


#%%%%%%%%%%%%%%%%%%%% river regions %%%%%%%%%%%%%%%%%%%%%%%%%
for (iflow in flow_region) {
  cat(paste("FLOW_CONDITION"), iflow, "\n")

  cat("  INTERPOLATION LINEAR\n")
  cat("  TYPE\n")
  cat("    PRESSURE seepage\n")
  if (mode == "TH") {
    cat("    TEMPERATURE dirichlet\n")
    }
  cat('  /\n')
#   cat(paste("  CONDUCTANCE"), cond.list[iflow], "\n")
#   cat("  CYCLIC\n")
#   cat(paste("  DATUM file ", fname_bc_dir, fname.river_datum[iflow], sep = ""), "\n")
  cat(paste("  DATUM file ", fname.river_datum[iflow] ,sep = ""), "\n")
#   cat(paste("  DATUM 0 0 105"), "\n")
  cat("  PRESSURE 101325\n")
  cat("  GRADIENT\n")
  cat(paste("    PRESSURE file ", fname.river_gradient[iflow], sep = ""), "\n")
  cat('  /\n')
  if (mode == "TH") {
    cat(paste('  TEMPERATURE FILE ', fname.River.Temp, sep = ""), "\n")
   }    
  cat('/\n')
  cat("\n")
}


# In[48]:


# cat("FLOW_CONDITION Recharge")
# cat("\n")
# cat("  TYPE")
# cat("\n")
# cat("    FLUX neumann")
# cat("\n")
# cat('/')
# cat("\n")
# cat(paste("    FLUX"), recharge)
# cat("\n")
# cat('/')
# cat("\n")


# ### **injection**

# - NEIGHBOR_PERM: scaling weighted as a function of the interfacial area and permeability of neighboring cells (in x,y)

# In[49]:


# for (i in 1:length(inj.list)) {
#     cat("FLOW_CONDITION ", inj_name.list[i], "\n")
#     cat("TYPE\n")
#     cat("  RATE scaled_volumetric_rate NEIGHBOR_PERM\n")
#     cat("/\n")
#     cat("SYNC_TIMESTEP_WITH_UPDATE\n")
#     cat("RATE list\n")
#     cat("  TIME_UNITS h\n")
#     cat("  DATA_UNITS m^3/h\n")
#     cat("0.d0 0.d0\n")
#     cat(inj_hr.list[i], " ", inj_rate, "\n")
#     cat(inj_hr.list[i] + 0.5, " ", "0.d0\n")
#     cat(nhours, " ", "0.d0\n")
#     cat("  /\n")
#     cat("/\n")
#     cat("\n")
# }


# ## transport conditions

# - use `dirichlet zero gradient` when mass is moving in and out of boundary

# In[50]:


if (has.solute) {

    cat("#==================transport conditions=========================")
    cat("\n")
    cat("TRANSPORT_CONDITION Initial")
    cat("\n")
    cat("  TYPE dirichlet_zero_gradient") 
    cat("\n")
    cat("  CONSTRAINT_LIST")
    cat("\n")
    cat("  ")
    cat(paste(0, "Concentration_initial"))
    cat("\n")
    cat("/")
    cat("\n")
    cat("END\n")
    cat("\n")

    for (isolute in solute.list) {
      cat(paste("TRANSPORT_CONDITION"), isolute)
      cat("\n")
      cat("#  TYPE dirichlet_zero_gradient\n") 
      cat("  TYPE zero_gradient\n") # Glenn inplemented third-type-bc for transport
      cat("  CONSTRAINT_LIST\n")
      cat("  ")
      cat(paste(0, concentration.list[isolute]))
      cat("\n")
      cat("/")
      cat("\n")
      cat("END\n")
      cat("\n")
    }

}


# ## constraints

# **need to add `Tracer_Age` for age simulation**

# In[51]:


if (has.solute) {

    cat("#==================constraints=========================\n")

    # transport solute concentration (river tracers)
    for (iconc in concentration.list) {
      cat(paste("CONSTRAINT", iconc), "\n")
      cat("  CONCENTRATIONS\n")
      for (itracer in tracer.list) {
        if (itracer == tracer.list[iconc]) {
          cat("   ", paste(itracer), "1.d0 T")
        } else {
          cat("   ", paste(itracer), "1.d-20 T")
        }
        cat("\n")

      }

      if (has.age) {
         cat("    Tracer_Age  1.d-20 T\n") 
      }  
      cat("  /\n")
      cat("END\n")
      cat("\n")
    }


    ## initial solute concentration
    cat("\n")
    cat("CONSTRAINT Concentration_initial\n")
    cat("  CONCENTRATIONS\n")

    for (itracer in tracer.list) {
      cat("   ", paste(itracer), "1.d-20 T\n")
    }
      if (has.age) {
         cat("    Tracer_Age  1.d-20 T\n") 
      } 
    cat("  /\n")
    cat("END\n")
    cat("\n")
}


# ## condition couplers

# In[52]:


cat("#==================condition couplers=========================\n")

cat("INITIAL_CONDITION\n")
cat("  FLOW_CONDITION Initial\n")
if (has.solute) {
    cat("  TRANSPORT_CONDITION Initial\n")
    }
cat("  REGION All\n")
cat("END\n")
cat("\n")

# #%%%%%%%%%%%%%%%%%%%%% River BC coupling %%%%%%%%%%%%%%%%%%%%%%%%%%
# cat(paste("BOUNDARY_CONDITION River\n"))
# cat(paste("  FLOW_CONDITION River\n"))
# if (has.solute) {
#     cat(paste("  TRANSPORT_CONDITION Solute_river\n"))
#     }
# if (ugrid) {
# cat(paste("  REGION Top\n"))
# } else {
# cat(paste("  REGION River\n"))    
# }

# cat("END\n")
# cat("\n")

for (iflow in flow_region) {
  cat(paste("BOUNDARY_CONDITION River_", slice.list[iflow], sep = ""))
  cat("\n")
  cat(paste("  FLOW_CONDITION"), iflow)
  cat("\n")
  cat(paste("  TRANSPORT_CONDITION"), solute.coupler.list[iflow])
  cat("\n")
  cat(paste("  REGION"), river_region[iflow])
  cat("\n")
  cat("END")
  cat("\n")
  cat("\n")
}


# In[53]:


# for (iflow in flow_region) {
#   cat(paste("BOUNDARY_CONDITION River_", slice.list[iflow], sep = ""))
#   cat("\n")
#   cat(paste("  FLOW_CONDITION"), iflow)
#   cat("\n")
#   cat(paste("  TRANSPORT_CONDITION"), solute.coupler.list[iflow])
#   cat("\n")
#   cat(paste("  REGION"), river_region[iflow])
#   cat("\n")
#   cat("END")
#   cat("\n")
#   cat("\n")
# }

# for (iface in BC.face) {
#   cat(paste("BOUNDARY_CONDITION", iface))
#   cat("\n")
#   cat(paste("  FLOW_CONDITION", flow.BC[iface]))
#   cat("\n")
#   if (iface == "North") {
#     cat(paste("  TRANSPORT_CONDITION", solute.list[5]))
#   } else {
#     cat("  TRANSPORT_CONDITION Initial")
#   }
#   cat("\n")
#   cat(paste("  REGION"), iface) 
#   cat("\n")
#   cat("END")
#   cat("\n")
#   cat("\n")
# }


# In[54]:


# ##%%%%%%%%%%%%%%%% transient inland BC %%%%%%%%%%%%%##
# if (ugrid) {

#     cat(paste("BOUNDARY_CONDITION Inland\n"))
#     cat(paste("  FLOW_CONDITION Inland\n"))
#     if (has.solute) {
#         cat(paste("  TRANSPORT_CONDITION Initial\n"))
#         }
#     cat(paste("  REGION Sides\n"))
#     cat("END\n")
#     cat("\n")

#     } else {

#     if (is.flowBC) {

#         for (iface in BC.face) {        

#           cat(paste("BOUNDARY_CONDITION", iface))
#           cat("\n")
#           cat(paste("  FLOW_CONDITION", flow.BC[iface]))
#           cat("\n")
# #             if (iface == "East") {
# #                 cat("  TRANSPORT_CONDITION ", solute.list[1])
# #             } else {
#                 cat("  TRANSPORT_CONDITION Initial")
# #             }

#           cat("\n")
# #             if (iface == "East") {            
# #                 cat(paste("  REGION River", '\n'))
# #                 } else {
#                 cat(paste("  REGION"), iface, '\n')
# #             }
#           cat("END\n")
#           cat("\n")
#         }
#     }
    
# }


# **add source sink**

# In[55]:


# for (i in 1:length(inj.list)) {
#     cat(paste0("SOURCE_SINK ", "Inj_", inj.list[i], "\n"))
#     cat("  FLOW_CONDITION ", inj_name.list[i], "\n")
#     cat("  TRANSPORT_CONDITION", solute.list[i + 1], "\n") # skip `Solute_river`
#     cat("  REGION ", inj_wellname[ceiling(i/16)], "\n")
#     cat("/\n")
#     cat("\n")
# }


# ## stratigraphy couplers

# In[56]:


cat("#==================stratigraphy couplers=========================")
cat("\n")
cat("STRATA")
cat("\n")
cat(paste("  FILE", fname_material.h5))
cat("\n")
cat("END")
cat("\n")
cat("\n")


# ## observation points

# In[57]:


if (has.obs.wells) {
    

cat("#==================observation points=========================\n")
    # % putting in "observation points" in input deck
#     for (iobs in names(obs.list)) {

#       if (obs.list[[iobs]]$screen_top[3] >= z0 & obs.list[[iobs]]$screen_bot[3] <= z0+zlen & round(obs.list[[iobs]]$screen_top[3] - obs.list[[iobs]]$screen_bot[3], 3) >= idz) {
#         ind = which((z >= round(obs.list[[iobs]]$screen_bot[3], 3)) & (z <= round(obs.list[[iobs]]$screen_top[3], 3)))
#         iscreen = z[ind]
#         nscreen = length(iscreen)
#         # wellname = rownames(Well)[iwell]
#         for (j in 1:nscreen) {

#           cat('OBSERVATION\n')
#           cat(paste('  REGION ', iobs, '_', j, sep = ''), '\n')
#           cat('  VELOCITY \n')
#           cat('/\n')
#           cat('\n')
#         }
#       }
#     }
#         for (iwell in well.list) {
            
            
#         screen.list = screen_top[iwell, ] - seq(1, 20)
#         screen.list = screen.list[screen.list >= screen_bot[iwell,]]
#         nscreen = length(screen.list)
#         for (i in 1:nscreen) {
#           cat('OBSERVATION\n')
#           cat(paste0('  REGION ', iwell, '_', i), '\n')
#           cat('  VELOCITY \n')
# #           cat('  AT_COORDINATE\n') # interpolate to screen interval instead of cell center; Currently NOT SUPPORTED in ugrid!
#           cat('/\n')
#           cat('\n')
#         }
#     }
    if (ugrid) {
    
        for (iwell in well.list) {
            if (screen_top[iwell, ] >= point_dem[iwell] - aqui_thk & screen_bot[iwell, ] <= point_dem[iwell] & round(screen_top[iwell,] - screen_bot[iwell, ]) >= min_z) {

                screen_length = screen_top[iwell, ] - screen_bot[iwell, ]
                screen.list = screen_top[iwell, ] - seq(1, screen_length, 2) # set screen interval every 2 m 
                screen.list = screen.list[screen.list > point_dem[iwell] - aqui_thk + 5] # add 1 to ensure the screen does not fall out of the model bottom
                nscreen = length(screen.list)

                if (nscreen > 0) {
                    selected.wells = c(selected.wells, iwell)

                     for (i in 1:nscreen) {
                          cat('OBSERVATION\n')
                          cat(paste0('  REGION ', iwell, '_', i), '\n')
                          cat('  VELOCITY \n')
                #           cat('  AT_COORDINATE\n') # interpolate to screen interval instead of cell center; Currently NOT SUPPORTED in ugrid!
                          cat('/\n')
                          cat('\n')
                     }
                }

            }
        }
    } else {
        
        for (iwell in well.list) {

          if (screen_top[iwell, ] >= z0 & screen_bot[iwell, ] <= z0 + zlen & round(screen_top[iwell,] - screen_bot[iwell, ]) >= idz) {
            ind = which((z >= round(screen_bot[iwell, ], 3)) & (z <= round(screen_top[iwell,], 3)))
            iscreen = z[ind]
            nscreen = length(iscreen)
              
            selected.wells = c(selected.wells, iwell)
              
            for (j in 1:nscreen) {

              cat('OBSERVATION\n')
              cat(paste0('  REGION ', iwell, '_', j), '\n')
              cat('  VELOCITY \n')
    #           cat('  AT_COORDINATE\n') # interpolate to screen interval instead of cell center; Currently NOT SUPPORTED in ugrid!
              cat('/\n')
              cat('\n')

            }
          }
        }
        
    }
    
#     if (ugrid) {
#         for (iwell in AT.list) {

#             if (screen_top[iwell, ] <= point_dem[iwell] - 0.25) {

#               cat('OBSERVATION\n')
#               cat(paste0('  REGION ', iwell), '\n')
#               cat('  VELOCITY \n')
#               cat('/\n')
#               cat('\n')
#           }

#        }
#     } else {
#         for (iwell in AT.list) {

#           cat('OBSERVATION\n')
#           cat(paste0('  REGION ', iwell), '\n')
#           cat('  VELOCITY \n')
#           cat('/\n')
#           cat('\n')
          

#        }
#     }
    
    
    
}


# ## end of file

# In[58]:


cat("#==================END=========================\n")
cat("END_SUBSURFACE")


# In[59]:


close(f)


# In[60]:


print(paste0("model inputdeck saved in: ", fname_pflotran.in))


# In[ ]:




