#!/usr/bin/env python
# coding: utf-8

# # Generate mesh using TINerator
# 
# [tutorials](https://github.com/lanl/LaGriT/blob/tinerator/docs/tutorials/index.md)
# 
# Two ways to run TINerator:
# - Using Docker image: `ees16/tinerator`
#     - make sure current working dir is within the image. e.g., /home/jovyan/examples
# - Compile and run on local computer

# In[1]:


import tinerator as tin
import os
import numpy as np
import rasterio
# add headless display
# os.system('/usr/bin/Xvfb :99 -screen 0 1024x768x24 &')
# os.environ['DISPLAY'] = ':99'
# import panel as pn
# pn.extension('vtk')

import geopandas as gpd
import h5py as h5
import pickle
import pandas as pd


# In[2]:


from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
import shapefile


# In[3]:


from tqdm.notebook import tqdm


# In[4]:


import pyvista as pv
from pyvista import set_plot_theme
set_plot_theme('document')
# %matplotlib inline


# In[5]:


def print_structure(name, obj):
    '''
    view the tree structure of hdf5 file
    
    Usage:input_h5.visititems(print_structure)
    '''
    
    print(name)


# In[6]:


print('TINerator version ' + tin.VERSION)
print("Current Working Directory " , os.getcwd())


# In[8]:


os.chdir('./mesh/')
print("Redirect output to Directory " , os.getcwd())


# In[9]:


# inputs
# data_dir = '/home/jovyan/examples/data/'
data_dir = '../data/'
# fname_dem = data_dir + 'columbia_subbasin_DEM.asc'
fname_dem = data_dir + 'DEM/hanford_thorne.tif'
fname_hr = data_dir + 'DEM/HR_thorne.tif'
# fname_river_geo = data_dir + 'river_geo_watershed/river_geometry_watershed.shp'
# fname_river_geo = data_dir + 'shapefile/AT-model-river-geo.shp'

fname_river_shp = data_dir + 'shapefile/river_geometry_watershed.shp'
# outputs
# fname_mesh = data_dir + 'mesh/AT-surface.exo'
fname_mesh = 'Thorne-mesh-surface.exo'
fname_mesh_stacked = 'Thorne-mesh-stacked.exo'
fname_final_mesh = 'Thorne-mesh.exo'

fname_out_h5 = 'AT-mesh-layerID-updated.h5'
fname_out_h5_matID = 'AT-mesh-matID-alluvium.h5'


# ## Import DEM
# 
# Methods of import are found in the submodule `tinerator.load`. Some of these are:
# 
# * `from_file`: load from a locally-stored file
# * `from_matrix`: initialize from a Numpy matrix
# * `from_coordinates`: download and initialize from a longitude / latitude bounding box
# * `from_shapefile`: download and initialize from a shapefile

# In[10]:


my_dem = tin.load.from_file(fname_dem)


# In[11]:


# print(my_dem.dem.__dict__)

my_dem


# ### Visualize DEM
# 
# We can visualize the DEM:

# In[12]:


tin.plot.plot_dem(my_dem) # alternately, you can call `my_dem.plot_dem()`


# ## import river feature shapefile
# 
# - have raster in ASCII format (TIFF currently did not work)

# In[13]:


my_dem.import_river_network(fname_river_shp)


# ## Delineate watershed (Optional)
# 
# In order to construct a dynamically refined TIN, watershed delineation is performed to capture a river feature and selectively refine the mesh around it.
# 
# This is done with the method
# 
# `my_dem.watershed_delineation(threshold:float,method:str='D8')`
#     
# It is difficult to initially tell what the threshold value should be. So, before performing the delineation, we can preview what feature would be generated:
# 
# Note:
# - For details on watershed flow accumulation, see this [watershed delineation doc](https://github.com/lanl/LaGriT/blob/tinerator/docs/tutorials/watershed.md).

# In[ ]:


_ = tin.plot.preview_accumulation(my_dem)


