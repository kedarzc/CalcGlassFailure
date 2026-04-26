import math

def extract_max_results_from_dat(filename):
    # Max Z-displacement (by absolute value, signed stored)
    max_disp = 0.0

    max_principal_stress = -1e20

    in_disp_block = False
    in_stress_block = False

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()

            # -------------------------
            # Detect sections (robust)
            # -------------------------
            if "displacements" in line.lower():
                in_disp_block = True
                in_stress_block = False
                continue

            if "stresses" in line.lower():
                in_disp_block = False
                in_stress_block = True
                continue

            # IMPORTANT: Do NOT kill block on blank line
            if line == "":
                continue

            # -------------------------
            # Displacement parsing (Z only)
            # -------------------------
            if in_disp_block:
                parts = line.split()

                # Expect: node ux uy uz
                if len(parts) < 4:
                    continue

                try:
                    uz = float(parts[3])

                    # Track largest absolute Z displacement
                    if abs(uz) > abs(max_disp):
                        max_disp = uz  # keep sign

                except:
                    continue

            # -------------------------
            # Stress parsing
            # -------------------------
            if in_stress_block:
                parts = line.split()

                # Expect: elem, ip, sxx, syy, szz, sxy, sxz, syz
                if len(parts) < 8:
                    continue

                try:
                    sxx = float(parts[2])
                    syy = float(parts[3])
                    szz = float(parts[4])
                    sxy = float(parts[5])
                    sxz = float(parts[6])
                    syz = float(parts[7])

                    import numpy as np
                    stress_tensor = np.array([
                        [sxx, sxy, sxz],
                        [sxy, syy, syz],
                        [sxz, syz, szz]
                    ])

                    eigvals = np.linalg.eigvalsh(stress_tensor)
                    sigma_max = max(eigvals)

                    max_principal_stress = max(max_principal_stress, sigma_max)

                except:
                    continue

    return max_disp, max_principal_stress