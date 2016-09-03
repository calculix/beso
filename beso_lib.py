import numpy as np
import matplotlib.pyplot as plt
import string
import operator
import time

def sround(x, s):
    'round float number x to s significant digits'
    if x > 0:
        result = round(x, -int(np.floor(np.log10(x))) + s-1)
    elif x < 0:
        result = round(x, -int(np.floor(np.log10(-x))) + s-1)
    elif x == 0:
        result = 0
    return result

# function importing a mesh consisting of nodes and elements of type C3D4, C3D10, S3, S6
# and importing *ELSET,ELSET=OptimizationDomain
# all elements of OptimizationDomain must be listed, divided by newline or comma
# possible problems: *Card lines of .inp file must be of exact format (as printed by FreeCAD)
def import_inp(file_name, domain_elset, domain_optimized, f_log):
    nodes = {} # dict with a nodes position
    nodes_min = {}
    nodes_max = {}
    class elements():
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
    model_definition = True
    domains = {}

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
        if (line[:5].upper() == "*NODE") and (model_definition == True):
            read_node = True
        elif read_node is True:
            line_list = string.split(line,',')
            number = int(line_list[0])
            x = float(line_list[1])
            y = float(line_list[2])
            z = float(line_list[3])
            nodes[number] = [x, y, z]

        # reading elements
        elif line[:8].upper() == "*ELEMENT":
            line_list = line[8:].upper().split(',')
            for line_part in line_list:
                if line_part.lstrip()[:4] == "TYPE":
                    elm_type = line_part.split('=')[1].strip()
                #elif line_part.lstrip()[:5] == "ELSET":
                    #add_element_number_to_elset_not_implemented = line_part.split('=')[1].strip()

            if elm_type in ["S3", "CPS3", "CPE3", "CAX3"]:
                elm_category = elements.tria3
                number_of_nodes = 3
            elif elm_type in ["S6", "CPS6", "CPE6", "CAX6"]:
                elm_category = elements.tria6
                number_of_nodes = 6
            elif elm_type in ["S4", "S4R", "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R"]:
                elm_category = elements.quad4
                number_of_nodes = 4
            elif elm_type in ["S8", "S8R", "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R"]:
                elm_category = elements.quad8
                number_of_nodes = 8
            elif elm_type == "C3D4":
                elm_category = elements.tetra4
                number_of_nodes = 4
            elif elm_type == "C3D10":
                elm_category = elements.tetra10
                number_of_nodes = 10
            elif elm_type in ["C3D8", "C3D8R", "C3D8I"]:
                elm_category = elements.hexa8
                number_of_nodes = 8
            elif elm_type in ["C3D20", "C3D20R", "C3D20RI"]:
                elm_category = elements.hexa20
                number_of_nodes = 20
            elif elm_type == "C3D6":
                elm_category = elements.penta6
                number_of_nodes = 6
            elif elm_type == "C3D15":
                elm_category = elements.penta15
                number_of_nodes = 15

        elif elm_category != []:
            line_list = string.split(line, ',')
            if elm_2nd_line is False:
                number = int(line_list[0])
                elm_category[number] = []
                pos = 1
            else:
                pos = 0
                elm_2nd_line = False
            for en in range(pos, pos + number_of_nodes - len(elm_category[number])):
                try:
                    enode = int(line_list[en])
                    elm_category[number].append(enode)
                except:
                    elm_2nd_line = True
                    break

        # reading domains from elset
        elif line[:6].upper() == "*ELSET":
            line_splitted = line.split("=")
            if line_splitted[1].strip() in domain_elset:
                read_domain = True
                domain_number = domain_elset.index(line_splitted[1].strip())
                domains[domain_number] = []
        elif read_domain == True:
            for en in line.replace("\n", "").replace(" ", "").split(","):
                if en.isdigit():
                    domains[domain_number].append(int(en))
            if line.replace(" ", "").upper() == "EALL\n":
                domains[domain_number] = elements.tria3.keys() + elements.tria6.keys() + elements.quad4.keys() + elements.quad8.keys() + elements.tetra4.keys() + elements.tetra10.keys() + elements.hexa8.keys() + elements.hexa20.keys() + elements.penta6.keys() + elements.penta15.keys()
        elif line[:5].upper() == "*STEP":
            model_definition = False
    f.close()

    en_all = elements.tria3.keys() + elements.tria6.keys() + elements.quad4.keys() + elements.quad8.keys() + elements.tetra4.keys() + elements.tetra10.keys() + elements.hexa8.keys() + elements.hexa20.keys() + elements.penta6.keys() + elements.penta15.keys()
    row =  ("%.f nodes, %.f TRIA3, %.f TRIA6, %.f QUAD4, %.f QUAD8, %.f TETRA4, %.f TETRA10,"
        %(len(nodes), len(elements.tria3), len(elements.tria6), len(elements.quad4), len(elements.quad8), len(elements.tetra4), len(elements.tetra10)))
    print(row)
    f_log.write(row + "\n")
    row =  ("%.f HEXA8, %.f HEXA20, %.f PENTA6, %.f PENTA15 have been imported"
        %(len(elements.hexa8), len(elements.hexa20), len(elements.penta6), len(elements.penta15)))
    print(row)
    f_log.write(row + "\n")

    opt_domains = []
    for dn in domains:
        if domain_optimized[dn] == True:
            opt_domains.extend(domains[dn])
    print ("%.f domains have been imported" %len(domains))
    if opt_domains == []:
        msg = "None optimized domain has been found"
        f_log.write("ERROR: " + msg + "\n")
        f_log.close()
        assert False, msg

    return nodes, elements, domains, opt_domains, en_all

