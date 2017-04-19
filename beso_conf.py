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

elset_name = "SolidMaterialShellThickness"  # string with name of the element set in .inp file
domain_optimized[elset_name] = True  # True - optimized domain, False - elements will not be removed
domain_density[elset_name] = [1e-6, 1]  # equivalent density of the domain material for states of switch_elm
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

elset_name = "SolidMaterial001ShellThickness"  # string with name of the element set in .inp file
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

continue_from = ""  # if not "", optimization will load full elements from the given files,
                              #  use 0th file name e.g. "file051_res_mesh0.frd" or "file051_res_mesh0.inp"

filter_list = [["close sensitivity", 1.5]]  # [[filter type, range, domains or nothing for all domains], [next filter type, range, "domain1", "domain2"], ...]
                            # filter types:
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

# deprecated filter functions, which work only on all optimization domains together, and work on sensitivity numbers
r_min = 2.0  # radius for filter_on_sensitivity
filter_on_sensitivity = 0  # 0 - do not use this filter,
                           # "over nodes" - filter with step over nodes (suffer from boundary sticking?, 2nd order elements need more memory)
                           # "over points" - filter with step over own point mesh (broken?)

# ADVANCED INPUTS:

cpu_cores = 0  # 0 - use all processor cores, N - will use N number of processor cores

FI_violated_tolerance = 1  # 0 - do not freeze mass due to high FI,
                           # <positive integer N> - freeze mass if there is N more elements with FI > 1 which cannot be swiched up
decay_coefficient = -0.2  # exponential decay coefficient to dump mass_additive_ratio and mass_removal_ratio after freezing mass, because
                           # exp(-0.22 * x) ~ drops after 10 iterations to 0.1
                           # exp(0 * x) ~ no decaying

shells_as_composite = True  # True - use more integration points to catch bending stresses (ccx 2.12 WILL FAIL for other than S4R and S6 shell elements)
                            # False - use ordinary shell section
reference_points = "integration points"  # "integration points" - read int. pt values from .dat file,
                                         # "nodes" - optimization will read nodal values from .inp file (model MUST NOT contain shell or beam elements)
reference_value = "max"  # "max" - maximal value on element,
                        # "average" - average value on element (do not use for bended shell elements)
sensitivity_averaging = False  # True - averaging sensitivity numbers with previous iteration, False - do not average

mass_addition_ratio = 0.01  # mass to be added in each iteration
mass_removal_ratio = 0.03  # mass to be removed in each iteration
ratio_type = "relative"  # "relative" - ratios of actual mass, "absolute" - ratios of maximal mass

iterations_limit = 0  # 0 - automatic estimate, <integer> - the maximum allowable number of iterations
tolerance = 1e-3  # the maximum relative difference in mean stress in optimization domains between the last 5 iterations needed to finish

save_iteration_results = 10  # every i-th iteration export a resulting mesh and do not delete .frd and .dat, 0 - do not save
save_iteration_format = "frd" # "frd" or "inp" format of resulting meshes (each state separately in own mesh file)
