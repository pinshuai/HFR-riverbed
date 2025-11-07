##########################################################################
## Tool to convert Exodus II mesh (in NetCDF format) to PFLOTRAN HDF5 mesh
## Usage: python exodus2pflotran.py exodus_mesh_name.exo pflotran_mesh_name.h5
## 
## Author: Jitendra (Jitu) Kumar (jkumar@climatemodeling.org)
## Environmental Sciences Division, Oak Ridge National Laboratory
## Date: 09/18/2013
## Modified by Satish Karra, LANL 10/09/13 to remove sidesets read
## Changed the type from wedge to hex
## Added check on the degenerate vertices of cells

## Modified by Pin Shuai, 11/01/19 to convert py2 to py3; remove the tab indents and some mismatch in if/elif statements
## fixed a typo on line 'elif exofile.variables[varname].elem_type == 'WEDGE''
##########################################################################


from h5py import * 
from netCDF4 import * 
import numpy 
import os
import sys
import time


def exodus_to_pflotran_mesh(exofilename, pflotranfilename):
    start_time = time.time()
#     infilename = sys.argv[1]
#     outfilename = sys.argv[2]
#     if len(sys.argv) != 3:
#         print("ERROR: Command line arguments not provided.\n")
#         print("Usage: python exodus2pflotran.py exodus_mesh_name.exo pflotran_mesh_name.h5\n")
#         sys.exit(0)

    print("Infile: %s Outfile: %s" %(exofilename, pflotranfilename))

    # Open Exodus NetCDF file
    exofile=Dataset(exofilename)
    
    # Open PFLOTRAN HDF5 Mesh file
    if os.path.exists(pflotranfilename):
        os.remove(pflotranfilename)

    pflotranfile = File(pflotranfilename, mode='w')
    # Let's read some dimensions out of the Exodus file
    
    # Read number of vertices
    num_vert=len(exofile.dimensions['num_nodes'])
    # Read number of elements
    num_elem=len(exofile.dimensions['num_elem'])
    # Number of side sets
    num_sidesets=len(exofile.dimensions['num_side_sets'])
    # Number of material blocks
    num_blocks=len(exofile.dimensions['num_el_blk'])
    
    block_size=numpy.zeros((num_blocks, 2), int)

    mat_id = numpy.zeros((num_elem), int)

    print("Preparing Domain/Vertices")

    # Let's read in x,y,z coordinates and write to the HDF5 file
    h5dset = pflotranfile.create_dataset('Domain/Vertices', (num_vert, 3), 'f8')
    x = exofile.variables['coordx'][:]
    y = exofile.variables['coordy'][:]
    z = exofile.variables['coordz'][:]
    h5dset[:,0] = x
    h5dset[:,1] = y
    h5dset[:,2] = z

    print("Preparing Domain/Cells")

    # We will loop through all blocks and find number of elements 
    # and number of nodes per element
    counter=0 #use this to name elements?? Check this to be consistent with sideset ele!!
    for i in range(num_blocks):
        print("Working on block %d" %(i+1))
        varname='num_el_in_blk'+str(i+1)
        block_size[i,0]=len(exofile.dimensions[varname])
        varname='num_nod_per_el'+str(i+1)
        block_size[i,1]=len(exofile.dimensions[varname])
        # create a matrix to store the Cells/elements and their corresponding vertices/nodes (1st col indicates num of nodes, e.g., WEDGE=6, HEX=8)
        if i == 0:
            cell_array = numpy.zeros((num_elem, (block_size[i,1]+1)), int)

        varname='connect'+str(i+1)
        if exofile.variables[varname].elem_type == 'HEX':
            num_vert_per_elem = 8
        elif exofile.variables[varname].elem_type == 'WEDGE':
            num_vert_per_elem = 6
            
        # store connectivity info (e.g., 6 nodes for each ele)         
        block = exofile.variables[varname][:]
        
        # loop over num of elements in each block
        # find nodes connected to each element
        for j in range(block_size[i,0]):
#             mat_id[counter] = i+1 # ??
            varname = 'eb_prop1'
            mat_id[counter] = exofile.variables[varname][i]
            cell_array[counter, 0] = num_vert_per_elem 
            for k in range(num_vert_per_elem):
                cell_array[counter, k+1] = block[j,k]
                # Check for repetitions in nodes
                nodelist = []
                for inode in cell_array[counter,1:len(cell_array[counter,:])]:
                    if inode not in nodelist:
                        nodelist.append(inode)
                cell_array[counter,:] = 0 
                cell_array[counter,0] = len(nodelist) 
                cell_array[counter,1:len(nodelist)+1] = nodelist  
            counter += 1
        print("Block %d: num_of_ele = %d, num_nod_per_ele = %d" %(i+1, block_size[i,0], block_size[i,1]))
    
