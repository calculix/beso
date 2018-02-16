import numpy as np
import operator

# function to print ongoing messages to the log file
def write_to_log(file_name, msg):
    f_log = open(file_name[:-4] + ".log", "a")
    f_log.write(msg)
    f_log.close()


# function importing a mesh consisting of nodes, volume and shell elements
def import_inp(file_name, domains_from_config, domain_optimized, shells_as_composite):
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

    try:
        f = open(file_name, "r")
    except IOError:
        msg = ("CalculiX input file " + file_name + " not found. Check your inputs.")
        write_to_log(file_name, "\nERROR: " + msg + "\n")
        raise Exception(msg)
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
            line_list = line[8:].split(',')
            for line_part in line_list:
                if line_part.split('=')[0].strip().upper() == "TYPE":
                    elm_type = line_part.split('=')[1].strip().upper()
                elif line_part.split('=')[0].strip().upper() == "ELSET":
                    current_elset = line_part.split('=')[1].strip()

            if elm_type in ["S3", "CPS3", "CPE3", "CAX3", "M3D3"]:
                elm_category = all_tria3
                number_of_nodes = 3
            elif elm_type in ["S6", "CPS6", "CPE6", "CAX6", "M3D6"]:
                elm_category = all_tria6
                number_of_nodes = 6
            elif elm_type in ["S4", "S4R", "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R", "M3D4", "M3D4R"]:
                elm_category = all_quad4
                number_of_nodes = 4
            elif elm_type in ["S8", "S8R", "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R", "M3D8", "M3D8R"]:
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
                if (shells_as_composite is True) and (elm_type in ["S3", "S4", "S4R", "S8"]):
                    msg = ("\nERROR: " + elm_type + "element type found. CalculiX might need S6 or S8R elements for "
                                                  "composite\n")
                    print(msg)
                    write_to_log(file_name, msg)

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
                    domains[current_elset].extend(domains[en])
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
    Elements.tria3 = {k: all_tria3[k] for k in keys}
    keys = set(en_all).intersection(set(all_tria6.keys()))
    Elements.tria6 = {k: all_tria6[k] for k in keys}
    keys = set(en_all).intersection(set(all_quad4.keys()))
    Elements.quad4 = {k: all_quad4[k] for k in keys}
    keys = set(en_all).intersection(set(all_quad8.keys()))
    Elements.quad8 = {k: all_quad8[k] for k in keys}
    keys = set(en_all).intersection(set(all_tetra4.keys()))
    Elements.tetra4 = {k: all_tetra4[k] for k in keys}
    keys = set(en_all).intersection(set(all_tetra10.keys()))
    Elements.tetra10 = {k: all_tetra10[k] for k in keys}
    keys = set(en_all).intersection(set(all_hexa8.keys()))
    Elements.hexa8 = {k: all_hexa8[k] for k in keys}
    keys = set(en_all).intersection(set(all_hexa20.keys()))
    Elements.hexa20 = {k: all_hexa20[k] for k in keys}
    keys = set(en_all).intersection(set(all_penta6.keys()))
    Elements.penta6 = {k: all_penta6[k] for k in keys}
    keys = set(en_all).intersection(set(all_penta15.keys()))
    Elements.penta15 = {k: all_penta15[k] for k in keys}
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
        msg += ("\nERROR: " + row + "\n")
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

    def second_order_info(elm_type):
        msg = "\nINFO: areas and centres of gravity of " + elm_type.upper() + " elements ignore mid-nodes' positions\n"
        print(msg)
        write_to_log(file_name, msg)

    # defining volume and centre of gravity for all element types
    volume_elm = {}
    area_elm = {}
    cg = {}

    for en, nod in Elements.tria3.items():
        [area_elm[en], cg[en]] = tria_area_cg(nod)

    if Elements.tria6:
        second_order_info("tria6")
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
        second_order_info("quad8")
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
        second_order_info("tetra10")
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
        second_order_info("hexa20")
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
        second_order_info("penta15")  # copy from penta6
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
              domain_thickness, domain_offset, domain_orientation, domain_material, domain_volumes, domain_shells,
              plane_strain, plane_stress, axisymmetry, save_iteration_results, i, reference_points, shells_as_composite,
              optimization_base):
    if reference_points == "nodes":
        fR = open(file_name[:-4] + "_separated.inp", "r")
    else:
        fR = open(file_name, "r")
    check_line_endings = False
    try:
        fW = open(file_nameW + ".inp", "w", newline="\n")
    except TypeError:  # python 2.x do not have newline argument
        fW = open(file_nameW + ".inp", "w")
        check_line_endings = True

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

    # function to add orientation to solid or shell section
    def add_orientation():
        try:
            fW.write(", ORIENTATION=" + domain_orientation[dn][sn] + "\n")
        except (KeyError, IndexError):
            fW.write("\n")

    elsets_done = 0
    sections_done = 0
    outputs_done = 1
    commenting = False
    elset_new = {}
    elsets_used = {}
    msg_error = ""
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
                        fW.write(domain_material[dn][sn] + "\n")
                        if domain_volumes[dn]:
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                            add_orientation()
                        elif len(plane_strain.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                            add_orientation()
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        elif plane_strain.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only plane strain types for 2D elements"
                        elif len(plane_stress.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                            add_orientation()
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        elif plane_stress.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only plane stress types for 2D elements"
                        elif len(axisymmetry.intersection(domain_shells[dn])) == len(domain_shells[dn]):
                            fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                            add_orientation()
                        elif axisymmetry.intersection(domain_shells[dn]):
                            msg_error = dn + " domain does not contain only axisymmetry types for 2D elements"
                        elif shells_as_composite is True:
                            fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", OFFSET=" + str(domain_offset[dn]) +
                                     ", COMPOSITE")
                            add_orientation()
                            # 0.1 + 0.8 + 0.1 of thickness, , material name
                            fW.write(str(0.1 * domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                            fW.write(str(0.8 * domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                            fW.write(str(0.1 * domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                        else:
                            fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) +
                                     ", OFFSET=" + str(domain_offset[dn]))
                            add_orientation()
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        fW.write(" \n")
                        if msg_error:
                            write_to_log(file_name, "\nERROR: " + msg_error + "\n")
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
                if optimization_base == "stiffness":
                    for dn in domains_from_config:
                        fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                        fW.write("ENER\n")
                if reference_points == "integration points":
                    for dn in domains_from_config:
                        fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                        fW.write("S\n")
                elif reference_points == "nodes":
                    fW.write("*EL FILE, GLOBAL=NO\n")
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
    if check_line_endings:
        fW = open(file_nameW + ".inp", "rb")
        content = fW.read().replace("\r\n", "\n")
        fW.close()
        fW = open(file_nameW + ".inp", "wb")
        fW.write(content)
        fW.close()


# function for importing results from .dat file
# Failure Indices are computed at each integration point and maximum or average above each element is returned
def import_FI_int_pt(reference_value, file_nameW, domains, criteria, domain_FI, file_name, elm_states,
                     domains_from_config, steps_superposition):
    try:
        f = open(file_nameW + ".dat", "r")
    except IOError:
        msg = "CalculiX result file not found, check your inputs"
        write_to_log(file_name, "\nERROR: " + msg + "\n")
        assert False, msg
    last_time = "initial"  # TODO solve how to read a new step which differs in time
    step_number = -1
    criteria_elm = {}  # {en1: numbers of applied criteria, en2: [], ...}
    FI_step = []  # list for steps - [{en1: list for criteria FI, en2: [], ...}, {en1: [], en2: [], ...}, next step]
    energy_density_step = []  # list for steps - [{en1: energy_density, en2: ..., ...}, {en1: ..., ...}, next step]

    memorized_steps = set()  # steps to use in superposition
    if steps_superposition:
        step_stress = {}  # {sn: {en: [sxx, syy, szz, sxy, sxz, syz], next element with int. pt. stresses}, next step, ...}
        step_ener = {}  # energy density {sn: {en: ener, next element with int. pt. stresses}, next step, ...}
        for LCn in range(len(steps_superposition)):
            for (scale, sn) in steps_superposition[LCn]:
                sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                memorized_steps.add(sn)
                step_stress[sn] = {}
                step_ener[sn] = {}

    # prepare FI dict from failure criteria
    for dn in domain_FI:
        for en in domains[dn]:
            cr = []
            for dn_crit in domain_FI[dn][elm_states[en]]:
                cr.append(criteria.index(dn_crit))
            criteria_elm[en] = cr

    def compute_FI():  # for the actual integration point
        for FIn in criteria_elm[en]:
            if criteria[FIn][0] == "stress_von_Mises":
                s_allowable = criteria[FIn][1]
                FI_int_pt[FIn].append(np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                                                     6 * (sxy ** 2 + syz ** 2 + sxz ** 2))) / s_allowable)
            elif criteria[FIn][0] == "user_def":
                FI_int_pt[FIn].append(eval(criteria[FIn][1]))
            else:
                msg = "\nError: failure criterion " + str(criteria[FIn]) + " not recognised.\n"
                write_to_log(file_name, msg)

    def save_FI(sn, en):
        FI_step[sn][en] = []
        for FIn in range(len(criteria)):
            FI_step[sn][en].append(None)
            if FIn in criteria_elm[en]:
                if reference_value == "max":
                    FI_step[sn][en][FIn] = max(FI_int_pt[FIn])
                elif reference_value == "average":
                    FI_step[sn][en][FIn] = np.average(FI_int_pt[FIn])

    read_stresses = 0
    read_energy_density = 0
    for line in f:
        line_split = line.split()
        if line.replace(" ", "") == "\n":
            if read_stresses == 1:
                save_FI(step_number, en_last)
            if read_energy_density == 1:
                energy_density_step[step_number][en_last] = np.average(ener_int_pt)
            read_stresses -= 1
            read_energy_density -= 1
            FI_int_pt = [[] for _ in range(len(criteria))]
            ener_int_pt = []
            en_last = None

        elif line[:9] == " stresses":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_stresses = 2
                if last_time != line_split[-1]:
                    step_number += 1
                    FI_step.append({})
                    energy_density_step.append({})
                    last_time = line_split[-1]
        elif line[:24] == " internal energy density":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_energy_density = 2
                if last_time != line_split[-1]:
                    step_number += 1
                    FI_step.append({})
                    energy_density_step.append({})
                    last_time = line_split[-1]

        elif read_stresses == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    save_FI(step_number, en_last)
                    FI_int_pt = [[] for _ in range(len(criteria))]
                en_last = en
            sxx = float(line_split[2])
            syy = float(line_split[3])
            szz = float(line_split[4])
            sxy = float(line_split[5])
            sxz = float(line_split[6])
            syz = float(line_split[7])
            syx = sxy
            szx = sxz
            szy = syz
            compute_FI()
            if step_number in memorized_steps:
                try:
                    step_stress[step_number][en]
                except KeyError:
                    step_stress[step_number][en] = []
                step_stress[step_number][en].append([sxx, syy, szz, sxy, sxz, syz])

        elif read_energy_density == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    energy_density_step[step_number][en_last] = np.average(ener_int_pt)
                    ener_int_pt = []
                en_last = en
            energy_density = float(line_split[2])
            ener_int_pt.append(energy_density)
            if step_number in memorized_steps:
                try:
                    step_ener[step_number][en]
                except KeyError:
                    step_ener[step_number][en] = []
                    step_ener[step_number][en].append(energy_density)
    if read_stresses == 1:
        save_FI(step_number, en_last)
    if read_energy_density == 1:
        energy_density_step[step_number][en_last] = np.average(ener_int_pt)
    f.close()

    # superposed steps
    # step_stress = {sn: {en: [[sxx, syy, szz, sxy, sxz, syz], next integration point], next element with int. pt. stresses}, next step, ...}
    # steps_superposition = [[(sn, scale), next scaled step to add, ...], next superposed step]
    for LCn in range(len(steps_superposition)):
        FI_step.append({})
        energy_density_step.append({})

        # sum scaled stress components at each integration point
        superposition_stress = {}
        superposition_energy_density = {}
        for (scale, sn) in steps_superposition[LCn]:
            sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
            # with stresses
            for en in step_stress[sn]:
                try:
                    superposition_stress[en]
                except KeyError:
                    superposition_stress[en] = []  # list of integration points
                for ip in range(len(step_stress[sn][en])):
                    try:
                        superposition_stress[en][ip]
                    except IndexError:
                        superposition_stress[en].append([0, 0, 0, 0, 0, 0])  # components of stress
                    for component in range(6):
                        superposition_stress[en][ip][component] += scale * step_stress[sn][en][ip][component]
            # again with energy density
            for en in step_ener[sn]:
                try:
                    superposition_energy_density[en]
                except KeyError:
                    superposition_energy_density[en] = []  # list of integration points
                for ip in range(len(step_ener[sn][en])):
                    try:
                        superposition_energy_density[en][ip]
                    except IndexError:
                        superposition_energy_density[en].append(0)  # components of stress
                    for component in range(6):
                        superposition_energy_density[en][ip] += scale * step_ener[sn][en][ip]

        # compute FI in each element at superposed step
        for en in superposition_stress:
            FI_int_pt = [[] for _ in range(len(criteria))]
            for ip in range(len(superposition_stress[en])):
                sxx = superposition_stress[en][ip][0]
                syy = superposition_stress[en][ip][1]
                szz = superposition_stress[en][ip][2]
                sxy = superposition_stress[en][ip][3]
                sxz = superposition_stress[en][ip][4]
                syz = superposition_stress[en][ip][5]
                syx = sxy
                szx = sxz
                szy = syz
                compute_FI()  # fill FI_int_pt
            sn = -1  # last step number
            save_FI(sn, en)  # save value to FI_step for given en
        # compute average energy density over integration point at superposed step
        for en in superposition_energy_density:
            ener_int_pt = []
            for ip in range(len(superposition_energy_density[en])):
                ener_int_pt.append(superposition_energy_density[en][ip])
            sn = -1  # last step number
            energy_density_step[sn][en] = np.average(ener_int_pt)

    return FI_step, energy_density_step


# function for importing results from .frd file
# Failure Indices are computed at each node and maximum or average above each element is returned
def import_FI_node(reference_value, file_nameW, domains, criteria, domain_FI, file_name, elm_states,
                   steps_superposition):
    try:
        f = open(file_nameW + ".frd", "r")
    except IOError:
        msg = "CalculiX result file not found, check your inputs"
        write_to_log(file_name, "\nERROR: " + msg + "\n")
        assert False, msg

    memorized_steps = set()  # steps to use in superposition
    if steps_superposition:
        step_stress = {}  #{sn: {en: [sxx, syy, szz, sxy, sxz, syz], next element with int. pt. stresses}, next step, ...}
        for LCn in range(len(steps_superposition)):
            for (scale, sn) in steps_superposition[LCn]:
                sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                memorized_steps.add(sn)
                step_stress[sn] = {}

    # prepare ordered elements of interest and failure criteria for each element
    criteria_elm = {}
    for dn in domain_FI:
        for en in domains[dn]:
            cr = []
            for dn_crit in domain_FI[dn][elm_states[en]]:
                cr.append(criteria.index(dn_crit))
            criteria_elm[en] = cr
    sorted_elements = sorted(criteria_elm.keys())  # [en_lowest, ..., en_highest]

    def compute_FI():  # for the actual node
        for FIn in criteria_elm[en]:
            if criteria[FIn][0] == "stress_von_Mises":
                s_allowable = criteria[FIn][1]
                FI_node[nn][FIn] = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                                                  6 * (sxy ** 2 + syz ** 2 + sxz ** 2))) / s_allowable
            elif criteria[FIn][0] == "user_def":
                FI_node[nn][FIn] = eval(criteria[FIn][1])
            else:
                msg = "\nError: failure criterion " + str(criteria[FIn]) + " not recognised.\n"
                write_to_log(file_name, msg)

    def save_FI(sn, en):
        FI_step[sn][en] = []
        for FIn in range(len(criteria)):
            FI_step[sn][en].append(None)
            if FIn in criteria_elm[en]:
                if reference_value == "max":
                    FI_step[sn][en][FIn] = max(FI_elm[en][FIn])
                elif reference_value == "average":
                    FI_step[sn][en][FIn] = np.average(FI_elm[en][FIn])

    read_mesh = False
    frd_nodes = {}  # en associated to given node
    elm_nodes = {}
    for en in sorted_elements:
        elm_nodes[en] = []
    read_stress = False
    sn = -1
    FI_step = []  # list for steps - [{en1: list for criteria FI, en2: [], ...}, {en1: [], en2: [], ...}, next step]
    for line in f:
        # reading mesh
        if line[:6] == "    3C":
            read_mesh = True
        elif read_mesh is True:
            if line[:3] == " -1":
                en = int(line[3:13])
                if en == sorted_elements[0]:
                    sorted_elements.pop(0)
                    read_elm_nodes = True
                else:
                    read_elm_nodes = False
            elif line[:3] == " -2" and read_elm_nodes is True:
                associated_nn = list(map(int, line.split()[1:]))
                elm_nodes[en] += associated_nn
                for nn in associated_nn:
                    frd_nodes[nn] = en

        # block end
        if line[:3] == " -3":
            if read_mesh is True:
                read_mesh = False
                frd_nodes_sorted = sorted(frd_nodes.items())  # [(nn, en), ...]
            elif read_stress is True:
                read_stress = False
                FI_elm = {}
                for en in elm_nodes:
                    FI_elm[en] = [[] for _ in range(len(criteria))]
                    for FIn in criteria_elm[en]:
                        for nn in elm_nodes[en]:
                            FI_elm[en][FIn].append(FI_node[nn][FIn])
                FI_step.append({})
                for en in FI_elm:
                    save_FI(sn, en)

        # reading stresses
        elif line[:11] == " -4  STRESS":
            read_stress = True
            sn += 1
            FI_node = {}
            for nn in frd_nodes:
                FI_node[nn] = [[] for _ in range(len(criteria))]
            next_node = 0
        elif read_stress is True:
            if line[:3] == " -1":
                nn = int(line[3:13])
                if nn == frd_nodes_sorted[next_node][0]:
                    next_node += 1
                    sxx = float(line[13:25])
                    syy = float(line[25:37])
                    szz = float(line[37:49])
                    sxy = float(line[49:61])
                    syz = float(line[61:73])
                    szx = float(line[73:85])
                    syx = sxy
                    szy = syz
                    sxz = szx
                    en = frd_nodes[nn]
                    compute_FI()
                    if sn in memorized_steps:
                        try:
                            step_stress[sn][en]
                        except KeyError:
                            step_stress[sn][en] = {}
                        step_stress[sn][en][nn] = [sxx, syy, szz, sxy, sxz, syz]
    f.close()

    # superposed steps
    # step_stress = {sn: {en: [[sxx, syy, szz, sxy, sxz, syz], next node], next element with nodal stresses}, next step, ...}
    # steps_superposition = [[(sn, scale), next scaled step to add, ...], next superposed step]
    for LCn in range(len(steps_superposition)):
        FI_step.append({})

        # sum scaled stress components at each integration node
        superposition_stress = {}
        for (scale, sn) in steps_superposition[LCn]:
            sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
            for en in step_stress[sn]:
                try:
                    superposition_stress[en]
                except KeyError:
                    superposition_stress[en] = {}  # for nodes
                for nn in elm_nodes[en]:
                    try:
                        superposition_stress[en][nn]
                    except KeyError:
                        superposition_stress[en][nn] = [0, 0, 0, 0, 0, 0]  # components of stress
                    for component in range(6):
                        superposition_stress[en][nn][component] += scale * step_stress[sn][en][nn][component]

        # compute FI in each element at superposed step
        for en in superposition_stress:
            FI_node = {}
            for nn in elm_nodes[en]:
                FI_node[nn] = [[] for _ in range(len(criteria))]
                sxx = superposition_stress[en][nn][0]
                syy = superposition_stress[en][nn][1]
                szz = superposition_stress[en][nn][2]
                sxy = superposition_stress[en][nn][3]
                sxz = superposition_stress[en][nn][4]
                syz = superposition_stress[en][nn][5]
                syx = sxy
                szx = sxz
                szy = syz
                compute_FI()  # fill FI_node
            FI_elm[en] = [[] for _ in range(len(criteria))]
            for FIn in criteria_elm[en]:
                for nn in elm_nodes[en]:
                    FI_elm[en][FIn].append(FI_node[nn][FIn])
            sn = -1  # last step number
            save_FI(sn, en)  # save value to FI_step for given en

    return FI_step


# function for switch element states
def switching(elm_states, domains_from_config, domain_optimized, domains, FI_step_max, domain_density, domain_thickness,
              domain_shells, area_elm, volume_elm, sensitivity_number, mass, mass_referential, mass_addition_ratio,
              mass_removal_ratio, compensate_state_filter, mass_excess, decay_coefficient, FI_violated, i_violated, i,
              mass_goal_i, domain_same_state):

    def compute_difference(failing=False):
        if en in domain_shells[dn]:  # shells mass difference
            mass[i] += area_elm[en] * domain_density[dn][elm_states_en] * domain_thickness[dn][elm_states_en]
            if (failing is False) and (elm_states_en != 0):  # for potential switching down
                mass_decrease[en] = area_elm[en] * (
                    domain_density[dn][elm_states_en] * domain_thickness[dn][elm_states_en] -
                    domain_density[dn][elm_states_en - 1] * domain_thickness[dn][elm_states_en - 1])
            if elm_states_en < len(domain_density[dn]) - 1:  # for potential switching up
                mass_increase[en] = area_elm[en] * (
                    domain_density[dn][elm_states_en + 1] * domain_thickness[dn][elm_states_en + 1] -
                    domain_density[dn][elm_states_en] * domain_thickness[dn][elm_states_en])
        else:  # volumes mass difference
            mass[i] += volume_elm[en] * domain_density[dn][elm_states_en]
            if (failing is False) and (elm_states_en != 0):  # for potential switching down
                mass_decrease[en] = volume_elm[en] * (
                    domain_density[dn][elm_states_en] - domain_density[dn][elm_states_en - 1])
            if elm_states_en < len(domain_density[dn]) - 1:  # for potential switching up
                mass_increase[en] = volume_elm[en] * (
                    domain_density[dn][elm_states_en + 1] - domain_density[dn][elm_states_en])

    mass_increase = {}
    mass_decrease = {}
    sensitivity_number_opt = {}
    mass.append(0)
    mass_overloaded = 0.0
    # switch up overloaded elements
    for dn in domains_from_config:
        if domain_optimized[dn] is True:
            len_domain_density_dn = len(domain_density[dn])
            if domain_same_state[dn] is True:
                new_state = 0
                failing = False
                highest_state = 0
                sensitivity_number_highest = 0
                for en in domains[dn]:  # find highest state, sensitivity number and if failing
                    elm_states_en = elm_states[en]
                    if elm_states_en >= highest_state:
                        sensitivity_number_highest = max(sensitivity_number_highest, sensitivity_number[en])
                        highest_state = elm_states_en
                    if FI_step_max[en] >= 1:  # new state if failing
                        failing = True
                        if elm_states_en < len_domain_density_dn - 1:
                            new_state = max(new_state, elm_states_en + 1)
                        else:
                            new_state = max(new_state, elm_states_en)
                    else:
                        new_state = max(new_state, elm_states_en)

                mass_increase[dn] = 0
                mass_decrease[dn] = 0
                for en in domains[dn]:  # evaluate mass, prepare to sorting and switching
                    elm_states[en] = highest_state
                    elm_states_en = elm_states[en]
                    compute_difference(failing)
                    if (failing is True) and (new_state != highest_state):
                            elm_states[en] = new_state
                            elm_states_en = elm_states[en]
                            mass[i] += mass_increase[en]
                            mass_overloaded += mass_increase[en]
                            mass_goal_i += mass_increase[en]
                    elif failing is False:  # use domain name dn instead of element number for future switching
                        sensitivity_number_opt[dn] = sensitivity_number_highest
                        try:
                            mass_increase[dn] += mass_increase[en]
                        except KeyError:
                            pass
                        try:
                            mass_decrease[dn] += mass_decrease[en]
                        except KeyError:
                            pass

            else: # domain_same_state is False
                for en in domains[dn]:
                    if FI_step_max[en] >= 1:  # increase state if it is not the highest
                        en_added = False
                        if elm_states[en] < len_domain_density_dn - 1:
                            elm_states[en] += 1
                            en_added = True
                        elm_states_en = elm_states[en]
                        if en in domain_shells[dn]:  # shells
                            mass[i] += area_elm[en] * domain_density[dn][elm_states_en] * domain_thickness[
                                dn][elm_states_en]
                            if en_added is True:
                                mass_difference = area_elm[en] * (
                                    domain_density[dn][elm_states_en] * domain_thickness[dn][elm_states_en] -
                                    domain_density[dn][elm_states_en - 1] * domain_thickness[dn][elm_states_en - 1])
                                mass_overloaded += mass_difference
                                mass_goal_i += mass_difference
                        else:  # volumes
                            mass[i] += volume_elm[en] * domain_density[dn][elm_states_en]
                            if en_added is True:
                                mass_difference = volume_elm[en] * (
                                    domain_density[dn][elm_states_en] - domain_density[dn][elm_states_en - 1])
                                mass_overloaded += mass_difference
                                mass_goal_i += mass_difference
                    else:  # rest of elements prepare to sorting and switching
                        elm_states_en = elm_states[en]
                        compute_difference()  # mass to add or remove
                        sensitivity_number_opt[en] = sensitivity_number[en]
    # sorting
    sensitivity_number_sorted = sorted(sensitivity_number_opt.items(), key=operator.itemgetter(1))
    sensitivity_number_sorted2 = list(sensitivity_number_sorted)
    if i_violated:
        if mass_removal_ratio - mass_addition_ratio > 0:  # removing from initial mass
            mass_to_add = mass_addition_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated))
            if sum(FI_violated[i - 1]):
                mass_to_remove = mass_addition_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated)) \
                                 - mass_overloaded
            else:
                mass_to_remove = mass_removal_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated)) \
                                 - mass_overloaded
        else:  # adding to initial mass  TODO include stress limit
            mass_to_add = mass_removal_ratio * mass_referential * np.exp(decay_coefficient * (i - i_violated))
            mass_to_remove = mass_to_add
    else:
        mass_to_add = mass_addition_ratio * mass_referential
        mass_to_remove = mass_removal_ratio * mass_referential
    if compensate_state_filter is True:
        if mass_excess > 0:
            mass_to_remove += mass_excess
        else:  # compensate by adding more mass
            mass_to_add -= mass_excess
    mass_added = mass_overloaded
    mass_removed = 0.0
    # if mass_goal_i < mass[i - 1]:  # going from bigger mass to lower
    added_elm = set()
    while mass_added < mass_to_add:
        if sensitivity_number_sorted:
            en = sensitivity_number_sorted.pop(-1)[0]  # highest sensitivity number
            try:
                mass[i] += mass_increase[en]
                mass_added += mass_increase[en]
                if isinstance(en, int):
                    elm_states[en] += 1
                else:  # same state domain en
                    if mass_increase[en] == 0:
                        raise KeyError
                    for en2 in domains[en]:
                        elm_states[en2] += 1
                added_elm.add(en)
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
            if isinstance(en, int):
                if elm_states[en] != 0:
                    mass[i] -= mass_decrease[en]
                    mass_removed += mass_decrease[en]
                    elm_states[en] -= 1
            else:  # same state domain en
                if mass_decrease[en] != 0:
                    mass[i] -= mass_decrease[en]
                    mass_removed += mass_decrease[en]
                    for en2 in domains[en]:
                        elm_states[en2] -= 1
        else:  # switch down elements just switched up or tried to be switched up (already in the highest state)
            try:
                en = sensitivity_number_sorted2[popped][0]
                popped += 1
            except IndexError:
                break
            if isinstance(en, int):
                if elm_states[en] != 0:
                    elm_states[en] -= 1
                    if en in added_elm:
                        mass[i] -= mass_increase[en]
                        mass_removed += mass_increase[en]
                    else:
                        mass[i] -= mass_decrease[en]
                        mass_removed += mass_decrease[en]
            else:  # same state domain en
                if mass_decrease[en] != 0:
                    for en2 in domains[en]:
                        elm_states[en2] -= 1
                    if en in added_elm:
                        mass[i] -= mass_increase[en]
                        mass_removed += mass_increase[en]
                    else:
                        mass[i] -= mass_decrease[en]
                        mass_removed += mass_decrease[en]
    return elm_states, mass


# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
def export_frd(file_nameW, nodes, Elements, elm_states, number_of_states):

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
        f = open(file_nameW + "_state" + str(state) + ".frd", "w")

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


# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
def export_inp(file_nameW, nodes, Elements, elm_states, number_of_states):

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
        f = open(file_nameW + "_state" + str(state) + ".inp", "w")

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


# sub-function to write vth mesh
def vtk_mesh(file_nameW, nodes, Elements):
    f = open(file_nameW + ".vtk", "w")
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Results from optimization\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")

    # nodes
    associated_nodes = set()
    for nn_lists in list(Elements.tria3.values()) + list(Elements.tria6.values()) + list(Elements.quad4.values()) + \
            list(Elements.quad8.values()) + list(Elements.tetra4.values()) + list(Elements.tetra10.values()) + \
            list(Elements.penta6.values()) + list(Elements.penta15.values()) + list(Elements.hexa8.values()) + \
            list(Elements.hexa20.values()):
        associated_nodes.update(nn_lists)
    associated_nodes = sorted(associated_nodes)
    # node renumbering table for vtk format which does not jump over node numbers and contains only associated nodes
    nodes_vtk = [None for _ in range(max(nodes.keys()) + 1)]
    nn_vtk = 0
    for nn in associated_nodes:
        nodes_vtk[nn] = nn_vtk
        nn_vtk += 1

    f.write("\nPOINTS " + str(len(associated_nodes)) + " float\n")
    for nn in associated_nodes:
        f.write("{} {} {}\n".format(nodes[nn][0], nodes[nn][1], nodes[nn][2]))

    # elements
    number_of_elements = len(Elements.tria3) + len(Elements.tria6) + len(Elements.quad4) + len(Elements.quad8) + \
                         len(Elements.tetra4) + len(Elements.tetra10) + len(Elements.penta6) + len(Elements.penta15) + \
                         len(Elements.hexa8) + len(Elements.hexa20)
    en_all = list(Elements.tria3.keys()) + list(Elements.tria6.keys()) + list(Elements.quad4.keys()) + \
             list(Elements.quad8.keys()) + list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) + \
             list(Elements.penta6.keys()) + list(Elements.penta15.keys()) + list(Elements.hexa8.keys()) + \
             list(Elements.hexa20.keys())  # defines vtk element numbering from 0

    size_of_cells = 4 * len(Elements.tria3) + 7 * len(Elements.tria6) + 5 * len(Elements.quad4) + \
                    9 * len(Elements.quad8) + 5 * len(Elements.tetra4) + 11 * len(Elements.tetra10) + \
                    7 * len(Elements.penta6) + 7 * len(Elements.penta15) + 9 * len(Elements.hexa8) + \
                    21 * len(Elements.hexa20)  # quadratic wedge not supported
    f.write("\nCELLS " + str(number_of_elements) + " " + str(size_of_cells) + "\n")

    def write_elm(elm_category, node_length):
        for en in elm_category:
            f.write(node_length)
            for nn in elm_category[en]:
                f.write(" " + str(nodes_vtk[nn]))
            f.write("\n")

    write_elm(Elements.tria3, "3")
    write_elm(Elements.tria6, "6")
    write_elm(Elements.quad4, "4")
    write_elm(Elements.quad8, "8")
    write_elm(Elements.tetra4, "4")
    write_elm(Elements.tetra10, "10")
    write_elm(Elements.penta6, "6")
    write_elm(Elements.penta15, "6")  # quadratic wedge not supported
    write_elm(Elements.hexa8, "8")
    write_elm(Elements.hexa20, "20")

    f.write("\nCELL_TYPES " + str(number_of_elements) + "\n")
    f.write("5\n" * len(Elements.tria3))
    f.write("22\n" * len(Elements.tria6))
    f.write("9\n" * len(Elements.quad4))
    f.write("23\n" * len(Elements.quad8))
    f.write("10\n" * len(Elements.tetra4))
    f.write("24\n" * len(Elements.tetra10))
    f.write("13\n" * len(Elements.penta6))
    f.write("13\n" * len(Elements.penta15))  # quadratic wedge not supported
    f.write("12\n" * len(Elements.hexa8))
    f.write("25\n" * len(Elements.hexa20))

    f.write("\nCELL_DATA " + str(number_of_elements) + "\n")

    f.close()
    return en_all