# Note that the feature appears around `1e4`. This will be our threshold value. Also, the threhold value `None` can be used *only* in `interactive` mode!

# In[11]:


delineation_threshold = 5000 # set delineation threshold

my_dem.watershed_delineation(delineation_threshold,interactive=True)

# click on "Run Interact" button after running this code


# ## Create surface mesh
# 
# See [meshing doc](https://github.com/lanl/LaGriT/blob/tinerator/docs/tutorials/meshing.md) and [fuction arguments](https://github.com/lanl/LaGriT/blob/tinerator/docs/api/dem.md#build_refined_triplane)
# 
# Now that we are satisfied with the river feature, we can build the surface mesh.
# 
# * `DEM.build_refined_triplane(edge_min,edge_max)` - builds a surface mesh refined around a feature captured by watershed delineation, with triangle edge lengths between `min_edge` and `max_edge` size
# * `DEM.build_uniform_triplane(edge_length)` - builds a surface mesh with uniform triangles, of edge length `edge_length`
# 
# Note:
# - the threhold value `None` can be used *only* in `interactive` mode!
# - `slope` determines how fast the mesh goes from fine to coarse
# - default `max_edge_length` = bounding_box_len/50; default `min_edge_length`=0

# In[14]:


min_edge_length = 30 # set minimum edge of mesh triangle (integer only); units here are consistent with units in DEM
max_edge_length = 1000 # set maximum edge of mesh triangle (integer only); units here are consistent with units in DEM

# Variably-refined mesh
my_dem.build_refined_triplane(min_edge_length, max_edge_length, slope = 2, 
#                               refine_dist = 0.01, 
                              interactive=False)
# my_dem.build_refined_triplane(None, None, interactive=True)
# Uniformly-refined mesh
#  my_dem.build_uniform_triplane(min_edge_length, max_edge_length, interactive=True)

# click on "Run Interact" button after running this code


# ### save surface mesh
# 
# - Currently mesh could not be dumped to the mounted volume if using Docker!
# - Options for mesh: surface or prism

# In[15]:


tin.dump.to_exodus(my_dem, fname_mesh, mesh='surface')


# ### Visualize surface mesh
# 
# We can visualize the mesh with full 3D interactivity using `vtki` (press `w` to switch to wireframe mode):
# 
# See this [doc](https://docs.pyvista.org/plotting/plotting.html#plotting-in-a-jupyter-notebook) for more plotting functions. 

# In[14]:


mesh = pv.read(fname_mesh)

p = pv.Plotter(notebook=True) # inline static plot
# p = pv.BackgroundPlotter() # popup a new windown; require PyQt5
p.add_mesh(mesh, color='b', style='wireframe')
# .plot(style='wireframe', use_panel=False)
p.show()


# ## Create layered mesh

# We can then create a stacked (layered) mesh.
# 
# The syntax is:
# 
# ```python
# DEM.build_layered_mesh(layers,matids:list=None)
# ```
# 
# Creating a stacked mesh requires only one argument: a list of depths to extrude. The number of layers created will be equal to the number of elements in the list.
# 
# For example, let's say that we want four layers: the first layer should be 10 meters thick, the second 20 meters, the third 30 meters, and the fourth 40 meters.
# 
# This would be represented as:
# 
# ```python
# depths = [10.,20.,30.,40.]
# ```
# 
# We can also assign material ID values to the layers, using another list of equal length.
# 
# ```python
# mat_ids = [1,4,2,1]
# ```
# 
# Note that material IDs must be integer-based.

# In[47]:


# x = np.array(["A", "B"])
tckness = np.repeat(np.array([0.5, 1, 2]), [2, 9, 5], axis=0)
# mat_ids = np.repeat(np.array([5, 1]), [2, 14], axis=0)
# tckness = np.repeat(np.array([0.5, 1]), [2, 9], axis=0)
# mat_ids = np.repeat(np.array([1]), [16], axis=0)
mat_ids = np.arange(101, 117) # layer ids

