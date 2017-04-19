# The aim of this script is to read .inp file and separate adjacend elements, so that every element has its own nodes,
# thus nodal results from CalculiX are not averaged between neighbouring elements.


def separating(file_name, nodes={}):

    # reading node position if it is not defined
    if not nodes:
        if file_name[-4:] == ".inp":
            file_nameR = file_name
        else:
            file_nameR = file_name + ".inp"
        fR = open(file_nameR, "r")

        nodes = {}  # dict with nodes position
        model_definition = True
        read_node = False
        line = "\n"
        include = ""
        while line != "":
            if include:
                line = f_include.readline()
                if line == "":
                    f_include.close()
                    include = ""
                    line = fR.readline()
            else:
                line = fR.readline()
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

            elif line[:5].upper() == "*STEP":
                model_definition = False
        fR.close()

    # creating new file from old one with separated elements
    if file_name[-4:] == ".inp":
        file_nameR = file_name
        file_nameW = file_name[:-4] + "_separated.inp"
    else:
        file_nameR = file_name + ".inp"
        file_nameW = file_name + "_separated.inp"
    fR = open(file_nameR, "r")
    fW = open(file_nameW, "w")

    nn_added = max(nodes.keys())
    number_of_nodes = 0
    rewriting_nodes = False
    left_original = set()
    for line in fR:
        if line[0:2] == '**':  # comments
            fW.write(line)
            continue

        # define nodes and equations after *ELEMENT block
        elif line[0] == "*" and rewriting_nodes is True:
            number_of_nodes = 0
            rewriting_nodes = False
            fW.write("** Nodes added by optimization to separate nodal stresses\n")
            fW.write("*NODE\n")
            for [nn, nn_added] in coincident_nodes:
                fW.write("{}, {}, {}, {}\n" .format(nn_added, nodes[nn][0], nodes[nn][1], nodes[nn][2]))
            fW.write(" \n")
            fW.write("**Equations added by optimization to separate nodal stresses\n")
            fW.write("*EQUATION\n")
            if only_translations is True:
                dofs = [1, 2, 3]
            else:
                dofs = [1, 2, 3, 4, 5, 6]
            for [nn, nn_added] in coincident_nodes:
                for dof in dofs:
                    fW.write("2\n")
                    fW.write("{}, {}, {}, {}, {}, {} \n" .format(nn_added, dof, 1, nn, dof, -1))
            fW.write(" \n")

        # rewriting associated nodes under *ELEMENT card
        elif rewriting_nodes is True:
            line_list = line.split(",")
            if len(line_list) > 1:
                if line_list[-1].strip() == "":
                    line_list.pop()
                if second_line is False:
                    line_new = line_list[0] + ", "
                    start_position = 1
                    if len(line_list) < number_of_nodes + 1:
                        second_line = True
                else:
                    line_new = ""
                    start_position = 0
                    second_line = False
                for nn in line_list[start_position:]:
                    nn = int(nn)
                    if (only_translations is False) and (nn not in left_original):  # write 1 original nn for shell/beam
                        left_original.add(nn)
                        line_new += str(nn) + ", "
                    else:
                        nn_added += 1
                        line_new += str(nn_added) + ", "
                        coincident_nodes.append((nn, nn_added))
                fW.write(line_new[:-2] + "\n")
                continue

        # find *ELEMENT card
        if line[:8].upper() == "*ELEMENT":
            line_list = line[8:].upper().split(',')
            for line_part in line_list:
                if line_part.split('=')[0].strip() == "TYPE":
                    elm_type = line_part.split('=')[1].strip()
                    if elm_type in ["S3", "CPS3", "CPE3", "CAX3"]:
                        number_of_nodes = 3
                        only_translations = False
                    elif elm_type in ["S6", "CPS6", "CPE6", "CAX6"]:
                        number_of_nodes = 6
                        only_translations = False
                    elif elm_type in ["S4", "S4R", "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R"]:
                        number_of_nodes = 4
                        only_translations = False
                    elif elm_type in ["S8", "S8R", "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R"]:
                        number_of_nodes = 8
                        only_translations = False
                    elif elm_type == "C3D4":
                        number_of_nodes = 4
                        only_translations = True
                    elif elm_type == "C3D10":
                        number_of_nodes = 10
                        only_translations = True
                    elif elm_type in ["C3D8", "C3D8R", "C3D8I"]:
                        number_of_nodes = 8
                        only_translations = True
                    elif elm_type in ["C3D20", "C3D20R", "C3D20RI"]:
                        number_of_nodes = 20
                        only_translations = True
                    elif elm_type == "C3D6":
                        number_of_nodes = 6
                        only_translations = True
                    elif elm_type == "C3D15":
                        number_of_nodes = 15
                        only_translations = True
                    elif elm_type == ["B31", "B31R", "T3D2"]:
                        number_of_nodes = 2
                        only_translations = False
                    elif elm_type == ["B32", "B32R", "T3D3"]:
                        number_of_nodes = 3
                        only_translations = False
                    coincident_nodes = []
                    break
            if number_of_nodes:
                rewriting_nodes = True
                second_line = False

        fW.write(line)
    fR.close()
    fW.close()