# function for computing volumes and centres of gravity of all elements (non-penalized)
# approximate for 2nd order elements!
def elm_volume_cg(nodes, elements, domain_elset, domain_thickness, domains, f_log):
    u = [0.0, 0.0, 0.0]
    v = [0.0, 0.0, 0.0]
    w = [0.0, 0.0, 0.0]

    def tria_volume_cg(nod, thickness):
        # compute volume
        for i in [0, 1, 2]:  # denote x, y, z directions
            u[i] = nodes[nod[2]][i] - nodes[nod[1]][i]
            v[i] = nodes[nod[0]][i] - nodes[nod[1]][i]
        volume_tria = np.linalg.linalg.norm(np.cross(u, v)) / 2.0 * thickness
        # compute centre of gravity
        x_cg = (nodes[nod[0]][0] + nodes[nod[1]][0] + nodes[nod[2]][0]) / 3.0
        y_cg = (nodes[nod[0]][1] + nodes[nod[1]][1] + nodes[nod[2]][1]) / 3.0
        z_cg = (nodes[nod[0]][2] + nodes[nod[1]][2] + nodes[nod[2]][2]) / 3.0
        cg_tria = [x_cg, y_cg, z_cg]
        return volume_tria, cg_tria

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

    # find thickness for each element
    dn = 0
    thickness = {}
    for elset in domain_elset:
        if domain_thickness[dn] <> 0:
            for en in domains[dn]:
                thickness[en] = domain_thickness[dn]
        dn += 1

    def check_thickness(en):
        if not en in thickness:
            msg = "Shell element found in domain with 0 thickness"
            f_log.write("ERROR: " + msg + "\n")
            f_log.close()
            assert False, msg

    def second_order_warning(elm_type):
        msg = "WARNING: areas and centres of gravity of " + elm_type.upper() + " elements ignore mid-nodes' positions"
        print(msg)
        f_log.write(msg + "\n")

    # defining volume and centre of gravity for all element types
    volume_elm = {}
    cg = {}

    for en, nod in elements.tria3.iteritems():
        check_thickness(en)
        [volume_elm[en], cg[en]] = tria_volume_cg(nod, thickness[en])

    if elements.tria6:
        second_order_warning("tria6")
    for en, nod in elements.tria6.iteritems():  # copy from tria3
        check_thickness(en)
        [volume_elm[en], cg[en]] = tria_volume_cg(nod, thickness[en])

    for en, nod in elements.quad4.iteritems():
        check_thickness(en)
        [v1, cg1] = tria_volume_cg(nod[0:3], thickness[en])
        [v2, cg2] = tria_volume_cg(nod[0:1] + nod[2:4], thickness[en])
        volume_elm[en] = float(v1 + v2)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k]) / volume_elm[en]

    if elements.quad8:
        second_order_warning("quad8")
    for en, nod in elements.quad8.iteritems():  # copy from quad4
        check_thickness(en)
        [v1, cg1] = tria_volume_cg(nod[0:3], thickness[en])
        [v2, cg2] = tria_volume_cg(nod[0:1] + nod[2:4], thickness[en])
        volume_elm[en] = float(v1 + v2)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k]) / volume_elm[en]

    for en, nod in elements.tetra4.iteritems():
        [volume_elm[en], cg[en]] = tetra_volume_cg(nod)

    if elements.tetra10:
        second_order_warning("tetra10")
    for en, nod in elements.tetra10.iteritems():  # copy from tetra4
        [volume_elm[en], cg[en]] = tetra_volume_cg(nod)

    for en, nod in elements.hexa8.iteritems():
        [v1, cg1] = tetra_volume_cg(nod[0:3] + nod[5:6])
        [v2, cg2] = tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
        [v3, cg3] = tetra_volume_cg(nod[2:3] + nod[4:7])
        [v4, cg4] = tetra_volume_cg(nod[0:1] + nod[2:5])
        [v5, cg5] = tetra_volume_cg(nod[3:5] + nod[6:8])
        [v6, cg6] = tetra_volume_cg(nod[2:5] + nod[6:7])
        volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k] + v3*cg3[k] + v4*cg4[k] + v5*cg5[k] + v6*cg6[k]
                         ) / volume_elm[en]

    if elements.hexa20:
        second_order_warning("hexa20")
    for en, nod in elements.hexa20.iteritems():  # copy from hexa8
        [v1, cg1] = tetra_volume_cg(nod[0:3] + nod[5:6])
        [v2, cg2] = tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
        [v3, cg3] = tetra_volume_cg(nod[2:3] + nod[4:7])
        [v4, cg4] = tetra_volume_cg(nod[0:1] + nod[2:5])
        [v5, cg5] = tetra_volume_cg(nod[3:5] + nod[6:8])
        [v6, cg6] = tetra_volume_cg(nod[2:5] + nod[6:7])
        volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k] + v3*cg3[k] + v4*cg4[k] + v5*cg5[k] + v6*cg6[k]
                  ) / volume_elm[en]

    for en, nod in elements.penta6.iteritems():
        [v1, cg1] = tetra_volume_cg(nod[0:4])
        [v2, cg2] = tetra_volume_cg(nod[1:5])
        [v3, cg3] = tetra_volume_cg(nod[2:6])
        volume_elm[en] = float(v1 + v2 + v3)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k] + v3*cg3[k]) / volume_elm[en]

    if elements.penta15:
        second_order_warning("penta15")  # copy from penta6
    for en, nod in elements.penta15.iteritems():
        [v1, cg1] = tetra_volume_cg(nod[0:4])
        [v2, cg2] = tetra_volume_cg(nod[1:5])
        [v3, cg3] = tetra_volume_cg(nod[2:6])
        volume_elm[en] = float(v1 + v2 + v3)
        cg[en] = [[],[],[]]
        for k in [0, 1, 2]:  # denote x, y, z dimensions
            cg[en][k] = (v1*cg1[k] + v2*cg2[k] + v3*cg3[k]) / volume_elm[en]

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

    return cg, cg_min, cg_max, volume_elm