my_dem.build_layered_mesh(layers=tckness, matids=mat_ids)


# ## add attribute

# Currently tinerator version does not support adding material id based on layer dem; however, it can assign different material ids based on different zone (shapefile?). See documentation [here](https://raw.githack.com/lanl/LaGriT/tinerator/html/tutorials/attributes.html). 

# In[28]:


from skimage.transform import resize


# In[ ]:


from rasterio.plot import show


# In[14]:


with rasterio.open(fname_hr, 'r') as f:
    arr = f.read()


# In[ ]:


# rasterio.plot.show(arr) 


# In[15]:


mat = arr[0, :, :]


# In[21]:


my_dem.add_attribute(mat, layers=None, dtype=int)


# In[ ]:


my_dem.map_function_to_attribute()


# **save stacked mesh file**

# In[47]:


tin.dump.to_exodus(my_dem, fname_mesh_stacked, mesh='stacked')


# ### Visualize layered mesh
# 
# We can visualize the layered mesh similarly to the surface mesh:

# In[16]:


mesh = pv.read(fname_mesh_stacked)

p = pv.Plotter(notebook=True) # inline static plot
# p = pv.BackgroundPlotter() # popup a new windown; require PyQt5
p.add_mesh(mesh, color='gray', style='surface', show_edges = True, edge_color = 'blue')
# .plot(style='wireframe', use_panel=False)
p.show()


# ## Create facesets
# 
# [facesets doc](https://github.com/lanl/LaGriT/blob/tinerator/docs/tutorials/facesets.md)
# 
# TINerator has multiple methods for faceset generation, all of which are found in the `tinerator.facesets` submodule.
# 
# These are:
# 
# * `tinerator.facesets.basic`: can create top surface, bottom surface, and/or side surface facesets
# * `tinerator.facesets.from_elevations`: creates top-surface facesets, discretized by elevation values
# * `tinerator.facesets.sidesets`: creates side-surface facesets, discretized by clockwise [x,y] values
# 
# These faceset objects can be combined to create more complex facesets. 

# ### Basic Facesets
# 
# The `basic` faceset object allows for one or more of:
# 
# * top
# * sides
# * bottom
# 
# Each of these sets - top, sides, bottom - will span the entire domain and will not be discretized.
# 
# ##### Syntax
# 
# ```python
# fs_basic  = tin.facesets.basic(has_top:bool=True,has_bottom:bool=True,has_sides:bool=True)
# ```
# 
# #### Elevation Facesets
# 
# The `from_elevations` faceset type allows for discretization along the Z-axis for the top layer.
# 
# The discretization is controlled by the `heights` argument, which is a sequential list of elevation values.
# 
# For example, with the `heights` array
# 
# ```python
# heights = [50.,100.,150.,200.]
# ```
# 
# five facesets will be created:
# 
# * all surface elements lower than 50 meters
# * all surface elements between 50 and 100 meters
# * all surface elements between 100 and 150 meters
# * all surface elements between 150 and 200 meters
# * all surface elements greater than 200 meters
# 
# The optional argument `keep_body` allows for this discretization to be applied to the entire mesh, rather than just the surface - but this is not recommended.
# 
# ##### Syntax
# 
# ```python
# fs_elev = tin.facesets.from_elevations(heights:list,keep_body:bool=False)
# ```
# 
# #### Sidesets
# 
# Sidesets are facesets that span the sides of the mesh. These may be discretized in one or both of two ways:
# 
# * Clockwise partitioning
# * Layer-based partitioning
# 
# Clockwise-based partitioning allows for distinct sidesets to be created along the boundary of the DEM.
# 
# For an example, consider a square that spans 0 to 1 in both the
# x and y planes. The top, right, and bottom sidesets are represented
# in the drawing below:
# 
# ```
#     1
#  _______
# |       |
# |       | 2
# |       |
#  -------
#     3
# 
# ```
# 
# To construct `coords` properly, the array would look like:
# 
# ```
# [[0.,1.], # top
#  [1.,1.], # right
#  [1.,0.]] # bottom
# ```
# 
# Layer-based partitioning is currently limited to (1) all layers, or (2) the top layer (to allow for outlet-based sidesets). This is controlled with the optional argument `top_layer`.
# 
# ##### Syntax
# 
# ```python
# fs_ss = tin.facesets.sidesets(coords:np.ndarray,top_layer:bool=False)
# ```
# 
# #### Exporting Sidesets
# 
# To export a stacked mesh with defined sidesets, use the function
# 
# ```python
# tin.dump.to_exodus(my_dem,facesets=[list,of,facesets])
# ```