def append_vtk_states(file_nameW, i, en_all, elm_states):
    f = open(file_nameW + ".vtk", "a")

    # element state
    f.write("\nSCALARS element_states" + str(i).zfill(3) + " float\n")
    f.write("LOOKUP_TABLE default\n")
    for en in en_all:
        f.write(str(elm_states[en]) + "\n")

    f.close()

# function for exporting result in the legacy vtk format
# nodes and elements are renumbered from 0 not to jump over values
def export_vtk(file_nameW, nodes, Elements, elm_states, sensitivity_number, criteria, FI_step, FI_step_max):
    en_all = vtk_mesh(file_nameW, nodes, Elements)
    f = open(file_nameW + ".vtk", "a")

    # element state
    f.write("\nSCALARS element_states float\n")
    f.write("LOOKUP_TABLE default\n")
    for en in en_all:
        f.write(str(elm_states[en]) + "\n")

    # sensitivity number
    f.write("\nSCALARS sensitivity_number float\n")
    f.write("LOOKUP_TABLE default\n")
    for en in en_all:
        f.write(str(sensitivity_number[en]) + "\n")

    # FI
    FI_criteria = {}  # list of FI on each element
    for en in en_all:
        FI_criteria[en] = [None for _ in range(len(criteria))]
        for sn in range(len(FI_step)):
            for FIn in range(len(criteria)):
                if FI_step[sn][en][FIn]:
                    if FI_criteria[en][FIn]:
                        FI_criteria[en][FIn] = max(FI_criteria[en][FIn], FI_step[sn][en][FIn])
                    else:
                        FI_criteria[en][FIn] = FI_step[sn][en][FIn]

    for FIn in range(len(criteria)):
        if criteria[FIn][0] == "stress_von_Mises":
            f.write("\nSCALARS FI=stress_von_Mises/" + str(criteria[FIn][1]).strip() + " float\n")
        elif criteria[FIn][0] == "user_def":
            f.write("SCALARS FI=" + criteria[FIn][1].replace(" ", "") + " float\n")
        f.write("LOOKUP_TABLE default\n")
        for en in en_all:
            if FI_criteria[en][FIn]:
                f.write(str(FI_criteria[en][FIn]) + "\n")
            else:
                f.write("0\n")  # since Paraview do not recognise None value

    # FI_max
    f.write("\nSCALARS FI_max float\n")
    f.write("LOOKUP_TABLE default\n")
    for en in en_all:
        f.write(str(FI_step_max[en]) + "\n")

    f.close()


