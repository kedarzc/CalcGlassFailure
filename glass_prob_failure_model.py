import post_utils as POST
import numpy as np

def parse_nodes(inp_file):
    nodes = {}

    with open(inp_file, 'r') as f:
        in_node_block = False

        for line in f:
            line = line.strip()

            if line.upper().startswith("*NODE"):
                in_node_block = True
                continue

            if line.startswith("*"):
                in_node_block = False

            if not in_node_block:
                continue

            parts = line.split(",")

            if len(parts) < 4:
                continue

            nid = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])

            nodes[nid] = np.array([x, y, z])

    return nodes
    
def parse_elements(inp_file):
    elements = {}

    with open(inp_file, 'r') as f:
        in_elem_block = False

        for line in f:
            line = line.strip()

            if line.upper().startswith("*ELEMENT"):
                in_elem_block = True
                continue

            if line.startswith("*"):
                in_elem_block = False

            if not in_elem_block:
                continue

            parts = line.split(",")

            if len(parts) < 5:
                continue

            eid = int(parts[0])
            nodes = list(map(int, parts[1:5]))

            elements[eid] = nodes

    return elements

def quad_area(n1, n2, n3, n4):
    # split quad into two triangles
    A1 = 0.5 * np.linalg.norm(np.cross(n2 - n1, n3 - n1))
    A2 = 0.5 * np.linalg.norm(np.cross(n4 - n1, n3 - n1))
    return A1 + A2
    
def compute_weibull_failure(dat_file, inp_file, m, k, td=3.0, n=16):

    thickness = POST.parse_shell_thickness(inp_file)
    element_gp_stress = POST.parse_dat_stresses(dat_file)

    nodes = parse_nodes(inp_file)
    elements = parse_elements(inp_file)

    z0 = thickness / (2.0 * np.sqrt(3.0))
    z_surface = thickness / 2.0

    B = 0.0

    for eid, gp_stresses in element_gp_stress.items():

        if eid not in elements:
            continue

        if len(gp_stresses) != 8:
            continue

        # element area
        nids = elements[eid]
        coords = [nodes[nid] for nid in nids]
        A = quad_area(*coords)

        dA = A / 4.0   # per Gauss point

        bottom_gp = gp_stresses[:4]
        top_gp    = gp_stresses[4:]

        for s_bot, s_top in zip(bottom_gp, top_gp):

            # thickness interpolation
            a = 0.5 * (s_top + s_bot)
            b = (s_top - s_bot) / (2.0 * z0)

            s_top_surface = a + b * z_surface
            s_bot_surface = a - b * z_surface

            for tensor in [s_top_surface, s_bot_surface]:

                eigvals = np.linalg.eigvalsh(tensor)
                sigma = max(eigvals[-1], 0.0)  # tension only

                if sigma <= 0:
                    continue

                B += (k *
                      (td/60.0)**(1.0/n) *
                      (sigma**m) *
                      dA)

    Pf = 1.0 - np.exp(-B)

    return Pf, B