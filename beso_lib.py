import numpy as np
import operator


def sround(x, s):
    """round float number x to s significant digits"""
    if x > 0:
        result = round(x, -int(np.floor(np.log10(x))) + s - 1)
    elif x < 0:
        result = round(x, -int(np.floor(np.log10(-x))) + s - 1)
    elif x == 0:
        result = 0
    return result


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
            line_splitted = line.split("=")
            current_elset = line_splitted[1].strip()
            try:
                domains[current_elset]
            except KeyError:
                domains[current_elset] = []
            read_domain = True
        elif read_domain is True:
            for en in line.split(","):
                en = en.strip()
                if en.isdigit():
                    domains[current_elset].append(int(en))
                elif en.isalpha():  # else: en is name of a previous elset
                    domains[current_elset].extend(domains[en.upper()])
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
        msg += ("ERROR: " + row + "\n")
        write_to_log(file_name, msg)
        assert False, row

    return nodes, Elements, domains, opt_domains, en_all


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


# function preparing values for filtering element sensitivity numbers to suppress checkerboard
def filter_prepare1(nodes, Elements, cg, r_min, opt_domains):
    # searching for Elements neighbouring to every node
    node_neighbours = {}

    def fce():
        if nn not in node_neighbours:
            node_neighbours[nn] = [en]
        elif en not in node_neighbours[nn]:
            node_neighbours[nn].append(en)

    for en in Elements.tria3:
        for nn in Elements.tria3[en]:
            fce()
    for en in Elements.tria6:
        for nn in Elements.tria6[en]:
            fce()
    for en in Elements.quad4:
        for nn in Elements.quad4[en]:
            fce()
    for en in Elements.quad8:
        for nn in Elements.quad8[en]:
            fce()
    for en in Elements.tetra4:
        for nn in Elements.tetra4[en]:
            fce()
    for en in Elements.tetra10:
        for nn in Elements.tetra10[en]:
            fce()
    for en in Elements.hexa8:
        for nn in Elements.hexa8[en]:
            fce()
    for en in Elements.hexa20:
        for nn in Elements.hexa20[en]:
            fce()
    for en in Elements.penta6:
        for nn in Elements.penta6[en]:
            fce()
    for en in Elements.penta15:
        for nn in Elements.penta15[en]:
            fce()
    # computing weight factors for sensitivity number of nodes according to distance to adjacent elements
    distance = {}
    M = {}  # element numbers en adjacent to each node nn
    weight_factor_node = {}
    for nn in node_neighbours:
        distance_sum = 0
        M[nn] = []
        for en in node_neighbours[nn]:
            dx = cg[en][0] - nodes[nn][0]
            dy = cg[en][1] - nodes[nn][1]
            dz = cg[en][2] - nodes[nn][2]
            distance[(en, nn)] = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
            distance_sum += distance[(en, nn)]
            M[nn].append(en)
        weight_factor_node[nn] = {}
        for en in M[nn]:
            if len(M[nn]) != 1:
                weight_factor_node[nn][en] = 1 / (len(M[nn]) - 1.0) * (1 - distance[(en, nn)] / distance_sum)
            else:
                weight_factor_node[nn][en] = 1.0
    # print ("weight_factor_node have been computed")
    # computing weight factors for distance of each element and node nearer than r_min
    weight_factor_distance = {}
    near_nodes = {}
    for en in opt_domains:
        near_nodes[en] = []
        down_x = cg[en][0] - r_min
        down_y = cg[en][1] - r_min
        down_z = cg[en][2] - r_min
        up_x = cg[en][0] + r_min
        up_y = cg[en][1] + r_min
        up_z = cg[en][2] + r_min
        for nn in nodes:
            condition_x = down_x < nodes[nn][0] < up_x
            condition_y = down_y < nodes[nn][1] < up_y
            condition_z = down_z < nodes[nn][2] < up_z
            if condition_x and condition_y and condition_z:  # prevents computing distance >> r_min
                dx = cg[en][0] - nodes[nn][0]
                dy = cg[en][1] - nodes[nn][1]
                dz = cg[en][2] - nodes[nn][2]
                distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                if distance < r_min:
                    weight_factor_distance[(en, nn)] = r_min - distance
                    near_nodes[en].append(nn)
    # print ("weight_factor_distance have been computed")
    return weight_factor_node, M, weight_factor_distance, near_nodes