# function preparing values for filtering element sensitivity numbers to suppress checkerboard
def filter_prepare1(nodes, elements, cg, r_min, opt_domains):
    # searching for elements neighbouring to every node
    node_neighbours = {}
    def fce():
        if nn not in node_neighbours:
            node_neighbours[nn] = [en]
        elif en not in node_neighbours[nn]:
            node_neighbours[nn].append(en)
    for en in elements.tria3:
        for nn in elements.tria3[en]:
            fce()
    for en in elements.tria6:
        for nn in elements.tria6[en]:
            fce()
    for en in elements.quad4:
        for nn in elements.quad4[en]:
            fce()
    for en in elements.quad8:
        for nn in elements.quad8[en]:
            fce()
    for en in elements.tetra4:
        for nn in elements.tetra4[en]:
            fce()
    for en in elements.tetra10:
        for nn in elements.tetra10[en]:
            fce()
    for en in elements.hexa8:
        for nn in elements.hexa8[en]:
            fce()
    for en in elements.hexa20:
        for nn in elements.hexa20[en]:
            fce()
    for en in elements.penta6:
        for nn in elements.penta6[en]:
            fce()
    for en in elements.penta15:
        for nn in elements.penta15[en]:
            fce()
    # computing weight factors for sensitivity number of nodes according to distance to adjacent elements
    distance = {}
    M = {} # element numbers en adjacent to each node nn
    weight_factor_node = {}
    for nn in node_neighbours:
        distance_sum = 0
        M[nn] = []
        for en in node_neighbours[nn]:
            dx = cg[en][0] - nodes[nn][0]
            dy = cg[en][1] - nodes[nn][1]
            dz = cg[en][2] - nodes[nn][2]
            distance[(en, nn)] = (dx**2 + dy**2 + dz**2)**0.5
            distance_sum += distance[(en, nn)]
            M[nn].append(en)
        weight_factor_node[nn] = {}
        for en in M[nn]:
            if len(M[nn]) <> 1:
                weight_factor_node[nn][en] = 1/(len(M[nn]) - 1.0) * (1 - distance[(en,nn)] / distance_sum)
            else:
                 weight_factor_node[nn][en] = 1.0
    #print ("weight_factor_node have been computed")
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
            if condition_x and condition_y and condition_z: # prevents computing distance >> r_min
                dx = cg[en][0] - nodes[nn][0]
                dy = cg[en][1] - nodes[nn][1]
                dz = cg[en][2] - nodes[nn][2]
                distance = (dx**2 + dy**2 + dz**2)**0.5
                if distance < r_min:
                    weight_factor_distance[(en, nn)] = r_min - distance
                    near_nodes[en].append(nn)
    #print ("weight_factor_distance have been computed")
    return weight_factor_node, M, weight_factor_distance, near_nodes

