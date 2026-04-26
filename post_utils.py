import numpy as np
from collections import defaultdict
import math

# ==========================================================
# MAX DISPLACEMENT (UNCHANGED - already correct)
# ==========================================================
def compute_max_displacement(dat_file):
    max_umag = 0.0
    max_uz = 0.0

    in_disp_block = False

    with open(dat_file, 'r') as f:
        for line in f:
            line = line.strip()

            if "displacements" in line.lower():
                in_disp_block = True
                continue

            if "stresses" in line.lower():
                in_disp_block = False

            if not in_disp_block or line == "":
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                int(parts[0])
            except:
                continue

            try:
                ux = float(parts[1])
                uy = float(parts[2])
                uz = float(parts[3])

                umag = math.sqrt(ux**2 + uy**2 + uz**2)

                if umag > max_umag:
                    max_umag = umag

                if abs(uz) > abs(max_uz):
                    max_uz = uz

            except:
                continue

    return max_umag, max_uz


# ==========================================================
# PARSE THICKNESS FROM INPUT FILE
# ==========================================================
def parse_shell_thickness(inp_file):
    with open(inp_file, 'r') as f:
        for line in f:
            line_clean = line.strip()

            if line_clean.upper().startswith("*SHELL SECTION"):

                parts = line_clean.split(",")

                for part in parts:
                    if "THICKNESS" in part.upper():
                        return float(part.split("=")[1])

                # thickness on next line
                next_line = next(f).strip()
                return float(next_line.split(",")[0])

    raise ValueError("Thickness not found in *SHELL SECTION")


# ==========================================================
# PARSE STRESSES FROM .DAT FILE
# ==========================================================
def parse_dat_stresses(dat_file):
    """
    Returns:
        element_gp_stress = {
            eid: [8 tensors] (4 bottom + 4 top)
        }
    """

    element_gp_stress = defaultdict(list)
    in_stress_block = False

    with open(dat_file, 'r') as f:
        for line in f:
            line = line.strip()

            if "stresses" in line.lower():
                in_stress_block = True
                continue

            if "displacements" in line.lower():
                in_stress_block = False

            if not in_stress_block or line == "":
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            try:
                eid = int(parts[0])
                ip  = int(parts[1])
            except:
                continue

            try:
                sxx = float(parts[2])
                syy = float(parts[3])
                szz = float(parts[4])

                # Correct shear order from CalculiX
                sxy = float(parts[5])
                syz = float(parts[6])
                sxz = float(parts[7])

                tensor = np.array([
                    [sxx, sxy, sxz],
                    [sxy, syy, syz],
                    [sxz, syz, szz]
                ])

                element_gp_stress[eid].append((ip, tensor))

            except:
                continue

    # Sort integration points
    for eid in element_gp_stress:
        element_gp_stress[eid] = [
            t for _, t in sorted(element_gp_stress[eid], key=lambda x: x[0])
        ]

    return element_gp_stress


# ==========================================================
# COMPUTE SURFACE STRESS AT GAUSS POINTS
# ==========================================================
def compute_surface_gp_stresses(element_gp_stress, thickness):
    """
    Returns:
        list of surface stress tensors (top + bottom at each GP)
    """

    surface_stresses = []

    # section point location
    z0 = thickness / (2.0 * np.sqrt(3.0))

    # actual surface location
    z_surface = thickness / 2.0

    for eid, gp_stresses in element_gp_stress.items():

        if len(gp_stresses) != 8:
            continue

        bottom_gp = gp_stresses[:4]
        top_gp    = gp_stresses[4:]

        for s_bot, s_top in zip(bottom_gp, top_gp):

            # Linear variation through thickness
            a = 0.5 * (s_top + s_bot)
            b = (s_top - s_bot) / (2.0 * z0)

            # Evaluate at actual surface
            s_top_surface = a + b * z_surface
            s_bot_surface = a - b * z_surface

            surface_stresses.append(s_top_surface)
            surface_stresses.append(s_bot_surface)

    return surface_stresses


# ==========================================================
# COMPUTE PRINCIPAL STRESS AT EACH GAUSS POINT
# ==========================================================
def compute_surface_principal_stresses(dat_file, inp_file):
    """
    Returns:
        sigma_list: list of max principal stress at each surface GP
    """

    thickness = parse_shell_thickness(inp_file)
    element_gp_stress = parse_dat_stresses(dat_file)

    surface_stresses = compute_surface_gp_stresses(
        element_gp_stress,
        thickness
    )

    sigma_list = []

    for tensor in surface_stresses:
        eigvals = np.linalg.eigvalsh(tensor)
        sigma_list.append(eigvals[-1])

    return sigma_list


# ==========================================================
# OPTIONAL: MAX STRESS (FOR DISPLAY ONLY)
# ==========================================================
def compute_max_surface_stress(dat_file, inp_file):
    sigma_list = compute_surface_principal_stresses(dat_file, inp_file)
    return max(sigma_list)


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":

    dat_file = "mesh.dat"
    inp_file = "mesh.inp"

    sigma_list = compute_surface_principal_stresses(dat_file, inp_file)

    max_stress = max(sigma_list)

    print(f"Max surface principal stress: {max_stress/1e6:.3f} MPa")