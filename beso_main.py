#!/usr/bin/env python3
# optimization program using CalculiX solver
# BESO (Bi-directional Evolutionary Structural Optimization Method)

import numpy as np
import matplotlib.pyplot as plt
import multiprocessing
import os
import subprocess
import sys
import time
import beso_lib
import beso_filters
import beso_plots
import beso_separate
# import importlib
# importlib.reload(beso_plots)  # reloads without FreeCAD restart
plt.close("all")
start_time = time.time()

# initialization of variables - default values
domain_optimized = {}
domain_density = {}
domain_thickness = {}
domain_offset = {}
domain_orientation = {}
domain_FI = {}
domain_material = {}
domain_same_state = {}
path = "."
path_calculix = ""
file_name = "Plane_Mesh.inp"
mass_goal_ratio = 0.4
continue_from = ""
filter_list = [["simple", 0]]
optimization_base = "stiffness"
cpu_cores = 0
FI_violated_tolerance = 1
decay_coefficient = -0.2
shells_as_composite = False
reference_points = "integration points"
reference_value = "max"
sensitivity_averaging = False
mass_addition_ratio = 0.01
mass_removal_ratio = 0.03
ratio_type = "relative"
compensate_state_filter = False
steps_superposition = []
iterations_limit = "auto"
tolerance = 1e-3
displacement_graph = []
save_iteration_results = 1
save_solver_files = ""
save_resulting_format = "inp vtk"

# Get the real beso_main.py to derive our filepath from
try:
    resolved_besofile = os.readlink(__file__)
except OSError:
    resolved_besofile = __file__

beso_dir = os.path.dirname(resolved_besofile)

# read configuration file to fill variables listed above
exec(open(os.path.join(beso_dir, "beso_conf.py")).read())

# if available, set the input file according to the first
# cmdline argument given to the script.
try:
    file_name = sys.argv[1]
except IndexError:
    pass

domains_from_config = domain_optimized.keys()
criteria = []
domain_FI_filled = False
for dn in domain_FI:  # extracting each type of criteria
    if domain_FI[dn]:
        domain_FI_filled = True
    for state in range(len(domain_FI[dn])):
        for dn_crit in domain_FI[dn][state]:
            if dn_crit not in criteria:
                criteria.append(dn_crit)

# default values if not defined by user
for dn in domain_optimized:
    try:
        domain_thickness[dn]
    except KeyError:
        domain_thickness[dn] = []
    try:
        domain_offset[dn]
    except KeyError:
        domain_offset[dn] = 0.0
    try:
        domain_orientation[dn]
    except KeyError:
        domain_orientation[dn] = []
    try:
        domain_same_state[dn]
    except KeyError:
        domain_same_state[dn] = False

number_of_states = 0  # find number of states possible in elm_states
for dn in domains_from_config:
    number_of_states = max(number_of_states, len(domain_density[dn]))

# set an environmental variable driving number of cpu cores to be used by CalculiX
if cpu_cores == 0:  # use all processor cores
    cpu_cores = multiprocessing.cpu_count()
os.putenv('OMP_NUM_THREADS', str(cpu_cores))

# writing log file with settings
msg = "\n"
msg += "---------------------------------------------------\n"
msg += ("file_name = %s\n" % file_name)
msg += ("Start at    " + time.ctime() + "\n\n")
for dn in domain_optimized:
    msg += ("elset_name              = %s\n" % dn)
    msg += ("domain_optimized        = %s\n" % domain_optimized[dn])
    msg += ("domain_density          = %s\n" % domain_density[dn])
    msg += ("domain_thickness        = %s\n" % domain_thickness[dn])
    msg += ("domain_offset           = %s\n" % domain_offset[dn])
    msg += ("domain_orientation      = %s\n" % domain_orientation[dn])
    try:
        msg += ("domain_FI               = %s\n" % domain_FI[dn])
    except KeyError:
        msg += "domain_FI               = None\n"
    msg += ("domain_material         = %s\n" % domain_material[dn])
    msg += ("domain_same_state       = %s\n" % domain_same_state[dn])
    msg += "\n"
msg += ("mass_goal_ratio         = %s\n" % mass_goal_ratio)
msg += ("continue_from           = %s\n" % continue_from)
msg += ("filter_list             = %s\n" % filter_list)
msg += ("optimization_base       = %s\n" % optimization_base)
msg += ("cpu_cores               = %s\n" % cpu_cores)
msg += ("FI_violated_tolerance   = %s\n" % FI_violated_tolerance)
msg += ("decay_coefficient       = %s\n" % decay_coefficient)
msg += ("shells_as_composite     = %s\n" % shells_as_composite)
msg += ("reference_points        = %s\n" % reference_points)
msg += ("reference_value         = %s\n" % reference_value)
msg += ("mass_addition_ratio     = %s\n" % mass_addition_ratio)
msg += ("mass_removal_ratio      = %s\n" % mass_removal_ratio)
msg += ("ratio_type              = %s\n" % ratio_type)
msg += ("compensate_state_filter = %s\n" % compensate_state_filter)
msg += ("sensitivity_averaging   = %s\n" % sensitivity_averaging)
msg += ("steps_superposition     = %s\n" % steps_superposition)
msg += ("iterations_limit        = %s\n" % iterations_limit)
msg += ("tolerance               = %s\n" % tolerance)
msg += ("displacement_graph      = %s\n" % displacement_graph)
msg += ("save_iteration_results  = %s\n" % save_iteration_results)
msg += ("save_solver_files       = %s\n" % save_solver_files)
msg += ("save_resulting_format   = %s\n" % save_resulting_format)
msg += "\n"
file_name = os.path.join(path, file_name)
beso_lib.write_to_log(file_name, msg)

# mesh and domains importing
[nodes, Elements, domains, opt_domains, en_all, plane_strain, plane_stress, axisymmetry] = beso_lib.import_inp(
    file_name, domains_from_config, domain_optimized, shells_as_composite)
domain_shells = {}
domain_volumes = {}
for dn in domains_from_config:  # distinguishing shell elements and volume elements
    domain_shells[dn] = set(domains[dn]).intersection(list(Elements.tria3.keys()) + list(Elements.tria6.keys()) +
                                                      list(Elements.quad4.keys()) + list(Elements.quad8.keys()))
    domain_volumes[dn] = set(domains[dn]).intersection(list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) +
                                                       list(Elements.hexa8.keys()) + list(Elements.hexa20.keys()) +
                                                       list(Elements.penta6.keys()) + list(Elements.penta15.keys()))

# initialize element states
elm_states = {}
if isinstance(continue_from, int):
    for dn in domains_from_config:
        if (len(domain_density[dn]) - 1) < continue_from:
            sn = len(domain_density[dn]) - 1
            msg = "\nINFO: elements from the domain " + dn + " were set to the highest state.\n"
            beso_lib.write_to_log(file_name, msg)
            print(msg)
        else:
            sn = continue_from
        for en in domains[dn]:
            elm_states[en] = sn
elif continue_from[-4:] == ".frd":
    elm_states = beso_lib.import_frd_state(continue_from, elm_states, number_of_states, file_name)
elif continue_from[-4:] == ".inp":
    elm_states = beso_lib.import_inp_state(continue_from, elm_states, number_of_states, file_name)
elif continue_from[-4:] == ".csv":
    elm_states = beso_lib.import_csv_state(continue_from, elm_states, file_name)
else:
    for dn in domains_from_config:
        for en in domains[dn]:
            elm_states[en] = len(domain_density[dn]) - 1  # set to highest state

# computing volume or area, and centre of gravity of each element
[cg, cg_min, cg_max, volume_elm, area_elm] = beso_lib.elm_volume_cg(file_name, nodes, Elements)
mass = [0.0]
mass_full = 0  # sum from initial states TODO make it independent on starting elm_states?

for dn in domains_from_config:
    if domain_optimized[dn] is True:
        for en in domain_shells[dn]:
            mass[0] += domain_density[dn][elm_states[en]] * area_elm[en] * domain_thickness[dn][elm_states[en]]
            mass_full += domain_density[dn][len(domain_density[dn]) - 1] * area_elm[en] * domain_thickness[dn][
                                                                                            len(domain_density[dn]) - 1]
        for en in domain_volumes[dn]:
            mass[0] += domain_density[dn][elm_states[en]] * volume_elm[en]
            mass_full += domain_density[dn][len(domain_density[dn]) - 1] * volume_elm[en]
print("initial optimization domains mass {}" .format(mass[0]))

if iterations_limit == "auto":  # automatic setting
    m = mass[0] / mass_full
    if ratio_type == "absolute" and (mass_removal_ratio - mass_addition_ratio > 0):
        iterations_limit = int((m - mass_goal_ratio) / (mass_removal_ratio - mass_addition_ratio) + 25)
    elif ratio_type == "absolute" and (mass_removal_ratio - mass_addition_ratio < 0):
        iterations_limit = int((mass_goal_ratio - m) / (mass_addition_ratio - mass_removal_ratio) + 25)
    elif ratio_type == "relative":
        it = 0
        if mass_removal_ratio - mass_addition_ratio > 0:
            while m > mass_goal_ratio:
                m -= m * (mass_removal_ratio - mass_addition_ratio)
                it += 1
        else:
            while m < mass_goal_ratio:
                m += m * (mass_addition_ratio - mass_removal_ratio)
                it += 1
        iterations_limit = it + 25
    print("\niterations_limit set automatically to %s" % iterations_limit)
    msg = ("\niterations_limit        = %s\n" % iterations_limit)
    beso_lib.write_to_log(file_name, msg)

# preparing parameters for filtering sensitivity numbers
weight_factor2 = {}
near_elm = {}
weight_factor3 = []
near_elm3 = []
near_points = []
weight_factor_node = []
M = []
weight_factor_distance = []
near_nodes = []
above_elm = {}
below_elm = {}
filter_auto = False
for ft in filter_list:  # find if automatic filter range is used
    if ft[0] and (ft[1] == "auto") and not filter_auto:
        size_elm = beso_filters.find_size_elm(Elements, nodes)
        filter_auto = True
for ft in filter_list:
    if ft[0] and ft[1]:
        f_range = ft[1]
        if ft[0] == "casting":
            if len(ft) == 3:
                domains_to_filter = list(opt_domains)
                beso_filters.check_same_state(domain_same_state, domains_from_config, file_name)
            else:
                domains_to_filter = []
                filtered_dn = []
                for dn in ft[3:]:
                    domains_to_filter += domains[dn]
                    filtered_dn.append(dn)
                beso_filters.check_same_state(domain_same_state, filtered_dn, file_name)
            casting_vector = ft[2]
            if f_range == "auto":
                size_avg = beso_filters.get_filter_range(size_elm, domains, filtered_dn)
                f_range = size_avg * 2
                msg = "Filtered average element size is {}, filter range set automatically to {}".format(size_avg,
                                                                                                         f_range)
                print(msg)
                beso_lib.write_to_log(file_name, msg)
            [above_elm, below_elm] = beso_filters.prepare2s_casting(cg, f_range, domains_to_filter,
                                                                    above_elm, below_elm, casting_vector)
            continue  # to evaluate other filters
        if len(ft) == 2:
            domains_to_filter = list(opt_domains)
            filtered_dn = domains_from_config
            beso_filters.check_same_state(domain_same_state, filtered_dn, file_name)
        else:
            domains_to_filter = []
            filtered_dn = []
            for dn in ft[3:]:
                domains_to_filter += domains[dn]
                filtered_dn.append(dn)
            beso_filters.check_same_state(domain_same_state, filtered_dn, file_name)
        if f_range == "auto":
            size_avg = beso_filters.get_filter_range(size_elm, domains, filtered_dn)
            f_range = size_avg * 2
            msg = "Filtered average element size is {}, filter range set automatically to {}".format(size_avg, f_range)
            print(msg)
            beso_lib.write_to_log(file_name, msg)
        if ft[0] == "over points":
            beso_filters.check_same_state(domain_same_state, domains_from_config, file_name)
            [w_f3, n_e3, n_p] = beso_filters.prepare3_tetra_grid(file_name, cg, f_range, domains_to_filter)
            weight_factor3.append(w_f3)
            near_elm3.append(n_e3)
            near_points.append(n_p)
        elif ft[0] == "over nodes":
            beso_filters.check_same_state(domain_same_state, domains_from_config, file_name)
            [w_f_n, M_, w_f_d, n_n] = beso_filters.prepare1s(nodes, Elements, cg, f_range, domains_to_filter)
            weight_factor_node.append(w_f_n)
            M.append(M_)
            weight_factor_distance.append(w_f_d)
            near_nodes.append(n_n)
        elif ft[0] == "simple":
            [weight_factor2, near_elm] = beso_filters.prepare2s(cg, cg_min, cg_max, f_range, domains_to_filter,
                                                                weight_factor2, near_elm)
        elif ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
            near_elm = beso_filters.prepare_morphology(cg, cg_min, cg_max, f_range, domains_to_filter, near_elm)

# separating elements for reading nodal input
if reference_points == "nodes":
    beso_separate.separating(file_name, nodes)

# writing log table header
msg = "\n"
msg += "domain order: \n"
dorder = 0
for dn in domains_from_config:
    msg += str(dorder) + ") " + dn + "\n"
    dorder += 1
msg += "\n   i              mass"
if optimization_base == "stiffness":
    msg += "    ener_dens_mean"
if optimization_base == "heat":
    msg += "    heat_flux_mean"
if domain_FI_filled:
    msg += " FI_violated_0)"
    for dno in range(len(domains_from_config) - 1):
        msg += (" " + str(dno + 1)).rjust(4, " ") + ")"
    if len(domains_from_config) > 1:
        msg += " all)"
    msg += "          FI_mean    _without_state0         FI_max_0)"
    for dno in range(len(domains_from_config) - 1):
        msg += str(dno + 1).rjust(17, " ") + ")"
    if len(domains_from_config) > 1:
        msg += "all".rjust(17, " ") + ")"