# function preparing values for filtering element sensitivity numbers to suppress checkerboard
# uses sectoring to prevent computing distance of far points
def filter_prepare1s(nodes, elements, cg, r_min, opt_domains):
    # searching for elements neighbouring to every node
    node_neighbours = {}
    def fce():
        if nn not in node_neighbours:
            node_neighbours[nn] = [en]
        elif en not in node_neighbours[nn]:
            node_neighbours[nn].append(en)
    for en in elements.tria3:  # element cg computed also out of opt_domains due to neighbours counted also there
        for nn in elements.tria3[en]:
            fce()
    for en in elements.tria6:
        for nn in elements.tria6[en]:
            fce()
    for en in elements.quad4:
        for nn in elements.quad4[en]:
            fce()
    for en in elements.quad8:
        for nn in elements.quad8[en]:
            fce()
    for en in elements.tetra4:
        for nn in elements.tetra4[en]:
            fce()
    for en in elements.tetra10:
        for nn in elements.tetra10[en]:
            fce()
    for en in elements.hexa8:
        for nn in elements.hexa8[en]:
            fce()
    for en in elements.hexa20:
        for nn in elements.hexa20[en]:
            fce()
    for en in elements.penta6:
        for nn in elements.penta6[en]:
            fce()
    for en in elements.penta15:
        for nn in elements.penta15[en]:
            fce()
    # computing weight factors for sensitivity number of nodes according to distance to adjacent elements
    M = {} # element numbers en adjacent to each node nn
    weight_factor_node = {}
    for nn in node_neighbours:
        distance_sum = 0
        M[nn] = []
        distance = []
        for en in node_neighbours[nn]:
            dx = cg[en][0] - nodes[nn][0]
            dy = cg[en][1] - nodes[nn][1]
            dz = cg[en][2] - nodes[nn][2]
            distance.append((dx**2 + dy**2 + dz**2)**0.5)
            distance_sum += distance[-1]
            M[nn].append(en)
        weight_factor_node[nn] = {}
        en_relative = 0
        for en in node_neighbours[nn]:
            if len(M[nn]) <> 1:
                weight_factor_node[nn][en] = 1/(len(M[nn]) - 1.0) * (1 - distance[en_relative] / distance_sum)
            else:
                 weight_factor_node[nn][en] = 1.0
            en_relative += 1
    #print ("weight_factor_node have been computed")
    # computing weight factors for distance of each element and node nearer than r_min
    weight_factor_distance = {}
    near_nodes = {}
    sector_nodes = {}
    sector_elm = {}
    nodes_min = nodes[nodes.keys()[0]] # initial values
    nodes_max = nodes[nodes.keys()[0]]
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
                sector_nodes[(sround(x, 6), sround(y, 6), sround(z, 6))] = [] # 6 significant digit round because of small declination (6 must be used for all sround)
                sector_elm[(sround(x, 6), sround(y, 6), sround(z, 6))] = []
                z += r_min
            y += r_min
        x += r_min
    # assigning nodes to the sectors
    for nn in nodes:
        sector_centre = []
        for k in range(3):
            position = nodes_min[k] + r_min * (0.5 + np.floor((nodes[nn][k] - nodes_min[k])/ r_min))
            sector_centre.append(sround(position, 6))
        sector_nodes[tuple(sector_centre)].append(nn)
    # assigning elements to the sectors
    for en in opt_domains:
        sector_centre = []
        for k in range(3):
            position = nodes_min[k] + r_min * (0.5 + np.floor((cg[en][k] - nodes_min[k])/ r_min))
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
                                        distance = (dx**2 + dy**2 + dz**2)**0.5
                                        if distance < r_min:
                                            weight_factor_distance[(en, nn)] = r_min - distance
                                            near_nodes[en].append(nn)
                                except KeyError: pass
                z += r_min
            y += r_min
        x += r_min
    #print ("weight_factor_distance have been computed")
    return weight_factor_node, M, weight_factor_distance, near_nodes