# function preparing values for filtering element sensitivity numbers to suppress checkerboard
# uses sectoring to prevent computing distance of far points
def filter_prepare1s(nodes, Elements, cg, r_min, opt_domains):
    # searching for elements neighbouring to every node
    node_neighbours = {}

    def fce():
        if nn not in node_neighbours:
            node_neighbours[nn] = [en]
        elif en not in node_neighbours[nn]:
            node_neighbours[nn].append(en)

    for en in Elements.tria3:  # element cg computed also out of opt_domains due to neighbours counted also there
        for nn in Elements.tria3[en]:
            fce()
    for en in Elements.tria6:
        for nn in Elements.tria6[en]:
            fce()
    for en in Elements.quad4:
        for nn in Elements.quad4[en]:
            fce()
    for en in Elements.quad8:
        for nn in Elements.quad8[en]:
            fce()
    for en in Elements.tetra4:
        for nn in Elements.tetra4[en]:
            fce()
    for en in Elements.tetra10:
        for nn in Elements.tetra10[en]:
            fce()
    for en in Elements.hexa8:
        for nn in Elements.hexa8[en]:
            fce()
    for en in Elements.hexa20:
        for nn in Elements.hexa20[en]:
            fce()
    for en in Elements.penta6:
        for nn in Elements.penta6[en]:
            fce()
    for en in Elements.penta15:
        for nn in Elements.penta15[en]:
            fce()
    # computing weight factors for sensitivity number of nodes according to distance to adjacent elements
    M = {}  # element numbers en adjacent to each node nn
    weight_factor_node = {}
    for nn in node_neighbours:
        distance_sum = 0
        M[nn] = []
        distance = []
        for en in node_neighbours[nn]:
            dx = cg[en][0] - nodes[nn][0]
            dy = cg[en][1] - nodes[nn][1]
            dz = cg[en][2] - nodes[nn][2]
            distance.append((dx ** 2 + dy ** 2 + dz ** 2) ** 0.5)
            distance_sum += distance[-1]
            M[nn].append(en)
        weight_factor_node[nn] = {}
        en_relative = 0
        for en in node_neighbours[nn]:
            if len(M[nn]) != 1:
                weight_factor_node[nn][en] = 1 / (len(M[nn]) - 1.0) * (1 - distance[en_relative] / distance_sum)
            else:
                weight_factor_node[nn][en] = 1.0
            en_relative += 1
    # print ("weight_factor_node have been computed")
    # computing weight factors for distance of each element and node nearer than r_min
    weight_factor_distance = {}
    near_nodes = {}
    sector_nodes = {}
    sector_elm = {}
    nodes_min = nodes[list(nodes.keys())[0]]  # initial values
    nodes_max = nodes[list(nodes.keys())[0]]
    for nn in nodes:
        nodes_min = [min(nodes[nn][0], nodes_min[0]), min(nodes[nn][1], nodes_min[1]), min(nodes[nn][2], nodes_min[2])]
        nodes_max = [max(nodes[nn][0], nodes_max[0]), max(nodes[nn][1], nodes_max[1]), max(nodes[nn][2], nodes_max[2])]
    # preparing empty sectors
    x = nodes_min[0] + 0.5 * r_min
    while x <= nodes_max[0] + 0.5 * r_min:
        y = nodes_min[1] + 0.5 * r_min
        while y <= nodes_max[1] + 0.5 * r_min:
            z = nodes_min[2] + 0.5 * r_min
            while z <= nodes_max[2] + 0.5 * r_min:
                sector_nodes[(sround(x, 6), sround(y, 6), sround(z,
                                                                 6))] = []  # 6 significant digit round because of small declination (6 must be used for all sround)
                sector_elm[(sround(x, 6), sround(y, 6), sround(z, 6))] = []
                z += r_min
            y += r_min
        x += r_min
    # assigning nodes to the sectors
    for nn in nodes:
        sector_centre = []
        for k in range(3):
            position = nodes_min[k] + r_min * (0.5 + np.floor((nodes[nn][k] - nodes_min[k]) / r_min))
            sector_centre.append(sround(position, 6))
        sector_nodes[tuple(sector_centre)].append(nn)
    # assigning elements to the sectors
    for en in opt_domains:
        sector_centre = []
        for k in range(3):
            position = nodes_min[k] + r_min * (0.5 + np.floor((cg[en][k] - nodes_min[k]) / r_min))
            sector_centre.append(sround(position, 6))
        sector_elm[tuple(sector_centre)].append(en)
        near_nodes[en] = []
    # finding near nodes in neighbouring sectors (even inside) by comparing distance with neighbouring sector elements
    x = nodes_min[0] + 0.5 * r_min
    while x <= nodes_max[0] + 0.5 * r_min:
        y = nodes_min[1] + 0.5 * r_min
        while y <= nodes_max[1] + 0.5 * r_min:
            z = nodes_min[2] + 0.5 * r_min
            while z <= nodes_max[2] + 0.5 * r_min:
                position = (sround(x, 6), sround(y, 6), sround(z, 6))
                for xx in [x + r_min, x, x - r_min]:
                    for yy in [y + r_min, y, y - r_min]:
                        for zz in [z + r_min, z, z - r_min]:
                            position_neighbour = (sround(xx, 6), sround(yy, 6), sround(zz, 6))
                            for en in sector_elm[position]:
                                try:
                                    for nn in sector_nodes[position_neighbour]:
                                        dx = cg[en][0] - nodes[nn][0]
                                        dy = cg[en][1] - nodes[nn][1]
                                        dz = cg[en][2] - nodes[nn][2]
                                        distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                                        if distance < r_min:
                                            weight_factor_distance[(en, nn)] = r_min - distance
                                            near_nodes[en].append(nn)
                                except KeyError:
                                    pass
                z += r_min
            y += r_min
        x += r_min
    # print ("weight_factor_distance have been computed")
    return weight_factor_node, M, weight_factor_distance, near_nodes