# In[49]:


# Basic facesets; Top, Bottom, and sides
# top face is labeled as "1"; bottom face is labeled as "2"; side face is labeled as "3"
fs_basic = tin.facesets.basic(has_top=True,has_bottom=True,has_sides=True)

# Top layer
# fs_top  = tin.facesets.basic(has_top=True,has_bottom=False,has_sides=False)

# # # Discretized elevations
# # heights = [100, 200, 300, 400, 500, 600, 700, 800, 900]
# # fs_elev = tin.facesets.from_elevations(heights,keep_body=False)

# Bottom layer
# fs_bottom  = tin.facesets.basic(has_top=False,has_bottom=True,has_sides=False)

# # Top and bottom layers
# fs_top_bottom = tin.facesets.basic(has_top=True,has_bottom=True,has_sides=False)

# # Sidesets
# all_sidesets = np.array([[0.,0.],[1.,1.]])
# fs_ss = tin.facesets.sidesets(all_sidesets)


# ### User-defined facesets (optional)
# 
# A user can define facesets along the mesh boundary.

# In[ ]:


# import numpy as np

# Inlet
# use ([x,y], [x, y]) coordinates to delineate (river width + padding) segment along the boundary
# [543890, 145710], [546055, 147140] # (x,y) coordinates from satellite image
# inlet = np.array([[543655,145258],[547045,148348]]) # set (x,y) coordinates from viewing already made mesh in Paraview; 1620 x 1620 mesh
# fs_inlet = tin.facesets.sidesets(inlet,top_layer=True)

# Outlet
# use ([x,y], [x,y]) coordinates to delineate (river width + padding) segment along the boundary
# [599020,101300], [599560, 102072] # (x,y) coordinates from satellite image
# outlet = np.array([[599095,103108],[598495,101068]]) # set (x,y) coordinates of (river width + padding) along the boundary; 1620 x 1620 mesh
# fs_outlet = tin.facesets.sidesets(outlet,top_layer=True)


# ### Visualize facesets
# 
# We can visualize the facesets:

# In[50]:


# import pyvista

# tin.plot.plot_facesets(my_dem,[fs_basic,fs_ss,fs_inlet,fs_outlet])
tin.plot.plot_facesets(my_dem, [fs_basic])


# ## Export final mesh

# In[51]:


tin.dump.to_exodus(my_dem, fname_final_mesh, facesets=fs_basic)
#tin.dump.to_exodus(my_dem,'final_mesh.exo',facesets=fs_top)
#tin.dump.to_exodus(my_dem,'final_mesh.exo',facesets=fs_bottom)
#tin.dump.to_exodus(my_dem,'final_mesh.exo',facesets=fs_ss
# tin.dump.to_exodus(my_dem,'final_mesh.exo',facesets=[fs_basic,fs_ss,fs_inlet,fs_outlet]) # 1 = side; 2 = inlet; 3 = outlet; 4 = top; 5 = bottom; 6 = side


# ### Visualize final mesh
# 
# We can visualize the final mesh:

# In[52]:


mesh = pv.read(fname_final_mesh)


# In[60]:


mesh


# In[ ]:


p = pv.Plotter(notebook=True) # inline static plot
# p = pv.BackgroundPlotter() # popup a new windown; require PyQt5

