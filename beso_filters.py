import numpy as np
import beso_lib

def sround(x, s):
    """round float number x to s significant digits"""
    if x > 0:
        result = round(x, -int(np.floor(np.log10(x))) + s - 1)
    elif x < 0:
        result = round(x, -int(np.floor(np.log10(-x))) + s - 1)
    elif x == 0:
        result = 0
    return result


# function to check if filtering is to be used on domains with prescribed same state
def check_same_state(domain_same_state, filtered_dn, file_name):
    wrong_domains = False
    filtered_dn_set = set(filtered_dn)
    domains_to_check = set()
    for dn in domain_same_state:
        if domain_same_state[dn]:
            domains_to_check.add(dn)
    if domains_to_check.intersection(filtered_dn_set):
        wrong_domains = True

    if wrong_domains is True:
        msg = "\nERROR: Filtering is used on domain with prescribed same state. It is recommended to exclude this domain" \
              " from filtering.\n"
        beso_lib.write_to_log(file_name, msg)
        print(msg)


# function preparing values for filtering element sensitivity numbers to suppress checkerboard
def prepare1(nodes, Elements, cg, r_min, opt_domains):
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
def prepare1s(nodes, Elements, cg, r_min, opt_domains):
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
                # 6 significant digit round because of small declination (6 must be used for all sround)
                sector_nodes[(sround(x, 6), sround(y, 6), sround(z, 6))] = []
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
def run1(file_name, sensitivity_number, weight_factor_node, M, weight_factor_distance, near_nodes, nodes, opt_domains):
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
            msg = "\nERROR: filter over nodes failed due to division by 0." \
                  "Some element CG has not a node in distance <= r_min.\n"
            print(msg)
            beso_lib.write_to_log(file_name, msg)
            filter_on_sensitivity = 0
            return sensitivity_number
    return sensitivity_number_filtered


# function preparing values for filtering element rho to suppress checkerboard
# uses sectoring to prevent computing distance of far points
def prepare2s(cg, cg_min, cg_max, r_min, opt_domains, weight_factor2, near_elm):
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
def run2(file_name, sensitivity_number, weight_factor2, near_elm, opt_domains):
    sensitivity_number_filtered = sensitivity_number.copy()  # sensitivity number of each element after filtering
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
            msg = "\nERROR: simple filter failed due to division by 0." \
                  "Some element has not a near element in distance <= r_min.\n"
            print(msg)
            beso_lib.write_to_log(file_name, msg)
            filter_on_sensitivity = 0
            return sensitivity_number
    return sensitivity_number_filtered


# function preparing values for filtering element sensitivity number using own point mesh
# currently set to work only with elements in opt_domains
def prepare3(file_name, cg, cg_min, r_min, opt_domains):
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
    beso_lib.write_to_log(file_name, msg)
    return weight_factor3, near_elm, near_points


# function for filtering element sensitivity number using own point mesh
# currently works only with elements in opt_domains
def run3(sensitivity_number, weight_factor3, near_elm, near_points):
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
def prepare_morphology(cg, cg_min, cg_max, r_min, opt_domains, near_elm):
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
def run_morphology(sensitivity_number, near_elm, opt_domains, filter_type):

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