if displacement_graph:
    for (ns, component) in displacement_graph:
        if component == "total":  # total displacement
            msg += (" " + ns + "(u_total)").rjust(18, " ")
        else:
            msg += (" " + ns + "(" + component + ")").rjust(18, " ")
if optimization_base == "buckling":
    msg += "  buckling_factors"

msg += "\n"
beso_lib.write_to_log(file_name, msg)

# preparing for writing quick results
file_name_resulting_states = os.path.join(path, "resulting_states")
[en_all_vtk, associated_nodes] = beso_lib.vtk_mesh(file_name_resulting_states, nodes, Elements)
# prepare for plotting
beso_plots.plotshow(domain_FI_filled, optimization_base, displacement_graph)

# ITERATION CYCLE
sensitivity_number = {}
sensitivity_number_old = {}
FI_max = []
FI_mean = []  # list of mean stress in every iteration
FI_mean_without_state0 = []  # mean stress without elements in state 0
energy_density_mean = []  # list of mean energy density in every iteration
heat_flux_mean = []  # list of mean heat flux in every iteration
FI_violated = []
disp_max = []
buckling_factors_all = []
i = 0
i_violated = 0
continue_iterations = True
check_tolerance = False
mass_excess = 0.0
elm_states_before_last = {}
elm_states_last = elm_states
oscillations = False

while True:
    # creating the new .inp file for CalculiX
    file_nameW = os.path.join(path, "file" + str(i).zfill(3))
    beso_lib.write_inp(file_name, file_nameW, elm_states, number_of_states, domains, domains_from_config,
                       domain_optimized, domain_thickness, domain_offset, domain_orientation, domain_material,
                       domain_volumes, domain_shells, plane_strain, plane_stress, axisymmetry, save_iteration_results,
                       i, reference_points, shells_as_composite, optimization_base, displacement_graph,
                       domain_FI_filled)
    # running CalculiX analysis
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        subprocess.call([os.path.normpath(path_calculix), file_nameW], cwd=path)
    else:
        subprocess.call([os.path.normpath(path_calculix), file_nameW], cwd=path, shell=True)

    # reading results and computing failure indices
    if (reference_points == "integration points") or (optimization_base == "stiffness") or \
            (optimization_base == "buckling") or (optimization_base == "heat"):  # from .dat file
        [FI_step, energy_density_step, disp_i, buckling_factors, energy_density_eigen, heat_flux] = \
            beso_lib.import_FI_int_pt(reference_value, file_nameW, domains, criteria, domain_FI, file_name, elm_states,
                                      domains_from_config, steps_superposition, displacement_graph)
    if reference_points == "nodes":  # from .frd file
        FI_step = beso_lib.import_FI_node(reference_value, file_nameW, domains, criteria, domain_FI, file_name,
                                          elm_states, steps_superposition)
        disp_i = beso_lib.import_displacement(file_nameW, displacement_graph, steps_superposition)
    disp_max.append(disp_i)

    # check if results were found
    missing_ccx_results = False
    if (optimization_base == "stiffness") and (not energy_density_step):
        missing_ccx_results = True
    elif (optimization_base == "buckling") and (not buckling_factors):
        missing_ccx_results = True
    elif (optimization_base == "heat") and (not heat_flux):
        missing_ccx_results = True
    elif domain_FI_filled and (not FI_step):
        missing_ccx_results = True
    if missing_ccx_results:
        msg = "CalculiX results not found, check CalculiX for errors."
        beso_lib.write_to_log(file_name, "\nERROR: " + msg + "\n")
        assert False, msg

    if domain_FI_filled:
        FI_max.append({})
        for dn in domains_from_config:
            FI_max[i][dn] = 0
            for en in domains[dn]:
                for sn in range(len(FI_step)):
                    try:
                        FI_step_en = list(filter(lambda a: a is not None, FI_step[sn][en]))  # drop None FI
                        FI_max[i][dn] = max(FI_max[i][dn], max(FI_step_en))
                    except ValueError:
                        msg = "FI_max computing failed. Check if each domain contains at least one failure criterion."
                        beso_lib.write_to_log(file_name, "\nERROR: " + msg + "\n")
                        raise Exception(msg)
                    except KeyError:
                        msg = "Some result values are missing. Check available disk space or steps_superposition " \
                              "settings"
                        beso_lib.write_to_log(file_name, "\nERROR: " + msg + "\n")
                        raise Exception(msg)
        print("FI_max, number of violated elements, domain name")

    # handling with more steps
    FI_step_max = {}  # maximal FI over all steps for each element in this iteration
    energy_density_enlist = {}   # {en1: [energy from sn1, energy from sn2, ...], en2: [], ...}
    FI_violated.append([])
    dno = 0
    for dn in domains_from_config:
        FI_violated[i].append(0)
        for en in domains[dn]:
            FI_step_max[en] = 0
            if optimization_base == "stiffness":
                energy_density_enlist[en] = []
            for sn in range(len(FI_step)):
                if domain_FI_filled:
                    FI_step_en = list(filter(lambda a: a is not None, FI_step[sn][en]))  # drop None FI
                    FI_step_max[en] = max(FI_step_max[en], max(FI_step_en))
                if optimization_base == "stiffness":
                    energy_density_enlist[en].append(energy_density_step[sn][en])
            if optimization_base == "stiffness":
                sensitivity_number[en] = max(energy_density_enlist[en])
            elif optimization_base == "heat":
                try:
                    sensitivity_number[en] = heat_flux[en] / volume_elm[en]
                except KeyError:
                    sensitivity_number[en] = heat_flux[en] / (area_elm[en] * domain_thickness[dn][elm_states[en]])
            elif optimization_base == "failure_index":
                sensitivity_number[en] = FI_step_max[en] / domain_density[dn][elm_states[en]]
            if domain_FI_filled:
                if FI_step_max[en] >= 1:
                    FI_violated[i][dno] += 1
        if domain_FI_filled:
            print(str(FI_max[i][dn]).rjust(15) + " " + str(FI_violated[i][dno]).rjust(4) + "   " + dn)
        dno += 1

    # buckling sensitivities
    if optimization_base == "buckling":
        # eigen energy density normalization
        #energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
        denominator = []  # normalization denominator for each buckling factor with numbering from 0
        for eigen_number in energy_density_eigen:  # numbering from 1
            denominator.append(max(energy_density_eigen[eigen_number].values()))
        bf_dif = {}
        bf_coef = {}
        buckling_influence_tolerance = 0.2  # Ki - K1 tolerance to influence sensitivity
        for bfn in range(len(buckling_factors) - 1):
            bf_dif_i = buckling_factors[bfn + 1] - buckling_factors[0]
            if bf_dif_i < buckling_influence_tolerance:
                bf_dif[bfn] = bf_dif_i
                bf_coef[bfn] = bf_dif_i / buckling_influence_tolerance
        for dn in domains_from_config:
            for en in domains[dn]:
                sensitivity_number[en] = energy_density_eigen[1][en] / denominator[0]
                for bfn in bf_dif:
                    sensitivity_number[en] += energy_density_eigen[bfn + 1][en] / denominator[bfn] * bf_coef[bfn]

    # filtering sensitivity number
    kp = 0
    kn = 0
    for ft in filter_list:
        if ft[0] and ft[1]:
            if ft[0] == "casting":
                if len(ft) == 3:
                    domains_to_filter = list(opt_domains)
                else:
                    domains_to_filter = []
                    for dn in ft[3:]:
                        domains_to_filter += domains[dn]
                sensitivity_number = beso_filters.run2_casting(sensitivity_number, above_elm, below_elm,
                                                               domains_to_filter)
                continue  # to evaluate other filters
            if len(ft) == 2:
                domains_to_filter = list(opt_domains)
            else:
                domains_to_filter = []
                for dn in ft[2:]:
                    domains_to_filter += domains[dn]
            if ft[0] == "over points":
                sensitivity_number = beso_filters.run3(sensitivity_number, weight_factor3[kp], near_elm3[kp],
                                                       near_points[kp])
                kp += 1
            elif ft[0] == "over nodes":
                sensitivity_number = beso_filters.run1(file_name, sensitivity_number, weight_factor_node[kn], M[kn],
                                                       weight_factor_distance[kn], near_nodes[kn], nodes,
                                                       domains_to_filter)
                kn += 1
            elif ft[0] == "simple":
                sensitivity_number = beso_filters.run2(file_name, sensitivity_number, weight_factor2, near_elm,
                                                       domains_to_filter)
            elif ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
                if ft[0].split()[1] == "sensitivity":
                    sensitivity_number = beso_filters.run_morphology(sensitivity_number, near_elm, domains_to_filter,
                                                                     ft[0].split()[0])

    if sensitivity_averaging:
        for en in opt_domains:
            # averaging with the last iteration should stabilize iterations
            if i > 0:
                sensitivity_number[en] = (sensitivity_number[en] + sensitivity_number_old[en]) / 2.0
            sensitivity_number_old[en] = sensitivity_number[en]  # for averaging in the next step

    # computing mean stress from maximums of each element in all steps in the optimization domain
    if domain_FI_filled:
        FI_mean_sum = 0
        FI_mean_sum_without_state0 = 0
        mass_without_state0 = 0
    if optimization_base == "stiffness":
        energy_density_mean_sum = 0  # mean of element maximums
    if optimization_base == "heat":
        heat_flux_mean_sum = 0
    for dn in domain_optimized:
        if domain_optimized[dn] is True:
            for en in domain_shells[dn]:
                mass_elm = domain_density[dn][elm_states[en]] * area_elm[en] * domain_thickness[dn][elm_states[en]]
                if domain_FI_filled:
                    FI_mean_sum += FI_step_max[en] * mass_elm
                    if elm_states[en] != 0:
                        FI_mean_sum_without_state0 += FI_step_max[en] * mass_elm
                        mass_without_state0 += mass_elm
                if optimization_base == "stiffness":
                    energy_density_mean_sum += max(energy_density_enlist[en]) * mass_elm
                if optimization_base == "heat":
                    heat_flux_mean_sum += heat_flux[en] * mass_elm
            for en in domain_volumes[dn]:
                mass_elm = domain_density[dn][elm_states[en]] * volume_elm[en]
                if domain_FI_filled:
                    FI_mean_sum += FI_step_max[en] * mass_elm
                    if elm_states[en] != 0:
                        FI_mean_sum_without_state0 += FI_step_max[en] * mass_elm
                        mass_without_state0 += mass_elm
                if optimization_base == "stiffness":
                    energy_density_mean_sum += max(energy_density_enlist[en]) * mass_elm
                if optimization_base == "heat":
                    heat_flux_mean_sum += heat_flux[en] * mass_elm
    if domain_FI_filled:
        FI_mean.append(FI_mean_sum / mass[i])
        print("FI_mean                = {}".format(FI_mean[i]))
        if mass_without_state0:
            FI_mean_without_state0.append(FI_mean_sum_without_state0 / mass_without_state0)
            print("FI_mean_without_state0 = {}".format(FI_mean_without_state0[i]))
        else:
            FI_mean_without_state0.append("NaN")
    if optimization_base == "stiffness":
        energy_density_mean.append(energy_density_mean_sum / mass[i])
        print("energy_density_mean    = {}".format(energy_density_mean[i]))
    if optimization_base == "heat":
        heat_flux_mean.append(heat_flux_mean_sum / mass[i])
        print("heat_flux_mean         = {}".format(heat_flux_mean[i]))

    if optimization_base == "buckling":
        k = 1
        for bf in buckling_factors:
            print("buckling factor K{} = {}".format(k, bf))
            k += 1
    # writing log table row
    msg = str(i).rjust(4, " ") + " " + str(mass[i]).rjust(17, " ") + " "
    if optimization_base == "stiffness":
        msg += " " + str(energy_density_mean[i]).rjust(17, " ")
    if optimization_base == "heat":
        msg += " " + str(heat_flux_mean[i]).rjust(17, " ")
    if domain_FI_filled:
        msg += str(FI_violated[i][0]).rjust(13, " ")
        for dno in range(len(domains_from_config) - 1):
            msg += " " + str(FI_violated[i][dno + 1]).rjust(4, " ")
        if len(domains_from_config) > 1:
            msg += " " + str(sum(FI_violated[i])).rjust(4, " ")
        msg += " " + str(FI_mean[i]).rjust(17, " ") + " " + str(FI_mean_without_state0[i]).rjust(18, " ")
        FI_max_all = 0
        for dn in domains_from_config:
            msg += " " + str(FI_max[i][dn]).rjust(17, " ")
            FI_max_all = max(FI_max_all, FI_max[i][dn])
        if len(domains_from_config) > 1:
            msg += " " + str(FI_max_all).rjust(17, " ")
    for cn in range(len(displacement_graph)):
        msg += " " + str(disp_i[cn]).rjust(17, " ")
    if optimization_base == "buckling":
        for bf in buckling_factors:
            msg += " " + str(bf).rjust(17, " ")
        buckling_factors_all.append(buckling_factors)
    msg += "\n"
    beso_lib.write_to_log(file_name, msg)

    # export element values
    if save_iteration_results and np.mod(float(i), save_iteration_results) == 0:
        if "csv" in save_resulting_format:
            beso_lib.export_csv(domains_from_config, domains, criteria, FI_step, FI_step_max, file_nameW, cg,
                                elm_states, sensitivity_number)
        if "vtk" in save_resulting_format:
            beso_lib.export_vtk(file_nameW, nodes, Elements, elm_states, sensitivity_number, criteria, FI_step,
                                FI_step_max)

    # relative difference in a mean stress for the last 5 iterations must be < tolerance
    if len(FI_mean) > 5:
        difference_last = []
        for last in range(1, 6):
            difference_last.append(abs(FI_mean[i] - FI_mean[i-last]) / FI_mean[i])
        difference = max(difference_last)
        if check_tolerance is True:
            print("maximum relative difference in FI_mean for the last 5 iterations = {}" .format(difference))
        if difference < tolerance:
            continue_iterations = False
        elif FI_mean[i] == FI_mean[i-1] == FI_mean[i-2]:
            continue_iterations = False
            print("FI_mean[i] == FI_mean[i-1] == FI_mean[i-2]")
    # relative difference in a mean energy density for the last 5 iterations must be < tolerance
    if len(energy_density_mean) > 5:
        difference_last = []
        for last in range(1, 6):
            difference_last.append(abs(energy_density_mean[i] - energy_density_mean[i - last]) / energy_density_mean[i])
        difference = max(difference_last)
        if check_tolerance is True:
            print("maximum relative difference in energy_density_mean for the last 5 iterations = {}".format(difference))
        if difference < tolerance:
            continue_iterations = False
        elif energy_density_mean[i] == energy_density_mean[i - 1] == energy_density_mean[i - 2]:
            continue_iterations = False
            print("energy_density_mean[i] == energy_density_mean[i-1] == energy_density_mean[i-2]")

    # finish or start new iteration
    if continue_iterations is False or i >= iterations_limit:
        if not(save_iteration_results and np.mod(float(i), save_iteration_results) == 0):
            if "csv" in save_resulting_format:
                beso_lib.export_csv(domains_from_config, domains, criteria, FI_step, FI_step_max, file_nameW, cg,
                                    elm_states, sensitivity_number)
            if "vtk" in save_resulting_format:
                beso_lib.export_vtk(file_nameW, nodes, Elements, elm_states, sensitivity_number, criteria, FI_step,
                                    FI_step_max)
        break
    # plot and save figures
    beso_plots.replot(path, i, oscillations, mass, domain_FI_filled, domains_from_config, FI_violated, FI_mean,
                      FI_mean_without_state0, FI_max, optimization_base, energy_density_mean, heat_flux_mean,
                      displacement_graph, disp_max, buckling_factors_all, savefig=True)
    i += 1  # iteration number
    print("\n----------- new iteration number %d ----------" % i)

    # set mass_goal for i-th iteration, check for number of violated elements
    if mass_removal_ratio - mass_addition_ratio > 0:  # removing from initial mass
        if sum(FI_violated[i - 1]) > sum(FI_violated[0]) + FI_violated_tolerance:
            if mass[i - 1] >= mass_goal_ratio * mass_full:
                mass_goal_i = mass[i - 1]  # use mass_new from previous iteration
            else:  # not to drop below goal mass
                mass_goal_i = mass_goal_ratio * mass_full
            if i_violated == 0:
                i_violated = i
                check_tolerance = True
        elif mass[i - 1] <= mass_goal_ratio * mass_full:  # goal mass achieved
            if not i_violated:
                i_violated = i  # to start decaying
                check_tolerance = True
            try:
                mass_goal_i
            except NameError:
                msg = "\nWARNING: mass goal is lower than initial mass. Check mass_goal_ratio."
                beso_lib.write_to_log(file_name, msg + "\n")
        else:
            mass_goal_i = mass_goal_ratio * mass_full
    else:  # adding to initial mass  TODO include stress limit
        if mass[i - 1] < mass_goal_ratio * mass_full:
            mass_goal_i = mass[i - 1] + (mass_addition_ratio - mass_removal_ratio) * mass_full
        elif mass[i - 1] >= mass_goal_ratio * mass_full:
            if not i_violated:
                i_violated = i  # to start decaying
                check_tolerance = True
            mass_goal_i = mass_goal_ratio * mass_full

    # switch element states
    if ratio_type == "absolute":
        mass_referential = mass_full
    elif ratio_type == "relative":
        mass_referential = mass[i - 1]
    [elm_states, mass] = beso_lib.switching(elm_states, domains_from_config, domain_optimized, domains, FI_step_max,
                                            domain_density, domain_thickness, domain_shells, area_elm, volume_elm,
                                            sensitivity_number, mass, mass_referential, mass_addition_ratio,
                                            mass_removal_ratio, compensate_state_filter, mass_excess, decay_coefficient,
                                            FI_violated, i_violated, i, mass_goal_i, domain_same_state)

    # filtering state
    mass_not_filtered = mass[i]  # use variable to store the "right" mass
    for ft in filter_list:
        if ft[0] and ft[1]:
            if ft[0] == "casting":
                continue  # to evaluate other filters
            if len(ft) == 2:
                domains_to_filter = list(opt_domains)
            else:
                domains_to_filter = []
                for dn in ft[2:]:
                    domains_to_filter += domains[dn]

            if ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
                if ft[0].split()[1] == "state":
                    # the same filter as for sensitivity numbers
                    elm_states_filtered = beso_filters.run_morphology(elm_states, near_elm, domains_to_filter,
                                                                      ft[0].split()[0], FI_step_max)
                    # compute mass difference
                    for dn in domains_from_config:
                        if domain_optimized[dn] is True:
                            for en in domain_shells[dn]:
                                if elm_states[en] != elm_states_filtered[en]:
                                    mass[i] += area_elm[en] * (
                                        domain_density[dn][elm_states_filtered[en]] * domain_thickness[dn][
                                                                                                elm_states_filtered[en]]
                                        - domain_density[dn][elm_states[en]] * domain_thickness[dn][elm_states[en]])
                                    elm_states[en] = elm_states_filtered[en]
                            for en in domain_volumes[dn]:
                                if elm_states[en] != elm_states_filtered[en]:
                                    mass[i] += volume_elm[en] * (
                                        domain_density[dn][elm_states_filtered[en]] - domain_density[dn][elm_states[en]])
                                    elm_states[en] = elm_states_filtered[en]
    print("mass = {}" .format(mass[i]))
    mass_excess = mass[i] - mass_not_filtered

    # export the present mesh
    beso_lib.append_vtk_states(file_name_resulting_states, i, en_all_vtk, elm_states)

    file_nameW2 = os.path.join(path, "file" + str(i).zfill(3))
    if save_iteration_results and np.mod(float(i), save_iteration_results) == 0:
        if "frd" in save_resulting_format:
            beso_lib.export_frd(file_nameW2, nodes, Elements, elm_states, number_of_states)
        if "inp" in save_resulting_format:
            beso_lib.export_inp(file_nameW2, nodes, Elements, elm_states, number_of_states)

    # check for oscillation state
    if elm_states_before_last == elm_states:  # oscillating state
        msg = "\nOSCILLATION: model turns back to " + str(i - 2) + "th iteration.\n"
        beso_lib.write_to_log(file_name, msg)
        print(msg)
        oscillations = True
        break
    elm_states_before_last = elm_states_last.copy()
    elm_states_last = elm_states.copy()

    # removing solver files
    if save_iteration_results and np.mod(float(i - 1), save_iteration_results) == 0:
        if "inp" not in save_solver_files:
            os.remove(file_nameW + ".inp")
        if "dat" not in save_solver_files:
            os.remove(file_nameW + ".dat")
        if "frd" not in save_solver_files:
            os.remove(file_nameW + ".frd")
        if "sta" not in save_solver_files:
            os.remove(file_nameW + ".sta")
        if "cvg" not in save_solver_files:
            os.remove(file_nameW + ".cvg")
        if "12d" not in save_solver_files:
            os.remove(file_nameW + ".12d")
    else:
        os.remove(file_nameW + ".inp")
        os.remove(file_nameW + ".dat")
        os.remove(file_nameW + ".frd")
        os.remove(file_nameW + ".sta")
        os.remove(file_nameW + ".cvg")
        os.remove(file_nameW + ".12d")

# export the resulting mesh
if not (save_iteration_results and np.mod(float(i), save_iteration_results) == 0):
    if "frd" in save_resulting_format:
        beso_lib.export_frd(file_nameW, nodes, Elements, elm_states, number_of_states)
    if "inp" in save_resulting_format:
        beso_lib.export_inp(file_nameW, nodes, Elements, elm_states, number_of_states)

# removing solver files
if "inp" not in save_solver_files:
    os.remove(file_nameW + ".inp")
    if reference_points == "nodes":
        os.remove(file_name[:-4] + "_separated.inp")
if "dat" not in save_solver_files:
    os.remove(file_nameW + ".dat")
if "frd" not in save_solver_files:
    os.remove(file_nameW + ".frd")
if "sta" not in save_solver_files:
    os.remove(file_nameW + ".sta")
if "cvg" not in save_solver_files:
    os.remove(file_nameW + ".cvg")
if "12d" not in save_solver_files:
    os.remove(file_nameW + ".12d")

# plot and save figures
beso_plots.replot(path, i, oscillations, mass, domain_FI_filled, domains_from_config, FI_violated, FI_mean,
                  FI_mean_without_state0, FI_max, optimization_base, energy_density_mean, heat_flux_mean,
                  displacement_graph, disp_max, buckling_factors_all, savefig=True,)
# print total time
total_time = time.time() - start_time
total_time_h = int(total_time / 3600.0)
total_time_min = int((total_time % 3600) / 60.0)
total_time_s = int(round(total_time % 60))
msg = "\n"
msg += ("Finished at  " + time.ctime() + "\n")
msg += ("Total time   " + str(total_time_h) + " h " + str(total_time_min) + " min " + str(total_time_s) + " s\n")
msg += "\n"
beso_lib.write_to_log(file_name, msg)
print("total time: " + str(total_time_h) + " h " + str(total_time_min) + " min " + str(total_time_s) + " s")