# function to filter sensitivity number to suppress checkerboard
def filter_run1(file_name, sensitivity_number, weight_factor_node, M, weight_factor_distance, near_nodes, nodes,
                opt_domains,):
    sensitivity_number_node = {}  # hypothetical sensitivity number of each node
    for nn in nodes:
        if nn in M:
            sensitivity_number_node[nn] = 0
            for en in M[nn]:
                sensitivity_number_node[nn] += weight_factor_node[nn][en] * sensitivity_number[en]
    sensitivity_number_filtered = {}  # sensitivity number of each element after filtering
    for en in opt_domains:
        numerator = 0
        denominator = 0
        for nn in near_nodes[en]:
            try:
                numerator += weight_factor_distance[(en, nn)] * sensitivity_number_node[nn]
                denominator += weight_factor_distance[(en, nn)]
            except KeyError:
                pass
        if denominator != 0:
            sensitivity_number_filtered[en] = numerator / denominator
        else:
            msg = "WARNING: filter1 failed due to division by 0. Some element CG has not a node in distance <= r_min.\n"
            print(msg)
            write_to_log(file_name, msg)
            filter_on_sensitivity = 0
            return sensitivity_number
    return sensitivity_number_filtered


# function preparing values for filtering element rho to suppress checkerboard
# uses sectoring to prevent computing distance of far points
def filter_prepare2s(cg, cg_min, cg_max, r_min, opt_domains):
    weight_factor2 = {}
    near_elm = {}
    sector_elm = {}
    # preparing empty sectors
    x = cg_min[0] + 0.5 * r_min
    while x <= cg_max[0] + 0.5 * r_min:
        y = cg_min[1] + 0.5 * r_min
        while y <= cg_max[1] + 0.5 * r_min:
            z = cg_min[2] + 0.5 * r_min
            while z <= cg_max[2] + 0.5 * r_min:
                # 6 significant digit round because of small declination (6 must be used for all sround below)
                sector_elm[(sround(x, 6), sround(y, 6), sround(z, 6))] = []
                z += r_min
            y += r_min
        x += r_min
    # assigning elements to the sectors
    for en in opt_domains:
        sector_centre = []
        for k in range(3):
            position = cg_min[k] + r_min * (0.5 + np.floor((cg[en][k] - cg_min[k]) / r_min))
            sector_centre.append(sround(position, 6))
        sector_elm[tuple(sector_centre)].append(en)
    # finding near elements inside each sector
    for sector_centre in sector_elm:
        for en in sector_elm[sector_centre]:
            near_elm[en] = []
        for en in sector_elm[sector_centre]:
            for en2 in sector_elm[sector_centre]:
                if en == en2:
                    continue
                ee = (min(en, en2), max(en, en2))
                try:
                    weight_factor2[ee]
                except KeyError:
                    dx = cg[en][0] - cg[en2][0]
                    dy = cg[en][1] - cg[en2][1]
                    dz = cg[en][2] - cg[en2][2]
                    distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                    if distance < r_min:
                        weight_factor2[ee] = r_min - distance
                        near_elm[en].append(en2)
                        near_elm[en2].append(en)
    # finding near elements in neighbouring sectors by comparing distance with neighbouring sector elements
    x = cg_min[0] + 0.5 * r_min
    while x <= cg_max[0] + 0.5 * r_min:
        y = cg_min[1] + 0.5 * r_min
        while y <= cg_max[1] + 0.5 * r_min:
            z = cg_min[2] + 0.5 * r_min
            while z <= cg_max[2] + 0.5 * r_min:
                position = (sround(x, 6), sround(y, 6), sround(z, 6))
                # down level neighbouring sectors:
                # o  o  -
                # o  -  -
                # o  -  -
                # middle level neighbouring sectors:
                # o  o  -
                # o self -
                # o  -  -
                # upper level neighbouring sectors:
                # o  o  -
                # o  o  -
                # o  -  -
                for position_neighbour in [(x + r_min, y - r_min, z - r_min),
                                           (x + r_min, y, z - r_min),
                                           (x + r_min, y + r_min, z - r_min),
                                           (x, y + r_min, z - r_min),
                                           (x + r_min, y - r_min, z),
                                           (x + r_min, y, z),
                                           (x + r_min, y + r_min, z),
                                           (x, y + r_min, z),
                                           (x + r_min, y - r_min, z + r_min),
                                           (x + r_min, y, z + r_min),
                                           (x + r_min, y + r_min, z + r_min),
                                           (x, y + r_min, z + r_min),
                                           (x, y, z + r_min)]:
                    position_neighbour = (sround(position_neighbour[0], 6), sround(position_neighbour[1], 6),
                                          sround(position_neighbour[2], 6))
                    for en in sector_elm[position]:
                        try:
                            for en2 in sector_elm[position_neighbour]:
                                dx = cg[en][0] - cg[en2][0]
                                dy = cg[en][1] - cg[en2][1]
                                dz = cg[en][2] - cg[en2][2]
                                distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                                if distance < r_min:
                                    ee = (min(en, en2), max(en, en2))
                                    weight_factor2[ee] = r_min - distance
                                    near_elm[en].append(en2)
                                    near_elm[en2].append(en)
                        except KeyError:
                            pass
                z += r_min
            y += r_min
        x += r_min
    # print ("near elements have been associated, weight factors computed")
    return weight_factor2, near_elm


