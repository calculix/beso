# plotting graphs

import matplotlib.pyplot as plt
import os


def replot(path, i, oscillations, mass, domain_FI_filled, domains_from_config, FI_violated, FI_mean, FI_mean_without_state0,
           FI_max, optimization_base, energy_density_mean, heat_flux_mean, displacement_graph, disp_max,
           buckling_factors_all, savefig=False):
    """plot graphs with actual data"""
    fn = 0  # figure number
    # plot mass
    fn += 1
    plt.figure(fn)
    plt.cla()
    plt.plot(range(i+1), mass, label="mass")
    plt.title("Mass of optimization domains")
    plt.xlabel("Iteration")
    plt.ylabel("Mass")
    plt.grid()
    plt.tight_layout()
    plt.pause(0.0001)
    if savefig:
        plt.savefig(os.path.join(path, "Mass"))

    if oscillations is True:
        i_plot = i - 1  # because other values for i-th iteration are not evaluated
    else:
        i_plot = i

    if domain_FI_filled:  # FI contain something
        # plot number of elements with FI > 1
        fn += 1
        plt.figure(fn)
        plt.cla()
        dno = 0
        for dn in domains_from_config:
            FI_violated_dn = []
            for ii in range(i_plot + 1):
                FI_violated_dn.append(FI_violated[ii][dno])
            plt.plot(range(i_plot + 1), FI_violated_dn, label=dn)
            dno += 1
        if len(domains_from_config) > 1:
            FI_violated_total = []
            for ii in range(i_plot + 1):
                FI_violated_total.append(sum(FI_violated[ii]))
            plt.plot(range(i_plot+1), FI_violated_total, label="Total")
        plt.legend(loc=2, fontsize=10)
        plt.title("Number of elements with Failure Index >= 1")
        plt.xlabel("Iteration")
        plt.ylabel("FI_violated")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "FI_violated"))

        # plot mean failure index
        fn += 1
        plt.figure(fn)
        plt.cla()
        plt.plot(range(i_plot+1), FI_mean, label="all")
        plt.plot(range(i_plot+1), FI_mean_without_state0, label="without state 0")
        plt.title("Mean Failure Index weighted by element mass")
        plt.xlabel("Iteration")
        plt.ylabel("FI_mean")
        plt.legend(loc=2, fontsize=10)
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "FI_mean"))

        # plot maximal failure indices
        fn += 1
        plt.figure(fn)
        plt.cla()
        for dn in domains_from_config:
            FI_max_dn = []
            for ii in range(i_plot + 1):
                FI_max_dn.append(FI_max[ii][dn])
            plt.plot(range(i_plot + 1), FI_max_dn, label=dn)
        plt.legend(loc=2, fontsize=10)
        plt.title("Maximal domain Failure Index")
        plt.xlabel("Iteration")
        plt.ylabel("FI_max")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "FI_max"))

    if optimization_base == "stiffness":
        # plot mean energy density
        fn += 1
        plt.figure(fn)
        plt.cla()
        plt.plot(range(i_plot+1), energy_density_mean)
        plt.title("Mean Energy Density weighted by element mass")
        plt.xlabel("Iteration")
        plt.ylabel("energy_density_mean")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "energy_density_mean"))

    if optimization_base == "heat":
        # plot mean energy density
        fn += 1
        plt.figure(fn)
        plt.cla()
        plt.plot(range(i_plot+1), heat_flux_mean)
        plt.title("Mean Heat Flux weighted by element mass")
        plt.xlabel("Iteration")
        plt.ylabel("heat_flux_mean")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "heat_flux_mean"))

    if displacement_graph:
        fn += 1
        plt.figure(fn)
        plt.cla()
        for cn in range(len(displacement_graph)):
            disp_max_cn = []
            for ii in range(i_plot + 1):
                disp_max_cn.append(disp_max[ii][cn])
            plt.plot(range(i + 1), disp_max_cn, label=displacement_graph[cn][0] + "(" + displacement_graph[cn][1] + ")")
        plt.legend(loc=2, fontsize=10)
        plt.title("Node set maximal displacements")
        plt.xlabel("Iteration")
        plt.ylabel("Displacement")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "Displacement_max"))

    if optimization_base == "buckling":
        fn += 1
        plt.figure(fn)
        plt.cla()
        for bfn in range(len(buckling_factors_all[0])):
            buckling_factors_bfn = []
            for ii in range(i_plot + 1):
                buckling_factors_bfn.append(buckling_factors_all[ii][bfn])
            plt.plot(range(i_plot + 1), buckling_factors_bfn, label="mode " + str(bfn + 1))
        plt.legend(loc=2, fontsize=10)
        plt.title("Buckling factors")
        plt.xlabel("Iteration")
        plt.ylabel("buckling_factors")
        plt.grid()
        plt.tight_layout()
        plt.pause(0.0001)
        if savefig:
            plt.savefig(os.path.join(path, "buckling_factors"))
