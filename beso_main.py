# optimization program using CalculiX solver
# BESO (Bi-directional Evolutionary Structural Optimization Method)

import numpy as np
import matplotlib.pyplot as plt
import multiprocessing
import os
import subprocess
import time
import beso_lib
plt.close("all")
start_time = time.time()

# initialization of variables
domain_optimized = {}
domain_density = {}
domain_thickness = {}
domain_offset = {}  # TODO read offset from .inp file
domain_FI = {}
domain_material = {}
path = None
path_calculix = None
file_name = None
mass_goal_ratio = None
r_min = None
continue_from = None
filter_list = None
cpu_cores = None
# FI_tolerance = None
FI_violated_tolerance = None
decay_coefficient = None
filter_on_sensitivity = None
filter_on_state = None
same_state = None
max_or_average = None
mass_addition_ratio = None
mass_removal_ratio = None
sensitivity_averaging = None
iterations_limit = None
tolerance = None
save_iteration_results = None

# read configuration file to fill variables listed above
exec(open("beso_conf.py").read())
domains_from_config = domain_optimized.keys()
criteria = []
for dn in domain_FI:  # extracting each type of criteria
    for state in range(len(domain_FI[dn])):
        for dn_crit in domain_FI[dn][state]:
            if dn_crit not in criteria:
                criteria.append(dn_crit)

number_of_states = 0  # find number of states possible in elm_states
for dn in domains_from_config:
    number_of_states = max(number_of_states, len(domain_density[dn]))

if iterations_limit == 0:  # automatic setting
    iterations_limit = int((1 - mass_goal_ratio) / abs(mass_removal_ratio - mass_addition_ratio) + 25)
    print("iterations_limit set to %s" % iterations_limit)

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
    msg += ("domain_FI               = %s\n" % domain_FI[dn])
    msg += ("domain_material         = %s\n" % domain_material[dn])
    msg += "\n"
msg += ("mass_goal_ratio         = %s\n" % mass_goal_ratio)
msg += ("filter_list             = %s\n" % filter_list)
msg += ("cpu_cores               = %s\n" % cpu_cores)
# msg += ("FI_tolerance            = %s\n" % FI_tolerance)
msg += ("FI_violated_tolerance   = %s\n" % FI_violated_tolerance)
msg += ("decay_coefficient       = %s\n" % decay_coefficient)
msg += ("r_min                   = %s\n" % r_min)
msg += ("filter_on_sensitivity   = %s\n" % filter_on_sensitivity)
msg += ("filter_on_state         = %s\n" % filter_on_state)
msg += ("same_state              = %s\n" % same_state)
msg += ("mass_addition_ratio     = %s\n" % mass_addition_ratio)
msg += ("mass_removal_ratio      = %s\n" % mass_removal_ratio)
msg += ("sensitivity_averaging   = %s\n" % sensitivity_averaging)
msg += ("iterations_limit        = %s\n" % iterations_limit)
msg += ("tolerance               = %s\n" % tolerance)
msg += ("save_iteration_results  = %s\n" % save_iteration_results)
msg += "\n"
beso_lib.write_to_log(file_name, msg)

# mesh and domains importing
[nodes, Elements, domains, opt_domains, en_all] = beso_lib.import_inp(file_name, domains_from_config, domain_optimized)
domain_shells = {}
domain_volumes = {}
for dn in domains_from_config:  # distinguishing shell elements and volume elements
    domain_shells[dn] = set(domains[dn]).intersection(list(Elements.tria3.keys()) + list(Elements.tria6.keys()) +
                                                      list(Elements.quad4.keys()) + list(Elements.quad8.keys()))
    domain_volumes[dn] = set(domains[dn]).intersection(list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) +
                                                       list(Elements.hexa8.keys()) + list(Elements.hexa20.keys()) +
                                                       list(Elements.penta6.keys()) + list(Elements.penta15.keys()))

elm_states = {}  # initial element state

if continue_from:
    elm_states = beso_lib.import_frd_state(continue_from, elm_states, number_of_states, file_name)
else:
    for dn in domains_from_config:
        for en in domains[dn]:
            elm_states[en] = len(domain_density[dn]) - 1  # set to highest state

# computing volume or area, and centre of gravity of each element
[cg, cg_min, cg_max, volume_elm, area_elm] = beso_lib.elm_volume_cg(file_name, nodes, Elements)
mass = [0.0]
mass_full = 0  # sum from 0th list position TODO make it independent on starting elm_states?

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

# preparing parameters for filtering sensitivity numbers
if filter_on_sensitivity == 1:
    [weight_factor_node, M, weight_factor_distance, near_nodes] = beso_lib.filter_prepare1s(nodes, Elements, cg, r_min,
                                                                                            opt_domains)
elif filter_on_sensitivity == 2:
    [weight_factor2, near_elm] = beso_lib.filter_prepare2s(cg, cg_min, cg_max, r_min, opt_domains)
elif filter_on_sensitivity == 3:
    [weight_factor3, near_elm, near_points] = beso_lib.filter_prepare3(file_name, cg, cg_min, r_min, opt_domains)
elif (filter_on_sensitivity in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]
      ) or (filter_on_state in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]):
    near_elm = beso_lib.filter_prepare_morphology(cg, cg_min, cg_max, r_min, opt_domains)

for ft in filter_list:
    f_range = ft[1]
    if len(ft) == 2:
        domains_to_filter = list(opt_domains)
    else:
        domains_to_filter = []
        for dn in ft[2:]:
            domains_to_filter += domains[dn]
    if ft[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
        near_elm = beso_lib.filter_prepare_morphology(cg, cg_min, cg_max, f_range, opt_domains)

# writing log table header
msg = "\n"
msg += "domain order: \n"
dorder = 0
for dn in domains_from_config:
    msg += str(dorder) + ") " + dn + "\n"
    dorder += 1
msg += "\niteration,              mass, FI_violated 0)"
for dno in range(len(domains_from_config) - 1):
    msg += (" " + str(dno + 1)).rjust(4, " ") + ")"
msg += ",          FI_mean,     FI_max     0)"
for dno in range(len(domains_from_config) - 1):
    msg += str(dno + 1).rjust(18, " ") + ")"
msg += "\n"
beso_lib.write_to_log(file_name, msg)

# ITERATION CYCLE
sensitivity_number = {}
sensitivity_number_old = {}
FI_max = []
FI_mean = []  # list of mean stress in every iteration
FI_violated = []
i = 0
i_violated = 0
continue_iterations = True
check_tolerance = False
elm_states_before_last = {}
elm_states_last = elm_states

while True:
    # creating a new .inp file for CalculiX
    file_nameW = "file" + str(i).zfill(3)
    beso_lib.write_inp(file_name, file_nameW, elm_states, number_of_states, domains, domains_from_config,
                       domain_optimized, domain_thickness, domain_offset, domain_material, domain_volumes,
                       save_iteration_results, i)
    # running CalculiX analysis
    subprocess.call(os.path.normpath(path_calculix) + " " + os.path.join(path, file_nameW), shell=True)

    # reading .dat results and computing failure inceces
    FI_step = beso_lib.import_FI(max_or_average, file_nameW+".dat", domains, criteria, domain_FI, file_name, elm_states,
                                 domains_from_config)
    os.remove(file_nameW + ".inp")
    if save_iteration_results and not np.mod(float(i - 1), save_iteration_results) > 0:
        os.remove(file_nameW + ".dat")
        os.remove(file_nameW + ".frd")
    os.remove(file_nameW + ".sta")
    os.remove(file_nameW + ".cvg")
    FI_max.append({})
    print("FI_max ordered by domain =")
    for dn in domains_from_config:
        FI_max[i][dn] = 0
        for en in domains[dn]:
            for sn in range(len(FI_step)):
                try:
                    FI_step_en = list(filter(lambda a: a != None, FI_step[sn][en]))  # drop None FI
                    FI_max[i][dn] = max(FI_max[i][dn], max(FI_step_en))
                except ValueError:
                    msg = "FI_max computing failed. Check if each domain contains at least one failure criterion."
                    beso_lib.write_to_log(file_name, "ERROR: " + msg + "\n")
                    raise Exception(msg)
        print(FI_max[i][dn])

    # handling with more steps
    FI_step_max = {}  # maximal FI over all steps for each element in this iteration
    FI_violated.append([])
    dno = 0
    for dn in domains_from_config:
        FI_violated[i].append(0)
        for en in domains[dn]:
            FI_step_max[en] = 0
            for sn in range(len(FI_step)):
                FI_step_en = list(filter(lambda a: a != None, FI_step[sn][en]))  # drop None FI
                FI_step_max[en] = max(FI_step_max[en], max(FI_step_en))
            sensitivity_number[en] = FI_step_max[en] / domain_density[dn][elm_states[en]]
            if FI_step_max[en] >= 1:
                FI_violated[i][dno] += 1
        dno += 1

    # filtering sensitivity number
    if filter_on_sensitivity == 1:
        sensitivity_number = beso_lib.filter_run1(file_name, sensitivity_number, weight_factor_node, M,
                                                  weight_factor_distance, near_nodes, nodes, opt_domains)
    elif filter_on_sensitivity == 2:
        sensitivity_number = beso_lib.filter_run2(file_name, sensitivity_number, weight_factor2, near_elm, opt_domains)
    elif filter_on_sensitivity == 3:
        sensitivity_number = beso_lib.filter_run3(sensitivity_number, weight_factor3, near_elm, near_points)
    elif filter_on_sensitivity in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
        sensitivity_number = beso_lib.filter_run_morphology(sensitivity_number, near_elm, opt_domains,
                                                            filter_on_sensitivity)
    elif filter_on_sensitivity == 0:
        pass

    for ft in filter_list:
        if len(ft) == 2:
            domains_to_filter = list(opt_domains)
        else:
            domains_to_filter = []
            for dn in ft[2:]:
                domains_to_filter += domains[dn]
        if ft[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
            domains_en_in_state = [[]] * number_of_states
            for en in domains_to_filter:
                sn = elm_states[en]
                domains_en_in_state[sn].append(en)
            for sn in range(number_of_states):
                if domains_en_in_state[sn]:
                    sensitivity_number = beso_lib.filter_run_morphology(sensitivity_number, near_elm,
                                                                        domains_en_in_state[sn], ft[0])

    if sensitivity_averaging:
        for en in opt_domains:
            # averaging with the last iteration should stabilize iterations
            if i > 0:
                sensitivity_number[en] = (sensitivity_number[en] + sensitivity_number_old[en]) / 2.0
            sensitivity_number_old[en] = sensitivity_number[en]  # for averaging in the next step

    # computing mean stress from maximums of each element in all steps in the optimization domain
    FI_mean_sum = 0
    for dn in domain_optimized:
        if domain_optimized[dn] is True:
            for en in domain_shells[dn]:
                mass_elm = domain_density[dn][elm_states[en]] * area_elm[en] * domain_thickness[dn][elm_states[en]]
                FI_mean_sum += FI_step_max[en] * mass_elm
            for en in domain_volumes[dn]:
                mass_elm = domain_density[dn][elm_states[en]] * volume_elm[en]
                FI_mean_sum += FI_step_max[en] * mass_elm
    FI_mean.append(FI_mean_sum / mass[i])
    print("FI_mean = {}" .format(FI_mean[i]))

    # writing log table row
    msg = str(i).rjust(9, " ") + ", " + str(mass[i]).rjust(17, " ") + ", " + str(FI_violated[i][0]).rjust(13, " ")
    for dno in range(len(domains_from_config) - 1):
        msg += ", " + str(FI_violated[i][dno + 1]).rjust(3, " ")
    msg += ", " + str(FI_mean[i]).rjust(17, " ")
    for dn in domains_from_config:
        msg += ", " + str(FI_max[i][dn]).rjust(17, " ")
    msg += "\n"
    beso_lib.write_to_log(file_name, msg)

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

    # start of the new iteration or finish of the iteration process
    if continue_iterations is False or i >= iterations_limit:
        break
    else:
        # export the present mesh
        if save_iteration_results and not np.mod(float(i-1), save_iteration_results) > 0:
            beso_lib.export_frd("file" + str(i), nodes, Elements, elm_states, number_of_states)
    i += 1  # iteration number
    print("----------- new iteration number %d ----------" % i)

    # check for number of violated elements
    if sum(FI_violated[i - 1]) > sum(FI_violated[0]) + FI_violated_tolerance:
        mass_goal_i = mass[i - 1]  # use mass_new from previous iteration
        if i_violated == 0:
            i_violated = i
    elif mass[i - 1] <= mass_goal_ratio * mass_full:  # goal volume achieved
        if not i_violated:
            i_violated = i  # to start decaying
    else:
        mass_goal_i = mass_goal_ratio * mass_full

    # switch element states
    [elm_states, mass] = beso_lib.switching(elm_states, domains_from_config, domain_optimized, domains, FI_step_max,
                                            domain_density, domain_thickness, domain_shells, area_elm, volume_elm,
                                            sensitivity_number, mass, mass_full, mass_addition_ratio,
                                            mass_removal_ratio, decay_coefficient, FI_violated, i_violated, i,
                                            mass_goal_i)

    # check for oscillation state
    if elm_states_before_last == elm_states:  # oscillating state
        msg = "OSCILLATION: model turns back to " + str(i - 2) + "th iteration\n"
        beso_lib.write_to_log(file_name, msg)
        print(msg)
        continue_iterations = False
    elm_states_before_last = elm_states_last.copy()
    elm_states_last = elm_states.copy()

    # filtering state
    if filter_on_state in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
        # the same filter as for sensitivity numbers
        elm_states_filtered = beso_lib.filter_run_morphology(elm_states, near_elm, opt_domains, filter_on_state)
        # compute mass difference
        for dn in domains_from_config:
            if domain_optimized[dn] is True:
                for en in domain_shells[dn]:
                    if elm_states[en] != elm_states_filtered[en]:
                        mass[i] += area_elm[en] * (
                            domain_density[dn][elm_states_filtered[en]] * domain_thickness[dn][elm_states_filtered[en]]
                            - domain_density[dn][elm_states[en]] * domain_thickness[dn][elm_states[en]])
                        elm_states[en] = elm_states_filtered[en]
                for en in domain_volumes[dn]:
                    if elm_states[en] != elm_states_filtered[en]:
                        mass[i] += volume_elm[en] * (
                            domain_density[dn][elm_states_filtered[en]] - domain_density[dn][elm_states[en]])
                        elm_states[en] = elm_states_filtered[en]
    print("mass = {}" .format(mass[i]))

# export the resulting mesh
beso_lib.export_frd(file_name, nodes, Elements, elm_states, number_of_states)

msg = "\n"
msg += ("Finish at                          " + time.ctime() + "\n")
msg += ("Total time                         " + str(time.time() - start_time) + " s\n")
msg += "\n"
beso_lib.write_to_log(file_name, msg)
print("total time: " + str(time.time() - start_time) + " s")

# plot mass
plt.figure(1)
plt.plot(range(i+1), mass, label="mass")
plt.title("Mass of optimization domains")
plt.xlabel("Iteration")
plt.ylabel("Mass")
plt.grid()
plt.savefig("Mass", dpi=100)

# plot number of elements with FI > 1
plt.figure(2)
dno = 0
for dn in domains_from_config:
    FI_violated_dn = []
    for ii in range(i + 1):
        FI_violated_dn.append(FI_violated[ii][dno])
    plt.plot(range(i + 1), FI_violated_dn, label=dn)
    dno += 1
if len(domains_from_config) > 1:
    FI_violated_total = []
    for ii in range(i + 1):
        FI_violated_total.append(sum(FI_violated[ii]))
    plt.plot(range(i+1), FI_violated_total, label="Total")
plt.legend(loc=2, fontsize=10)
plt.title("Number of elements with Failure Index > 1")
plt.xlabel("Iteration")
plt.ylabel("FI_violated")
plt.grid()
plt.savefig("FI_violated", dpi=100)

# plot mean failure index
plt.figure(3)
plt.plot(range(i+1), FI_mean, label="mean")
plt.title("Mean Failure Index weighted by element mass")
plt.xlabel("Iteration")
plt.ylabel("FI_mean")
plt.grid()
plt.savefig("FI_mean", dpi=100)

# plot maximal failure indices
plt.figure(4)
for dn in domains_from_config:
    FI_max_dn = []
    for ii in range(i + 1):
        FI_max_dn.append(FI_max[ii][dn])
    plt.plot(range(i + 1), FI_max_dn, label=dn)
plt.legend(loc=2, fontsize=10)
plt.title("Maximal domain Failure Index")
plt.xlabel("Iteration")
plt.ylabel("FI_max")
plt.grid()
plt.savefig("FI_max", dpi=100)

plt.show()
