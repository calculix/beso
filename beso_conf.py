# this is the configuration file with input values, which will be executed as python commands

# BASIC INPUTS:

path = "."  # path to the working directory where the initial file is located
#path = "."  # example - in the current working directory
#path = "~/tmp/beso/"  # Linux example
#path = "D:\\tmp\\"  # Windows example
path_calculix = "d:\\soft\FreeCad\\FreeCAD_0.17.8264_x64_dev_win\\bin\\ccx"  # path to the CalculiX solver
#path_calculix = "/usr/bin/ccx"  # Linux example, may help shell command: which ccx
#path_calculix = "d:\\soft\FreeCad\\FreeCAD_0.17.8264_x64_dev_win\\bin\\ccx"  # Windows example

file_name = "Fusion_Mesh.inp"  # file with prepared linear static analysis

elset_name = "MechanicalMaterialShellThickness"  # string with name of the element set in .inp file
domain_optimized[elset_name] = True  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [7.9e-15, 7.9e-9]  # equivalent density of the domain material for states of switch_elm
domain_thickness[elset_name] = [1.0, 1.0]  # thickness of shell elements for states of switch_elm
domain_offset[elset_name] = 0.0  # offset of shell elements
domain_FI[elset_name] = [[("stress_von_Mises", 450.0)],  # inner tuples () for separate Failure indices
                         [("stress_von_Mises", 450.0)]]  # new inner list [] for the next state of switch_elm
                        # Filure Indices definition in python tuples (separeate FI for each element state if there are more lists)
                        # Failure Indice FI = element stress / allowable value
                        # examples:
                        # [("user_def", "sxx / 600.0"), ("user_def", "syy / 150.0"), ("user_def", "sxy / 50.0")]  # "user_def" defines complete formula for FI
                        # [("stress_von_Mises", 450.0)]  # for von Mises stress give only allowable stress
domain_material[elset_name] = ["*ELASTIC \n210000e-6,  0.3",  # material definition after CalculiX *MATERIAL card, use \n for line break
                               "*ELASTIC \n210000,  0.3"]  # next string for the next state of switch_elm

elset_name = "MechanicalMaterial001ShellThickness"  # string with name of the element set in .inp file
domain_optimized[elset_name] = False  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [7.9e-15, 7.9e-9]  # equivalent density of the domain material for states of switch_elm
domain_thickness[elset_name] = [1.0, 1.0]  # thickness of shell elements for states of switch_elm
domain_offset[elset_name] = 0.0  # offset of shell elements
domain_FI[elset_name] = [[("stress_von_Mises", 450.0)],  # inner tuples () for separate Failure indices
                         [("stress_von_Mises", 450.0)]]  # new inner list [] for the next state of switch_elm
                        # Filure Indices definition in python tuples (separeate FI for each element state if there are more lists)
                        # Failure Indice FI = element stress / allowable value
                        # examples:
                        # [("user_def", "sxx / 600.0"), ("user_def", "syy / 150.0"), ("user_def", "sxy / 50.0")]  # "user_def" defines complete formula for FI
                        # [("stress_von_Mises", 450.0)]  # for von Mises stress give only allowable stress
domain_material[elset_name] = ["*ELASTIC \n210000e-6,  0.3",  # material definition after CalculiX *MATERIAL card, use \n for line break
                               "*ELASTIC \n210000,  0.3"]  # next string for the next state of switch_elm
# copy this block for defining properties of the next domain

mass_goal_ratio = 0.4  # the goal mass as a fragment of the optimized domains full mass

r_min = 2.0  # the radius for applying a filter, perhaps good is 2x mesh size for filters 1, 2; 1.5x mesh size for filter 3
             # this radius is for filter_on_sensitivity and for filter_on_state

continue_from = ""  # if not "", optimization will load full elements from the given files,
                              #  use file name without number of state e.g. "file051_res_mesh"
                              # in this case total mass is computed from this state which affect mass_goal_ratio

filter_list = [["close", 1.5]]  # [[filter type, range, domains or nothing for all domains], [next filter type, range, "domain1", "domain2"], ...]

# ADVANCED INPUTS:

cpu_cores = 0  # 0 - use all processor cores, N - will use N number of processor cores

FI_violated_tolerance = 1  # 0 - do not freeze mass due to high FI,
                           # <positive integer N> - freeze mass if there is N more elements with FI > 1 which cannot be swiched up
decay_coefficient = -0.2  # exponential decay coefficient to dump mass_additive_ratio and mass_removal_ratio after freezing mass
                           # exp(-0.22 x) ~ 0.1 x
                           # exp(0 x) = x

filter_on_sensitivity = 0  # 0 - do not use filter,
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

filter_on_state = 0  # 0 - do not use filter,
                                # or any of morphological filters mentioned above (except "combine")

##same_state = []  # list of domains which are forced to have same element state over the whole domain (each separately)

max_or_average = "max"  # "max" - maximal value from all int. pt.,
                        # "average" - average value from all int. pt. (do not use for shell elements in bending)
sensitivity_averaging = True  # True - averaging sensitivity numbers with previous iteration, False - do not average

mass_addition_ratio = 0.01  # mass to be added in each iteration
mass_removal_ratio = 0.03  # mass to be removed in each iteration

iterations_limit = 0  # 0 - automatic estimate, <integer> - the maximum allowable number of iterations
tolerance = 1e-3  # the maximum relative difference in mean stress in optimization domains between the last 5 iterations needed to finish

save_iteration_results = 10  # every i-th iteration export a resulting mesh and do not delete .frd and .dat, 0 - do not save
