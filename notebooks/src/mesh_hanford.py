#!/usr/bin/env python
# coding: utf-8

# # Example: mesh a delineated watershed
# 
# Here we mesh the [Coweeta Hydrologic Laboratory](https://www.srs.fs.usda.gov/coweeta/) as an example of how to pull data in from default locations and generate a fully functional ATS mesh.
# 
# This might be the worst example to use to learn how to use Watershed Workflows.  But it is useful to demonstrate the breadth of problems this project was intended to solve.
# 
# This includes a range of datasets:
# 
# * National Hydrography Dataset (NHD) Plus for river network
# * National Resources Conservation Service (NRCS) Soil Survey data for soil types
# * National Land Cover Database (NLCD) for land cover/transpiration/rooting depths
# * National Elevation Dataset (NED) for elevation/DEM

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')
# %matplotlib notebook

import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150


# In[2]:


import os,sys
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm as pcm
import shapely
import logging
import fiona
import rasterio


# In[5]:


sys.path.append('/global/project/projectdirs/m1800/pin/github/watershed-workflow')
sys.path.append('/global/project/projectdirs/m1800/pin/github/watershed-workflow/workflow')
sys.path.append('/global/project/projectdirs/m1800/pin/github/watershed-workflow/workflow_tpls')
sys.path.append('/global/project/projectdirs/m1800/pin/github/seacas/install/lib')


# In[7]:


import workflow
import workflow.source_list
import workflow.ui
import workflow.colors
import workflow.condition
import workflow.mesh
import workflow.split_hucs

workflow.ui.setup_logging(1,None)


# In[8]:


bnd_shp = './data/shapefile/boundary_poly_v5.shp'
river_shp = "./data/shapefile/columbia_river_poly_v2.shp"

fname_dem = "./data/DEM/topobathymetry_20200312_10m.tif"


# ## Import watershed boundary
# 
# Next we set up the source watershed and coordinate system and all data sources for our mesh.  We will use the CRS that is included in the shapefile.

# In[9]:


# specify the input shapefile and a hint as to what HUC it is in.
logging.info("")
logging.info("Meshing shape: {}".format(bnd_shp))
logging.info("="*30)

# get the shape and crs of the shape
crs, watershed = workflow.get_split_form_shapes(bnd_shp)


# In[107]:


# fig,ax = plt.subplots(1,1, figsize=(4,4))
# workflow.plot.hucs(watershed, crs, ax=ax, color='k', linewidth=1)


# A wide range of data sources are available; here we use the defaults except for using NHD Plus for watershed boundaries and hydrography (the default is NHD, which is lower resolution and therefore smaller download sizes).

# In[10]:


# set up a dictionary of source objects
sources = workflow.source_list.get_default_sources()
# sources['HUC'] = workflow.source_list.huc_sources['NHD Plus']
# sources['hydrography'] = workflow.source_list.hydrography_sources['NHD Plus']
workflow.source_list.log_sources(sources)


# ## import river shapes

# ### Option 1--bring your own shape

# In[11]:


with fiona.open(river_shp, mode='r') as fid:
    profile = fid.profile
#     bounds = watershed.exterior().bounds
#     bounds_crs = workflow.crs.from_fiona(profile['crs'])
#     bounds = workflow.warp.bounds(bounds, bounds_crs, workflow.crs.from_fiona(profile['crs']))
    reaches = [r for (i,r) in fid.items()]


# Watershed boundary and river must be in the same CRS.

# In[12]:


# convert to destination crs
native_crs = workflow.crs.from_fiona(profile['crs'])
if crs and not workflow.crs.equal(crs, native_crs):
    for reach in reaches:
        workflow.warp.shape(reach, native_crs, crs)
else:
    crs = native_crs


# **convert to shapely, and merge multiple reach segments into single rivers**

# In[13]:


reaches_s = [workflow.utils.shply(reach) for reach in reaches]
rivers_s = list([shapely.ops.linemerge(shapely.geometry.MultiLineString(reaches_s))])


# In[14]:


fig,ax = plt.subplots(1,1, figsize=(4,4))
workflow.plot.hucs(watershed, crs, ax=ax, color='k', linewidth=1)
# workflow.plot.rivers(reaches_s, crs, ax=ax, color='red', linewidth=1)
x,y = rivers_s[0].xy
ax.plot(x,y, 'b', linewidth = 0.5)


# In[15]:


logging.info("Generate the river tree")
rivers = workflow.hydrography.make_global_tree(rivers_s)


# In[29]:


# rivers = workflow.simplify_and_prune(watershed, rivers_s, filter=False, simplify=500, cut_intersections=True)


# ### Option 2--download river hydrography from NHD

# In[51]:


# simplify = 100 # length scale to target average edge
# hint = '17020016'  # hint: HUC 4 containing this shape. This is necessary to avoid downloading all HUCs to search for this shape

# has_rivers = True
# if has_rivers:
#     # download/collect the river network within that shape's bounds
#     _, reaches = workflow.get_reaches(sources['hydrography'], hint, 
#                                       watershed.exterior().bounds, crs, merge = True, presimplify=True)
#     # simplify and prune rivers not IN the shape, constructing a tree-like data structure
#     # for the river network
#     rivers = workflow.simplify_and_prune(watershed, reaches, filter=True, simplify=simplify, cut_intersections=True)

# else:
#     rivers = list()
#     workflow.split_hucs.simplify(watershed, simplify)


# ## Generate the surface mesh
# 
# First we'll generate the flattened, 2D triangulation, which builds on hydrography data.  Then we download a digital elevation map from the National Elevation Dataset, and extrude that 2D triangulation to a 3D surface mesh based on interpolation between pixels of the DEM.

# Note: 
# - use `tol` to adjust the tolerance of minmium distance between two nodes.
# - The triangles at the intersection between river and watershed will be extremely small, try to cut the intersection.

# In[16]:


# form a triangulation on the shape + river network

# triangulation refinement:
# Refine triangles if their area (in m^2) is greater than A(d), where d is the 
# distance from the triangle centroid to the nearest stream.
# A(d) is a piecewise linear function -- A = A0 if d <= d0, A = A1 if d >= d1, and
# linearly interpolates between the two endpoints.
d0 = 1000; d1 = 10000
# A0 = 100; A1 = 500000 # [10, 1000]m
# A0 = 10000; A1 = 500000 # [100, 1000]m
A0 = 100000; A1 = 5000000

# Refine triangles if they get too acute
min_angle = 32 # degrees

# make 2D mesh
mesh_points2, mesh_tris, d = workflow.triangulate(watershed, rivers,
                                               refine_distance=[d0,A0,d1,A1],
                                               refine_min_angle=min_angle,
                                               enforce_delaunay=True,
                                               diagnostics=True)
#mesh_points2, mesh_tris, d = workflow.triangulate(watershed, rivers,
#                                                 refine_max_area=100000,
#                                                 enforce_delaunay=True,
#                                                 diagnostics=True)


# ## Import DEM

# ### Option 1--Bring your own DEM

# In[17]:


logging.info("import dem from {}".format(fname_dem))
with rasterio.open(fname_dem, 'r') as fid:
    dem_profile = fid.profile
    dem = fid.read(1) # read the first band


# ### Option 2--Download DEM data from source
# 
# This download DEM from USGS NED with resolution of 1as (30 m).

# In[99]:


# # get a raster for the elevation map
# dem_profile, dem = workflow.get_raster_on_shape(sources['DEM'], watershed.exterior(), crs)


# ## elevate mesh to DEM

# In[18]:


# elevate the triangle nodes to the dem
mesh_points3 = workflow.elevate(mesh_points2, crs, dem, dem_profile, algorithm='piecewise bilinear')


# ### plot surface mesh

# Plotting the resulting mesh can be done in a variety of ways, including both 3D plots and mapview.  We show both here, but hereafter use mapview plots as they are a bit clearer (if not so flashy)...

# In[19]:


figsize = (6,6)
figsize_3d = (8,6)

# plot the resulting surface mesh
fig = plt.figure(figsize=figsize_3d)
ax = workflow.plot.get_ax('3d', fig, window=[0.0,0.2,1,0.8])
cax = fig.add_axes([0.23,0.18,0.58,0.03])

mp = ax.plot_trisurf(mesh_points3[:,0], mesh_points3[:,1], mesh_points3[:,2], 
                     triangles=mesh_tris, cmap='viridis', 
                     edgecolor=(0,0,0,.2), linewidth=0.5)
cb = fig.colorbar(mp, orientation="horizontal", cax=cax)

t = cax.set_title('elevation [m]')
ax.view_init(55,0)
ax.set_xticklabels(list())
ax.set_yticklabels(list())

#fig.savefig('watershed_dem_3d')


# In[20]:


# plot the resulting surface mesh
fig = plt.figure(figsize=figsize)
ax = workflow.plot.get_ax(crs, fig)

mp = workflow.plot.triangulation(mesh_points3, mesh_tris, crs, ax=ax, 
                                 color='elevation', edgecolor='gray', linewidth=0.2)
