# optimization program using CalculiX solver
# BESO (Bi-directional Evolutionary Structural Optimization Method)

import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import string
import operator
import time
import beso_lib
plt.close(1)
start_time = time.time()

# initialization of variables
domain_elset = []
domain_optimized = []
domain_E = []
domain_poisson = []
domain_density = []
domain_thickness = []
domain_offset = []
domain_stress_allowable = []
try: reload(beso_conf) # user inputs
except NameError: import beso_conf
[path, path_calculix, file_name, domain_elset, domain_optimized, domain_E, domain_poisson, domain_density, domain_thickness, domain_offset, domain_stress_allowable, volume_goal, r_min, sigma_allowable_tolerance, use_filter, evolutionary_volume_ratio, volume_additional_ratio_max, iterations_limit, tolerance, void_coefficient, save_iteration_meshes
    ] = beso_conf.inputs(
    domain_elset, domain_optimized, domain_E, domain_poisson, domain_density, domain_thickness, domain_offset, domain_stress_allowable)

if iterations_limit == 0: # automatic setting
    iterations_limit = int((1 - volume_goal) / evolutionary_volume_ratio + 25)
    print("iterations_limit set to %s" %iterations_limit)

# writing log file with settings
f_log = open(file_name[:-4] + ".log", "a")
f_log.write("------------------------------------\n")
f_log.write("Start at: " + time.ctime() + "\n")
f_log.write("\n")
for dn in range(len(domain_elset)):
    f_log.write("domain_elset = %s\n" %domain_elset[dn])
    f_log.write("domain_optimized = %s\n" %domain_optimized[dn])
    f_log.write("domain_E = %s\n" %domain_E[dn])
    f_log.write("domain_poisson = %s\n" %domain_poisson[dn])
    f_log.write("domain_density = %s\n" %domain_density[dn])
    f_log.write("domain_thickness = %s\n" %domain_thickness[dn])
    f_log.write("domain_offset = %s\n" %domain_offset[dn])
    f_log.write("domain_stress_allowable = %s\n" %domain_stress_allowable[dn])
    f_log.write("\n")
f_log.write("volume_goal initial = %s\n" %volume_goal)
f_log.write("sigma_allowable_tolerance = %s\n" %sigma_allowable_tolerance)
f_log.write("r_min = %s\n" %r_min)
f_log.write("use_filter = %s\n" %use_filter)
f_log.write("evolutionary_volume_ratio = %s\n" %evolutionary_volume_ratio)
f_log.write("volume_additional_ratio_max = %s\n" %volume_additional_ratio_max)
f_log.write("iterations_limit = %s\n" %iterations_limit)
f_log.write("tolerance = %s\n" %tolerance)
f_log.write("void_coefficient = %s\n" %void_coefficient)
f_log.write("save_iteration_meshes = %s\n" %save_iteration_meshes)
f_log.write("\n")

# mesh and domains importing
[nodes, elm_C3D4, elm_C3D10, elm_S3, elm_S6, domains, opt_domains, en_all] = beso_lib.import_inp(file_name, domain_elset, domain_optimized)
f_log.write("%.f nodes, %.f C3D4, %.f C3D10, %.f S3, %.f S6 have been imported\n" %(len(nodes), len(elm_C3D4), len(elm_C3D10), len(elm_S3), len(elm_S6)))

# computing a volume of each element in opt_domains
[volume_elm, volume_sum] = beso_lib.volume_full(nodes, elm_C3D4, elm_C3D10, elm_S3, elm_S6, domain_thickness, domains, opt_domains)
volume = [volume_sum] # in the first iteration (for the optimization domain only)
print("optimization domain volume %s" %volume_sum)

# computing centres of gravity of each element and elements associated to each node
[cg, cg_min, cg_max] = beso_lib.elm_cg(nodes, elm_C3D4, elm_C3D10, elm_S3, elm_S6, opt_domains)

# preparing parameters for filtering sensitivity numbers
if use_filter == 1:
    [weight_factor_node, M, weight_factor_distance, near_nodes] = beso_lib.filter_prepare1s(elm_C3D4, elm_C3D10, elm_S3, elm_S6, nodes, cg, r_min, opt_domains)