# function to filter sensitivity number to suppress checkerboard
def filter_run1(sensitivity_number, weight_factor_node, M, weight_factor_distance, near_nodes, nodes, opt_domains, f_log):
    sensitivity_number_node = {} # hypothetical sensitivity number of each node
    for nn in nodes:
        if nn in M:
            sensitivity_number_node[nn] = 0
            for en in M[nn]:
                sensitivity_number_node[nn] += weight_factor_node[nn][en] * sensitivity_number[en]
    sensitivity_number_filtered = {} # sensitivity number of each element after filtering
    for en in opt_domains:
        numerator = 0
        denominator = 0
        for nn in near_nodes[en]:
            numerator += weight_factor_distance[(en, nn)] * sensitivity_number_node[nn]
            denominator += weight_factor_distance[(en, nn)]
        if denominator <> 0:
            sensitivity_number_filtered[en] = numerator / denominator
        else:
            msg = "WARNING: filter1 failed due to division by 0. Some element CG has not a node in distance <= r_min."
            print(msg)
            f_log.write(msg + "\n")
            use_filter = 0
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
            position = cg_min[k] + r_min * (0.5 + np.floor((cg[en][k] - cg_min[k])/ r_min))
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
                try: weight_factor2[(en2, en)]
                except:
                    dx = cg[en][0] - cg[en2][0]
                    dy = cg[en][1] - cg[en2][1]
                    dz = cg[en][2] - cg[en2][2]
                    distance = (dx**2 + dy**2 + dz**2)**0.5
                    if distance < r_min:
                        weight_factor2[(en, en2)] = r_min - distance
                        weight_factor2[(en2, en)] = weight_factor2[(en, en2)]
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
                                           (x + r_min, y        , z - r_min),
                                           (x + r_min, y + r_min, z - r_min),
                                           (x        , y + r_min, z - r_min),
                                           (x + r_min, y - r_min, z        ),
                                           (x + r_min, y        , z        ),
                                           (x + r_min, y + r_min, z        ),
                                           (x        , y + r_min, z        ),
                                           (x + r_min, y - r_min, z + r_min),
                                           (x + r_min, y        , z + r_min),
                                           (x + r_min, y + r_min, z + r_min),
                                           (x        , y + r_min, z + r_min),
                                           (x        , y        , z + r_min)]:
                    position_neighbour = (sround(position_neighbour[0], 6), sround(position_neighbour[1], 6), sround(position_neighbour[2], 6))
                    for en in sector_elm[position]:
                      try:
                        for en2 in sector_elm[position_neighbour]:
                            dx = cg[en][0] - cg[en2][0]
                            dy = cg[en][1] - cg[en2][1]
                            dz = cg[en][2] - cg[en2][2]
                            distance = (dx**2 + dy**2 + dz**2)**0.5
                            if distance < r_min:
                                ee = [en, en2]
                                ee.sort()
                                weight_factor2[tuple(ee)] = r_min - distance
                                near_elm[en].append(en2)
                                near_elm[en2].append(en)
                      except KeyError: pass
                z += r_min
            y += r_min
        x += r_min
    #print ("near elements have been associated, weight factors computed")
    return weight_factor2, near_elm

# function to filter sensitivity number to suppress checkerboard
# simplified version: makes weighted average of sensitivity numbers from near elements
def filter_run2(sensitivity_number, weight_factor2, near_elm, opt_domains, f_log):
    sensitivity_number_filtered = {} # sensitivity number of each element after filtering
    for en in opt_domains:
        numerator = 0
        denominator = 0
        for en2 in near_elm[en]:
            ee = [en, en2]
            ee.sort()
            numerator += weight_factor2[tuple(ee)] * sensitivity_number[en2]
            denominator += weight_factor2[tuple(ee)]
        if denominator <> 0:
            sensitivity_number_filtered[en] = numerator / denominator
        else:
            msg = "WARNING: filter2 failed due to division by 0. Some element has not a near element in distance <= r_min."
            print(msg)
            f_log.write(msg + "\n")
            use_filter = 0
            return sensitivity_number
    return sensitivity_number_filtered

# function for copying .inp file with additional elsets, materials, solid and shell sections, different output request
# switch_elm is a dict of the elements containing 0 for void element or 1 for full element
def write_inp(file_nameR, file_nameW, switch_elm, domains, domain_optimized, domain_E, domain_poisson, domain_density, void_coefficient, domain_thickness, domain_offset):
    fR = open(file_nameR, "r")
    fW = open(file_nameW + ".inp", "w")

    solid_domains = []
    shell_domains = []
    for dn in range(len(domain_thickness)):
        if domain_thickness[dn] == 0:
            solid_domains.append(dn)
        else:
            shell_domains.append(dn)

    elsets_done = 0
    sections_done = 0
    outputs_done = 1
    commenting = False
    content_full = {}
    content_void = {}

    #function for writing ELSETs
    def write_ELSET():
        fW.write(" \n")
        fW.write("** Added ELSETs by optimization:\n")
        for dn in solid_domains:
            content_full[dn] = False
            content_void[dn] = False
            fW.write("*ELSET,ELSET=OptimizationSolidFull" + str(dn) + "\n")
            voids = []
            if domain_optimized[dn] == True:
                for en in domains[dn]:
                    if switch_elm[en] == 1:
                        fW.write(str(en) + ",\n")
                        content_full[dn] = True
                    else:
                        voids.append(en)
                        content_void[dn] = True
            fW.write("*ELSET,ELSET=OptimizationSolidVoid" + str(dn) + "\n")
            for en in voids:
                fW.write(str(en) + ",\n")
        for dn in shell_domains:
            content_full[dn] = False
            content_void[dn] = False
            fW.write("*ELSET,ELSET=OptimizationShellFull" + str(dn) + "\n")
            voids = []
            if domain_optimized[dn] == True:
                for en in domains[dn]:
                    if switch_elm[en] == 1:
                        fW.write(str(en) + ",\n")
                        content_full[dn] = True
                    else:
                        voids.append(en)
                        content_void[dn] = True
            fW.write("*ELSET,ELSET=OptimizationShellVoid" + str(dn) + "\n")
            for en in voids:
                fW.write(str(en) + ",\n")
        fW.write(" \n")

    for line in fR:
        if line[0]== "*":
            commenting = False

        # writing ELSETs
        if line[:6] == "*ELSET" and elsets_done == 0:
            write_ELSET()
            elsets_done = 1

        # optimization materials, solid and shell sections
        if line[:5] == "*STEP" and sections_done == 0:
            if elsets_done == 0:
                write_ELSET()
                elsets_done = 1

            fW.write(" \n")
            fW.write("** Materials and sections by optimization\n")
            fW.write("** (redefines elements properties defined above):\n")
            for dn in domains:
                fW.write("*MATERIAL, NAME=OptimizationMaterialFull" + str(dn) + "\n");
                fW.write("*ELASTIC\n");
                fW.write(str(domain_E[dn]) + ", " + str(domain_poisson[dn]) + "\n");
                fW.write("*DENSITY\n");
                fW.write(str(domain_density[dn]) + "\n");

                fW.write("*MATERIAL, NAME=OptimizationMaterialVoid" + str(dn) + "\n");
                fW.write("*ELASTIC\n");
                fW.write(str(domain_E[dn] * void_coefficient) + ",\n");
                fW.write(str(domain_poisson[dn]) + "\n");
                fW.write("*DENSITY\n");
                fW.write(str(domain_density[dn] * void_coefficient) + "\n");

                if domain_thickness[dn] == 0:
                    if content_full[dn] == True:
                        fW.write("*SOLID SECTION, ELSET=OptimizationSolidFull" + str(dn) +
                                 ", MATERIAL=OptimizationMaterialFull" + str(dn) + "\n");
                    if content_void[dn] == True:
                        fW.write("*SOLID SECTION, ELSET=OptimizationSolidVoid" + str(dn) +
                                 ", MATERIAL=OptimizationMaterialVoid" + str(dn) + "\n");
                else:
                    if content_full[dn] == True:
                        fW.write("*SHELL SECTION, ELSET=OptimizationShellFull" + str(dn) +
                                 ", MATERIAL=OptimizationMaterialFull" + str(dn) +
                                 ", OFFSET=" + str(domain_offset[dn]) + "\n")
                        fW.write(str(domain_thickness[dn]) + "\n")
                    if content_void[dn] == True:
                        fW.write("*SHELL SECTION, ELSET=OptimizationShellVoid" + str(dn) +
                                 ", MATERIAL=OptimizationMaterialVoid" + str(dn) +
                                 ", OFFSET=" + str(domain_offset[dn]) + "\n")
                        fW.write(str(domain_thickness[dn]) + "\n")
                fW.write(" \n")
            sections_done = 1

        if line[:5] == "*STEP":
            outputs_done -= 1

        # output request only for element stresses in .dat file:
        if line[0:10] == "*NODE FILE" or line[0:8] == "*EL FILE" or line[0:13] == "*CONTACT FILE" or \
          line[0:11] == "*NODE PRINT" or line[0:9] == "*EL PRINT" or line[0:14] == "*CONTACT PRINT":

            if outputs_done < 1:
                fW.write(" \n")
                # for dn in solid_domains:
                    # fW.write("** Added output requested by optimization:\n")
                    # fW.write("*EL PRINT, " + "ELSET=OptimizationSolidFull" + str(dn) + "\n")
                    # fW.write("S\n")
                    # fW.write("*EL PRINT, " + " ELSET=OptimizationSolidVoid" + str(dn) + "\n")
                    # fW.write("S\n")
                # for dn in shell_domains:
                    # fW.write("*EL PRINT, " + "ELSET=OptimizationShellFull" + str(dn) + "\n")
                    # fW.write("S\n")
                    # fW.write("*EL PRINT, " + "ELSET=OptimizationShellVoid" + str(dn) + "\n")
                    # fW.write("S\n")
                fW.write("*EL PRINT, " + "ELSET=EALL" + "\n")
                fW.write("S\n")
                fW.write(" \n")
                outputs_done += 1
            commenting = True
            continue
        elif commenting == True:
            continue

        fW.write(line)
    fR.close()
    fW.close()

