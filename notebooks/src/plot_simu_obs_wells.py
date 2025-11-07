#!/usr/bin/env python
# coding: utf-8

# # Plot simu vs. obs well data

# In[43]:


get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150


# In[2]:


# %matplotlib notebook
# import glob, datetime, ipdb, pickle, pyproj, json, mplleaflet, geopandas, fiona, sys, cartopy, \
#          math, folium, base64
import glob, pickle
import numpy as np
import h5py as h5
import math
import pyproj

import matplotlib 
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
# plt.style.use('seaborn-notebook')
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates

import pandas as pd
import ipywidgets as ipyw
# import cartopy.crs as ccrs
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
# import datetime
from datetime import timedelta, datetime
from scipy import interpolate
# from ipyleaflet import *
# from geojson import Feature, FeatureCollection, Point
from geopandas import GeoDataFrame
# from shapely.geometry import Point
from natsort import natsorted, ns, natsort_keygen
from sklearn.metrics import  mean_squared_error
# from folium.plugins import FloatImage
# from folium import IFrame

import re

# from tqdm import tqdm_notebook
from tqdm.notebook import tqdm

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from myfunc import insertNA, printname, batch_delta_to_time, get_rmse

from fav_colors import fav_colors

from collections import Counter
import seaborn as sns


# ## I/O files and parameters

# In[3]:


#=======================input==========================
# case_name = "AT-ugrid/TH-hete-bc/"
case_name = "mesh-100m/"
model_dir = "/global/cscratch1/sd/pshuai/HFR-thorne/" + case_name

# fig_dir = "/global/project/projectdirs/pflotran/pin/AT-model/outputs/AT-20x10m/BTC/"

# # fname_model_origin = model_dir + "model_origin.txt"
# fname_material_h5 = model_dir + "AT_material_river.h5"

# fname_pflotran_h5 = model_dir + "AT-model-noAlluvium.h5"

# fname_300A_h5 = "/Users/shua784/Paraview/300A/John_case_optim_5/pflotran_bigplume-004.h5"

fname_tec_files = model_dir + "HFR-model-obs-*.tec"
# fname_tec_files = model_dir + "AT-model-spinup-obs-*.tec"
fname_selected_wells = model_dir + "selected_well.txt"

data_dir = "/global/project/projectdirs/m1800/pin/AT-model/data/"
fname_well_data = data_dir + "300A_wells_2008-2019.csv"
fname_WellScreen = data_dir + "HEIS_300A_AT_well_screen.csv"
fname_optio2_data = data_dir + "chemistry/Processed_optio2_data_last10m_%O2.csv"

out_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/outputs/" + case_name
fname_simu_obs_head = out_dir + "simu_obs_head/"
fname_tracer_spc = out_dir + "tracer_spc/"
fname_head_tracer_spc = out_dir + "head_tracer_spc/"
fname_head_tracer_spc_temp = out_dir + "head_tracer_spc_temp/"
fname_simu_obs_temp = out_dir + "simu_obs_temp/"

fname_simu_obs_chem = out_dir + "simu_obs_chem/"

results_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/results/" + case_name

fname_river_stage_plot = "/global/project/projectdirs/m1800/pin/AT-model/outputs/AT-ugrid/river_stage/"
fname_river_temp_stage_plot = "/global/project/projectdirs/m1800/pin/AT-model/outputs/AT-ugrid/river_temp_stage/"

input_dir = "/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/"
fname_river_stage = input_dir + 'river_bc/stage_2007-2019/DatumH_River_321.txt'
fname_river_temp = input_dir + 'river_bc/Temp_River_321.txt'
## riverbed temp
HFR_data_dir = "/global/project/projectdirs/m1800/pin/HFR-thermal/data/"
fname_RG3_T = HFR_data_dir + "riverbed_temp_data/RG3_T3/300_Area_RG3_T3_Temps_20180502.csv"
fname_RG3_T_dat = HFR_data_dir + "riverbed_temp_data/RG3_T3/RG3_T3_Temps.dat"
fname_DA_T = HFR_data_dir + "riverbed_temp_data/DenseArray/DA1_CRiver_TM_T.csv"
fname_100H_dir = HFR_data_dir + "riverbed_temp_data/100H_thermistor_rods/"
iButton_dir = HFR_data_dir + 'riverbed_temp_data/iButton/'


