#!/usr/bin/env python
# coding: utf-8

# # Convert Exodus mesh to PFLOTRAN mesh

# In[13]:


from netCDF4 import Dataset 
from ncdump import ncdump
# import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import cm
# from mpl_toolkits.basemap import Basemap, addcyclic, shiftgrid
from mpl_toolkits.mplot3d import Axes3D

import h5py as h5
import os
import numpy as np
import pandas as pd
import pickle

from exodus2pflotran import exodus_to_pflotran_mesh


# In[14]:


import rasterio
import tqdm
import seaborn as sns

from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
import shapefile


# In[15]:


from fav_colors import fav_colors


# In[16]:


get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150


# In[17]:


def print_structure(name, obj):
    '''
    view the tree structure of hdf5 file
    
    Usage:input_h5.visititems(print_structure)
    '''
    
    print(name)


# In[18]:


os.chdir('./mesh/')
print("Current Working Directory " , os.getcwd())


# In[19]:


fname_exo_mesh = 'Thorne-mesh_v2.exo'
fname_pfotran_mesh = 'Thorne-mesh_v2.h5'
fname_out_h5 = 'Thorne-mesh_layerID.h5'

data_dir = '../data/'
# fname_dem = data_dir + 'columbia_subbasin_DEM.asc'
fname_dem = data_dir + 'DEM/DEM_thorne_v2.tif'
fname_hanford_basal = data_dir + 'DEM/hanford_basal.asc'
fname_ringolde_basal = data_dir + 'DEM/ringolde_basal.asc'
fname_basalt_basal = data_dir + 'DEM/basalt_basal.asc'
fname_ringoldlm_basal = data_dir + 'DEM/ringoldlm_basal.asc'
fname_ringolda_basal = data_dir + 'DEM/ringolda_basal.asc'
fname_coldcreek_basal = data_dir + 'DEM/coldcreek_basal.asc'
fname_taylorflats_basal = data_dir + 'DEM/taylorflats_basal.asc'

fname_river_shp = data_dir + 'shapefile/river_geometry_watershed.shp'


# ## view exodus file

# In[8]:


exofile=Dataset(fname_exo_mesh)


# In[9]:


ncdump(exofile)


# ## Convert Exodus file to PFLOTRAN mesh

# In[10]:


exodus_to_pflotran_mesh(fname_exo_mesh, fname_pfotran_mesh)


# ## Rewrite hdf5 file structure

# In[11]:


input_h5 = h5.File(fname_pfotran_mesh, "r")


# In[12]:


input_h5.visititems(print_structure)


# In[13]:


if os.path.exists(fname_out_h5):
    os.remove(fname_out_h5)
output_h5 = h5.File(fname_out_h5, "w")


# ### Duplicate hdf5 file

# In[14]:


groups = list(input_h5.keys())
for i_group in groups:
    print(i_group)
    group_id = output_h5.require_group(i_group)
    datasets = list(input_h5[i_group].keys())
    for i_dataset in datasets:
        print(i_dataset)
        input_h5.copy("/" + i_group + "/" + i_dataset,
                      group_id, name=i_dataset)


# ### create new groups

# In[15]:


output_h5.create_group("Regions/All")

output_h5.create_group("Regions/Top")
output_h5.create_group("Regions/Bottom")
output_h5.create_group("Regions/Sides")


# In[16]:


dset_Cells = input_h5['Materials/Cell Ids']
dset_IDs = input_h5['Materials/Material Ids']

dset_ss1 = input_h5['Regions/Sideset1']
dset_ss2 = input_h5['Regions/Sideset2']
dset_ss3 = input_h5['Regions/Sideset3']


# ### create new datasets

# In[17]:


output_h5.create_dataset("Regions/All/Cell Ids", data=dset_Cells)

output_h5.create_dataset("Regions/Top/Vertex Ids", data=dset_ss1)
output_h5.create_dataset("Regions/Bottom/Vertex Ids", data=dset_ss2)
output_h5.create_dataset("Regions/Sides/Vertex Ids", data=dset_ss3)


# **create `Layer Ids` dataset**

# In[18]:


output_h5.create_dataset("Materials/Layer Ids", data=dset_IDs)


# ### Rename a dataset

# In[18]:


# output_h5['Regions'].move('Sideset1', 'Top')
# output_h5['Regions'].move('Sideset2', 'Bottom')
# output_h5['Regions'].move('Sideset3', 'Sides')


# ### delete a dataset

# In[19]:


del output_h5['Regions/Sideset1']
del output_h5['Regions/Sideset2']
del output_h5['Regions/Sideset3']


# In[20]:


output_h5.visititems(print_structure)


# In[21]:


input_h5.close()
output_h5.close()


# # Generate material ids

# ## get vertices, cell ids, and layer ids

# In[21]:


input_h5 = h5.File(fname_out_h5, "r")


# In[22]:


input_h5.visititems(print_structure)


# In[23]:


vert_coord = np.array(input_h5['Domain/Vertices'][:])


# In[24]:


vert_coord[:5]


# In[25]:


cell_vert = np.array(input_h5['Domain/Cells'][:])


# In[26]:


cell_vert[:5]


# In[27]:


layer_ids = np.array(input_h5['Materials/Layer Ids'][:])


# In[29]:


np.unique(layer_ids)


# ## plot single cell (optional)

# In[71]:


i = 0
ivert_id = cell_vert[i, 1:] # vertice id is 1-based
ivert_coord = vert_coord[ivert_id -1, :]    
ivert_coord


# In[72]:


fig = plt.figure(figsize=(8,6))
ax = Axes3D(fig)

for i in np.arange(6):
    ax.scatter(ivert_coord[i, 0], ivert_coord[i, 1],
               ivert_coord[i, 2],
               c='b', marker='o')
    ax.text(ivert_coord[i, 0], ivert_coord[i, 1],
               ivert_coord[i, 2],  '%s' % (str(i + 1)), size=20, zorder=1,  
    color='k') 
    
ax.scatter(ivert_coord[:, 0].mean(), ivert_coord[:, 1].mean(), ivert_coord[:, 2].mean() ,
          c = 'r', marker = '*')

ax.plot_trisurf(ivert_coord[:3, 0], ivert_coord[:3, 1],
               ivert_coord[:3, 2], cmap=cm.Set1, linewidth=1)

ax.plot_trisurf(ivert_coord[3:, 0], ivert_coord[3:, 1],
               ivert_coord[3:, 2], cmap=cm.Set2, linewidth=1, alpha = 0.5)
# fig.colorbar(surf)


# ## get centroid for all cells

# In[30]:


centr = []
for i in np.arange(cell_vert.shape[0])[:]:

    ivert_id = cell_vert[i, 1:] # vertice id is 1-based
    ivert_coord = vert_coord[ivert_id-1, :]  
    
    icentr = ivert_coord[:, 0].mean(), ivert_coord[:, 1].mean(), ivert_coord[:, 2].mean()
    centr.append(icentr)

centr = np.asarray(centr)


# In[31]:


with open("../results/centroid-layerID.p", 'wb') as f:
    pickle.dump(centr, f, protocol=-1)


# ### sample dem elevation for each cell

# In[155]:


with open("../results/centroid-layerID.p", 'rb') as f:
    centr = pickle.load(f)


# In[32]:


centr_xy = centr[:, 0:2]


# In[13]:


# centr_xy_unq = np.vstack({tuple(row) for row in centr_xy})


# Sample point value at each cell center

# In[39]:


centr_df = pd.DataFrame(centr, columns= ['x', 'y', 'z'])


# In[41]:


with rasterio.open(fname_dem) as ras:
    ele_dem = [i[0] for i in ras.sample(centr_xy[:])]

with rasterio.open(fname_coldcreek_basal) as ras:
    ele_cc = [i[0] for i in ras.sample(centr_xy[:])]
with rasterio.open(fname_taylorflats_basal) as ras:
    ele_tf = [i[0] for i in ras.sample(centr_xy[:])]
with rasterio.open(fname_ringolde_basal) as ras:
    ele_re = [i[0] for i in ras.sample(centr_xy[:])]    
with rasterio.open(fname_ringoldlm_basal) as ras:
    ele_rlm = [i[0] for i in ras.sample(centr_xy[:])]
with rasterio.open(fname_ringolda_basal) as ras:
    ele_ra = [i[0] for i in ras.sample(centr_xy[:])]
with rasterio.open(fname_basalt_basal) as ras:
    ele_ba = [i[0] for i in ras.sample(centr_xy[:])]


# In[42]:


centr_df['dem'] = ele_dem
centr_df['cc'] = ele_cc
centr_df['tf'] = ele_tf
centr_df['re'] = ele_re
centr_df['rlm'] = ele_rlm
centr_df['ra'] = ele_ra
centr_df['ba'] = ele_ba


# In[46]:


centr_df['layer_ids'] = layer_ids


# In[47]:


with open("../results/Thorne_model_centroid_df.p", 'wb') as f:
    pickle.dump(centr_df, f, protocol=-1)


# ### assign material id