#     totsize = numpy.shape(cell_array)
#     print(totsize)
    
    

    h5dset = pflotranfile.create_dataset('Domain/Cells', data=cell_array)

    print("Preparing Materials/Cell Ids and Materials/Material Ids")

    # Write Material Ids
    int_array = numpy.arange(num_elem)
    int_array += 1
    h5dset = pflotranfile.create_dataset('Materials/Cell Ids', data=int_array)
    h5dset = pflotranfile.create_dataset('Materials/Material Ids', data=mat_id)

    # Write sidesets
    for i in range(num_sidesets):
        # ele in each sideset
        varname='elem_ss'+str(i+1)
        elem = exofile.variables[varname][:]
        # face id of boundary face in each ele
        varname='side_ss'+str(i+1)
        side = exofile.variables[varname][:]

#         print(numpy.shape(elem))

        if elem.size != side.size:
            print("Inconsistent size in the data set: "+str(varname))
            sys.exit(0)
        
        # each face has up to 5 nodes         
        sideset = numpy.zeros((side.size,5), int)
        # We will check which face of the element is at the boundary and
        # create our sidesets accordingly
        for j in range(len(elem)):
            sideset[j,0] = 4 # default to 4 node per face
            jelem = elem[j] -1
            # WEDGE
            if (cell_array[jelem,0] == 6): 
                if side[j] == 1:
                    sideset[j,1] = cell_array[jelem,1]
                    sideset[j,2] = cell_array[jelem,2]
                    sideset[j,3] = cell_array[jelem,5]
                    sideset[j,4] = cell_array[jelem,4]
                elif side[j] == 2:
                    sideset[j,1] = cell_array[jelem,2]
                    sideset[j,2] = cell_array[jelem,3]
                    sideset[j,3] = cell_array[jelem,6]
                    sideset[j,4] = cell_array[jelem,5]
                elif side[j] == 3:
                    sideset[j,1] = cell_array[jelem,3]
                    sideset[j,2] = cell_array[jelem,1]
                    sideset[j,3] = cell_array[jelem,4]
                    sideset[j,4] = cell_array[jelem,6]
                elif side[j] == 4:
                    sideset[j,0] = 3 # bottom face has 3 nodes
                    sideset[j,1] = cell_array[jelem,3]
                    sideset[j,2] = cell_array[jelem,2]
                    sideset[j,3] = cell_array[jelem,1]
                elif side[j] == 5:
                    sideset[j,0] = 3 # top face has 3 nodes
                    sideset[j,1] = cell_array[jelem,4]
                    sideset[j,2] = cell_array[jelem,5]
                    sideset[j,3] = cell_array[jelem,6]
            # HEX
            elif (cell_array[jelem,0] == 8):
                if side[j] == 1:
                    sideset[j,1] = cell_array[jelem,1]
                    sideset[j,2] = cell_array[jelem,2]
                    sideset[j,3] = cell_array[jelem,6]
                    sideset[j,4] = cell_array[jelem,5]
                elif side[j] == 2:
                    sideset[j,1] = cell_array[jelem,2]
                    sideset[j,2] = cell_array[jelem,3]
                    sideset[j,3] = cell_array[jelem,7]
                    sideset[j,4] = cell_array[jelem,6]
                elif side[j] == 3:
                    sideset[j,1] = cell_array[jelem,3]
                    sideset[j,2] = cell_array[jelem,7]
                    sideset[j,3] = cell_array[jelem,8]
                    sideset[j,4] = cell_array[jelem,4]
                elif side[j] == 4:
                    sideset[j,1] = cell_array[jelem,4]
                    sideset[j,2] = cell_array[jelem,8]
                    sideset[j,3] = cell_array[jelem,5]
                    sideset[j,4] = cell_array[jelem,1]
                elif side[j] == 5:
                    sideset[j,1] = cell_array[jelem,1]
                    sideset[j,2] = cell_array[jelem,2]
                    sideset[j,3] = cell_array[jelem,3]
                    sideset[j,4] = cell_array[jelem,4]
                elif side[j] == 6:
                    sideset[j,1] = cell_array[jelem,5]
                    sideset[j,2] = cell_array[jelem,6]
                    sideset[j,3] = cell_array[jelem,7]
                    sideset[j,4] = cell_array[jelem,8]


        dataset_name = 'Regions/Sideset%d' % (i+1)
        h5dset = pflotranfile.create_dataset(dataset_name, data=sideset)

    print("Finished conversion!")
    print("Converted PFLOTRAN mesh file is located in " + pflotranfilename)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Time for the mesh conversion = "+str(elapsed_time)+" seconds.")

    exofile.close()
    pflotranfile.close()
if __name__ == "__main__":
    exodus_to_pflotran_mesh()
