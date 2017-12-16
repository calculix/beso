# this is the configuration file with input values, which will be executed as python commands

# BASIC INPUTS:

path = "."  # path to the working directory where the initial file is located
#path = "."  # example - in the current working directory
#path = "~/tmp/beso/"  # Linux example
#path = "D:\\tmp\\"  # Windows example
path_calculix = "d:\\soft\\FreeCad\\FreeCAD_0.17.10993_x64_dev_win\\bin\\ccx"  # path to the CalculiX solver
#path_calculix = "/usr/bin/ccx"  # Linux example, may help shell command: which ccx
#path_calculix = "d:\\soft\FreeCad\\FreeCAD_0.17.8264_x64_dev_win\\bin\\ccx"  # Windows example

file_name = "Plane_Mesh.inp"  # file with prepared linear static analysis

elset_name = "SolidMaterialElementGeometry2D"  # string with name of the element set in .inp file
domain_optimized[elset_name] = True  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [1e-6, 1]  # equivalent density of the domain material for states of switch_elm
domain_thickness[elset_name] = [1.0, 1.0]  # thickness of shell elements for states of switch_elm
domain_offset[elset_name] = 0.0  # offset of shell elements
domain_orientation[elset_name] = []  # orientations for each state referring to inp file,
                                     # e.g. for 2 states ["or1", "or1"], for isotropic material use empty list []
domain_FI[elset_name] = [[("stress_von_Mises", 450.0e6)],  # inner tuples () for separate Failure indices
                         [("stress_von_Mises", 450.0)]]  # new inner list [] for the next state of switch_elm
                        # Filure Indices definition in python tuples (separeate FI for each element state if there are more lists)
                        # Failure Indice FI = element stress / allowable value
                        # examples:
                        # [("user_def", "sxx / 600.0"), ("user_def", "syy / 150.0"), ("user_def", "sxy / 50.0")]  # "user_def" defines complete formula for FI
                        # [("stress_von_Mises", 450.0)]  # for von Mises stress give only allowable stress
domain_material[elset_name] = ["*ELASTIC \n210000e-6,  0.3",  # material definition after CalculiX *MATERIAL card, use \n for line break
                               "*ELASTIC \n210000,  0.3"]  # next string for the next state of switch_elm
domain_same_state[elset_name] = False  # False - element states can differ, True - all domain elements have common state
# copy this block for defining properties of the next domain

mass_goal_ratio = 0.4  # the goal mass as a fragment of the full mass of optimized domains,
                       # i.e. fragment of mass evaluated from effective density and volumes of optimized elements in the highest state

continue_from = ""  # if not "", optimization will load element states from the given files,
                              # for previously generated csv file use "file_name.csv"
                              # for inp or frd meshes use 0th file name e.g. "file051_res_mesh0.inp" or "file051_res_mesh0.frd"
                              # or use number N without apostrophes to start each element from state N (numbered from 0)
                              # (continuing from vtk result file is not supported)

filter_list = [["simple", 2]]  # [[filter type, range, domains or nothing for all domains], [next filter type, range, "domain1", "domain2"], ...]
                            # filter types:
                            # "over points" - filter with step over own point mesh, works on sensitivities TODO does not work correctly, need a fix
                            # "over nodes" - filter with step over nodes (suffer from boundary sticking?, 2nd order elements need more memory), works on sensitivities
                            # "simple" - averages sensitivity number with surroundings (suffer from boundary sticking?), works on sensitivities
                            # morphology based filters:
                            # "erode sensitivity" - use minimum sensitivity number in radius range
                            # "dilate sensitivity" - use maximum sensitivity number in radius range
                            # "open sensitivity" - aims to remove elements smaller than filter radius(it is "erode" and than "dilate" filter)
                            # "close sensitivity" - aims to close holes smaller than filter radius (it is "dilate" and than "erode" filter)
                            # "open-close sensitivity" - (it is "open" and than "close" filter)
                            # "close-open sensitivity" - (it is "close" and than "open" filter)
                            # "combine sensitivity" - average of erode and delate (i.e. simplified/dirty "open-close" or "close-open" filter)

                            # replace "sensitivity" by "state" to use filter on element states instead of sensitivities

# ADVANCED INPUTS:

optimization_base = "stiffness"  # "stiffness" - maximization of stiffness (minimization of compliance), reference_points must be set to "integration points"
                                 # "failure_index" sensitivity number is given by FI/density

cpu_cores = 0  # 0 - use all processor cores, N - will use N number of processor cores

FI_violated_tolerance = 1  # N - freeze mass if, compared to initial state, there is N more elements with FI >= 1
decay_coefficient = -0.2  # k - exponential decay coefficient to dump mass_additive_ratio and mass_removal_ratio after freezing mass
                          # fits to equation: exp(k * i), where i is iteration number from triggering by exceeding FI_violated_tolerance
                          # k = -0.2 ~ after 10 iterations slows down approximately 10 times
                          # k = 0 ~ no decaying

shells_as_composite = False  # True - use more integration points to catch bending stresses (ccx 2.12 WILL FAIL for other than S8R and S6 shell elements)
                            # False - use ordinary shell section
reference_points = "integration points"  # "integration points" - read int. pt values (stresses) from .dat file,
                                         # "nodes" - optimization will read nodal values (stresses) from .inp file (model MUST NOT contain shell nor beam elements)
reference_value = "max"  # "max" - maximal value on element,
                        # "average" - average value on element (do not use for bended shell elements)
sensitivity_averaging = False  # True - averaging sensitivity numbers with previous iteration, False - do not average

mass_addition_ratio = 0.015  # mass to be added in each iteration
mass_removal_ratio = 0.03  # mass to be removed in each iteration
ratio_type = "relative"  # "relative" - ratios of actual mass, "absolute" - ratios of maximal mass
compensate_state_filter = True  # True - if state filter changes iteration mass, next iteration will compensate it
                                 # False - do nothing

steps_superposition = []  # make linear superposition of stress tensors from different steps to save time for evaluation of new load cases,
                          # [] - do not superpose
                          # exammple for 2 new load cases:
                          # [[(0.5, 1), (0.2, 2)], [(-1.5, 3)]]
                          # first superposition is from the first step (i.e. step 1) with stress tensor multiplied by 0.5 plus stress tensor from step 2 multiplied by 0.2,
                          # second superposition is only from step 3 but with stress tensor multiplied by -1.5

iterations_limit = "auto"  # "auto" - automatic estimate, <integer> - the maximum allowable number of iterations
tolerance = 1e-3  # the maximum relative difference in mean stress in optimization domains between the last 5 iterations needed to finish

save_iteration_results = 1  # every i-th iteration save temporary results, 0 - save only final results
save_solver_files = ""  # not removed outputs from the solver, e.g. "inp frd dat cvg sta" will preserve all outputs in iterations defined by save_iteration_results
save_resulting_format = "inp vtk" # "frd" or "inp" format of resulting meshes (each state separately in own mesh file)
                                  # "vtk" output for viewing in Paraview (renumbered mesh, states, sensitivity numbers, failure indices)
                                  # "csv" simple tabelized data - also possible to import into Paraview (element centres of gravity, states, sensitivity numbers, failure indices)