cbar = fig.colorbar(mp, orientation="horizontal", pad=0.05)
workflow.plot.hucs(watershed, crs, ax=ax, color='k', linewidth=1)
workflow.plot.rivers(rivers, crs, ax=ax, color='red', linewidth=1)
ax.set_aspect('equal', 'datalim')
ax.set_title('elevation [m]')
cbar.ax.set_title('elevation [m]')
#fig.savefig('coweeta_dem')


# ### construct 2D mesh

# In[21]:


m2 = workflow.mesh.Mesh2D(coords = mesh_points3.copy(), conn = list(mesh_tris))


# ### hydrologically conditioning the mesh in place by removing pits (optional)

# In[22]:


workflow.condition.condition(m2)


# In[23]:


# plot the change between the two meshes
diff = np.copy(mesh_points3)
diff[:,2] = m2.points[:,2] - mesh_points3[:,2] 
print("max diff = ", np.abs(diff[:,2]).max())
fig, ax = workflow.plot.get_ax(crs, figsize=figsize)
workflow.plot.triangulation(diff, m2.conn, crs, color='elevation', edgecolors='gray', 
                            linewidth=0.2, ax=ax)
ax.set_title('conditioned dz')
plt.show()


# ### export surface mesh to VTK

# In[134]:


m2.write_VTK("./meshes/hanford-mesh-coarse-surface.vtk")


# ## Surface properties: land cover (optional)
# 
# Meshes interact with data to provide forcing, parameters, and more in the actual simulation.  Specifically, we need vegetation type on the surface to provide information about transpiration and subsurface structure to provide information about water retention curves, etc.
# 
# We'll start by downloading and collecting land cover from the NLCD dataset, and generate sets for each land cover type that cover the surface.  Likely these will be some combination of grass, deciduous forest, coniferous forest, and mixed.

# In[37]:


# download the NLCD raster
lc_profile, lc_raster = workflow.get_raster_on_shape(sources['land cover'], 
                                                     watershed.exterior(), crs)

# resample the raster to the triangles
lc = workflow.values_from_raster(m2.centroids(), crs, lc_raster, lc_profile)

# what land cover types did we get?
logging.info('Found land cover dtypes: {}'.format(lc.dtype))
logging.info('Found land cover types: {}'.format(set(lc)))


# In[ ]:


# plot the NLCD data

# -- get the NLCD colormap which uses official NLCD colors and labels
nlcd_indices, nlcd_cmap, nlcd_norm, nlcd_ticks, nlcd_labels =                 workflow.colors.generate_nlcd_colormap(lc)

nlcd_labels_fw = []
for label in nlcd_labels:
    label_fw = label
    if len(label) > 15:
        if ' ' in label:
            lsplit = label.split()
            if len(lsplit) == 2:
                label_fw = '\n'.join(lsplit)
            elif len(lsplit) == 4:
                label_fw = '\n'.join([' '.join(lsplit[0:2]),
                                      ' '.join(lsplit[2:])])
            elif len(lsplit) == 3:
                if len(lsplit[0]) > len(lsplit[-1]):
                    label_fw = '\n'.join([lsplit[0],
                                          ' '.join(lsplit[1:])])
                else:
                    label_fw = '\n'.join([' '.join(lsplit[:-1]),
                                          lsplit[-1]])
    nlcd_labels_fw.append(label_fw)

fig = plt.figure(figsize=figsize)
ax = workflow.plot.get_ax(crs, fig)

polys = workflow.plot.mesh(m2, crs, ax=ax, color=lc, cmap=nlcd_cmap, norm=nlcd_norm, edgecolor='none', 
                                     facecolor='color', linewidth=0.5)
mp = pcm.ScalarMappable(norm=nlcd_norm, cmap=nlcd_cmap)
cb = fig.colorbar(mp)
cb.set_ticks(nlcd_ticks)
cb.set_ticklabels(nlcd_labels_fw)
ax.set_title("land cover index")
fig.savefig('watershed_nlcd')


# ## Subsurface properties: soil type (optional)
# 
# Get soil structure from SSURGO

# In[39]:


# download the NRCS soils data as shapes and project it onto the mesh
import workflow.sources.manager_nrcs
import matplotlib.cm

# -- download the shapes
target_bounds = watershed.exterior().bounds
_, soil_survey = workflow.get_shapes(sources['soil type'], target_bounds, crs)

# -- log the bounds targetted and found
logging.info('target bounds: {}'.format(target_bounds))
logging.info('shape union bounds: {}'.format(
    shapely.ops.cascaded_union(soil_survey).bounds))