elif use_filter == 2:
    [weight_factor2, near_elm] = beso_lib.filter_prepare2s(cg, cg_min, cg_max, r_min, opt_domains)

switch_elm = {} # initial full volume for all elements
new_switch_elm = {}
for en in en_all:
    switch_elm[en] = 1
    new_switch_elm[en] = 1

# writing log table header
f_log.write("\n")
row = "iteration, volume, mean"
for dn in range(len(domains)):
    row += ", max" + str(dn)
f_log.write(row + "\n")

# ITERATION CYCLE
sensitivity_number = {}
sensitivity_number_opt = {}
sensitivity_number_old = {}
sigma_max = []
sigma_mean = [] # list of mean stress in every iteration
i = 0
continue_itarations = True
check_tolerance = False
volume_goal_backup = volume_goal

while True:
    # creating a new .inp file for CalculiX
    file_nameW = "file" + str(i).zfill(3)
    beso_lib.write_inp(file_name, file_nameW, switch_elm, domains, domain_optimized, domain_E, domain_poisson, domain_density, void_coefficient, domain_thickness, domain_offset)
    # running CalculiX analysis
    subprocess.call(path_calculix + " " + path + file_nameW, shell=True)
    os.remove(file_nameW + ".inp")

    # reading von Mises stress
    sigma_step = beso_lib.import_sigma(file_nameW + ".dat")
    os.remove(file_nameW + ".dat")
    os.remove(file_nameW + ".frd")
    os.remove(file_nameW + ".sta")
    sigma_max.append([])
    print("sigma_max (by domain) =")
    for dn in range(len(domains)):
        sigma_max[i].append(0)
        for en in domains[dn]:
            for sn in range(len(sigma_step)):
                sigma_max[i][dn] = max(sigma_max[i][dn], sigma_step[sn][en])
        print sigma_max[i][dn]

    # handling with more steps
    sigma_step_max = {}
    for dn in range(len(domains)):
        for en in domains[dn]:
            sigma_step_max[en] = 0
            for sn in range(len(sigma_step)):
                sigma_step_max[en] = max(sigma_step[sn][en], sigma_step_max[en])
            sensitivity_number[en] = sigma_step_max[en] / domain_density[dn]

    # filtering sensitivity number
    if use_filter == 1:
        sensitivity_number = beso_lib.filter_run1(sensitivity_number, weight_factor_node, M, weight_factor_distance, near_nodes, nodes, opt_domains)
    elif use_filter == 2:
        sensitivity_number = beso_lib.filter_run2(sensitivity_number, weight_factor2, near_elm, opt_domains)
    elif use_filter == 0:
        pass

    for en in opt_domains:
        # averaging with last iteration should stabilize iterations
        if i > 0:
            sensitivity_number[en] = (sensitivity_number[en] + sensitivity_number_old[en]) / 2.0
        sensitivity_number_old[en] = sensitivity_number[en] # for averaging in the next step

    # computing mean stress from the full elements in optimization domain
    sigma_mean_sum = 0
    for en in opt_domains:
        if switch_elm[en]==1:
            sigma_mean_sum += sigma_step_max[en] * volume_elm[en] # mean sum from maximums of each element in all steps
    sigma_mean.append(sigma_mean_sum / volume[i])
    print("sigma_mean = %f" %sigma_mean[i])
    
    # writing log table row
    row = str(i) + ", " + str(volume[i]) + ", " + str(sigma_mean[i])
    for dn in range(len(domains)):
        row += ", " + str(sigma_max[i][dn])
    f_log.write(row + "\n")

    # relative difference in a mean stress for the last 5 iterations must be < tolerance
    if check_tolerance == True :
        difference_last = []
        for last in range(1,6):
            difference_last.append( abs(sigma_mean[i] - sigma_mean[i-last]) / sigma_mean[i])
        difference = max(difference_last)
        print("maximum relative difference in sigma_mean for the last 5 iterations = %f" %difference)
        if difference < tolerance:
            continue_itarations = False
        elif sigma_mean[i] == sigma_mean[i-1] == sigma_mean[i-2]:
            continue_itarations = False
            print("sigma_mean[i] == sigma_mean[i-1] == sigma_mean[i-2]")

    # start of the new iteration or finish of the iteration process
    if continue_itarations == False or i >= iterations_limit:
        break
    else:
        # export the present mesh
        if save_iteration_meshes and not np.mod(float(i-1), save_iteration_meshes) > 0:
            beso_lib.export_frd(file_nameW, nodes, elm_C3D4, elm_C3D10, elm_S3, elm_S6, switch_elm)
    i += 1 # iteration number
    print("new iteration number %d" %i)

    # fixing volume_goal
    dn = -1
    can_defreeze = True
    freeze = False
    for sigma_allowable in domain_stress_allowable:
        dn += 1
        if sigma_allowable:
            if sigma_max[i-1][dn] > sigma_allowable:
                freeze = True
            elif sigma_max[i-1][dn] < (sigma_allowable - sigma_allowable_tolerance):
                pass
            else:
                can_defreeze = False
    if freeze == True:
        volume_goal = volume[i-1] / volume_sum
        check_tolerance = True
        print("volume_goal has been fixed at: %.s" %volume_goal)
    elif freeze == False and can_defreeze == True:
        if volume_goal <> volume_goal_backup:
            volume_goal = volume_goal_backup
            print("volume_goal is back at initial value")

    # switching elements to 0 (void) or 1 (full)
    if volume[i-1] < volume_goal * volume_sum: # add elements with maximal sensitivity_number
        volume_new = min(volume_goal * volume_sum, volume[i-1] + evolutionary_volume_ratio * volume_sum)
        check_tolerance = True
    else:# remove elements with minimal sensitivity_number
        volume_new = max(volume_goal * volume_sum, volume[i-1] - evolutionary_volume_ratio * volume_sum)
        if volume_new == volume_goal * volume_sum:
            check_tolerance = True
    volume.append(0)
    volume_switched = 0
    for en in opt_domains:
        new_switch_elm[en] = 0
        sensitivity_number_opt[en] = sensitivity_number[en]
    sensitivity_number_sorted = sorted(sensitivity_number_opt.items(), key=operator.itemgetter(1)) #sorting elm_list by sensitivity number
    highest_position = len(sensitivity_number_sorted) - 1
    while volume[i] < volume_new:
        en = sensitivity_number_sorted[highest_position][0]
        highest_position -= 1
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
beso_lib.export_frd(file_name, nodes, elm_C3D4, elm_C3D10, elm_S3, elm_S6, switch_elm)

