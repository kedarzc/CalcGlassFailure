import math

def extract_max_results_from_dat(filename):
    max_disp = 0.0
    max_principal_stress = -1e20

    in_disp_block = False
    in_stress_block = False

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()

            # -------------------------
            # Detect sections
            # -------------------------
            if "displacements (vx,vy,vz)" in line:
                in_disp_block = True
                in_stress_block = False
                continue

            if "stresses (elem, integ.pnt." in line:
                in_disp_block = False
                in_stress_block = True
                continue

            # Stop blocks when blank line appears
            if line == "":
                in_disp_block = False
                in_stress_block = False
                continue

            # -------------------------
            # Displacement parsing
            # -------------------------
            if in_disp_block:
                parts = line.split()
                if len(parts) < 4:
                    continue

                try:
                    ux = float(parts[1])
                    uy = float(parts[2])
                    uz = float(parts[3])

                    mag = math.sqrt(ux**2 + uy**2 + uz**2)
                    max_disp = max(max_disp, mag)
                except:
                    continue

            # -------------------------
            # Stress parsing
            # -------------------------
            if in_stress_block:
                parts = line.split()
                if len(parts) < 8:
                    continue

                try:
                    sxx = float(parts[2])
                    syy = float(parts[3])
                    szz = float(parts[4])
                    sxy = float(parts[5])
                    sxz = float(parts[6])
                    syz = float(parts[7])

                    # Build stress tensor
                    # [ sxx  sxy  sxz ]
                    # [ sxy  syy  syz ]
                    # [ sxz  syz  szz ]
                    import numpy as np
                    stress_tensor = np.array([
                        [sxx, sxy, sxz],
                        [sxy, syy, syz],
                        [sxz, syz, szz]
                    ])

                    # Principal stresses = eigenvalues
                    eigvals = np.linalg.eigvalsh(stress_tensor)

                    sigma_max = max(eigvals)
                    max_principal_stress = max(max_principal_stress, sigma_max)

                except:
                    continue

    return max_disp, max_principal_stress