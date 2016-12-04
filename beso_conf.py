# this is the configuration file with input values, which will be executed as python commands

# BASIC INPUTS:

path = "d:\\tmp\\"  # path to the working directory where the initial file is located
#path = "~/tmp/beso/"  # Linux example
#path = "D:\\tmp\\"  # Windows example
path_calculix = "d:\\soft\FreeCad\\FreeCAD_0.17.8264_x64_dev_win\\bin\\ccx"  # path to the CalculiX solver
#path_calculix = "/usr/bin/ccx"  # Linux example, may help shell command: which ccx
#path_calculix = "d:\\soft\FreeCad\\FreeCAD_0.17.8264_x64_dev_win\\bin\\ccx"  # Windows example

file_name = "Fusion_Mesh.inp"  # file with prepared linear static analysis

elset_name = "MechanicalMaterialShellThickness"  # string with name of the element set in .inp file
domain_optimized[elset_name] = True  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [7.9e-9, 7.9e-15]  # equivalent density of the domain material for full material and void material
domain_thickness[elset_name] = [1.0, 1.0]  # [0] for solid elements / thickness of [full, void] shell elements - TODO ignore for solid elements
domain_offset[elset_name] = 0  # offset of shell elements - TODO read offset from .inp file
domain_stress_allowable[elset_name] = [0]  # if not [0], after overcoming this stress, volume_goal will be frozen at the present value
# material of the domain in a CalculiX format after *MATERIAL line,
# insert data for VOID material, FULL material is let from .inp file
# use \n for line break
domain_material[elset_name] = ["*ELASTIC \n210000e-6,  0.3"]

elset_name = "MechanicalMaterial001ShellThickness"  # string with name of the element set in .inp file
domain_optimized[elset_name] = False  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [7.9e-9, 7.9e-15]  # the density of material in the domain
domain_thickness[elset_name] = [1.0, 1.0]  # 0.0 for solid elements / thickness of shell elements
domain_offset[elset_name] = 0  # offset of shell elements
domain_stress_allowable[elset_name] = [0]  # if not 0, after overcoming this stress, volume_goal will be frozen at the present value
# material of the domain in a CalculiX format after *MATERIAL line,
# insert data for VOID material, FULL material is let from .inp file
# use \n for line break
domain_material[elset_name] = ["*ELASTIC \n210000e-6,  0.3"]
# copy this block for defining properties of the next domain

volume_goal = 0.4  # the goal volume as a fragment of the optimized domains full volume

r_min = 2.0  # the radius for applying a filter, perhaps good is 2x mesh size for filters 1, 2; 1.5x mesh size for filter 3

continue_from = ""  # if not "", optimization will load full elements from the given .frd file, e.g. "file051_res_mesh.frd" - TODO will not work for sequential thicknesses


# ADVANCED INPUTS:

cpu_cores = 0  # 0 - use all processor cores, N - will use N number of processor cores

sigma_allowable_tolerance = 10  # negative tolerance to de-freeze volume_goal
# make note, this is von Mises stress averaged over integration points of the each element;
# stresses in nodes are different (they are not used in this algorithm)

use_filter = 3  # 0 - do not use filter,
                # 1 - filter with step over nodes (suffer from boundary sticking, 2nd order elements need more memory)
                # 2 - filter only between elements (suffer from boundary sticking)
                # 3 - filter with step over own point mesh
                # morphology based filters:
                # "erode" - use minimum sensitivity number in radius range
                # "dilate" - use maximum sensitivity number in radius range
                # "open" - aims to remove elements smaller than filter radius(it is "erode" and than "dilate" filter)
                # "close" - aims to close holes smaller than filter radius (it is "dilate" and than "erode" filter)
                # "open-close" - (it is "open" and than "close" filter)
                # "close-open" - (it is "close" and than "open" filter)
                # "combine" - average of erode and delate (i.e. simplified/dirty "open-close" or "close-open" filter)

integration_points = "max"  # "max" - maximal value from all int. pt.,
                            # "average" - average value from all int. pt. (do not use for shell elements in bending)

evolutionary_volume_ratio = 0.015  # the maximum volume change from the last iteration
volume_additional_ratio_max = 0.05  # the maximum volume change of elements switched to the full volume

iterations_limit = 0  # 0 - automatic, <number> - the maximum allowable number of iterations
tolerance = 1e-3  # the maximum relative difference in mean stress in optimization domains between the last 5 iterations needed to finish

save_iteration_meshes = 10  # every i-th iteration export a resulting mesh, 0 - do not save