# **assign material id based on its relative elevation to cell coords**
# 
# material|id
# ---|---
# hf|1
# cold creek|2
# taylor flats|3
# ringolde|4
# ringoldlm|5
# ringolda|6
# basalt|9
# alluvium|10
# 
# 
# Note, the stratigraphy follows the order Hanford >-- ColdCreek > taylor flats > ringolde > ringold lm > ringold a > basalt

# In[207]:


# mat_ids = [1 if centr_df.loc[i, "z"] > centr_df.loc[i, "hr_elev"] 
#  else 4 for i in np.arange(centr_df.shape[0]) ]


# In[67]:


material_list = {'dem':1, 'cc':2, 'tf':3, 're':4, 'rlm':5, 'ra':6, 'ba':9}


# In[178]:


mat_ids = []
for i in np.arange(centr_df.shape[0])[:]:
    row =centr_df.iloc[i, :]
    lst = row.z - row.iloc[3:-1] 

    if all(lst > 0): 
        # if z above all layers, assign hf=1
        mat = 1
    elif not any(lst >0): 
        # if z below all layers, assign ba=9
        mat = 9
    else:
        # if z in between layers, assign material id of the layer immediately above z
        mat = material_list[lst[lst <0].index[-1]]    
    mat_ids.append(mat)


# In[182]:


centr_df['mat_ids'] = mat_ids


# In[183]:


with open("../results/centr_df_matID.p", 'wb') as f:
    pickle.dump(centr_df, f, protocol=-1)


# **assign alluvium layer**

# In[20]:


with open("../results/centr_df_matID_alluvium.p", 'rb') as f:
    centr_df = pickle.load(f)


# In[194]:


river_shp = shapefile.Reader(fname_river_shp) 
river_shp = river_shp.shapes() 
# river_poly = [shape.points for shape in river_shp]
river_poly = river_shp[0].points


# In[195]:


river_idx = [Polygon(river_poly).contains(Point(centr_df.loc[i, 'x'], centr_df.loc[i, 'y'])) 
             for i in centr_df.index]


# In[196]:


centr_df['river_idx'] = river_idx


# In[197]:


# assign alluvium to the top 2 layers within river channel
# centr_df.loc[(centr_df['layer_ids'] <= 102) & (centr_df['mat_ids'] == 1) & 
#              (centr_df['river_idx'] == True), 'mat_ids'] = 5

centr_df.loc[(centr_df['layer_ids'] <= 2) & 
             (centr_df['river_idx'] == True), 'mat_ids'] = 10


# In[44]:


ilayer = centr_df[centr_df['layer_ids'] == 30]

sns.scatterplot(x = 'x', y = 'y', hue = 'mat_ids', 
                marker = '.', s=1,
                palette=sns.color_palette(fav_colors('CB_color_cycle'), len(ilayer.mat_ids.unique())),
                edgecolor=None,
               data=ilayer, )


# In[200]:


with open("../results/centr_df_matID_alluvium.p", 'wb') as f:
    pickle.dump(centr_df, f, protocol=-1)


# **assign material ids based on layer id (optional)**
# 
# - Layer #1 is located on top and follow the sequence 1, 2, 3, ...; 
# 
# - Without knowing its layerID, select the cells based on their relative location in the cell index. i.e., `1 : ele_per_layer` belongs to layer 1.

# In[116]:


# layers = [101, 102] # top 2 layers
# add alluvium id --5 to the two top layers while the cell id is Hf -- 1
centr_df.loc[(centr_df['layer_ids'] <= 102) & (centr_df['mat_ids'] == 1), 'mat_ids'] = 5


# In[215]:


with open("../results/centroid_df_matID.p", 'wb') as f:
    pickle.dump(centr_df, f, protocol=-1)


# In[216]:


input_h5.close()


# ### write material id to hdf5 file

# In[139]:


with open("../results/centroid_df_layerID.p", 'rb') as f:
    centr_df = pickle.load(f)


# In[224]:


in_h5 = h5.File(fname_out_h5, "r")


# In[225]:


out_h5 = h5.File("Thorne-mesh-matID.h5", 'w')


# In[226]:


groups = list(in_h5.keys())
for i_group in groups:
    print(i_group)
    group_id = out_h5.require_group(i_group)
    datasets = list(in_h5[i_group].keys())
    for i_dataset in datasets:
        print(i_dataset)
        in_h5.copy("/" + i_group + "/" + i_dataset,
                      group_id, name=i_dataset)


# **read in material ids**

# In[227]:


data = out_h5['Materials/Material Ids']       # load the data
data[...] = centr_df['mat_ids'].values


# In[228]:


np.allclose(np.array(data), centr_df.mat_ids) # check if the new mat_ids has been read in.


# In[229]:


# del out_h5['Materials/Layer Ids']


# In[229]:


in_h5.close()
out_h5.close()