# plotting sigma_mean and sigma_max during iterations
plt.figure(1)
plt.subplot2grid((1,5), (0,1), colspan = 4)
plt.plot(range(i+1), sigma_mean, '--', label = "mean")
for dn in range(len(domains)):
    sigma_max_dn = []
    for ii in range(i+1):
        sigma_max_dn.append(sigma_max[ii][dn])
    plt.plot(range(i+1), sigma_max_dn, label = "max" + str(dn))
plt.legend(bbox_to_anchor = (-0.45, 1), loc = 2, title = "Stresses")
plt.title("Maximal domain stresses,\n mean stress in all optimization domains")
plt.xlabel("Iteration")
plt.ylabel("Stress")
plt.grid()
plt.twinx()
plt.plot(volume, '+', label = "volume")
plt.legend(bbox_to_anchor = (-0.45, 1), loc = 3)
plt.ylabel("Volume changes in optimization domains")
plt.savefig("stresses_and_volume", dpi = 150)
plt.show()

f_log.write("\n")
if volume_goal <> volume_goal_backup:
    f_log.write("volume_goal freezed = %s\n" %volume_goal)
f_log.write("Finish at: " + time.ctime() + "\n")
f_log.write("Total time: " + str(time.time() - start_time) + " s\n")
f_log.write("\n\n")
f_log.close()
print("total time: " + str(time.time() - start_time) + " s\n")