# function to filter sensitivity number to suppress checkerboard
# simplified version: makes weighted average of sensitivity numbers from near elements
def filter_run2(file_name, sensitivity_number, weight_factor2, near_elm, opt_domains):
    sensitivity_number_filtered = {}  # sensitivity number of each element after filtering
    for en in opt_domains:
        numerator = 0
        denominator = 0
        for en2 in near_elm[en]:
            ee = (min(en, en2), max(en, en2))
            numerator += weight_factor2[ee] * sensitivity_number[en2]
            denominator += weight_factor2[ee]
        if denominator != 0:
            sensitivity_number_filtered[en] = numerator / denominator
        else:
            msg = "WARNING: filter2 failed due to division by 0." \
                  "Some element has not a near element in distance <= r_min.\n"
            print(msg)
            write_to_log(file_name, msg)
            filter_on_sensitivity = 0
            return sensitivity_number
    return sensitivity_number_filtered


# function preparing values for filtering element sensitivity number using own point mesh
# currently set to work only with elements in opt_domains
def filter_prepare3(file_name, cg, cg_min, r_min, opt_domains):
    weight_factor3 = {}
    near_points = {}
    near_elm = {}
    grid_size = 0.7 * r_min  # constant less than sqrt(6)/2 is chosen ensuring that each element has at least 3 near points
    # if codes below are done for situation where grid_size > 0.5 * r_min

    # searching for near points of each element
    for en in opt_domains:  # domain to take elements for filtering
        x_elm, y_elm, z_elm = cg[en]

        # set proper starting point coordinates
        reminder = divmod(x_elm - cg_min[0], grid_size)[1]
        if (grid_size + reminder) < r_min:
            x = x_elm - grid_size - reminder
        else:
            x = x_elm - reminder
        reminder = divmod(y_elm - cg_min[1], grid_size)[1]
        if (grid_size + reminder) < r_min:
            yy = y_elm - grid_size - reminder
        else:
            yy = y_elm - reminder
        reminder = divmod(z_elm - cg_min[2], grid_size)[1]
        if (grid_size + reminder) < r_min:
            zz = z_elm - grid_size - reminder
        else:
            zz = z_elm - reminder
        near_points[en] = []

        # through points in the cube around element centre of gravity
        while x < x_elm + r_min:
            y = yy
            while y < y_elm + r_min:
                z = zz
                while z < z_elm + r_min:
                    distance = ((x_elm - x) ** 2 + (y_elm - y) ** 2 + (z_elm - z) ** 2) ** 0.5
                    if distance < r_min:
                        weight_factor3[(en, (x, y, z))] = r_min - distance
                        near_points[en].append((x, y, z))
                        try:
                            near_elm[(x, y, z)].append(en)
                        except KeyError:
                            near_elm[(x, y, z)] = [en]
                    z += grid_size
                y += grid_size
            x += grid_size
    hist_near_elm = list(np.zeros(25))
    hist_near_points = list(np.zeros(25))
    for pn in near_elm:
        if isinstance(near_elm[pn], int):
            le = 1
        else:
            le = len(near_elm[pn])
        if le >= len(hist_near_elm):
            while len(hist_near_elm) <= le:
                hist_near_elm.append(0)
        hist_near_elm[le] += 1
    for en in near_points:
        if isinstance(near_points[en], int):
            le = 1
        else:
            le = len(near_points[en])
        if le >= len(hist_near_points):
            while len(hist_near_points) <= le:
                hist_near_points.append(0)
        hist_near_points[le] += 1
    msg = "\nfilter3 statistics:\n"
    msg += "histogram - number of near elements (list position) vs. number of points (value)\n"
    msg += str(hist_near_elm) + "\n"
    msg += "histogram - number of near points (list position) vs. number of elements (value)\n"
    msg += str(hist_near_points) + "\n"
    write_to_log(file_name, msg)
    return weight_factor3, near_elm, near_points


