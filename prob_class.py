import os
os.environ["QT_API"] = "pyside6"

import sys
import numpy as np
import pyvista as pv
import pyvistaqt as pvqt

from PySide6.QtWidgets import QApplication, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile




class App:
    def __init__(self):
        loader = QUiLoader()

        ui_file = QFile("main_window.ui")
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        ui_file.close()

        # -------------------------
        # Adjust Max and Min numbers
        # --------------------------
        self.window.EMod.setRange(1e-3, 1e6)
        self.window.EMod.setDecimals(2)
        self.window.EMod.setSingleStep(1)

        # Poisson’s ratio
        self.window.nu.setRange(0.0, 0.499)
        self.window.nu.setSingleStep(0.01)
        
        # Geometry
        self.window.Lx.setRange(1e-3, 1e6)
        self.window.Ly.setRange(1e-3, 1e6)
        self.window.thick_glass.setRange(1e-3, 1e6)
        self.window.thick_glass.setSingleStep(0.01)

        # Mesh
        self.window.ex.setRange(1e-3, 1000)
        self.window.ey.setRange(1e-3, 1000)

        # Load
        self.window.appliedLoad.setRange(1e-3, 1e6)

        # Make results un-editable

        # -------------------------
        # Attach PyVista
        # -------------------------
        self.plotter = pvqt.QtInteractor(self.window.plotter_container)

        layout = self.window.plotter_container.layout()
        if layout is None:
            layout = QVBoxLayout(self.window.plotter_container)

        layout.addWidget(self.plotter.interactor)

        self.plotter.set_background("white")
        self.plotter.set_background("white")

        self.plotter.add_axes(
            line_width=2,
            labels_off=False,
            viewport=(0.8, 0.0, 1.0, 0.2)
        )

        # -------------------------
        # Internal state
        # -------------------------
        self.grid = None
        self.actor = None

        # -------------------------
        # Connect buttons
        # -------------------------
        self.window.meshButton.clicked.connect(self.create_mesh)
        self.window.solveButton.clicked.connect(self.solve_fea)
        self.window.loadResultsButton.clicked.connect(self.read_results)

        # -------------------------
        # Initial render (IMPORTANT)
        # -------------------------
        self.create_mesh()

    # -------------------------
    # Grid creation
    # -------------------------
    def create_structured_grid(self, Lx, Ly, ex, ey):
        nx = ex + 1
        ny = ey + 1

        x = np.linspace(0, Lx, nx)
        y = np.linspace(0, Ly, ny)

        X, Y = np.meshgrid(x, y, indexing='ij')
        Z = np.zeros_like(X)

        return pv.StructuredGrid(X, Y, Z)

    # -------------------------
    # Update grid
    # -------------------------
    def create_mesh(self):
        Lx = self.window.Lx.value()
        Ly = self.window.Ly.value()
        ex = self.window.ex.value()
        ey = self.window.ey.value()

        EMod = self.window.EMod.value()

        self.grid = self.create_structured_grid(Lx, Ly, ex, ey)

        # Remove previous mesh
        if self.actor is not None:
            self.plotter.remove_actor(self.actor)

        # Add new mesh
        self.actor = self.plotter.add_mesh(
            self.grid,
            color="lightblue",
            show_edges=True,
            edge_color="black"
        )

        self.plotter.view_xy()
        self.plotter.reset_camera()
        self.plotter.render()

    # -------------------------
    # Export Abaqus
    # -------------------------
    def solve_fea(self):
        if self.grid is None:
            return

        grid = self.grid
        nx, ny, _ = grid.dimensions
        points = grid.points

        filename = "mesh.inp"

        with open(filename, 'w') as f:
            f.write("*HEADING\n")
            f.write("** Generated from PyVista structured grid\n")

            # Nodes
            f.write("*NODE\n")
            for nid, (x, y, z) in enumerate(points, start=1):
                f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")

            # Elements
            f.write("*ELEMENT, TYPE=S4\n")

            eid = 1
            for j in range(ny - 1):
                for i in range(nx - 1):
                    n1 = i + j * nx + 1
                    n2 = (i + 1) + j * nx + 1
                    n3 = (i + 1) + (j + 1) * nx + 1
                    n4 = i + (j + 1) * nx + 1

                    f.write(f"{eid}, {n1}, {n2}, {n3}, {n4}\n")
                    eid += 1

        print(f"Abaqus input file written: {filename}")

    # -------------------------
    # Read results
    # -------------------------
    def read_results(self):
        self.window.u_max.setText("N/A")
        self.window.sigma_1.setText("N/A")
        

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    myapp = App()
    myapp.window.show()

    sys.exit(app.exec())