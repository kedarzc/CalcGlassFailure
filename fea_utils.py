import subprocess
import os
from fea_data import Model

def m_to_mm(number):
    return number/1000.0

def GPa_to_Pa(number):
    return(number*10**9)

def kPa_to_Pa(number):
    return(number*10**3)

def write_abaqus_inp(grid,  model: Model, filename="mesh.inp"):
    """
    Writes a structured grid to an Abaqus .inp file (S4 elements)

    Parameters:
        grid     : PyVista structured grid
        model    : FEA Input data
        filename : output file name
    """

    materialName = "Glass"

    if grid is None:
        raise ValueError("Grid is None")

    nx, ny, _ = grid.dimensions
    points = grid.points

    # Extract values
    Lx = model.geometry.Lx
    Ly = model.geometry.Ly
    t = m_to_mm(model.geometry.thickness)
    E = GPa_to_Pa(model.material.E)
    nu = model.material.nu
    pressure = kPa_to_Pa(model.load.pressure)

    with open(filename, 'w') as f:

        # -------------------------
        # Nodes
        # -------------------------
        f.write("*NODE, NSET=Nall\n")
        for nid, (x, y, z) in enumerate(points, start=1):
            f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")

        # -------------------------
        # Elements (S4)
        # -------------------------
        f.write("*ELEMENT, TYPE=S4R, ELSET=Eall\n")

        eid = 1
        for j in range(ny - 1):
            for i in range(nx - 1):
                n1 = i + j * nx + 1
                n2 = (i + 1) + j * nx + 1
                n3 = (i + 1) + (j + 1) * nx + 1
                n4 = i + (j + 1) * nx + 1

                f.write(f"{eid}, {n1}, {n2}, {n3}, {n4}\n")
                eid += 1
        
        # -------------------------
        # Material and section
        # -------------------------
        f.write(f"*MATERIAL, NAME={materialName}\n")
        f.write(f"*ELASTIC\n")
        f.write(f"{E}, {nu}\n")
        f.write(f"*SHELL SECTION, ELSET=Eall, MATERIAL={materialName}, Offset=0\n")
        f.write(f"{t}\n")
                
        # -------------------------
        # Node sets
        # -------------------------
        # Node at (0, 0)
        # Create Node sets
        f.write("*NSET, NSET=BCXY\n")
        f.write("1\n")
        
        # Node at (0, Ly)
        nid_top_left = (ny - 1) * nx + 1
        f.write("*NSET, NSET=BCY\n")
        f.write(f"{nid_top_left}\n")

        # All nodes at the edge
        tol = 1e-8

        edge_nodes = []

        for nid, (x, y, z) in enumerate(points, start=1):
            if (abs(x - 0.0) < tol or
                abs(x - Lx) < tol or
                abs(y - 0.0) < tol or
                abs(y - Ly) < tol):
                edge_nodes.append(nid)

        # Write to ccx
        f.write("*NSET, NSET=EDGENODES\n")

        for i, nid in enumerate(edge_nodes):
            if i % 16 == 0 and i != 0:
                f.write("\n")  # optional formatting (ccx readable lines)
            f.write(f"{nid}, ")

        f.write("\n")

        # -------------------------
        # Create Top Surface
        # -------------------------
        f.write("*Surface, Name=TopSurface, Type=Element\n")
        f.write("Eall, S2\n")

        # -------------------------
        # Create Step
        # -------------------------
        # WORKS
        # f.write("*STEP\n")
        # f.write("*STATIC\n")
        
        f.write("*STEP, NLGEOM\n")
        f.write("*STATIC\n")
        f.write("0.1, 1.0, 1e-8, 0.1\n")
   
        # Output Frequency
        f.write("*Output, Frequency=1\n")
        
        # Boundary Conditions
        f.write("*BOUNDARY, FIXED\n")
        f.write("BCXY, 1, 1\n")
        f.write("BCXY, 2, 2\n")
        f.write("*BOUNDARY, FIXED\n")
        f.write("BCY, 2, 2\n")
        f.write("*BOUNDARY, FIXED\n")
        f.write("EDGENODES, 3, 3\n")

        # Apply Load
        f.write("*DLOAD\n")
        f.write(f"Eall, P, -{pressure}\n")

        # Print outputs
        f.write("*NODE FILE\n")
        f.write("U\n")
        f.write("*EL FILE\n")
        f.write("S\n")
        f.write("*NODE PRINT, NSET=Nall, FREQUENCY=9999\n")
        f.write("U\n")
        f.write("*EL PRINT, ELSET=Eall, FREQUENCY=9999\n")
        f.write("S\n")
        
        f.write("*END STEP\n")    

    print(f"Abaqus input file written: {filename}")

def run_ccx_dynamic(jobname="mesh"):
    exe_path = r"C:\MyComputerPrograms\CalcGlassFailure\solver\ccx_dynamic.exe"

    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"Executable not found: {exe_path}")

    result = subprocess.run(
        [exe_path, "-i", jobname],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("ERROR:\n", result.stderr)

    return result