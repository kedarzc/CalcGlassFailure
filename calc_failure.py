import sys
import numpy as np
import pyvista as pv
import pyvistaqt as pvqt

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout,
    QWidget, QPushButton, QLabel,
    QDoubleSpinBox, QSpinBox
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('2D Structured Grid (FEA Style)')
        self.setGeometry(100, 100, 900, 700)

        # -------------------------
        # Layout
        # -------------------------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # -------------------------
        # PyVista plotter
        # -------------------------
        self.plotter = pvqt.QtInteractor(central_widget)
        layout.addWidget(self.plotter.interactor)

        self.plotter.set_background("white")

        self.plotter.add_axes(
            line_width=2,
            labels_off=False,
            viewport=(0.8, 0.0, 1.0, 0.2)
        )

        # -------------------------
        # Geometry (Domain Size)
        # -------------------------
        layout.addWidget(QLabel("Domain Size"))

        self.Lx = QDoubleSpinBox()
        self.Lx.setRange(0.1, 100.0)
        self.Lx.setValue(10.0)
        self.Lx.setKeyboardTracking(False)
        layout.addWidget(self.Lx)

        self.Ly = QDoubleSpinBox()
        self.Ly.setRange(0.1, 100.0)
        self.Ly.setValue(5.0)
        self.Ly.setKeyboardTracking(False)
        layout.addWidget(self.Ly)

        # -------------------------
        # Mesh (Elements)
        # -------------------------
        layout.addWidget(QLabel("Number of Elements"))

        self.ex = QSpinBox()
        self.ex.setRange(1, 200)
        self.ex.setValue(10)
        self.ex.setKeyboardTracking(False)
        layout.addWidget(self.ex)

        self.ey = QSpinBox()
        self.ey.setRange(1, 200)
        self.ey.setValue(6)
        self.ey.setKeyboardTracking(False)
        layout.addWidget(self.ey)

        # -------------------------
        # Button
        # -------------------------
        self.button = QPushButton("Update Grid")
        self.button.clicked.connect(self.update_grid)
        layout.addWidget(self.button)

        # -------------------------
        # Export Abaqus
        # -------------------------
        self.export_button = QPushButton("Export Abaqus")
        self.export_button.clicked.connect(lambda: self.write_abaqus_inp("mesh.inp"))
        layout.addWidget(self.export_button)

        # -------------------------
        # Internal state
        # -------------------------
        self.grid = None
        self.actor = None

        self.update_grid()

    def create_structured_grid(self, Lx, Ly, ex, ey):
        nx = ex + 1
        ny = ey + 1

        x = np.linspace(0, Lx, nx)
        y = np.linspace(0, Ly, ny)

        X, Y = np.meshgrid(x, y, indexing='ij')
        Z = np.zeros_like(X)

        return pv.StructuredGrid(X, Y, Z)

    def update_grid(self):
        self.Lx.interpretText()
        self.Ly.interpretText()
        self.ex.interpretText()
        self.ey.interpretText()

        Lx = self.Lx.value()
        Ly = self.Ly.value()
        ex = self.ex.value()
        ey = self.ey.value()

        self.grid = self.create_structured_grid(Lx, Ly, ex, ey)

        if self.actor is not None:
            self.plotter.remove_actor(self.actor)

        self.actor = self.plotter.add_mesh(
            self.grid,
            color="lightblue",
            show_edges=True,
            edge_color="black"
        )

        self.plotter.reset_camera()
        self.plotter.view_xy()
        self.plotter.render()

    def write_abaqus_inp(self, filename):
        grid = self.grid

        nx, ny, _ = grid.dimensions
        points = grid.points

        with open(filename, 'w') as f:
            f.write("*HEADING\n")
            f.write("** Generated from PyVista structured grid\n")

            f.write("*NODE\n")
            for nid, (x, y, z) in enumerate(points, start=1):
                f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())