# function for filtering element sensitivity number using own point mesh
# currently works only with elements in opt_domains
def filter_run3(sensitivity_number, weight_factor3, near_elm, near_points):
    sensitivity_number_filtered = {}  # sensitivity number of each element after filtering
    point_sensitivity = {}

    # weighted averaging of sensitivity number from elements to points
    for pn in near_elm:
        numerator = 0
        denominator = 0
        for en in near_elm[pn]:
            numerator += weight_factor3[(en, pn)] * sensitivity_number[en]
            denominator += weight_factor3[(en, pn)]
        point_sensitivity[pn] = numerator / denominator

    # weighted averaging of sensitivity number from points back to elements
    for en in near_points:
        numerator = 0
        denominator = 0
        for pn in near_points[en]:
            numerator += weight_factor3[(en, pn)] * point_sensitivity[pn]
            denominator += weight_factor3[(en, pn)]
        sensitivity_number_filtered[en] = numerator / denominator

    return sensitivity_number_filtered


# function preparing values for morphology based filtering
# it is a copy of filter_prepare2s without saving distance of near elements
# uses sectoring to prevent computing distance of far points
def filter_prepare_morphology(cg, cg_min, cg_max, r_min, opt_domains):
    near_elm = {}
    sector_elm = {}

    # preparing empty sectors
    x = cg_min[0] + 0.5 * r_min
    while x <= cg_max[0] + 0.5 * r_min:
        y = cg_min[1] + 0.5 * r_min
        while y <= cg_max[1] + 0.5 * r_min:
            z = cg_min[2] + 0.5 * r_min
            while z <= cg_max[2] + 0.5 * r_min:
                # 6 significant digit round because of small declination (6 must be used for all sround below)
                sector_elm[(sround(x, 6), sround(y, 6), sround(z, 6))] = []
                z += r_min
            y += r_min
        x += r_min

    # assigning elements to the sectors
    for en in opt_domains:
        sector_centre = []
        for k in range(3):
            position = cg_min[k] + r_min * (0.5 + np.floor((cg[en][k] - cg_min[k]) / r_min))
            sector_centre.append(sround(position, 6))
        sector_elm[tuple(sector_centre)].append(en)

    # finding near elements inside each sector
    for sector_centre in sector_elm:
        for en in sector_elm[sector_centre]:
            near_elm[en] = []
        for en in sector_elm[sector_centre]:
            for en2 in sector_elm[sector_centre]:
                if en == en2:
                    continue
                dx = cg[en][0] - cg[en2][0]
                dy = cg[en][1] - cg[en2][1]
                dz = cg[en][2] - cg[en2][2]
                distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                if distance < r_min:
                    near_elm[en].append(en2)
                    near_elm[en2].append(en)

    # finding near elements in neighbouring sectors by comparing distance with neighbouring sector elements
    x = cg_min[0] + 0.5 * r_min
    while x <= cg_max[0] + 0.5 * r_min:
        y = cg_min[1] + 0.5 * r_min
        while y <= cg_max[1] + 0.5 * r_min:
            z = cg_min[2] + 0.5 * r_min
            while z <= cg_max[2] + 0.5 * r_min:
                position = (sround(x, 6), sround(y, 6), sround(z, 6))
                # down level neighbouring sectors:
                # o  o  -
                # o  -  -
                # o  -  -
                # middle level neighbouring sectors:
                # o  o  -
                # o self -
                # o  -  -
                # upper level neighbouring sectors:
                # o  o  -
                # o  o  -
                # o  -  -
                for position_neighbour in [(x + r_min, y - r_min, z - r_min),
                                           (x + r_min, y, z - r_min),
                                           (x + r_min, y + r_min, z - r_min),
                                           (x, y + r_min, z - r_min),
                                           (x + r_min, y - r_min, z),
                                           (x + r_min, y, z),
                                           (x + r_min, y + r_min, z),
                                           (x, y + r_min, z),
                                           (x + r_min, y - r_min, z + r_min),
                                           (x + r_min, y, z + r_min),
                                           (x + r_min, y + r_min, z + r_min),
                                           (x, y + r_min, z + r_min),
                                           (x, y, z + r_min)]:
                    position_neighbour = (sround(position_neighbour[0], 6), sround(position_neighbour[1], 6),
                                          sround(position_neighbour[2], 6))
                    for en in sector_elm[position]:
                        try:
                            for en2 in sector_elm[position_neighbour]:
                                dx = cg[en][0] - cg[en2][0]
                                dy = cg[en][1] - cg[en2][1]
                                dz = cg[en][2] - cg[en2][2]
                                distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
                                if distance < r_min:
                                    near_elm[en].append(en2)
                                    near_elm[en2].append(en)
                        except KeyError:
                            pass
                z += r_min
            y += r_min
        x += r_min
    # print ("near elements have been associated")
    return near_elm


# morphology based filtering (erode, dilate, open, close, open-close, close-open, combine)
def filter_run_morphology(sensitivity_number, near_elm, opt_domains, filter_type):

    def filter(filter_type, sensitivity_number, near_elm, opt_domains):
        sensitivity_number_subtype = sensitivity_number.copy()
        for en in opt_domains:
            sensitivity_number_near = [sensitivity_number[en]]
            for en2 in near_elm[en]:
                sensitivity_number_near.append(sensitivity_number[en2])
            if filter_type == "erode":
                sensitivity_number_subtype[en] = min(sensitivity_number_near)
            elif filter_type == "dilate":
                sensitivity_number_subtype[en] = max(sensitivity_number_near)
        return sensitivity_number_subtype

    sensitivity_number_filtered = sensitivity_number.copy()
    if filter_type in ["erode", "dilate"]:
        sensitivity_number_filtered = filter(filter_type, sensitivity_number, near_elm, opt_domains)
    elif filter_type == "open":
        sensitivity_number_1 = filter("erode", sensitivity_number, near_elm, opt_domains)
        sensitivity_number_filtered = filter("dilate", sensitivity_number_1, near_elm, opt_domains)
    elif filter_type == "close":
        sensitivity_number_1 = filter("dilate", sensitivity_number, near_elm, opt_domains)
        sensitivity_number_filtered = filter("erode", sensitivity_number_1, near_elm, opt_domains)
    elif filter_type == "open-close":
        sensitivity_number_1 = filter("erode", sensitivity_number, near_elm, opt_domains)
        sensitivity_number_1 = filter("dilate", sensitivity_number_1, near_elm, opt_domains)
        sensitivity_number_1 = filter("dilate", sensitivity_number_1, near_elm, opt_domains)
        sensitivity_number_filtered = filter("erode", sensitivity_number_1, near_elm, opt_domains)
    elif filter_type == "close-open":
        sensitivity_number_1 = filter("dilate", sensitivity_number, near_elm, opt_domains)
        sensitivity_number_1 = filter("erode", sensitivity_number_1, near_elm, opt_domains)
        sensitivity_number_1 = filter("erode", sensitivity_number_1, near_elm, opt_domains)
        sensitivity_number_filtered = filter("dilate", sensitivity_number_1, near_elm, opt_domains)
    elif filter_type == "combine":
        sensitivity_number_1 = filter("erode", sensitivity_number, near_elm, opt_domains)
        sensitivity_number_2 = filter("dilate", sensitivity_number, near_elm, opt_domains)
        for en in opt_domains:
            sensitivity_number_filtered[en] = (sensitivity_number_1[en] + sensitivity_number_2[en]) / 2.0
    return sensitivity_number_filtered


# function for copying .inp file with additional elsets, materials, solid and shell sections, different output request
# elm_states is a dict of the elements containing 0 for void element or 1 for full element
def write_inp(file_nameR, file_nameW, elm_states, number_of_states, domains, domains_from_config, domain_optimized,
              domain_thickness, domain_offset, domain_material, domain_volumes):
    fR = open(file_nameR, "r")
    fW = open(file_nameW + ".inp", "w")
    elsets_done = 0
    sections_done = 0
    outputs_done = 1
    commenting = False
    elset_new = {}
    elsets_used = {}

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
        if (line[:6] == "*ELSET" and elsets_done == 0) or (line[:5] == "*STEP" and elsets_done == 0):
            write_elset()
            elsets_done = 1

        # optimization materials, solid and shell sections
        if line[:5] == "*STEP" and sections_done == 0:
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
                        else:
                            fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) +
                                     ", OFFSET=" + str(domain_offset[dn]) + "\n")
                            fW.write(str(domain_thickness[dn][sn]) + "\n")
                        fW.write(" \n")
            sections_done = 1

        if line[:5] == "*STEP":
            outputs_done -= 1

        # output request only for element stresses in .dat file:
        if line[0:10] == "*NODE FILE" or line[0:8] == "*EL FILE" or line[0:13] == "*CONTACT FILE" or \
                         line[0:11] == "*NODE PRINT" or line[0:9] == "*EL PRINT" or line[0:14] == "*CONTACT PRINT":

            if outputs_done < 1:
                fW.write(" \n")
                for dn in domains_from_config:
                    fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                    fW.write("S\n")
                fW.write(" \n")
                outputs_done += 1
            commenting = True
            continue
        elif commenting is True:
            continue

        fW.write(line)
    fR.close()
    fW.close()


# function for importing results from .dat file
# Failure Indices are computed at each integration point and maximum or average above each element is yielded
def import_FI(max_or_average, file_nameW, domains, criteria, domain_FI, file_name, elm_states):
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
        elif line[:9] == " stresses":  # TODO prevent collision with results from another sets
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
              domain_shells, area_elm, volume_elm, sensitivity_number, mass, mass_full, mass_addition_ratio,
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
        mass_to_add = mass_addition_ratio * mass_full * np.exp(decay_coefficient * (i - i_violated))
        if sum(FI_violated[i - 1]):
            mass_to_remove = mass_addition_ratio * mass_full * np.exp(decay_coefficient * (i - i_violated)) \
                             - mass_overloaded
        else:
            mass_to_remove = mass_removal_ratio * mass_full * np.exp(decay_coefficient * (i - i_violated)) \
                             - mass_overloaded
    else:
        mass_to_add = mass_addition_ratio * mass_full
        mass_to_remove = mass_removal_ratio * mass_full
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


# function for importing elm_states state from .frd file which was previously created as a resulting mesh
# it is done via element numbers only; in case of the wrong mesh, no error is recognised
def import_frd_state(continue_from, elm_states, number_of_states, file_name):
    for state in range(number_of_states):
        try:
            f = open(continue_from + str(state) + ".frd", "r")
        except IOError:
            msg = "continue_from state " + str(state) + " file not found. Check your inputs."
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
    return elm_states
