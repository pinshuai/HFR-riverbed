Generate the PFLOTRAN deck:

1. run mesh_hanford.ipynb to generate the mesh for hanford site
   require watershed-workflow

2. run generate_material_ids.ipynb

3. run generate_initial_bc.ipynb

4. run generate_PF_in.ipynb

5. run update_permeability.ipynb

6. run PFLOTRAN_input_deck.ipynb

Runing the PFLOTRAN model

Postprocess the PFLOTRAN dataset

1. plot_comparison_wells.ipynb

2. plot_flux_from_mass_balance.ipynb

3. plot_flux_from_river_cell.ipynb

4. plot gw_map.ipynb

5. plot river_tracer.ipynb

6. plot_simu_obs_wells.ipynb

7. VTK_output.ipynb