p.add_mesh(mesh, color='gray', style='surface', show_edges = True, edge_color = 'blue')
p.show()


# In[68]:


# top face is labeled as "1"; bottom face is labeled as "2"; side face is labeled as "3"

mesh['Side Sets'].plot()


# <a id='Conclusion'></a>
# ### Conclusion
# 
# This has been a basic workflow for TINerator. More advanced capabilities can be found in other Jupyter notebooks in this directory, or through the API on the [TINerator homepage](https://raw.githack.com/lanl/LaGriT/tinerator/html/index.html).

# ## add material ids based on raster layers

# In[132]:


input_h5 = h5.File(fname_out_h5, "r")


# In[133]:


input_h5.visititems(print_structure)


# In[134]:


vert_coord = np.array(input_h5['Domain/Vertices'][:])


# In[56]:


vert_coord[:5]


# In[135]:


cell_vert = np.array(input_h5['Domain/Cells'][:])


# In[58]:


cell_vert[:5]


# In[136]:


layer_ids = np.array(input_h5['Materials/Layer Ids'][:])


# In[ ]:





# ## plot single cell

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

# In[59]:


centr = []
for i in np.arange(cell_vert.shape[0])[:]:

    ivert_id = cell_vert[i, 1:] # vertice id is 1-based
    ivert_coord = vert_coord[ivert_id-1, :]  
    
    icentr = ivert_coord[:, 0].mean(), ivert_coord[:, 1].mean(), ivert_coord[:, 2].mean()
    centr.append(icentr)

centr = np.asarray(centr)


# In[61]:


with open("../results/centroid-layerID.p", 'wb') as f:
    pickle.dump(centr, f, protocol=-1)


# ### sample dem elevation for each cell

# In[155]:


with open("../results/centroid-layerID.p", 'rb') as f:
    centr = pickle.load(f)


# In[156]:


centr_xy = centr[:, 0:2]


# In[13]:


# centr_xy_unq = np.vstack({tuple(row) for row in centr_xy})


# Sample point value at each cell center

# In[147]:


with rasterio.open(fname_hr) as ras:
    pts = [i[0] for i in ras.sample(centr_xy[:])]


# In[157]:


centr_df = pd.DataFrame(centr, columns= ['x', 'y', 'z'])


# In[158]:


centr_df['hr_elev'] = pts


# In[159]:


centr_df['layer_ids'] = layer_ids


# ### assign material id

# **assign material id based on its relative elevation to `HR_contact`**
# 
# material|id
# ---|---
# hf|1
# ringold|4
# alluvium|5
# 

# In[207]:


mat_ids = [1 if centr_df.loc[i, "z"] > centr_df.loc[i, "hr_elev"] else 4 for i in np.arange(centr_df.shape[0]) ]


# In[208]:


centr_df['mat_ids'] = mat_ids


# **assign material id based on river shape**

# In[170]:


river_shp = shapefile.Reader(fname_river_shp) 
river_shp = river_shp.shapes() 
# river_poly = [shape.points for shape in river_shp]
river_poly = river_shp[0].points


# In[201]:


river_idx = [Polygon(river_poly).contains(Point(centr_df.loc[i, 'x'], centr_df.loc[i, 'y'])) 
             for i in centr_df.index]


# In[205]:


centr_df['river_idx'] = river_idx


# In[210]:


centr_df.loc[(centr_df['layer_ids'] <= 102) & (centr_df['mat_ids'] == 1) & (centr_df['river_idx'] == True), 'mat_ids'] = 5


# **assign material ids based on layer id**
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


out_h5 = h5.File("AT-mesh-alluvium-rivershape.h5", 'w')


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


# In[227]:


data = out_h5['Materials/Material Ids']       # load the data
data[...] = centr_df['mat_ids'].values


# In[228]:


np.allclose(np.array(data), centr_df.mat_ids) # check if the new mat_ids has been read in.


# In[229]:


# del out_h5['Materials/Layer Ids']


# In[230]:


in_h5.close()
out_h5.close()


# <a id='Appendix'></a>
# ### Appendix
# 
# Run all code at once, bypassing previous descriptions:

# In[ ]:


import tinerator as tin
import os
import numpy as np
 
os.chdir('/Users/leer384/Documents/MODELING/mesh_generation/TINerator') # set working directory
dem_filename = 'data/columbia_subbasin_DEM_hanford.asc' # set filename of DEM, which is stored in "data" folder
my_dem = tin.load.from_file(dem_filename)

# Watershed river features delineation
delineation_threshold = 200000 # set delineation threshold
my_dem.watershed_delineation(delineation_threshold)

# Mesh cell edge length
edge_min = 100 # set minimum edge of mesh triangle (integer only); units here are consistent with units in DEM
edge_max = 1620  # set maximum edge of mesh triangle (integer only); units here are consistent with units in DEM
edge_length = 1620 # set uniform edge of mesh triangle (integer only); units here are consistent with units in DEM

# Mesh type
my_dem.build_refined_triplane(edge_min,edge_max) # set if variably-refined mesh (if yes, then uncomment)
#my_dem.build_uniform_triplane(edge_length) # set if uniformly-refined mesh (if yes, then uncomment)

# Mesh layers
depths = [1000, 1000] # set depths of layers
mat_ids = [0, 1] # set material IDs of layers
my_dem.build_layered_mesh(depths,matids=mat_ids)

# Mesh facesets
# Basic facesets; Top, Bottom, and sides
# top face is labeled as "1"; bottom face is labeled as "2"; side face is labeled as "3"
fs_basic = tin.facesets.basic(has_top=True,has_bottom=True,has_sides=True)
 
# Top layer
fs_top  = tin.facesets.basic(has_top=True,has_bottom=False,has_sides=False)
 
# Discretized elevations
heights = [100, 200, 300, 400, 500, 600, 700, 800, 900]
fs_elev = tin.facesets.from_elevations(heights,keep_body=False)
 
# Bottom layer
fs_bottom  = tin.facesets.basic(has_top=False,has_bottom=True,has_sides=False)

# Top and bottom layers
fs_top_bottom = tin.facesets.basic(has_top=True,has_bottom=True,has_sides=False)

# Sidesets
all_sidesets = np.array([[0.,0.],[1.,1.]])
fs_ss = tin.facesets.sidesets(all_sidesets)

# Inlet
# use ([x,y], [x, y]) coordinates to delineate (river width + padding) segment along the boundary
# [543890, 145710], [546055, 147140] # (x,y) coordinates from satellite image
inlet = np.array([[543655,145258],[547045,148348]]) # set (x,y) coordinates from viewing already made mesh in Paraview; 1620 x 1620 mesh
fs_inlet = tin.facesets.sidesets(inlet,top_layer=True)

# Outlet
# use ([x,y], [x,y]) coordinates to delineate (river width + padding) segment along the boundary
# [599020,101300], [599560, 102072] # (x,y) coordinates from satellite image
outlet = np.array([[599095,103108],[598495,101068]]) # set (x,y) coordinates of (river width + padding) along the boundary; 1620 x 1620 mesh
fs_outlet = tin.facesets.sidesets(outlet,top_layer=True)



# Export mesh
tin.dump.to_exodus(my_dem,'final_mesh.exo',facesets=[fs_basic,fs_ss,fs_inlet,fs_outlet]) # 1 = side sans outlet; 2 = inlet; 3 = outlet; 4 = top; 5 = bottom; 6 = full side

# Visualize DEM
print('DEM:')
tin.plot.plot_dem(my_dem)

# Visualize facesets
print('Facesets:')
tin.plot.plot_facesets(my_dem,[fs_basic,fs_ss,fs_inlet,fs_outlet])

# Print TINerator version
print('TINerator version ' + tin.VERSION)


# In[ ]:




