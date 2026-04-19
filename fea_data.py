from dataclasses import dataclass

@dataclass
class Geometry:
    Lx: float
    Ly: float
    thickness: float

@dataclass
class Material:
    E: float
    nu:float

@dataclass
class Load:
    pressure: float

@dataclass
class Model:
    geometry: Geometry
    material: Material
    load: Load

def build_model_from_ui(window) -> Model:

    geometry = Geometry(
        Lx=window.Lx.value(),
        Ly=window.Ly.value(),
        thickness=window.thick_glass.value()
    )

    material = Material(
        E=window.EMod.value(),  # or window input later
        nu=window.nu.value()
    )

    load = Load(
        pressure=window.appliedLoad.value()
    )

    return Model(
        geometry=geometry,
        material=material,
        load=load
    )