# The aim of this script is to read .inp file and separate adjacend elements, so that every element has its own nodes,
# thus nodal results from CalculiX are not averaged between neighbouring elements.


def separating(file_name : str, nodes : dict | None = None):

    # reading node position if it is not defined
    if (nodes is None) | (nodes == {}):
        file_name_read = file_name
        if not file_name.endswith(".inp"):
            file_name_read += ".inp"

        nodes = {}  # dict with nodes position
        model_definition = True
        read_node = False
        line = "\n"
        include = ""

        with open(file_name_read, 'r') as file_read:

            while line != "":
                if include:
                    line = f_include.readline()
                    if line == "":
                        f_include.close()
                        include = ""
                        line = file_read.readline()
                else:
                    line = file_read.readline()

                if line.strip() == '':
                    continue
                elif line[0] == '*':  # start/end of a reading set
                    if line[:2] == '**':  # comments
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
                    nodes[int(line_list[0])] = list(map(float, line_list[1:]))

                elif line[:5].upper() == "*STEP":
                    model_definition = False


    # creating new file from old one with separated elements
    file_name_read = file_name
    if not file_name.endswith('.inp'):
        file_name_read = file_name_read.join(".inp")

    if file_name.endswith('.inp'):
        file_name_write = ''.join(file_name.split(".")[:-1])
    else:
        file_name_write = file_name
    file_name_write = file_name_write.join("_separated.inp")

    with (open(file_name_read, "r") as file_read,
          open(file_name_write, "w") as file_write):

        nn_added = max(nodes.keys())
        number_of_nodes = 0
        rewriting_nodes = False
        left_original = set()
        for line in file_read:
            if line[:2] == '**':  # comments
                file_write.write(line)
                continue

            # define nodes and equations after *ELEMENT block
            elif line[0] == "*" and rewriting_nodes is True:
                number_of_nodes = 0
                rewriting_nodes = False
                file_write.write("** Nodes added by optimization to separate nodal stresses\n")
                file_write.write("*NODE\n")
                for [nn, nn_added] in coincident_nodes:
                    file_write.write(f"{nn_added}, {nodes[nn][0]}, {nodes[nn][1]}, {nodes[nn][2]}\n")
                file_write.write(" \n")
                file_write.write("**Equations added by optimization to separate nodal stresses\n")
                file_write.write("*EQUATION\n")
                dofs = [1, 2, 3]
                if not only_translations:
                    dofs += [4, 5, 6]
                for [nn, nn_added] in coincident_nodes:
                    for dof in dofs:
                        file_write.write("2\n")
                        file_write.write(f"{nn_added}, {dof}, {1}, {nn}, {dof}, {-1} \n")
                file_write.write(" \n")

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
                    file_write.write(line_new[:-2] + "\n")
                    continue

            # find *ELEMENT card
            if line[:8].upper() == "*ELEMENT":
                line_list = line[8:].upper().split(',')
                for line_part in line_list:
                    if line_part.split('=')[0].strip() == "TYPE":
                        elm_type = line_part.split('=')[1].strip()
                        match elm_type:
                            case "S3" | "CPS3" | "CPE3" | "CAX3":
                                number_of_nodes, only_translations = 3, False
                            case "S6" | "CPS6" | "CPE6" | "CAX6":
                                number_of_nodes, only_translations = 6, False
                            case "S4" | "S4R" | "CPS4" | "CPS4R" | "CPE4" | \
                                 "CPE4R" | "CAX4" | "CAX4R":
                                number_of_nodes, only_translations = 4, False
                            case "S8" | "S8R" | "CPS8" | "CPS8R" | "CPE8" | \
                                 "CPE8R" | "CAX8" | "CAX8R":
                                number_of_nodes, only_translations = 8, False
                            case "C3D4":
                                number_of_nodes, only_translations = 4, True
                            case "C3D10":
                                number_of_nodes, only_translations = 10, True
                            case "C3D8" | "C3D8R" | "C3D8I":
                                number_of_nodes, only_translations = 8, True
                            case "C3D20" | "C3D20R" | "C3D20RI":
                                number_of_nodes, only_translations = 20, True
                            case "C3D6":
                                number_of_nodes, only_translations = 6, True
                            case "C3D15":
                                number_of_nodes, only_translations = 15, True
                            case "B31" | "B31R" | "T3D2":
                                number_of_nodes, only_translations = 2, False
                            case "B32" | "B32R" | "T3D3":
                                number_of_nodes, only_translations = 3, False
                            case _:
                                print("Unknown element type")
                        coincident_nodes = []
                        break
                if number_of_nodes:
                    rewriting_nodes = True
                    second_line = False

            file_write.write(line)
