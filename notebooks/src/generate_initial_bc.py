#!/usr/bin/env python
# coding: utf-8

# # generate initial boundary head for HFR-thorne model

# In[11]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import h5py

from glob import glob

from natsort import natsorted

from PS import find_nearest, printname

import geopandas as gpd


# In[2]:


get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150


# ## IO files

# In[10]:


fname_mass1 = "/global/project/projectdirs/m1800/pin/HFR-thermal/data/MASS1/transient_1976_2019/"
fname_mass1_datum = "/global/project/projectdirs/m1800/pin/HFR-thermal/data/MASS1/Mass1_datum_shift.csv"

fname_head = "/global/project/projectdirs/m1800/pin/HFR-thermal/outputs/TH_100x100x2_thermal/wl-exported/wl-exported_2016-2019/" +            '2016-01-11 00:00:00.csv'

fname_initial_head = "/global/project/projectdirs/m1800/pin/HFR-thorne/inputs/"      + "HFR_H_Initial.h5"

fname_boundary_shp = "/global/project/projectdirs/m1800/pin/HFR-thorne/data/boundary_polygon_v3/boundary_polygon_v3.shp"


# ## plot river stage

# In[7]:


mass1_files = glob(fname_mass1 + '*.csv')

mass1_files = natsorted(mass1_files)

mass1_df = pd.read_csv(mass1_files[0])

mass1_datum = pd.read_csv(fname_mass1_datum)

mass1_df['stage'] = mass1_df['stage'] + mass1_datum.loc[0, 'NGVD88Offse']

mass1_df['date'] = pd.to_datetime(mass1_df['date'])

mass1_df.set_index('date', inplace = True)


# In[31]:


fig, ax = plt.subplots(1,1, figsize= (8, 4))
mass1_df.plot(y = 'stage', ax= ax, lw = 0.5)
ax.set_xlim(['01/01/2007', None])


# In[36]:


mass1_df.loc['2007-01-01 00:00:00', 'stage']


# In[32]:


fig, ax = plt.subplots(1,1, figsize= (8, 4))
mass1_df.plot(y = 'stage', ax= ax, lw = 0.5)
ax.set_xlim(['01/01/2007', '12/31/2007'])


# In[ ]:





# In[35]:


mass1_df.loc['01/01/2016', 'stage']


# In[15]:


mass1_new = mass1_df.loc['01/01/2016':'01/31/2016', 'stage'].copy()


# In[16]:


idx, value = find_nearest(mass1_new.values, mass1_df.loc['2007-01-01 00:00:00', 'stage'])


# In[24]:


mass1_new.iloc[idx], mass1_new.index[idx]


# In[18]:


fig, ax = plt.subplots(1,1, figsize= (8, 4))
mass1_df.plot(y = 'stage', ax= ax, lw = 0.5)
# ax.plot(x = mass1_df.iloc[idx, 'stage'])
mass1_new.plot(y = mass1_new[idx])
ax.set_xlim(['01/01/2016', '12/31/2016'])


# ## import head from Reach-scale simulation

# In[6]:


head = pd.read_csv(fname_head, header= None)


# In[7]:


dx = dy = 100
model_ll_coord = (552050, 105050)
xlen = ylen = 60000


# In[12]:


fig, ax = plt.subplots(1,1, figsize=(8,8))

xcoord = np.arange(model_ll_coord[0], model_ll_coord[0] + xlen -99, dx)
ycoord = np.arange(model_ll_coord[1], model_ll_coord[1] + ylen - 99, dy)

cl = ax.contour(xcoord, ycoord, head, linewidths=0.5, colors='gray')
plt.clabel(cl, inline = True, fmt = '%5.0f', fontsize = 10)

cf = ax.contourf(xcoord, ycoord, head)
plt.colorbar(cf)

boundary_shape=gpd.read_file(fname_boundary_shp)
boundary_shape.plot(facecolor = 'none', edgecolor = 'black', ax=ax, alpha=1)


# ## export to HDF5

# **note: In PFLOTRAN initial head hdf5 file, the matrix dimension is (ny, nx); i.e. ny = ncol, nx = nrow; it starts from (x0, y0) in the upper left, while it starts from (x0, yn) in the upper left in `contourf` plot**

# In[15]:


head_T = head.T


# In[16]:


f = h5py.File(fname_initial_head, "w")

grp = f.create_group("Initial_Head")

dset = f.create_dataset("Initial_Head/Data", data = head_T)


# In[17]:


f.visit(printname)


# **add attributes**

# For strings in attributes, need to use fixed-width ASCII strings using `numpy.string_("hello")` method for maximum compatability. See [documentation](http://docs.h5py.org/en/stable/strings.html#how-to-store-text-strings)

# In[18]:


grp.attrs['Cell Centered'] = 1.0
grp.attrs['Dimension'] = np.string_("XY")
grp.attrs['Discretization'] = (dx, dy)
grp.attrs['Max Buffer Size'] = 250
grp.attrs['Origin'] = model_ll_coord


# In[19]:


for item in grp.attrs.keys():
    print(item + ":", grp.attrs[item])


# In[20]:


f.close()


# In[ ]:




