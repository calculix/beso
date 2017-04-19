import numpy as np
import operator


# function to print ongoing messages to the log file
def write_to_log(file_name, msg):
    f_log = open(file_name[:-4] + ".log", "a")
    f_log.write(msg)
    f_log.close()


# function importing a mesh consisting of nodes, volume and shell elements
def import_inp(file_name, domains_from_config, domain_optimized):
    nodes = {}  # dict with nodes position

    class Elements():
        tria3 = {}
        tria6 = {}
        quad4 = {}
        quad8 = {}
        tetra4 = {}
        tetra10 = {}
        hexa8 = {}
        hexa20 = {}
        penta6 = {}
        penta15 = {}

    all_tria3 = {}
    all_tria6 = {}
    all_quad4 = {}
    all_quad8 = {}
    all_tetra4 = {}
    all_tetra10 = {}
    all_hexa8 = {}
    all_hexa20 = {}
    all_penta6 = {}
    all_penta15 = {}

    model_definition = True
    domains = {}
    read_domain = False
    read_node = False
    elm_category = []
    elm_2nd_line = False
    elset_generate = False
    special_type = ""  # for plane strain, plane stress, or axisymmetry
    plane_strain = set()
    plane_stress = set()
    axisymmetry = set()

    f = open(file_name, "r")
    line = "\n"
    include = ""
    while line != "":
        if include:
            line = f_include.readline()
            if line == "":
                f_include.close()
                include = ""
                line = f.readline()
        else:
            line = f.readline()
        if line.strip() == '':
            continue
        elif line[0] == '*':  # start/end of a reading set
            if line[0:2] == '**':  # comments
                continue
            if line[:8].upper() == "*INCLUDE":
                start = 1 + line.index("=")
                include = line[start:].strip().strip('"')
                f_include = open(include, "r")
                continue
            read_node = False
            elm_category = []
            elm_2nd_line = False
            read_domain = False
            elset_generate = False

        # reading nodes
        if (line[:5].upper() == "*NODE") and (model_definition is True):
            read_node = True
        elif read_node is True:
            line_list = line.split(',')
            number = int(line_list[0])
            x = float(line_list[1])
            y = float(line_list[2])
            z = float(line_list[3])
            nodes[number] = [x, y, z]

        # reading elements
        elif line[:8].upper() == "*ELEMENT":
            current_elset = ""
            line_list = line[8:].upper().split(',')
            for line_part in line_list:
                if line_part.split('=')[0].strip() == "TYPE":
                    elm_type = line_part.split('=')[1].strip()
                elif line_part.split('=')[0].strip() == "ELSET":
                    current_elset = line_part.split('=')[1].strip().upper()

            if elm_type in ["S3", "CPS3", "CPE3", "CAX3"]:
                elm_category = all_tria3
                number_of_nodes = 3
            elif elm_type in ["S6", "CPS6", "CPE6", "CAX6"]:
                elm_category = all_tria6
                number_of_nodes = 6
            elif elm_type in ["S4", "S4R", "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R"]:
                elm_category = all_quad4
                number_of_nodes = 4
            elif elm_type in ["S8", "S8R", "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R"]:
                elm_category = all_quad8
                number_of_nodes = 8
            elif elm_type == "C3D4":
                elm_category = all_tetra4
                number_of_nodes = 4
            elif elm_type == "C3D10":
                elm_category = all_tetra10
                number_of_nodes = 10
            elif elm_type in ["C3D8", "C3D8R", "C3D8I"]:
                elm_category = all_hexa8
                number_of_nodes = 8
            elif elm_type in ["C3D20", "C3D20R", "C3D20RI"]:
                elm_category = all_hexa20
                number_of_nodes = 20
            elif elm_type == "C3D6":
                elm_category = all_penta6
                number_of_nodes = 6
            elif elm_type == "C3D15":
                elm_category = all_penta15
                number_of_nodes = 15
            if elm_type in ["CPE3", "CPE6", "CPE4", "CPE4R", "CPE8", "CPE8R"]:
                special_type = "plane strain"
            elif elm_type in ["CPS3", "CPS6", "CPS4", "CPS4R", "CPS8", "CPS8R"]:
                special_type = "plane stress"
            elif elm_type in ["CAX3", "CAX6", "CAX4", "CAX4R", "CAX8", "CAX8R"]:
                special_type = "axisymmetry"
            else:
                special_type = ""

        elif elm_category != []:
            line_list = line.split(',')
            if elm_2nd_line is False:
                en = int(line_list[0])  # element number
                elm_category[en] = []
                pos = 1
                if current_elset:  # save en to the domain
                    try:
                        domains[current_elset].append(en)
                    except KeyError:
                        domains[current_elset] = [en]
                if special_type == "plane strain":
                    plane_strain.add(en)
                elif special_type == "plane stress":
                    plane_stress.add(en)
                elif special_type == "axisymmetry":
                    axisymmetry.add(en)
            else:
                pos = 0
                elm_2nd_line = False
            for nn in range(pos, pos + number_of_nodes - len(elm_category[en])):
                try:
                    enode = int(line_list[nn])
                    elm_category[en].append(enode)
                except IndexError:
                    elm_2nd_line = True
                    break

        # reading domains from elset
        elif line[:6].upper() == "*ELSET":
            line_split_comma = line.split(",")
            if "=" in line_split_comma[1]:
                name_member = 1
                try:
                    if "GENERATE" in line_split_comma[2].upper():
                        elset_generate = True
                except IndexError:
                    pass
            else:
                name_member = 2
                if "GENERATE" in line_split_comma[1].upper():
                    elset_generate = True
            member_split = line_split_comma[name_member].split("=")
            current_elset = member_split[1].strip()
            try:
                domains[current_elset]
            except KeyError:
                domains[current_elset] = []
            if elset_generate is False:
                read_domain = True
        elif read_domain is True:
            for en in line.split(","):
                en = en.strip()
                if en.isdigit():
                    domains[current_elset].append(int(en))
                elif en.isalpha():  # else: en is name of a previous elset
                    domains[current_elset].extend(domains[en.upper()])
        elif elset_generate is True:
            line_split_comma = line.split(",")
            try:
                if line_split_comma[3]:
                    en_generated = list(range(int(line_split_comma[0]), int(line_split_comma[1]) + 1,
                                              int(line_split_comma[2])))
            except IndexError:
                en_generated = list(range(int(line_split_comma[0]), int(line_split_comma[1]) + 1))
            domains[current_elset].extend(en_generated)

        elif line[:5].upper() == "*STEP":
            model_definition = False
    f.close()

    en_all = []
    opt_domains = []
    for dn in domains_from_config:
        en_all.extend(domains[dn])
        if domain_optimized[dn] is True:
            opt_domains.extend(domains[dn])
    msg = ("domains: %.f\n" % len(domains_from_config))

    # only elements in domains_from_config are stored, the rest is discarded
    keys = set(en_all).intersection(set(all_tria3.keys()))
    Elements.tria3 = dict([(k, all_tria3[k]) for k in keys])
    keys = set(en_all).intersection(set(all_tria6.keys()))
    Elements.tria6 = dict([(k, all_tria6[k]) for k in keys])
    keys = set(en_all).intersection(set(all_quad4.keys()))
    Elements.quad4 = dict([(k, all_quad4[k]) for k in keys])
    keys = set(en_all).intersection(set(all_quad8.keys()))
    Elements.quad8 = dict([(k, all_quad8[k]) for k in keys])
    keys = set(en_all).intersection(set(all_tetra4.keys()))
    Elements.tetra4 = dict([(k, all_tetra4[k]) for k in keys])
    keys = set(en_all).intersection(set(all_tetra10.keys()))
    Elements.tetra10 = dict([(k, all_tetra10[k]) for k in keys])
    keys = set(en_all).intersection(set(all_hexa8.keys()))
    Elements.hexa8 = dict([(k, all_hexa8[k]) for k in keys])
    keys = set(en_all).intersection(set(all_hexa20.keys()))
    Elements.hexa20 = dict([(k, all_hexa20[k]) for k in keys])
    keys = set(en_all).intersection(set(all_penta6.keys()))
    Elements.penta6 = dict([(k, all_penta6[k]) for k in keys])
    keys = set(en_all).intersection(set(all_penta15.keys()))
    Elements.penta15 = dict([(k, all_penta15[k]) for k in keys])
    en_all = list(Elements.tria3.keys()) + list(Elements.tria6.keys()) + list(Elements.quad4.keys()) + \
             list(Elements.quad8.keys()) + list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) + \
             list(Elements.hexa8.keys()) + list(Elements.hexa20.keys()) + list(Elements.penta6.keys()) + \
             list(Elements.penta15.keys())

    msg += ("nodes  : %.f\nTRIA3  : %.f\nTRIA6  : %.f\nQUAD4  : %.f\nQUAD8  : %.f\nTETRA4 : %.f\nTETRA10: %.f\n"
           "HEXA8  : %.f\nHEXA20 : %.f\nPENTA6 : %.f\nPENTA15: %.f\n"
           % (len(nodes), len(Elements.tria3), len(Elements.tria6), len(Elements.quad4), len(Elements.quad8),
              len(Elements.tetra4), len(Elements.tetra10), len(Elements.hexa8), len(Elements.hexa20),
              len(Elements.penta6), len(Elements.penta15)))
    print(msg)
    write_to_log(file_name, msg)

    if not opt_domains:
        row = "None optimized domain has been found. Check your inputs."
        msg += ("ERROR: " + row + "\n")
        write_to_log(file_name, msg)
        assert False, row

    return nodes, Elements, domains, opt_domains, en_all, plane_strain, plane_stress, axisymmetry


# function for computing volumes or area (shell elements) and centres of gravity
# approximate for 2nd order elements!
def elm_volume_cg(file_name, nodes, Elements):
    u = [0.0, 0.0, 0.0]
    v = [0.0, 0.0, 0.0]
    w = [0.0, 0.0, 0.0]

    def tria_area_cg(nod):
        # compute volume
        for i in [0, 1, 2]:  # denote x, y, z directions
            u[i] = nodes[nod[2]][i] - nodes[nod[1]][i]
            v[i] = nodes[nod[0]][i] - nodes[nod[1]][i]
        area_tria = np.linalg.linalg.norm(np.cross(u, v)) / 2.0
        # compute centre of gravity
        x_cg = (nodes[nod[0]][0] + nodes[nod[1]][0] + nodes[nod[2]][0]) / 3.0
        y_cg = (nodes[nod[0]][1] + nodes[nod[1]][1] + nodes[nod[2]][1]) / 3.0
        z_cg = (nodes[nod[0]][2] + nodes[nod[1]][2] + nodes[nod[2]][2]) / 3.0
        cg_tria = [x_cg, y_cg, z_cg]
        return area_tria, cg_tria

    def tetra_volume_cg(nod):
        # compute volume
        for i in [0, 1, 2]:  # denote x, y, z directions
            u[i] = nodes[nod[2]][i] - nodes[nod[1]][i]
            v[i] = nodes[nod[3]][i] - nodes[nod[1]][i]
            w[i] = nodes[nod[0]][i] - nodes[nod[1]][i]
            volume_tetra = abs(np.dot(np.cross(u, v), w)) / 6.0
        # compute centre of gravity
        x_cg = (nodes[nod[0]][0] + nodes[nod[1]][0] + nodes[nod[2]][0] + nodes[nod[3]][0]) / 4.0
        y_cg = (nodes[nod[0]][1] + nodes[nod[1]][1] + nodes[nod[2]][1] + nodes[nod[3]][1]) / 4.0
        z_cg = (nodes[nod[0]][2] + nodes[nod[1]][2] + nodes[nod[2]][2] + nodes[nod[3]][2]) / 4.0
        cg_tetra = [x_cg, y_cg, z_cg]
        return volume_tetra, cg_tetra

    def second_order_warning(elm_type):
        msg = "WARNING: areas and centres of gravity of " + elm_type.upper() + " elements ignore mid-nodes' positions\n"
        print(msg)
        write_to_log(file_name, msg)

    # defining volume and centre of gravity for all element types
    volume_elm = {}
    area_elm = {}
    cg = {}

    for en, nod in Elements.tria3.items():
        [area_elm[en], cg[en]] = tria_area_cg(nod)

    if Elements.tria6:
        second_order_warning("tria6")
    for en, nod in Elements.tria6.items():  # copy from tria3
        [area_elm[en], cg[en]] = tria_area_cg(nod)

    for en, nod in Elements.quad4.items():
        [a1, cg1] = tria_area_cg(nod[0:3])
        [a2, cg2] = tria_area_cg(nod[0:1] + nod[2:4])
        area_elm[en] = float(a1 + a2)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (a1 * cg1[k] + a2 * cg2[k]) / area_elm[en]

    if Elements.quad8:
        second_order_warning("quad8")
    for en, nod in Elements.quad8.items():  # copy from quad4
        [a1, cg1] = tria_area_cg(nod[0:3])
        [a2, cg2] = tria_area_cg(nod[0:1] + nod[2:4])
        area_elm[en] = float(a1 + a2)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (a1 * cg1[k] + a2 * cg2[k]) / area_elm[en]

    for en, nod in Elements.tetra4.items():
        [volume_elm[en], cg[en]] = tetra_volume_cg(nod)

    if Elements.tetra10:
        second_order_warning("tetra10")
    for en, nod in Elements.tetra10.items():  # copy from tetra4
        [volume_elm[en], cg[en]] = tetra_volume_cg(nod)

    for en, nod in Elements.hexa8.items():
        [v1, cg1] = tetra_volume_cg(nod[0:3] + nod[5:6])
        [v2, cg2] = tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
        [v3, cg3] = tetra_volume_cg(nod[2:3] + nod[4:7])
        [v4, cg4] = tetra_volume_cg(nod[0:1] + nod[2:5])
        [v5, cg5] = tetra_volume_cg(nod[3:5] + nod[6:8])
        [v6, cg6] = tetra_volume_cg(nod[2:5] + nod[6:7])
        volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k] + v4 * cg4[k] + v5 * cg5[k] + v6 * cg6[k]
                         ) / volume_elm[en]

    if Elements.hexa20:
        second_order_warning("hexa20")
    for en, nod in Elements.hexa20.items():  # copy from hexa8
        [v1, cg1] = tetra_volume_cg(nod[0:3] + nod[5:6])
        [v2, cg2] = tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
        [v3, cg3] = tetra_volume_cg(nod[2:3] + nod[4:7])
        [v4, cg4] = tetra_volume_cg(nod[0:1] + nod[2:5])
        [v5, cg5] = tetra_volume_cg(nod[3:5] + nod[6:8])
        [v6, cg6] = tetra_volume_cg(nod[2:5] + nod[6:7])
        volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k] + v4 * cg4[k] + v5 * cg5[k] + v6 * cg6[k]
                         ) / volume_elm[en]

    for en, nod in Elements.penta6.items():
        [v1, cg1] = tetra_volume_cg(nod[0:4])
        [v2, cg2] = tetra_volume_cg(nod[1:5])
        [v3, cg3] = tetra_volume_cg(nod[2:6])
        volume_elm[en] = float(v1 + v2 + v3)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k]) / volume_elm[en]

    if Elements.penta15:
        second_order_warning("penta15")  # copy from penta6
    for en, nod in Elements.penta15.items():
        [v1, cg1] = tetra_volume_cg(nod[0:4])
        [v2, cg2] = tetra_volume_cg(nod[1:5])
        [v3, cg3] = tetra_volume_cg(nod[2:6])
        volume_elm[en] = float(v1 + v2 + v3)
        cg[en] = [[], [], []]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k]) / volume_elm[en]

    # finding the minimum and maximum cg position
    x_cg = []
    y_cg = []
    z_cg = []
    for xyz in cg.values():
        x_cg.append(xyz[0])
        y_cg.append(xyz[1])
        z_cg.append(xyz[2])
    cg_min = [min(x_cg), min(y_cg), min(z_cg)]
    cg_max = [max(x_cg), max(y_cg), max(z_cg)]

    return cg, cg_min, cg_max, volume_elm, area_elm


# function for copying .inp file with additional elsets, materials, solid and shell sections, different output request
# elm_states is a dict of the elements containing 0 for void element or 1 for full element
def write_inp(file_name, file_nameW, elm_states, number_of_states, domains, domains_from_config, domain_optimized,
              domain_thickness, domain_offset, domain_material, domain_volumes, domain_shells, plane_strain,
              plane_stress, axisymmetry, save_iteration_results, i):
    fR = open(file_name, "r")
    fW = open(file_nameW + ".inp", "w")
    elsets_done = 0
    sections_done = 0
    outputs_done = 1
    commenting = False
    elset_new = {}
    elsets_used = {}
    msg_error = ""

    # function for writing ELSETs of each state
    def write_elset():
        fW.write(" \n")
        fW.write("** Added ELSETs by optimization:\n")
        for dn in domains_from_config:
            if domain_optimized[dn] is True:
                elsets_used[dn] = []
                elset_new[dn] = {}
                for sn in range(number_of_states):
                    elset_new[dn][sn] = []
                    for en in domains[dn]:
                        if elm_states[en] == sn:
                            elset_new[dn][elm_states[en]].append(en)
                for sn, en_list in elset_new[dn].items():
                    if en_list:
                        elsets_used[dn].append(sn)
                        fW.write("*ELSET,ELSET=" + dn + str(sn) + "\n")
                        position = 0
                        for en in en_list:
                            if position < 8:
                                fW.write(str(en) + ", ")
                                position += 1
                            else:
                                fW.write(str(en) + ",\n")
                                position = 0
                        fW.write("\n")
        fW.write(" \n")

    for line in fR:
        if line[0] == "*":
            commenting = False

        # writing ELSETs
        if (line[:6].upper() == "*ELSET" and elsets_done == 0) or (line[:5].upper() == "*STEP" and elsets_done == 0):
            write_elset()
            elsets_done = 1

        # optimization materials, solid and shell sections
        if line[:5].upper() == "*STEP" and sections_done == 0:
            if elsets_done == 0:
                write_elset()
                elsets_done = 1

            fW.write(" \n")
            fW.write("** Materials and sections in optimized domains\n")
            fW.write("** (redefines elements properties defined above):\n")
            for dn in domains_from_config:
                if domain_optimized[dn]:
                    for sn in elsets_used[dn]:
                        fW.write("*MATERIAL, NAME=" + dn + str(sn) + "\n")
                        fW.write(domain_material[dn][sn] + "\n\n")
                        if domain_volumes[dn]:
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) + "\n")
                        elif len(plane_strain.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) + "\n")
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        elif plane_strain.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only plane strain types for 2D elements"
                        elif len(plane_stress.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) + "\n")
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        elif plane_stress.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only plane stress types for 2D elements"
                        elif len(axisymmetry.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) + "\n")
                        elif axisymmetry.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only axisymmetry types for 2D elements"
                        else:
                            fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) +
                                     ", OFFSET=" + str(domain_offset[dn]) + "\n")
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        fW.write(" \n")
                        if msg_error:
                            write_to_log(file_name, "ERROR: " + msg_error + "\n")
                            raise Exception(msg_error)
            sections_done = 1

        if line[:5].upper() == "*STEP":
            outputs_done -= 1

        # output request only for element stresses in .dat file:
        if line[0:10].upper() == "*NODE FILE" or line[0:8].upper() == "*EL FILE" or \
                        line[0:13].upper() == "*CONTACT FILE" or line[0:11].upper() == "*NODE PRINT" or \
                        line[0:9].upper() == "*EL PRINT" or line[0:14].upper() == "*CONTACT PRINT":
            if outputs_done < 1:
                fW.write(" \n")
                for dn in domains_from_config:
                    fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                    fW.write("S\n")
                fW.write(" \n")
                outputs_done += 1
            commenting = True
            if not save_iteration_results or np.mod(float(i - 1), save_iteration_results) != 0:
                continue
        elif commenting is True:
            if not save_iteration_results or np.mod(float(i - 1), save_iteration_results) != 0:
                continue

        fW.write(line)
    fR.close()
    fW.close()


# function for importing results from .dat file
# Failure Indices are computed at each integration point and maximum or average above each element is yielded
def import_FI(max_or_average, file_nameW, domains, criteria, domain_FI, file_name, elm_states, domains_from_config):
    try:
        f = open(file_nameW, "r")
    except IOError:
        msg = "CalculiX results not found, check your inputs"
        write_to_log(file_name, "ERROR: " + msg + "\n")
        assert False, msg
    last_time = "initial"  # TODO solve how to read a new step which differs in time
    step_number = -1
    FI_step_template = {}  # {en1: numbers of applied critera, en2: [], ...}
    FI_step = []  # list for steps - [{en1: list for criteria FI, en2: [], ...}, {en1: [], en2: [], ...}, next step]

    # prepare FI dict from failure criteria
    for dn in domain_FI:
        for en in domains[dn]:
            cr = []
            for dn_crit in domain_FI[dn][elm_states[en]]:
                cr.append(criteria.index(dn_crit))
            FI_step_template[en] = cr

    def compute_FI():  # for the actual integration point
        sxx = float(line_split[2])
        syy = float(line_split[3])
        szz = float(line_split[4])
        sxy = float(line_split[5])
        sxz = float(line_split[6])
        syz = float(line_split[7])
        for FIn in FI_step_template[en]:
            if criteria[FIn][0] == "stress_von_Mises":
                s_allowable = criteria[FIn][1]
                FI_int_pt[FIn].append(np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                                                     6 * (sxy ** 2 + syz ** 2 + sxz ** 2))) / s_allowable)
            elif criteria[FIn][0] == "user_def":
                FI_int_pt[FIn].append(eval(criteria[FIn][0]))

    def save_FI():
        FI_step[step_number][en_last] = []
        for FIn in range(len(criteria)):
            FI_step[step_number][en_last].append(None)
            if FIn in FI_step_template[en_last]:
                if max_or_average == "max":
                    FI_step[step_number][en_last][FIn] = max(FI_int_pt[FIn])
                elif max_or_average == "average":
                    FI_step[step_number][en_last][FIn] = np.average(FI_int_pt[FIn])

    read_stresses = 0
    for line in f:
        line_split = line.split()
        if line == "\n":
            if read_stresses == 1:
                save_FI()
            read_stresses -= 1
            FI_int_pt = [[]] * len(criteria)
            en_last = None
        elif line[:9] == " stresses":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_stresses = 2
                if last_time != line_split[-1]:
                    step_number += 1
                    FI_step.append({})
                    last_time = line_split[-1]
        elif read_stresses == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    save_FI()
                    FI_int_pt = [[]] * len(criteria)
                en_last = en
            compute_FI()
    if read_stresses == 1:
        save_FI()
    f.close()
    return FI_step


# function for switch element states
def switching(elm_states, domains_from_config, domain_optimized, domains, FI_step_max, domain_density, domain_thickness,
              domain_shells, area_elm, volume_elm, sensitivity_number, mass, mass_referential, mass_addition_ratio,
              mass_removal_ratio, decay_coefficient, FI_violated, i_violated, i, mass_goal_i):
    mass_increase = {}
    mass_decrease = {}
    sensitivity_number_opt = {}
    mass.append(0)
    mass_overloaded = 0.0
    # switch up overloaded elements
    for dn in domains_from_config:
        if domain_optimized[dn] is True:
            for en in domains[dn]:
                if FI_step_max[en] >= 1:  # increase state if it is not highest
                    en_added = False
                    if elm_states[en] < len(domain_density[dn]) - 1:
                        elm_states[en] += 1
                        en_added = True
                    if en in domain_shells[dn]:
                        mass[i] += area_elm[en] * domain_density[dn][elm_states[en]] * domain_thickness[
                            dn][elm_states[en]]
                        if en_added is True:
                            mass_difference = area_elm[en] * (
                                domain_density[dn][elm_states[en]] * domain_thickness[dn][elm_states[en]] -
                                domain_density[dn][elm_states[en] - 1] * domain_thickness[dn][elm_states[en] - 1])
                            mass_overloaded += mass_difference
                            mass_goal_i += mass_difference
                    else:
                        mass[i] += volume_elm[en] * domain_density[dn][elm_states[en]]
                        if en_added is True:
                            mass_difference = volume_elm[en] * (
                                domain_density[dn][elm_states[en]] - domain_density[dn][elm_states[en] - 1])
                            mass_overloaded += mass_difference
                            mass_goal_i += mass_difference
                else:  # rest of elements prepare to sorting and switching
                    if en in domain_shells[dn]:  # shells
                        mass[i] += area_elm[en] * domain_density[dn][elm_states[en]] * domain_thickness[
                            dn][elm_states[en]]
                        if elm_states[en] != 0:  # for potential switching down
                            mass_decrease[en] = area_elm[en] * (
                                domain_density[dn][elm_states[en]] * domain_thickness[dn][elm_states[en]] -
                                domain_density[dn][elm_states[en] - 1] * domain_thickness[dn][elm_states[en] - 1])
                        if elm_states[en] < len(domain_density[dn]) - 1:  # for potential switching up
                            mass_increase[en] = area_elm[en] * (
                                domain_density[dn][elm_states[en] + 1] * domain_thickness[dn][elm_states[en] + 1] -
                                domain_density[dn][elm_states[en]] * domain_thickness[dn][elm_states[en]])
                    else:  # volumes
                        mass[i] += volume_elm[en] * domain_density[dn][elm_states[en]]
                        if elm_states[en] != 0:  # for potential switching down
                            mass_decrease[en] = volume_elm[en] * (
                                domain_density[dn][elm_states[en]] - domain_density[dn][elm_states[en] - 1])
                        if elm_states[en] < len(domain_density[dn]) - 1:  # for potential switching up
                            mass_increase[en] = volume_elm[en] * (
                                domain_density[dn][elm_states[en] + 1] - domain_density[dn][elm_states[en]])
                    sensitivity_number_opt[en] = sensitivity_number[en]
    # sorting
    sensitivity_number_sorted = sorted(sensitivity_number_opt.items(), key=operator.itemgetter(1))
    sensitivity_number_sorted2 = list(sensitivity_number_sorted)
    if i_violated:
        mass_to_add = mass_addition_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated))
        if sum(FI_violated[i - 1]):
            mass_to_remove = mass_addition_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated)) \
                             - mass_overloaded
        else:
            mass_to_remove = mass_removal_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated)) \
                             - mass_overloaded
    else:
        mass_to_add = mass_addition_ratio * mass_referential
        mass_to_remove = mass_removal_ratio * mass_referential
    mass_added = mass_overloaded
    mass_removed = 0.0
    # if mass_goal_i < mass[i - 1]:  # going from bigger mass to lower
    added_elm = []
    while mass_added < mass_to_add:
        if sensitivity_number_sorted:
            en = sensitivity_number_sorted.pop(-1)[0]  # highest sensitivity number
            try:
                mass[i] += mass_increase[en]
                mass_added += mass_increase[en]
                elm_states[en] += 1
                added_elm.append(en)
            except KeyError:  # there is no mass_increase due to highest element state
                pass
        else:
            break
    popped = 0
    while mass_removed < mass_to_remove:
        if mass[i] <= mass_goal_i:
            break
        if sensitivity_number_sorted:
            en = sensitivity_number_sorted.pop(0)[0]  # lowest sensitivity number
            popped += 1
            if elm_states[en] != 0:
                mass[i] -= mass_decrease[en]
                mass_removed += mass_decrease[en]
                elm_states[en] -= 1
        else:
            try:
                en = sensitivity_number_sorted2[popped][0]
                popped += 1
            except IndexError:
                break
            if elm_states[en] != 0:
                elm_states[en] -= 1
                if en in added_elm:
                    mass[i] -= mass_increase[en]
                    mass_removed += mass_increase[en]
                else:
                    mass[i] -= mass_decrease[en]
                    mass_removed += mass_decrease[en]
    return elm_states, mass


# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
def export_frd(file_name, nodes, Elements, elm_states, number_of_states):

    def get_associated_nodes(elm_category):
        for en in elm_category:
            if elm_states[en] == state:
                associated_nodes.extend(elm_category[en])

    def write_elm(elm_category, category_symbol):
        for en in elm_category:
            if elm_states[en] == state:
                f.write(" -1" + str(en).rjust(10, " ") + category_symbol.rjust(5, " ") + "\n")
                line = ""
                nodes_done = 0
                if category_symbol == "4":  # hexa20 different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                               10, 11, 16, 17, 18, 19, 12, 13, 14, 15]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10, " ")
                        if np in [9, 15]:
                            f.write(" -2" + line + "\n")
                            line = ""
                elif category_symbol == "5":  # penta15 has different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12,
                               13, 14, 9, 10, 11]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10, " ")
                        if np in [12, 11]:
                            f.write(" -2" + line + "\n")
                            line = ""
                else:
                    for nn in elm_category[en]:
                        line += str(nn).rjust(10, " ")
                        nodes_done += 1
                        if nodes_done == 10 and elm_category != Elements.tetra10:
                            f.write(" -2" + line + "\n")
                            line = ""
                    f.write(" -2" + line + "\n")

    # find all possible states in elm_states and run separately for each of them
    for state in range(number_of_states):
        if file_name[-4:] == ".inp":
            new_name = file_name[:-4] + "_res_mesh" + str(state) + ".frd"
        else:
            new_name = file_name + "_res_mesh" + str(state) + ".frd"
        f = open(new_name, "w")

        # print nodes
        associated_nodes = []
        get_associated_nodes(Elements.tria3)
        get_associated_nodes(Elements.tria6)
        get_associated_nodes(Elements.quad4)
        get_associated_nodes(Elements.quad8)
        get_associated_nodes(Elements.tetra4)
        get_associated_nodes(Elements.tetra10)
        get_associated_nodes(Elements.penta6)
        get_associated_nodes(Elements.penta15)
        get_associated_nodes(Elements.hexa8)
        get_associated_nodes(Elements.hexa20)

        associated_nodes = sorted(list(set(associated_nodes)))
        f.write("    1C\n")
        f.write("    2C" + str(len(associated_nodes)).rjust(30, " ") + 37 * " " + "1\n")
        for nn in associated_nodes:
            f.write(" -1" + str(nn).rjust(10, " ") + "% .5E% .5E% .5E\n" % (nodes[nn][0], nodes[nn][1], nodes[nn][2]))
        f.write(" -3\n")

        # print elements
        elm_sum = 0
        for en in elm_states:
            if elm_states[en] == state:
                elm_sum += 1
        f.write("    3C" + str(elm_sum).rjust(30, " ") + 37 * " " + "1\n")
        write_elm(Elements.tria3, "7")
        write_elm(Elements.tria6, "8")
        write_elm(Elements.quad4, "9")
        write_elm(Elements.quad8, "10")
        write_elm(Elements.tetra4, "3")
        write_elm(Elements.tetra10, "6")
        write_elm(Elements.penta6, "2")
        write_elm(Elements.penta15, "5")
        write_elm(Elements.hexa8, "1")
        write_elm(Elements.hexa20, "4")

        f.write(" -3\n")
        f.close()
    print("%i files with resulting meshes have been created" % number_of_states)


# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
def export_inp(file_name, nodes, Elements, elm_states, number_of_states):

    def get_associated_nodes(elm_category):
        for en in elm_category:
            if elm_states[en] == state:
                associated_nodes.extend(elm_category[en])

    def write_elements_of_type(elm_type, elm_type_inp):
        if elm_type:
            f.write("*ELEMENT, TYPE=" + elm_type_inp + ", ELSET=state" + str(state) + "\n")
            for en, nod in elm_type.items():
                if elm_states[en] == state:
                    f.write(str(en))
                    for nn in nod:
                        f.write(", " + str(nn))
                    f.write("\n")

    # find all possible states in elm_states and run separately for each of them
    for state in range(number_of_states):
        if file_name[-4:] == ".inp":
            new_name = file_name[:-4] + "_res_mesh" + str(state) + ".inp"
        else:
            new_name = file_name + "_res_mesh" + str(state) + ".inp"
        f = open(new_name, "w")

        # print nodes
        associated_nodes = []
        get_associated_nodes(Elements.tria3)
        get_associated_nodes(Elements.tria6)
        get_associated_nodes(Elements.quad4)
        get_associated_nodes(Elements.quad8)
        get_associated_nodes(Elements.tetra4)
        get_associated_nodes(Elements.tetra10)
        get_associated_nodes(Elements.penta6)
        get_associated_nodes(Elements.penta15)
        get_associated_nodes(Elements.hexa8)
        get_associated_nodes(Elements.hexa20)

        associated_nodes = sorted(list(set(associated_nodes)))
        f.write("*NODE\n")
        for nn in associated_nodes:
            f.write(str(nn) + ", % .5E, % .5E, % .5E\n" % (nodes[nn][0], nodes[nn][1], nodes[nn][2]))
        f.write("\n")

        # print elements
        # prints only basic element types
        write_elements_of_type(Elements.tria3, "S3")
        write_elements_of_type(Elements.tria6, "S6")
        write_elements_of_type(Elements.quad4, "S4")
        write_elements_of_type(Elements.quad8, "S8")
        write_elements_of_type(Elements.tetra4, "C3D4")
        write_elements_of_type(Elements.tetra10, "C3D10")
        write_elements_of_type(Elements.penta6, "C3D6")
        write_elements_of_type(Elements.penta15, "C3D15")
        write_elements_of_type(Elements.hexa8, "C3D8")
        if Elements.hexa20:
            f.write("*ELEMENT, TYPE=C3D20\n")
            for en, nod in Elements.hexa20.items():
                f.write(str(en))
                for nn in nod[:15]:
                    f.write(", " + str(nn))
                f.write("\n")
                for nn in nod[15:]:
                    f.write(", " + str(nn))
                f.write("\n")

        f.close()
    print("%i files with resulting meshes have been created" % number_of_states)


# function for importing elm_states state from .frd file which was previously created as a resulting mesh
# it is done via element numbers only; in case of the wrong mesh, no error is recognised
def import_frd_state(continue_from, elm_states, number_of_states, file_name):
    for state in range(number_of_states):
        try:
            f = open(continue_from[:-5] + str(state) + ".frd", "r")
        except IOError:
            msg = continue_from[:-5] + str(state) + ".frd" + " file not found. Check your inputs."
            write_to_log(file_name, "ERROR: " + msg + "\n")
            assert False, msg

        read_elm = False
        for line in f:
            if line[4:6] == "3C":  # start reading element numbers
                read_elm = True
            elif read_elm is True and line[1:3] == "-1":
                en = int(line[3:13])
                elm_states[en] = state
            elif read_elm is True and line[1:3] == "-3":  # finish reading element numbers
                break
        f.close()
    return elm_states


# function for importing elm_states state from .frd file which was previously created as a resulting mesh
# it is done via element numbers only; in case of the wrong mesh, no error is recognised
def import_inp_state(continue_from, elm_states, number_of_states, file_name):
    for state in range(number_of_states):
        try:
            f = open(continue_from[:-5] + str(state) + ".inp", "r")
        except IOError:
            msg = continue_from[:-5] + str(state) + ".inp" + " file not found. Check your inputs."
            write_to_log(file_name, "ERROR: " + msg + "\n")
            assert False, msg

        read_elm = False
        for line in f:
            if line[0] == '*' and not line[1] == '*':
                read_elm = False
            if line[:8].upper() == "*ELEMENT":
                read_elm = True
            elif read_elm == True:
                try:
                    en = int(line.split(",")[0])
                    elm_states[en] = state
                except ValueError:
                    pass
        f.close()
    return elm_states