# function for exporting element values to csv file for displaying in Paraview, output format:
# element_number, cg_x, cg_y, cg_z, element_state, sensitivity_number, failure indices 1, 2,..., maximal failure index
# only elements found by import_inp function are taken into account
def export_csv(domains_from_config, domains, criteria, FI_step, FI_step_max, file_nameW, cg, elm_states,
               sensitivity_number):
    # associate FI to each element and get maximums
    FI_criteria = {}  # list of FI on each element
    for dn in domains_from_config:
        for en in domains[dn]:
            FI_criteria[en] = [None for _ in range(len(criteria))]
            for sn in range(len(FI_step)):
                for FIn in range(len(criteria)):
                    if FI_step[sn][en][FIn]:
                        if FI_criteria[en][FIn]:
                            FI_criteria[en][FIn] = max(FI_criteria[en][FIn], FI_step[sn][en][FIn])
                        else:
                            FI_criteria[en][FIn] = FI_step[sn][en][FIn]

    # write element values to the csv file
    f = open(file_nameW + ".csv", "w")
    line = "element_number, cg_x, cg_y, cg_z, element_state, sensitivity_number, "
    for cr in criteria:
        if cr[0] == "stress_von_Mises":
            line += "FI=stress_von_Mises/" + str(cr[1]).strip() + ", "
        else:
            line += "FI=" + cr[1].replace(" ", "") + ", "
    line += "FI_max\n"
    f.write(line)
    for dn in domains_from_config:
        for en in domains[dn]:
            line = str(en) + ", " + str(cg[en][0]) + ", " + str(cg[en][1]) + ", " + str(cg[en][2]) + ", " + \
                   str(elm_states[en]) + ", " + str(sensitivity_number[en]) + ", "
            for FIn in range(len(criteria)):
                if FI_criteria[en][FIn]:
                    value = FI_criteria[en][FIn]
                else:
                    value = 0  # since Paraview do not recognise None value
                line += str(value) + ", "
            line += str(FI_step_max[en]) + "\n"
            f.write(line)
    f.close()


# function for importing elm_states state from .frd file which was previously created as a resulting mesh
# it is done via element numbers only; in case of the wrong mesh, no error is recognised
def import_frd_state(continue_from, elm_states, number_of_states, file_name):
    for state in range(number_of_states):
        try:
            f = open(continue_from[:-5] + str(state) + ".frd", "r")
        except IOError:
            msg = continue_from[:-5] + str(state) + ".frd" + " file not found. Check your inputs."
            write_to_log(file_name, "\nERROR: " + msg + "\n")
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
            write_to_log(file_name, "\nERROR: " + msg + "\n")
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


# function for importing elm_states state from .csv file
def import_csv_state(continue_from, elm_states, file_name):
    try:
        f = open(continue_from, "r")
    except IOError:
        msg = continue_from + " file not found. Check your inputs."
        write_to_log(file_name, "\nERROR: " + msg + "\n")
        assert False, msg

    headers = f.readline().split(",")
    pos_en = [x.strip() for x in headers].index("element_number")
    pos_state = [x.strip() for x in headers].index("element_state")
    for line in f:
        en = int(line.split(",")[pos_en])
        state = int(line.split(",")[pos_state])
        elm_states[en] = state

    f.close()
    return elm_states