# function for importing von Mises stress of the given domain
# stress components in each element are averaged over integration points
# von Mises stress is computed from components
def import_sigma(file_name):
    f = open(file_name, "r")
    read_sigma = 0
    step_number = -1
    line_memory = {}
    integ_pnt = 0
    last_time = "initial" # HERE CONTINUE WITH SOLVING HOW TO READ A NEW STEP WHICH DIFFERS IN TIME
    sigma_step = []

    # averages stress in integration points and computes von Mises stress
    def average():
        en = int(line_memory[0][0])
        sum_sxx, sum_syy, sum_szz, sum_sxy, sum_sxz, sum_syz = 0, 0, 0, 0, 0, 0
        for i in range(integ_pnt):
            sum_sxx += float(line_memory[i][2])
            sum_syy += float(line_memory[i][3])
            sum_szz += float(line_memory[i][4])
            sum_sxy += float(line_memory[i][5])
            sum_sxz += float(line_memory[i][6])
            sum_syz += float(line_memory[i][7])
        sxx = sum_sxx / float(integ_pnt)
        syy = sum_syy / float(integ_pnt)
        szz = sum_szz / float(integ_pnt)
        sxy = sum_sxy / float(integ_pnt)
        sxz = sum_sxz / float(integ_pnt)
        syz = sum_syz / float(integ_pnt)
        von_mises = np.sqrt(0.5 * ((sxx-syy)**2 + (syy-szz)**2 + (szz-sxx)**2 + 6 * (sxy**2 + syz**2 + sxz**2)))
        sigma_step[step_number][en] = von_mises

    for line in f:
        if line == "\n":
            if read_sigma == 1:
                average()
            read_sigma -= 1
        elif line[:9] == " stresses":
            read_sigma = 2
            if last_time <> line.split()[-1]:
                step_number += 1
                sigma_step.append({})
                last_time = line.split()[-1]
        elif read_sigma == 1:
            if integ_pnt >= int(line.split()[1]):
                average()
            integ_pnt = int(line.split()[1])
            line_memory[integ_pnt - 1] = line.split()
    if read_sigma == 1:
        average()
    f.close()
    #print("Von Mises element stresses have been imported")
    return sigma_step

# function for exporting the resulting mesh without void elements
# only elements found by import_inp function are taken into account
def export_frd(file_name, nodes, elements, switch_elm):
    if file_name[-4:] == ".inp":
        new_name = file_name[:-4] + "_res_mesh.frd"
    else:
        new_name = file_name + "_res_mesh.frd"
    f = open(new_name, "w")
    # print nodes
    f.write("    2C" + str(len(nodes)).rjust(30," ") + "\n")
    for nn in nodes:
        f.write(" -1" + str(nn).rjust(10," ") + "% .5E% .5E% .5E\n" % (nodes[nn][0], nodes[nn][1], nodes[nn][2]))
    f.write(" -3\n")
    # print elements
    elm_sum = 0
    for en in switch_elm:
        if switch_elm[en] == 1:
            elm_sum += 1
    f.write("    3C" + str(elm_sum).rjust(30," ") + "\n")

    def write_elm(elm_category, category_symbol):
        for en in elm_category:
            if switch_elm[en] == 1:
                f.write(" -1" + str(en).rjust(10," ") + category_symbol.rjust(5," ") +"\n")
                line = ""
                nodes_done = 0
                if category_symbol == "4":  # hexa20 different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                               10, 11, 16, 17, 18, 19, 12, 13, 14, 15]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10," ")
                        if np in [9, 15]:
                            f.write(" -2" + line + "\n")
                            line = ""
                elif category_symbol == "5":  # penta15 has different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12,
                               13, 14, 9, 10, 11]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10," ")
                        if np in [12, 11]:
                            f.write(" -2" + line + "\n")
                            line = ""
                else:
                    for nn in elm_category[en]:
                        line += str(nn).rjust(10," ")
                        nodes_done += 1
                        if nodes_done == 10 and elm_category != elements.tetra10:
                            f.write(" -2" + line + "\n")
                            line = ""
                    f.write(" -2" + line + "\n")

    write_elm(elements.tria3, "7")
    write_elm(elements.tria6, "8")
    write_elm(elements.quad4, "9")
    write_elm(elements.quad8, "10")
    write_elm(elements.tetra4, "3")
    write_elm(elements.tetra10, "6")
    write_elm(elements.penta6, "2")
    write_elm(elements.penta15, "5")
    write_elm(elements.hexa8, "1")
    write_elm(elements.hexa20, "4")

    f.write(" -3\n")
    f.close()
    print("%s file with resulting mesh has been created" %new_name)

# function for importing full elements from .frd file which was previously created as resulting elements
# it is done via element numbers only; in case of the wrong mesh, no error is recognised
def frd_as_full(continue_from, switch_elm):
    f = open(continue_from, "r")
    read_elm = False

    for line in f:
        if line[4:6] == "3C": # start reading element numbers
            read_elm = True
        elif read_elm == True and line[1:3] == "-1":
            en = int(line[3:13])
            switch_elm[en] = 1
        elif read_elm == True and line[1:3] == "-3": # finish reading element numbers
            break
    return switch_elm