# -- determine the NRCS mukey for each soil unit; this uniquely identifies soil 
#    properties
soil_ids = np.array([shp.properties['id'] for shp in soil_survey], np.int32)

# -- color a raster by the polygons (this makes identifying a triangle's value much 
#    more efficient)
soil_color_raster, soil_color_profile, img_bounds =             workflow.color_raster_from_shapes(target_bounds, 10, soil_survey,
                                              soil_ids, crs)

# -- resample the raster to the triangles
soil_color = workflow.values_from_raster(m2.centroids(), crs, 
                                         soil_color_raster, soil_color_profile)


# In[ ]:


# plot the soil data
fig = plt.figure(figsize=figsize)
ax = workflow.plot.get_ax(crs, fig)

mp = workflow.plot.mesh(m2, crs, ax=ax, facecolor='color',
                                 linewidth=0.5, color=soil_color, cmap='copper')
ax.set_title('soil type index')

fig.savefig('watershed_soils')


# ## Mesh extrusion
# 
# Given the surface mesh and material IDs on both the surface and subsurface, we can extrude the surface mesh in the vertical to make a 3D mesh.

# In[24]:


ele_per_layer = mesh_tris.shape[0]


# In[25]:


dz=0.1
tele = 1.1 # increment factor
tckness = [np.around(dz*tele**(i), decimals=2) for i in np.arange(2)]

# tckness = [np.around(dz*tele**(i), decimals=2) for i in np.arange(49)]
# + np.repeat(5, 1, axis=0).tolist()

mat_ids = np.arange(1, len(tckness)+1) # layer ids


# In[26]:


layer_types = ['constant'] * len(tckness)
layer_data = tckness
layer_ncells = [1] * len(tckness)
layer_mat_ids = [np.array([i]*ele_per_layer, dtype=int) for i in mat_ids]


# In[41]:


# layer extrusion
# -- data structures needed for extrusion
# layer_types = []
# layer_data = []
# layer_ncells = []
# layer_mat_ids = []
# z = 0.0

# # -- soil layer --
# #  top 6 m
# #  5 cm initial top cell
# #  10 cells
# #  expanding dz, growing with depth
# ncells = 9 # num of layers
# dz = 0.1 # top layer thickness
# layer_dz = 4 # thickness of total soil layer

# # get increment factor between 1x and 2x to fill a given layer. i.e.,  
# # find f so that z0 + z0*f + z0*f^2 + z0*f^3 + ... + z0*f^ncell <= layer_dz
# tele = workflow.mesh.telescope_factor(ncells, dz, layer_dz)
# logging.info("Got telescoping factor: {}".format(tele))

# for i in range(ncells):
#     layer_types.append('constant')
#     layer_data.append(dz)
#     layer_ncells.append(1)
#     layer_mat_ids.append(soil_color)
#     z += dz
#     dz *= tele
       
# # one more 2m layer makes 6m
# dz = 2.0
# layer_types.append('constant')
# layer_data.append(dz)
# layer_ncells.append(1)
# layer_mat_ids.append(soil_color)
# z += dz

# # -- geologic layer --
# # keep going for 2m cells until we hit the bottom of
# # the domain
# layer_types.append("constant")
# layer_data.append(40 - z) # depth of bottom of domain is 40 m
# layer_ncells.append(int(round(layer_data[-1] / dz)))
# layer_mat_ids.append(999*np.ones_like(soil_color))


# In[27]:


# print the summary
workflow.mesh.Mesh3D.summarize_extrusion(layer_types, layer_data, 
                                            layer_ncells, layer_mat_ids)


# In[28]:


# extrude
m3 = workflow.mesh.Mesh3D.extruded_Mesh2D(m2, layer_types, layer_data, 
                                             layer_ncells, layer_mat_ids)


# ### add land cover sidesets (optional)

# In[43]:


# # add back on land cover side sets
# surf_ss = m3.side_sets[1]

# for index, name in zip(nlcd_indices, nlcd_labels):
#     where = np.where(lc == index)[0]
#     ss = workflow.mesh.SideSet(name, int(index), 
#                             [surf_ss.elem_list[w] for w in where],
#                             [surf_ss.side_list[w] for w in where])        
#     m3.side_sets.append(ss)


# ## export mesh file

# In[29]:


# save to disk
try:
    os.remove('./meshes/hanford_mesh_2layer.exo')
except FileNotFoundError:
    pass
m3.write_exodus('./meshes/hanford_mesh_2layer.exo')


# In[ ]:




