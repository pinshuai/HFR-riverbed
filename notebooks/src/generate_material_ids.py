#!/usr/bin/env python
# coding: utf-8

# # Convert Exodus mesh to PFLOTRAN mesh

# In[1]:


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

import rasterio
# import tqdm
from tqdm.notebook import tqdm
import seaborn as sns

from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
import shapefile

from fav_colors import fav_colors
from myfunc import print_structure, closest_node

get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150


# In[2]:


os.chdir('./mesh/')
print("Current Working Directory " , os.getcwd())


# In[237]:


# fname_raw_exo = 'hanford_mesh_coarse.exo'
name = "Thorne_mesh_10m"
# fname_exo_mesh = 'hanford-mesh-10m-20pct-simplex.exo'
fname_exo_mesh = 'hanford-mesh-10m-2layer-simplex.exo'
fname_pfotran_mesh = '{}-cvrt.h5'.format(name)
fname_out_h5 = '{}-layerID.h5'.format(name)
fname_mesh_matID = '{}-matID.h5'.format(name)
fname_mesh_matID_river = '{}-matID-river.h5'.format(name)

data_dir = '../data/'
fname_dem = data_dir + 'DEM/topobathymetry_20200312_10m.tif'
# fname_dem = data_dir + 'DEM/DEM_thorne_v2.tif'
fname_hanford_basal = data_dir + 'DEM/hanford_basal.asc'
fname_ringolde_basal = data_dir + 'DEM/ringolde_basal.asc'
fname_basalt_basal = data_dir + 'DEM/basalt_basal.asc'
fname_ringoldlm_basal = data_dir + 'DEM/ringoldlm_basal.asc'
fname_ringolda_basal = data_dir + 'DEM/ringolda_basal.asc'
fname_coldcreek_basal = data_dir + 'DEM/coldcreek_basal.asc'
fname_taylorflats_basal = data_dir + 'DEM/taylorflats_basal.asc'

fname_river_shp = data_dir + 'shapefile/river_geometry_watershed.shp'
fname_mass1_coord = "/global/project/projectdirs/m1800/pin/HFR-thermal/data/MASS1/Mass1_datum_shift.csv"


# ## view exodus file

# In[17]:


exofile=Dataset(fname_exo_mesh)


# In[18]:


ncdump(exofile)


# ## Convert Exodus file to PFLOTRAN mesh

# In[19]:


exodus_to_pflotran_mesh(fname_exo_mesh, fname_pfotran_mesh)


# ## Rewrite hdf5 file structure

# ### Duplicate hdf5 file

# In[20]:


input_h5 = h5.File(fname_pfotran_mesh, "r")

input_h5.visititems(print_structure)


# In[21]:


if os.path.exists(fname_out_h5):
    os.remove(fname_out_h5)
output_h5 = h5.File(fname_out_h5, "w")


# In[22]:


groups = list(input_h5.keys())
for i_group in groups:
    print(i_group)
    group_id = output_h5.require_group(i_group)
    datasets = list(input_h5[i_group].keys())
    for i_dataset in datasets:
        print(i_dataset)
        input_h5.copy("/" + i_group + "/" + i_dataset,
                      group_id, name=i_dataset)


# ### write datasets

# - for basic sidesets: 1. Top, 2. Bottom , 3. Sides
# - for custom facesets: 1. Side land; 2. Side river; 3. Top river; 4. Top land; 5. Top; 6. Bottom; 7. Sides

# In[23]:


dset_Cells = input_h5['Materials/Cell Ids']
dset_IDs = input_h5['Materials/Material Ids']


# In[24]:


output_h5.create_group("Regions/All")
output_h5.create_dataset("Regions/All/Cell Ids", data=dset_Cells)


# **note: no space is allowed in group name in HDF5**

# In[25]:


# sidesets_name = {1: 'Top', 2: 'Bottom' , 3: 'Sides'} # the default sequence in exodus file for mesh exported from tinerator
sidesets_name = {1: 'Bottom', 2: 'Top' , 3: 'Sides'} # the default for mesh exported from watershed_workflow
# sidesets_name = {1: 'Side_land', 2: 'Side_river', 3: 'Top_river', 4: 'Top_land', 5: 'Top', 6: 'Bottom' , 7: 'Sides'}


# In[26]:


for key, value in sidesets_name.items():
    dset_ss = input_h5['Regions/Sideset' + str(key)]
    
    output_h5.create_group("Regions/{}".format(value))
    output_h5.create_dataset("Regions/{}/Vertex Ids".format(value), data=dset_ss)
    
    del output_h5['Regions/Sideset' + str(key)]


# **create `Layer Ids` dataset**

# In[27]:


output_h5.create_dataset("Materials/Layer Ids", data=dset_IDs)


# In[28]:


output_h5.visititems(print_structure)


# In[29]:


input_h5.close()
output_h5.close()


# # Generate material ids

# ## get vertices, cell ids, and layer ids

# In[30]:


input_h5 = h5.File(fname_out_h5, "r")

input_h5.visititems(print_structure)


# In[31]:


vert_coord = np.array(input_h5['Domain/Vertices'][:])


# In[32]:


vert_coord[:5]


# In[33]:


cell_vert = np.array(input_h5['Domain/Cells'][:])


# In[34]:


cell_vert[:5]


# In[35]:


layer_ids = np.array(input_h5['Materials/Layer Ids'][:])


# In[36]:


np.unique(layer_ids)


# ## plot single cell (optional)

# In[165]:


i = 100
ivert_id = cell_vert[i, 1:] # vertice id is 1-based
ivert_coord = vert_coord[ivert_id -1, :]    
ivert_coord


# In[167]:


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
               ivert_coord[:3, 2], cmap=cm.Set1, linewidth=1, alpha = 0.5)

ax.plot_trisurf(ivert_coord[3:, 0], ivert_coord[3:, 1],
               ivert_coord[3:, 2], cmap=cm.Set2, linewidth=1, alpha = 0.5)
# fig.colorbar(surf)


# scaling = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
# ax.auto_scale_xyz(scaling[0], scaling[1], [108.2, 108.8])


# ## get centroid for all cells

# In[37]:


centr = []
for i in np.arange(cell_vert.shape[0])[:]:

    ivert_id = cell_vert[i, 1:]
    # vertice id is 1-based
    ivert_coord = vert_coord[ivert_id-1, :]  
    
    icentr = ivert_coord[:, 0].mean(), ivert_coord[:, 1].mean(), ivert_coord[:, 2].mean()
    centr.append(icentr)

centr = np.asarray(centr)


# In[38]:


with open("../results/{}-centroid-layerID.p".format(name), 'wb') as f:
    pickle.dump(centr, f, protocol=-1)


# ### sample dem elevation for each cell

# In[155]:


with open("../results/centroid-layerID.p", 'rb') as f:
    centr = pickle.load(f)


# In[39]:


centr_xy = centr[:, 0:2]


# In[ ]:


# centr_xy_unq = np.vstack({tuple(row) for row in centr_xy})


# Sample point value at each cell center

# In[40]:


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


# In[ ]:


centr_df['dem'] = ele_dem
centr_df['cc'] = ele_cc
centr_df['tf'] = ele_tf
centr_df['re'] = ele_re
centr_df['rlm'] = ele_rlm
centr_df['ra'] = ele_ra
centr_df['ba'] = ele_ba


# In[ ]:


centr_df['layer_ids'] = layer_ids


# In[ ]:


with open("../results/{}-centroid_df.p".format(name), 'wb') as f:
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

# In[6]:


with open("../results/{}-centroid_df.p".format(name), 'rb') as f:
    centr_df = pickle.load(f)


# In[207]:


# mat_ids = [1 if centr_df.loc[i, "z"] > centr_df.loc[i, "hr_elev"] 
#  else 4 for i in np.arange(centr_df.shape[0]) ]


# In[46]:


material_list = {'dem':1, 'cc':2, 'tf':3, 're':4, 'rlm':5, 'ra':6, 'ba':9}


# In[48]:


mat_ids = []
for i in tqdm(np.arange(centr_df.shape[0])[:]):
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


# In[49]:


centr_df['mat_ids'] = mat_ids


# In[50]:


with open("../results/matID.p", 'wb') as f:
    pickle.dump(mat_ids, f, protocol=-1)


# **assign alluvium layer**

# In[20]:


with open("../results/centr_df_matID_alluvium.p", 'rb') as f:
    centr_df = pickle.load(f)


# In[51]:


river_shp = shapefile.Reader(fname_river_shp) 
river_shp = river_shp.shapes() 
# river_poly = [shape.points for shape in river_shp]
river_poly = river_shp[0].points


# In[52]:


river_idx = [Polygon(river_poly).contains(Point(centr_df.loc[i, 'x'], centr_df.loc[i, 'y'])) 
             for i in centr_df.index]


# In[53]:


centr_df['river_idx'] = river_idx


# In[54]:


# assign alluvium to the top 2 layers within river channel
centr_df.loc[(centr_df['layer_ids'] <= 2) & 
             (centr_df['river_idx'] == True), 'mat_ids'] = 10


# **plot material ids**

# In[56]:


ilayer = centr_df[centr_df['layer_ids'] == 1]

sns.scatterplot(x = 'x', y = 'y', hue = 'mat_ids', 
                marker = '.', s=1,
                palette=sns.color_palette(fav_colors('CB_color_cycle'), len(ilayer.mat_ids.unique())),
                edgecolor=None,
               data=ilayer, )


# In[57]:


with open("../results/{}-matID.p".format(name), 'wb') as f:
    pickle.dump(centr_df, f, protocol=-1)


# **assign material ids based on layer id (optional)**
# 
# - Layer #1 is located on top and follow the sequence 1, 2, 3, ...; 
# 
# - Without knowing its layerID, select the cells based on their relative location in the cell index. i.e., `1 : ele_per_layer` belongs to layer 1.

# In[116]:


# # layers = [101, 102] # top 2 layers
# # add alluvium id --5 to the two top layers while the cell id is Hf -- 1
# centr_df.loc[(centr_df['layer_ids'] <= 102) & (centr_df['mat_ids'] == 1), 'mat_ids'] = 5


# In[61]:


# with open("../results/centr_df-coarse_matID.p", 'wb') as f:
#     pickle.dump(centr_df, f, protocol=-1)


# In[58]:


input_h5.close()


# ### write material id to hdf5 file

# In[5]:


with open("../results/{}-matID.p".format(name), 'rb') as f:
    centr_df = pickle.load(f)


# In[59]:


in_h5 = h5.File(fname_out_h5, "r")

out_h5 = h5.File(fname_mesh_matID, 'w')


# In[60]:


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

# In[61]:


data = out_h5['Materials/Material Ids']       # load the data
data[...] = centr_df['mat_ids'].values


# In[62]:


np.allclose(np.array(data), centr_df.mat_ids) # check if the new mat_ids has been read in.


# In[67]:


# del out_h5['Materials/Layer Ids']


# In[63]:


in_h5.close()
out_h5.close()


# ## locate cells （optional)

# In[9]:


with open("../results/centr_df_matID_alluvium.p", 'rb') as f:
    centr_df = pickle.load(f)


# In[11]:


icell = 252300
centr_df.loc[icell, :]


# # Add river region

# Currently, the meshes generated from watershed workflow has some problems in geting the top face correct. See **3.2** for steps. 

# In[238]:


with open("../results/{}-matID.p".format(name), 'rb') as f:
    centr_df = pickle.load(f)


# In[240]:


in_h5 = h5.File(fname_mesh_matID, "r")

out_h5 = h5.File(fname_mesh_matID_river, 'w')


# In[241]:


vert_coord = np.array(in_h5['Domain/Vertices'][:])

cell_vert = np.array(in_h5['Domain/Cells'][:])


# In[242]:


groups = list(in_h5.keys())
for i_group in groups:
    print(i_group)
    group_id = out_h5.require_group(i_group)
    datasets = list(in_h5[i_group].keys())
    for i_dataset in datasets:
        print(i_dataset)
        in_h5.copy("/" + i_group + "/" + i_dataset,
                      group_id, name=i_dataset)


# In[243]:


mass1_df = pd.read_csv(fname_mass1_coord)

mass1_coord = mass1_df[['easting', 'northing']]


# ## get river cells based on layer id

# Only do this if you are certain about the ordering of vertex in each cell. This works for meshes generated using TINERATOR.

# In[66]:


river_cells_df = centr_df[(centr_df['river_idx'] == True) & (centr_df['layer_ids'] ==1)].copy()


# In[72]:


mass1_list = []

for i in tqdm(river_cells_df.index):
    iriver_cell = (river_cells_df.loc[i, 'x'], river_cells_df.loc[i, 'y'])
    idx = closest_node(iriver_cell, mass1_coord)
    imass = mass1_df.loc[idx, 'quadrant']
    mass1_list.append(imass)

mass1_list_unique = sorted(np.unique(mass1_list))


# In[17]:


with open('../results/mass1_list.txt', 'w') as f:
    for item in mass1_list_unique:
        f.write("%s\n" % item)


# In[73]:


river_cells_df['mass1_id']= mass1_list


# In[75]:


sns.scatterplot('x', 'y', 'mass1_id', data= river_cells_df, 
                s= 1, edgecolor = None)
sns.scatterplot('easting', 'northing', color = 'white', s = 1,
                data = mass1_coord.loc[river_cells_df.mass1_id.unique()-1, :])


# In[79]:


# mass1_unique = sorted(river_cells_df.mass1_id.unique())


# In[168]:


for imass in tqdm(mass1_list_unique):
#     imass = 250 # 1-based
    imass_name = 'Mass1_' + str(imass)
    # find river cells within the mass1
    icells = river_cells_df[river_cells_df['mass1_id'] == imass].index

    # find all vertices for the river cells
#     ivert_id = cell_vert[icells, 1:]

    # get top cell face vertex ids, vertices ordered from bottom to top?
    # choose the last three vertices for meshes generated by TINERATOR
#     iface_vert = cell_vert[icells, 4:]   
    # the face vertex id order is not known in watershed workflow!
    iface_vert = cell_vert[icells, 1:4] 

    ivertex_ids = np.concatenate((np.tile(3, (iface_vert.shape[0], 1)), 
                                  iface_vert, 
                                  np.tile(0, (iface_vert.shape[0], 1))), axis = 1)

#     if not all([i in top_vertex for i in ivertex_ids]):
    for i in ivertex_ids:
        if i.tolist() not in top_vertex.tolist():
            raise Exception('cell face vertex_id {} not found in top surface vertex_ids for region {}'.format(i, imass_name))
#         break
#     # get unique vertices
#     iunique_vert = np.array(list(set(x for l in ivert_id for x in l)))

#     # get vertice coordinates, vertice id is 1-based
#     ivert_coord = vert_coord[iunique_vert -1, :] 

    
    
    # write to hdf5 file
    out_h5.create_group("Regions/" + imass_name)
    out_h5.create_dataset("Regions/" + imass_name + "/Vertex Ids", data= ivertex_ids)


# ## get river cells from top sidesets (watershed_workflow)

# Do this if you are not sure about the internal ordering of each vertex. Works for meshes from Watershed Workflow.

# In[176]:


def get_cell_center(vertex_id):
    
    ivert_coord = vert_coord[vertex_id - 1, :]  
    icentr = ivert_coord[:, 0].mean(), ivert_coord[:, 1].mean(), ivert_coord[:, 2].mean()
    
    return icentr


# In[244]:


top_vertex = np.array(in_h5['Regions/Top/Vertex Ids'][:])
top_cell_center = [get_cell_center(i) for i in top_vertex[:, 1:4]]

river_idx = [Polygon(river_poly).contains(Point(top_cell_center[i][0], top_cell_center[i][1])) 
             for i in np.arange(len(top_cell_center))]

top_river_cells = top_vertex[river_idx]
top_river_cell_coord = np.array(top_cell_center)[river_idx]


# In[245]:


mass1_list = []

for i in tqdm(np.arange(len(top_river_cells))):
    iriver_cell = (top_river_cell_coord[i, 0], top_river_cell_coord[i, 1])
    idx = closest_node(iriver_cell, mass1_coord)
    imass = mass1_df.loc[idx, 'quadrant']
    mass1_list.append(imass)

mass1_list_unique = sorted(np.unique(mass1_list))


# In[224]:


fig,ax = plt.subplots(1,1)

ax.plot(top_river_cell_coord[:, 0], top_river_cell_coord[:, 1], 'o', ms = 1)


# In[246]:


for imass in tqdm(mass1_list_unique):
#     imass = 250 # 1-based
    imass_name = 'Mass1_' + str(imass)
    # find river cells within the mass1
    icells = [i for i, e in enumerate(mass1_list) if e == imass]
    ivertex_ids = top_river_cells[icells]
    
#     for i in ivertex_ids:
#     if i.tolist() not in top_vertex.tolist():
#         raise Exception('cell face vertex_id {} not found in top surface vertex_ids for region {}'.format(i, imass_name))
    # write to hdf5 file
    out_h5.create_group("Regions/" + imass_name)
    out_h5.create_dataset("Regions/" + imass_name + "/Vertex Ids", data= ivertex_ids)


# ## save to hdf5

# In[247]:


out_h5.visititems(print_structure)


# In[248]:


in_h5.close()
out_h5.close()


# In[ ]:




