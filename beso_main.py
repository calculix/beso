# optimization program using CalculiX solver
# BESO (Bi-directional Evolutionary Structural Optimization Method)

import numpy as np
import matplotlib.pyplot as plt
import multiprocessing
import os
import subprocess
import operator
import time
import beso_lib
plt.close(1)
start_time = time.time()

# initialization of variables
domain_optimized = {}
domain_density = {}
domain_thickness = {}
domain_offset = {}
domain_stress_allowable = {}
domain_material = {}
path = None
path_calculix = None
file_name = None
volume_goal = None
r_min = None
continue_from = None
cpu_cores = None
sigma_allowable_tolerance = None
use_filter = None
integration_points = None
evolutionary_volume_ratio = None
volume_additional_ratio_max = None
iterations_limit = None
tolerance = None
save_iteration_meshes = None

# read configuration file to fill variables listed above
execfile("beso_conf.py")
domains_from_config = domain_optimized.keys()

if iterations_limit == 0:  # automatic setting
    iterations_limit = int((1 - volume_goal) / evolutionary_volume_ratio + 25)
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
    msg += ("domain_stress_allowable = %s\n" % domain_stress_allowable[dn])
    msg += ("domain_material         = %s\n" % domain_material[dn])
    msg += "\n"
msg += ("volume_goal                 = %s\n" % volume_goal)
msg += ("cpu_cores                   = %s\n" % cpu_cores)
msg += ("sigma_allowable_tolerance   = %s\n" % sigma_allowable_tolerance)
msg += ("r_min                       = %s\n" % r_min)
msg += ("use_filter                  = %s\n" % use_filter)
msg += ("evolutionary_volume_ratio   = %s\n" % evolutionary_volume_ratio)
msg += ("volume_additional_ratio_max = %s\n" % volume_additional_ratio_max)
msg += ("iterations_limit            = %s\n" % iterations_limit)
msg += ("tolerance                   = %s\n" % tolerance)
msg += ("save_iteration_meshes       = %s\n" % save_iteration_meshes)
msg += "\n"
beso_lib.write_to_log(file_name, msg)

# mesh and domains importing
[nodes, Elements, domains, opt_domains, en_all] = beso_lib.import_inp(file_name, domains_from_config, domain_optimized)

switch_elm = {}  # initial full/void Elements
new_switch_elm = {}
if continue_from:
    for en in en_all:
        switch_elm[en] = 0
    switch_elm = beso_lib.frd_as_full(continue_from, switch_elm)
    new_switch_elm = switch_elm.copy()
else:
    for en in en_all:
        switch_elm[en] = 1
    new_switch_elm = switch_elm.copy()

# computing volume and centre of gravity of each element
[cg, cg_min, cg_max, volume_elm] = beso_lib.elm_volume_cg(file_name, nodes, Elements, domains_from_config,
                                                          domain_thickness, domains)
volume = [0.0]
volume_sum = 0
for en in opt_domains:  # in the zeroth iteration (for the optimization domain only)
    if switch_elm[en] == 1:
        volume[0] += volume_elm[en]
    volume_sum += volume_elm[en]
print("initial optimization domain volume %s" % volume[0])

# preparing parameters for filtering sensitivity numbers
if use_filter == 1:
    [weight_factor_node, M, weight_factor_distance, near_nodes] = beso_lib.filter_prepare1s(nodes, Elements, cg, r_min,
                                                                                            opt_domains)
elif use_filter == 2:
    [weight_factor2, near_elm] = beso_lib.filter_prepare2s(cg, cg_min, cg_max, r_min, opt_domains)
elif use_filter == 3:
    [weight_factor3, near_elm, near_points] = beso_lib.filter_prepare3(file_name, cg, cg_min, r_min, opt_domains)
elif use_filter in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
    near_elm = beso_lib.filter_prepare_morphology(cg, cg_min, cg_max, r_min, opt_domains)

# writing log table header
msg = "\n"
msg += "domain order: \n"
dorder = 0
for dn in domains_from_config:
    msg += str(dorder) + ") " + dn + "\n"
    dorder += 1
msg += "iteration,  volume, stresses:mean"
for dn in range(len(domains_from_config)):
    msg += ", " + "max".rjust(12, " ") + str(dn)
msg += "\n"
beso_lib.write_to_log(file_name, msg)

# ITERATION CYCLE
sensitivity_number = {}
sensitivity_number_opt = {}
sensitivity_number_old = {}
sigma_max = []
sigma_mean = []  # list of mean stress in every iteration
i = 0
continue_iterations = True
check_tolerance = False
volume_goal_backup = volume_goal

while True:
    # creating a new .inp file for CalculiX
    file_nameW = "file" + str(i).zfill(3)
    beso_lib.write_inp(file_name, file_nameW, switch_elm, domains, domains_from_config, domain_optimized,
                       domain_density, domain_thickness, domain_offset, domain_material)
    # running CalculiX analysis
    subprocess.call(os.path.normpath(path_calculix) + " " + os.path.join(path, file_nameW), shell=True)
    os.remove(file_nameW + ".inp")

    # reading von Mises stress
    try:
        if integration_points == "max":
            sigma_step = beso_lib.import_sigma_max(file_nameW + ".dat")
        elif integration_points == "average":
            sigma_step = beso_lib.import_sigma_average(file_nameW + ".dat")
    except:
        msg = "CalculiX results not found, check your inputs"
        beso_lib.write_to_log(file_name, "ERROR: " + msg + "\n")
        raise Exception(msg)
    os.remove(file_nameW + ".dat")
    os.remove(file_nameW + ".frd")
    os.remove(file_nameW + ".sta")
    os.remove(file_nameW + ".cvg")
    sigma_max.append({})
    print("sigma_max (by domain) =")
    for dn in domains_from_config:
        sigma_max[i][dn] = 0
        for en in domains[dn]:
            for sn in range(len(sigma_step)):
                sigma_max[i][dn] = max(sigma_max[i][dn], sigma_step[sn][en])
        print sigma_max[i][dn]

    # handling with more steps
    sigma_step_max = {}
    for dn in domains_from_config:
        for en in domains[dn]:
            sigma_step_max[en] = 0
            for sn in range(len(sigma_step)):
                sigma_step_max[en] = max(sigma_step[sn][en], sigma_step_max[en])
            sensitivity_number[en] = sigma_step_max[en] / domain_density[dn][0]  # TODO density of actual element state

    # filtering sensitivity number
    if use_filter == 1:
        sensitivity_number = beso_lib.filter_run1(file_name, sensitivity_number, weight_factor_node, M,
                                                  weight_factor_distance, near_nodes, nodes, opt_domains)
    elif use_filter == 2:
        sensitivity_number = beso_lib.filter_run2(file_name, sensitivity_number, weight_factor2, near_elm, opt_domains)
    elif use_filter == 3:
        sensitivity_number = beso_lib.filter_run3(sensitivity_number, weight_factor3, near_elm, near_points)
    elif use_filter in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
        sensitivity_number = beso_lib.filter_run_morphology(sensitivity_number, near_elm, opt_domains, use_filter)
    elif use_filter == 0:
        pass

    for en in opt_domains:
        # averaging with last iteration should stabilize iterations
        if i > 0:
            sensitivity_number[en] = (sensitivity_number[en] + sensitivity_number_old[en]) / 2.0
        sensitivity_number_old[en] = sensitivity_number[en]  # for averaging in the next step

    # computing mean stress from the full elements in optimization domain
    sigma_mean_sum = 0
    for en in opt_domains:
        if switch_elm[en] == 1:
            sigma_mean_sum += sigma_step_max[en] * volume_elm[en]  # mean sum from maximums of each element in all steps
    sigma_mean.append(sigma_mean_sum / volume[i])
    print("sigma_mean = %f" % sigma_mean[i])

    # writing log table row
    msg = str(i).rjust(3, " ") + ", " + str(volume[i]).rjust(13, " ") + ", " + str(sigma_mean[i]).rjust(13, " ")
    for dn in domains_from_config:
        msg += ", " + str(sigma_max[i][dn]).rjust(13, " ")
    msg += "\n"
    beso_lib.write_to_log(file_name, msg)

    # relative difference in a mean stress for the last 5 iterations must be < tolerance
    if (check_tolerance is True) and (len(sigma_mean) > 5):
        difference_last = []
        for last in range(1, 6):
            difference_last.append(abs(sigma_mean[i] - sigma_mean[i-last]) / sigma_mean[i])
        difference = max(difference_last)
        print("maximum relative difference in sigma_mean for the last 5 iterations = %f" % difference)
        if difference < tolerance:
            continue_iterations = False
        elif sigma_mean[i] == sigma_mean[i-1] == sigma_mean[i-2]:
            continue_iterations = False
            print("sigma_mean[i] == sigma_mean[i-1] == sigma_mean[i-2]")

    # start of the new iteration or finish of the iteration process
    if continue_iterations is False or i >= iterations_limit:
        break
    else:
        # export the present mesh
        if save_iteration_meshes and not np.mod(float(i-1), save_iteration_meshes) > 0:
            beso_lib.export_frd(file_nameW, nodes, Elements, switch_elm)
    i += 1  # iteration number
    print("----------- new iteration number %d ----------" % i)

    # fixing volume_goal
    can_defreeze = True
    freeze = False
    for dn in domains_from_config:
        sigma_allowable = domain_stress_allowable[dn]
        if sigma_allowable != [0]:
            if sigma_max[i-1][dn] > sigma_allowable:
                freeze = True
            elif sigma_max[i-1][dn] < (sigma_allowable - sigma_allowable_tolerance):
                pass
            else:
                can_defreeze = False
    if freeze is True:
        volume_goal = volume[i-1] / volume_sum
        check_tolerance = True
        print("volume_goal has been fixed at: %.s" % volume_goal)
    elif freeze is False and can_defreeze is True:
        if volume_goal != volume_goal_backup:
            volume_goal = volume_goal_backup
            print("volume_goal is back at initial value")

    # switching elements to 0 (void) or 1 (full)
    if volume[i-1] < volume_goal * volume_sum:  # add elements with maximal sensitivity_number
        volume_new = min(volume_goal * volume_sum, volume[i-1] + evolutionary_volume_ratio * volume_sum)
        check_tolerance = True
    else:  # remove elements with minimal sensitivity_number
        volume_new = max(volume_goal * volume_sum, volume[i-1] - evolutionary_volume_ratio * volume_sum)
        if volume_new == volume_goal * volume_sum:
            check_tolerance = True
    volume.append(0)
    volume_switched = 0
    for en in opt_domains:
        new_switch_elm[en] = 0
        sensitivity_number_opt[en] = sensitivity_number[en]
    # sorting elm_list by sensitivity number
    sensitivity_number_sorted = sorted(sensitivity_number_opt.items(), key=operator.itemgetter(1))
    while volume[i] < volume_new:
        en = sensitivity_number_sorted.pop()[0]
        if switch_elm[en] == 1:
            pass
        elif (switch_elm[en] == 0) and (volume_switched / volume_sum <= volume_additional_ratio_max):
            volume_switched += volume_elm[en]
        else:
            continue
        new_switch_elm[en] = 1
        volume[i] += volume_elm[en]
    switch_elm = new_switch_elm.copy()
    print("volume = %f" % volume[i])

# export the resulting mesh
beso_lib.export_frd(file_name, nodes, Elements, switch_elm)

# plotting sigma_mean and sigma_max during iterations
plt.figure(1)
plt.subplot2grid((1, 5), (0, 1), colspan=4)
plt.plot(range(i+1), sigma_mean, '--', label="mean")
dorder = 0
for dn in domains_from_config:  # TODO use domains_from_config for printing only
    sigma_max_dn = []
    for ii in range(i+1):
        sigma_max_dn.append(sigma_max[ii][dn])
    plt.plot(range(i+1), sigma_max_dn, label="max" + str(dorder))
    dorder += 1
plt.legend(bbox_to_anchor=(-0.45, 1), loc=2, title="Stresses")
plt.title("Maximal domain stresses,\n mean stress in all optimization domains")
plt.xlabel("Iteration")
plt.ylabel("Stress")
plt.grid()
plt.twinx()
plt.plot(volume, '+', label="volume")
plt.legend(bbox_to_anchor=(-0.45, 1), loc=3)
plt.ylabel("Volume changes in optimization domains")
plt.savefig("stresses_and_volume", dpi=150)
plt.show()

msg = "\n"
if volume_goal != volume_goal_backup:
    msg += ("volume_goal absolute value froze = %s\n" % volume_goal)
msg += ("Finish at                          " + time.ctime() + "\n")
msg += ("Total time                         " + str(time.time() - start_time) + " s\n")
msg += "\n"
beso_lib.write_to_log(file_name, msg)
print("total time: " + str(time.time() - start_time) + " s")