# In[4]:


date_origin = datetime.strptime("2007-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
# model_origin = [594462.6688, 116280.5661] 


# In[5]:


P_atm = 101325
rho = 997.16
g_const = 9.81


# ## import well data

# In[6]:


# obs_data_df = pd.read_csv(fname_well_data, parse_dates=["DateTime"])
obs_data_df = pd.read_csv(fname_well_data)
# obs_data_df['DateTime'] = pd.to_datetime(obs_data_df['DateTime'],format='%m/%d/%y %H:%M:%S')
obs_data_df['DateTime'] = pd.to_datetime(obs_data_df['DateTime'],format='%Y-%m-%d %H:%M:%S')


# In[7]:


obs_well_list = obs_data_df['WellName'].unique()
obs_well_list = ['Well_' + i for i in obs_well_list]


# ### import river stage & temp

# In[8]:


# downstream location MASS1-321
river_stage = pd.read_csv(fname_river_stage, header = None, sep = " ", 
                          names= ['dt', 'Easting', 'Northing', 'wl'])
river_stage['datetime'] = [date_origin + timedelta(seconds = i) for i in river_stage['dt'].values]
river_stage.set_index('datetime', drop = False, inplace = True)


# In[11]:


# river_temp = pd.read_csv(fname_river_temp, header = None, sep = " ", 
#                           names= ['dt', 'temp'])
# river_temp['datetime'] = [date_origin + timedelta(seconds = i) for i in river_temp['dt'].values]
# river_temp.set_index('datetime', drop = False, inplace = True)


# ### import well screen

# In[9]:


well_screen = pd.read_csv(fname_WellScreen)


# ## export simulated head using .TEC observation files

# We will import well observation from .tec outputs.

# In[11]:


# with open(results_dir + "well_data_df.p", 'rb') as f:
#     well_data_df = pickle.load(f)

# with open(results_dir + "obs_pts_df.p", 'rb') as f:
#     obs_pts_df = pickle.load(f)

# with open(results_dir + "selected_obs_wells.p", 'rb') as f:
#     selected_obs_wells = pickle.load(f)


# In[10]:


simu_well_list = pd.read_csv(fname_selected_wells,  header=None, names=['WellName'])
simu_well_list = simu_well_list['WellName'].values.tolist()


# In[13]:


# simu_time = np.array([date_origin + timedelta(hours=i) for i in well_data_df.index])


# ### assemble all output data file

# In[39]:


with open(results_dir + "well_data_df-300A.p", 'rb') as f:
    simu_time, well_data_df = pickle.load(f)


# In[ ]:


with open(results_dir + "obs_pts_df.p", 'rb') as f:
    obs_pts_df = pickle.load(f)


# In[27]:


with open(results_dir + 'simu_data_df.p', "rb") as f:
    simu_data_df = pickle.load(f)


# In[11]:


tec_files = glob.glob(fname_tec_files)
tec_files = natsorted(tec_files)


# This may take a while...

# In[12]:


simu_data_df = pd.DataFrame()

for ifile in tqdm(tec_files[:]):   
#     ifile = '/global/cscratch1/sd/pshuai/TH-100x100x2-thermal/TH_100x100x2_thermal-obs-1238.tec'
#     print(ifile)
    idf_header_row = pd.read_table(ifile, sep=',',header=None, nrows=1, engine='python')
    iheader = list(np.asarray(idf_header_row.values).flatten())
    idf = pd.read_table(ifile, sep='\s+',header=None, names=iheader, index_col=0, skiprows=1, engine='python')
    
    simu_data_df = pd.concat([simu_data_df, idf], axis=1, join='outer')


# In[15]:


# with open(results_dir + 'simu_data_df.p', "wb") as f:
#     pickle.dump(simu_data_df, f, protocol = -1)


# In[13]:


simu_time = np.array([date_origin + timedelta(hours=i) for i in simu_data_df.index])


# **import well list**

# In[15]:


selected_obs_wells = list(set(obs_well_list).intersection(simu_well_list))


# In[21]:


# obs_var_names=['Liquid Pressure [Pa]', 'Temperature [C]', 'Total Tracer_river [M]', 'qlx [m/h]', 'qly [m/h]']
# obs_var_names=['Liquid Pressure [Pa]', 'Total Tracer_river [M]', 'qlx [m/h]', 'qly [m/h]']


# **careful: double check to see if there is any ambiguity in the var names**
# 
# e.g., O2 laps with NO2 and CO2 when searching based on string `O2`

# In[16]:


obs_var_names=['Liquid Pressure [Pa]', 'Total Tracer_river [M]', 
               'qlx [m/h]', 'qly [m/h]']


# ### create dataframe to store obs.well point coordinates

# In[17]:


obs_point_name = []
obs_point_coordx = []
obs_point_coordy = []
obs_point_coordz = []
for iwell in simu_well_list:
    iobs = 'Liquid Pressure'
    
#     iwell_id = [iwell + '_' if '399' in iwell else iwell][0]
    
    iwell_id = iwell + '_'
    # search for columns contain both iwell_id and iobs
    iwell_col_ind = [icol for icol in simu_data_df.columns if iwell_id in icol and icol.startswith(iobs)]
    
    # find obs coord
    for icol in iwell_col_ind:
        istr = re.split("\s", icol) # split by space. e.g., 'Liquid Pressure', '[Pa]', 'Well_399-2-1_1', '(241534)', '(5.9447E+05', '1.1612E+05', '109.4)'
        obs_point_name.append(istr[3])  # 
        obs_point_coordx.append(float(istr[5].replace('(', '')))
        obs_point_coordy.append(float(istr[6]))
        obs_point_coordz.append(float(istr[7].replace(')', '')))    
# create a dataframe

arrays = np.vstack((np.array(obs_point_name), np.array(obs_point_coordx), np.array(obs_point_coordy), np.array(obs_point_coordz))).T

obs_pts_df = pd.DataFrame(arrays, index=arrays[:,0], columns=['obs_point', 'coord_x', 'coord_y', 'coord_z'])

obs_pts_df["coord_x"] = pd.to_numeric(obs_pts_df["coord_x"])
obs_pts_df["coord_y"] = pd.to_numeric(obs_pts_df["coord_y"])
obs_pts_df["coord_z"] = pd.to_numeric(obs_pts_df["coord_z"])

obs_pts_df = obs_pts_df.loc[~obs_pts_df.index.duplicated(keep='first')]


# ### **create multiindex for dataframe**
# 
# column has three levels: well_name, variable_name, well_screen_name
# 
# Note: be careful that some well screen order may be reversed. Check `iwell_screen_array` to make sure it aligns with the order in `iwell_col_ind`.

# In[18]:


well_list_300A = [i for i in simu_well_list if '399' in i ]


# In[19]:


well_list = well_list_300A


# In[34]:


# iwell_name = 'Well_399-1-7'


# In[20]:


well_array = []
var_array = []
well_screen_array = []

well_cols = []

for iwell in tqdm(well_list[:]):
#     iwell = iwell_name
    for iobs in obs_var_names[:]:
#         iobs = 'O2 Rate [mol/m^3-sec]'
        
#         iwell_id = [iwell + '_' if '399' in iwell else iwell][0]
        iwell_id = iwell + '_'
        # search for columns contain both iwell_id and iobs, double check if there is any ambiguity
        iwell_col_ind = [icol for icol in simu_data_df.columns if iwell_id in icol and icol.startswith(iobs)]                 
        
        # find well screens 
        iwell_screen_array = [re.search('Well(.+?)\ ', i).group(0)[:-1] for i in iwell_col_ind]
        iwell_array = [iwell]*len(iwell_col_ind)
        ivar_array = [iobs]*len(iwell_col_ind)
        
        var_array += ivar_array
        well_array += iwell_array 
        well_screen_array += iwell_screen_array
        
        well_cols += iwell_col_ind
        
        # see if there is duplicates
        dup_list = [item for item, count in Counter(well_cols).items() if count > 1]
        if len(dup_list) > 0:
            raise Exception('Duplicates:{} found in list!'.format(dup_list))


# In[21]:


arrays = [np.array(well_array), np.array(var_array), np.array(well_screen_array)]
index_col = pd.MultiIndex.from_arrays(arrays, names=('WellName', 'VariableName', 'WellInterval'))
well_data_df = pd.DataFrame(index=simu_data_df.index, columns=index_col)


# This may take a long time to finish..

# In[22]:


for iwell in tqdm(well_list[:]):
#     print(iwell)
#     iwell = iwell_name
    for iobs in obs_var_names:
#         iwell_id = [iwell + '_' if '399' in iwell else iwell][0]
        iwell_id = iwell + '_'
        # search for columns contain both iwell_id and iobs
        iwell_col_ind = [icol for icol in simu_data_df.columns if iwell_id in icol and icol.startswith(iobs)] 
        iwell_screen_array = [re.search('Well(.+?)\ ', i).group(0)[:-1] for i in iwell_col_ind]
        for i in np.arange(len(iwell_col_ind))[:]:
            well_data_df[iwell, iobs, iwell_screen_array[i]] = simu_data_df[iwell_col_ind[i]].values

well_data_df = well_data_df.sort_index(axis=1)


# In[23]:


with open(results_dir + "well_data_df-300A.p", 'wb') as f:
    pickle.dump((simu_time, well_data_df), f, protocol=-1)


# In[47]:


with open(results_dir + "obs_pts_df.p", 'wb') as f:
    pickle.dump(obs_pts_df, f, protocol=-1)


# In[26]:


with open(results_dir + "selected_obs_wells.p", 'wb') as f:
    pickle.dump(selected_obs_wells, f, protocol=-1)


# ### calculate flux averaged tracer conc. & temperature

# In[24]:


for iwell in tqdm(well_list[:]):
#     iwell = iwell_name
#     print(iwell)
    obs_vec_df = np.sqrt(well_data_df[iwell, 'qlx [m/h]']**2 + well_data_df[iwell, 'qly [m/h]']**2)
    well_data_df[iwell,'Total Tracer_river [M]', 'flux_ave_tracer'] = (well_data_df[iwell, 'Total Tracer_river [M]'] * 
                                                                 obs_vec_df).sum(axis = 1) / obs_vec_df.sum(axis = 1)
# # average temp
#     well_data_df[iwell, 'Temperature [C]', 'flux_ave_temp'] = (well_data_df[iwell, 'Temperature [C]'] * 
#                                                                  obs_vec_df).sum(axis = 1) / obs_vec_df.sum(axis = 1)


# ## plot river stage

# In[16]:


# for itime in tqdm(river_stage.index[::120]):

fig, ax = plt.subplots(1,1, figsize=(8,4))

river_stage.plot(y='wl', color = 'blue', ax=ax, lw=0.5, zorder=1)

#     ax.scatter(river_stage.loc[itime, 'datetime'], river_stage.loc[itime, 'wl'], 
#                     facecolors = 'red', edgecolors= 'black', s = 30, alpha = 1,zorder=2)

ax.set_ylabel('River stage (m)', fontsize = 14)
ax.set_xlabel('')
ax.set_title('River stage', fontsize=16)
ax.get_legend().remove()
# ax.set_xlim(['01/01/2017','01/01/2019']) 

#     fig.savefig(fname_river_stage_plot + str(itime) + '.png', dpi=300)
#     plt.close(fig)


# ## plot simu vs obs head

# ### convert pressure to head

# In[40]:


iwell_name = 'Well_399-2-2'
iwell = iwell_name
isimu_head = well_data_df[iwell, 'Liquid Pressure [Pa]'].copy()
isimu_head = (isimu_head - P_atm) / rho / g_const


# In[41]:


isimu_head.dropna(axis = 1, inplace = True)

for i in isimu_head.columns:
    isimu_head.loc[:, i] = isimu_head.loc[:, i] + obs_pts_df.loc[i, 'coord_z']

simu_time = np.array([date_origin + timedelta(hours=i) for i in isimu_head.index])

isimu_head['DateTime'] = simu_time
isimu_head.set_index('DateTime', inplace=True)


# In[42]:


# iwell = "399-2-3"
iobs_head =  obs_data_df[obs_data_df['WellName'] == iwell.replace('Well_', '')].sort_values(by = ['DateTime'])
iobs_head = iobs_head[iobs_head['DateTime'].notnull()]
iobs_head.set_index('DateTime', drop = False, inplace = True)


# In[43]:


fig, ax = plt.subplots(1,1, figsize=(8,6))

ax.plot(isimu_head.index, isimu_head.iloc[:, -1])
ax.plot(iobs_head.index,iobs_head.loc[:, 'WL'])
# ax.set_xlim(['01/01/2017', '03/31/2017'])
ax.legend(['simu_head', 'obs_head'])
ax.set_title(iwell)
ax.set_ylabel('Water table (m)')
# ax.set_xlim(['01/01/2018','01/01/2019'])


# In[43]:


# homo-k_al_4.6 case


# In[49]:





# ### Batch plot

# In[42]:


for iwell in tqdm(selected_obs_wells[:1]):
    iwell = 'Well_399-1-7'
    isimu_head = well_data_df[iwell, 'Liquid Pressure [Pa]'].copy()
    isimu_head = (isimu_head - P_atm) / rho / g_const
    isimu_head.dropna(axis = 1, inplace = True)

    for i in isimu_head.columns:
        isimu_head.loc[:, i] = isimu_head.loc[:, i] + obs_pts_df.loc[i, 'coord_z']

    simu_time = np.array([date_origin + timedelta(hours=i) for i in isimu_head.index])

    isimu_head['DateTime'] = simu_time
    isimu_head.set_index('DateTime', inplace=True)

    iobs_head =  obs_data_df[obs_data_df['WellName'] == iwell.replace('Well_', '')].sort_values(by = ['DateTime'])
    iobs_head = iobs_head[iobs_head['DateTime'].notnull()]
    iobs_head.set_index('DateTime', drop = False, inplace = True)
    
    start_window = '01/01/2011'
    end_window = '01/01/2016'

    rmse = get_rmse(iobs_head.loc[start_window:end_window, 'WL'], isimu_head.loc[start_window:end_window, :].iloc[:, -1])
    
    fig, ax = plt.subplots(1,1, figsize=(8,5))

    ax.plot(isimu_head.index, isimu_head.iloc[:, -1], 'r', lw = 0.5)
    ax.plot(iobs_head.index,iobs_head.loc[:, 'WL'], 'k', lw = 0.5)
    ax.set_xlim(start_window, end_window)
    ax.set_ylim([104, 109])
    ax.legend(['simu_head', 'obs_head'])
    ax.set_title(iwell)
    ax.set_ylabel('Water table (m)')
    
    ax.text(0.05, 0.9, "RMSE: {:.2f}".format(rmse), transform=ax.transAxes)

#     fig.savefig(fname_simu_obs_head + iwell + '.png', dpi=300)
#     plt.close(fig)


# In[37]:


# mesh-100m case


# ## plot simu tracer vs. obs SpC

# In[51]:


for iwell in selected_obs_wells[:1]:
    iwell = 'Well_399-2-32'
    isimu_df = well_data_df[iwell,'Total Tracer_river [M]', 'flux_ave_tracer'].copy()
#     isimu_head = (isimu_head - P_atm) / rho / g_const
#     isimu_head.dropna(axis = 1, inplace = True)

#     for i in isimu_df.columns:
#         isimu_head.loc[:, i] = isimu_head.loc[:, i] + obs_pts_df.loc[i, 'coord_z']

    simu_time = np.array([date_origin + timedelta(hours=i) for i in isimu_df.index])

#     isimu_df['DateTime'] = simu_time
#     isimu_df.set_index('DateTime', inplace=True)
#     isimu_df.set_index(simu_time)

    iobs_df =  obs_data_df[obs_data_df['WellName'] == iwell.replace('Well_', '')].sort_values(by = ['DateTime'])
    iobs_df = iobs_df[iobs_df['DateTime'].notnull()]
    iobs_df.set_index('DateTime', drop = False, inplace = True)

    fig, ax = plt.subplots(1,1, figsize=(8,6))

    ax.plot(simu_time, isimu_df.values, 'r-')
    
    ax11 = ax.twinx()
    ax11.plot(iobs_df.index,iobs_df.loc[:, 'SpC'], 'k-')
    ax11.set_ylabel('SpC (ms/cm)')
    ax11.legend(['SpC'],loc=[0.31, 1.01], frameon = False)
    
    ax.set_xlim(['01/01/2017', '01/01/2019'])
    ax.set_ylim([0, 1])
    ax.legend(['river tracer'],loc=[0.01, 1.01], frameon = False)
    ax.set_title(iwell, fontsize = 16, pad = 30)
    ax.set_ylabel('River tracer (-)', color = 'r')
    ax.tick_params('y', colors='r')
    
#     fig.savefig(fname_tracer_spc + iwell + '.png', dpi=300)
#     plt.close(fig)


# In[125]:





# ## plot tracer, head, spc all in one

# In[44]:


for iwell in tqdm(selected_obs_wells[:1]):
    iwell = 'Well_399-1-7'
    isimu_head = well_data_df[iwell, 'Liquid Pressure [Pa]'].copy()
    isimu_head = (isimu_head - P_atm) / rho / g_const
    isimu_head.dropna(axis = 1, inplace = True)

    for i in isimu_head.columns:
        isimu_head.loc[:, i] = isimu_head.loc[:, i] + obs_pts_df.loc[i, 'coord_z']

    simu_time = np.array([date_origin + timedelta(hours=i) for i in isimu_head.index])

    isimu_head['DateTime'] = simu_time
    isimu_head.set_index('DateTime', inplace=True)

    iobs_head =  obs_data_df[obs_data_df['WellName'] == iwell.replace('Well_', '')].sort_values(by = ['DateTime'])
    iobs_head = iobs_head[iobs_head['DateTime'].notnull()]
    iobs_head.set_index('DateTime', drop = False, inplace = True)
    
    
    isimu_df = well_data_df[iwell,'Total Tracer_river [M]', 'flux_ave_tracer'].copy()
#     simu_time = np.array([date_origin + timedelta(hours=i) for i in isimu_df.index])

    iobs_df =  obs_data_df[obs_data_df['WellName'] == iwell.replace('Well_', '')].sort_values(by = ['DateTime'])
    iobs_df = iobs_df[iobs_df['DateTime'].notnull()]
    iobs_df.set_index('DateTime', drop = False, inplace = True)
    
    #------------plotting--------------#
    fig = plt.figure(figsize=(8, 6))
#     gs = gridspec.GridSpec(3, 1, height_ratios = [2, 0.5, 4])
    gs = gridspec.GridSpec(2, 1, height_ratios = [3, 4])
    gs.update(left=0.1,right=0.9,top=0.9, bottom=0.1, hspace = 0.2) # adjust vertical spacing b/w subplots

    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1], sharex = ax1)
#     ax3 = plt.subplot(gs[1])

    ax1.plot(isimu_head.index, isimu_head.iloc[:, -1])
    ax1.plot(iobs_head.index,iobs_head.loc[:, 'WL'], alpha=0.7)
#     ax1.set_xlim(['01/01/2017', '01/01/2018'])
    ax1.set_ylim([104, 109])
    ax1.legend(['simu_head', 'obs_head'])
#     ax1.set_title(iwell)
    ax1.set_ylabel('Water table (m)')
    
    ax1.set_title(iwell, fontsize = 16, pad = 5)
    
    ax2.plot(simu_time, isimu_df.values, 'r-')
    
    # add gw tracer
    gw_tracer = 1 - isimu_df.values
    ax2.plot(simu_time, gw_tracer, 'b--')
    
    ax21 = ax2.twinx()
    ax21.plot(iobs_df.index,iobs_df.loc[:, 'SpC'], 'k-')
    ax21.set_ylabel('SpC (ms/cm)')
    
    
#     ax2.set_xlim(['01/01/2007', '01/01/2008'])
    ax2.set_ylim([0, 1])
    ax2.legend(['River tracer', 'GW tracer'],loc=[0.01, 1.01], ncol = 2, frameon = False)
#     ax2.legend(['GW tracer'],loc=[0.31, 1.01], frameon = False)
    
    ax2.set_ylabel('Tracer (-)', color = 'k')
#     ax2.tick_params('y', colors='r')
    
    ax21.legend(['SpC'],loc=[0.51, 1.01], frameon = False)
    
    plt.setp(ax1.get_xticklabels(), visible=False)
    
#     fig.savefig(fname_head_tracer_spc + iwell + '.png', dpi=300)
#     plt.close(fig)
    
    
    


# In[38]:


# 150 m homo model

